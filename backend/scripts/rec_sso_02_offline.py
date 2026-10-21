"""REC-SSO-02: standalone offline contract probes, never an E2E suite.

Run: backend/.venv/bin/python -B backend/scripts/rec_sso_02_offline.py
Use --group local|decisions|consumers and --output PATH for durable JSON evidence.
Decision probes intentionally FAIL until an approved contract is implemented.
No expectedFailure/skip masks a security finding. No project settings/.env read.
"""

import argparse
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import socket
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import MagicMock, patch
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
# Install before Django setup or importing any consumer module.
NETWORK_GUARDS = []
for target in ('socket.socket.connect', 'socket.socket.connect_ex',
               'socket.create_connection', 'socket.getaddrinfo'):
    guard = patch(target, side_effect=AssertionError('Network forbidden'))
    NETWORK_GUARDS.append(guard.start())

from django.conf import settings  # noqa: E402

KEY = 'synthetic-rec-sso-02-signing-key-never-for-deployment'
ISSUER = 'https://sso.smart3ai.local'
settings.configure(
    SECRET_KEY=KEY,
    SMART3AI_SSO_ISSUER=ISSUER,
    INSTALLED_APPS=[
        'django.contrib.auth', 'django.contrib.contenttypes',
        'apps.users', 'apps.organizations', 'apps.products',
        'apps.subscriptions', 'apps.integration',
        'rest_framework_simplejwt.token_blacklist',
    ],
    AUTH_USER_MODEL='users.User',
    DATABASES={'default': {'ENGINE': 'django.db.backends.dummy'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    LOGGING_CONFIG=None,
    USE_TZ=True,
    SIMPLE_JWT={
        'ALGORITHM': 'HS256', 'SIGNING_KEY': KEY,
        'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
        'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    },
)
from django.db.backends.base.base import BaseDatabaseWrapper  # noqa: E402

DB_GUARD = patch.object(BaseDatabaseWrapper, 'connect',
                        side_effect=AssertionError('Database forbidden')).start()
import django  # noqa: E402

django.setup()
from django.db import DatabaseError  # noqa: E402
from django.test import RequestFactory, override_settings  # noqa: E402
from django.utils import timezone  # noqa: E402
import jwt  # noqa: E402
from rest_framework.exceptions import APIException, ValidationError  # noqa: E402
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken  # noqa: E402
from apps.integration import sso_views as sso, views  # noqa: E402
from apps.organizations.models import Organization  # noqa: E402
from apps.products.models import OrganizationProductEntitlement, ProductSystem  # noqa: E402
from apps.products.serializers import OrganizationProductEntitlementSerializer  # noqa: E402
from apps.subscriptions.models import Subscription  # noqa: E402
from apps.users.models import User  # noqa: E402

ORG = uuid.UUID('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
OTHER = uuid.UUID('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb')
USER = uuid.UUID('cccccccc-cccc-4ccc-8ccc-cccccccccccc')


def entitlement(**changes):
    organization = Organization(id=ORG, name='Synthetic', status='active')
    organization.subscription = None
    product = ProductSystem(code='ISO_SMART', name='ISO Smart', status='active',
                            billing_enabled=False)
    result = OrganizationProductEntitlement(organization=organization, product=product,
                                           enabled=True, status='active')
    for key, value in changes.items():
        setattr(result, key, value)
    return result


class Fixture(unittest.TestCase):
    def setUp(self):
        self.user = User(id=USER, email='synthetic@example.invalid',
                         first_name='Synthetic', last_name='User', is_active=True)
        self.org = Organization(id=ORG, name='Synthetic', code='SYN', status='active')
        self.member = NS(user=self.user, organization=self.org, organization_id=ORG,
                         role='viewer', is_active=True, is_primary=True)
        self.deleted_user = False
        self.deleted_member = False
        self.auth = self.mock(views, 'authenticate_integration_api_key',
                              return_value='synthetic-service')
        self.users = self.mock(sso.User.objects, 'get', side_effect=self.get_user)
        self.members = self.mock(sso.UserOrganization.objects, 'filter',
                                 side_effect=self.get_members)
        self.products = self.mock(sso, '_serialize_product_entitlements', return_value=[])

    def mock(self, target, attribute, **kwargs):
        item = patch.object(target, attribute, **kwargs)
        self.addCleanup(item.stop)
        return item.start()

    def get_user(self, **filters):
        if self.deleted_user or not all(
            str(getattr(self.user, key)) == str(value) for key, value in filters.items()
        ):
            raise User.DoesNotExist
        return self.user

    def get_members(self, **filters):
        def matches(key, value):
            actual = self.org.status if key == 'organization__status' else getattr(self.member, key)
            return actual == value or str(actual) == str(value)
        rows = [] if self.deleted_member or not all(matches(k, v) for k, v in filters.items()) else [self.member]
        result = MagicMock()
        result.exists.return_value = bool(rows)
        result.first.return_value = rows[0] if rows else None
        result.select_related.return_value = result
        result.filter.side_effect = lambda **extra: self.get_members(**dict(filters, **extra))
        result.__iter__.side_effect = lambda: iter(rows)
        return result

    def token(self, **claims):
        result = AccessToken()
        result['iss'] = ISSUER
        result['aud'] = ['isosmart']
        result['client_id'] = 'isosmart'
        result['user_id'] = str(USER)
        result['organization_id'] = str(ORG)
        result['role'] = self.member.role
        for key, value in claims.items():
            if value is None:
                del result[key]
            else:
                result[key] = value
        return str(result)

    def post(self, view, data, key=True):
        return view(RequestFactory().post(
            '/', json.dumps(data), content_type='application/json',
            **({'HTTP_X_API_KEY': 'synthetic-key'} if key else {}),
        ))

    def introspect(self, token=None):
        try:
            response = self.post(sso.sso_introspect, {'token': token or self.token()})
        except DatabaseError:
            self.fail('DatabaseError escapes introspection')
        return response, json.loads(response.content)

    def assert_inactive(self, token):
        response, body = self.introspect(token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body, {'active': False})

    def issue(self, role='viewer', products=None):
        self.member.role = role
        self.products.return_value = products or []
        with patch.object(sso.two_factor, 'require_commit_boundary'), \
             patch.object(sso.RefreshToken, 'for_user', return_value=RefreshToken()):
            return sso._build_token_pair(self.user, self.member, [self.member],
                                         audience=['isosmart'], client_id='isosmart')


class LocalFixTests(Fixture):
    def test_live_user_revocation(self):
        token = self.token()
        self.assertTrue(self.introspect(token)[1]['active'])
        self.user.is_active = False
        self.assert_inactive(token)

    def test_deleted_user(self):
        token = self.token()
        self.deleted_user = True
        self.assert_inactive(token)

    def test_live_membership_revocation(self):
        token = self.token()
        self.assertTrue(self.introspect(token)[1]['active'])
        self.member.is_active = False
        self.assert_inactive(token)

    def test_deleted_membership(self):
        token = self.token()
        self.deleted_member = True
        self.assert_inactive(token)

    def test_live_organization_revocation(self):
        token = self.token()
        self.org.status = 'suspended'
        self.assert_inactive(token)

    def test_missing_tenant(self):
        self.assert_inactive(self.token(organization_id=None))
        self.products.assert_not_called()

    def test_foreign_tenant(self):
        self.assert_inactive(self.token(organization_id=str(OTHER)))
        self.products.assert_not_called()

    def test_missing_subject(self):
        self.assert_inactive(self.token(user_id=None))

    def test_invalid_identifiers(self):
        for field in ('user_id', 'organization_id'):
            for value in ('invalid-uuid', ['bad'], True, ''):
                with self.subTest(field=field, value=value):
                    self.assert_inactive(self.token(**{field: value}))

    def test_wrong_issuer(self):
        self.assert_inactive(self.token(iss='https://untrusted.example.invalid'))

    def test_missing_issuer(self):
        self.assert_inactive(self.token(iss=None))

    def test_valid_response_contract(self):
        response, body = self.introspect()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(body['active'])
        self.assertEqual(body['sub'], str(USER))
        self.assertEqual(body['organization_id'], str(ORG))
        self.assertEqual(set(body), {
            'active', 'sub', 'email', 'full_name', 'role', 'organization_id',
            'organization_name', 'organization_code', 'memberships', 'products',
            'client_id', 'aud', 'iss', 'exp', 'iat',
        })
        self.products.assert_called_once_with(str(ORG))

    def test_product_revocation_reloaded(self):
        token = self.token()
        self.products.side_effect = [[{'access_allowed': True}], [{'access_allowed': False}]]
        self.assertTrue(self.introspect(token)[1]['products'][0]['access_allowed'])
        self.assertFalse(self.introspect(token)[1]['products'][0]['access_allowed'])

    def test_database_failures_are_closed_and_sanitized(self):
        for boundary in (self.auth, self.users, self.members, self.products):
            original = boundary.side_effect
            with self.subTest(boundary=boundary._mock_name):
                boundary.side_effect = DatabaseError('private-db-detail')
                response, body = self.introspect()
                self.assertEqual(response.status_code, 503)
                self.assertIs(body.get('active'), False)
                self.assertNotIn(b'private-db-detail', response.content)
                self.assertNotIn('products', body)
            boundary.side_effect = original

    def test_api_key_usage_write_failure_is_closed(self):
        self.auth.return_value = views.IntegrationAPIKey(name='synthetic-service')
        with patch.object(views.IntegrationAPIKey, 'save', side_effect=DatabaseError('private')):
            response, body = self.introspect()
        self.assertEqual(response.status_code, 503)
        self.assertIs(body.get('active'), False)
        self.products.assert_not_called()

    def test_bad_signature_expiry_and_refresh_rejected(self):
        payload = AccessToken(self.token()).payload
        for token in ('invalid', jwt.encode(payload, KEY + '-wrong', algorithm='HS256'),
                      jwt.encode(dict(payload, exp=1), KEY, algorithm='HS256'), str(RefreshToken())):
            with self.subTest(kind=token[:6]):
                self.assert_inactive(token)

    def test_api_key_required_and_invalid_denied(self):
        response = self.post(sso.sso_introspect, {'token': self.token()}, key=False)
        self.assertEqual(response.status_code, 401)
        self.auth.return_value = None
        self.assertEqual(self.introspect()[0].status_code, 401)
        self.products.assert_not_called()

    def test_product_database_error_prevents_issuance(self):
        with patch.object(sso.two_factor, 'require_commit_boundary'), \
             patch.object(sso, '_build_product_claims', side_effect=DatabaseError('private')), \
             patch.object(sso.RefreshToken, 'for_user') as issue:
            with self.assertRaises(APIException) as caught:
                sso._build_token_pair(self.user, self.member, [], audience=['isosmart'], client_id='isosmart')
        self.assertNotIn('private', str(caught.exception.detail))
        issue.assert_not_called()

    def test_sso_2fa_enabled_never_issues_without_factor(self):
        user = NS(is_active=True, is_locked=False, get_temporary_password_expiry=lambda: None,
                  id=USER, email='synthetic@example.invalid', full_name='Synthetic User',
                  two_factor_auth=NS(is_enabled=True))
        self.member.user = user
        with patch.object(sso, '_auth_user', return_value=user), \
             patch.object(sso.two_factor, 'issue_challenge', return_value='synthetic-challenge'), \
             patch.object(sso, '_build_token_pair') as issue:
            response = self.post(sso.sso_login, {'email': user.email, 'password': 'synthetic'})
        self.assertTrue(json.loads(response.content)['requires_2fa'])
        issue.assert_not_called()

    def test_entitlement_denial_and_allowed_products(self):
        for code in ('ISO_SMART', 'MEDSUPPLIER'):
            e = entitlement()
            e.product.code = code
            for attrs in ({'enabled': False}, {'status': 'suspended'}, {'status': 'cancelled'},
                          {'ends_at': timezone.now() - timedelta(seconds=1)}):
                with self.subTest(code=code, attrs=attrs):
                    denied = entitlement(**attrs)
                    self.assertFalse(denied.access_allowed)
            products = [{'code': code, 'access_allowed': True},
                        {'code': 'DISABLED', 'access_allowed': False}]
            pair = self.issue(products=products)
            self.assertEqual(AccessToken(pair['access_token'])['allowed_products'], [code])


class DecisionTests(Fixture):
    def test_legacy_2fa_requires_second_factor(self):
        user = NS(id=str(USER), email='synthetic@example.invalid', first_name='Synthetic',
                  last_name='User', is_active=True, two_factor_auth=NS(is_enabled=True))
        self.member.user = user
        with patch.object(views, 'authenticate', return_value=user):
            response = self.post(views.validate_credentials, {'email': user.email, 'password': 'synthetic'})
        self.assertFalse(json.loads(response.content).get('valid', False))

    def test_wrong_audience_is_rejected(self):
        self.assert_inactive(self.token(aud=['unregistered-product']))

    def test_missing_audience_is_rejected(self):
        self.assert_inactive(self.token(aud=None))

    def test_viewer_and_auditor_never_receive_write_scope(self):
        for role in ('viewer', 'auditor'):
            with self.subTest(role=role):
                token = AccessToken(self.issue(role)['access_token'])
                self.assertNotIn('tenant:write', token['scope'].split())

    def test_write_scope_requires_entitlement(self):
        token = AccessToken(self.issue('org_admin', products=[
            {'code': 'ISO_SMART', 'access_allowed': False, 'scopes': []},
        ])['access_token'])
        self.assertNotIn('tenant:write', token['scope'].split())

    def test_role_revocation_does_not_return_old_role(self):
        token = self.token(role='org_admin')
        self.member.role = 'viewer'
        _, body = self.introspect(token)
        self.assertTrue(not body['active'] or body['role'] == 'viewer')

    def test_trial_requires_subscription_candidate(self):
        e = entitlement(status='trial')
        e.product.billing_enabled = True
        self.assertFalse(e.access_allowed)

    def test_future_start_denies_candidate(self):
        self.assertFalse(entitlement(starts_at=timezone.now() + timedelta(days=1)).access_allowed)

    def test_foreign_subscription_denies_candidate(self):
        e = entitlement()
        e.product.billing_enabled = True
        subscription = Subscription(status='active')
        other_org = Organization(id=OTHER, subscription=subscription)
        self.assertNotEqual(other_org.id, e.organization_id)
        attrs = {'organization': e.organization, 'product': e.product,
                 'subscription': subscription, 'status': 'active', 'enabled': True}
        try:
            OrganizationProductEntitlementSerializer().validate(attrs)
        except ValidationError:
            return
        e.subscription = subscription
        self.assertFalse(e.access_allowed)


class ConsumerTests(unittest.TestCase):
    def clients(self):
        for repo, code in (('isosmart', 'ISO_SMART'), ('ISO_Smart_MedSupplier', 'MEDSUPPLIER')):
            path = ROOT.parent.parent / repo / 'backend/integration/client.py'
            spec = importlib.util.spec_from_file_location('rec_sso_02_' + repo, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            yield module.AdminAppsClient(), code

    @override_settings(IS_PRODUCTION=True, ALLOW_LOCAL_AUTH_FALLBACK=False,
                       ADMIN_APPS_INTEGRATION={'ALLOW_LOCAL_FALLBACK': False})
    def test_outage_denies_both_products(self):
        for client, code in self.clients():
            with self.subTest(product=code), \
                 patch.object(client, '_resolve_adminapps_org_id', return_value=str(ORG)), \
                 patch.object(client, '_make_request', return_value={'error': 'offline'}):
                result = client.validate_product_access(str(ORG), code, use_cache=False)
                self.assertFalse(result['allowed'])
                self.assertEqual(result['source'], 'fail_closed')

    def test_canonical_tenant_and_product_request(self):
        for client, code in self.clients():
            with self.subTest(product=code), \
                 patch.object(client, '_resolve_adminapps_org_id', return_value=str(ORG)), \
                 patch.object(client, '_make_request', return_value={'allowed': True}) as transport:
                self.assertTrue(client.validate_product_access(17, code.lower(), use_cache=False)['allowed'])
                self.assertEqual(transport.call_args.args,
                                 ('GET', f'/organizations/{ORG}/products/{code}/validate/'))
                self.assertFalse(transport.call_args.kwargs['use_cache'])

    @override_settings(IS_PRODUCTION=False, ALLOW_LOCAL_AUTH_FALLBACK=True,
                       ADMIN_APPS_INTEGRATION={'ALLOW_LOCAL_FALLBACK': True})
    def test_explicit_denial_never_falls_back(self):
        for client, code in self.clients():
            with self.subTest(product=code), \
                 patch.object(client, '_resolve_adminapps_org_id', return_value=str(ORG)), \
                 patch.object(client, '_make_request', return_value={'allowed': False}), \
                 patch.object(client, '_validate_product_access_local') as fallback:
                self.assertFalse(client.validate_product_access(str(ORG), code)['allowed'])
                fallback.assert_not_called()


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = {}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes[test.id()] = 'PASS'

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes[test.id()] = 'FAIL'

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes[test.id()] = 'ERROR'

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err:
            self.outcomes[test.id()] = 'FAIL' if issubclass(err[0], AssertionError) else 'ERROR'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=('all', 'local', 'decisions', 'consumers'), default='all')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    groups = {'local': LocalFixTests, 'decisions': DecisionTests, 'consumers': ConsumerTests}
    selected = groups.values() if args.group == 'all' else [groups[args.group]]
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in selected)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    forbidden = DB_GUARD.call_count + sum(g.call_count for g in NETWORK_GUARDS)
    report = {
        'scope': 'offline unit and local consumer contracts; NOT E2E', 'group': args.group,
        'tests_run': result.testsRun, 'outcomes': result.outcomes,
        'passed': sum(v == 'PASS' for v in result.outcomes.values()),
        'failed': sum(v == 'FAIL' for v in result.outcomes.values()),
        'errors': sum(v == 'ERROR' for v in result.outcomes.values()),
        'database_connection_attempts': DB_GUARD.call_count,
        'network_attempts': sum(g.call_count for g in NETWORK_GUARDS),
        'success': result.wasSuccessful() and not forbidden,
    }
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'outcomes'}, indent=2))
    sys.exit(not report['success'])
