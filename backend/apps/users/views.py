"""
Views for Users - Admin Apps
"""
from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import User, UserOrganization, UserSession, UserActivityLog
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    ResetPasswordConfirmSerializer,
    UserOrganizationSerializer,
    UserSessionSerializer,
    UserActivityLogSerializer,
    RegisterSerializer,
)
from .permissions import IsSuperAdmin, IsAdmin, IsOrgAdmin, IsOwnerOrAdmin


PASSWORD_REUSE_REASON_CODE = 'PASSWORD_REUSE_RECENT'


def _password_history_limit():
    return max(1, int(getattr(settings, 'PASSWORD_HISTORY_COUNT', 5)))


def _password_history_from_metadata(user):
    metadata = user.metadata or {}
    history = metadata.get('password_history') or []
    return list(history)


def _is_password_reused(user, raw_password):
    if check_password(raw_password, user.password):
        return True

    for previous_hash in _password_history_from_metadata(user):
        if previous_hash and check_password(raw_password, previous_hash):
            return True
    return False


def _append_password_history_to_metadata(user):
    metadata = dict(user.metadata or {})
    history = _password_history_from_metadata(user)
    if user.password:
        history.insert(0, user.password)

    deduped = []
    for item in history:
        if item and item not in deduped:
            deduped.append(item)

    metadata['password_history'] = deduped[:_password_history_limit()]
    user.metadata = metadata


def _log_password_reuse_rejected(user, request, flow):
    UserActivityLog.objects.create(
        user=user,
        organization=user.organization,
        action='password_change',
        module='users',
        entity_type='User',
        entity_id=str(user.id),
        description='Intento bloqueado por reutilizacion de contrasena',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        new_values={
            'event': 'password_reuse_rejected',
            'flow': flow,
            'reason_code': PASSWORD_REUSE_REASON_CODE,
        },
    )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener tokens JWT"""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(APIView):
    """Vista para registro de usuarios"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generar tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """Vista para cerrar sesión"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Registrar logout
            UserActivityLog.objects.create(
                user=request.user,
                organization=request.user.organization,
                action='logout',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({'detail': 'Sesión cerrada exitosamente'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'organization']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['email', 'created_at', 'last_login_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'activate', 'deactivate', 'reset_password']:
            return [IsOrgAdmin()]
        elif self.action in ['destroy', 'unlock']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()
        
        # Filtrar por organización si no es admin global
        if not user.is_admin:
            queryset = queryset.filter(organization=user.organization)
        
        return queryset.select_related('organization')
    
    def perform_destroy(self, instance):
        # No permitir auto-eliminación
        if instance == self.request.user:
            raise serializers.ValidationError('No puedes eliminarte a ti mismo')
        instance.delete()
    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Obtener o actualizar perfil del usuario actual"""
        user = request.user
        
        if request.method == 'PATCH':
            serializer = UserProfileSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            # Registrar actividad
            UserActivityLog.objects.create(
                user=user,
                organization=user.organization,
                action='profile_update',
                module='users',
                entity_type='User',
                entity_id=str(user.id),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Cambiar contraseña del usuario actual"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        new_password = serializer.validated_data['new_password']

        if _is_password_reused(user, new_password):
            _log_password_reuse_rejected(user, request, flow='change_password')
            return Response(
                {
                    'detail': 'No puedes reutilizar una contraseña reciente. Elige una nueva.',
                    'reason_code': PASSWORD_REUSE_REASON_CODE,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        _append_password_history_to_metadata(user)
        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.clear_temporary_password()
        user.save()
        
        # Registrar actividad
        UserActivityLog.objects.create(
            user=user,
            organization=user.organization,
            action='password_change',
            module='users',
            entity_type='User',
            entity_id=str(user.id),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'detail': 'Contraseña actualizada exitosamente'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsOrgAdmin])
    def activate(self, request, pk=None):
        """Activar usuario"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'detail': 'Usuario activado'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsOrgAdmin])
    def deactivate(self, request, pk=None):
        """Desactivar usuario"""
        user = self.get_object()
        if user == request.user:
            return Response(
                {'error': 'No puedes desactivarte a ti mismo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.is_active = False
        user.save()
        return Response({'detail': 'Usuario desactivado'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def unlock(self, request, pk=None):
        """Desbloquear cuenta de usuario"""
        user = self.get_object()
        user.unlock_account()
        return Response({'detail': 'Cuenta desbloqueada'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsOrgAdmin])
    def reset_password(self, request, pk=None):
        """Resetear contraseña de usuario (admin)"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {'error': 'Se requiere new_password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user)
        except ValidationError as exc:
            return Response({'error': exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)

        if _is_password_reused(user, new_password):
            _log_password_reuse_rejected(user, request, flow='admin_reset_password')
            return Response(
                {
                    'error': 'No puedes reutilizar una contraseña reciente. Elige una nueva.',
                    'reason_code': PASSWORD_REUSE_REASON_CODE,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        _append_password_history_to_metadata(user)
        user.set_password(new_password)
        user.mark_temporary_password()
        user.save()
        
        return Response({'detail': 'Contraseña reseteada. El usuario debe cambiarla en su próximo inicio de sesión.'})
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """Listar sesiones activas del usuario"""
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at')
        
        serializer = UserSessionSerializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def revoke_sessions(self, request):
        """Revocar todas las sesiones excepto la actual"""
        current_token = request.data.get('current_token_jti')
        
        UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(token_jti=current_token).update(is_active=False)
        
        return Response({'detail': 'Otras sesiones revocadas'})
    
    @action(detail=False, methods=['get'])
    def activity(self, request):
        """Obtener log de actividad del usuario"""
        logs = UserActivityLog.objects.filter(
            user=request.user
        ).order_by('-created_at')[:50]
        
        serializer = UserActivityLogSerializer(logs, many=True)
        return Response(serializer.data)


class UserOrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de membresías de usuarios en organizaciones
    """
    queryset = UserOrganization.objects.all()
    serializer_class = UserOrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrgAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'organization', 'role', 'is_active']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return UserOrganization.objects.all()
        return UserOrganization.objects.filter(organization=user.organization)


class UserActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar logs de actividad (solo lectura)
    """
    queryset = UserActivityLog.objects.all()
    serializer_class = UserActivityLogSerializer
    permission_classes = [IsAuthenticated, IsOrgAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'organization', 'action', 'module']
    search_fields = ['description', 'entity_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return UserActivityLog.objects.all()
        return UserActivityLog.objects.filter(organization=user.organization)


class PasswordResetRequestView(APIView):
    """Vista para solicitar reset de contraseña"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            # TODO: Generar token y enviar email
            # Por ahora solo confirmamos que el email existe
        except User.DoesNotExist:
            pass  # No revelar si el email existe o no
        
        return Response({
            'detail': 'Si el email existe, recibirás instrucciones para resetear tu contraseña.'
        })


class PasswordResetConfirmView(APIView):
    """Vista para confirmar reset de contraseña"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # TODO: Verificar token y actualizar contraseña
        
        return Response({'detail': 'Contraseña actualizada exitosamente'})
