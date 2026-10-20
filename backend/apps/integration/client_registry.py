"""Authenticated, durable client resolution; request fields are assertions only."""
from dataclasses import dataclass
from functools import wraps
import json

from django.http import JsonResponse
from rest_framework.exceptions import APIException, AuthenticationFailed

from .models import IntegrationAPIKey, SSOClient
from .services import authenticate_integration_api_key
from .trust_jwt import CONTRACT, PRODUCTS, TrustUnavailable, trust


@dataclass(frozen=True)
class ClientContract:
    client_id: str
    product: str
    audience: str
    issuer: str
    principal_id: int
    allowed_kids: tuple[str, ...]
    version: str = CONTRACT
    token_family: str = 'CENTRAL'
    algorithm: str = 'RS256'
    credential_policy: str = 'hashed_v1'

    @classmethod
    def from_row(cls, row, *, require_enabled=True):
        principal = row.principal
        if ((require_enabled and row.enabled is not True)
                or type(row.enabled) is not bool or row.product.code not in PRODUCTS or not row.product.is_available
                or principal.is_active is not True or principal.status != 'active'
                or principal.credential_format != 'hashed_v1' or not principal.pk
                or row.contract_version != CONTRACT or row.token_family != 'CENTRAL'
                or row.algorithm != 'RS256' or row.credential_policy != 'hashed_v1'
                or not isinstance(row.allowed_kids, list) or not row.allowed_kids
                or any(not isinstance(k, str) or not k for k in row.allowed_kids)
                or len(set(row.allowed_kids)) != len(row.allowed_kids)
                or any(not isinstance(v, str) or not v.strip() for v in (row.client_id, row.audience, row.issuer))):
            raise AuthenticationFailed('Invalid client contract.')
        return cls(row.client_id, row.product.code, row.audience, row.issuer, principal.pk, tuple(row.allowed_kids))


def resolve(request, data):
    raw = request.headers.get('X-API-Key')
    principal = authenticate_integration_api_key(raw) if raw else None
    # Configured hash aliases and legacy plaintext rows are deliberately excluded.
    if (not isinstance(principal, IntegrationAPIKey) or not principal.pk
            or principal.is_active is not True or principal.status != 'active'
            or principal.credential_format != 'hashed_v1'):
        raise AuthenticationFailed('Invalid integration principal.')
    try:
        row = SSOClient.objects.select_related('principal', 'product').get(principal_id=principal.pk)
    except SSOClient.DoesNotExist:
        raise AuthenticationFailed('Unregistered integration principal.') from None
    client = ClientContract.from_row(row)
    if (client.principal_id != principal.pk or data.get('client_id') != client.client_id
            or data.get('product') != client.product or data.get('audience') != [client.audience]
            or data.get('contract_version') != CONTRACT):
        raise AuthenticationFailed('Client context mismatch.')
    config, keys = trust('CENTRAL')
    if client.issuer != config['ISSUER'] or any(k not in keys for k in client.allowed_kids):
        raise TrustUnavailable()
    request.sso_client = client
    request.sso_client_row = row
    return client


def require_tenant(request, tenant_id):
    if not request.sso_client_row.tenants.filter(pk=tenant_id, status='active').exists():
        raise AuthenticationFailed('Tenant outside client contract.')


def require_client(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            data = json.loads(request.body or '{}')
            if not isinstance(data, dict):
                raise AuthenticationFailed('Invalid client request.')
            from .session_lifecycle import authentication_epoch
            request.sso_authority_epoch = authentication_epoch()
            resolve(request, data)
            return view(request, *args, **kwargs)
        except APIException as exc:
            return JsonResponse({'active': False, 'error': 'Authentication rejected.', 'code': exc.default_code}, status=exc.status_code)
        except (ValueError, TypeError):
            return JsonResponse({'active': False, 'error': 'Invalid request.'}, status=400)
        except Exception:
            return JsonResponse({'active': False, 'error': 'Authentication authority unavailable.'}, status=503)
    return wrapped
