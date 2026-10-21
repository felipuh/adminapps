import hashlib
import hmac

from django.conf import settings


_FINGERPRINT_PREFIX = b'AdminApps IntegrationAPIKey fingerprint v1\0'


def integration_api_key_fingerprint(raw_key):
    """Return a versioned keyed fingerprint, separate from the auth verifier."""
    fingerprint = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        _FINGERPRINT_PREFIX + raw_key.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return f'hmac-sha256-v1:{fingerprint}'
