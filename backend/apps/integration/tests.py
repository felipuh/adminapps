import hashlib
from io import StringIO
from threading import Barrier, Thread
from unittest.mock import patch

from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command, CommandError
from django.db import connection, close_old_connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.integration.models import (
    DemoRequest,
    IntegrationAPIKey,
    IntegrationAPIKeyAuditEvent,
)
from apps.integration.services import (
    create_integration_api_key,
    integration_api_key_fingerprint,
    rotate_integration_api_key,
)
from apps.organizations.models import Organization
from apps.products.models import OrganizationProductEntitlement, ProductSystem
from apps.subscriptions.models import Plan, Subscription
from apps.users.models import User, UserOrganization


def create_legacy_api_key_fixture(*, name, key, is_active=True):
    credential = IntegrationAPIKey(
        name=name,
        key=key,
        credential_format='legacy_plaintext',
        is_active=is_active,
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )
    credential.save_base(raw=True)
    return credential


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class IntegrationAPIKeyUsageTests(APITestCase):
    def test_integration_health_rejects_missing_api_key(self):
        response = self.client.get('/api/integration/health/')

        self.assertEqual(response.status_code, 401)

    def test_integration_health_rejects_invalid_api_key(self):
        response = self.client.get(
            '/api/integration/health/',
            HTTP_X_API_KEY='not-a-valid-key',
        )

        self.assertEqual(response.status_code, 401)

    def test_persisted_api_key_tracks_last_usage(self):
        api_key = IntegrationAPIKey.objects.create(
            name='medsupplier-service',
            key='integration-key-for-usage-test',
            is_active=True,
        )

        response = self.client.get(
            '/api/integration/health/',
            HTTP_X_API_KEY='integration-key-for-usage-test',
        )

        self.assertEqual(response.status_code, 200)
        api_key.refresh_from_db()
        self.assertIsNotNone(api_key.last_used_at)
        self.assertEqual(api_key.last_used_service, 'medsupplier-service')

    @override_settings(
        ENVIRONMENT='production',
        INTEGRATION_API_KEYS={'isosmart': ''},
    )
    def test_production_requires_explicit_integration_key(self):
        response = self.client.get(
            '/api/integration/health/',
            HTTP_X_API_KEY='dev-only-default-key',
        )

        self.assertEqual(response.status_code, 401)

    @override_settings(
        ENVIRONMENT='development',
        INTEGRATION_API_KEYS={
            'isosmart': hashlib.sha256('local-demo-key'.encode()).hexdigest(),
        },
    )
    def test_development_can_use_explicit_settings_hash(self):
        response = self.client.get(
            '/api/integration/health/',
            HTTP_X_API_KEY='local-demo-key',
        )

        self.assertEqual(response.status_code, 200)


class SecureIntegrationAPIKeyLifecycleTests(APITestCase):
    def setUp(self):
        self.operator = User.objects.create_superuser(
            email='rotation-operator@example.test',
            password='synthetic-test-password',
            first_name='Rotation',
            last_name='Operator',
        )

    def _request_health(self, key):
        return self.client.get(
            '/api/integration/health/',
            HTTP_X_API_KEY=key,
        )

    def test_secure_creation_persists_only_verifier_and_fingerprint(self):
        credential, raw_key = create_integration_api_key(
            name='synthetic-service',
            operator=self.operator,
        )
        credential.refresh_from_db()

        self.assertIsNone(credential.key)
        self.assertNotEqual(credential.credential_hash, raw_key)
        self.assertEqual(credential.credential_format, 'hashed_v1')
        self.assertEqual(credential.status, 'active')
        self.assertTrue(credential.credential_hash)
        self.assertEqual(
            credential.fingerprint,
            integration_api_key_fingerprint(raw_key),
        )
        self.assertNotEqual(credential.fingerprint, raw_key)
        self.assertNotIn(raw_key, repr(credential.__dict__))
        self.assertTrue(
            IntegrationAPIKeyAuditEvent.objects.filter(
                action='created',
                new_credential=credential,
                new_fingerprint=credential.fingerprint,
                actor=self.operator,
            ).exists()
        )

    def test_direct_orm_creation_hashes_new_key_before_persistence(self):
        raw_key = 'synthetic-direct-model-key'
        credential = IntegrationAPIKey.objects.create(
            name='synthetic-direct-model-service',
            key=raw_key,
            is_active=True,
        )
        credential.refresh_from_db()

        self.assertIsNone(credential.key)
        self.assertEqual(credential.credential_format, 'hashed_v1')
        self.assertNotEqual(credential.credential_hash, raw_key)
        self.assertEqual(self._request_health(raw_key).status_code, 200)

    def test_revoked_lifecycle_state_cannot_be_reactivated(self):
        credential = IntegrationAPIKey.objects.create(
            name='synthetic-revocation-service',
            key='synthetic-revocation-token',
            is_active=True,
        )
        credential.is_active = False
        credential.save(update_fields=['is_active'])
        credential.refresh_from_db()

        self.assertEqual(credential.status, 'revoked')
        self.assertIsNotNone(credential.revoked_at)

        credential.is_active = True
        credential.save(update_fields=['is_active'])
        credential.refresh_from_db()
        self.assertEqual(credential.status, 'revoked')
        self.assertFalse(credential.is_active)
        self.assertEqual(self._request_health('synthetic-revocation-token').status_code, 401)

    def test_fingerprint_is_deterministic_and_not_the_auth_verifier(self):
        credential, raw_key = create_integration_api_key(
            name='synthetic-service',
            operator=self.operator,
        )

        fingerprint = integration_api_key_fingerprint(raw_key)
        self.assertEqual(fingerprint, integration_api_key_fingerprint(raw_key))
        self.assertTrue(fingerprint.startswith('hmac-sha256-v1:'))
        self.assertNotEqual(fingerprint, credential.credential_hash)

    def test_new_key_authenticates_and_wrong_or_malformed_keys_do_not(self):
        _, raw_key = create_integration_api_key(
            name='synthetic-service',
            operator=self.operator,
        )

        self.assertEqual(self._request_health(raw_key).status_code, 200)
        self.assertEqual(self._request_health(raw_key + 'wrong').status_code, 401)
        self.assertEqual(self._request_health('iak-malformed').status_code, 401)

    def test_legacy_key_authenticates_until_rotation_then_is_removed_and_rejected(self):
        old_key = 'legacy-synthetic-rotation-token'
        legacy = create_legacy_api_key_fixture(
            name='synthetic-service',
            key=old_key,
            is_active=True,
        )
        self.assertEqual(self._request_health(old_key).status_code, 200)

        replacement, raw_replacement = rotate_integration_api_key(
            credential_id=legacy.pk,
            operator=self.operator,
        )
        legacy.refresh_from_db()

        self.assertEqual(legacy.status, 'rotated')
        self.assertFalse(legacy.is_active)
        self.assertIsNotNone(legacy.revoked_at)
        self.assertIsNotNone(legacy.rotated_at)
        self.assertEqual(legacy.replaced_by_id, replacement.pk)
        self.assertIsNone(legacy.key)
        self.assertEqual(legacy.credential_format, 'hashed_v1')
        with override_settings(INTEGRATION_API_KEYS={
            'synthetic-service': hashlib.sha256(old_key.encode()).hexdigest(),
        }):
            self.assertEqual(self._request_health(old_key).status_code, 401)
        self.assertEqual(self._request_health(raw_replacement).status_code, 200)
        self.assertNotEqual(legacy.fingerprint, replacement.fingerprint)

    def test_rotation_records_secret_free_audit_event(self):
        old_key = 'legacy-synthetic-audit-token'
        legacy = create_legacy_api_key_fixture(
            name='synthetic-audit-service',
            key=old_key,
            is_active=True,
        )

        replacement, raw_replacement = rotate_integration_api_key(
            credential_id=legacy.pk,
            operator=self.operator,
        )
        event = IntegrationAPIKeyAuditEvent.objects.get(action='rotated')
        legacy.refresh_from_db()

        self.assertEqual(event.old_credential_id, legacy.pk)
        self.assertEqual(event.new_credential_id, replacement.pk)
        self.assertEqual(event.old_fingerprint, legacy.fingerprint)
        self.assertEqual(event.new_fingerprint, replacement.fingerprint)
        self.assertEqual(event.actor, self.operator)
        self.assertNotIn(old_key, repr(event.__dict__))
        self.assertNotIn(raw_replacement, repr(event.__dict__))
        self.assertNotIn(replacement.credential_hash, repr(event.__dict__))
        self.assertNotIn('credential_hash', event.metadata)
        self.assertNotIn('api_key', event.metadata)

    def test_failed_audit_write_rolls_back_replacement_and_revocation(self):
        legacy = create_legacy_api_key_fixture(
            name='synthetic-rollback-service',
            key='legacy-synthetic-rollback-token',
            is_active=True,
        )

        with patch(
            'apps.integration.services.IntegrationAPIKeyAuditEvent.objects.create',
            side_effect=RuntimeError('synthetic audit failure'),
        ):
            with self.assertRaises(RuntimeError):
                rotate_integration_api_key(
                    credential_id=legacy.pk,
                    operator=self.operator,
                )

        legacy.refresh_from_db()
        self.assertEqual(IntegrationAPIKey.objects.count(), 1)
        self.assertEqual(legacy.status, 'active')
        self.assertTrue(legacy.is_active)
        self.assertEqual(legacy.key, 'legacy-synthetic-rollback-token')
        self.assertEqual(IntegrationAPIKeyAuditEvent.objects.count(), 0)

    def test_lifecycle_operations_require_an_active_staff_operator(self):
        non_staff = User.objects.create_user(
            email='non-staff@example.test',
            password='synthetic-test-password',
            first_name='Non',
            last_name='Staff',
            is_active=True,
            is_staff=False,
        )

        with self.assertRaises(PermissionDenied):
            create_integration_api_key(name='synthetic-service', operator=non_staff)

    def test_admin_never_exposes_raw_key_or_verifier_and_is_read_only(self):
        model_admin = admin.site._registry[IntegrationAPIKey]
        legacy = create_legacy_api_key_fixture(
            name='synthetic-admin-service',
            key='legacy-synthetic-admin-token',
            is_active=True,
        )

        self.assertNotIn('key', model_admin.list_display)
        self.assertNotIn('credential_hash', model_admin.list_display)
        self.assertNotIn('key', model_admin.search_fields)
        self.assertNotIn('credential_hash', model_admin.search_fields)
        self.assertNotIn('key', model_admin.fields)
        self.assertNotIn('credential_hash', model_admin.fields)
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))

        self.client.force_login(self.operator)
        list_response = self.client.get('/admin/integration/integrationapikey/')
        detail_response = self.client.get(
            f'/admin/integration/integrationapikey/{legacy.pk}/change/'
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(detail_response.status_code, 200)
        self.assertNotContains(list_response, 'legacy-synthetic-admin-token')
        self.assertNotContains(detail_response, 'legacy-synthetic-admin-token')
        self.assertNotContains(detail_response, 'credential_hash')

    def test_create_command_generates_key_without_secret_cli_argument(self):
        output = StringIO()
        call_command(
            'create_integration_key',
            '--name',
            'synthetic-command-service',
            '--actor-id',
            str(self.operator.pk),
            stdout=output,
        )
        rendered = output.getvalue()
        credential = IntegrationAPIKey.objects.get(name='synthetic-command-service')

        self.assertIn('cannot be recovered later', rendered)
        self.assertIn('API key (one-time):', rendered)
        raw_key = next(
            line.split(': ', 1)[1]
            for line in rendered.splitlines()
            if line.startswith('API key (one-time): ')
        )
        self.assertEqual(rendered.count(raw_key), 1)
        self.assertIsNone(credential.key)
        self.assertNotIn(raw_key, credential.credential_hash)
        self.assertEqual(credential.credential_format, 'hashed_v1')

        with self.assertRaises(CommandError):
            call_command(
                'create_integration_key',
                '--name',
                'should-not-be-created',
                '--actor-id',
                str(self.operator.pk),
                '--key',
                'synthetic-cli-secret',
                stdout=StringIO(),
            )
        self.assertFalse(
            IntegrationAPIKey.objects.filter(name='should-not-be-created').exists()
        )

    def test_rotation_command_uses_only_record_and_operator_ids(self):
        legacy = create_legacy_api_key_fixture(
            name='synthetic-command-rotation',
            key='legacy-synthetic-command-token',
            is_active=True,
        )
        output = StringIO()

        call_command(
            'rotate_integration_key',
            '--id',
            str(legacy.pk),
            '--actor-id',
            str(self.operator.pk),
            stdout=output,
        )

        self.assertIn('API key (one-time): iak_', output.getvalue())
        legacy.refresh_from_db()
        self.assertEqual(legacy.status, 'rotated')
        self.assertIsNone(legacy.key)


class IntegrationAPIKeyLegacyMigrationTests(TransactionTestCase):
    migrate_from = [('integration', '0005_demorequest')]
    migrate_to = [('integration', '0006_integration_api_key_lifecycle')]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps
        legacy_model = old_apps.get_model('integration', 'IntegrationAPIKey')
        legacy_model.objects.create(
            name='synthetic-migration-active',
            key='migration-synthetic-active-token',
            is_active=True,
        )
        legacy_model.objects.create(
            name='synthetic-migration-inactive',
            key='migration-synthetic-inactive-token',
            is_active=False,
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        migrated_apps = executor.loader.project_state(self.migrate_to).apps
        self.migrated_model = migrated_apps.get_model(
            'integration',
            'IntegrationAPIKey',
        )

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_keys_are_classified_without_rewriting_legacy_values(self):
        active = self.migrated_model.objects.get(name='synthetic-migration-active')
        inactive = self.migrated_model.objects.get(name='synthetic-migration-inactive')

        self.assertEqual(active.key, 'migration-synthetic-active-token')
        self.assertEqual(active.credential_format, 'legacy_plaintext')
        self.assertEqual(active.status, 'active')
        self.assertEqual(inactive.key, 'migration-synthetic-inactive-token')
        self.assertEqual(inactive.credential_format, 'legacy_plaintext')
        self.assertEqual(inactive.status, 'revoked')


class PostgreSQLIntegrationAPIKeyRotationConcurrencyTests(TransactionTestCase):
    def test_concurrent_rotations_allow_only_one_replacement(self):
        if connection.vendor != 'postgresql':
            self.skipTest('PostgreSQL row-lock concurrency test requires PostgreSQL.')

        operator = User.objects.create_superuser(
            email='concurrent-rotation@example.test',
            password='synthetic-test-password',
            first_name='Concurrent',
            last_name='Operator',
        )
        original = create_legacy_api_key_fixture(
            name='synthetic-concurrent-service',
            key='legacy-synthetic-concurrent-token',
            is_active=True,
        )
        barrier = Barrier(2)
        outcomes = []

        def rotate():
            close_old_connections()
            try:
                thread_operator = User.objects.get(pk=operator.pk)
                barrier.wait(timeout=10)
                rotate_integration_api_key(
                    credential_id=original.pk,
                    operator=thread_operator,
                )
                outcomes.append('rotated')
            except ValidationError:
                outcomes.append('rejected')
            finally:
                close_old_connections()

        threads = [Thread(target=rotate) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertCountEqual(outcomes, ['rotated', 'rejected'])
        original.refresh_from_db()
        self.assertEqual(original.status, 'rotated')
        self.assertEqual(
            IntegrationAPIKey.objects.filter(
                name='synthetic-concurrent-service',
                status='active',
            ).count(),
            1,
        )


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DemoRequestIntegrationTests(APITestCase):
    def setUp(self):
        self.api_key = IntegrationAPIKey.objects.create(
            name='landing_demo',
            key='demo-request-contract-key',
            is_active=True,
        )
        self.payload = {
            'request_id': 'f30e6c84-ec2c-49ec-b3e6-0a6f4d0ee00a',
            'name': 'Ana Calidad',
            'email': 'ANA@EXAMPLE.COM',
            'organization': 'Example Quality',
            'product': 'ISO_SMART',
            'priority': 'audit_readiness',
            'consent': True,
            'source': 'landing',
            'page_url': 'https://example.com/',
        }

    def _post(self, payload=None, key='demo-request-contract-key'):
        return self.client.post(
            '/api/integration/demo-requests/',
            payload if payload is not None else self.payload,
            format='json',
            HTTP_X_API_KEY=key,
        )

    def test_rejects_missing_api_key(self):
        response = self.client.post('/api/integration/demo-requests/', self.payload, format='json')

        self.assertEqual(response.status_code, 401)
        self.assertEqual(DemoRequest.objects.count(), 0)

    def test_rejects_invalid_fields_and_missing_consent(self):
        response = self._post({
            **self.payload,
            'email': 'invalid',
            'priority': 'unknown',
            'consent': False,
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], 'validation_error')
        self.assertIn('email', response.json()['fields'])
        self.assertIn('priority', response.json()['fields'])
        self.assertIn('consent', response.json()['fields'])
        self.assertEqual(DemoRequest.objects.count(), 0)

    def test_creates_pretenant_request_without_creating_organization_or_user(self):
        organizations_before = Organization.objects.count()
        users_before = User.objects.count()

        response = self._post()

        self.assertEqual(response.status_code, 201)
        request_record = DemoRequest.objects.get()
        self.assertEqual(request_record.work_email, 'ana@example.com')
        self.assertEqual(request_record.status, 'new')
        self.assertEqual(request_record.source_service, 'landing_demo')
        self.assertTrue(request_record.consent_given)
        self.assertEqual(Organization.objects.count(), organizations_before)
        self.assertEqual(User.objects.count(), users_before)

    def test_is_idempotent_for_same_external_request(self):
        first = self._post()
        second = self._post()

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.json()['created'])
        self.assertEqual(DemoRequest.objects.count(), 1)

    def test_rejects_unapproved_integration_service(self):
        IntegrationAPIKey.objects.create(name='isosmart-service', key='wrong-service-key', is_active=True)

        response = self._post(key='wrong-service-key')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 'service_not_allowed')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class IntegrationContractTests(APITestCase):
    def setUp(self):
        self.api_key = IntegrationAPIKey.objects.create(
            name='isosmart-service',
            key='contract-key',
            is_active=True,
        )
        self.org_a = Organization.objects.create(
            code='ORG-A',
            name='Org A',
            email='orga@example.com',
            status='active',
        )
        self.org_b = Organization.objects.create(
            code='ORG-B',
            name='Org B',
            email='orgb@example.com',
            status='active',
        )
        self.product, _ = ProductSystem.objects.update_or_create(
            code='ISO_SMART',
            defaults={
                'name': 'ISO Smart',
                'slug': 'iso-smart-contract',
                'status': 'active',
                'billing_enabled': False,
            },
        )
        self.med_product, _ = ProductSystem.objects.update_or_create(
            code='MEDSUPPLIER',
            defaults={
                'name': 'ISO Smart MedSupplier',
                'slug': 'medsupplier-contract',
                'status': 'active',
                'billing_enabled': False,
            },
        )
        self.entitlement_a = OrganizationProductEntitlement.objects.create(
            organization=self.org_a,
            product=self.product,
            status='active',
            enabled=True,
            scopes=['qms'],
        )
        OrganizationProductEntitlement.objects.create(
            organization=self.org_b,
            product=self.product,
            status='suspended',
            enabled=True,
            scopes=['qms'],
        )

    def _get(self, path, key='contract-key'):
        return self.client.get(path, HTTP_X_API_KEY=key)

    def test_isosmart_contract_allows_valid_org_entitlement(self):
        response = self._get(
            f'/api/integration/organizations/{self.org_a.id}/products/ISO_SMART/validate/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['allowed'])

    def test_medsupplier_contract_denies_missing_entitlement(self):
        response = self._get(
            f'/api/integration/organizations/{self.org_a.id}/products/MEDSUPPLIER/validate/'
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['allowed'])
        self.assertEqual(response.json()['reason'], 'product_not_enabled')

    def test_contract_denies_suspended_entitlement(self):
        response = self._get(
            f'/api/integration/organizations/{self.org_b.id}/products/ISO_SMART/validate/'
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['allowed'])
        self.assertEqual(response.json()['reason'], 'entitlement_inactive')

    def test_invalid_key_cannot_consume_other_tenant_contract(self):
        response = self._get(
            f'/api/integration/organizations/{self.org_b.id}/products/ISO_SMART/validate/',
            key='wrong-key',
        )

        self.assertEqual(response.status_code, 401)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SSOProductClaimsTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            code='SSO001',
            name='SSO Customer',
            email='sso@example.com',
            status='active',
        )
        self.plan = Plan.objects.create(
            code='SSO_PLAN',
            name='SSO Plan',
            price='100.00',
            currency='CRC',
        )
        self.subscription = Subscription.objects.create(
            plan=self.plan,
            status='active',
            amount='100.00',
        )
        self.organization.subscription = self.subscription
        self.organization.save(update_fields=['subscription'])

        self.user = User.objects.create_user(
            email='sso-user@example.com',
            password='SsoPass123!',
            first_name='SSO',
            last_name='User',
            organization=self.organization,
            role='org_admin',
            is_active=True,
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.organization,
            role='org_admin',
            is_primary=True,
            is_active=True,
        )

        self.iso_product, _ = ProductSystem.objects.update_or_create(
            code='ISO_SMART',
            defaults={
                'name': 'ISO Smart',
                'slug': 'iso-smart-sso',
                'status': 'active',
                'billing_enabled': True,
            },
        )
        self.med_product, _ = ProductSystem.objects.update_or_create(
            code='MEDSUPPLIER',
            defaults={
                'name': 'ISO Smart MedSupplier',
                'slug': 'iso-smart-medsupplier-sso',
                'status': 'active',
                'billing_enabled': True,
            },
        )
        OrganizationProductEntitlement.objects.create(
            organization=self.organization,
            product=self.iso_product,
            subscription=self.subscription,
            plan=self.plan,
            status='active',
            enabled=True,
            scopes=['qms'],
        )
        OrganizationProductEntitlement.objects.create(
            organization=self.organization,
            product=self.med_product,
            subscription=self.subscription,
            plan=self.plan,
            status='suspended',
            enabled=True,
            scopes=['supplier'],
        )

    def test_sso_login_includes_product_claims_in_response_and_access_token(self):
        response = self.client.post(
            '/api/integration/sso/login/',
            {
                'email': 'sso-user@example.com',
                'password': 'SsoPass123!',
                'organization_id': str(self.organization.id),
                'client_id': 'isosmart',
                'audience': ['isosmart'],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        tokens = response.json()['tokens']
        self.assertEqual(tokens['allowed_products'], ['ISO_SMART'])

        product_claims = {item['code']: item for item in tokens['product_entitlements']}
        self.assertTrue(product_claims['ISO_SMART']['access_allowed'])
        self.assertFalse(product_claims['MEDSUPPLIER']['access_allowed'])
        self.assertEqual(product_claims['MEDSUPPLIER']['access_denial_reason'], 'entitlement_inactive')

        access = AccessToken(tokens['access_token'])
        self.assertEqual(access['allowed_products'], ['ISO_SMART'])
        jwt_claims = {item['code']: item for item in access['product_entitlements']}
        self.assertIn('ISO_SMART', jwt_claims)
        self.assertIn('MEDSUPPLIER', jwt_claims)
        self.assertFalse(jwt_claims['MEDSUPPLIER']['access_allowed'])
