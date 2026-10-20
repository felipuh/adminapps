"""Decision D successors; originals A/C/H/B are not modified."""
import importlib.util,json,sys,unittest,uuid
from pathlib import Path
from types import SimpleNamespace as NS
from datetime import timedelta
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('b',Path.cwd()/'backend/scripts/rec_sso_03b_offline.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
h=b.h
from apps.integration.authorization import entitlement_eligible
from apps.integration.authorization_contract import CONTRACT
from apps.products.models import OrganizationProductEntitlement,ProductSystem

class AuthorizationTests(b.LifecycleTests):
    def products_with_scopes(self,role='viewer',scopes=None):
        self.member.role=role
        return [{'code':self.row.product.code,'access_allowed':True,'authorization_eligible':True,'modules_enabled':[],'scopes':scopes if scopes is not None else [self.row.product.code+':resources.resource:read']}]
    def test_live_grant_intersection_and_no_extra_scope(self):
        product=self.row.product.code
        products=self.products_with_scopes(scopes=[product+':resources.resource:read',product+':resources.resource:create'])
        with patch.object(h.sso,'_serialize_product_entitlements',return_value=products):
            token=self.issue();response,body=self.inspect(token)
        self.assertEqual(response.status_code,200);self.assertEqual(body['authorization']['contract'],CONTRACT)
        self.assertEqual(body['authorization']['scopes'],[product+':resources.resource:read'])
        self.assertEqual(body['authorization']['av'],body['av']);self.assertEqual(body['authorization']['tenant_id'],body['tenant_id'])
        self.assertNotIn('authorization',self.data(token))
    def test_empty_unknown_foreign_scopes_and_entitlement_absent_deny_functional_only(self):
        for scopes in ([],['*'],['unknown'],['OTHER:resources.resource:read'],None):
            products=self.products_with_scopes();products[0]['scopes']=scopes
            with patch.object(h.sso,'_serialize_product_entitlements',return_value=products):
                token=self.issue();_,body=self.inspect(token)
            self.assertTrue(body['active']);self.assertEqual(body['authorization']['state'],'denied');self.assertEqual(body['authorization']['scopes'],[])
        products=self.products_with_scopes();products[0]['authorization_eligible']=False
        with patch.object(h.sso,'_serialize_product_entitlements',return_value=products):
            token=self.issue();_,body=self.inspect(token)
        self.assertEqual(body['authorization']['scopes'],[])
    def test_legacy_module_constraints_are_not_ignored(self):
        for modules in (None, ['quality'], ['unknown'], {}):
            products=self.products_with_scopes();products[0]['modules_enabled']=modules
            with patch.object(h.sso,'_serialize_product_entitlements',return_value=products):
                token=self.issue();_,body=self.inspect(token)
            self.assertEqual(body['authorization']['state'],'denied')
    def test_global_admin_role_is_not_product_grant(self):
        products=self.products_with_scopes(role='admin')
        with patch.object(h.sso,'_serialize_product_entitlements',return_value=products):
            token=self.issue();_,body=self.inspect(token)
        self.assertEqual(body['authorization']['state'],'denied')
    def test_entitlement_change_never_restores_revoked_session(self):
        products=self.products_with_scopes()
        with patch.object(h.sso,'_serialize_product_entitlements',return_value=products):
            token=self.issue();self.assertEqual(self.inspect(token)[1]['authorization']['state'],'active')
            products[0]['authorization_eligible']=False;self.assertEqual(self.inspect(token)[1]['authorization']['state'],'denied')
            session=self.records[self.data(token)['sid']];b.life.revoke_record(session,self.fence,'authority_entitlement')
            products[0]['authorization_eligible']=True;self.assert_denied(token)
    def test_request_scope_and_role_parameters_do_not_grant(self):
        products=self.products_with_scopes()
        with patch.object(h.sso,'_serialize_product_entitlements',return_value=products):
            token=self.issue();response,body=self.call(self.context(token=token,role='org_admin',scopes=['*']),h.sso.sso_introspect)
        self.assertEqual(response.status_code,200);self.assertEqual(body['authorization']['scopes'],[self.row.product.code+':resources.resource:read'])
    def test_service_credential_without_user_proof_has_no_functional_authority(self):
        response,body=self.call(self.context(scopes=['*']),h.sso.sso_introspect)
        self.assertEqual(response.status_code,400);self.assertNotIn('authorization',body)

class CommercialHoldTests(unittest.TestCase):
    def entitlement(self):
        org=NS(is_active=True,subscription_id=None,subscription=None)
        product=ProductSystem(code='ISO_SMART',status='active',billing_enabled=False)
        e=OrganizationProductEntitlement(product=product,status='active',enabled=True,starts_at=h.timezone.now()-timedelta(seconds=1))
        e._state.fields_cache['organization']=org
        return e
    def test_explicit_nonbilled_active_product_allowed(self):self.assertTrue(entitlement_eligible(self.entitlement()))
    def test_unadjudicated_nonbilled_trial_without_subscription_held(self):
        e=self.entitlement();e.status='trial'
        self.assertFalse(entitlement_eligible(e))
    def test_future_start_and_end_boundary_denied(self):
        e=self.entitlement();e.starts_at=h.timezone.now()+timedelta(days=1);self.assertFalse(entitlement_eligible(e))
        e.starts_at=h.timezone.now()-timedelta(days=1);e.ends_at=h.timezone.now();self.assertFalse(entitlement_eligible(e))
    def test_trial_without_subscription_held(self):
        e=self.entitlement();e.product.billing_enabled=True;e.status='trial';self.assertFalse(entitlement_eligible(e))
    def test_subscription_other_tenant_link_denied(self):
        e=self.entitlement();e.subscription_id=uuid.uuid4();e._state.fields_cache['subscription']=NS(pk=e.subscription_id,is_active=True,status='active')
        self.assertFalse(entitlement_eligible(e))
    def test_canonical_active_subscription_and_window(self):
        e=self.entitlement();e.product.billing_enabled=True;pk=uuid.uuid4();sub=NS(pk=pk,is_active=True,status='active',current_period_start=None,current_period_end=None)
        e.organization.subscription_id=pk;e.organization.subscription=sub
        self.assertTrue(entitlement_eligible(e))
        sub.current_period_start=h.timezone.now()+timedelta(days=1);self.assertFalse(entitlement_eligible(e))
        sub.current_period_start=None;sub.current_period_end=h.timezone.now()-timedelta(days=1);self.assertFalse(entitlement_eligible(e))
    def test_inactive_product_tenant_entitlement_denied(self):
        for field,value in [('enabled',False),('status','suspended')]:
            e=self.entitlement();setattr(e,field,value);self.assertFalse(entitlement_eligible(e))
        e=self.entitlement();e.product.status='retired';self.assertFalse(entitlement_eligible(e))
        e=self.entitlement();e.organization.is_active=False;self.assertFalse(entitlement_eligible(e))

if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (AuthorizationTests,CommercialHoldTests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),database_attempts=h.DB_GUARD.call_count,network_attempts=sum(g.call_count for g in h.NETWORK_GUARDS))))
    sys.exit(bool(result.failures or result.errors or h.DB_GUARD.call_count or any(g.call_count for g in h.NETWORK_GUARDS)))
