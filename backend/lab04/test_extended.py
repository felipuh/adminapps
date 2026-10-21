from test_lab import *
from apps.integration import session_lifecycle as central_life
class Extended(Lab):
    # Load only methods declared here, not inherited focused methods.
    def test_23_insert_failure_login_mfa(self):
        u=user()
        def fail_insert(execute,sql,params,many,ctx):
            result=execute(sql,params,many,ctx)
            if sql.startswith('INSERT INTO "user_sessions"'):raise DatabaseError('synthetic failure after INSERT')
            return result
        with connection.execute_wrapper(fail_insert):
            r=Client().post('/api/auth/login/',{'email':u.email,'password':PW},content_type='application/json')
        self.assertEqual(r.status_code,500);self.assertNotIn('access',r.json());fresh();self.assertFalse(UserSession.objects.filter(user=u).exists())
        config=TwoFactorAuth(user=u,is_enabled=True);config.secret=config.generate_secret();config.save();p=login(u)
        with connection.execute_wrapper(fail_insert):
            r=Client().post('/api/auth/2fa/verify/',{'token':config.get_totp().now()},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+p['temporary_token'])
        self.assertEqual(r.status_code,500);self.assertNotIn('access',r.json());fresh();self.assertFalse(UserSession.objects.filter(user=u).exists());self.assertTrue(TwoFactorChallenge.objects.get(user=u).consumed_at)
        r=Client().post('/api/auth/2fa/verify/',{'token':config.get_totp().now()},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+p['temporary_token']);self.assertEqual(r.status_code,403)

    def test_24_backup_mfa(self):
        u=user();config=TwoFactorAuth(user=u,is_enabled=True);config.secret=config.generate_secret();codes=config.generate_backup_codes();config.save();p=login(u)
        r=Client().post('/api/auth/2fa/verify/',{'token':codes[0]},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+p['temporary_token']);self.assertEqual(r.status_code,200);fresh();self.assertEqual(probe(r.json()['access']),200)
        life.revoke(u);self.deny(r.json()['access']);p=login(u)
        r=Client().post('/api/auth/2fa/verify/',{'token':codes[0]},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+p['temporary_token']);self.assertEqual(r.status_code,400);self.assertEqual(UserSession.objects.filter(user=u).count(),1)

    def test_25_b_and_human_concurrency(self):
        u=user();t=issue(u);s=central(u)
        r=self.ordered(lambda:central_life.revoke_for_user(actor=u,session_id=s.pk),lambda:User.objects.filter(pk=u.pk).update(password=make_password(PW+'reset')),match='FROM "sso_security_fence"')
        self.assertEqual(r['a'],('ok',1));self.assertEqual(r['b'],('ok',1));self.deny(t.access_token);s.refresh_from_db();self.assertEqual(s.state,'revoked');self.assertEqual(SSORevocationOutbox.objects.filter(session=s).count(),1)
        # Opposite ordering: user mutation holds fence after local trigger.
        u=user();t=issue(u);s=central(u)
        def update():
            with transaction.atomic():return raw('UPDATE users SET password=%s WHERE id=%s',[make_password(PW+'reset'),str(u.pk)])
        r=self.ordered(update,lambda:central_life.revoke_for_user(actor=u,session_id=s.pk),match='UPDATE users')
        self.assertEqual(r['a'],('ok',1));self.assertEqual(r['b'],('ok',0));self.deny(t.access_token)

    def test_26_missing_fence_fail_closed(self):
        u=user();t=issue(u);s=central(u)
        # Disabled B fence rejects central lifecycle; local authority stays separate.
        raw('UPDATE sso_security_fence SET enabled=false WHERE id=1')
        try:
            with self.assertRaises(AuthenticationFailed):central_life.revoke_for_user(actor=u,session_id=s.pk)
            self.assertEqual(probe(t.access_token),200)
        finally:raw('UPDATE sso_security_fence SET enabled=true WHERE id=1')
        self.sql_reject('DELETE FROM sso_security_fence WHERE id=1')

    def test_27_app_timeout_maps_to_503(self):
        u=user();t=issue(u)
        with transaction.atomic():
            User.objects.select_for_update().get(pk=u.pk)
            def worker():
                try:
                    raw("SET lock_timeout='100ms'")
                    try:life.refresh_pair(str(t))
                    except life.SessionUnavailable as e:return e.status_code
                    return 'unexpected success'
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as p:self.assertEqual(p.submit(worker).result(timeout=4),503)
        self.assertEqual(state(t['sid'])[3],1);self.assertEqual(probe(t.access_token),200)

    def test_28_family_unique_and_legacy(self):
        u=user();a=issue(u)
        fields=[f.column for f in UserSession._meta.concrete_fields];select=[('%s' if f in ('id','token_jti') else '"'+f+'"') for f in fields]
        sql='INSERT INTO user_sessions ('+','.join('"'+f+'"' for f in fields)+') SELECT '+','.join(select)+' FROM user_sessions WHERE id=%s'
        self.sql_reject(sql,[str(uuid.uuid4()),uuid.uuid4().hex,a['sid']],('23505',))
        legacy=UserSession.objects.create(user=u,token_jti=uuid.uuid4().hex,expires_at=timezone.now()+timedelta(days=1))
        self.assertEqual(legacy.contract_version,0);self.assertIsNone(legacy.family_id)
        token=a.access_token;token['sid']=str(legacy.pk);self.deny(token)

    def test_29_sql_delete_reinsert_resurrection_boundary(self):
        u=user();t=issue(u);access=t.access_token;original=UserSession.objects.get(pk=t['sid']);life.revoke(u);self.deny(access)
        # Actual application-role DELETE/INSERT, with a saved synthetic row snapshot.
        # This is a deliberately failing acceptance, not a simulated ORM result.
        try:
            with transaction.atomic():
                raw('DELETE FROM user_sessions WHERE id=%s',[t['sid']])
                fields=[f for f in UserSession._meta.concrete_fields]
                raw('INSERT INTO user_sessions ('+','.join('"'+f.column+'"' for f in fields)+') VALUES ('+','.join(['%s']*len(fields))+')',[getattr(original,f.attname) for f in fields])
            fresh();status=probe(access);event('delete_reinsert',restored_http_status=status,role='lab04_iam',finding='UPDATE-only guard does not protect DELETE/INSERT')
            self.assertEqual(status,401,'Revoked JWT regained authority after SQL DELETE/reinsert under application DML grants')
        finally:
            # Return synthetic row to terminal state before retaining evidence.
            life.revoke(u,session_id=t['sid'])

    def test_30_authenticator_rollback_safety(self):
        u=user();t=issue(u);life.revoke(u);fresh();self.deny(t.access_token)
        # Pure validation demonstration: historical stateless backend still accepts signature/user.
        from rest_framework_simplejwt.authentication import JWTAuthentication
        stateless=JWTAuthentication();validated=stateless.get_validated_token(str(t.access_token));self.assertEqual(stateless.get_user(validated).pk,u.pk)
        event('unsafe_stateless_rollback',would_accept_revoked_bearer=True,active_settings_changed=False)

if __name__=='__main__':
    suite=unittest.TestSuite(Extended(name) for name in sorted(Extended.__dict__) if name.startswith('test_'))
    r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
    (ROOT/'extended-results.json').write_text(json.dumps(RESULTS,indent=2));(ROOT/'observations-extended.json').write_text(json.dumps(EVENTS,indent=2,default=str))
    raise SystemExit(not r.wasSuccessful())
