"""
Vistas de Integración para Admin Apps
Proporciona endpoints para que servicios externos (como ISO Smart) 
puedan consultar información de Admin Apps
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, get_user_model
from functools import wraps
import json

from apps.organizations.models import Organization
from apps.users.models import UserOrganization
from .models import IntegrationAPIKey

User = get_user_model()

MODULE_CODE_MAP = {
    'sca': {'code': 'SCA', 'name': 'SCA'},
    'sie': {'code': 'SIE', 'name': 'SIE'},
    'asb': {'code': 'ASB', 'name': 'ASB'},
    'spm': {'code': 'SPM', 'name': 'SPM'},
    'documents': {'code': 'DOC', 'name': 'Documentos'},
    'risks': {'code': 'RISK', 'name': 'Riesgos'},
    'objectives': {'code': 'OBJ', 'name': 'Objetivos'},
}


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
        
        # Verificar si la API key es válida
        try:
            key_obj = IntegrationAPIKey.objects.get(key=api_key, is_active=True)
        except IntegrationAPIKey.DoesNotExist:
            return JsonResponse({
                'error': 'API Key inválida',
                'code': 'invalid_api_key'
            }, status=401)
        
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
    
    modules = []
    subscription = org.subscription
    if subscription and subscription.is_active:
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
        'organization_id': org.id,
        'organization_name': org.name,
        'modules': unique_modules
    }
    
    return JsonResponse(data)


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
