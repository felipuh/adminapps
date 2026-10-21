"""
API de Integración para Admin Apps
Endpoints que otros servicios (ISO Smart) pueden consumir
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.utils import timezone
from functools import wraps
import hashlib
import hmac

from organizations.models import Organization
from users.models import User, OrganizationMembership


# =============================================================================
# AUTENTICACIÓN POR API KEY
# =============================================================================

def get_api_key_from_request(request):
    """Extrae la API Key del header"""
    auth_header = request.headers.get('X-API-Key', '')
    return auth_header


def verify_api_key(api_key):
    """Verifica que la API Key sea válida"""
    from django.conf import settings
    
    valid_keys = getattr(settings, 'INTEGRATION_API_KEYS', {})
    
    for service_name, key_hash in valid_keys.items():
        # Comparar hash de la key proporcionada
        provided_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if hmac.compare_digest(provided_hash, key_hash):
            return service_name
    
    return None


def api_key_required(view_func):
    """Decorador que requiere API Key válida"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        api_key = get_api_key_from_request(request)
        
        if not api_key:
            return Response(
                {'error': 'API Key requerida', 'code': 'missing_api_key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        service_name = verify_api_key(api_key)
        if not service_name:
            return Response(
                {'error': 'API Key inválida', 'code': 'invalid_api_key'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Agregar nombre del servicio al request
        request.integration_service = service_name
        return view_func(request, *args, **kwargs)
    
    return wrapper


# =============================================================================
# ENDPOINTS DE INTEGRACIÓN
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
@api_key_required
def list_organizations(request):
    """
    Lista todas las organizaciones activas
    
    GET /api/integration/organizations/
    Headers: X-API-Key: <api_key>
    
    Response:
    {
        "organizations": [
            {
                "id": 1,
                "uuid": "...",
                "name": "Empresa XYZ",
                "slug": "empresa-xyz",
                "plan": "professional",
                "status": "active",
                "max_users": 10,
                "user_count": 5,
                "modules": ["SCA", "SIE", "ASB", "SPM"]
            }
        ]
    }
    """
    organizations = Organization.objects.filter(
        status__in=['active', 'trial']
    ).order_by('name')
    
    data = []
    for org in organizations:
        data.append({
            'id': org.id,
            'uuid': str(org.uuid),
            'name': org.name,
            'slug': org.slug,
            'legal_name': org.legal_name,
            'plan': org.plan,
            'status': org.status,
            'max_users': org.max_users,
            'user_count': org.user_count,
            'modules': [m['code'] for m in org.get_enabled_modules()],
            'created_at': org.created_at.isoformat(),
        })
    
    return Response({'organizations': data})


@api_view(['GET'])
@permission_classes([AllowAny])
@api_key_required
def get_organization(request, org_id):
    """
    Obtiene detalle de una organización
    
    GET /api/integration/organizations/<id>/
    Headers: X-API-Key: <api_key>
    """
    try:
        org = Organization.objects.get(pk=org_id)
    except Organization.DoesNotExist:
        return Response(
            {'error': 'Organización no encontrada', 'code': 'not_found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    data = {
        'id': org.id,
        'uuid': str(org.uuid),
        'name': org.name,
        'slug': org.slug,
        'legal_name': org.legal_name,
        'tax_id': org.tax_id,
        'email': org.email,
        'phone': org.phone,
        'website': org.website,
        'address': org.address,
        'city': org.city,
        'country': org.country,
        'logo_url': org.logo.url if org.logo else None,
        'primary_color': org.primary_color,
        'plan': org.plan,
        'status': org.status,
        'max_users': org.max_users,
        'user_count': org.user_count,
        'modules': org.get_enabled_modules(),
        'trial_ends_at': org.trial_ends_at.isoformat() if org.trial_ends_at else None,
        'subscription_ends_at': org.subscription_ends_at.isoformat() if org.subscription_ends_at else None,
        'created_at': org.created_at.isoformat(),
        'updated_at': org.updated_at.isoformat(),
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
@api_key_required
def get_organization_users(request, org_id):
    """
    Obtiene usuarios de una organización
    
    GET /api/integration/organizations/<id>/users/
    Headers: X-API-Key: <api_key>
    """
    try:
        org = Organization.objects.get(pk=org_id)
    except Organization.DoesNotExist:
        return Response(
            {'error': 'Organización no encontrada', 'code': 'not_found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    memberships = OrganizationMembership.objects.filter(
        organization=org,
        is_active=True,
        user__is_active=True
    ).select_related('user')
    
    users = []
    for membership in memberships:
        user = membership.user
        users.append({
            'id': user.id,
            'uuid': str(user.uuid),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'role': membership.role,
            'role_display': membership.get_role_display(),
            'job_title': membership.job_title,
            'department': membership.department,
            'is_primary': membership.is_primary,
            'avatar_url': user.avatar.url if user.avatar else None,
            'joined_at': membership.joined_at.isoformat(),
        })
    
    return Response({
        'organization_id': org.id,
        'organization_name': org.name,
        'users': users,
        'total': len(users)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@api_key_required
def get_organization_modules(request, org_id):
    """
    Obtiene módulos habilitados de una organización
    
    GET /api/integration/organizations/<id>/modules/
    Headers: X-API-Key: <api_key>
    """
    try:
        org = Organization.objects.get(pk=org_id)
    except Organization.DoesNotExist:
        return Response(
            {'error': 'Organización no encontrada', 'code': 'not_found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        'organization_id': org.id,
        'organization_name': org.name,
        'plan': org.plan,
        'modules': org.get_enabled_modules()
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@api_key_required
def validate_credentials(request):
    """
    Valida credenciales de usuario y retorna información si es válido
    
    POST /api/integration/validate-credentials/
    Headers: X-API-Key: <api_key>
    Body: {
        "email": "user@example.com",
        "password": "password123",
        "organization_id": 1  // opcional
    }
    
    Response (éxito):
    {
        "valid": true,
        "user": {
            "id": 1,
            "uuid": "...",
            "email": "...",
            "first_name": "...",
            "last_name": "...",
            "organizations": [...]
        }
    }
    
    Response (error):
    {
        "valid": false,
        "error": "Credenciales inválidas",
        "code": "invalid_credentials"
    }
    """
    email = request.data.get('email', '').lower().strip()
    password = request.data.get('password', '')
    organization_id = request.data.get('organization_id')
    
    if not email or not password:
        return Response({
            'valid': False,
            'error': 'Email y contraseña son requeridos',
            'code': 'missing_fields'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Autenticar usuario
    user = authenticate(email=email, password=password)
    
    if not user:
        return Response({
            'valid': False,
            'error': 'Credenciales inválidas',
            'code': 'invalid_credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({
            'valid': False,
            'error': 'Usuario desactivado',
            'code': 'user_inactive'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Obtener organizaciones del usuario
    memberships = user.memberships.filter(is_active=True).select_related('organization')
    
    organizations = []
    selected_org = None
    selected_role = None
    
    for membership in memberships:
        org = membership.organization
        if org.status not in ['active', 'trial']:
            continue
        
        org_data = {
            'id': org.id,
            'uuid': str(org.uuid),
            'name': org.name,
            'slug': org.slug,
            'role': membership.role,
            'role_display': membership.get_role_display(),
            'is_primary': membership.is_primary,
            'modules': [m['code'] for m in org.get_enabled_modules()]
        }
        organizations.append(org_data)
        
        # Determinar organización seleccionada
        if organization_id and org.id == organization_id:
            selected_org = org_data
            selected_role = membership.role
        elif membership.is_primary and not selected_org:
            selected_org = org_data
            selected_role = membership.role
    
    if not organizations:
        return Response({
            'valid': False,
            'error': 'Usuario sin organizaciones activas',
            'code': 'no_organizations'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Si no se seleccionó ninguna, usar la primera
    if not selected_org:
        selected_org = organizations[0]
        selected_role = organizations[0]['role']
    
    # Actualizar último login
    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])
    
    return Response({
        'valid': True,
        'user': {
            'id': user.id,
            'uuid': str(user.uuid),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'avatar_url': user.avatar.url if user.avatar else None,
            'is_platform_admin': user.is_platform_admin,
            'must_change_password': user.must_change_password,
        },
        'organizations': organizations,
        'current_organization': selected_org,
        'current_role': selected_role,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@api_key_required
def get_user_by_id(request):
    """
    Obtiene información de un usuario por ID
    
    POST /api/integration/user/
    Headers: X-API-Key: <api_key>
    Body: {
        "user_id": 1,
        "organization_id": 1  // opcional
    }
    """
    user_id = request.data.get('user_id')
    organization_id = request.data.get('organization_id')
    
    if not user_id:
        return Response({
            'error': 'user_id es requerido',
            'code': 'missing_user_id'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado',
            'code': 'not_found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Obtener membresía específica si se proporciona organization_id
    membership = None
    if organization_id:
        membership = user.memberships.filter(
            organization_id=organization_id,
            is_active=True
        ).first()
    
    return Response({
        'user': {
            'id': user.id,
            'uuid': str(user.uuid),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'avatar_url': user.avatar.url if user.avatar else None,
        },
        'membership': {
            'role': membership.role,
            'role_display': membership.get_role_display(),
            'job_title': membership.job_title,
            'department': membership.department,
        } if membership else None
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@api_key_required
def health_check(request):
    """
    Health check para verificar que la API está disponible
    
    GET /api/integration/health/
    Headers: X-API-Key: <api_key>
    """
    return Response({
        'status': 'healthy',
        'service': 'Admin Apps Integration API',
        'version': '1.0.0',
        'timestamp': timezone.now().isoformat(),
        'caller': request.integration_service
    })
