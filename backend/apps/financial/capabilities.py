"""Versioned Ed25519 admission capabilities.

Private keys are injected only into the isolated issuer process in disposable
validation.  They are intentionally never persisted by Django models, settings,
migrations, source constants, or logs.
"""
import base64
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


CAPABILITY_VERSION = 1
CAPABILITY_ALGORITHM = 'Ed25519'
CAPABILITY_AUDIENCE = 'adminapps-financial-admission'
CAPABILITY_DOMAIN = 'adminapps.financial.admission-capability.v1'


class CapabilityDenied(PermissionError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _b64encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')


def _b64decode(value):
    if not isinstance(value, str):
        raise CapabilityDenied('CAPABILITY_MALFORMED')
    try:
        return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
    except Exception as exc:
        raise CapabilityDenied('CAPABILITY_MALFORMED') from exc


def canonical_capability_bytes(claims):
    """Canonical JSON signed under a financial-only domain separator."""
    return (CAPABILITY_DOMAIN + '\n' + json.dumps(
        claims, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False,
    )).encode('utf-8')


def _iso(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _time(value, name):
    if not isinstance(value, str) or not value.endswith('Z'):
        raise CapabilityDenied('CAPABILITY_TIME_INVALID')
    try:
        return datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError as exc:
        raise CapabilityDenied('CAPABILITY_TIME_INVALID') from exc


_REQUIRED = frozenset({
    'alg', 'aud', 'capability_id', 'environment', 'exp', 'grant_id', 'grant_version',
    'iat', 'iss', 'jti', 'kid', 'material_request_hash', 'nbf', 'operation',
    'organization_id', 'product_id', 'producer_registration_id', 'version',
})


def mint_capability(*, private_key, issuer_id, key_id, producer_registration_id,
                    organization_id, product_id, environment, invocation_id,
                    material_request_hash, grant_id, grant_version, now=None,
                    lifetime_seconds=60):
    """Issue a short-lived capability from an already-authorized issuer decision."""
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError('private_key must be an Ed25519PrivateKey')
    if not isinstance(lifetime_seconds, int) or lifetime_seconds <= 0 or lifetime_seconds > 60:
        raise ValueError('S3 capabilities must have a positive lifetime of at most 60 seconds')
    now = now or datetime.now(timezone.utc)
    claims = {
        'alg': CAPABILITY_ALGORITHM, 'aud': CAPABILITY_AUDIENCE,
        'capability_id': str(uuid.uuid4()), 'environment': environment,
        'exp': _iso(now + timedelta(seconds=lifetime_seconds)), 'grant_id': str(grant_id),
        'grant_version': int(grant_version), 'iat': _iso(now), 'iss': issuer_id,
        'jti': str(invocation_id), 'kid': key_id, 'material_request_hash': material_request_hash,
        'nbf': _iso(now), 'operation': 'admit_reserve',
        'organization_id': str(organization_id), 'product_id': str(product_id),
        'producer_registration_id': str(producer_registration_id), 'version': CAPABILITY_VERSION,
    }
    payload = canonical_capability_bytes(claims)
    return _b64encode(json.dumps(claims, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8')) + '.' + _b64encode(private_key.sign(payload))


def verify_capability(token, *, public_keys, issuer_id, now=None, expected=None):
    """Verify the exact, versioned claim set before any database effect."""
    try:
        payload_part, signature_part = token.split('.')
        claims = json.loads(_b64decode(payload_part).decode('utf-8'))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapabilityDenied('CAPABILITY_MALFORMED') from exc
    if not isinstance(claims, dict) or set(claims) != _REQUIRED:
        raise CapabilityDenied('CAPABILITY_CLAIMS_INVALID')
    if claims['alg'] != CAPABILITY_ALGORITHM:
        raise CapabilityDenied('CAPABILITY_ALGORITHM_DENIED')
    if claims['version'] != CAPABILITY_VERSION:
        raise CapabilityDenied('CAPABILITY_VERSION_DENIED')
    if claims['aud'] != CAPABILITY_AUDIENCE or claims['iss'] != issuer_id:
        raise CapabilityDenied('CAPABILITY_AUDIENCE_DENIED')
    public_key = public_keys.get(claims['kid'])
    if not isinstance(public_key, Ed25519PublicKey):
        raise CapabilityDenied('CAPABILITY_KEY_UNKNOWN')
    try:
        public_key.verify(_b64decode(signature_part), canonical_capability_bytes(claims))
    except InvalidSignature as exc:
        raise CapabilityDenied('CAPABILITY_SIGNATURE_INVALID') from exc
    now = now or datetime.now(timezone.utc)
    issued, not_before, expires = (_time(claims[name], name) for name in ('iat', 'nbf', 'exp'))
    if not (issued <= not_before <= expires) or expires - issued > timedelta(seconds=60):
        raise CapabilityDenied('CAPABILITY_TIME_INVALID')
    if now < not_before or now >= expires:
        raise CapabilityDenied('CAPABILITY_EXPIRED')
    for key, value in (expected or {}).items():
        if claims.get(key) != str(value):
            raise CapabilityDenied('CAPABILITY_BINDING_DENIED')
    return claims


def public_key_bytes(private_key):
    """Return public verification material for an executor key allow-list."""
    return private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
