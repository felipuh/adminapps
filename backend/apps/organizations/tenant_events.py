"""Versioned tenant integration facts from the active AdminApps customer aggregate."""

from uuid import uuid4

from django.db.models import Max
from django.utils import timezone

from .models import TenantIntegrationOutbox


STATUS_LIFECYCLE = {
    'trial': 'active',
    'active': 'active',
    'inactive': 'suspended',
    'suspended': 'suspended',
}


def record_tenant_event(organization, *, trace_id=None, correlation_id=None, actor_id=None):
    """Call inside the same transaction as the organization mutation.

    The caller holds the organization row lock on updates. Creation is unique
    by aggregate UUID, and (organization, source_version) is unique in SQL.
    """
    version = (TenantIntegrationOutbox.objects.filter(organization=organization)
               .aggregate(value=Max('source_version'))['value'] or 0) + 1
    event_id = uuid4()
    status = STATUS_LIFECYCLE[organization.status]
    event_type = ('tenant.provisioned' if version == 1 else
                  'tenant.suspended' if status == 'suspended' else 'tenant.updated')
    envelope = {
        'event_id': str(event_id),
        'event_type': event_type,
        'schema_version': 1,
        'source': 'adminapps',
        'source_version': version,
        'occurred_at': timezone.now().isoformat(),
        'trace_id': str(trace_id or uuid4()),
        'correlation_id': str(correlation_id) if correlation_id else None,
        'aggregate_type': 'tenant',
        'aggregate_id': str(organization.id),
        'adminapps_tenant_id': str(organization.id),
        'actor_id': str(actor_id) if actor_id else None,
        'payload': {
            'display_name': organization.name,
            'lifecycle_status': status,
            'adminapps_status': organization.status,
        },
    }
    return TenantIntegrationOutbox.objects.create(
        id=event_id, organization=organization, source_version=version,
        envelope=envelope,
    )
