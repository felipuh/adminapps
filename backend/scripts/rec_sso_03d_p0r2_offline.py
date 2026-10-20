"""P0R2 real DRF/crypto/services with memory ORM; no settings/env/DB/network.

--baseline executes the SAME critical acceptance against the previous configured
SimpleJWT authenticator and must fail (revoked JWT still reaches handler).
"""
from contextlib import nullcontext
from datetime import timedelta
from pathlib import Path
import json
import socket
import sys
import unittest
from unittest.mock import Mock, patch
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
BASELINE = '--baseline' in sys.argv
sys.argv = [a for a in sys.argv if a != '--baseline']
NETWORK = [patch(t, side_effect=AssertionError('Network forbidden')).start() for t in (
    'socket.socket.connect', 'socket.socket.connect_ex', 'socket.create_connection', 'socket.getaddrinfo')]
from django.conf import settings
KEY = 'p0r2-synthetic-offline-signing-material-only'
settings.configure(
    SECRET_KEY=KEY, USE_TZ=True, AUTH_USER_MODEL='users.User',
    ROOT_URLCONF='config.urls', ALLOWED_HOSTS=['testserver'], BILLING_SCHEDULER_ENABLED=False,
    INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
                    'rest_framework', 'django_filters', 'apps.users', 'apps.organizations',
                    'apps.subscriptions', 'apps.products', 'apps.integration', 'apps.billing', 'apps.api',
                    'rest_framework_simplejwt.token_blacklist'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.dummy'}}, LOGGING_CONFIG=None,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication' if BASELINE else
        'apps.users.authentication.HumanJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication']},
    SIMPLE_JWT={'ALGORITHM': 'HS256', 'SIGNING_KEY': KEY, 'ROTATE_REFRESH_TOKENS': True,
                'ACCESS_TOKEN_LIFETIME': timedelta(minutes=10),
                'REFRESH_TOKEN_LIFETIME': timedelta(days=1)},
)
from django.db.backends.base.base import BaseDatabaseWrapper
DB = patch.object(BaseDatabaseWrapper, 'connect', side_effect=AssertionError('Database forbidden')).start()
import django
django.setup()
from django.db import DatabaseError
from django.test import override_settings
from django.utils import timezone
import jwt
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from apps.users import human_sessions as life
from apps.users.models import User, UserSession, UserActivityLog
from apps.users.models_2fa import TwoFactorAuth, TwoFactorAuthLog, TwoFactorChallenge
from apps.users.serializers import CustomTokenObtainPairSerializer
from apps.users.views import LogoutView, UserViewSet, RegisterView, CustomTokenObtainPairView, PasswordResetConfirmView
from apps.users.human_token_views import HumanTokenRefreshView


class Query:
    """Small stateful ORM substitute: actual services choose filters and writes."""
    def __init__(self, records, model, filters=None, excluded=None):
        self.records, self.model = records, model
        self.filters, self.excluded = filters or {}, excluded or {}

    def select_related(self, *args): return self
    def select_for_update(self): return self
    def order_by(self, *args): return self
    def __iter__(self): return iter(self.rows())
    def filter(self, **kw): return Query(self.records, self.model, dict(self.filters, **kw), self.excluded)
    def exclude(self, **kw): return Query(self.records, self.model, self.filters, dict(self.excluded, **kw))

    def matches(self, row, data):
        for key, value in data.items():
            if key.endswith('__isnull'):
                actual = getattr(row, key[:-8]) is None
            else:
                actual = getattr(row, key)
            if str(actual) != str(value): return False
        return True

    def rows(self):
        return [r for r in self.records.values() if self.matches(r, self.filters)
                and (not self.excluded or not self.matches(r, self.excluded))]

    def get(self, **kw):
        rows = self.filter(**kw).rows()
        if len(rows) != 1: raise self.model.DoesNotExist
        return rows[0]

    def update(self, **kw):
        rows = self.rows()
        for row in rows:
            for key, value in kw.items():
                if hasattr(value, 'connector'):
                    assert value.lhs.name == key and value.connector == '+'
                    value = getattr(row, key) + value.rhs.value
                setattr(row, key, value)
        return len(rows)


class Protected(APIView):
    permission_classes = [IsAuthenticated]
    calls = 0

    def get(self, request):
        type(self).calls += 1
        return Response({'user_id': str(request.user.pk)})


class HumanSessionTests(unittest.TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.users, self.records = {}, {}
        self.user = self.add_user()
        self.other = self.add_user()
        self.uq, self.sq = Query(self.users, User), Query(self.records, UserSession)
        from django.db import connections
        self.connection = connections['default']
        self.patch(self.connection, 'vendor', 'postgresql')
        self.patch(self.connection, 'get_autocommit', return_value=True)
        self.patch(life.transaction, 'atomic', side_effect=lambda **kw: nullcontext())
        for manager, query in ((User.objects, self.uq), (UserSession.objects, self.sq)):
            for name in ('get', 'filter', 'select_related', 'select_for_update'):
                self.patch(manager, name, side_effect=getattr(query, name))
        self.patch(UserSession.objects, 'create', side_effect=self.create)
        self.patch(UserSession, 'save', autospec=True)
        self.audit = self.patch(UserActivityLog.objects, 'create')
        self.full_token_store = self.patch(OutstandingToken.objects, 'create', side_effect=AssertionError('Full JWT storage forbidden'))
        Protected.calls = 0

    def patch(self, obj, name, *args, **kw):
        p = patch.object(obj, name, *args, **kw); self.addCleanup(p.stop); return p.start()

    def add_user(self):
        user = User(email=f'{uuid.uuid4()}@example.invalid', first_name='Offline', last_name='User')
        user.set_password('offline-synthetic-password')
        self.users[user.pk] = user
        return user

    def create(self, **kw):
        row = UserSession(**kw); row.created_at = timezone.now()
        self.records[row.pk] = row
        return row

    def simulate_authority_trigger(self, user):
        # Emulate users.0005; actual PostgreSQL execution is explicitly pending.
        user.human_auth_version += 1
        self.sq.filter(user_id=user.pk, is_active=True, revoked_at__isnull=True).update(
            is_active=False, revoked_at=timezone.now(), generation=life.F('generation') + 1)

    def issue(self, user=None):
        token = CustomTokenObtainPairSerializer.get_token(user or self.user)
        return token, str(token.access_token)

    def request(self, token, view=Protected, data=None, action=None, session=None):
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token} if token else {}
        request = (self.factory.get('/offline/', **headers) if data is None else
                   self.factory.post('/offline/', data, format='json', **headers))
        if session is not None:
            request.session = session
        return view.as_view({request.method.lower(): action})(request) if action else view.as_view()(request)

    def assert_denied(self, token):
        before = Protected.calls
        response = self.request(token)
        self.assertIn(response.status_code, (401, 403, 503), response.data)
        self.assertEqual(Protected.calls, before, 'protected handler executed')

    def test_critical_same_signed_jwt_rejected_before_handler_after_service_revocation(self):
        refresh, access = self.issue()
        self.assertEqual(self.request(access).status_code, 200)
        self.assertEqual(Protected.calls, 1)
        self.assertEqual(life.revoke(self.user, session_id=refresh['sid']), 1)
        # Signature/expiry remain valid. Only the live session authority denies.
        self.assertEqual(AccessToken(access)['sid'], refresh['sid'])
        self.assert_denied(access)
        self.assertEqual(Protected.calls, 1)

    def test_issuance_binds_pair_and_persists_only_identifiers(self):
        refresh, access = self.issue()
        row = self.records[uuid.UUID(refresh['sid'])]
        decoded = AccessToken(access)
        for k in ('sid', 'fid', 'sg', 'av', 'token_family', 'hsv', 'user_id'):
            self.assertEqual(decoded[k], refresh[k])
        self.assertEqual(row.token_jti, refresh['jti'])
        self.assertNotEqual(decoded['jti'], refresh['jti'])
        self.assertEqual(row.family_id, uuid.UUID(refresh['fid']))
        self.assertEqual(row.user_id, self.user.pk)
        self.assertEqual(self.request(access).status_code, 200)
        self.full_token_store.assert_not_called()

    def test_missing_foreign_or_inconsistent_record_denied(self):
        for change in ('missing', 'user', 'family', 'version', 'generation', 'authority', 'expiry'):
            refresh, access = self.issue(); sid = uuid.UUID(refresh['sid']); row = self.records[sid]
            if change == 'missing': del self.records[sid]
            elif change == 'user': row.user_id = self.other.pk
            elif change == 'family': row.family_id = uuid.uuid4()
            elif change == 'version': row.contract_version = 0
            elif change == 'generation': row.generation += 1
            elif change == 'authority': row.authority_version += 1
            elif change == 'expiry': row.expires_at = timezone.now()
            with self.subTest(change=change): self.assert_denied(access)

    def test_legacy_and_wrong_families_never_fall_back(self):
        for family in (None, 'CENTRAL', 'LOCAL', 'ISO_SMART', 'MEDSUPPLIER', 'IntegrationAPIKey'):
            token = AccessToken(); token['user_id'] = str(self.user.pk)
            if family: token['token_family'] = family
            with self.subTest(family=family): self.assert_denied(str(token))
        self.assert_denied('synthetic-api-key')
        refresh, _ = self.issue()
        self.assert_denied(str(refresh))
        for marker in ({'client_id': 'isosmart'}, {'product': 'MEDSUPPLIER'}, {'principal_type': 'service'}):
            token = refresh.access_token; token.payload.update(marker)
            self.assert_denied(str(token))

    def test_invalid_signature_algorithm_expiry_and_claim_types_denied(self):
        refresh, _ = self.issue()
        for changes in ({'sg': True}, {'av': '1'}, {'hsv': True}, {'sid': 'invalid'},
                        {'iat': 1}, {'exp': 1}, {'exp': refresh['exp'] + 1000}, {'fid': None}):
            token = refresh.access_token; token.payload.update(changes)
            with self.subTest(changes=changes): self.assert_denied(str(token))
        payload = refresh.access_token.payload
        for algorithm, key in (('HS384', KEY), ('HS256', KEY + '-wrong')):
            self.assert_denied(jwt.encode(payload, key, algorithm=algorithm))
        self.assert_denied(jwt.encode(payload, '', algorithm='none'))

    def test_refresh_active_rotation_old_access_and_replay_denied(self):
        refresh, old_access = self.issue(); raw = str(refresh)
        response = self.request(None, HumanTokenRefreshView, {'refresh': raw})
        self.assertEqual(response.status_code, 200, response.data)
        pair = response.data
        self.assertEqual(self.request(pair['access']).status_code, 200)
        self.assert_denied(old_access)
        self.assertEqual(self.request(None, HumanTokenRefreshView, {'refresh': raw}).status_code, 401)
        current = life.HumanRefreshToken(pair['refresh'])
        self.assertEqual(current['sg'], refresh['sg'] + 1)
        self.assertEqual(current['exp'], refresh['exp'])
        life.revoke(self.user, session_id=current['sid'])
        self.assertEqual(self.request(None, HumanTokenRefreshView, {'refresh': pair['refresh']}).status_code, 401)

    def test_refresh_foreign_authenticated_actor_and_legacy_denied(self):
        other_refresh, _ = self.issue(self.other); _, mine = self.issue()
        response = self.request(mine, HumanTokenRefreshView, {'refresh': str(other_refresh)})
        self.assertEqual(response.status_code, 401)
        with self.assertRaises(life.AuthenticationFailed):
            life.refresh_pair(str(other_refresh), expected_user_id=self.user.pk)
        token = RefreshToken(); token['user_id'] = str(self.user.pk)
        self.assertEqual(self.request(None, HumanTokenRefreshView, {'refresh': str(token)}).status_code, 401)

    def test_nonrotating_refresh_stays_subordinate_to_session(self):
        refresh, access = self.issue()
        from rest_framework_simplejwt.settings import api_settings
        with patch.object(api_settings, 'ROTATE_REFRESH_TOKENS', False):
            pair = life.refresh_pair(str(refresh)); self.assertNotIn('refresh', pair)
            self.assertEqual(self.request(pair['access']).status_code, 200)
            self.assertEqual(self.request(access).status_code, 200)
            life.revoke(self.user, session_id=refresh['sid'])
            with self.assertRaises(life.AuthenticationFailed): life.refresh_pair(str(refresh))

    def test_logout_revokes_current_access_and_refresh_and_flushes_django_cookie(self):
        from django.contrib.sessions.backends.cache import SessionStore
        refresh, access = self.issue(); _, other_access = self.issue(self.other)
        cookie = SessionStore(); cookie['unrelated'] = 'value'; cookie.save(); old_key = cookie.session_key
        response = self.request(access, LogoutView, {'refresh': str(refresh)}, session=cookie)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(dict(cookie), {}); self.assertIsNone(cookie.session_key)
        self.assertFalse(SessionStore().exists(old_key))
        self.assert_denied(access)
        with self.assertRaises(life.AuthenticationFailed): life.refresh_pair(str(refresh))
        self.assertEqual(self.request(other_access).status_code, 200)
        self.assertEqual(life.logout_session(self.user, AccessToken(access), str(refresh)), 0)

    def test_logout_foreign_or_different_owned_refresh_rejected_without_effect(self):
        refresh, access = self.issue(); same_user, _ = self.issue(); foreign, _ = self.issue(self.other)
        for bad in (str(same_user), str(foreign), access, str(refresh) + 'bad'):
            with self.subTest(token_kind=bad[:8]):
                self.assertEqual(self.request(access, LogoutView, {'refresh': bad}).status_code, 401)
                self.assertEqual(self.request(access).status_code, 200)

    def test_revoke_others_preserves_sid_and_other_user_even_after_rotation(self):
        current, access = self.issue(); _, second = self.issue(); _, foreign = self.issue(self.other)
        pair = life.refresh_pair(str(current)); access = pair['access']
        response = self.request(access, UserViewSet, {}, 'revoke_sessions')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['revoked'], 1)
        self.assertEqual(self.request(access).status_code, 200)
        self.assertEqual(self.request(foreign).status_code, 200)
        self.assert_denied(second)
        self.assertEqual(self.request(access, UserViewSet, {'current_token_jti': 'forged'}, 'revoke_sessions').status_code, 400)

    def test_individual_global_idempotent_and_foreign_revoke_denied(self):
        first, access = self.issue(); _, second = self.issue(); foreign, f_access = self.issue(self.other)
        for sid in (foreign['sid'], str(uuid.uuid4())):
            response = self.request(access, UserViewSet, {'session_id': sid}, 'revoke_session')
            self.assertEqual(response.status_code, 401, response.data)
        self.assertEqual(self.request(access).status_code, 200)
        response = self.request(access, UserViewSet, {'session_id': first['sid']}, 'revoke_session')
        self.assertEqual(response.status_code, 200, response.data); self.assert_denied(access)
        self.assertEqual(life.revoke(self.user, session_id=first['sid']), 0)
        response = self.request(second, UserViewSet, {'all': True}, 'revoke_session')
        self.assertEqual(response.status_code, 200, response.data)
        self.assert_denied(second); self.assertEqual(life.revoke(self.user), 0)
        self.assertEqual(self.request(f_access).status_code, 200)

    def test_disable_reenable_password_authority_epoch_never_restores_tokens(self):
        # Emulate the PREPARED PostgreSQL user trigger, not a production DB proof.
        refresh, access = self.issue()
        self.user.is_active = False; self.simulate_authority_trigger(self.user)
        self.assert_denied(access)
        with self.assertRaises(life.AuthenticationFailed): life.refresh_pair(str(refresh))
        self.user.is_active = True; self.simulate_authority_trigger(self.user)
        self.assert_denied(access)
        _, new = self.issue(); self.assertEqual(self.request(new).status_code, 200)
        self.user.set_password('changed-offline-password'); self.simulate_authority_trigger(self.user)
        self.assert_denied(new)
        with self.assertRaises(life.AuthenticationFailed): life.refresh_pair(str(refresh))

    def test_state_unavailable_denies_access_refresh_issuance_and_revocation(self):
        refresh, access = self.issue()
        with patch.object(UserSession.objects, 'select_related', side_effect=DatabaseError('private')):
            response = self.request(access); self.assertEqual(response.status_code, 503)
            self.assertNotIn('private', str(response.data)); self.assertEqual(Protected.calls, 0)
        with patch.object(User.objects, 'select_for_update', side_effect=DatabaseError('private')):
            for fn in (lambda: life.refresh_pair(str(refresh)), lambda: life.issue_refresh(self.user),
                       lambda: life.revoke(self.user)):
                with self.assertRaises(life.SessionUnavailable): fn()
        with patch.object(self.connection, 'vendor', 'sqlite'):
            self.assertEqual(self.request(access).status_code, 503)

    def test_audit_or_response_loss_never_restores_revoked_authority(self):
        refresh, access = self.issue()
        with patch('apps.users.views.log_logout_activity', side_effect=RuntimeError('lost audit')):
            with self.assertRaises(RuntimeError): self.request(access, LogoutView, {})
        self.assert_denied(access)
        self.assertEqual(life.revoke(self.user, session_id=refresh['sid']), 0)
        with self.assertRaises(life.AuthenticationFailed): life.refresh_pair(str(refresh))

    def test_rejected_bearer_cannot_fall_through_to_django_cookie(self):
        from rest_framework.authentication import SessionAuthentication
        refresh, access = self.issue(); life.revoke(self.user, session_id=refresh['sid'])
        with patch.object(SessionAuthentication, 'authenticate', return_value=(self.user, None)) as cookie:
            self.assert_denied(access); cookie.assert_not_called()
            self.assertEqual(self.request(None).status_code, 200)

    def test_refresh_url_resolves_to_session_bound_view(self):
        from django.urls import resolve
        from apps.users.urls import urlpatterns
        match = resolve('/refresh/', urlconf=tuple(urlpatterns))
        self.assertIs(match.func.view_class, HumanTokenRefreshView)

    def test_existing_session_list_handler_uses_new_default_authentication(self):
        refresh, access = self.issue()
        response = self.request(access, UserViewSet, action='sessions')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(str(response.data[0]['id']), refresh['sid'])
        life.revoke(self.user, session_id=refresh['sid'])
        with patch.object(UserViewSet, 'sessions', wraps=UserViewSet.sessions) as handler:
            response = self.request(access, UserViewSet, action='sessions')
            self.assertEqual(response.status_code, 401); handler.assert_not_called()

    def login(self, serializer_class=CustomTokenObtainPairSerializer, password='offline-synthetic-password'):
        request = self.factory.post('/login/', {'email': self.user.email, 'password': password}, format='json')
        return CustomTokenObtainPairView.as_view(serializer_class=serializer_class)(request)

    def test_real_login_single_session_custom_claims_and_preissuance_gates(self):
        self.user._state.fields_cache['two_factor_auth'] = None
        self.patch(User.objects, 'get_by_natural_key', return_value=self.user)
        self.patch(self.user, 'record_login')

        class Extended(CustomTokenObtainPairSerializer):
            @classmethod
            def get_token(cls, user):
                token = super().get_token(user); token['custom_claim'] = 'retained'; return token

        response = self.login(Extended)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(set(response.data), {'access', 'refresh', 'user'})
        self.assertEqual(len(self.records), 1)
        self.assertEqual(AccessToken(response.data['access'])['custom_claim'], 'retained')
        self.assertEqual(self.request(response.data['access']).status_code, 200)
        self.assertEqual(self.login(password='wrong').status_code, 401)
        self.user.locked_until = timezone.now() + timedelta(minutes=5)
        self.assertEqual(self.login().status_code, 400)
        self.assertEqual(len(self.records), 1)
        self.full_token_store.assert_not_called()

    def test_real_mfa_challenge_totp_backup_and_replay_with_session_issuer(self):
        import pyotp
        from apps.users import two_factor_service as mfa, views_2fa
        from apps.users.models_2fa import TwoFactorAuth, TwoFactorAuthLog, TwoFactorChallenge
        config = TwoFactorAuth(user=self.user, is_enabled=True)
        config.secret = 'JBSWY3DPEHPK3PXP'; config.backup_codes = 'A1B2C3D4'
        self.user._state.fields_cache['two_factor_auth'] = config
        self.patch(User.objects, 'get_by_natural_key', return_value=self.user)
        self.patch(self.user, 'record_login')
        self.patch(TwoFactorAuth.objects, 'select_for_update', return_value=TwoFactorAuth.objects)
        self.patch(TwoFactorAuth.objects, 'get', return_value=config)
        self.patch(TwoFactorAuth, 'save'); self.patch(TwoFactorAuthLog.objects, 'create')
        challenges = {}
        def create_challenge(**kw):
            row = TwoFactorChallenge(**kw); challenges[row.pk] = row; return row
        self.patch(TwoFactorChallenge.objects, 'create', side_effect=create_challenge)
        self.patch(TwoFactorChallenge.objects, 'select_for_update', return_value=Query(challenges, TwoFactorChallenge))
        self.patch(TwoFactorChallenge, 'save')
        def verify(challenge, factor):
            request = self.factory.post('/2fa/verify/', {'token': factor}, format='json',
                                        HTTP_AUTHORIZATION='Bearer ' + challenge)
            return views_2fa.verify_2fa_token(request)
        for factor in (pyotp.TOTP(config.secret).now(), 'A1B2C3D4'):
            before = len(self.records)
            response = self.login()
            self.assertEqual(response.status_code, 200, response.data)
            self.assertTrue(response.data['requires_2fa'])
            self.assertEqual(len(self.records), before, 'session emitted before MFA')
            challenge = response.data['temporary_token']
            self.assertEqual(verify(challenge, 'bad').status_code, 400)
            self.assertEqual(len(self.records), before)
            response = verify(challenge, factor)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(len(self.records), before + 1)
            self.assertEqual(self.request(response.data['access']).status_code, 200)
            self.assertEqual(verify(challenge, factor).status_code, 403)
            self.assertEqual(len(self.records), before + 1)
        self.assertEqual(config.backup_codes_used, [0]); self.full_token_store.assert_not_called()

    def test_registration_uses_real_serializer_and_session_bound_pair(self):
        self.patch(User.objects, 'filter', return_value=Mock(first=lambda: None))
        self.patch(User, 'save', autospec=True, side_effect=lambda user, **kw: self.users.update({user.pk: user}))
        payload = {'email': 'new@example.invalid', 'first_name': 'New', 'last_name': 'User',
                   'password': 'Local-registration-123!', 'password_confirm': 'Local-registration-123!'}
        response = self.request(None, RegisterView, payload)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(self.records), 1)
        access = response.data['tokens']['access']
        self.assertEqual(self.request(access).status_code, 200)
        row = next(iter(self.records.values()))
        life.revoke(self.users[row.user_id], session_id=row.pk)
        self.assert_denied(access)

    def test_password_change_and_reset_handlers_with_simulated_authority_trigger(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        def save_authority(user, **kw):
            # PostgreSQL users.0005 trigger effect; SQL execution remains pending.
            self.simulate_authority_trigger(user)
        self.patch(User, 'save', autospec=True, side_effect=save_authority)
        _, access = self.issue()
        response = self.request(access, UserViewSet, {
            'current_password': 'offline-synthetic-password',
            'new_password': 'Changed-password-123!', 'new_password_confirm': 'Changed-password-123!',
        }, 'change_password')
        self.assertEqual(response.status_code, 200, response.data); self.assert_denied(access)
        _, access = self.issue()
        response = self.request(None, PasswordResetConfirmView, {
            'uid': urlsafe_base64_encode(force_bytes(self.user.pk)),
            'token': default_token_generator.make_token(self.user),
            'new_password': 'Reset-password-123!', 'new_password_confirm': 'Reset-password-123!',
        })
        self.assertEqual(response.status_code, 200, response.data); self.assert_denied(access)

    def test_ambient_transaction_cannot_roll_back_completed_revocation(self):
        refresh, _ = self.issue()
        with patch.object(self.connection, 'in_atomic_block', True):
            with self.assertRaises(life.SessionUnavailable): life.revoke(self.user)
        with patch.object(self.connection, 'get_autocommit', return_value=False):
            with self.assertRaises(life.SessionUnavailable): life.refresh_pair(str(refresh))

    def test_cookie_authenticated_logout_revokes_owned_bound_refresh_without_storing_jwt(self):
        from rest_framework.authentication import SessionAuthentication
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        refresh, access = self.issue(); foreign, _ = self.issue(self.other)
        with patch.object(SessionAuthentication, 'authenticate', return_value=(self.user, None)), \
                patch.object(BlacklistedToken.objects, 'filter', return_value=Mock(exists=lambda: False)), \
                patch.object(OutstandingToken.objects, 'get_or_create', side_effect=AssertionError('JWT storage forbidden')):
            self.assertEqual(self.request(None, LogoutView, {'refresh': str(foreign)}).status_code, 400)
            self.assertEqual(self.request(access).status_code, 200)
            self.assertEqual(self.request(None, LogoutView, {'refresh': str(refresh)}).status_code, 200)
            self.assert_denied(access)
            self.assertEqual(self.request(None, LogoutView, {'refresh': str(refresh)}).status_code, 200)
            _, other_owned = self.issue()
            response = self.request(None, UserViewSet, {}, 'revoke_sessions')
            self.assertEqual(response.status_code, 200, response.data)
            self.assertIs(response.data['django_cookie_revoked'], False)
            self.assert_denied(other_owned)

    def test_live_invitation_dispatch_with_new_session_storage(self):
        # Keep the original historical fixture/test bytes untouched; supply the
        # additional session persistence required by the new issuer contract.
        from apps.api.test_p0r import InvitationLifecycleTests
        original_save = User.save
        probe = InvitationLifecycleTests()
        probe.setUp(); self.addCleanup(probe.doCleanups); probe.fixture()
        self.patch(User.objects, 'select_for_update', return_value=self.uq)
        self.patch(User, 'save', original_save)
        self.patch(User, 'save', autospec=True, side_effect=lambda user, **kw: self.users.update({user.pk: user}))
        response = self.request(None, RegisterView, probe.payload)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(probe.invitation.status, 'accepted')
        access = response.data['tokens']['access']
        self.assertEqual(self.request(access).status_code, 200)
        row = next(iter(self.records.values()))
        self.assertEqual(row.user.organization_id, probe.org.pk)
        life.revoke(row.user, session_id=row.pk); self.assert_denied(access)


if __name__ == '__main__':
    suite = (unittest.TestSuite([HumanSessionTests('test_critical_same_signed_jwt_rejected_before_handler_after_service_revocation')])
             if BASELINE else unittest.defaultTestLoader.loadTestsFromTestCase(HumanSessionTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   database_attempts=DB.call_count, network_attempts=sum(g.call_count for g in NETWORK),
                   baseline_authenticator=BASELINE)
    print(json.dumps(summary))
    sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
