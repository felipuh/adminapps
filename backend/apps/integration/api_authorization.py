"""Explicit grants for legacy service data APIs; independent of SSO client trust.

INTEGRATION_API_GRANTS is server-owned configuration keyed by credential_id, with
operations (exact handler names), tenant_ids and product_codes. Empty/missing
configuration denies. No name, global user role or SSOClient creates a grant.
"""
from functools import wraps
import json
import uuid

from django.conf import settings
from django.http import JsonResponse
from .models import IntegrationAPIKey
from .authorization_contract import CATALOG

OPERATIONS = frozenset({
    'list_organizations', 'get_organization', 'get_organization_users',
    'get_organization_modules', 'get_organization_products',
    'validate_organization_product_access', 'get_user_by_id',
})


def exact_list(values, allowed=None):
    return (isinstance(values, list) and bool(values)
            and all(isinstance(value, str) and value for value in values)
            and len(set(values)) == len(values)
            and (allowed is None or set(values) <= allowed))


def service_data_access(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        principal = getattr(request, 'integration_principal', None)
        grants = getattr(settings, 'INTEGRATION_API_GRANTS', {})
        grant = grants.get(getattr(principal, 'credential_id', None), {}) if isinstance(grants, dict) else {}
        operations = grant.get('operations', []) if isinstance(grant, dict) else []
        tenants = grant.get('tenant_ids', []) if isinstance(grant, dict) else []
        products = grant.get('product_codes', []) if isinstance(grant, dict) else []
        if (not isinstance(principal, IntegrationAPIKey) or principal.is_active is not True
                or not principal.pk or principal.revoked_at is not None
                or principal.status != 'active' or principal.credential_format != 'hashed_v1'
                or not principal.credential_id or not exact_list(operations, OPERATIONS)
                or view.__name__ not in operations or not exact_list(tenants)
                or not exact_list(products, set(CATALOG))
                or set(grant) != {'operations', 'tenant_ids', 'product_codes'}):
            return JsonResponse({'code': 'service_operation_denied'}, status=403)
        try:
            tenant_ids = {str(uuid.UUID(str(value))) for value in tenants}
            tenant = kwargs.get('org_id')
            if view.__name__ == 'get_user_by_id':
                payload = json.loads(request.body)
                tenant = payload.get('organization_id') if isinstance(payload, dict) else None
                if not tenant:
                    raise ValueError()
                uuid.UUID(str(payload.get('user_id')))
            if tenant is not None and str(uuid.UUID(str(tenant))) not in tenant_ids:
                return JsonResponse({'code': 'service_tenant_denied'}, status=403)
        except (ValueError, TypeError, AttributeError):
            return JsonResponse({'code': 'invalid_service_tenant'}, status=400)
        if view.__name__ in {'get_organization_products', 'validate_organization_product_access'}:
            product = kwargs.get('product_code')
            if product and product.upper() not in products:
                return JsonResponse({'code': 'service_product_denied'}, status=403)
        request.authorized_tenant_ids = tenant_ids
        request.authorized_product_codes = products
        return view(request, *args, **kwargs)
    return wrapped
