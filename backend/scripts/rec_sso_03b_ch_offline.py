"""CH endpoint contracts. Synthetic RSA, mocked persistence, no DB/network."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path.cwd()
spec = importlib.util.spec_from_file_location('historical', ROOT / 'backend/scripts/rec_sso_02_offline.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from apps.integration import client_registry as registry
from apps.integration import trust_jwt as crypto
from apps.integration.models import IntegrationAPIKey, SSOClient


def keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return (key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode(),
            key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode())


PRIVATE, PUBLIC = keypair()
TRUST = {'ALGORITHM': 'RS256', 'ISSUER': 'https://central.invalid', 'SIGNING_KID': 'synthetic-central',
         'PRIVATE_KEY': PRIVATE, 'PUBLIC_KEYS': {'synthetic-central': PUBLIC}}
GEN = 'dddddddd-dddd-4ddd-8ddd-dddddddddddd'


class CHTests(h.Fixture):
    def setUp(self):
        super().setUp()
        self.user._state.fields_cache['two_factor_auth'] = None
        self.mock(h.settings, 'SSO_CENTRAL_TRUST', create=True, new=TRUST.copy())
        self.principal = IntegrationAPIKey(id=11, name='synthetic-iso', status='active', is_active=True,
                                          credential_format='hashed_v1')
        self.row = NS(client_id='iso-client', principal=self.principal, product=h.ProductSystem(code='ISO_SMART', status='active'),
                      audience='iso-central', issuer=TRUST['ISSUER'], enabled=True, token_family='CENTRAL',
                      algorithm='RS256', allowed_kids=['synthetic-central'], credential_policy='hashed_v1',
                      contract_version=crypto.CONTRACT, tenants=MagicMock())
        self.tenant_allowed = True
        self.row.tenants.filter.side_effect = lambda **kw: NS(exists=lambda: self.tenant_allowed and str(kw['pk']) == str(self.org.id))
        self.credential = self.mock(registry, 'authenticate_integration_api_key', return_value=self.principal)
        self.rows = self.mock(SSOClient.objects, 'select_related')
        self.rows.return_value.get.return_value = self.row
        self.products.return_value = [{'code': 'ISO_SMART', 'access_allowed': True}, {'code': 'MEDSUPPLIER', 'access_allowed': True}]
        self.mock(h.sso.two_factor, 'require_commit_boundary')

    def context(self, **changes):
        data = {'client_id': self.row.client_id, 'product': self.row.product.code, 'audience': [self.row.audience],
                'contract_version': crypto.CONTRACT}
        data.update(changes)
        return data

    def issue(self):
        return h.sso._build_token_pair(self.user, self.member, [self.member], audience=[self.row.audience],
                                      client_id=self.row.client_id, client=registry.ClientContract.from_row(self.row),
                                      authentication_methods=['pwd'])['access_token']

    def call(self, payload, view=None, key=True):
        response = self.post(view or h.sso.sso_introspect, payload, key=key)
        return response, json.loads(response.content)

    def inspect(self, token=None, **changes):
        return self.call(self.context(token=token or self.issue(), **changes))

    def resign(self, **changes):
        data = h.jwt.decode(self.issue(), PUBLIC, algorithms=['RS256'], audience=self.row.audience)
        for key, value in changes.items():
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
        return h.jwt.encode(data, PRIVATE, algorithm='RS256', headers={'kid': 'synthetic-central'})

    def test_valid_contract_least_privilege(self):
        response, body = self.inspect()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body['active'])
        self.assertEqual(body['role'], 'viewer')
        self.assertEqual(body['sub'], str(h.USER))
        self.assertEqual(body['tenant_id'], str(h.ORG))
        self.assertEqual(body['products'], [{'code': 'ISO_SMART', 'access_allowed': True}])
        self.assertNotIn('scope', body)

    def test_impersonation_both_directions(self):
        for own, other in [('ISO_SMART', 'MEDSUPPLIER'), ('MEDSUPPLIER', 'ISO_SMART')]:
            self.row.product.code = own
            for changes in ({'client_id': 'another'}, {'product': other}, {'audience': ['another']}, {'contract_version': 'decision-a-v1'}):
                with self.subTest(own=own, changes=changes):
                    response, body = self.inspect(**changes)
                    self.assertEqual(response.status_code, 401)
                    self.assertFalse(body['active'])

    def test_missing_contract_fields_and_credentials(self):
        for field in ('client_id', 'audience', 'product', 'contract_version'):
            data = self.context(token=self.issue()); data.pop(field)
            self.assertEqual(self.call(data)[0].status_code, 401)
        self.assertEqual(self.call(self.context(), key=False)[0].status_code, 401)
        for principal in (None, 'legacy-config-service', IntegrationAPIKey(id=99, credential_format='legacy_plaintext')):
            self.credential.return_value = principal
            self.assertEqual(self.call(self.context())[0].status_code, 401)

    def test_wrong_credential_binding(self):
        self.credential.return_value = IntegrationAPIKey(id=22, credential_format='hashed_v1', status='active', is_active=True)
        self.assertEqual(self.inspect()[0].status_code, 401)

    def test_unknown_disabled_revoked_clients(self):
        self.rows.return_value.get.side_effect = SSOClient.DoesNotExist
        self.assertEqual(self.inspect()[0].status_code, 401)
        self.rows.return_value.get.side_effect = None
        proof = self.issue()
        for obj, field, value in [(self.row, 'enabled', False), (self.principal, 'is_active', False),
                                   (self.principal, 'status', 'revoked'), (self.principal, 'status', 'rotated')]:
            with patch.object(obj, field, value):
                self.assertEqual(self.inspect(proof)[0].status_code, 401)

    def test_tenant_user_membership_revocation(self):
        proof = self.issue()
        self.tenant_allowed = False
        self.assertEqual(self.inspect(proof)[0].status_code, 401)
        self.tenant_allowed = True
        for obj, field, value in [(self.org, 'status', 'disabled'), (self.user, 'is_active', False),
                                   (self.member, 'is_active', False), (self.member, 'role', 'admin')]:
            with patch.object(obj, field, value):
                self.assertFalse(self.inspect(proof)[1]['active'])
        self.assertFalse(self.inspect(self.resign(organization_id=str(h.OTHER), tenant_id=str(h.OTHER)))[1]['active'])

    def test_claim_matrix(self):
        for key, value in [('aud', None), ('aud', ['unknown']), ('aud', 'iso-central'), ('aud', ['iso-central', 'other']),
                           ('iss', None), ('iss', 'https://foreign.invalid'), ('sub', None), ('sub', 'not-uuid'),
                           ('tenant_id', None), ('organization_id', str(h.OTHER)), ('product', 'MEDSUPPLIER'),
                           ('token_family', 'LOCAL'), ('auth_contract', 'decision-a-v1'), ('amr', []),
                           ('exp', int(time.time()) - 5), ('exp', True), ('iat', int(time.time()) + 99),
                           ('token_type', 'refresh'), ('jti', None)]:
            with self.subTest(key=key, value=value):
                self.assertFalse(self.inspect(self.resign(**{key: value}))[1]['active'])

    def test_signature_algorithm_and_kid(self):
        token = self.issue()
        data = h.jwt.decode(token, PUBLIC, algorithms=['RS256'], audience=self.row.audience)
        bad = [token[:-20] + ('A' if token[-20] != 'A' else 'B') + token[-19:],
               h.jwt.encode(data, '', algorithm='none', headers={'kid': 'synthetic-central'}),
               h.jwt.encode(data, 'synthetic-hmac-secret-never-deploy', algorithm='HS256', headers={'kid': 'synthetic-central'}),
               h.jwt.encode(data, PRIVATE, algorithm='RS256', headers={'kid': 'unknown'}),
               h.jwt.encode(data, PRIVATE, algorithm='RS256'),
               h.jwt.encode(data, PRIVATE, algorithm='RS256', headers={'kid': 'synthetic-central', 'jku': 'https://evil.invalid'})]
        foreign, _ = keypair()
        bad.append(h.jwt.encode(data, foreign, algorithm='RS256', headers={'kid': 'synthetic-central'}))
        for token in bad:
            self.assertFalse(self.inspect(token)[1]['active'])

    def test_unconfigured_or_database_down_sanitized(self):
        proof = self.issue()
        with patch.object(h.settings, 'SSO_CENTRAL_TRUST', {}):
            response, body = self.inspect(proof)
            self.assertEqual(response.status_code, 503)
            self.assertFalse(body['active'])
        self.rows.side_effect = h.DatabaseError('private-schema-secret')
        response, body = self.inspect(proof)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private-schema', json.dumps(body))

    def test_registry_rejects_unapproved_crypto(self):
        proof = self.issue()
        for key, value in [('algorithm', 'HS256'), ('allowed_kids', []), ('allowed_kids', ['foreign']),
                           ('issuer', 'https://foreign.invalid'), ('token_family', 'LOCAL'),
                           ('credential_policy', 'legacy'), ('contract_version', 'decision-a-v1')]:
            with patch.object(self.row, key, value):
                self.assertFalse(self.inspect(proof)[1]['active'])

    def test_mfa_live_generation(self):
        proof = self.issue()
        self.user._state.fields_cache['two_factor_auth'] = NS(is_enabled=True, generation=GEN)
        self.assertFalse(self.inspect(proof)[1]['active'])
        self.assertTrue(self.inspect(self.resign(amr=['pwd', 'otp'], mfa_generation=GEN))[1]['active'])
        self.assertFalse(self.inspect(self.resign(amr=['pwd', 'otp'], mfa_generation='foreign'))[1]['active'])

    def test_login_real_emission_and_tenant(self):
        with patch.object(h.sso, '_auth_user', return_value=self.user), patch.object(self.user, 'save'), \
             patch.object(h.sso.two_factor, 'validate_user_eligibility'):
            response, body = self.call(self.context(email=self.user.email, password='synthetic', organization_id=str(h.ORG)), h.sso.sso_login)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.inspect(body['tokens']['access_token'])[1]['active'])
            self.tenant_allowed = False
            self.assertEqual(self.call(self.context(email=self.user.email, password='synthetic'), h.sso.sso_login)[0].status_code, 401)

    def test_login_response_does_not_disclose_other_tenants(self):
        other = NS(organization=NS(id=h.OTHER, name='Other tenant', code='OTHER'),
                   organization_id=h.OTHER, role='org_admin', is_primary=False)
        self.members.side_effect = None
        self.members.return_value.select_related.return_value = [self.member, other]
        with patch.object(h.sso, '_auth_user', return_value=self.user), patch.object(self.user, 'save'), \
             patch.object(h.sso.two_factor, 'validate_user_eligibility'):
            response, body = self.call(self.context(email=self.user.email, password='synthetic'), h.sso.sso_login)
            self.assertEqual(response.status_code, 200)
            self.assertEqual([m['id'] for m in body['organizations']], [str(h.ORG)])
            claims = h.jwt.decode(body['tokens']['access_token'], PUBLIC, algorithms=['RS256'], audience=self.row.audience)
            self.assertEqual([m['id'] for m in claims['memberships']], [str(h.ORG)])
            self.assertEqual(claims['allowed_products'], ['ISO_SMART'])

    def test_challenge_binding_before_irreversible_consume(self):
        challenge = dict(self.context(), user_id=str(h.USER), organization_id=str(h.ORG), principal_id=11, generation=GEN)
        for key, value in [('principal_id', 22), ('product', 'MEDSUPPLIER'), ('client_id', 'other'),
                           ('contract_version', 'decision-a-v1'), ('audience', ['other'])]:
            with patch.object(h.sso.two_factor, 'decode_challenge', return_value=dict(challenge, **{key: value})), \
                 patch.object(h.sso.two_factor, 'consume_challenge') as consume:
                self.assertEqual(self.call(self.context(challenge_token='synthetic', otp_code='123456'), h.sso.sso_login_verify_2fa)[0].status_code, 403)
                consume.assert_not_called()

    def test_verify_valid_and_postconsume_failure_no_restoration(self):
        challenge = dict(self.context(), user_id=str(h.USER), organization_id=str(h.ORG), principal_id=11, generation=GEN)
        with patch.object(h.sso.two_factor, 'decode_challenge', return_value=challenge), \
             patch.object(h.sso.two_factor, 'consume_challenge', return_value=(self.user, 'totp')) as consume, patch.object(self.user, 'save'):
            response, body = self.call(self.context(challenge_token='synthetic', otp_code='123456'), h.sso.sso_login_verify_2fa)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(h.jwt.decode(body['tokens']['access_token'], PUBLIC, algorithms=['RS256'], audience=self.row.audience)['amr'], ['pwd', 'otp'])
            with patch.object(h.sso, '_build_token_pair', side_effect=h.APIException('Unable to complete authentication')):
                self.assertEqual(self.call(self.context(challenge_token='synthetic', otp_code='123456'), h.sso.sso_login_verify_2fa)[0].status_code, 500)
            self.assertEqual(consume.call_count, 2)

    def test_api_key_real_hash_lifecycle(self):
        from apps.integration import services
        from django.contrib.auth.hashers import make_password
        raw = 'synthetic-unprefixed-offline'
        self.principal.credential_hash = make_password(raw)
        # Execute the real verifier; the database returns only eligible active rows.
        with patch.object(IntegrationAPIKey.objects, 'filter') as query:
            query.return_value.iterator.return_value = [self.principal]
            self.assertIs(services.authenticate_integration_api_key(raw), self.principal)
            query.return_value.iterator.return_value = []
            query.return_value.first.return_value = None
            with patch.object(h.settings, 'INTEGRATION_API_KEYS', {}, create=True):
                self.assertIsNone(services.authenticate_integration_api_key('wrong-synthetic'))

    def test_schema_state_matches_models_without_database(self):
        from django.db.migrations.loader import MigrationLoader
        from django.db.migrations.autodetector import MigrationAutodetector
        from django.db.migrations.state import ProjectState
        from django.db.migrations.questioner import MigrationQuestioner
        from django.apps import apps
        loader = MigrationLoader(None)
        changes = MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps),
                                       MigrationQuestioner({'ask_initial': False})).changes(graph=loader.graph)
        self.assertNotIn('integration', changes)

    def test_coordinated_cross_product_consumers(self):
        proofs = {}
        for repo, product, client, audience in [('isosmart', 'ISO_SMART', 'iso-client', 'iso-central'),
                                               ('ISO_Smart_MedSupplier', 'MEDSUPPLIER', 'med-client', 'med-central')]:
            self.row.client_id, self.row.audience, self.row.product.code = client, audience, product
            if product == 'MEDSUPPLIER':
                self.user.id = h.OTHER
                self.org.id = 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee'
                self.member.organization_id = self.org.id
                self.principal.id = 22
            token = self.issue()
            body = self.inspect(token)[1]
            proofs[repo] = {'proof': token, 'introspection': body, 'client_id': client, 'audience': audience}
        for repo, own in proofs.items():
            foreign = proofs[next(k for k in proofs if k != repo)]
            payload = {'public_key': PUBLIC, 'own': own, 'foreign': foreign}
            backend = ROOT.parent / repo / 'backend'
            result = subprocess.run([str(backend / '.venv/bin/python'), '-B', 'integration/tests_ch_offline.py', '--coordinated'],
                                    cwd=backend, input=json.dumps(payload), text=True, capture_output=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('CROSS_PRODUCT_PASS', result.stdout)
            print(result.stdout.strip())


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CHTests))
    summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'database_attempts': h.DB_GUARD.call_count, 'network_attempts': sum(x.call_count for x in h.NETWORK_GUARDS),
               'scope': 'offline real endpoints/codec, mocked ORM; NOT HTTP E2E'}
    print(json.dumps(summary))
    sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
