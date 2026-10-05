"""Credential lifecycle operations for Integration API keys."""

import hashlib
import hmac
import re
import secrets
import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .credentials import integration_api_key_fingerprint
from .models import IntegrationAPIKey, IntegrationAPIKeyAuditEvent

_SECURE_KEY_PATTERN = re.compile(r'^iak_([a-f0-9]{32})\.([A-Za-z0-9_-]{43})$')


def _require_operator(operator):
    if (
        operator is None
        or not getattr(operator, 'is_authenticated', False)
        or not operator.is_active
        or not operator.is_staff
    ):
        raise PermissionDenied('An active staff operator is required.')


def _new_credential(name):
    credential_id = uuid.uuid4().hex
    raw_key = f'iak_{credential_id}.{secrets.token_urlsafe(32)}'
    fingerprint = integration_api_key_fingerprint(raw_key)
    credential = IntegrationAPIKey.objects.create(
        name=name,
        key=None,
        credential_id=credential_id,
        credential_hash=make_password(raw_key),
        credential_format='hashed_v1',
        fingerprint=fingerprint,
        status='active',
        is_active=True,
    )
    return credential, raw_key


def create_integration_api_key(*, name, operator):
    """Create a secure key and return its raw value once with the safe record."""
    _require_operator(operator)
    with transaction.atomic():
        credential, raw_key = _new_credential(name)
        IntegrationAPIKeyAuditEvent.objects.create(
            action='created',
            new_credential=credential,
            new_fingerprint=credential.fingerprint,
            service_name=credential.name,
            actor=operator,
            metadata={'new_status': credential.status},
        )
    return credential, raw_key


def rotate_integration_api_key(*, credential_id, operator):
    """Atomically replace an active key and return the new secret exactly once."""
    _require_operator(operator)
    with transaction.atomic():
        try:
            old_credential = IntegrationAPIKey.objects.select_for_update().get(
                pk=credential_id
            )
        except IntegrationAPIKey.DoesNotExist as exc:
            raise ValidationError('Integration API key not found.') from exc

        if not old_credential.is_active or old_credential.status != 'active':
            raise ValidationError('Only an active Integration API key can be rotated.')

        if old_credential.credential_format == 'legacy_plaintext':
            legacy_key = old_credential.key
            if not legacy_key:
                raise ValidationError('Legacy credential has no recoverable key to rotate.')
            old_fingerprint = integration_api_key_fingerprint(legacy_key)
        else:
            legacy_key = None
            old_fingerprint = old_credential.fingerprint
            if not old_credential.credential_hash or not old_fingerprint:
                raise ValidationError('Hashed credential metadata is incomplete.')

        replacement, raw_replacement = _new_credential(old_credential.name)
        now = timezone.now()
        old_status = old_credential.status
        old_credential.status = 'rotated'
        old_credential.is_active = False
        old_credential.revoked_at = now
        old_credential.rotated_at = now
        old_credential.replaced_by = replacement
        old_credential.fingerprint = old_fingerprint
        if legacy_key is not None:
            old_credential.credential_hash = make_password(legacy_key)
            old_credential.credential_format = 'hashed_v1'
        old_credential.key = None
        old_credential.save(update_fields=[
            'status',
            'is_active',
            'revoked_at',
            'rotated_at',
            'replaced_by',
            'fingerprint',
            'credential_hash',
            'credential_format',
            'key',
            'updated_at',
        ])
        IntegrationAPIKeyAuditEvent.objects.create(
            action='rotated',
            old_credential=old_credential,
            new_credential=replacement,
            old_fingerprint=old_fingerprint,
            new_fingerprint=replacement.fingerprint,
            service_name=old_credential.name,
            actor=operator,
            metadata={
                'old_status_before_rotation': old_status,
                'old_status_after_rotation': old_credential.status,
                'new_status': replacement.status,
                'revoked_at': now.isoformat(),
            },
        )
    return replacement, raw_replacement


def authenticate_integration_api_key(raw_key):
    """Resolve a valid active row or a configured hash fallback."""
    if not raw_key:
        return None

    secure_match = _SECURE_KEY_PATTERN.fullmatch(raw_key)
    if secure_match:
        credential_id = secure_match.group(1)
        credential = IntegrationAPIKey.objects.filter(
            credential_id=credential_id,
        ).first()
        if credential is not None:
            if (
                credential.status == 'active'
                and credential.is_active
                and credential.credential_format == 'hashed_v1'
                and check_password(raw_key, credential.credential_hash)
            ):
                return credential
            if credential.status in {'revoked', 'rotated'}:
                return None

    unprefixed_credentials = IntegrationAPIKey.objects.filter(
        credential_id__isnull=True,
        credential_format='hashed_v1',
        status='active',
        is_active=True,
    )
    for credential in unprefixed_credentials.iterator():
        if check_password(raw_key, credential.credential_hash):
            return credential

    legacy_credential = IntegrationAPIKey.objects.filter(
        key=raw_key,
        credential_format='legacy_plaintext',
        status='active',
        is_active=True,
    ).first()
    if legacy_credential is not None:
        return legacy_credential

    valid_keys = getattr(settings, 'INTEGRATION_API_KEYS', {})
    provided_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    service_name = next(
        (
            name
            for name, key_hash in valid_keys.items()
            if key_hash and hmac.compare_digest(provided_hash, key_hash)
        ),
        None,
    )
    if not service_name:
        return None

    revoked_hashes = IntegrationAPIKey.objects.filter(
        status__in=('revoked', 'rotated'),
        credential_hash__gt='',
    ).values_list('credential_hash', flat=True)
    if any(check_password(raw_key, stored_hash) for stored_hash in revoked_hashes):
        return None
    return service_name
