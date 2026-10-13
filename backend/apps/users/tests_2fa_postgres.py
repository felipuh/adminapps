"""Real PostgreSQL races using independent connections and deterministic barriers.

Standalone disposable-only runner (does not read .env or application settings):
  REC2FA_LAB_ROOT=/tmp/adminapps-rec2fa03b-pg-... .venv312/bin/python -B \
      apps/users/tests_2fa_postgres.py
Requires a fresh, private initdb cluster with TCP disabled, database rec2fa_lab
owned by nonsuperuser rec2fa_lab_app and port 55483. No SQLite fallback.
"""
import os
from pathlib import Path
import sys
from datetime import timedelta


def configure_lab():
    import stat
    from django.conf import settings
    lab = Path(os.environ['REC2FA_LAB_ROOT']).resolve()
    if (lab.parent != Path('/tmp') or not lab.name.startswith('adminapps-rec2fa03b-pg-')
            or lab.stat().st_uid != os.getuid() or stat.S_IMODE(lab.stat().st_mode) != 0o700
            or not (lab / 'data/PG_VERSION').is_file()):
        raise RuntimeError('Refusing unverified laboratory')
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    settings.configure(
        SECRET_KEY='rec2fa-disposable-laboratory-key-not-for-deployment',
        INSTALLED_APPS=[
            'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
            'rest_framework', 'rest_framework_simplejwt.token_blacklist',
            'apps.organizations', 'apps.users', 'apps.subscriptions', 'apps.products',
            'apps.billing', 'apps.integration',
        ],
        AUTH_USER_MODEL='users.User',
        DATABASES={'default': {
            'ENGINE': 'django.db.backends.postgresql', 'NAME': 'rec2fa_lab',
            'USER': 'rec2fa_lab_app', 'PASSWORD': '', 'HOST': str(lab / 'socket'),
            'PORT': '55483', 'CONN_MAX_AGE': 0,
            'OPTIONS': {'options': '-c statement_timeout=15000 -c lock_timeout=10000'},
        }},
        USE_TZ=True, ROOT_URLCONF=__name__, ALLOWED_HOSTS=['testserver'],
        MIDDLEWARE=[], PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
            'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
            'DEFAULT_THROTTLE_RATES': {'anon': '100000/minute', 'user': '100000/minute'},
        },
        SIMPLE_JWT={'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
                    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
                    'ROTATE_REFRESH_TOKENS': True, 'BLACKLIST_AFTER_ROTATION': True,
                    'UPDATE_LAST_LOGIN': True},
        BILLING_SCHEDULER_ENABLED=False,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='lab@example.invalid',
        TEMP_PASSWORD_MAX_AGE_DAYS=7, TEMP_PASSWORD_WARNING_DAYS=2,
    )
    import django
    django.setup()


if __name__ == '__main__':
    configure_lab()

from concurrent.futures import ThreadPoolExecutor
import json
import threading
import time
from unittest.mock import patch

from django.core import signing
from django.db import connection, connections, transaction, IntegrityError
from django.test import TransactionTestCase, override_settings
from django.urls import include, path
from django.utils import timezone
from rest_framework.exceptions import APIException
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from apps.users import two_factor_service as service, views_2fa
from apps.users.models import User, UserOrganization
from apps.users.models_2fa import TwoFactorAuth, TwoFactorChallenge, TwoFactorAuthLog
from apps.users.serializers import CustomTokenObtainPairSerializer
from apps.organizations.models import Organization
from apps.integration import sso_views

urlpatterns = [
    path('api/auth/', include('apps.users.urls')),
    path('sso/login/', sso_views.sso_login),
    path('sso/verify/', sso_views.sso_login_verify_2fa),
]


class AntiReplayPostgresTests(TransactionTestCase):
    def setUp(self):
        self.assertEqual(connection.vendor, 'postgresql', 'PostgreSQL required')
        self.org = Organization.objects.create(code='ARLAB', name='Lab', status='active')
        self.user = User.objects.create_user(
            email='rec2fa@example.invalid', password='LabPassword!12345', organization=self.org,
        )
        self.config = TwoFactorAuth(user=self.user, is_enabled=True)
        self.config.secret = 'JBSWY3DPEHPK3PXP'
        self.config.backup_codes = 'A1B2C3D4,ABCDEF12'
        self.config.save()
        UserOrganization.objects.create(user=self.user, organization=self.org, role='user', is_active=True)
        self.factor = self.config.get_totp().now()
        self.client = APIClient()

    def challenge(self, channel='login'):
        return service.issue_challenge(self.user, channel, context=(
            {'organization_id': str(self.org.pk), 'client_id': 'lab', 'audience': ['lab']}
            if channel == 'sso' else None))

    def post(self, challenge, factor, channel='login'):
        client = APIClient()
        if channel == 'sso':
            response = client.post('/sso/verify/', {'challenge_token': challenge, 'otp_code': factor}, format='json')
        else:
            response = client.post('/api/auth/2fa/verify/', {'token': factor}, format='json',
                                   HTTP_AUTHORIZATION='Bearer ' + challenge)
        return response.status_code, json.loads(response.content)

    def race(self, operations):
        barrier = threading.Barrier(len(operations))
        def worker(fn):
            connections.close_all()
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pid = cursor.fetchone()[0]
                barrier.wait(timeout=10)
                return pid, fn()
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            results = list(pool.map(worker, operations))
        self.assertEqual(len({pid for pid, _ in results}), len(operations))
        return [result for _, result in results]

    def exactly_one(self, operations):
        results = self.race(operations)
        self.assertEqual([status for status, _ in results].count(200), 1, results)
        for status, body in results:
            if status != 200:
                self.assertIn(status, (400, 401, 403), body)
                self.assertFalse({'access', 'refresh', 'tokens'}.intersection(body))
        self.assertEqual(OutstandingToken.objects.count(), 1)

    def test_ar_t01_same_challenge(self):
        challenge = self.challenge()
        self.exactly_one([lambda: self.post(challenge, self.factor)] * 2)
        self.assertEqual(TwoFactorChallenge.objects.filter(consumed_at__isnull=False).count(), 1)

    def test_ar_t02_same_totp_distinct_challenges(self):
        a, b = self.challenge(), self.challenge()
        self.assertNotEqual(a, b)
        self.exactly_one([lambda: self.post(a, self.factor), lambda: self.post(b, self.factor)])

    def test_ar_t03_same_backup_distinct_challenges(self):
        a, b = self.challenge(), self.challenge()
        self.exactly_one([lambda: self.post(a, 'A1B2C3D4'), lambda: self.post(b, 'A1B2C3D4')])
        self.config.refresh_from_db()
        self.assertEqual(self.config.backup_codes_used, [0])

    def test_ar_t04_login_sso_same_factor(self):
        for factor in (self.factor, 'A1B2C3D4'):
            with self.subTest(backup=factor == 'A1B2C3D4'):
                OutstandingToken.objects.all().delete()
                a, b = self.challenge(), self.challenge('sso')
                self.exactly_one([lambda: self.post(a, factor), lambda: self.post(b, factor, 'sso')])

    def test_ar_t05_shared_five_failures(self):
        challenges = [self.challenge('sso' if i % 2 else 'login') for i in range(5)]
        results = self.race([lambda i=i: self.post(challenges[i], 'invalid', 'sso' if i % 2 else 'login')
                             for i in range(5)])
        self.assertEqual([status for status, _ in results], [400, 401, 400, 401, 400])
        self.config.refresh_from_db()
        self.assertEqual(self.config.failed_attempts, 5)
        self.assertAlmostEqual((self.config.attempts_expires_at - timezone.now()).total_seconds(), 900, delta=5)
        self.assertEqual(self.post(challenges[0], self.factor)[0], 403)
        self.assertEqual(OutstandingToken.objects.count(), 0)
        self.assertEqual(TwoFactorAuthLog.objects.filter(event_type='token_failed').count(), 5)

    def test_ar_t06_expiration_after_lock_wait(self):
        challenge = self.challenge()
        expiry = timezone.now() + timedelta(seconds=1)
        TwoFactorChallenge.objects.update(expires_at=expiry)
        # Hold a real row lock; observe the second backend actually waiting on it.
        ready = threading.Event()
        worker_pid = []
        def worker():
            connections.close_all()
            try:
                with connection.cursor() as c:
                    c.execute('SELECT pg_backend_pid()')
                    worker_pid.append(c.fetchone()[0])
                ready.set()
                return self.post(challenge, self.factor)
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                User.objects.select_for_update().get(pk=self.user.pk)
                future = pool.submit(worker)
                self.assertTrue(ready.wait(5))
                deadline = time.monotonic() + 5
                while True:
                    with connection.cursor() as c:
                        c.execute('SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s', [worker_pid[0]])
                        waiting = c.fetchone()[0] == 'Lock'
                    if waiting:
                        break
                    self.assertLess(time.monotonic(), deadline, 'worker never blocked')
                    time.sleep(.01)
                # Let the real wall clock pass the stored deadline under the lock.
                time.sleep(max(0, (expiry - timezone.now()).total_seconds()) + .05)
            self.assertEqual(future.result(timeout=10)[0], 403)
        self.assertEqual(OutstandingToken.objects.count(), 0)

    def test_ar_t07_real_postgresql_unavailable(self):
        challenges = {c: self.challenge(c) for c in ('login', 'sso')}
        original = dict(connection.settings_dict)
        connection.close()
        try:
            connection.settings_dict['HOST'] = str(Path(original['HOST']).parent / 'absent-socket')
            with patch.object(CustomTokenObtainPairSerializer, 'get_token', wraps=CustomTokenObtainPairSerializer.get_token) as issuer:
                for channel in ('login', 'sso'):
                    status, body = self.post(challenges[channel], self.factor, channel)
                    self.assertEqual(status, 503)
                    self.assertNotIn('absent-socket', str(body))
                for endpoint in ('/api/auth/login/', '/sso/login/'):
                    response = self.client.post(endpoint, {'email': self.user.email, 'password': 'LabPassword!12345'}, format='json')
                    self.assertEqual(response.status_code, 503)
                    self.assertNotIn('absent-socket', str(response.content))
                issuer.assert_not_called()
        finally:
            connection.close()
            connection.settings_dict.update(original)
        self.assertEqual(OutstandingToken.objects.count(), 0)
        self.assertFalse(TwoFactorChallenge.objects.exclude(consumed_at=None).exists())

    def test_ar_t08_issuer_failure_keeps_consumption(self):
        challenge = self.challenge()
        with patch.object(CustomTokenObtainPairSerializer, 'get_token', side_effect=RuntimeError('private issuer detail')):
            status, body = self.post(challenge, self.factor)
        self.assertEqual(status, 500)
        self.assertNotIn('private issuer detail', str(body))
        self.assertEqual(self.post(challenge, 'ABCDEF12')[0], 403)
        self.assertEqual(self.post(self.challenge(), self.factor)[0], 400)
        self.assertEqual(self.post(self.challenge(), 'ABCDEF12')[0], 200)

    def test_sso_issuer_failure_and_commit_visibility(self):
        challenge = self.challenge('sso')
        def issue(*args, **kwargs):
            self.assertFalse(connection.in_atomic_block)
            def observer():
                connections.close_all()
                try:
                    return TwoFactorChallenge.objects.filter(consumed_at__isnull=False).count()
                finally:
                    connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as pool:
                self.assertEqual(pool.submit(observer).result(timeout=5), 1)
            raise RuntimeError('private issuer detail')
        with patch.object(sso_views, '_build_token_pair_unchecked', side_effect=issue):
            status, body = self.post(challenge, self.factor, 'sso')
        self.assertEqual(status, 500)
        self.assertNotIn('private issuer detail', str(body))
        self.assertEqual(self.post(challenge, 'A1B2C3D4', 'sso')[0], 401)
        self.assertEqual(self.post(self.challenge(), self.factor)[0], 400)

    def test_ar_t09_generation_change_invalidates_pending(self):
        old = self.challenge()
        service.disable_configuration(self.user.pk)
        secret = service.initiate_configuration(self.user.pk)
        import pyotp
        config, _ = service.verify_configuration(self.user.pk, pyotp.TOTP(secret).now())
        self.assertNotEqual(config.generation, self.config.generation)
        self.assertEqual(self.post(old, 'A1B2C3D4')[0], 403)
        # Setup itself consumed the matching TOTP counter.
        self.assertEqual(self.post(self.challenge(), pyotp.TOTP(secret).now())[0], 400)

    def test_ar_t10_legacy_rejected_both_channels(self):
        for channel, salt in [('login', 'adminapps.2fa.login'), ('sso', 'smart3ai.sso.2fa')]:
            old = signing.dumps({'user_id': str(self.user.pk)}, salt=salt)
            self.assertEqual(self.post(old, self.factor, channel)[0], 401 if channel == 'sso' else 403)
        self.assertEqual(OutstandingToken.objects.count(), 0)

    def test_ar_t11_standard_login_and_refresh_logout(self):
        self.config.is_enabled = False
        self.config.save()
        result = self.client.post('/api/auth/login/', {'email': self.user.email, 'password': 'LabPassword!12345'})
        self.assertEqual(result.status_code, 200, result.data)
        access = AccessToken(result.data['access'])
        self.assertEqual(access['email'], self.user.email)
        old = result.data['refresh']
        rotated = self.client.post('/api/auth/refresh/', {'refresh': old})
        self.assertEqual(rotated.status_code, 200)
        self.assertNotEqual(rotated.data['refresh'], old)
        self.assertEqual(self.client.post('/api/auth/refresh/', {'refresh': old}).status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + rotated.data['access'])
        logout = self.client.post('/api/auth/logout/', {'refresh': rotated.data['refresh']})
        self.assertIn(logout.status_code, (200, 204))
        self.assertEqual(self.client.post('/api/auth/refresh/', {'refresh': rotated.data['refresh']}).status_code, 401)

    def test_ar_t12_issuer_sees_committed_consumption(self):
        challenge = self.challenge()
        original = CustomTokenObtainPairSerializer.get_token
        def issue(user):
            self.assertFalse(connection.in_atomic_block)
            def observer():
                connections.close_all()
                try:
                    return TwoFactorChallenge.objects.filter(consumed_at__isnull=False).count()
                finally:
                    connections.close_all()
            with ThreadPoolExecutor(max_workers=1) as pool:
                self.assertEqual(pool.submit(observer).result(timeout=5), 1)
            return original(user)
        with patch.object(CustomTokenObtainPairSerializer, 'get_token', side_effect=issue):
            self.assertEqual(self.post(challenge, self.factor)[0], 200)
        # Lost response: same challenge and same factor remain ineligible.
        self.assertEqual(self.post(challenge, self.factor)[0], 403)
        self.assertEqual(self.post(self.challenge(), self.factor)[0], 400)

    def test_ar_t13_audit_contains_no_credentials(self):
        challenge = self.challenge()
        status, body = self.post(challenge, 'A1B2C3D4')
        self.assertEqual(status, 200)
        logs = json.dumps(list(TwoFactorAuthLog.objects.values()), default=str)
        for secret in [self.config.secret, 'A1B2C3D4', self.factor, challenge, body['access'], body['refresh']]:
            self.assertNotIn(secret, logs)

    def test_outer_transaction_rejected_even_testcase_style(self):
        challenge = self.challenge()
        with transaction.atomic():
            self.assertEqual(self.post(challenge, self.factor)[0], 503)
        self.assertEqual(self.post(challenge, self.factor)[0], 200)

    def test_atomic_requests_exemption_and_direct_transaction_guard(self):
        self.assertIn('default', views_2fa.verify_2fa_token._non_atomic_requests)
        self.assertIn('default', sso_views.sso_login._non_atomic_requests)
        self.assertIn('default', sso_views.sso_login_verify_2fa._non_atomic_requests)
        challenge = self.challenge()
        connection.settings_dict['ATOMIC_REQUESTS'] = True
        try:
            self.assertEqual(self.post(challenge, self.factor)[0], 200)
        finally:
            connection.settings_dict['ATOMIC_REQUESTS'] = False

    @override_settings(SMART3AI_SSO_ALLOW_2FA_BYPASS=True)
    def test_sso_inline_otp_and_no_bypass(self):
        credentials = {'email': self.user.email, 'password': 'LabPassword!12345'}
        result = self.client.post('/sso/login/', {**credentials, 'otp_code': 'BYPASS-LOCAL-2FA'}, format='json')
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.json()['code'], 'invalid_otp')
        result = self.client.post('/sso/login/', {**credentials, 'otp_code': 'A1B2C3D4'}, format='json')
        self.assertEqual(result.status_code, 200, result.content)
        self.assertFalse(result.json()['two_fa_bypassed'])
        self.assertEqual(self.post(self.challenge(), 'A1B2C3D4')[0], 400)

    def test_model_consumers_share_replay_state(self):
        self.assertTrue(self.config.verify_token(self.factor))
        self.assertEqual(self.post(self.challenge(), self.factor)[0], 400)
        self.assertTrue(self.config.use_backup_code('A1B2C3D4'))
        self.config.save()  # Refreshed instance must not overwrite consumption.
        self.assertEqual(self.post(self.challenge('sso'), 'A1B2C3D4', 'sso')[0], 401)

    def test_setup_endpoints_share_ledger_and_disable_requires_password(self):
        service.disable_configuration(self.user.pk)
        self.client.force_authenticate(self.user)
        started = self.client.post('/api/auth/2fa/setup/initiate/')
        self.assertEqual(started.status_code, 200)
        import pyotp
        otp = pyotp.TOTP(started.data['secret']).now()
        wrong = self.client.post('/api/auth/2fa/setup/verify/', {'token': 'invalid'})
        self.assertEqual(wrong.status_code, 400)
        self.config.refresh_from_db()
        self.assertEqual(self.config.failed_attempts, 1)
        verified = self.client.post('/api/auth/2fa/setup/verify/', {'token': otp})
        self.assertEqual(verified.status_code, 201)
        self.assertEqual(len(verified.data['backup_codes']), 10)
        repeated = self.client.post('/api/auth/2fa/setup/verify/', {'token': otp})
        self.assertEqual(repeated.status_code, 400)
        self.assertEqual(self.post(self.challenge(), otp)[0], 400)
        self.assertEqual(self.client.post('/api/auth/2fa/disable/', {'password': 'wrong'}).status_code, 403)
        self.assertEqual(self.client.post('/api/auth/2fa/disable/', {'password': 'LabPassword!12345'}).status_code, 200)

    def test_unique_nonce_digest_and_no_plaintext_challenge(self):
        challenge = self.challenge()
        payload = service.decode_challenge(challenge)
        self.assertEqual(len(bytes.fromhex(payload['nonce'])), 32)
        row = TwoFactorChallenge.objects.get()
        self.assertNotIn(payload['nonce'], json.dumps(row.__dict__, default=str))
        with self.assertRaises(IntegrityError), transaction.atomic():
            row.pk = row.nonce_digest
            row.save(force_insert=True)

    def test_totp_window_and_counter_monotonicity(self):
        now = timezone.now()
        totp = self.config.get_totp()
        for delta in (-1, 0, 1):
            factor = totp.at(now + timedelta(seconds=delta * totp.interval))
            with patch.object(service.timezone, 'now', return_value=now):
                self.assertEqual(self.post(self.challenge(), factor)[0], 200)
        with patch.object(service.timezone, 'now', return_value=now):
            self.assertEqual(self.post(self.challenge(), totp.at(now))[0], 400)
            self.assertEqual(self.post(self.challenge(), totp.at(now + timedelta(seconds=60)))[0], 400)

    def test_account_gates_rechecked_and_scope_bound(self):
        challenge = self.challenge()
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.post(challenge, self.factor)[0], 403)
        self.user.is_active = True
        self.user.mark_temporary_password(when=timezone.now() - timedelta(days=8))
        self.user.save()
        self.assertEqual(self.post(challenge, self.factor)[0], 403)
        self.user.clear_temporary_password()
        self.user.save()
        payload = service.decode_challenge(challenge)
        payload['email'] = 'changed@example.invalid'
        tampered = signing.dumps(payload, salt='adminapps.2fa.login')
        self.assertEqual(self.post(tampered, self.factor)[0], 403)


if __name__ == '__main__':
    from django.core.management import call_command
    from django.db.migrations.executor import MigrationExecutor
    from django.test.runner import DiscoverRunner
    with connection.cursor() as cursor:
        cursor.execute('SHOW listen_addresses')
        assert cursor.fetchone()[0] == '', 'TCP must be disabled'
        cursor.execute('SELECT current_database(), current_user, inet_server_addr()')
        assert cursor.fetchone() == ('rec2fa_lab', 'rec2fa_lab_app', None)
        cursor.execute('SELECT rolsuper, rolcreaterole FROM pg_roles WHERE rolname=current_user')
        assert cursor.fetchone() == (False, False)
        cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
        assert cursor.fetchone()[0] == 0, 'Refusing nonempty database; create a fresh task-owned lab'
    executor = MigrationExecutor(connection)
    targets = [node for node in executor.loader.graph.leaf_nodes()
               if node[0] in ('users', 'organizations', 'products', 'token_blacklist', 'sessions')]
    print('LAB VERIFIED: private Unix socket, no TCP, empty database, nonsuperuser role', flush=True)
    print('MIGRATION PLAN:', [f'{m.app_label}.{m.name}' for m, backwards in executor.migration_plan(targets)], flush=True)
    executor.migrate(targets)
    call_command('check', verbosity=1)
    call_command('makemigrations', 'users', check=True, dry_run=True, verbosity=1)
    class LabRunner(DiscoverRunner):
        def setup_databases(self, **kwargs):
            return []  # Already migrated the verified disposable database above.
        def teardown_databases(self, old_config, **kwargs):
            pass
    labels = [__name__ + '.AntiReplayPostgresTests',
              'apps.users.tests.AuthSecurityRegressionTests']
    sys.exit(bool(LabRunner(verbosity=2).run_tests(labels)))
