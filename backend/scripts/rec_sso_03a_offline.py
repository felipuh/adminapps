"""Successor Decision A contracts, without changing historical probes."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch,PropertyMock

ROOT=Path.cwd()
spec=importlib.util.spec_from_file_location('historical',ROOT/'backend/scripts/rec_sso_02_offline.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
sso=h.sso;views=h.views
GEN='dddddddd-dddd-4ddd-8ddd-dddddddddddd'

class CurrentFixture(h.Fixture):
    def setUp(self):
        super().setUp()
        self.user._state.fields_cache['two_factor_auth']=None
    def token(self,**claims):
        data={'auth_contract':'decision-a-v1','amr':['pwd']}
        data.update(claims)
        result=h.AccessToken(super().token())
        for key,value in data.items():
            if value is None: result.payload.pop(key,None)
            else: result[key]=value
        return str(result)
    def issue(self,role='viewer',products=None):
        self.member.role=role;self.products.return_value=products or []
        with patch.object(sso.two_factor,'require_commit_boundary'),patch.object(sso.RefreshToken,'for_user',return_value=h.RefreshToken()):
            return sso._build_token_pair(self.user,self.member,[self.member],audience=['isosmart'],client_id='isosmart',authentication_methods=['pwd'])

class CurrentLocal(h.LocalFixTests,CurrentFixture):
    def test_valid_response_contract(self):
        response,body=self.introspect()
        self.assertEqual(response.status_code,200)
        self.assertTrue(body['active'])
        self.assertEqual(body['sub'],str(h.USER))
        self.assertEqual(body['organization_id'],str(h.ORG))
        self.assertEqual(body['auth_contract'],'decision-a-v1')
        self.assertEqual(body['amr'],['pwd'])
        self.assertEqual(set(body),{'active','sub','email','full_name','role','organization_id',
            'organization_name','organization_code','memberships','products','client_id','aud','iss','exp','iat',
            'auth_contract','amr'})
        self.products.assert_called_once_with(str(h.ORG))

class DecisionATests(CurrentFixture):
    def legacy(self,authenticated=True):
        with patch.object(views,'authenticate',return_value=self.user if authenticated else None):
            return self.post(views.validate_credentials,{'email':self.user.email,'password':'synthetic'})
    def test_legacy_mfa_denied(self):
        self.user._state.fields_cache['two_factor_auth']=NS(is_enabled=True,generation=GEN)
        response=self.legacy()
        self.assertEqual(response.status_code,403)
        self.assertEqual(json.loads(response.content)['code'],'second_factor_required')
    def test_legacy_no_mfa_succeeds(self):
        response=self.legacy()
        self.assertEqual(response.status_code,200)
        self.assertIs(json.loads(response.content)['valid'],True)
    def test_legacy_wrong_password_does_not_disclose_mfa(self):
        self.user._state.fields_cache['two_factor_auth']=NS(is_enabled=True,generation=GEN)
        response=self.legacy(False)
        self.assertEqual(response.status_code,401)
        self.assertEqual(json.loads(response.content)['code'],'invalid_credentials')
    def test_legacy_mfa_lookup_and_key_db_fail_closed(self):
        with patch.object(views.User,'two_factor_auth',new_callable=PropertyMock,side_effect=h.DatabaseError('private-secret')):
            response=self.legacy()
            self.assertEqual(response.status_code,503)
            self.assertNotIn('private-secret',response.content.decode())
        self.auth.side_effect=h.DatabaseError('private-key')
        response=self.legacy()
        self.assertEqual(response.status_code,503)
        self.assertNotIn('private-key',response.content.decode())
    def test_old_token_requires_new_auth(self):
        self.assert_inactive(self.token(auth_contract=None))
    def test_mfa_enrollment_invalidates_password_only_proof(self):
        self.user._state.fields_cache['two_factor_auth']=NS(is_enabled=True,generation=GEN)
        self.assert_inactive(self.token())
    def test_valid_mfa_proof(self):
        self.user._state.fields_cache['two_factor_auth']=NS(is_enabled=True,generation=GEN)
        r,body=self.introspect(self.token(amr=['pwd','otp'],mfa_generation=GEN))
        self.assertTrue(body['active'])
        self.assertEqual(body['amr'],['pwd','otp'])
    def test_reset_disabled_or_foreign_generation_denied(self):
        for enabled,generation in ((False,GEN),(True,'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee')):
            self.user._state.fields_cache['two_factor_auth']=NS(is_enabled=enabled,generation=generation)
            self.assert_inactive(self.token(amr=['pwd','otp'],mfa_generation=GEN))
    def test_verify_foreign_context_does_not_consume(self):
        decoded={'user_id':str(h.USER),'organization_id':str(h.ORG),'client_id':'isosmart','audience':['isosmart'],'generation':GEN}
        with patch.object(sso.two_factor,'decode_challenge',return_value=decoded),patch.object(sso.two_factor,'consume_challenge') as consume,patch.object(sso,'_build_token_pair') as mint:
            for change in ({'client_id':'medsupplier'},{'audience':['medsupplier']}):
                response=self.post(sso.sso_login_verify_2fa,dict({'challenge_token':'synthetic','otp_code':'123456'},**change))
                self.assertEqual(response.status_code,403)
            consume.assert_not_called();mint.assert_not_called()
    def test_verify_complete_contract_and_generation(self):
        decoded={'user_id':str(h.USER),'organization_id':str(h.ORG),'client_id':'isosmart','audience':['isosmart'],'generation':GEN}
        with patch.object(self.user,'save'),patch.object(sso.two_factor,'decode_challenge',return_value=decoded),patch.object(sso.two_factor,'consume_challenge',return_value=(self.user,'totp')),patch.object(sso,'_build_token_pair',return_value={'access_token':'synthetic'}) as mint:
            response=self.post(sso.sso_login_verify_2fa,{'challenge_token':'synthetic','otp_code':'123456','client_id':'isosmart','audience':['isosmart']})
            self.assertEqual(response.status_code,200)
            self.assertIs(json.loads(response.content)['requires_2fa'],False)
            self.assertEqual(mint.call_args.kwargs['mfa_generation'],GEN)
            self.assertEqual(mint.call_args.kwargs['authentication_methods'],['pwd','otp'])

if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(x) for x in (CurrentLocal,DecisionATests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    summary={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'db_attempts':h.DB_GUARD.call_count,'network_attempts':sum(x.call_count for x in h.NETWORK_GUARDS),'scope':'offline successor contract; NOT E2E'}
    print(json.dumps(summary));sys.exit(not result.wasSuccessful() or summary['db_attempts'] or summary['network_attempts'])
