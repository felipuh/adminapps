"""R1: real Django Client/URL/DRF lifecycle and versioned legacy test adapter.

No project settings, .env, database or network. Only persistence/transaction
boundaries are simulated. Original test methods/files remain unchanged.
"""
from datetime import datetime, timedelta, timezone as dt_timezone
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
import uuid

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('p0r2_memory', BASE / 'rec_sso_03d_p0r2_offline.py')
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.test import Client, override_settings
from django.urls import include, path, get_resolver
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from apps.users import human_sessions as life
from apps.users import tests_2fa_contract as historical_mfa
from apps.users.models import User, UserSession
from apps.users.views import UserViewSet, LogoutView
from apps.api.test_p0r import InvitationLifecycleTests

# Runtime-only synthetic configuration; actual settings modules are never imported.
settings.MIDDLEWARE = ['django.contrib.sessions.middleware.SessionMiddleware',
                       'django.contrib.auth.middleware.AuthenticationMiddleware']
settings.SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
settings.REST_FRAMEWORK = dict(settings.REST_FRAMEWORK, DEFAULT_PERMISSION_CLASSES=[
    'rest_framework.permissions.IsAuthenticated'])
root = types.ModuleType('p0r2_r1_urls')
root.urlpatterns = [path('api/auth/', include('apps.users.urls')),
                    path('api/', include('apps.api.urls')),
                    path('api/organizations/', include('apps.organizations.urls')),
                    path('api/subscriptions/', include('apps.subscriptions.urls')),
                    path('api/products/', include('apps.products.urls')),
                    path('api/billing/', include('apps.billing.urls')),
                    path('api/integration/', include('apps.integration.urls'))]
sys.modules[root.__name__] = root
settings.ROOT_URLCONF = root.__name__
# Import all URL model dependencies before taking references to cached managers.
get_resolver().url_patterns


class ClientLifecycleTests(unittest.TestCase):
    """Reuse memory ORM fixtures only; do not inherit the 25 P0R2 test methods."""
    setUp = h.HumanSessionTests.setUp
    patch = h.HumanSessionTests.patch
    add_user = h.HumanSessionTests.add_user
    create = h.HumanSessionTests.create
    simulate_authority_trigger = h.HumanSessionTests.simulate_authority_trigger

    def prepare(self):
        cache.clear(); self.addCleanup(cache.clear)
        self.client = Client()
        self.user._state.fields_cache['two_factor_auth'] = None
        self.patch(User.objects, 'get_by_natural_key', return_value=self.user)
        self.patch(self.user, 'record_login')
        self.patch(User, 'save', autospec=True)

    def post(self, url, data, access=None, client=None):
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + access} if access else {}
        return (client or self.client).post(url, data, content_type='application/json', **headers)

    def login(self):
        response = self.post('/api/auth/login/', {'email': self.user.email,
                                                'password': 'offline-synthetic-password'})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def protected(self, access=None, expected=200):
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + access} if access else {}
        response = self.client.get('/api/auth/users/sessions/', **headers)
        self.assertEqual(response.status_code, expected, response.content)
        return response

    def test_login_refresh_revoke_deny_and_relogin_through_real_django_client(self):
        self.prepare()
        pair = self.login(); self.assertEqual(len(self.records), 1)
        self.protected(pair['access'])
        response = self.post('/api/auth/refresh/', {'refresh': pair['refresh']})
        self.assertEqual(response.status_code, 200, response.content); rotated = response.json()
        self.protected(rotated['access']); self.protected(pair['access'], expected=401)
        self.assertEqual(self.post('/api/auth/refresh/', {'refresh': pair['refresh']}).status_code, 401)
        response = self.post('/api/auth/users/revoke_session/', {'session_id': AccessToken(rotated['access'])['sid']}, rotated['access'])
        self.assertEqual(response.status_code, 200, response.content)
        # Spy preserves the real method; a denied request must not reach it.
        with patch.object(UserViewSet, 'sessions', wraps=UserViewSet.sessions) as handler:
            self.protected(rotated['access'], expected=401); handler.assert_not_called()
        self.assertEqual(self.post('/api/auth/refresh/', {'refresh': rotated['refresh']}).status_code, 401)
        new = self.login(); self.assertEqual(len(self.records), 2); self.protected(new['access'])
        self.assertNotEqual(AccessToken(new['access'])['sid'], AccessToken(rotated['access'])['sid'])
        self.protected(rotated['access'], expected=401)
        print(json.dumps({'cycle': 'login->ALLOW->refresh->old_DENY->revoke->access_401_before_handler->refresh_DENY->relogin_ALLOW'}))

    def test_authority_change_between_password_verification_and_issuance_denied(self):
        self.prepare()
        original_get = self.uq.get
        for mutation in ('password', 'disable_reenable'):
            with self.subTest(mutation=mutation):
                self.user.set_password('offline-synthetic-password')
                verified = copy.copy(self.user)
                self.patch(User.objects, 'get_by_natural_key', return_value=verified)
                def change_before_lock(**kw):
                    if mutation == 'password':
                        self.user.set_password('Changed-during-authentication-123!')
                    else:
                        self.user.is_active = False
                        self.simulate_authority_trigger(self.user)
                        self.user.is_active = True
                    self.simulate_authority_trigger(self.user)
                    return original_get(**kw)
                self.patch(self.uq, 'get', side_effect=change_before_lock)
                response = self.post('/api/auth/login/', {'email': verified.email,
                                                        'password': 'offline-synthetic-password'})
                self.assertEqual(response.status_code, 401, 'stale authentication emitted a new token pair')
                self.assertEqual(len(self.records), 0)

    def prepare_hash_upgrade(self, concurrent_reset=False):
        # Django's real check_password setter changes the stored hash during
        # authentication. Simulate only its SQL write and authority trigger.
        original_save = User.save
        self.prepare()
        verified = copy.copy(self.user)
        self.patch(User.objects, 'get_by_natural_key', return_value=verified)
        self.patch(User, 'save', new=original_save)
        from django.db.models import Model
        def persist(instance, *args, **kw):
            self.user.password = instance.password
            self.simulate_authority_trigger(self.user)
        self.patch(Model, 'save', autospec=True, side_effect=persist)
        self.patch(h.Query, 'only', new=lambda query, *fields: query, create=True)
        self.patch(User._base_manager, 'db_manager', return_value=self.uq)
        factor_query = Mock()
        factor_query.all.return_value.get.side_effect = h.TwoFactorAuth.DoesNotExist
        self.patch(h.TwoFactorAuth._base_manager, 'db_manager', return_value=factor_query)
        if concurrent_reset:
            from django.contrib.auth.hashers import PBKDF2PasswordHasher, make_password
            self.reset_hash = make_password('Concurrent-reset-password-123!')
            original_encode = PBKDF2PasswordHasher.encode
            def encode_with_reset(hasher, password, salt, iterations=None):
                encoded = original_encode(hasher, password, salt, iterations)
                # Another transaction commits while the verified old password's
                # replacement hash is being computed, before User.save locks.
                self.user.password = self.reset_hash
                self.simulate_authority_trigger(self.user)
                return encoded
            self.patch(PBKDF2PasswordHasher, 'encode', new=encode_with_reset)

    def test_django_password_hash_upgrade_retains_fresh_authority_snapshot(self):
        self.prepare_hash_upgrade()
        with override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher',
                                                'django.contrib.auth.hashers.MD5PasswordHasher']):
            pair = self.login()
        self.assertTrue(self.user.password.startswith('pbkdf2_sha256$'))
        self.assertEqual(AccessToken(pair['access'])['av'], self.user.human_auth_version)
        self.protected(pair['access'])

    def test_concurrent_reset_during_django_hash_upgrade_cannot_be_overwritten(self):
        self.prepare_hash_upgrade(concurrent_reset=True)
        with override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher',
                                                'django.contrib.auth.hashers.MD5PasswordHasher']):
            response = self.post('/api/auth/login/', {'email': self.user.email,
                                                    'password': 'offline-synthetic-password'})
        self.assertEqual(response.status_code, 401, 'hash upgrade overwrote concurrent credential revocation')
        self.assertEqual(self.user.password, self.reset_hash)
        self.assertEqual(len(self.records), 0)

    def test_credential_families_and_no_cookie_fallback_after_bearer_rejection(self):
        self.prepare(); pair = self.login()
        self.client.force_login(self.user)
        self.protected()  # Real cache cookie + Django authentication middleware.
        legacy = AccessToken(); legacy['user_id'] = str(self.user.pk)
        for family in (None, 'CENTRAL', 'LOCAL', 'ISO_SMART', 'MEDSUPPLIER', 'IntegrationAPIKey'):
            token = AccessToken(); token['user_id'] = str(self.user.pk)
            if family: token['token_family'] = family
            with self.subTest(family=family): self.protected(str(token), expected=401)
        self.protected(pair['refresh'], expected=401)
        self.protected('synthetic-api-key', expected=401)
        response = self.post('/api/auth/users/revoke_session/', {'all': True}, pair['access'])
        self.assertEqual(response.status_code, 200, response.content)
        with patch.object(UserViewSet, 'sessions', wraps=UserViewSet.sessions) as handler:
            self.protected(pair['access'], expected=401); handler.assert_not_called()
        self.protected()  # JWT revocation does not claim cookie revocation.

    def test_logout_flushes_only_current_cookie_and_revokes_current_jwt_family(self):
        self.prepare(); first = self.login(); second = self.login()
        self.client.force_login(self.user)
        from django.contrib.sessions.backends.cache import SessionStore
        old_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        response = self.post('/api/auth/logout/', {}, first['access'])
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(SessionStore().exists(old_key))
        self.protected(first['access'], expected=401)
        self.protected(second['access']); self.protected(expected=403)
        self.assertEqual(self.post('/api/auth/refresh/', {'refresh': first['refresh']}).status_code, 401)

    def test_resolved_human_routes_have_new_default_and_particular_paths_stay_separate(self):
        from apps.users.authentication import HumanJWTAuthentication
        human = []; public = []; technical = []
        def walk(patterns, prefix=''):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    walk(pattern.url_patterns, prefix + str(pattern.pattern)); continue
                callback = pattern.callback
                route = prefix + str(pattern.pattern)
                if route.startswith('api/integration/'):
                    technical.append(route); continue
                cls = getattr(callback, 'cls', getattr(callback, 'view_class', None))
                if cls is None: continue
                auth = cls.authentication_classes
                if not auth:
                    public.append(route); continue
                self.assertIs(auth[0], HumanJWTAuthentication, route)
                human.append(route)
        walk(get_resolver().url_patterns)
        self.assertGreater(len(human), 20)
        self.assertTrue(any('refresh/' in p for p in human))
        self.assertTrue(any('2fa/verify/' in p for p in public))
        self.assertTrue(technical)
        print(json.dumps({'resolved_human_routes': len(human), 'public_no_default_auth': public,
                          'technical_or_central_paths_preserved': len(technical)}))


class SessionIssuerAdapter:
    """Version old persistence observations to the UserSession contract.

    Historical .outstanding assertions now observe UserSession.create, and
    .for_user assertions observe HumanRefreshToken.for_user. Production methods,
    authenticators, serializers and inherited assertion bodies stay real.
    """
    def configure_session_store(self):
        self.session_records = {}
        connection = connections['default']
        self.start_patch(connection, 'vendor', new='postgresql')
        self.start_patch(connection, 'get_autocommit', return_value=True)
        self.start_patch(AccessToken, 'lifetime', new=timedelta(hours=8))
        self.start_patch(life.HumanRefreshToken, 'lifetime', new=timedelta(days=7))
        self.start_patch(api_settings, 'UPDATE_LAST_LOGIN', new=True)
        # Align the historical 2030 ORM clock with JWT issuance (no signature bypass).
        self.start_patch(historical_mfa.service.timezone, 'now', return_value=datetime.now(dt_timezone.utc))
        self.instant = timezone.now()
        from rest_framework_simplejwt import tokens as jwt_tokens
        self.start_patch(jwt_tokens, 'aware_utcnow', return_value=self.instant)
        self.otp = self.two_fa.get_totp().at(self.instant)
        self.start_patch(OutstandingToken.objects, 'create', side_effect=AssertionError('Full JWT storage forbidden'))
        self.start_patch(OutstandingToken.objects, 'get_or_create', side_effect=AssertionError('Full JWT storage forbidden'))
        def create(**kw):
            row = UserSession(**kw); row.created_at = timezone.now(); self.session_records[row.pk] = row
            return row
        self.outstanding = self.start_patch(UserSession.objects, 'create', side_effect=create)
        self.for_user = self.start_patch(life.HumanRefreshToken, 'for_user', wraps=life.HumanRefreshToken.for_user)
        query = h.Query(self.session_records, UserSession)
        self.start_patch(UserSession.objects, 'select_related', return_value=query)
        self.start_patch(UserSession.objects, 'select_for_update', return_value=query)
        self.issued_tokens = []
        original_issuer = self.issuer._mock_wraps
        def observe_issuer(user):
            token = original_issuer(user)
            self.issued_tokens.append(token)
            return token
        self.issuer._mock_wraps = observe_issuer

    def assert_session_binding_and_rejection(self):
        # Each inherited success has persisted only identifiers and metadata.
        for row in self.session_records.values():
            self.assertEqual(row.contract_version, life.VERSION)
            self.assertEqual(row.token_family, life.FAMILY)
            self.assertEqual(row.authority_version, self.user.human_auth_version)
            self.assertIsNotNone(row.family_id)
            self.assertNotIn('.', row.token_jti)
        from apps.users.authentication import HumanJWTAuthentication
        auth = HumanJWTAuthentication()
        for token in self.issued_tokens:
            access = str(token.access_token)
            request = self.factory.get('/offline/', HTTP_AUTHORIZATION='Bearer ' + access)
            self.assertEqual(auth.authenticate(request)[0].pk, self.user.pk)
            self.assertEqual(life.revoke(self.user, session_id=token['sid']), 1)
            with self.assertRaises(life.AuthenticationFailed): auth.authenticate(request)
            with self.assertRaises(life.AuthenticationFailed): life.refresh_pair(str(token))


class MFAContractsWithSessions(SessionIssuerAdapter, historical_mfa.TwoFactorContractTests):
    def setUp(self):
        super().setUp(); self.configure_session_store()

    def tearDown(self):
        self.assert_session_binding_and_rejection()


class LoginContractsWithSessions(SessionIssuerAdapter, historical_mfa.JWTIssuanceGateTests):
    def setUp(self):
        super().setUp(); self.configure_session_store()

    def tearDown(self):
        self.assert_session_binding_and_rejection()


class InvitationContractsWithSessions(InvitationLifecycleTests):
    """The original valid-invitation test, with actual new persistence simulated."""
    def fixture(self):
        stack = super().fixture()
        connection = connections['default']
        stack.enter_context(patch.object(connection, 'vendor', 'postgresql'))
        stack.enter_context(patch.object(connection, 'get_autocommit', return_value=True))
        self.session_records = {}; self.live_users = {}
        query = h.Query(self.live_users, User)
        stack.enter_context(patch.object(User.objects, 'select_for_update', return_value=query))
        # The original fixture installed a descriptor-less mock. Use a bound
        # persistence double that records the newly registered User for re-read.
        def persist(user, **kw): self.live_users[user.pk] = user
        def bound_save(user, **kw): self.saved(**kw); persist(user, **kw)
        stack.enter_context(patch.object(User, 'save', new=bound_save))
        def create(**kw):
            row = UserSession(**kw); row.created_at = timezone.now(); self.session_records[row.pk] = row; return row
        stack.enter_context(patch.object(UserSession.objects, 'create', side_effect=create))
        sessions = h.Query(self.session_records, UserSession)
        stack.enter_context(patch.object(UserSession.objects, 'select_related', return_value=sessions))
        stack.enter_context(patch.object(UserSession.objects, 'select_for_update', return_value=sessions))
        self.issued_tokens = []
        original = life.HumanRefreshToken.for_user
        def observe(user):
            token = original(user); self.issued_tokens.append(token); return token
        stack.enter_context(patch.object(life.HumanRefreshToken, 'for_user', side_effect=observe))
        return stack

    def tearDown(self):
        from apps.users.authentication import HumanJWTAuthentication
        auth = HumanJWTAuthentication()
        self.assertEqual(len(self.session_records), 1)
        self.assertEqual(len(self.issued_tokens), 1)
        for token in self.issued_tokens:
            row = self.session_records[uuid.UUID(token['sid'])]
            request = self.factory.get('/offline/', HTTP_AUTHORIZATION='Bearer ' + str(token.access_token))
            self.assertEqual(auth.authenticate(request)[0].pk, row.user_id)
            self.assertEqual(life.revoke(row.user, session_id=row.pk), 1)
            with self.assertRaises(life.AuthenticationFailed): auth.authenticate(request)
            with self.assertRaises(life.AuthenticationFailed): life.refresh_pair(str(token))


class PreparedSchemaTests(unittest.TestCase):
    def test_migration_graph_and_model_state_match_without_database(self):
        from django.apps import apps
        from django.db.migrations.loader import MigrationLoader
        from django.db.migrations.state import ProjectState
        from django.db.migrations.autodetector import MigrationAutodetector
        loader = MigrationLoader(None, ignore_no_migrations=True)
        changes = MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps))._detect_changes()
        self.assertEqual(changes.get('users', []), [])
        target = ('users', '0005_human_jwt_sessions')
        self.assertEqual(loader.disk_migrations[target].dependencies, [('users', '0004_transactional_2fa')])
        loader.graph.ensure_not_cyclic()
        state = loader.project_state([target])
        session = state.apps.get_model('users', 'UserSession')
        self.assertTrue(session._meta.get_field('id').primary_key)
        self.assertTrue(session._meta.get_field('token_jti').unique)
        self.assertTrue(session._meta.get_field('family_id').unique)
        self.assertTrue(session._meta.get_field('family_id').null)
        self.assertTrue(session._meta.get_field('user').db_index)
        self.assertEqual(session._meta.get_field('contract_version').default, 0)
        self.assertEqual(session._meta.get_field('generation').default, 1)
        self.assertEqual(state.apps.get_model('users', 'User')._meta.get_field('human_auth_version').default, 1)

    def test_prepared_trigger_installation_is_postgresql_only_and_captures_sql_without_executing_it(self):
        import importlib
        migration = importlib.import_module('apps.users.migrations.0005_human_jwt_sessions')
        editor = Mock(connection=Mock(vendor='postgresql'))
        migration.install(None, editor)
        editor.execute.assert_called_once_with(migration.FORWARD)
        editor.connection.vendor = 'sqlite'
        with self.assertRaises(RuntimeError): migration.install(None, editor)
        self.assertEqual(editor.execute.call_count, 1)
        sql = migration.FORWARD
        for statement in ('OLD.password IS DISTINCT FROM NEW.password',
                          'OLD.is_active IS DISTINCT FROM NEW.is_active',
                          'OLD.human_auth_version + 1',
                          'NEW.human_auth_version := OLD.human_auth_version;',
                          'generation=generation+1', 'contract_version=1 AND is_active AND revoked_at IS NULL',
                          'NEW.generation < OLD.generation', 'NOT OLD.is_active AND NEW.is_active',
                          'OLD.revoked_at IS NOT NULL', 'NEW.generation <= OLD.generation'):
            self.assertIn(statement, sql)
        migration.uninstall(None, editor)
        editor.execute.assert_called_with(migration.REVERSE)
        print(json.dumps({'schema_review': 'STATIC_ONLY', 'postgresql_sql_executed': False,
                          'migration_applied': False, 'durability': 'NOT_EVIDENCED'}))


if __name__ == '__main__':
    group = sys.argv[1] if len(sys.argv) > 1 else 'integration'
    groups = {'integration': [ClientLifecycleTests],
              'successor-mfa': [MFAContractsWithSessions, LoginContractsWithSessions],
              'schema': [PreparedSchemaTests]}
    if group == 'successor-registration':
        suite = unittest.TestSuite([InvitationContractsWithSessions(
            'test_registration_dispatch_emits_signed_tokens_after_live_consumption')])
    elif group == 'hash-upgrade':
        suite = unittest.TestSuite([ClientLifecycleTests(
            'test_django_password_hash_upgrade_retains_fresh_authority_snapshot')])
    elif group == 'hash-upgrade-race':
        suite = unittest.TestSuite([ClientLifecycleTests(
            'test_concurrent_reset_during_django_hash_upgrade_cannot_be_overwritten')])
    else:
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in groups[group])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   database_attempts=h.DB.call_count, network_attempts=sum(g.call_count for g in h.NETWORK))
    print(json.dumps(summary))
    sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
