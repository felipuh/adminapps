"""Controlled S2 lifecycle and non-operational S3 admission operations."""

import hashlib
import json
import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP

from django.core.exceptions import ValidationError
from django.db import OperationalError, connection, transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.integration.models import IntegrationAPIKey
from apps.organizations.models import Organization
from apps.products.models import OrganizationProductEntitlement, ProductSystem

from .authorization import FinancialAuthorizationDenied, authenticate_registered_producer, validate_s2_registration
from .models import (
    AdmissionDecision, BudgetScope, FinancialAuditEvent, FinancialPolicyVersion,
    FinancialReservation, ProducerRegistration, ProducerRegistrationLifecycleEvent,
    VerifiedTariff,
)


def create_producer_registration(*, producer_code, credential, environment,
                                 product_ids, operations, audit_owner,
                                 creation_evidence_hash, actor_reference):
    """Create immutable registration evidence and its initial pending lifecycle event."""
    validate_s2_registration(
        credential=credential,
        environment=environment,
        product_ids=product_ids,
        operations=operations,
    )
    with transaction.atomic():
        registration = ProducerRegistration.objects.create(
            producer_code=producer_code,
            credential=credential,
            credential_fingerprint=credential.fingerprint,
            environment=environment,
            permitted_product_ids=[str(value) for value in product_ids],
            permitted_operations=sorted(set(operations)),
            lifecycle_state='pending',
            creation_evidence_hash=creation_evidence_hash,
            audit_owner=audit_owner,
        )
        ProducerRegistrationLifecycleEvent.objects.create(
            registration=registration,
            lifecycle_state='pending',
            actor_reference=actor_reference,
            evidence_hash=creation_evidence_hash,
            reason_code='registration_created',
        )
    return registration


def transition_producer_registration(*, registration, lifecycle_state,
                                     actor_reference, evidence_hash, reason_code):
    """Append a lifecycle transition.  Revoked/retired registrations never reactivate."""
    if lifecycle_state not in dict(ProducerRegistration.LIFECYCLE_STATES):
        raise ValidationError('Unknown registration lifecycle state.')
    current = registration.lifecycle_events.order_by('-created_at', '-id').first()
    if current is None:
        raise ValidationError('Registration has no lifecycle evidence.')
    if current.lifecycle_state in {'revoked', 'retired'} and lifecycle_state != current.lifecycle_state:
        raise ValidationError('Terminal producer registrations cannot be reactivated.')
    if lifecycle_state == current.lifecycle_state:
        raise ValidationError('Lifecycle transition must change state.')
    return ProducerRegistrationLifecycleEvent.objects.create(
        registration=registration,
        lifecycle_state=lifecycle_state,
        actor_reference=actor_reference,
        evidence_hash=evidence_hash,
        reason_code=reason_code,
    )


# S3 deliberately has no view or URL.  This service is an internal controlled
# boundary which can only produce synthetic reservations.
class FinancialAdmissionDenied(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class AdmissionResult:
    decision_id: str
    decision_state: str
    denial_code: str
    reservation_id: str | None
    currency: str
    reserved_amount: Decimal | None
    replayed: bool


_ROUNDING = {'half_up': ROUND_HALF_UP, 'half_even': ROUND_HALF_EVEN, 'down': ROUND_DOWN, 'up': ROUND_UP}
_SERIALIZATION_RETRIES = 3


def canonical_material_request_hash(*, tenant_assertion, product_id, provider,
                                    model_identifier, max_input_tokens,
                                    max_output_tokens, request_class,
                                    schema_version=1, evidence_ids=None):
    """Return the server-computed hash of all financially material fields."""
    material = {
        'schema_version': schema_version,
        'tenant_assertion': tenant_assertion,
        'product_id': str(product_id),
        'provider': provider,
        'model_identifier': model_identifier,
        'max_input_tokens': max_input_tokens,
        'max_output_tokens': max_output_tokens,
        'request_class': request_class,
        'evidence_ids': sorted(str(value) for value in (evidence_ids or [])),
    }
    try:
        payload = json.dumps(material, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise FinancialAdmissionDenied('MATERIAL_REQUEST_INVALID') from exc
    return hashlib.sha256(payload).hexdigest()


def _current_lifecycle_state(registration):
    event = registration.lifecycle_events.order_by('-created_at', '-id').only('lifecycle_state').first()
    return event.lifecycle_state if event else None


def _result(decision, replayed=False):
    reservation = getattr(decision, 'reservation', None) if decision.decision_state == 'reserved' else None
    return AdmissionResult(
        decision_id=str(decision.id), decision_state=decision.decision_state,
        denial_code=decision.denial_code, reservation_id=str(reservation.id) if reservation else None,
        currency=decision.currency, reserved_amount=decision.reserved_amount, replayed=replayed,
    )


def _replay_or_conflict(*, registration, organization, product, invocation_id, material_hash):
    existing = AdmissionDecision.objects.select_related('reservation').filter(
        producer_registration=registration, organization=organization, product=product,
        invocation_id=invocation_id,
    ).first()
    if not existing:
        return None
    if existing.material_request_hash != material_hash:
        raise FinancialAdmissionDenied('IDEMPOTENCY_CONFLICT')
    return _result(existing, replayed=True)


def _persist_denial(*, registration, organization, product, invocation_id,
                    material_hash, correlation_id, code):
    decision = AdmissionDecision.objects.create(
        producer_registration=registration, organization=organization, product=product,
        invocation_id=invocation_id, material_request_hash=material_hash,
        decision_state='denied', correlation_id=correlation_id, denial_code=code,
    )
    FinancialAuditEvent.objects.create(
        organization=organization, event_type='admission_denied',
        actor_reference=f'producer_registration:{registration.id}', correlation_id=correlation_id,
        entity_type='admission_decision', entity_id=decision.id, payload_hash=material_hash,
        metadata={'denial_code': code},
    )
    return _result(decision)


def _effective_one(queryset, code):
    rows = list(queryset[:2])
    if len(rows) != 1:
        raise FinancialAdmissionDenied(code)
    return rows[0]


def _reserve_amount(*, tariff, policy, max_input_tokens, max_output_tokens):
    if not isinstance(max_input_tokens, int) or isinstance(max_input_tokens, bool) or max_input_tokens < 0:
        raise FinancialAdmissionDenied('INPUT_BOUND_INVALID')
    if not isinstance(max_output_tokens, int) or isinstance(max_output_tokens, bool) or max_output_tokens < 0:
        raise FinancialAdmissionDenied('OUTPUT_BOUND_INVALID')
    if policy.max_input_tokens is None:
        raise FinancialAdmissionDenied('INPUT_BOUND_UNVERIFIED')
    if policy.max_output_tokens is None:
        raise FinancialAdmissionDenied('OUTPUT_BOUND_UNVERIFIED')
    if max_input_tokens > policy.max_input_tokens:
        raise FinancialAdmissionDenied('INPUT_BOUND_EXCEEDED')
    if max_output_tokens > policy.max_output_tokens:
        raise FinancialAdmissionDenied('OUTPUT_BOUND_EXCEEDED')
    try:
        amount = (
            Decimal(max_input_tokens) * tariff.input_unit_cost / Decimal(tariff.unit_size)
            + Decimal(max_output_tokens) * tariff.output_unit_cost / Decimal(tariff.unit_size)
        )
        return amount.quantize(Decimal(1).scaleb(-int(policy.amount_precision)), rounding=_ROUNDING[policy.rounding_rule])
    except (InvalidOperation, KeyError, ValueError) as exc:
        raise FinancialAdmissionDenied('POLICY_PRECISION_INVALID') from exc


def _applicable_scopes(*, organization, product, policy, now):
    base = BudgetScope.objects.filter(
        organization=organization, policy_version=policy,
        period_start__lte=now, period_end__gt=now,
    )
    global_scope = _effective_one(base.filter(scope_type='tenant_global', product__isnull=True), 'GLOBAL_BUDGET_MISSING')
    scopes = [global_scope, *base.filter(scope_type='tenant_product', product=product)]
    # V1.1 §5.1: global scope first, then product scope, UUID ties.
    scopes.sort(key=lambda scope: (0 if scope.scope_type == 'tenant_global' else 1, str(scope.id)))
    return [BudgetScope.objects.select_for_update().get(pk=scope.pk) for scope in scopes]


def _serialization_failure(exc):
    cause = getattr(exc, '__cause__', None)
    return (
        getattr(exc, 'pgcode', None) == '40001'
        or getattr(cause, 'pgcode', None) == '40001'
        or getattr(exc, 'sqlstate', None) == '40001'
        or getattr(cause, 'sqlstate', None) == '40001'
    )


def admit_and_reserve(*, raw_api_key, environment, organization_id, product_id,
                      invocation_id, correlation_id, tenant_assertion, provider,
                      model_identifier, max_input_tokens, max_output_tokens,
                      request_class, schema_version=1, evidence_ids=None):
    """Atomically admit a synthetic request; it never dispatches a provider call."""
    try:
        principal = authenticate_registered_producer(
            raw_api_key=raw_api_key, environment=environment, product_id=product_id,
            operation='admit_reserve',
        )
    except FinancialAuthorizationDenied as exc:
        raise FinancialAdmissionDenied(exc.code) from exc
    if not isinstance(tenant_assertion, dict) or str(tenant_assertion.get('adminapps_tenant_id')) != str(organization_id):
        raise FinancialAdmissionDenied('TENANT_ASSERTION_UNTRUSTED')
    material_hash = canonical_material_request_hash(
        tenant_assertion=tenant_assertion, product_id=product_id, provider=provider,
        model_identifier=model_identifier, max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens, request_class=request_class,
        schema_version=schema_version, evidence_ids=evidence_ids,
    )
    for attempt in range(_SERIALIZATION_RETRIES):
        try:
            return _admit_once(
                registration_id=principal.registration_id, organization_id=organization_id,
                product_id=product_id, invocation_id=invocation_id, correlation_id=correlation_id,
                material_hash=material_hash, provider=provider, model_identifier=model_identifier,
                max_input_tokens=max_input_tokens, max_output_tokens=max_output_tokens,
                environment=environment,
            )
        except OperationalError as exc:
            if not _serialization_failure(exc) or attempt == _SERIALIZATION_RETRIES - 1:
                raise FinancialAdmissionDenied('ADMISSION_UNAVAILABLE') from exc
    raise FinancialAdmissionDenied('ADMISSION_UNAVAILABLE')


def _admit_once(*, registration_id, organization_id, product_id, invocation_id,
                correlation_id, material_hash, provider, model_identifier,
                max_input_tokens, max_output_tokens, environment):
    with transaction.atomic():
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                # The restricted runtime role can execute only the reviewed
                # SECURITY DEFINER admission boundary.  It has no direct
                # financial write grant and cannot activate that boundary with
                # a caller-controlled GUC/session variable.
                cursor.execute(
                    '''SELECT decision_id, decision_state, denial_code, reservation_id,
                              currency, reserved_amount, replayed
                       FROM public.financial_admit_reserve(
                         %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                       )''',
                    [
                        str(registration_id), str(organization_id), str(product_id),
                        str(invocation_id), str(correlation_id), material_hash,
                        # authenticate_registered_producer already verifies this
                        # exact registration/key/scope before this transaction.
                        environment, provider, model_identifier,
                        max_input_tokens, max_output_tokens, str(uuid.uuid4()), str(uuid.uuid4()),
                    ],
                )
                row = cursor.fetchone()
            if not row:
                raise FinancialAdmissionDenied('ADMISSION_UNAVAILABLE')
            decision_id, state, denial_code, reservation_id, currency, amount, replayed = row
            if state == 'conflict':
                raise FinancialAdmissionDenied('IDEMPOTENCY_CONFLICT')
            return AdmissionResult(
                decision_id=str(decision_id), decision_state=state,
                denial_code=denial_code or '', reservation_id=str(reservation_id) if reservation_id else None,
                currency=currency or '', reserved_amount=amount, replayed=replayed,
            )
        registration = ProducerRegistration.objects.select_for_update(of=('self',)).select_related('credential').get(pk=registration_id)
        credential = IntegrationAPIKey.objects.select_for_update().get(pk=registration.credential_id) if registration.credential_id else None
        organization = Organization.objects.select_for_update().get(pk=organization_id)
        product = ProductSystem.objects.select_for_update().get(pk=product_id)
        replay = _replay_or_conflict(
            registration=registration, organization=organization, product=product,
            invocation_id=invocation_id, material_hash=material_hash,
        )
        if replay:
            return replay
        if (
            _current_lifecycle_state(registration) != 'active'
            or not credential
            or credential.status != 'active'
            or not credential.is_active
            or credential.credential_format != 'hashed_v1'
            or registration.credential_fingerprint != credential.fingerprint
        ):
            return _persist_denial(registration=registration, organization=organization, product=product, invocation_id=invocation_id, material_hash=material_hash, correlation_id=correlation_id, code='PRODUCER_INACTIVE')
        if str(product.id) not in {str(value) for value in registration.permitted_product_ids} or 'admit_reserve' not in registration.permitted_operations:
            return _persist_denial(registration=registration, organization=organization, product=product, invocation_id=invocation_id, material_hash=material_hash, correlation_id=correlation_id, code='PRODUCER_SCOPE_DENIED')
        entitlement = OrganizationProductEntitlement.objects.select_for_update(of=('self',)).select_related('subscription', 'organization', 'product').filter(organization=organization, product=product).first()
        if not organization.is_active or not product.is_available or not entitlement or not entitlement.access_allowed:
            return _persist_denial(registration=registration, organization=organization, product=product, invocation_id=invocation_id, material_hash=material_hash, correlation_id=correlation_id, code='ENTITLEMENT_DENIED')
        now = timezone.now()
        try:
            policy = _effective_one(
                FinancialPolicyVersion.objects.select_for_update().filter(
                    policy__organization=organization, state='approved', effective_from__lte=now,
                ).filter(Q(effective_until__isnull=True) | Q(effective_until__gt=now)),
                'FINANCIAL_POLICY_MISSING',
            )
            if policy.allowed_provider != provider or policy.allowed_model != model_identifier:
                raise FinancialAdmissionDenied('MODEL_NOT_ALLOWED')
            tariff = _effective_one(
                VerifiedTariff.objects.select_for_update().filter(
                    provider=provider, model_identifier=model_identifier, state='verified',
                    effective_from__isnull=False, effective_from__lte=now,
                ).filter(Q(effective_until__isnull=True) | Q(effective_until__gt=now)),
                'TARIFF_UNAVAILABLE',
            )
            if policy.currency != tariff.currency:
                raise FinancialAdmissionDenied('FX_POLICY_REQUIRED')
            amount = _reserve_amount(tariff=tariff, policy=policy, max_input_tokens=max_input_tokens, max_output_tokens=max_output_tokens)
            scopes = _applicable_scopes(organization=organization, product=product, policy=policy, now=now)
            for scope in scopes:
                if scope.request_limit is not None and scope.reserved_request_count >= scope.request_limit:
                    raise FinancialAdmissionDenied('REQUEST_QUOTA_EXHAUSTED')
                used = scope.reserved_exposure + scope.settled_exposure + scope.unresolved_exposure + scope.approved_liability
                if scope.limit_amount - used < amount:
                    raise FinancialAdmissionDenied('BUDGET_EXHAUSTED')
        except FinancialAdmissionDenied as denial:
            return _persist_denial(registration=registration, organization=organization, product=product, invocation_id=invocation_id, material_hash=material_hash, correlation_id=correlation_id, code=denial.code)
        decision = AdmissionDecision.objects.create(
            producer_registration=registration, organization=organization, product=product,
            invocation_id=invocation_id, material_request_hash=material_hash,
            decision_state='reserved', correlation_id=correlation_id,
            policy_version=policy, tariff=tariff, currency=policy.currency, reserved_amount=amount,
        )
        reservation = FinancialReservation.objects.create(
            admission_decision=decision, organization=organization, product=product,
            policy_version=policy, tariff=tariff, currency=policy.currency, reserved_amount=amount,
            state='reserved', budget_period_start=scopes[0].period_start, budget_period_end=scopes[0].period_end,
        )
        for scope in scopes:
            BudgetScope.objects.filter(pk=scope.pk).update(
                reserved_exposure=F('reserved_exposure') + amount,
                reserved_request_count=F('reserved_request_count') + 1,
            )
        FinancialAuditEvent.objects.create(
            organization=organization, event_type='admission_reserved',
            actor_reference=f'producer_registration:{registration.id}', correlation_id=correlation_id,
            entity_type='financial_reservation', entity_id=reservation.id, payload_hash=material_hash,
            metadata={'scope_ids': [str(scope.id) for scope in scopes], 'synthetic_only': True},
        )
        return _result(decision)
