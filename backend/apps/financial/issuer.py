"""Trusted issuer decision logic for the Decision 02-A test boundary.

This module does not load or create a private key.  Deployment must inject a
signer owned by the isolated issuer process.  The synthetic test harness passes
an ephemeral signer directly and destroys it at process exit.
"""
from django.utils import timezone
from django.db.models import Q

from .authorization import FinancialAuthorizationDenied, authenticate_registered_producer
from .capabilities import mint_capability
from .models import ProducerTenantGrant, ProducerTenantGrantLifecycleEvent


def _active_grant(*, registration_id, organization_id, product_id, environment, now):
    grant = ProducerTenantGrant.objects.filter(
        producer_registration_id=registration_id, organization_id=organization_id,
        product_id=product_id, operation='admit_reserve', environment=environment,
        state='active', effective_from__lte=now,
    ).filter(Q(effective_until__isnull=True) | Q(effective_until__gt=now)).first()
    if not grant:
        raise FinancialAuthorizationDenied('producer_tenant_grant_denied')
    event = grant.lifecycle_events.order_by('-created_at', '-id').only('state').first()
    if event is None or event.state != 'active':
        raise FinancialAuthorizationDenied('producer_tenant_grant_denied')
    return grant


def issue_admission_capability(*, raw_api_key, environment, organization_id, product_id,
                               invocation_id, material_request_hash, private_key,
                               issuer_id, key_id, now=None):
    """Authenticate the producer and issue only an explicitly granted capability."""
    principal = authenticate_registered_producer(
        raw_api_key=raw_api_key, environment=environment, product_id=product_id,
        operation='admit_reserve',
    )
    now = now or timezone.now()
    grant = _active_grant(
        registration_id=principal.registration_id, organization_id=organization_id,
        product_id=product_id, environment=environment, now=now,
    )
    return mint_capability(
        private_key=private_key, issuer_id=issuer_id, key_id=key_id,
        producer_registration_id=principal.registration_id, organization_id=organization_id,
        product_id=product_id, environment=environment, invocation_id=invocation_id,
        material_request_hash=material_request_hash, grant_id=grant.id,
        grant_version=grant.version, now=now,
    )


def transition_producer_tenant_grant(*, grant, state, actor_reference, evidence_hash, reason_code):
    """Record a grant transition; revoked grants cannot be silently reactivated."""
    if state not in dict(ProducerTenantGrant.STATES):
        raise ValueError('Unknown producer-to-tenant grant state.')
    current = grant.lifecycle_events.order_by('-created_at', '-id').first()
    if current and current.state == 'revoked' and state != 'revoked':
        raise ValueError('Revoked producer-to-tenant grants cannot be reactivated.')
    if current and current.state == state:
        raise ValueError('Grant lifecycle transition must change state.')
    grant.state = state
    if state == 'revoked':
        grant.revocation_evidence_hash = evidence_hash
    grant.version += 1
    grant.save(update_fields=['state', 'revocation_evidence_hash', 'version'])
    return ProducerTenantGrantLifecycleEvent.objects.create(
        grant=grant, state=state, actor_reference=actor_reference,
        evidence_hash=evidence_hash, reason_code=reason_code,
    )
