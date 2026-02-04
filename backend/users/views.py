"""
Views de Usuarios para Admin Apps
"""
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import authenticate
from django.utils import timezone

from .models import User, OrganizationMembership
from .serializers import UserSerializer, UserCreateSerializer, LoginSerializer


class LoginView(APIView):
    """Vista de login - genera tokens JWT"""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        organization_id = serializer.validated_data.get('organization_id')
        
        # Autenticar usuario
        user = authenticate(request, email=email, password=password)
        
        if not user:
            return Response(
                {'error': 'Credenciales inválidas', 'code': 'invalid_credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Usuario desactivado', 'code': 'user_inactive'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Obtener organizaciones del usuario
        memberships = user.memberships.filter(
            is_active=True,
            organization__status__in=['active', 'trial']
        ).select_related('organization')
        
        if not memberships.exists():
            return Response(
                {'error': 'Sin organizaciones activas', 'code': 'no_organizations'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Seleccionar organización
        current_membership = None
        if organization_id:
            current_membership = memberships.filter(organization_id=organization_id).first()
        
        if not current_membership:
            current_membership = memberships.filter(is_primary=True).first() or memberships.first()
        
        # Generar tokens
        refresh = RefreshToken.for_user(user)
        refresh['organization_id'] = current_membership.organization_id
        refresh['role'] = current_membership.role
        
        # Actualizar último login
        user.last_login_at = timezone.now()
        user.last_login_ip = self._get_client_ip(request)
        user.save(update_fields=['last_login_at', 'last_login_ip'])
        
        # Preparar respuesta
        organizations = []
        for m in memberships:
            organizations.append({
                'id': m.organization.id,
                'name': m.organization.name,
                'slug': m.organization.slug,
                'role': m.role,
                'is_primary': m.is_primary,
            })
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'organizations': organizations,
            'current_organization': {
                'id': current_membership.organization.id,
                'name': current_membership.organization.name,
                'slug': current_membership.organization.slug,
            },
            'current_role': current_membership.role,
        })
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class LogoutView(APIView):
    """Vista de logout - invalida refresh token"""
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'status': 'Sesión cerrada'})
        except Exception:
            return Response({'status': 'Sesión cerrada'})


class MeView(APIView):
    """Obtener información del usuario actual"""
    
    def get(self, request):
        user = request.user
        
        # Obtener membresía actual (del token o la primera)
        organization_id = getattr(request, 'organization_id', None)
        
        if organization_id:
            membership = user.memberships.filter(
                organization_id=organization_id,
                is_active=True
            ).first()
        else:
            membership = user.memberships.filter(is_active=True).first()
        
        data = UserSerializer(user).data
        
        if membership:
            data['current_organization'] = {
                'id': membership.organization.id,
                'name': membership.organization.name,
                'slug': membership.organization.slug,
            }
            data['current_role'] = membership.role
        
        return Response(data)


class UserListView(generics.ListCreateAPIView):
    """Listar y crear usuarios"""
    
    queryset = User.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        
        # Filtrar por organización si se especifica
        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(
                memberships__organization_id=org_id,
                memberships__is_active=True
            )
        
        return queryset.distinct().order_by('email')


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detalle, actualización y eliminación de usuario"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save()
