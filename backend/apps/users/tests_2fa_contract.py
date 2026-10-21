"""Offline REC-2FA-02/03A contracts, without database or network access.

Run from backend: .venv312/bin/python -B apps/users/tests_2fa_contract.py -v
The standalone bootstrap uses synthetic settings, a dummy database and local
cache. Signing, TOTP verification and SimpleJWT encoding/decoding are real;
ORM operations, transaction boundaries, audit writes and OutstandingToken
persistence are test doubles. The PostgreSQL suite proves actual atomicity.
This does not validate deployed keys, persistence, rotation or concurrency.
"""

import ast
from contextlib import nullcontext
from types import SimpleNamespace
import uuid
from datetime import datetime, timedelta, timezone as datetime_timezone
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import Mock, PropertyMock, patch


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from django.conf import settings

    settings.configure(
        SECRET_KEY='offline-only-rec-2fa-02-signing-secret',
        INSTALLED_APPS=[
            'django.contrib.auth', 'django.contrib.contenttypes',
            'apps.organizations', 'apps.users',
            'rest_framework_simplejwt.token_blacklist',
        ],
        AUTH_USER_MODEL='users.User',
        DATABASES={'default': {'ENGINE': 'django.db.backends.dummy'}},
        CACHES={'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }},
        USE_TZ=True,
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_CLASSES': [
                'rest_framework.throttling.AnonRateThrottle',
                'rest_framework.throttling.UserRateThrottle',
            ],
            'DEFAULT_THROTTLE_RATES': {'anon': '60/minute', 'user': '300/minute'},
        },
        SIMPLE_JWT={
            'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
            'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
            'ROTATE_REFRESH_TOKENS': True,
            'BLACKLIST_AFTER_ROTATION': True,
            'UPDATE_LAST_LOGIN': True,
            'ALGORITHM': 'HS256',
            'SIGNING_KEY': 'offline-only-rec-2fa-02-jwt-signing-key',
            'AUTH_HEADER_TYPES': ('Bearer',),
            'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
            'USER_ID_FIELD': 'id',
            'USER_ID_CLAIM': 'user_id',
        },
    )
    import django

    django.setup()

from django.core import signing
from django.core.cache import cache
from django.test import SimpleTestCase
from django.utils import timezone
import pyotp
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt import serializers as jwt_serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.organizations.models import Organization
from apps.users import rate_limit, views_2fa, two_factor_service as service
from apps.users.models import User
from apps.users.models_2fa import TwoFactorAuth, TwoFactorAuthLog, TwoFactorChallenge
from apps.users.serializers import CustomTokenObtainPairSerializer


class TwoFactorContractTests(SimpleTestCase):
    """No database setup: SimpleTestCase also forbids accidental DB queries."""

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.factory = APIRequestFactory()
        self.user = User(
            id=uuid.UUID('00000000-0000-0000-0000-000000000002'),
            email='offline@example.invalid', first_name='Offline',
            last_name='User', is_active=True, role='user', theme='light',
            organization=Organization(
                id='00000000-0000-0000-0000-000000000001', name='Offline Org',
                subscription_id=None,
            ),
        )
        self.user.record_login = Mock()
        self.two_fa = TwoFactorAuth(user=self.user, is_enabled=True)
        self.two_fa.secret = 'JBSWY3DPEHPK3PXP'
        self.two_fa.backup_codes = 'A1B2C3D4'
        self.two_fa.save = Mock()
        self.instant = datetime(2030, 1, 1, tzinfo=datetime_timezone.utc)
        totp = pyotp.TOTP(self.two_fa.secret)
        self.otp = totp.at(self.instant)
        self.start_patch(service, 'require_commit_boundary')
        self.start_patch(service.transaction, 'atomic', side_effect=lambda **kw: nullcontext())
        self.start_patch(service.timezone, 'now', return_value=self.instant)
        self.start_patch(User.objects, 'select_for_update', return_value=User.objects)
        self.start_patch(TwoFactorAuth.objects, 'select_for_update', return_value=TwoFactorAuth.objects)
        self.start_patch(TwoFactorAuth.objects, 'get', return_value=self.two_fa)
        self.rows = {}
        def create_row(**kwargs):
            row = SimpleNamespace(**kwargs, user_id=kwargs['user'].pk, consumed_at=None, save=Mock())
            self.rows[kwargs['nonce_digest']] = row
            return row
        def get_row(**kwargs):
            if kwargs['pk'] not in self.rows:
                raise TwoFactorChallenge.DoesNotExist
            return self.rows[kwargs['pk']]
        self.start_patch(TwoFactorChallenge.objects, 'create', side_effect=create_row)
        self.start_patch(TwoFactorChallenge.objects, 'select_for_update', return_value=TwoFactorChallenge.objects)
        self.start_patch(TwoFactorChallenge.objects, 'get', side_effect=get_row)
        self.factor_check = self.start_patch(service, '_factor', wraps=service._factor)
        self.lookup = self.start_patch(
            User.objects, 'get', side_effect=self.lookup_user,
        )
        self.audit = self.start_patch(TwoFactorAuthLog.objects, 'create')
        # Keep the project's blacklist-enabled issuer; intercept only its write.
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

        self.outstanding = self.start_patch(OutstandingToken.objects, 'create')
        self.issuer = self.start_patch(
            CustomTokenObtainPairSerializer, 'get_token',
            wraps=CustomTokenObtainPairSerializer.get_token,
        )

    def start_patch(self, target, name, **kwargs):
        patcher = patch.object(target, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def lookup_user(self, **kwargs):
        if str(kwargs.get('pk', kwargs.get('id'))) == str(self.user.id):
            return self.user
        raise User.DoesNotExist

    def challenge(self, **overrides):
        token = service.issue_challenge(self.user)
        if not overrides:
            return token
        payload = signing.loads(token, salt='adminapps.2fa.login')
        payload.update(overrides)
        return signing.dumps(payload, salt='adminapps.2fa.login')

    def post(self, otp=None, challenge=None, authenticated_user=None):
        headers = {}
        if challenge is not None:
            headers['HTTP_AUTHORIZATION'] = f'Bearer {challenge}'
        request = self.factory.post(
            '/api/auth/2fa/verify/',
            {'token': otp} if otp is not None else {}, format='json', **headers,
        )
        if authenticated_user is not None:
            force_authenticate(request, user=authenticated_user)
        return views_2fa.verify_2fa_token(request)

    def assert_rejected(self, response, code):
        self.assertEqual(response.status_code, code)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertNotIn('tokens', response.data)
        self.assertNotEqual(response.data.get('status'), 'verified')
        self.issuer.assert_not_called()
        self.outstanding.assert_not_called()
        self.user.record_login.assert_not_called()

    def test_2fa_b01_success_returns_signed_jwt_pair(self):
        for token in (self.otp, 'A1B2C3D4'):
            with self.subTest(factor='totp' if token == self.otp else 'backup'):
                self.issuer.reset_mock()
                self.outstanding.reset_mock()
                response = self.post(token, self.challenge())
                self.assertEqual(response.status_code, 200)
                self.issuer.assert_called_once_with(self.user)
                self.outstanding.assert_called_once()
                for kind in ('access', 'refresh'):
                    claims = token_backend.decode(response.data[kind], verify=True)
                    self.assertEqual(claims['token_type'], kind)
                    self.assertEqual(claims['user_id'], str(self.user.id))
                    for name in ('email', 'full_name', 'role'):
                        self.assertEqual(claims[name], getattr(self.user, name))
                    self.assertEqual(claims['organization_id'], str(self.user.organization.id))
                    self.assertEqual(claims['organization_name'], self.user.organization.name)
                    seconds = 8 * 3600 if kind == 'access' else 7 * 86400
                    self.assertEqual(claims['exp'] - claims['iat'], seconds)
        self.assertEqual(self.two_fa.backup_codes_used, [0])

    def test_2fa_b02_view_requires_second_factor_before_issuance(self):
        challenge = self.challenge()
        self.assert_rejected(self.post(challenge=challenge), 400)
        with self.assertRaises(TokenError):
            AccessToken(challenge)
        self.assert_rejected(self.post(self.otp), 403)
        self.two_fa.is_enabled = False
        self.assert_rejected(self.post(self.otp, challenge), 403)
        self.two_fa.is_enabled = True
        self.factor_check.assert_not_called()
        original = self.issuer._mock_wraps

        def issue_after_verification(user):
            self.factor_check.assert_called_once()
            self.assertEqual(self.factor_check.call_args.args[1], self.otp)
            return original(user)

        self.issuer.side_effect = issue_after_verification
        self.assertEqual(self.post(self.otp, challenge).status_code, 200)
        self.issuer.assert_called_once_with(self.user)

    def test_2fa_b03_wrong_otp_does_not_issue(self):
        wrong = '000000' if self.otp != '000000' else '111111'
        response = self.post(wrong, self.challenge())
        self.assert_rejected(response, 400)
        self.assertEqual(str(response.data['token']), 'Invalid OTP token or backup code')
        self.assertEqual(str(response.data['remaining_attempts']), '4')
        self.factor_check.assert_called_once()
        self.assertEqual(self.factor_check.call_args.args[1], wrong)
        self.assertEqual(self.audit.call_args.kwargs['event_type'], 'token_failed')

    def test_2fa_b04_expired_challenge_is_rejected(self):
        with patch('django.core.signing.time.time', return_value=1_900_000_000):
            challenge = self.challenge()
        with patch('django.core.signing.time.time', return_value=1_900_000_301):
            self.assert_rejected(self.post(self.otp, challenge), 403)
        self.assertEqual(self.lookup.call_count, 1)  # Issuance lookup only.
        self.factor_check.assert_not_called()

    def test_2fa_b05_signature_scope_purpose_and_identity_are_checked(self):
        signed = self.challenge()
        cases = [
            signed + 'tampered',
            signing.dumps({'user_id': str(self.user.id)}, salt='wrong-salt'),
            self.challenge(scope='access'), self.challenge(purpose='login'),
            self.challenge(user_id='00000000-0000-0000-0000-000000000099'),
        ]
        for challenge in cases:
            with self.subTest(case=cases.index(challenge)):
                self.assert_rejected(self.post(self.otp, challenge), 403)
        self.factor_check.assert_not_called()

    def test_2fa_b06_inactive_user_never_receives_jwt(self):
        challenge = self.challenge()
        self.user.is_active = False
        self.assert_rejected(self.post(self.otp, challenge), 403)
        self.lookup.assert_called_with(pk=str(self.user.id))
        # Authenticated identity alone cannot substitute for a nonce challenge.
        self.assert_rejected(self.post(self.otp, authenticated_user=self.user), 403)
        self.factor_check.assert_not_called()

    def test_2fa_b07_frontend_response_and_route_contract(self):
        response = self.post(self.otp, self.challenge())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {
            'status', 'message', 'user', 'remaining_attempts', 'access', 'refresh',
        })
        self.assertEqual(response.data['status'], 'verified')
        self.assertEqual(response.data['remaining_attempts'], 5)
        self.assertEqual(response.data['user']['id'], str(self.user.id))
        self.assertEqual(response.data['user']['avatar'], None)
        self.assertEqual(set(response.data['user']), {
            'id', 'email', 'full_name', 'role', 'organization_id',
            'organization_name', 'theme', 'avatar',
        })
        root = Path(__file__).resolve().parents[3]
        for relative in ('frontend/src/pages/LoginPage.jsx',
                         'frontend/src/hooks/useLoginWith2FA.js'):
            source = (root / relative).read_text()
            self.assertIn('response.access || response.tokens?.access', source)
            self.assertIn('response.refresh || response.tokens?.refresh', source)
        # Inspect routing without importing unrelated application views.
        routes = ast.parse(Path(__file__).with_name('urls.py').read_text())
        self.assertTrue(any(
            isinstance(node, ast.Call) and len(node.args) >= 2
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == '2fa/verify/'
            and isinstance(node.args[1], ast.Name)
            and node.args[1].id == 'verify_2fa_token'
            for node in ast.walk(routes)
        ))

    def test_2fa_b08_issuance_failure_has_no_partial_success(self):
        rate_limit.increment_two_fa_attempts(self.user)
        cases = [(factor, stage) for factor in ('totp', 'backup')
                 for stage in ('issuer', 'persistence', 'encoding')]
        for factor, stage in cases:
            with self.subTest(factor=factor, stage=stage):
                self.issuer.reset_mock()
                self.outstanding.reset_mock()
                self.issuer.side_effect = None
                self.outstanding.side_effect = None
                self.two_fa.backup_codes_used = []
                self.two_fa.last_totp_counter = None
                self.audit.reset_mock()
                failure = RuntimeError('synthetic sensitive internal detail')
                if stage == 'issuer':
                    self.issuer.side_effect = failure
                elif stage == 'persistence':
                    self.outstanding.side_effect = failure
                else:
                    broken = Mock()
                    type(broken).__str__ = Mock(side_effect=failure)
                    self.issuer.side_effect = lambda user: broken
                token = self.otp if factor == 'totp' else 'A1B2C3D4'
                with self.assertNoLogs('apps.users', level='INFO'):
                    response = self.post(token, self.challenge())
                self.assertEqual(response.status_code, 500)
                self.assertEqual(set(response.data), {'detail'})
                self.assertNotIn('synthetic sensitive', str(response.data))
                self.user.record_login.assert_not_called()
                self.audit.assert_called_once()
                self.assertEqual(rate_limit.get_two_fa_attempts(self.user), 0)
                self.assertTrue(any(row.consumed_at for row in self.rows.values()))
                if factor == 'backup':
                    self.assertEqual(self.two_fa.backup_codes_used, [0])

    def test_2fa_b09_existing_attempt_and_backup_reuse_controls(self):
        # Sequential contract test only; no assertion of real atomicity here.
        challenge = self.challenge()
        for attempt in range(1, 6):
            response = self.post('invalid', challenge)
            self.assert_rejected(response, 400)
            self.assertEqual(rate_limit.get_two_fa_attempts(self.user), attempt)
            self.assertEqual(str(response.data['remaining_attempts']), str(5 - attempt))
        self.factor_check.reset_mock()
        self.assert_rejected(self.post(self.otp, challenge), 403)
        self.factor_check.assert_not_called()
        self.assertEqual(self.two_fa.attempts_expires_at, self.instant + timedelta(minutes=15))
        self.two_fa.attempts_expires_at = self.instant
        self.assertEqual(self.post('A1B2C3D4', challenge).status_code, 200)
        self.assertEqual(rate_limit.get_two_fa_attempts(self.user), 0)
        self.assertEqual(self.two_fa.backup_codes_used, [0])
        self.issuer.reset_mock()
        self.outstanding.reset_mock()
        self.user.record_login.reset_mock()
        self.assert_rejected(self.post('A1B2C3D4', challenge), 403)
        self.assert_rejected(self.post('A1B2C3D4', self.challenge()), 400)



class JWTIssuanceGateTests(SimpleTestCase):
    # Share only the existing offline fixtures/helpers, not its test methods.
    start_patch = TwoFactorContractTests.start_patch
    lookup_user = TwoFactorContractTests.lookup_user
    post = TwoFactorContractTests.post

    def setUp(self):
        TwoFactorContractTests.setUp(self)
        self.password = 'Offline-only-password-927!'
        self.user.set_password(self.password)
        # Exercise Django's real ModelBackend and password/active checks;
        # replace only the database lookup with the unsaved fixture.
        self.start_patch(User.objects, 'get_by_natural_key', return_value=self.user)
        self.authenticate = self.start_patch(
            jwt_serializers, 'authenticate', wraps=jwt_serializers.authenticate,
        )
        self.last_login = self.start_patch(
            sys.modules[CustomTokenObtainPairSerializer.__module__], 'update_last_login',
        )
        self.signer = self.start_patch(signing, 'dumps', wraps=signing.dumps)
        self.for_user = self.start_patch(RefreshToken, 'for_user', wraps=RefreshToken.for_user)
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

        self.outstanding_get = self.start_patch(OutstandingToken.objects, 'get_or_create')

    def login(self, password=None, serializer_class=CustomTokenObtainPairSerializer):
        request = self.factory.post('/api/auth/login/', {
            'email': self.user.email,
            'password': self.password if password is None else password,
        }, format='json')
        return TokenObtainPairView.as_view(serializer_class=serializer_class)(request)

    def assert_no_issuance(self):
        self.issuer.assert_not_called()
        self.for_user.assert_not_called()
        self.outstanding.assert_not_called()
        self.outstanding_get.assert_not_called()
        self.last_login.assert_not_called()
        self.user.record_login.assert_not_called()

    def assert_login_rejected(self, response, status):
        self.assertEqual(response.status_code, status)
        for key in ('access', 'refresh', 'temporary_token', 'user', 'requires_2fa'):
            self.assertNotIn(key, response.data)
        self.signer.assert_not_called()
        self.assert_no_issuance()

    def test_2fa_g01_no_early_jwt_and_challenge_contract(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {
            'requires_2fa', 'temporary_token', 'access', 'token_type', 'user',
        })
        self.assertIs(response.data['requires_2fa'], True)
        self.assertEqual(response.data['token_type'], '2fa_temporary')
        challenge = response.data['temporary_token']
        self.assertEqual(response.data['access'], challenge)
        self.assertEqual(response.data['user'], {
            'id': str(self.user.id), 'email': self.user.email,
            'full_name': self.user.full_name,
        })
        payload = signing.loads(challenge, salt='adminapps.2fa.login', max_age=300)
        self.assertEqual({k: payload[k] for k in ('user_id', 'email', 'purpose', 'scope')}, {
            'user_id': str(self.user.id), 'email': self.user.email,
            'purpose': '2fa_verification', 'scope': 'totp_verification_only',
        })
        self.assertEqual(payload['version'], 1)
        self.assertEqual(len(bytes.fromhex(payload['nonce'])), 32)
        self.assertEqual(payload['generation'], str(self.two_fa.generation))
        self.signer.assert_called_once()
        self.authenticate.assert_called_once()
        self.assertEqual(self.authenticate.call_args.kwargs['password'], self.password)
        self.assertEqual(self.authenticate.call_args.kwargs['email'], self.user.email)
        self.assertIn('request', self.authenticate.call_args.kwargs)
        with self.assertRaises(TokenError):
            AccessToken(challenge)
        with self.assertRaises(signing.BadSignature):
            signing.loads(challenge, salt='wrong-salt', max_age=300)
        with patch('django.core.signing.time.time', return_value=time.time() + 301):
            with self.assertRaises(signing.SignatureExpired):
                signing.loads(challenge, salt='adminapps.2fa.login', max_age=300)
        self.assert_no_issuance()

    def test_2fa_g02_no_premature_persistence_attempt(self):
        # Spies prove no write is attempted, not real database persistence.
        self.outstanding.side_effect = AssertionError('Unexpected refresh persistence')
        self.outstanding_get.side_effect = AssertionError('Unexpected refresh persistence')
        self.assertEqual(self.login().status_code, 200)
        self.assert_no_issuance()

    def test_2fa_g03_standard_login_contract_and_single_emission(self):
        for configured in (True, False):
            with self.subTest(configured=configured):
                self.two_fa.is_enabled = False
                self.user._state.fields_cache['two_factor_auth'] = self.two_fa if configured else None
                for spy in (self.issuer, self.for_user, self.outstanding,
                            self.last_login, self.user.record_login, self.authenticate):
                    spy.reset_mock()
                response = self.login()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(set(response.data), {'access', 'refresh', 'user'})
                self.assertEqual(response.data['user'], {
                    'id': str(self.user.id), 'email': self.user.email,
                    'full_name': self.user.full_name, 'role': self.user.role,
                    'organization_id': str(self.user.organization.id),
                    'organization_name': self.user.organization.name,
                    'theme': self.user.theme,
                    'must_change_password': self.user.must_change_password,
                })
                self.issuer.assert_called_once_with(self.user)
                self.for_user.assert_called_once_with(self.user)
                self.outstanding.assert_called_once()
                self.outstanding_get.assert_not_called()
                self.last_login.assert_called_once_with(None, self.user)
                self.user.record_login.assert_called_once_with()
                self.authenticate.assert_called_once()
                self.signer.assert_not_called()
                for kind in ('access', 'refresh'):
                    claims = token_backend.decode(response.data[kind], verify=True)
                    self.assertEqual(claims['token_type'], kind)
                    self.assertEqual(claims['user_id'], str(self.user.id))
                    lifetime = 8 * 3600 if kind == 'access' else 7 * 86400
                    self.assertEqual(claims['exp'] - claims['iat'], lifetime)

    def test_2fa_g04_custom_claims_and_extension_hook(self):
        class ExtendedSerializer(CustomTokenObtainPairSerializer):
            @classmethod
            def get_token(cls, user):
                token = super().get_token(user)
                token['custom_claim'] = 'offline-extension'
                return token

        self.two_fa.is_enabled = False
        response = self.login(serializer_class=ExtendedSerializer)
        self.assertEqual(response.status_code, 200)
        for kind in ('access', 'refresh'):
            claims = token_backend.decode(response.data[kind], verify=True)
            for name in ('email', 'full_name', 'role'):
                self.assertEqual(claims[name], getattr(self.user, name))
            self.assertEqual(claims['organization_id'], str(self.user.organization.id))
            self.assertEqual(claims['organization_name'], self.user.organization.name)
            self.assertEqual(claims['custom_claim'], 'offline-extension')
        self.issuer.assert_called_once_with(self.user)
        self.for_user.assert_called_once_with(self.user)

    def test_2fa_g05_invalid_credentials(self):
        for enabled in (True, False):
            with self.subTest(two_fa=enabled):
                self.two_fa.is_enabled = enabled
                self.assert_login_rejected(self.login(password='wrong-password'), 401)
        self.authenticate.assert_called()

    def test_2fa_g06_inactive_user(self):
        self.user.is_active = False
        for enabled in (True, False):
            with self.subTest(two_fa=enabled):
                self.two_fa.is_enabled = enabled
                self.assert_login_rejected(self.login(), 401)
        # Even a backend/custom rule admitting inactive users cannot open the gate.
        self.authenticate.return_value = self.user
        with patch.object(api_settings, 'USER_AUTHENTICATION_RULE', return_value=True):
            self.assert_login_rejected(self.login(), 401)

    def test_2fa_g07_generated_challenge_completes_totp_and_backup_login(self):
        for token in (self.otp, 'A1B2C3D4'):
            with self.subTest(factor=token == self.otp):
                self.issuer.reset_mock()
                self.for_user.reset_mock()
                self.outstanding.reset_mock()
                challenge = self.login().data['temporary_token']
                self.issuer.assert_not_called()
                self.for_user.assert_not_called()
                self.outstanding.assert_not_called()
                response = self.post(token, challenge)
                self.assertEqual(response.status_code, 200)
                self.issuer.assert_called_once_with(self.user)
                self.for_user.assert_called_once_with(self.user)
                self.outstanding.assert_called_once()
                for kind in ('access', 'refresh'):
                    self.assertEqual(token_backend.decode(response.data[kind], verify=True)['token_type'], kind)

    def test_2fa_g08_emission_failures_are_sanitized_without_partial_success(self):
        self.two_fa.is_enabled = False
        for stage in ('issuer', 'persistence', 'refresh_encoding', 'access_encoding'):
            with self.subTest(stage=stage):
                self.issuer.side_effect = None
                self.outstanding.side_effect = None
                failure = RuntimeError('synthetic sensitive internal detail')
                if stage == 'issuer':
                    self.issuer.side_effect = failure
                elif stage == 'persistence':
                    self.outstanding.side_effect = failure
                else:
                    broken = Mock()
                    type(broken).__str__ = Mock(side_effect=failure)
                    pair = broken if stage == 'refresh_encoding' else Mock(access_token=broken)
                    self.issuer.side_effect = lambda user: pair
                with self.assertNoLogs('apps.users', level='INFO'):
                    response = self.login()
                self.assertEqual(response.status_code, 500)
                self.assertEqual(set(response.data), {'detail'})
                self.assertEqual(str(response.data['detail']), 'Unable to complete authentication')
                self.assertNotIn('synthetic sensitive', str(response.data))
                self.signer.assert_not_called()
                self.last_login.assert_not_called()
                self.user.record_login.assert_not_called()

    def test_2fa_g09_locked_and_expired_password_gates(self):
        for enabled in (True, False):
            with self.subTest(two_fa=enabled):
                self.two_fa.is_enabled = enabled
                self.user.locked_until = timezone.now() + timedelta(minutes=10)
                self.assert_login_rejected(self.login(), 400)
                self.user.locked_until = None
                self.user.mark_temporary_password(when=timezone.now() - timedelta(days=8))
                response = self.login()
                self.assert_login_rejected(response, 400)
                self.assertEqual(response.data['reason_code'], ['TEMP_PASSWORD_EXPIRED'])
                self.user.clear_temporary_password()

    def test_2fa_g09_temporary_password_warning_and_optional_last_login(self):
        self.two_fa.is_enabled = False
        self.user.mark_temporary_password(when=timezone.now() - timedelta(days=6))
        with patch.object(api_settings, 'UPDATE_LAST_LOGIN', False):
            response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.data['user']['must_change_password'], True)
        self.assertEqual(response.data['security_alert']['reason_code'], 'TEMP_PASSWORD_EXPIRING')
        self.assertEqual(response.data['security_alert']['days_left'], 1)
        self.assertEqual(response.data['security_alert']['expires_at'], self.user.get_temporary_password_expiry())
        self.issuer.assert_called_once_with(self.user)
        self.last_login.assert_not_called()
        self.user.record_login.assert_called_once_with()

    def test_2fa_g09_configured_authentication_rule_is_preserved(self):
        with patch.object(api_settings, 'USER_AUTHENTICATION_RULE', return_value=False) as rule:
            self.assert_login_rejected(self.login(), 401)
        rule.assert_called_once_with(self.user)

    def test_2fa_g09_two_fa_lookup_error_cannot_bypass_gate(self):
        with patch.object(User, 'two_factor_auth', new_callable=PropertyMock) as relation:
            relation.side_effect = RuntimeError('Offline lookup failure')
            with self.assertRaises(RuntimeError):
                self.login()
        self.signer.assert_not_called()
        self.assert_no_issuance()


if __name__ == '__main__':
    # No sockets may be opened by this offline runner, even accidentally.
    with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')), \
         patch('socket.socket.connect_ex', side_effect=AssertionError('Network forbidden')):
        unittest.main()
