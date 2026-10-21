import lab_env
import json,time,threading,traceback,uuid,unittest,hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from contextlib import contextmanager
from unittest.mock import patch
from django.db import connection,connections,transaction,DatabaseError
from django.test import Client,override_settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password,PBKDF2PasswordHasher
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from apps.users import human_sessions as life
from apps.users.models import User,UserSession,UserActivityLog,UserOrganization
from apps.users.models_2fa import TwoFactorAuth,TwoFactorChallenge
from apps.integration.models import SSOSession,SSOSecurityFence,SSORevocationOutbox,SSOClient,IntegrationAPIKey
from apps.organizations.models import Organization,OrganizationInvitation
from apps.products.models import ProductSystem
from lab_urls import Protected
ROOT=lab_env.ROOT
PW='Synthetic-only-Lab01!a72'
EVENTS=[]
SQL=open(ROOT/'sql-trace.jsonl','a',buffering=1)
def event(kind,**kw): EVENTS.append({'kind':kind,**kw})
def trace(execute,sql,params,many,context):
    start=time.monotonic()
    try: return execute(sql,params,many,context)
    finally:
        # Parameters deliberately excluded: no passwords, JWTs, TOTP secrets or cookies.
        SQL.write(json.dumps({'thread':threading.current_thread().name,'sql':sql,'parameters':'OMITTED','ms':round((time.monotonic()-start)*1000,2)})+'\n')
def fresh():
    connection.close()
    with connection.cursor() as q: q.execute('SELECT pg_backend_pid()'); return q.fetchone()[0]
def user(): return User.objects.create_user(email=f'{uuid.uuid4()}@example.invalid',password=PW,first_name='Lab',last_name='Synthetic')
def issue(u): return life.issue_refresh(u)
def raw(sql,args=()):
    with connection.cursor() as q:
        q.execute(sql,args)
        return q.fetchall() if q.description else q.rowcount
def probe(access,client=None): return (client or Client()).get('/probe/',HTTP_AUTHORIZATION='Bearer '+str(access)).status_code
def login(u,client=None):
    r=(client or Client()).post('/api/auth/login/',{'email':u.email,'password':PW},content_type='application/json')
    assert r.status_code==200, ('login status',r.status_code)
    return r.json()
def rejected(fn):
    try: fn()
    except (AuthenticationFailed,life.SessionUnavailable): return
    raise AssertionError('Expected authority denial')
def central(u):
    tag=uuid.uuid4().hex[:12]
    org=Organization.objects.create(code=tag,name='Lab tenant',email=tag+'@example.invalid',status='active')
    prod=ProductSystem.objects.create(code=tag,slug=tag,name='Lab product')
    key=IntegrationAPIKey.objects.create(name='Lab principal',credential_hash='synthetic-unusable',fingerprint=tag)
    client=SSOClient.objects.create(client_id=tag,audience='lab:'+tag,issuer='https://example.invalid',product=prod,principal=key)
    gen=raw('UPDATE sso_security_fence SET generation=generation+1 WHERE id=1 RETURNING generation')[0][0]
    return SSOSession.objects.create(user=u,client=client,tenant=org,product=prod.code,generation=gen,authority_version=gen,
        authenticated_at=timezone.now(),expires_at=timezone.now()+timedelta(hours=1),role='user')
def state(sid):
    return raw('SELECT id,user_id,family_id,generation,authority_version,is_active,revoked_at,revocation_reason FROM user_sessions WHERE id=%s',[sid])[0]

class Lab(unittest.TestCase):
    def setUp(self): self.trace=connection.execute_wrapper(trace); self.trace.__enter__()
    def tearDown(self): self.trace.__exit__(None,None,None); connections.close_all()
    def deny(self,t):
        before=Protected.calls; self.assertEqual(probe(t),401); self.assertEqual(Protected.calls,before)
    def sql_reject(self,sql,args=(),codes=('P0001','23514','23505','23503','22003')):
        try:
            with transaction.atomic(): raw(sql,args)
        except DatabaseError as e:
            code=getattr(e.__cause__, 'sqlstate', None) or getattr(e.__cause__, 'pgcode', None); self.assertIn(code,codes); event('sql_rejected',sql=sql,sqlstate=code); return
        self.fail('SQL mutation unexpectedly accepted: '+sql)
    def ordered(self,a,b,match='FROM "users"',must_wait=True):
        held=threading.Event(); release=threading.Event(); entered=threading.Event(); results={}; pids={}
        def worker(name,fn):
            connections.close_all(); pids[name]=fresh()
            def pause(execute,sql,params,many,ctx):
                value=trace(execute,sql,params,many,ctx)
                if name=='a' and not held.is_set() and match in sql and ('FOR UPDATE' in sql or sql.startswith('UPDATE')):
                    held.set(); assert release.wait(6),'release timeout'
                return value
            try:
                with connection.execute_wrapper(pause):
                    if name=='b': entered.set()
                    results[name]=('ok',fn())
            except Exception as e: results[name]=('error',type(e).__name__)
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            fa=pool.submit(worker,'a',a)
            try:
                self.assertTrue(held.wait(5),'first lock not reached')
                fb=pool.submit(worker,'b',b); self.assertTrue(entered.wait(3))
                blockers=[]; end=time.monotonic()+3
                while time.monotonic()<end:
                    blockers=raw('SELECT pg_blocking_pids(%s)',[pids['b']])[0][0]
                    if blockers or fb.done(): break
                    time.sleep(.02)
                if must_wait:self.assertIn(pids['a'],blockers)
                event('ordered_race',pids=pids.copy(),blockers=blockers,match=match)
            finally: release.set()
            fa.result(timeout=8); fb.result(timeout=8)
        self.assertNotEqual(pids['a'],pids['b']);return results

    def test_01_schema_role(self):
        row=raw("SELECT current_user,current_setting('transaction_isolation'),current_setting('fsync'),current_setting('synchronous_commit')")[0]
        self.assertEqual(row,('lab04_iam','read committed','on','on'))
        perms=raw("SELECT rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=current_user")[0];self.assertFalse(any(perms))
        self.assertFalse(raw("SELECT has_schema_privilege(current_user,'public','CREATE')")[0][0])
        triggers=raw("SELECT c.relname,t.tgname,pg_get_triggerdef(t.oid) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid WHERE NOT t.tgisinternal ORDER BY 1,2")
        self.assertIn('adminapps_human_authority',[r[1] for r in triggers]);self.assertIn('sso_authority_users',[r[1] for r in triggers])
        (ROOT/'schema-catalog.json').write_text(json.dumps({'effective':row,'role_flags':perms,'triggers':triggers,
          'constraints':raw("SELECT conrelid::regclass::text,conname,pg_get_constraintdef(oid) FROM pg_constraint WHERE connamespace='public'::regnamespace ORDER BY 1,2"),
          'indexes':raw("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY 1,2"),
          'permissions':raw("SELECT table_name,privilege_type FROM information_schema.role_table_grants WHERE grantee=current_user ORDER BY 1,2")},indent=2,default=str))
        self.assertEqual(raw('SELECT count(*) FROM token_blacklist_outstandingtoken')[0][0],0)

    def test_02_durable_client_lifecycle(self):
        u=user();pair=login(u); t=life.HumanRefreshToken(pair['refresh']); sid=t['sid']
        p1=fresh(); self.assertEqual(probe(pair['access']),200); p2=fresh();self.assertNotEqual(p1,p2);self.assertEqual(probe(pair['access']),200)
        event('durable_before',pids=[p1,p2],row=state(sid))
        r=Client().post('/api/auth/refresh/',{'refresh':pair['refresh']},content_type='application/json');self.assertEqual(r.status_code,200);p=r.json(); self.deny(pair['access'])
        r=Client().post('/api/auth/users/revoke_session/',{'session_id':sid},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+p['access']);self.assertEqual(r.status_code,200)
        fresh();self.deny(p['access']);self.assertEqual(Client().post('/api/auth/refresh/',{'refresh':p['refresh']},content_type='application/json').status_code,401)
        new=login(u);self.assertEqual(probe(new['access']),200);self.deny(p['access']);self.assertNotEqual(life.HumanRefreshToken(new['refresh'])['sid'],sid)
        event('durable_after',row=state(sid))
        r=Client().post('/api/auth/logout/',{'refresh':new['refresh']},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+new['access']);self.assertEqual(r.status_code,200);fresh();self.deny(new['access'])

    def test_03_two_refresh(self):
        u=user();t=issue(u);r=self.ordered(lambda:life.refresh_pair(str(t)),lambda:life.refresh_pair(str(t)))
        self.assertEqual(r['a'][0],'ok');self.assertEqual(r['b'],('error','AuthenticationFailed'))
        self.assertEqual(state(t['sid'])[3],2);self.assertEqual(probe(r['a'][1]['access']),200);self.deny(t.access_token)

    def test_04_refresh_revoke_both_orders(self):
        for first in ('refresh','revoke'):
            with self.subTest(first=first):
                u=user();t=issue(u);ops={'refresh':lambda:life.refresh_pair(str(t)),'revoke':lambda:life.revoke(u,session_id=t['sid'])}
                second='revoke' if first=='refresh' else 'refresh';r=self.ordered(ops[first],ops[second])
                self.assertEqual(r['a'][0],'ok')
                self.assertEqual(r['b'][0],'ok' if first=='refresh' else 'error')
                fresh();self.deny(t.access_token);rejected(lambda:life.refresh_pair(str(t)))
                if first=='refresh':self.deny(r['a'][1]['access'])

    def test_05_logout_rotation(self):
        for first in ('logout','refresh'):
            u=user();t=issue(u);a=t.access_token
            ops={'logout':lambda:life.logout_session(u,a,str(t)),'refresh':lambda:life.refresh_pair(str(t))}
            r=self.ordered(ops[first],ops['refresh' if first=='logout' else 'logout'])
            self.assertEqual(r['a'][0],'ok');self.deny(a)
            if first=='refresh':self.deny(r['a'][1]['access'])
            self.assertFalse(state(t['sid'])[5])

    def test_06_individual_and_global_revocation(self):
        for global_ in (False,True):
            u=user();t=issue(u);other=issue(u); outsider=user();foreign=issue(outsider)
            kwargs={} if global_ else {'session_id':t['sid']}
            r=self.ordered(lambda:life.revoke(u,**kwargs),lambda:life.revoke(u,**kwargs))
            self.assertEqual(r['a'],('ok',2 if global_ else 1));self.assertEqual(r['b'],('ok',0));self.deny(t.access_token)
            self.assertEqual(probe(other.access_token),401 if global_ else 200);self.assertEqual(probe(foreign.access_token),200)

    def test_07_password_vs_issue(self):
        for first in ('password','issue'):
            u=user();t=issue(u)
            def change():
                with transaction.atomic(): return raw('UPDATE users SET password=%s WHERE id=%s',[make_password(PW+'reset'),str(u.pk)])
            r=self.ordered(change if first=='password' else lambda:issue(u),lambda:issue(u) if first=='password' else change(),match='UPDATE users' if first=='password' else 'FROM "users"')
            self.assertEqual(r['a'][0],'ok');self.deny(t.access_token)
            if first=='password':self.assertEqual(r['b'],('error','AuthenticationFailed'))
            else:self.deny(r['a'][1].access_token)

    def test_08_disable_auth_and_enable(self):
        u=user();t=issue(u)
        # Reader sees committed state while disabling transaction is still uncommitted (READ COMMITTED).
        def disable():
            with transaction.atomic():return raw('UPDATE users SET is_active=false WHERE id=%s',[str(u.pk)])
        r=self.ordered(disable,lambda:probe(t.access_token),match='UPDATE users',must_wait=False)
        self.assertEqual(r['b'],('ok',200));fresh();self.deny(t.access_token)
        User.objects.filter(pk=u.pk).update(is_active=True);fresh();self.deny(t.access_token);u.refresh_from_db();self.assertEqual(u.human_auth_version,3);self.assertEqual(probe(issue(u).access_token),200)

    def test_09_password_and_activity_all_write_paths(self):
        for field in ('password','is_active'):
            for route in ('save','bulk','sql'):
                u=user();t=issue(u);old=getattr(u,field);new=make_password(PW+'x') if field=='password' else False
                if route=='save':setattr(u,field,new);u.save(update_fields=[field])
                elif route=='bulk':setattr(u,field,new);User.objects.bulk_update([u],[field])
                else:raw('UPDATE users SET '+field+'=%s WHERE id=%s',[new,str(u.pk)])
                fresh();u.refresh_from_db();self.assertEqual(u.human_auth_version,2);self.deny(t.access_token)
                raw('UPDATE users SET '+field+'=%s WHERE id=%s',[old,str(u.pk)]);self.deny(t.access_token);u.refresh_from_db();self.assertEqual(u.human_auth_version,3)

    def test_10_trigger_guards(self):
        u=user();t=issue(u);sid=t['sid'];row=state(sid)
        edits=[('generation=0',[]),('user_id=%s',[str(user().pk)]),('family_id=%s',[str(uuid.uuid4())]),('authority_version=authority_version+1',[]),('contract_version=0',[]),('token_family=%s',['CENTRAL']),('created_at=created_at-interval \'1 day\'',[]),('expires_at=expires_at+interval \'1 day\'',[]),('token_jti=%s',[uuid.uuid4().hex]),('is_active=false',[]),('revoked_at=clock_timestamp()',[])]
        for edit,params in edits:self.sql_reject('UPDATE user_sessions SET '+edit+' WHERE id=%s',params+[sid])
        self.assertEqual(state(sid),row)
        raw('UPDATE users SET human_auth_version=0 WHERE id=%s',[str(u.pk)]);u.refresh_from_db();self.assertEqual(u.human_auth_version,1)
        raw('UPDATE users SET human_auth_version=500 WHERE id=%s',[str(u.pk)]);u.refresh_from_db();self.assertEqual(u.human_auth_version,1)
        life.revoke(u,session_id=sid);rev=state(sid)
        for edit in ('is_active=true,generation=generation+1','generation=generation+1','revoked_at=NULL','revocation_reason=\'altered\''):
            self.sql_reject('UPDATE user_sessions SET '+edit+' WHERE id=%s',[sid])
        self.assertEqual(state(sid),rev)

    def test_11_uniqueness_fk_overflow_inconsistency(self):
        u=user();a=issue(u);b=issue(u)
        self.sql_reject('UPDATE user_sessions SET token_jti=%s,generation=generation+1 WHERE id=%s',[a['jti'],b['sid']],('23505',))
        # FK tested on a legacy insert to avoid monotonic UPDATE guard.
        self.sql_reject('INSERT INTO user_sessions(id,user_id,token_jti,ip_address,user_agent,device_type,browser,os,created_at,expires_at,last_activity_at,is_active,contract_version,token_family,family_id,generation,authority_version,revocation_reason) SELECT %s,%s,%s,ip_address,user_agent,device_type,browser,os,created_at,expires_at,last_activity_at,is_active,contract_version,token_family,%s,generation,authority_version,revocation_reason FROM user_sessions WHERE id=%s',[str(uuid.uuid4()),str(uuid.uuid4()),uuid.uuid4().hex,str(uuid.uuid4()),a['sid']],('23503',))
        raw('UPDATE user_sessions SET generation=9223372036854775807 WHERE id=%s',[a['sid']]);self.deny(a.access_token)
        with self.assertRaises(life.SessionUnavailable):life.revoke(u,session_id=a['sid'])
        self.assertTrue(state(a['sid'])[5]);self.deny(a.access_token)

    def test_12_rollback_local_central_outbox(self):
        u=user();t=issue(u);s=central(u);before=state(t['sid']);fence=list(SSOSecurityFence.objects.values())[0];n=SSORevocationOutbox.objects.count()
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                User.objects.filter(pk=u.pk).update(is_active=False)
                self.assertFalse(UserSession.objects.get(pk=t['sid']).is_active);self.assertEqual(SSOSession.objects.get(pk=s.pk).state,'revoked')
                # Independent connection cannot see partial effects.
                with ThreadPoolExecutor(max_workers=1) as p:
                    def read():
                        try:return state(t['sid'])[5]
                        finally:connections.close_all()
                    self.assertTrue(p.submit(read).result())
                raise RuntimeError('synthetic rollback')
        fresh();self.assertEqual(state(t['sid']),before);self.assertEqual(list(SSOSecurityFence.objects.values())[0],fence);self.assertEqual(SSORevocationOutbox.objects.count(),n);self.assertEqual(SSOSession.objects.get(pk=s.pk).state,'active');self.assertEqual(probe(t.access_token),200)
        # Rejection by trigger rolls back an earlier valid write in same transaction.
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                User.objects.filter(pk=u.pk).update(first_name='Rolled back')
                raw('UPDATE user_sessions SET generation=0 WHERE id=%s',[t['sid']])
        u.refresh_from_db();self.assertEqual(u.first_name,'Lab')

    def test_13_hash_upgrade(self):
        u=user();User.objects.filter(pk=u.pk).update(password=make_password(PW,hasher='md5'));u.refresh_from_db();old=issue(u);v=u.human_auth_version
        pair=login(u);fresh();u.refresh_from_db();self.assertTrue(u.password.startswith('pbkdf2_sha256$'));self.assertEqual(u.human_auth_version,v+1)
        self.deny(old.access_token);self.assertEqual(probe(pair['access']),200);self.assertEqual(life.HumanRefreshToken(pair['refresh'])['av'],u.human_auth_version)

    def test_14_reset_vs_hash_upgrade(self):
        u=user();User.objects.filter(pk=u.pk).update(password=make_password(PW,hasher='md5'));u.refresh_from_db()
        entered=threading.Event();release=threading.Event();original=PBKDF2PasswordHasher.encode
        def pause(hasher,password,salt,iterations=None):
            value=original(hasher,password,salt,iterations)
            if threading.current_thread().name.startswith('hash-upgrade'):entered.set();assert release.wait(6)
            return value
        result={}
        def worker():
            try:result['status']=Client().post('/api/auth/login/',{'email':u.email,'password':PW},content_type='application/json').status_code
            finally:connections.close_all()
        with patch.object(PBKDF2PasswordHasher,'encode',pause):
            thread=threading.Thread(target=worker,name='hash-upgrade-race');thread.start()
            try:
                self.assertTrue(entered.wait(5));reset=make_password(PW+'reset');User.objects.filter(pk=u.pk).update(password=reset)
            finally:release.set()
            thread.join(8);self.assertFalse(thread.is_alive())
        self.assertEqual(result['status'],401);u.refresh_from_db();self.assertEqual(u.password,reset);self.assertFalse(UserSession.objects.filter(user=u).exists())

    def test_15_b_authority_separation(self):
        u=user();a=issue(u);b=issue(u);s=central(u);other=user();foreign=central(other)
        self.assertNotEqual(str(s.pk),a['sid']);life.revoke(u,session_id=a['sid']);s.refresh_from_db();self.assertEqual(s.state,'active');self.assertEqual(probe(b.access_token),200)
        User.objects.filter(pk=u.pk).update(password=make_password(PW+'reset'));fresh();s.refresh_from_db();foreign.refresh_from_db()
        self.assertEqual(s.state,'revoked');self.assertEqual(foreign.state,'active');self.assertEqual(SSORevocationOutbox.objects.filter(session=s).count(),1);self.deny(b.access_token)
        # Local bearer does not grant product creation.
        normal=user();t=issue(normal);self.assertEqual(Client().post('/api/products/systems/',{'name':'forbidden'},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+str(t.access_token)).status_code,403)

    def test_16_b_revocation_does_not_revoke_human(self):
        u=user();a=issue(u);s=central(u)
        # Triggered client revocation affects B only.
        SSOClient.objects.filter(pk=s.client_id).update(enabled=True);s.refresh_from_db();self.assertEqual(s.state,'revoked');self.assertEqual(probe(a.access_token),200)
        self.sql_reject('UPDATE sso_sessions SET state=\'active\',revoked_at=NULL,generation=generation+1 WHERE id=%s',[str(s.pk)])
        self.sql_reject('UPDATE sso_security_fence SET authority_epoch=0 WHERE id=1')

    def test_17_mfa_and_registration(self):
        u=user();config=TwoFactorAuth(user=u,is_enabled=True);config.secret=config.generate_secret();config.save()
        pair=login(u);self.assertTrue(pair['requires_2fa']);self.assertFalse(UserSession.objects.filter(user=u).exists())
        r=Client().post('/api/auth/2fa/verify/',{'token':config.get_totp().now()},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+pair['temporary_token']);self.assertEqual(r.status_code,200);self.assertEqual(probe(r.json()['access']),200)
        r=Client().post('/api/auth/2fa/verify/',{'token':config.get_totp().now()},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+pair['temporary_token']);self.assertEqual(r.status_code,403)
        inviter=user();org=Organization.objects.create(code=uuid.uuid4().hex[:15],name='Registration',email='org@example.invalid',status='active');inviter.organization=org;inviter.role='org_admin';inviter.save();UserOrganization.objects.create(user=inviter,organization=org,role='org_admin',is_active=True)
        email=uuid.uuid4().hex+'@example.invalid';inv=OrganizationInvitation.objects.create(organization=org,email=email,invited_by=inviter,expires_at=timezone.now()+timedelta(days=1))
        r=Client().post('/api/auth/register/',{'email':email,'first_name':'Registered','last_name':'Lab','password':PW,'password_confirm':PW,'invitation_token':inv.token},content_type='application/json');self.assertEqual(r.status_code,201);p=r.json()['tokens'];self.assertEqual(probe(p['access']),200);fresh();inv.refresh_from_db();self.assertEqual(inv.status,'accepted')
        registered=User.objects.get(email=email);life.revoke(registered);self.deny(p['access'])

    def test_18_legacy_foreign_and_cookie(self):
        u=user();t=issue(u);client=Client(enforce_csrf_checks=True);client.force_login(u)
        self.assertEqual(client.get('/probe/').status_code,200);self.assertEqual(client.post('/probe/',{}).status_code,403)
        legacy=AccessToken.for_user(u);self.assertEqual(probe(legacy,client),401)
        for family in ('CENTRAL','ISO_LOCAL','MED_LOCAL'):
            access=t.access_token;access['token_family']=family;self.assertEqual(probe(access,client),401)
        self.assertEqual(probe(t,client),401);self.assertEqual(client.get('/probe/',HTTP_AUTHORIZATION='Bearer synthetic-api-key').status_code,401)
        life.revoke(u);self.assertEqual(probe(t.access_token,client),401);self.assertEqual(client.get('/probe/').status_code,200)
        from django.middleware.csrf import _get_new_csrf_string
        csrf=_get_new_csrf_string();client.cookies['csrftoken']=csrf
        r=client.post('/api/auth/logout/',{},HTTP_X_CSRFTOKEN=csrf);self.assertEqual(r.status_code,200);self.assertEqual(client.get('/probe/').status_code,401)

    def test_19_ambient_transactions_and_store_error(self):
        u=user();t=issue(u)
        with transaction.atomic():
            for fn in (lambda:issue(u),lambda:life.refresh_pair(str(t)),lambda:life.revoke(u)):
                with self.assertRaises(life.SessionUnavailable):fn()
        connection.set_autocommit(False)
        try:
            with self.assertRaises(life.SessionUnavailable):life.revoke(u)
        finally:connection.rollback();connection.set_autocommit(True)
        # Real PostgreSQL missing relation, confined to this session search_path.
        raw('SET search_path=pg_catalog')
        try:
            with self.assertRaises(life.SessionUnavailable):life.authenticate_access(t.access_token)
        finally:raw('SET search_path=public')
        self.assertEqual(probe(t.access_token),200)

    def test_20_post_write_failure_and_audit(self):
        u=user();t=issue(u);before=state(t['sid'])
        def fail_after_update(execute,sql,params,many,ctx):
            result=execute(sql,params,many,ctx)
            if sql.startswith('UPDATE "user_sessions"'):raise DatabaseError('synthetic after SQL persistence before commit')
            return result
        with connection.execute_wrapper(fail_after_update):
            with self.assertRaises(life.SessionUnavailable):life.refresh_pair(str(t))
        fresh();self.assertEqual(state(t['sid']),before);self.assertEqual(probe(t.access_token),200)
        # Audit failure after durable revocation must not restore bearer authority.
        client=Client(raise_request_exception=False)
        with patch('apps.users.views.log_logout_activity',side_effect=RuntimeError('synthetic post-commit audit failure')):
            r=client.post('/api/auth/logout/',{},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+str(t.access_token));self.assertEqual(r.status_code,500)
        fresh();self.deny(t.access_token);self.assertEqual(life.revoke(u,session_id=t['sid']),0)

    def test_21_lock_timeout(self):
        u=user();t=issue(u)
        def waiter():
            raw("SET lock_timeout='150ms'")
            try:return life.refresh_pair(str(t))
            finally:raw("SET lock_timeout='8000ms'")
        r=self.ordered(lambda:life.refresh_pair(str(t)),waiter)
        # ordered releases on observed lock; separate explicit holder verifies timeout deterministically below.
        u=user();t=issue(u)
        with transaction.atomic():
            User.objects.select_for_update().get(pk=u.pk)
            def blocked():
                try:
                    raw("SET lock_timeout='100ms'")
                    try:raw('SELECT id FROM users WHERE id=%s FOR UPDATE',[str(u.pk)])
                    except DatabaseError as e:return getattr(e.__cause__, 'sqlstate', None) or getattr(e.__cause__, 'pgcode', None)
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as p:self.assertEqual(p.submit(blocked).result(timeout=4),'55P03')
        self.assertEqual(probe(t.access_token),200);event('lock_timeout',sqlstate='55P03')

    def test_22_deadlock_rollback(self):
        a=user();b=user();ta=issue(a);tb=issue(b);barrier=threading.Barrier(2)
        def worker(x,y):
            try:
                with transaction.atomic():
                    raw('SELECT id FROM users WHERE id=%s FOR UPDATE',[str(x.pk)]);barrier.wait(timeout=4)
                    raw('UPDATE users SET is_active=false WHERE id=%s',[str(y.pk)])
                return 'commit'
            except DatabaseError as e:return getattr(e.__cause__, 'sqlstate', None) or getattr(e.__cause__, 'pgcode', None)
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as p:
            fa=p.submit(worker,a,b);fb=p.submit(worker,b,a);out=[fa.result(timeout=8),fb.result(timeout=8)]
        self.assertCountEqual(out,['commit','40P01']);event('deadlock',outcomes=out)
        a.refresh_from_db();b.refresh_from_db();self.assertEqual(sum([a.is_active,b.is_active]),1)
        self.assertEqual(probe(ta.access_token),200 if a.is_active else 401);self.assertEqual(probe(tb.access_token),200 if b.is_active else 401)

class Result(unittest.TextTestResult):
    def startTest(self,test):super().startTest(test);self.start=time.monotonic()
    def addSuccess(self,test):super().addSuccess(test);RESULTS.append({'test':test.id(),'status':'PASS','seconds':round(time.monotonic()-self.start,3)})
    def addFailure(self,test,err):super().addFailure(test,err);RESULTS.append({'test':test.id(),'status':'FAIL','error':self._exc_info_to_string(err,test)})
    def addError(self,test,err):super().addError(test,err);RESULTS.append({'test':test.id(),'status':'ERROR','error':self._exc_info_to_string(err,test)})
RESULTS=[]
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Lab)
    result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
    (ROOT/'focused-results.json').write_text(json.dumps(RESULTS,indent=2));(ROOT/'observations.json').write_text(json.dumps(EVENTS,indent=2,default=str))
    raise SystemExit(not result.wasSuccessful())
