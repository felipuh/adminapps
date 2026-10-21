"""Secret-free outbox adapter. No worker, network transport or scheduler is started.

TenantIntegrationOutbox uses tenant source versions and an incompatible envelope;
SSO retains its transaction/outbox pattern in a dedicated stream. A transport
must authenticate its receiver, return the exact event id, and handle duplicates.
"""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import SSORevocationOutbox
from .session_lifecycle import mfa


def envelope(event):
    return {'event_id': str(event.id), 'schema_version': 1, 'type': 'sso.generation.invalidated',
            'source': 'adminapps', 'sid': str(event.session_id), 'generation': event.generation,
            'client_id': event.client_id_snapshot, 'product': event.product,
            'tenant_id': str(event.tenant_id_snapshot), 'reason': event.reason,
            'trace_id': str(event.correlation_id)}


def invalidation_watermark(previous, event, *, client_id, product, tenant_id, session_id):
    """Pure receiver reducer; never authorizes. Store max transactionally if used.

Transport authentication precedes this reducer. No receiver cache replaces live
introspection; late/duplicate events cannot lower a deny watermark.
"""
    import uuid
    if (event.get('schema_version') != 1 or event.get('type') != 'sso.generation.invalidated'
            or event.get('source') != 'adminapps' or event.get('client_id') != client_id
            or event.get('product') != product or event.get('tenant_id') != str(tenant_id)
            or event.get('sid') != str(session_id)
            or type(event.get('generation')) is not int or event['generation'] <= 0
            or type(previous) is not int or previous < 0):
        raise ValueError('Invalid revocation event')
    uuid.UUID(event['event_id'])
    uuid.UUID(event['trace_id'])
    return max(previous, event['generation'])


def deliver_one(event_id, sender):
    """Explicit adapter invocation only; retries persist, errors contain no payload.

Locks only the outbox row, not the authority fence. sender must use a bounded
network timeout. A delivery followed by rollback can repeat; receiver dedupes.
"""
    mfa.require_commit_boundary()
    with transaction.atomic(durable=True):
        event = SSORevocationOutbox.objects.select_for_update().get(pk=event_id)
        now = timezone.now()
        if event.delivered_at or (event.next_attempt_at and event.next_attempt_at > now):
            return False
        event.attempts += 1
        try:
            ack = sender(envelope(event))
            if not isinstance(ack, dict) or ack.get('event_id') != str(event.id):
                raise ValueError()
        except Exception:
            event.next_attempt_at = now + timedelta(seconds=min(3600, 2 ** min(event.attempts, 12)))
        else:
            event.delivered_at = now
            event.next_attempt_at = None
        event.save(update_fields=['attempts', 'delivered_at', 'next_attempt_at'])
        return event.delivered_at is not None
