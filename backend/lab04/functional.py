from test_lab import *
import test_lab,test_extended,copy
from apps.integration import session_lifecycle as central_life
@contextmanager
def fixture_owner():
 # Fixtures for business provisioning only. Every HTTP/service under test uses runtime.
 old=copy.deepcopy(connection.settings_dict);connection.close()
 connection.settings_dict.update(USER='lab04_bootstrap',PASSWORD='',OPTIONS={'options':'-c role=lab04_maintenance'})
 try:
  assert raw('SELECT current_user')[0][0]=='lab04_maintenance'
  yield
 finally:
  connection.close();connection.settings_dict.clear();connection.settings_dict.update(old)
  assert raw('SELECT current_user')[0][0]=='lab04_iam'
original_central=test_lab.central
def fixture_central(u):
 with fixture_owner():return original_central(u)
test_lab.central=fixture_central;test_extended.central=fixture_central
class Added(Lab):
 def test_mfa_totp_registration(self):
  u=user();config=TwoFactorAuth(user=u,is_enabled=True);config.secret=config.generate_secret();config.save()
  pair=login(u);self.assertTrue(pair['requires_2fa']);self.assertFalse(UserSession.objects.filter(user=u).exists())
  r=Client().post('/api/auth/2fa/verify/',{'token':config.get_totp().now()},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+pair['temporary_token']);self.assertEqual(r.status_code,200);self.assertEqual(probe(r.json()['access']),200)
  r=Client().post('/api/auth/2fa/verify/',{'token':config.get_totp().now()},content_type='application/json',HTTP_AUTHORIZATION='Bearer '+pair['temporary_token']);self.assertEqual(r.status_code,403)
  inviter=user()
  with fixture_owner():
   org=Organization.objects.create(code=uuid.uuid4().hex[:15],name='Registration',email='org@example.invalid',status='active');inviter.organization=org;inviter.role='org_admin';inviter.save();UserOrganization.objects.create(user=inviter,organization=org,role='org_admin',is_active=True)
   email=uuid.uuid4().hex+'@example.invalid';inv=OrganizationInvitation.objects.create(organization=org,email=email,invited_by=inviter,expires_at=timezone.now()+timedelta(days=1))
  r=Client().post('/api/auth/register/',{'email':email,'first_name':'Registered','last_name':'Lab','password':PW,'password_confirm':PW,'invitation_token':inv.token},content_type='application/json');self.assertEqual(r.status_code,201);p=r.json()['tokens'];self.assertEqual(probe(p['access']),200);fresh();inv.refresh_from_db();self.assertEqual(inv.status,'accepted');registered=User.objects.get(email=email);life.revoke(registered);self.deny(p['access'])
 def test_b_service_and_retention(self):
  u=user();t=issue(u);s=fixture_central(u)
  self.assertEqual(central_life.revoke_for_user(actor=u,session_id=s.pk),1);self.assertEqual(central_life.revoke_for_user(actor=u,session_id=s.pk),0)
  self.assertEqual(probe(t.access_token),200);s.refresh_from_db();self.assertEqual(s.state,'revoked');self.assertEqual(SSORevocationOutbox.objects.filter(session=s).count(),1)
  self.sql_reject("UPDATE sso_sessions SET state='active',revoked_at=NULL,generation=generation+1 WHERE id=%s",[str(s.pk)])
  self.sql_reject('DELETE FROM sso_sessions WHERE id=%s',[str(s.pk)],('42501',))
  self.sql_reject('DELETE FROM sso_revocation_outbox WHERE session_id=%s',[str(s.pk)],('42501',))
  s2=fixture_central(u)
  with fixture_owner():SSOClient.objects.filter(pk=s2.client_id).update(enabled=True)
  s2.refresh_from_db();self.assertEqual(s2.state,'revoked');self.assertEqual(probe(t.access_token),200)

names=['test_02_durable_client_lifecycle','test_03_two_refresh','test_04_refresh_revoke_both_orders','test_05_logout_rotation','test_06_individual_and_global_revocation','test_09_password_and_activity_all_write_paths','test_10_trigger_guards','test_12_rollback_local_central_outbox','test_13_hash_upgrade','test_14_reset_vs_hash_upgrade','test_15_b_authority_separation','test_18_legacy_foreign_and_cookie']
suite=unittest.TestSuite([Lab(n) for n in names]+[test_extended.Extended(n) for n in ['test_23_insert_failure_login_mfa','test_24_backup_mfa','test_25_b_and_human_concurrency']]+[Added('test_mfa_totp_registration'),Added('test_b_service_and_retention')])
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
(ROOT/'functional-results.json').write_text(json.dumps(RESULTS,indent=2));(ROOT/'functional-observations.json').write_text(json.dumps(EVENTS,indent=2,default=str));raise SystemExit(not r.wasSuccessful())
