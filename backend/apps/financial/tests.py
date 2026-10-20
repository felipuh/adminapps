import uuid
import threading
import unittest
import base64
import json
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, connection, connections, transaction
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from apps.integration.services import create_integration_api_key
from apps.integration.models import IntegrationAPIKey
from apps.financial.authorization import (
    FinancialAuthorizationDenied,
    authenticate_registered_producer,
)
from apps.financial.capabilities import (
    CapabilityDenied, mint_capability, public_key_bytes, verify_capability,
)
from apps.financial.rbac import (
    grant_financial_permission,
    has_financial_permission,
    require_financial_permission,
    revoke_financial_permission,
)
from apps.financial.executor import FinancialExecutor
from apps.financial.issuer import issue_admission_capability
from apps.financial.services import (
    FinancialAdmissionDenied,
    admit_and_reserve,
    canonical_material_request_hash,
    create_producer_registration,
    transition_producer_registration,
)

from apps.financial.models import (
    AdmissionDecision,
    BudgetScope,
    FinancialAuditEvent,
    FinancialPolicy,
    FinancialPolicyVersion,
    FinancialReservation,
    ProducerRegistration,
    ProducerTenantGrant,
    ProducerTenantGrantLifecycleEvent,
    SettlementEvidence,
    VerifiedTariff,
)
from apps.organizations.models import Organization
from apps.products.models import ProductSystem
from apps.users.models import User


class FinancialSchemaTests(TestCase):
    def setUp(self):
        suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            code=f'FIN{suffix[:5]}', name='Financial test tenant', email=f'{suffix}@example.test', status='active'
        )
        self.product = ProductSystem.objects.create(
            code=f'FIN-{suffix}', name='Financial test product', slug=f'financial-{suffix}', status='active'
        )
        self.policy = FinancialPolicy.objects.create(organization=self.organization, policy_code='test-policy')
        self.policy_version = FinancialPolicyVersion.objects.create(
            policy=self.policy,
            version=1,
            currency='USD',
            period_timezone='UTC',
            period_boundary='calendar_month',
            rounding_rule='half_up',
        )
        self.tariff = VerifiedTariff.objects.create(
            provider='synthetic-provider', model_identifier='synthetic-model', version=1,
            currency='USD', input_unit_cost=Decimal('0.0000000001'), output_unit_cost=Decimal('0.0000000002'),
            unit_size=1, source_reference='synthetic test source', source_hash='a' * 64,
        )
        self.producer = ProducerRegistration.objects.create(
            producer_code='SYNTHETIC_TEST', environment='controlled_test',
            creation_evidence_hash='b' * 64, audit_owner='test-owner',
        )

    def _decision(self, invocation_id=None):
        return AdmissionDecision.objects.create(
            producer_registration=self.producer,
            organization=self.organization,
            product=self.product,
            invocation_id=invocation_id or uuid.uuid4(),
            material_request_hash='c' * 64,
            decision_state='reserved',
            correlation_id=uuid.uuid4(),
            policy_version=self.policy_version,
            tariff=self.tariff,
            currency='USD',
            reserved_amount=Decimal('1.0000000000'),
        )

    def test_admission_identity_is_unique(self):
        invocation_id = uuid.uuid4()
        self._decision(invocation_id)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._decision(invocation_id)

    def test_settlement_identity_is_unique(self):
        decision = self._decision()
        reservation = FinancialReservation.objects.create(
            admission_decision=decision, organization=self.organization, product=self.product,
            policy_version=self.policy_version, tariff=self.tariff, currency='USD',
            reserved_amount=Decimal('1.0000000000'), budget_period_start=timezone.now(),
            budget_period_end=timezone.now() + timedelta(days=30),
        )
        settlement_id = uuid.uuid4()
        settlement = dict(
            reservation=reservation, organization=self.organization, settlement_id=settlement_id,
            settlement_payload_hash='d' * 64, evidence_class='D', source_owner='synthetic-test',
            retention_classification='test', payload_hash='e' * 64, captured_at=timezone.now(),
        )
        SettlementEvidence.objects.create(evidence_id=uuid.uuid4(), **settlement)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SettlementEvidence.objects.create(evidence_id=uuid.uuid4(), **settlement)

    def test_budget_scope_shape_and_global_identity_are_enforced(self):
        starts = timezone.now()
        kwargs = dict(
            organization=self.organization, policy_version=self.policy_version,
            scope_type='tenant_global', period_start=starts, period_end=starts + timedelta(days=30),
            limit_amount=Decimal('100.0000000000'),
        )
        BudgetScope.objects.create(**kwargs)
        with self.assertRaises(IntegrityError), transaction.atomic():
            BudgetScope.objects.create(**kwargs)
        with self.assertRaises(IntegrityError), transaction.atomic():
            BudgetScope.objects.create(**{**kwargs, 'scope_type': 'tenant_product'})

    def test_financial_amounts_use_contract_precision_and_no_policy_is_active_by_default(self):
        self.assertEqual(VerifiedTariff._meta.get_field('input_unit_cost').max_digits, 20)
        self.assertEqual(VerifiedTariff._meta.get_field('input_unit_cost').decimal_places, 10)
        self.assertEqual(self.policy_version.state, 'draft')
        self.assertEqual(self.tariff.state, 'draft')
        self.assertEqual(self.producer.lifecycle_state, 'pending')


class FinancialCapabilityTests(TestCase):
    """Ed25519 checks are intentionally independent of SQLite/PostgreSQL ORM tests."""

    def setUp(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        self.private_key = Ed25519PrivateKey.generate()
        self.public_keys = {'synthetic-k1': self.private_key.public_key()}
        self.now = timezone.now().replace(microsecond=0)
        self.claims = dict(
            issuer_id='synthetic-financial-issuer', key_id='synthetic-k1',
            producer_registration_id=uuid.uuid4(), organization_id=uuid.uuid4(),
            product_id=uuid.uuid4(), environment='controlled_test', invocation_id=uuid.uuid4(),
            material_request_hash='a' * 64, grant_id=uuid.uuid4(), grant_version=1, now=self.now,
        )

    def _token(self, **changes):
        values = {**self.claims, **changes}
        return mint_capability(private_key=self.private_key, **values)

    def test_signed_capability_has_exact_bindings_and_public_key_only_verification(self):
        token = self._token()
        claims = verify_capability(
            token, public_keys=self.public_keys, issuer_id='synthetic-financial-issuer', now=self.now,
            expected={'organization_id': self.claims['organization_id'], 'product_id': self.claims['product_id']},
        )
        self.assertEqual(claims['jti'], str(self.claims['invocation_id']))
        self.assertEqual(len(public_key_bytes(self.private_key)), 32)

    def test_forgery_substitution_expiration_and_wrong_binding_are_denied(self):
        token = self._token()
        payload, signature = token.split('.')
        decoded = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
        decoded['organization_id'] = str(uuid.uuid4())
        altered_payload = base64.urlsafe_b64encode(
            json.dumps(decoded, sort_keys=True, separators=(',', ':')).encode()
        ).rstrip(b'=').decode()
        altered = altered_payload + '.' + signature
        checks = [
            (altered, self.public_keys, {}, 'CAPABILITY_SIGNATURE_INVALID'),
            (token, {}, {}, 'CAPABILITY_KEY_UNKNOWN'),
            (token, self.public_keys, {'organization_id': uuid.uuid4()}, 'CAPABILITY_BINDING_DENIED'),
        ]
        for candidate, keys, expected, code in checks:
            with self.subTest(code=code), self.assertRaises(CapabilityDenied) as denied:
                verify_capability(candidate, public_keys=keys, issuer_id='synthetic-financial-issuer', now=self.now, expected=expected)
            self.assertEqual(denied.exception.code, code)
        with self.assertRaises(CapabilityDenied) as expired:
            verify_capability(token, public_keys=self.public_keys, issuer_id='synthetic-financial-issuer', now=self.now + timedelta(seconds=61))
        self.assertEqual(expired.exception.code, 'CAPABILITY_EXPIRED')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ProducerRegistrationAuthorizationTests(TestCase):
    """S2 identity checks use synthetic keys only and make no admission decision."""

    def setUp(self):
        suffix = uuid.uuid4().hex[:8]
        self.operator = User.objects.create_user(
            email=f'operator-{suffix}@example.test', password='synthetic-password',
            first_name='S2', last_name='Operator', is_staff=True,
        )
        self.product = ProductSystem.objects.create(
            code=f'S2-{suffix}', name='S2 test product', slug=f's2-test-{suffix}', status='active'
        )

    def _credential(self, name='producer'):
        return create_integration_api_key(name=f'{name}-{uuid.uuid4().hex[:8]}', operator=self.operator)

    def _registration(self, *, credential=None, environment='controlled_test',
                      products=None, operations=None):
        credential, raw_key = credential or self._credential()
        registration = create_producer_registration(
            producer_code=f'SYNTHETIC_{uuid.uuid4().hex[:8]}',
            credential=credential,
            environment=environment,
            product_ids=products if products is not None else [self.product.id],
            operations=operations if operations is not None else ['status_read'],
            audit_owner='synthetic-s2-owner',
            creation_evidence_hash='a' * 64,
            actor_reference=f'user:{self.operator.pk}',
        )
        transition_producer_registration(
            registration=registration,
            lifecycle_state='active',
            actor_reference=f'user:{self.operator.pk}',
            evidence_hash='b' * 64,
            reason_code='synthetic_activation',
        )
        return registration, raw_key

    def _authenticate(self, raw_key, **kwargs):
        return authenticate_registered_producer(
            raw_api_key=raw_key,
            environment=kwargs.get('environment', 'controlled_test'),
            product_id=kwargs.get('product_id', self.product.id),
            operation=kwargs.get('operation', 'status_read'),
        )

    def test_active_registered_hashed_credential_with_exact_scopes_is_authenticated(self):
        registration, raw_key = self._registration()
        principal = self._authenticate(raw_key)

        self.assertEqual(principal.registration_id, str(registration.id))
        self.assertEqual(principal.environment, 'controlled_test')
        self.assertFalse(hasattr(principal, 'organization_id'))
        self.assertNotIn(raw_key, repr(principal))

    def test_invalid_unregistered_and_settings_fallback_credentials_are_denied(self):
        with self.assertRaises(FinancialAuthorizationDenied) as invalid:
            self._authenticate('not-a-financial-key')
        self.assertEqual(invalid.exception.code, 'unregistered_financial_credential')

        credential, raw_key = self._credential('unregistered')
        with self.assertRaises(FinancialAuthorizationDenied) as unregistered:
            self._authenticate(raw_key)
        self.assertEqual(unregistered.exception.code, 'unregistered_financial_credential')

        import hashlib
        with self.settings(INTEGRATION_API_KEYS={'settings-only': hashlib.sha256(b'settings-key').hexdigest()}):
            with self.assertRaises(FinancialAuthorizationDenied) as fallback:
                self._authenticate('settings-key')
        self.assertEqual(fallback.exception.code, 'unregistered_financial_credential')
        self.assertTrue(IntegrationAPIKey.objects.filter(pk=credential.pk).exists())

    def test_revoked_credential_disabled_and_revoked_registration_are_denied(self):
        registration, raw_key = self._registration()
        registration.credential.is_active = False
        registration.credential.save(update_fields=['is_active'])
        with self.assertRaises(FinancialAuthorizationDenied):
            self._authenticate(raw_key)

        registration, raw_key = self._registration()
        transition_producer_registration(
            registration=registration, lifecycle_state='suspended',
            actor_reference='synthetic-admin', evidence_hash='c' * 64,
            reason_code='synthetic_disable',
        )
        with self.assertRaises(FinancialAuthorizationDenied) as suspended:
            self._authenticate(raw_key)
        self.assertEqual(suspended.exception.code, 'producer_registration_inactive')

        registration, raw_key = self._registration()
        transition_producer_registration(
            registration=registration, lifecycle_state='revoked',
            actor_reference='synthetic-admin', evidence_hash='d' * 64,
            reason_code='synthetic_revoke',
        )
        with self.assertRaises(FinancialAuthorizationDenied):
            self._authenticate(raw_key)

    def test_environment_product_operation_and_binding_mismatches_are_denied(self):
        registration, raw_key = self._registration()
        other_product = ProductSystem.objects.create(
            code=f'OTHER-{uuid.uuid4().hex[:8]}', name='Other',
            slug=f'other-{uuid.uuid4().hex[:8]}', status='active',
        )
        for kwargs, code in (
            ({'environment': 'staging'}, 'financial_environment_denied'),
            ({'product_id': other_product.id}, 'financial_product_denied'),
            ({'operation': 'settle'}, 'financial_operation_denied'),
        ):
            with self.assertRaises(FinancialAuthorizationDenied) as denied:
                self._authenticate(raw_key, **kwargs)
            self.assertEqual(denied.exception.code, code)

        registration.credential_fingerprint = 'hmac-sha256-v1:incorrect'
        registration.save(update_fields=['credential_fingerprint'])
        with self.assertRaises(FinancialAuthorizationDenied) as mismatch:
            self._authenticate(raw_key)
        self.assertEqual(mismatch.exception.code, 'credential_binding_mismatch')

    def test_lifecycle_evidence_is_append_only_and_terminal_registration_cannot_reactivate(self):
        registration, _ = self._registration()
        transition_producer_registration(
            registration=registration, lifecycle_state='revoked',
            actor_reference='synthetic-admin', evidence_hash='e' * 64,
            reason_code='synthetic_revoke',
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            transition_producer_registration(
                registration=registration, lifecycle_state='active',
                actor_reference='synthetic-admin', evidence_hash='f' * 64,
                reason_code='invalid_reactivate',
            )
        self.assertEqual(registration.lifecycle_events.count(), 3)
        self.assertNotIn('raw_api_key', repr(list(registration.lifecycle_events.values())))


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FinancialRBACBoundaryTests(TestCase):
    def setUp(self):
        suffix = uuid.uuid4().hex[:8]
        self.financial_admin = User.objects.create_user(
            email=f'financial-admin-{suffix}@example.test', password='synthetic-password',
            first_name='Financial', last_name='Admin',
        )
        self.platform_admin = User.objects.create_superuser(
            email=f'platform-admin-{suffix}@example.test', password='synthetic-password',
            first_name='Platform', last_name='Admin',
        )
        self.org_admin = User.objects.create_user(
            email=f'org-admin-{suffix}@example.test', password='synthetic-password',
            first_name='Organization', last_name='Admin', role='org_admin',
        )
        self.subject = User.objects.create_user(
            email=f'subject-{suffix}@example.test', password='synthetic-password',
            first_name='Subject', last_name='User',
        )
        self._assign_direct(self.financial_admin, 'financial_admin')

    @staticmethod
    def _permission(code):
        return Permission.objects.get(content_type__app_label='financial', codename=code)

    def _assign_direct(self, user, code):
        user.user_permissions.add(self._permission(code))

    def test_general_and_organization_administration_do_not_imply_financial_authority(self):
        for user in (self.platform_admin, self.org_admin):
            self.assertFalse(has_financial_permission(user, 'financial_audit_read'))
            with self.assertRaises(PermissionDenied):
                require_financial_permission(actor=user, permission_code='financial_audit_read')

    def test_explicit_financial_assignment_and_revocation_are_auditable(self):
        grant_financial_permission(
            actor=self.financial_admin,
            subject=self.subject,
            permission_code='financial_audit_read',
        )
        self.assertTrue(has_financial_permission(self.subject, 'financial_audit_read'))
        revoke_financial_permission(
            actor=self.financial_admin,
            subject=self.subject,
            permission_code='financial_audit_read',
        )
        self.assertFalse(has_financial_permission(self.subject, 'financial_audit_read'))

        from apps.financial.models import FinancialPermissionAuditEvent
        self.assertEqual(
            list(FinancialPermissionAuditEvent.objects.values_list('action', flat=True)),
            ['granted', 'revoked'],
        )

    def test_only_explicit_financial_admin_can_assign_financial_permissions(self):
        with self.assertRaises(PermissionDenied):
            grant_financial_permission(
                actor=self.platform_admin,
                subject=self.subject,
                permission_code='financial_policy_admin',
            )
        self.assertFalse(has_financial_permission(self.subject, 'financial_policy_admin'))


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FinancialAdmissionServiceTests(TestCase):
    """S3 logic tests use controlled synthetic tariffs and never dispatch a provider."""

    def setUp(self):
        suffix = uuid.uuid4().hex[:8]
        self.operator = User.objects.create_user(
            email=f's3-{suffix}@example.test', password='synthetic-password',
            first_name='S3', last_name='Operator', is_staff=True,
        )
        self.organization = Organization.objects.create(
            code=f'S3{suffix[:5]}', name='S3 tenant', email=f'tenant-{suffix}@example.test', status='active',
        )
        self.product = ProductSystem.objects.create(
            code=f'S3-{suffix}', name='S3 product', slug=f's3-{suffix}', status='active', billing_enabled=False,
        )
        self.other_product = ProductSystem.objects.create(
            code=f'S3O-{suffix}', name='S3 other product', slug=f's3o-{suffix}', status='active', billing_enabled=False,
        )
        from apps.products.models import OrganizationProductEntitlement
        OrganizationProductEntitlement.objects.create(
            organization=self.organization, product=self.product, status='active', enabled=True,
        )
        OrganizationProductEntitlement.objects.create(
            organization=self.organization, product=self.other_product, status='active', enabled=True,
        )
        credential, self.raw_key = create_integration_api_key(name=f's3-producer-{suffix}', operator=self.operator)
        self.registration = create_producer_registration(
            producer_code=f'SYNTHETIC_S3_{suffix}', credential=credential, environment='controlled_test',
            product_ids=[self.product.id, self.other_product.id], operations=['admit_reserve'],
            audit_owner='s3-test-owner', creation_evidence_hash='a' * 64,
            actor_reference=f'user:{self.operator.pk}',
        )
        transition_producer_registration(
            registration=self.registration, lifecycle_state='active', actor_reference=f'user:{self.operator.pk}',
            evidence_hash='b' * 64, reason_code='synthetic_activation',
        )
        now = timezone.now()
        policy = FinancialPolicy.objects.create(organization=self.organization, policy_code=f's3-{suffix}')
        self.policy = FinancialPolicyVersion.objects.create(
            policy=policy, version=1, state='approved', currency='USD', period_timezone='UTC',
            period_boundary='calendar_month', amount_precision=2, rounding_rule='half_up',
            allowed_provider='synthetic', allowed_model='synthetic-model',
            max_input_tokens=100, max_output_tokens=100, effective_from=now - timedelta(minutes=1),
            approved_evidence_hash='c' * 64,
        )
        self.tariff = VerifiedTariff.objects.create(
            provider='synthetic', model_identifier='synthetic-model', version=1, state='verified', currency='USD',
            input_unit_cost=Decimal('1.0000000000'), output_unit_cost=Decimal('1.0000000000'), unit_size=1,
            source_reference='synthetic controlled tariff', source_hash='d' * 64,
            effective_from=now - timedelta(minutes=1),
        )
        self.global_scope = BudgetScope.objects.create(
            organization=self.organization, policy_version=self.policy, scope_type='tenant_global',
            period_start=now - timedelta(minutes=1), period_end=now + timedelta(days=1),
            limit_amount=Decimal('100.0000000000'), request_limit=2,
        )
        self.product_scope = BudgetScope.objects.create(
            organization=self.organization, product=self.product, policy_version=self.policy, scope_type='tenant_product',
            period_start=now - timedelta(minutes=1), period_end=now + timedelta(days=1),
            limit_amount=Decimal('50.0000000000'), request_limit=1,
        )

    def _admit(self, *, product=None, invocation_id=None, input_tokens=10, output_tokens=10, request_class='synthetic'):
        product = product or self.product
        return admit_and_reserve(
            raw_api_key=self.raw_key, environment='controlled_test', organization_id=self.organization.id,
            product_id=product.id, invocation_id=invocation_id or uuid.uuid4(), correlation_id=uuid.uuid4(),
            tenant_assertion={'adminapps_tenant_id': str(self.organization.id), 'source': 'controlled-s3-test'},
            provider='synthetic', model_identifier='synthetic-model', max_input_tokens=input_tokens,
            max_output_tokens=output_tokens, request_class=request_class,
        )

    def test_valid_admission_reserves_all_applicable_scopes_and_creates_immutable_evidence(self):
        result = self._admit()
        self.assertEqual(result.decision_state, 'reserved')
        self.assertEqual(result.reserved_amount, Decimal('20.00'))
        self.global_scope.refresh_from_db()
        self.product_scope.refresh_from_db()
        self.assertEqual(self.global_scope.reserved_exposure, Decimal('20.0000000000'))
        self.assertEqual(self.product_scope.reserved_exposure, Decimal('20.0000000000'))
        self.assertEqual(self.global_scope.reserved_request_count, 1)
        self.assertEqual(FinancialAuditEvent.objects.filter(event_type='admission_reserved').count(), 1)

    def test_identical_and_conflicting_replay_have_one_financial_effect(self):
        invocation_id = uuid.uuid4()
        first = self._admit(invocation_id=invocation_id)
        replay = self._admit(invocation_id=invocation_id)
        self.assertTrue(replay.replayed)
        self.assertEqual(replay.decision_id, first.decision_id)
        self.global_scope.refresh_from_db()
        self.assertEqual(self.global_scope.reserved_exposure, Decimal('20.0000000000'))
        with self.assertRaises(FinancialAdmissionDenied) as conflict:
            self._admit(invocation_id=invocation_id, output_tokens=11)
        self.assertEqual(conflict.exception.code, 'IDEMPOTENCY_CONFLICT')
        self.assertEqual(AdmissionDecision.objects.count(), 1)

    def test_entitlement_budget_quota_and_input_bound_fail_closed(self):
        self.product_scope.limit_amount = Decimal('10.0000000000')
        self.product_scope.save(update_fields=['limit_amount'])
        exhausted = self._admit()
        self.assertEqual(exhausted.decision_state, 'denied')
        self.assertEqual(exhausted.denial_code, 'BUDGET_EXHAUSTED')
        self.assertEqual(FinancialReservation.objects.count(), 0)
        bound = self._admit(input_tokens=101)
        self.assertEqual(bound.decision_state, 'denied')
        self.assertEqual(bound.denial_code, 'INPUT_BOUND_EXCEEDED')
        self.product_scope.limit_amount = Decimal('100.0000000000')
        self.product_scope.save(update_fields=['limit_amount'])
        first = self._admit()
        self.assertEqual(first.decision_state, 'reserved')
        quota = self._admit()
        self.assertEqual(quota.denial_code, 'REQUEST_QUOTA_EXHAUSTED')


@unittest.skipUnless(connection.vendor == 'postgresql', 'requires PostgreSQL row locks and isolation')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FinancialAdmissionPostgresConcurrencyTests(TransactionTestCase):
    """Actual concurrent S3 calls using independent PostgreSQL connections."""

    reset_sequences = True

    def setUp(self):
        FinancialAdmissionServiceTests.setUp(self)
        now = timezone.now()
        # Create the race budget with its final terms; the PostgreSQL S3 guard
        # intentionally rejects direct counter/budget mutation outside admission.
        self.global_scope.delete()
        self.product_scope.delete()
        self.global_scope = BudgetScope.objects.create(
            organization=self.organization, policy_version=self.policy, scope_type='tenant_global',
            period_start=now - timedelta(minutes=1), period_end=now + timedelta(days=1),
            limit_amount=Decimal('30.0000000000'), request_limit=2,
        )
        self.product_scope = BudgetScope.objects.create(
            organization=self.organization, product=self.product, policy_version=self.policy,
            scope_type='tenant_product', period_start=now - timedelta(minutes=1),
            period_end=now + timedelta(days=1), limit_amount=Decimal('100.0000000000'), request_limit=2,
        )
        self.other_scope = BudgetScope.objects.create(
            organization=self.organization, product=self.other_product, policy_version=self.policy,
            scope_type='tenant_product', period_start=now - timedelta(minutes=1),
            period_end=now + timedelta(days=1), limit_amount=Decimal('100.0000000000'), request_limit=2,
        )

    def _admit(self, **kwargs):
        return FinancialAdmissionServiceTests._admit(self, **kwargs)

    def test_cross_product_global_budget_and_duplicate_replay_are_atomic(self):
        barrier = threading.Barrier(2)
        outcomes = []
        backend_pids = []
        lock = threading.Lock()

        def worker(product, invocation_id):
            connections.close_all()
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pid = cursor.fetchone()[0]
                barrier.wait(timeout=10)
                result = self._admit(product=product, invocation_id=invocation_id)
                item = ('result', result)
            except Exception as exc:  # Keep assertion context in the parent thread.
                item = ('error', exc)
                pid = None
            finally:
                connections.close_all()
            with lock:
                outcomes.append(item)
                if pid is not None:
                    backend_pids.append(pid)

        threads = [
            threading.Thread(target=worker, args=(self.product, uuid.uuid4())),
            threading.Thread(target=worker, args=(self.other_product, uuid.uuid4())),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertFalse([item for item in outcomes if item[0] == 'error'], outcomes)
        self.assertEqual(len(set(backend_pids)), 2)
        print(f'S3 PostgreSQL concurrency evidence backend_pids={sorted(set(backend_pids))}')
        decisions = [item[1] for item in outcomes]
        self.assertEqual(sorted(result.decision_state for result in decisions), ['denied', 'reserved'])
        self.global_scope.refresh_from_db()
        self.assertEqual(self.global_scope.reserved_exposure, Decimal('20.0000000000'))
        self.assertEqual(FinancialReservation.objects.filter(state='reserved').count(), 1)

        reserved_result = next(result for result in decisions if result.decision_state == 'reserved')
        original = AdmissionDecision.objects.get(pk=reserved_result.decision_id)
        invocation_id = original.invocation_id
        barrier = threading.Barrier(2)
        outcomes.clear()
        backend_pids.clear()
        threads = [
            threading.Thread(target=worker, args=(original.product, invocation_id)),
            threading.Thread(target=worker, args=(original.product, invocation_id)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertFalse([item for item in outcomes if item[0] == 'error'], outcomes)
        duplicate_results = [item[1] for item in outcomes]
        self.assertEqual(len({item.decision_id for item in duplicate_results}), 1)
        self.assertTrue(all(item.replayed for item in duplicate_results))
        self.assertEqual(FinancialReservation.objects.filter(state='reserved').count(), 1)


@unittest.skipUnless(connection.vendor == 'postgresql', 'requires PostgreSQL roles, RLS, and functions')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FinancialAdmissionPostgresRuntimeRoleTests(TransactionTestCase):
    """Exercise the S3 function from a non-administrator runtime session."""

    def setUp(self):
        FinancialAdmissionServiceTests.setUp(self)
        self.grant = ProducerTenantGrant.objects.create(
            producer_registration=self.registration, organization=self.organization,
            product=self.product, operation='admit_reserve', environment='controlled_test',
            state='active', effective_from=timezone.now() - timedelta(minutes=1),
        )
        ProducerTenantGrantLifecycleEvent.objects.create(
            grant=self.grant, state='active', actor_reference='synthetic-security-iam',
            evidence_hash='9' * 64, reason_code='synthetic_grant',
        )

    def _admit(self, **kwargs):
        return FinancialAdmissionServiceTests._admit(self, **kwargs)

    def _runtime_evidence_connection(self):
        """Return a separate NOINHERIT login which may only SET ROLE runtime.

        The production runtime role intentionally remains NOLOGIN.  This
        disposable verifier principal prevents an administrator session from
        being misreported as evidence of the runtime role's effective rights.
        """
        alias = f'financial_runtime_evidence_{uuid.uuid4().hex}'
        settings = connection.settings_dict.copy()
        settings['USER'] = 'adminapps_financial_runtime_evidence'
        connections.databases[alias] = settings
        runtime_connection = connections[alias]

        def close_runtime_connection():
            runtime_connection.close()
            connections.databases.pop(alias, None)

        self.addCleanup(close_runtime_connection)
        return runtime_connection

    def _second_eligible_tenant(self):
        """Create independent synthetic tenant state for a boundary test."""
        suffix = uuid.uuid4().hex[:8]
        organization = Organization.objects.create(
            code=f'S3B{suffix[:4]}', name='S3 tenant B',
            email=f'tenant-b-{suffix}@example.test', status='active',
        )
        from apps.products.models import OrganizationProductEntitlement
        OrganizationProductEntitlement.objects.create(
            organization=organization, product=self.product, status='active', enabled=True,
        )
        now = timezone.now()
        policy = FinancialPolicy.objects.create(organization=organization, policy_code=f's3-b-{suffix}')
        policy_version = FinancialPolicyVersion.objects.create(
            policy=policy, version=1, state='approved', currency='USD', period_timezone='UTC',
            period_boundary='calendar_month', amount_precision=2, rounding_rule='half_up',
            allowed_provider='synthetic', allowed_model='synthetic-model',
            max_input_tokens=100, max_output_tokens=100, effective_from=now - timedelta(minutes=1),
            approved_evidence_hash='c' * 64,
        )
        BudgetScope.objects.create(
            organization=organization, policy_version=policy_version, scope_type='tenant_global',
            period_start=now - timedelta(minutes=1), period_end=now + timedelta(days=1),
            limit_amount=Decimal('100.0000000000'), request_limit=2,
        )
        BudgetScope.objects.create(
            organization=organization, product=self.product, policy_version=policy_version,
            scope_type='tenant_product', period_start=now - timedelta(minutes=1),
            period_end=now + timedelta(days=1), limit_amount=Decimal('100.0000000000'), request_limit=2,
        )
        return organization

    def test_runtime_role_can_only_use_the_reviewed_admission_function(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT rolsuper, rolbypassrls, rolcanlogin, rolinherit
                   FROM pg_roles WHERE rolname = 'adminapps_financial_runtime'"""
            )
            self.assertEqual(cursor.fetchone(), (False, False, False, False))
            cursor.execute(
                """SELECT rolsuper, rolbypassrls, rolcanlogin, rolinherit
                   FROM pg_roles WHERE rolname = 'adminapps_financial_admission'"""
            )
            self.assertEqual(cursor.fetchone(), (False, False, False, False))
            cursor.execute(
                """SELECT count(*) FROM pg_class c JOIN pg_roles r ON r.oid = c.relowner
                   WHERE c.relnamespace = 'public'::regnamespace
                     AND c.relname LIKE 'financial_%' AND r.rolname = 'adminapps_financial_runtime'"""
            )
            self.assertEqual(cursor.fetchone()[0], 0)
            cursor.execute(
                """SELECT has_function_privilege('adminapps_financial_runtime',
                          'public.financial_admit_reserve(uuid,uuid,uuid,uuid,uuid,text,text,text,text,bigint,bigint,uuid,uuid)', 'EXECUTE'),
                         has_function_privilege('adminapps_financial_runtime',
                          'public.financial_admit_reserve_capability(uuid,text,text,smallint,uuid,integer,uuid,uuid,uuid,uuid,text,text,text,uuid,text,text,bigint,bigint)', 'EXECUTE'),
                         has_function_privilege('adminapps_financial_executor',
                          'public.financial_admit_reserve_capability(uuid,text,text,smallint,uuid,integer,uuid,uuid,uuid,uuid,text,text,text,uuid,text,text,bigint,bigint)', 'EXECUTE')"""
            )
            self.assertEqual(cursor.fetchone(), (False, False, True))
            cursor.execute(
                """SELECT count(*)
                   FROM pg_auth_members membership
                   JOIN pg_roles role ON role.oid IN (membership.roleid, membership.member)
                  WHERE role.rolname = 'adminapps_financial_admission'"""
            )
            self.assertEqual(cursor.fetchone()[0], 0)

        runtime_connection = self._runtime_evidence_connection()
        with runtime_connection.cursor() as cursor:
            cursor.execute('SELECT current_user, session_user')
            self.assertEqual(
                cursor.fetchone(),
                ('adminapps_financial_runtime_evidence', 'adminapps_financial_runtime_evidence'),
            )
            cursor.execute('SET ROLE adminapps_financial_runtime')
            cursor.execute('SELECT current_user, session_user')
            self.assertEqual(
                cursor.fetchone(),
                ('adminapps_financial_runtime', 'adminapps_financial_runtime_evidence'),
            )
            with self.assertRaises(Exception):
                cursor.execute('UPDATE financial_budget_scopes SET reserved_exposure = 99')
            with self.assertRaises(Exception):
                cursor.execute(
                    """INSERT INTO financial_audit_events
                       (id, organization_id, event_type, actor_reference, entity_type, entity_id, payload_hash, metadata, created_at)
                       VALUES (%s, %s, 'forged', 'runtime', 'forged', %s, %s, '{}', now())""",
                    [uuid.uuid4(), self.organization.id, uuid.uuid4(), 'f' * 64],
                )
            with self.assertRaises(Exception):
                cursor.execute('SELECT count(*) FROM financial_admission_decisions')

            with self.assertRaises(Exception):
                cursor.execute(
                    """SELECT * FROM public.financial_admit_reserve(
                         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                       )""",
                    [
                        self.registration.id, self.organization.id, self.product.id,
                        uuid.uuid4(), uuid.uuid4(), 'e' * 64, 'controlled_test',
                        'synthetic', 'synthetic-model', 10, 10, uuid.uuid4(), uuid.uuid4(),
                    ],
                )

            unpermitted_product = ProductSystem.objects.create(
                code=f'FORGED-{uuid.uuid4().hex[:8]}', name='Forged product',
                slug=f'forged-{uuid.uuid4().hex[:8]}', status='active',
            )
            with self.assertRaises(Exception):
                cursor.execute(
                    """SELECT * FROM public.financial_admit_reserve(
                         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                       )""",
                    [
                        self.registration.id, self.organization.id, unpermitted_product.id,
                        uuid.uuid4(), uuid.uuid4(), 'd' * 64, 'controlled_test',
                        'synthetic', 'synthetic-model', 10, 10, uuid.uuid4(), uuid.uuid4(),
                    ],
                )

        with self.assertRaises(FinancialAdmissionDenied) as missing_assertion:
            admit_and_reserve(
                raw_api_key=self.raw_key, environment='controlled_test', organization_id=self.organization.id,
                product_id=self.product.id, invocation_id=uuid.uuid4(), correlation_id=uuid.uuid4(),
                tenant_assertion={}, provider='synthetic', model_identifier='synthetic-model',
                max_input_tokens=10, max_output_tokens=10, request_class='synthetic',
            )
        self.assertEqual(missing_assertion.exception.code, 'TENANT_ASSERTION_UNTRUSTED')

        self.global_scope.refresh_from_db()
        self.assertEqual(self.global_scope.reserved_exposure, Decimal('0E-10'))
        self.assertEqual(FinancialReservation.objects.count(), 0)

    def test_runtime_direct_call_cannot_forge_an_eligible_tenant_identity(self):
        """The former cross-tenant exploit must fail before any side effect."""
        tenant_b = self._second_eligible_tenant()
        runtime_connection = self._runtime_evidence_connection()
        with runtime_connection.cursor() as cursor:
            cursor.execute('SET ROLE adminapps_financial_runtime')
            with self.assertRaises(Exception):
                cursor.execute(
                    """SELECT * FROM public.financial_admit_reserve(
                         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                       )""",
                    [
                        self.registration.id, tenant_b.id, self.product.id,
                        uuid.uuid4(), uuid.uuid4(), 'a' * 64, 'controlled_test',
                        'synthetic', 'synthetic-model', 10, 10, uuid.uuid4(), uuid.uuid4(),
                    ],
                )
        self.assertFalse(FinancialReservation.objects.filter(organization=tenant_b).exists())
        self.assertFalse(AdmissionDecision.objects.filter(organization=tenant_b).exists())

    def test_executor_verifies_signed_capability_and_uses_executor_identity(self):
        """A real executor-login connection can perform only a granted admission."""
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        private_key = Ed25519PrivateKey.generate()
        material_hash = canonical_material_request_hash(
            tenant_assertion={'adminapps_tenant_id': str(self.organization.id), 'source': 's3'},
            product_id=self.product.id, provider='synthetic', model_identifier='synthetic-model',
            max_input_tokens=10, max_output_tokens=10, request_class='synthetic',
        )
        capability = issue_admission_capability(
            raw_api_key=self.raw_key, environment='controlled_test', organization_id=self.organization.id,
            product_id=self.product.id, invocation_id=uuid.uuid4(), material_request_hash=material_hash,
            private_key=private_key, issuer_id='synthetic-isolated-issuer', key_id='s3-k1',
        )
        executor_database = connection.settings_dict.copy()
        executor_database['USER'] = 'adminapps_financial_executor'
        executor = FinancialExecutor(
            database=executor_database,
            public_keys={'s3-k1': private_key.public_key()}, issuer_id='synthetic-isolated-issuer',
        )
        result = executor.admit_reserve(
            capability=capability, correlation_id=uuid.uuid4(), provider='synthetic',
            model_identifier='synthetic-model', max_input_tokens=10, max_output_tokens=10,
            tenant_assertion={'adminapps_tenant_id': str(self.organization.id), 'source': 's3'},
            request_class='synthetic',
        )
        self.assertEqual(result['decision_state'], 'reserved')
        self.assertTrue(FinancialReservation.objects.filter(id=result['reservation_id']).exists())
        with self.assertRaises(PermissionError):
            executor.admit_reserve(
                capability=capability, correlation_id=uuid.uuid4(), provider='synthetic',
                model_identifier='different-model', max_input_tokens=10, max_output_tokens=10,
                tenant_assertion={'adminapps_tenant_id': str(self.organization.id), 'source': 's3'},
                request_class='synthetic',
            )
