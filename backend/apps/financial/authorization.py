"""Fail-closed producer identity checks for the non-operational S2 boundary."""

from dataclasses import dataclass
from typing import Optional

from django.core.exceptions import ValidationError

from apps.integration.models import IntegrationAPIKey
from apps.integration.services import authenticate_integration_api_key

from .models import ProducerRegistration, ProducerRegistrationLifecycleEvent


FINANCIAL_OPERATIONS = frozenset({
    'admit_reserve',
    'settle',
    'status_read',
    'submit_evidence',
})


class FinancialAuthorizationDenied(PermissionError):
    """A safe, code-bearing authorization denial with no credential disclosure."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class RegisteredProducerPrincipal:
    registration_id: str
    producer_code: str
    credential_id: str
    credential_fingerprint: str
    environment: str


def _deny(code):
    raise FinancialAuthorizationDenied(code)


def _current_lifecycle_state(registration: ProducerRegistration) -> Optional[str]:
    event = (
        ProducerRegistrationLifecycleEvent.objects
        .filter(registration=registration)
        .order_by('-created_at', '-id')
        .only('lifecycle_state')
        .first()
    )
    return event.lifecycle_state if event else None


def authenticate_registered_producer(*, raw_api_key, environment, product_id, operation):
    """Authenticate only a dedicated active registration with exact S2 scopes.

    This function intentionally does not consult settings-based service-name
    fallback as financial authority.  The generic verifier may identify a
    credential, but only a one-to-one registered, hashed credential can pass.
    It also makes no tenant-admission or budget decision; those remain S3.
    """
    if operation not in FINANCIAL_OPERATIONS:
        _deny('financial_operation_denied')
    credential = authenticate_integration_api_key(raw_api_key)
    if not isinstance(credential, IntegrationAPIKey):
        _deny('unregistered_financial_credential')
    if (
        credential.credential_format != 'hashed_v1'
        or not credential.credential_id
        or not credential.fingerprint
        or credential.status != 'active'
        or not credential.is_active
    ):
        _deny('invalid_financial_credential')

    registrations = list(
        ProducerRegistration.objects.filter(credential=credential).only(
            'id', 'producer_code', 'credential_id', 'credential_fingerprint',
            'environment', 'permitted_product_ids', 'permitted_operations',
        )[:2]
    )
    if len(registrations) != 1:
        _deny('unregistered_financial_credential')
    registration = registrations[0]
    if registration.credential_fingerprint != credential.fingerprint:
        _deny('credential_binding_mismatch')
    if _current_lifecycle_state(registration) != 'active':
        _deny('producer_registration_inactive')
    if registration.environment != environment:
        _deny('financial_environment_denied')
    if str(product_id) not in {str(value) for value in registration.permitted_product_ids}:
        _deny('financial_product_denied')
    if operation not in set(registration.permitted_operations):
        _deny('financial_operation_denied')
    return RegisteredProducerPrincipal(
        registration_id=str(registration.id),
        producer_code=registration.producer_code,
        credential_id=credential.credential_id,
        credential_fingerprint=credential.fingerprint,
        environment=registration.environment,
    )


def validate_s2_registration(*, credential, environment, product_ids, operations):
    """Validate data before an append-only registration is created."""
    if not isinstance(credential, IntegrationAPIKey):
        raise ValidationError('A persisted IntegrationAPIKey is required.')
    if (
        credential.credential_format != 'hashed_v1'
        or not credential.credential_id
        or not credential.fingerprint
        or credential.status != 'active'
        or not credential.is_active
    ):
        raise ValidationError('Financial registrations require an active hashed credential.')
    if not product_ids:
        raise ValidationError('At least one explicitly permitted product is required.')
    if not operations or not set(operations).issubset(FINANCIAL_OPERATIONS):
        raise ValidationError('Registration operations must be explicit S2 financial operations.')
    if environment not in dict(ProducerRegistration.ENVIRONMENTS):
        raise ValidationError('Unknown producer environment.')
