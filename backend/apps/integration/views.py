"""
Vistas de Integración para Admin Apps
Proporciona endpoints para que servicios externos (como ISO Smart) 
puedan consultar información de Admin Apps
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.db.models import Count
from functools import wraps
import hashlib
import hmac
import json

from apps.organizations.models import Organization
from apps.products.models import OrganizationProductEntitlement
from apps.users.models import UserOrganization
from .models import IntegrationAPIKey, LandingAnalyticsEvent

User = get_user_model()

MODULE_CODE_MAP = {
    'sca': {'code': 'SCA', 'name': 'SCA'},
    'sie': {'code': 'SIE', 'name': 'SIE'},
    'asb': {'code': 'ASB', 'name': 'ASB'},
    'spm': {'code': 'SPM', 'name': 'SPM'},
    'documents': {'code': 'DOC', 'name': 'Documentos'},
    'risks': {'code': 'RISK', 'name': 'Riesgos'},
    'objectives': {'code': 'OBJ', 'name': 'Objetivos'},
    'medsupplier': {'code': 'MEDSUPPLIER', 'name': 'ISO Smart MedSupplier'},
}


def _subscription_payload(subscription):
    if not subscription:
        return {
            'status': 'not_configured',
            'is_active': False,
            'billing_status': 'not_configured',
        }
    return {
        'id': str(subscription.id),
        'status': subscription.status,
        'is_active': subscription.is_active,
        'billing_status': subscription.status,
        'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        'next_billing_date': subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
    }


def _entitlement_payload(entitlement):
    subscription = entitlement.subscription or entitlement.organization.subscription
    return {
        'id': str(entitlement.id),
        'code': entitlement.product.code,
        'name': entitlement.product.name,
        'slug': entitlement.product.slug,
        'enabled': entitlement.enabled,
        'status': entitlement.status,
        'is_active': entitlement.is_active,
        'access_allowed': entitlement.access_allowed,
        'access_denial_reason': entitlement.access_denial_reason,
        'modules_enabled': entitlement.modules_enabled,
        'scopes': entitlement.scopes,
        'billing_status': _subscription_payload(subscription)['billing_status'],
        'subscription': _subscription_payload(subscription),
    }


def _active_product_entitlements(org):
    return (
        OrganizationProductEntitlement.objects
        .filter(organization=org, enabled=True, product__status__in=['active', 'beta'])
        .select_related('organization', 'product', 'subscription')
    )


def require_api_key(view_func):
    """
    Decorator para requerir API Key en las peticiones
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return JsonResponse({
                'error': 'API Key requerida',
                'code': 'missing_api_key'
            }, status=401)
        
        # Verificar primero contra la base de datos
        service_name = None
        try:
            key_obj = IntegrationAPIKey.objects.get(key=api_key, is_active=True)
            service_name = key_obj.name
        except IntegrationAPIKey.DoesNotExist:
            # Fallback opcional a hashes en settings para claves de entorno.
            valid_keys = getattr(settings, 'INTEGRATION_API_KEYS', {})
            provided_hash = hashlib.sha256(api_key.encode()).hexdigest()
            for name, key_hash in valid_keys.items():
                if key_hash and hmac.compare_digest(provided_hash, key_hash):
                    service_name = name
                    break

            if not service_name:
                return JsonResponse({
                    'error': 'API Key inválida',
                    'code': 'invalid_api_key'
                }, status=401)

        request.integration_service = service_name
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


@csrf_exempt
@require_http_methods(["GET"])
@require_api_key
def health_check(request):
    """
    Health check endpoint
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'Admin Apps Integration',
        'version': '1.0'
    })


@csrf_exempt
@require_http_methods(["GET"])
@require_api_key
def list_organizations(request):
    """
    Lista todas las organizaciones activas
    """
    organizations = Organization.objects.filter(status='active')
    
    data = {
        'organizations': [
            {
                'id': str(org.id),
                'name': org.name,
                'code': org.code,
                'slug': org.code.lower(),
                'status': org.status,
                'is_active': org.is_active,
                'created_at': org.created_at.isoformat(),
            }
            for org in organizations
        ]
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@require_api_key
def get_organization(request, org_id):
    """
    Obtiene detalle de una organización
    """
    try:
        org = Organization.objects.get(id=org_id, status='active')
    except Organization.DoesNotExist:
        return JsonResponse({
            'error': 'Organización no encontrada',
            'code': 'organization_not_found'
        }, status=404)
    
    data = {
        'id': str(org.id),
        'name': org.name,
        'code': org.code,
        'slug': org.code.lower(),
        'status': org.status,
        'is_active': org.is_active,
        'created_at': org.created_at.isoformat(),
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@require_api_key
def get_organization_users(request, org_id):
    """
    Obtiene usuarios de una organización
    """
    try:
        org = Organization.objects.get(id=org_id, status='active')
    except Organization.DoesNotExist:
        return JsonResponse({
            'error': 'Organización no encontrada',
            'code': 'organization_not_found'
        }, status=404)
    
    members = UserOrganization.objects.filter(
        organization=org,
        is_active=True
    ).select_related('user')
    
    data = {
        'organization_id': org.id,
        'organization_name': org.name,
        'users': [
            {
                'id': member.user.id,
                'email': member.user.email,
                'first_name': member.user.first_name,
                'last_name': member.user.last_name,
                'role': member.role,
                'is_active': member.is_active,
            }
            for member in members
        ]
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@require_api_key
def get_organization_modules(request, org_id):
    """
    Obtiene módulos habilitados para una organización
    """
    try:
        org = Organization.objects.get(id=org_id, status='active')
    except Organization.DoesNotExist:
        return JsonResponse({
            'error': 'Organización no encontrada',
            'code': 'organization_not_found'
        }, status=404)
    
    owner_org_name = getattr(settings, 'BILLING_OWNER_ORG_NAME', 'Smart3AI')
    owner_org_code = getattr(settings, 'BILLING_OWNER_ORG_CODE', '')
    owner_org_id = getattr(settings, 'BILLING_OWNER_ORG_ID', '')
    metadata = org.metadata or {}
    is_owner_exempt = (
        bool(metadata.get('billing_exempt') or metadata.get('owner_organization'))
        or (owner_org_name and org.name.lower() == owner_org_name.lower())
        or (owner_org_code and org.code.lower() == owner_org_code.lower())
        or (owner_org_id and str(org.id) == str(owner_org_id))
    )

    modules = list(MODULE_CODE_MAP.values()) if is_owner_exempt else []

    product_entitlements = list(_active_product_entitlements(org))
    for entitlement in product_entitlements:
        if entitlement.access_allowed:
            modules.append({
                'code': entitlement.product.code,
                'name': entitlement.product.name,
                'enabled': entitlement.enabled,
                'status': entitlement.status,
                'source': 'product_entitlement',
                'billing_status': _subscription_payload(entitlement.subscription or org.subscription)['billing_status'],
            })

    subscription = org.subscription
    if not is_owner_exempt and subscription and subscription.is_active:
        plan_modules = subscription.plan.modules_included
        if isinstance(plan_modules, list):
            for module in plan_modules:
                if isinstance(module, str):
                    normalized = module.strip().lower()
                    mapped = MODULE_CODE_MAP.get(normalized)
                    if mapped:
                        modules.append(mapped)
                    else:
                        modules.append({'code': normalized.upper(), 'name': module})
                elif isinstance(module, dict) and 'code' in module:
                    modules.append(module)
    
    # Eliminar duplicados por código
    unique_modules = list({m['code']: m for m in modules if isinstance(m, dict)}.values())
    
    data = {
        'organization_id': str(org.id),
        'organization_name': org.name,
        'modules': unique_modules
    }
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
@require_api_key
def get_organization_products(request, org_id):
    """Lista productos/sistemas habilitados para una organizacion."""
    try:
        org = Organization.objects.get(id=org_id, status='active')
    except Organization.DoesNotExist:
        return JsonResponse({
            'error': 'Organización no encontrada',
            'code': 'organization_not_found'
        }, status=404)

    entitlements = [_entitlement_payload(item) for item in _active_product_entitlements(org)]
    return JsonResponse({
        'organization_id': str(org.id),
        'organization_name': org.name,
        'products': entitlements,
    })


@csrf_exempt
@require_http_methods(["GET"])
@require_api_key
def validate_organization_product_access(request, org_id, product_code):
    """Valida acceso producto-neutral de una organizacion."""
    try:
        org = Organization.objects.get(id=org_id, status='active')
    except Organization.DoesNotExist:
        return JsonResponse({
            'allowed': False,
            'error': 'Organización no encontrada',
            'code': 'organization_not_found'
        }, status=404)

    entitlement = (
        OrganizationProductEntitlement.objects
        .filter(organization=org, product__code=product_code.upper())
        .select_related('organization', 'product', 'subscription')
        .first()
    )
    if not entitlement:
        return JsonResponse({
            'allowed': False,
            'organization_id': str(org.id),
            'product_code': product_code.upper(),
            'reason': 'product_not_enabled',
        }, status=403)

    payload = _entitlement_payload(entitlement)
    return JsonResponse({
        'allowed': entitlement.access_allowed,
        'organization_id': str(org.id),
        'organization_status': org.status,
        'product': payload,
        'reason': entitlement.access_denial_reason,
    }, status=200 if entitlement.access_allowed else 403)


@csrf_exempt
@require_http_methods(["POST"])
@require_api_key
def validate_credentials(request):
    """
    Valida credenciales de un usuario
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido',
            'code': 'invalid_json'
        }, status=400)
    
    email = data.get('email')
    password = data.get('password')
    organization_id = data.get('organization_id')
    
    if not email or not password:
        return JsonResponse({
            'error': 'Email y contraseña requeridos',
            'code': 'missing_credentials'
        }, status=400)
    
    # Autenticar usuario
    user = authenticate(request, username=email, password=password)
    
    if not user:
        return JsonResponse({
            'valid': False,
            'error': 'Credenciales inválidas',
            'code': 'invalid_credentials'
        }, status=401)
    
    # Obtener organizaciones del usuario
    memberships = UserOrganization.objects.filter(
        user=user,
        is_active=True,
        organization__status='active'
    ).select_related('organization')
    
    if not memberships.exists():
        return JsonResponse({
            'valid': False,
            'error': 'Usuario no pertenece a ninguna organización',
            'code': 'no_organization'
        }, status=403)
    
    # Si se especificó una organización, verificar que el usuario pertenezca a ella
    if organization_id:
        membership = memberships.filter(organization_id=organization_id).first()
        if not membership:
            return JsonResponse({
                'valid': False,
                'error': 'Usuario no pertenece a esta organización',
                'code': 'not_member'
            }, status=403)
    else:
        # Usar la primera organización
        membership = memberships.first()
    
    # Construir respuesta
    response_data = {
        'valid': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
        },
        'organizations': [
            {
                'id': m.organization.id,
                'name': m.organization.name,
                'code': m.organization.code,
                'role': m.role,
            }
            for m in memberships
        ],
        'current_organization': {
            'id': membership.organization.id,
            'name': membership.organization.name,
            'code': membership.organization.code,
        },
        'current_role': membership.role,
    }
    
    return JsonResponse(response_data)


@csrf_exempt
@require_http_methods(["POST"])
@require_api_key
def get_user_by_id(request):
    """
    Obtiene información de un usuario por ID
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido',
            'code': 'invalid_json'
        }, status=400)
    
    user_id = data.get('user_id')
    organization_id = data.get('organization_id')
    
    if not user_id:
        return JsonResponse({
            'error': 'user_id requerido',
            'code': 'missing_user_id'
        }, status=400)
    
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({
            'error': 'Usuario no encontrado',
            'code': 'user_not_found'
        }, status=404)
    
    # Obtener organizaciones del usuario
    memberships = UserOrganization.objects.filter(
        user=user,
        is_active=True,
        organization__status='active'
    ).select_related('organization')
    
    # Si se especificó organización, filtrar por ella
    if organization_id:
        memberships = memberships.filter(organization_id=organization_id)
    
    response_data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_active': user.is_active,
        'organizations': [
            {
                'id': m.organization.id,
                'name': m.organization.name,
                'code': m.organization.code,
                'role': m.role,
            }
            for m in memberships
        ]
    }
    
    return JsonResponse(response_data)


@csrf_exempt
@require_http_methods(["POST"])
@require_api_key
def ingest_landing_analytics(request):
    """Ingesta de eventos de analítica del landing de Smart3AI."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido',
            'code': 'invalid_json'
        }, status=400)

    events = data.get('events')
    campaign = str(data.get('campaign') or '').strip()[:120]

    if not isinstance(events, list):
        single_event = data.get('event')
        if isinstance(single_event, dict):
            events = [single_event]
        else:
            return JsonResponse({
                'error': 'Se requiere "events" (array) o "event" (objeto)',
                'code': 'missing_events'
            }, status=400)

    created = 0
    rejected = 0

    for raw in events:
        if not isinstance(raw, dict):
            rejected += 1
            continue

        event_name = str(raw.get('eventName') or raw.get('event_name') or '').strip()
        if not event_name:
            rejected += 1
            continue

        raw_ts = raw.get('ts') or raw.get('timestamp')
        occurred_at = parse_datetime(str(raw_ts)) if raw_ts else None
        if occurred_at is None:
            occurred_at = timezone.now()
        elif timezone.is_naive(occurred_at):
            occurred_at = timezone.make_aware(occurred_at, timezone.get_current_timezone())

        LandingAnalyticsEvent.objects.create(
            event_name=event_name[:80],
            event_date=timezone.localtime(occurred_at).date(),
            occurred_at=occurred_at,
            campaign=campaign,
            variant=str(raw.get('experiment') or raw.get('variant') or '').strip().upper()[:8],
            persona=str(raw.get('persona') or '').strip()[:32],
            intent=str(raw.get('intent') or '').strip()[:24],
            location=str(raw.get('location') or '').strip()[:80],
            session_id=str(raw.get('sessionId') or raw.get('session_id') or '').strip()[:120],
            page_path=str(raw.get('pagePath') or raw.get('page_path') or '').strip()[:255],
            page_url=str(raw.get('pageUrl') or raw.get('page_url') or '').strip(),
            href=str(raw.get('href') or '').strip(),
            referrer=str(raw.get('referrer') or '').strip(),
            source_service=str(getattr(request, 'integration_service', '') or '')[:64],
            payload=raw,
        )
        created += 1

    return JsonResponse({
        'ok': True,
        'created': created,
        'rejected': rejected,
        'campaign': campaign or 'direct',
        'received_at': timezone.now().isoformat(),
    }, status=201)


@csrf_exempt
@require_http_methods(["GET"])
@require_api_key
def landing_analytics_summary(request):
    """Resumen agregado por fecha, campaña y variante."""
    campaign = str(request.GET.get('campaign') or '').strip()
    from_date = parse_date(str(request.GET.get('from') or '').strip())
    to_date = parse_date(str(request.GET.get('to') or '').strip())

    queryset = LandingAnalyticsEvent.objects.all()
    if campaign:
        queryset = queryset.filter(campaign=campaign)
    if from_date:
        queryset = queryset.filter(event_date__gte=from_date)
    if to_date:
        queryset = queryset.filter(event_date__lte=to_date)

    total_events = queryset.count()
    cta_events = queryset.filter(event_name='cta_click')

    by_variant = []
    for item in queryset.values('variant').annotate(total=Count('id')).order_by('variant'):
        variant_key = item['variant'] or 'N/A'
        total = item['total']
        cta_total = cta_events.filter(variant=item['variant']).count()
        cta_rate = round((cta_total / total) * 100, 2) if total else 0
        by_variant.append({
            'variant': variant_key,
            'events': total,
            'cta_clicks': cta_total,
            'cta_rate_percent': cta_rate,
        })

    by_day = list(
        queryset.values('event_date', 'campaign', 'variant')
        .annotate(total=Count('id'))
        .order_by('-event_date', 'campaign', 'variant')
    )

    winner = None
    sortable = [item for item in by_variant if item['variant'] in {'A', 'B'}]
    if sortable:
        winner = sorted(sortable, key=lambda row: (row['cta_rate_percent'], row['cta_clicks']), reverse=True)[0]['variant']

    return JsonResponse({
        'campaign': campaign,
        'filters': {
            'from': from_date.isoformat() if from_date else None,
            'to': to_date.isoformat() if to_date else None,
        },
        'totals': {
            'events': total_events,
            'cta_clicks': cta_events.count(),
        },
        'winner_variant': winner,
        'by_variant': by_variant,
        'by_day': by_day,
    })
