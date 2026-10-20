"""
Views de Autenticación para ISO Smart
"""

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db import IntegrityError
from datetime import timedelta
import logging
import secrets

from .models import PasswordResetToken, User, UserProfile, RefreshTokenBlacklist
from core.models import AuditLog, Organization
from integration.client import admin_apps_client
from integration.backends import ROLE_MAP
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshTokenSerializer,
    TokenResponseSerializer,
    UserSerializer,
    UserProfileSerializer,
    SwitchOrganizationSerializer,
    UserRegistrationSerializer,
)
from .permissions import IsOrgAdmin

logger = logging.getLogger(__name__)

PASSWORD_REUSE_REASON_CODE = 'PASSWORD_REUSE_RECENT'


def _password_history_limit():
    return max(1, int(getattr(settings, 'PASSWORD_HISTORY_COUNT', 5)))


def _is_password_reused(user, raw_password):
    if check_password(raw_password, user.password):
        return True

    for previous_hash in (user.password_history or []):
        if previous_hash and check_password(raw_password, previous_hash):
            return True
    return False


def _build_password_history(user):
    history_limit = _password_history_limit()
    history = list(user.password_history or [])
    if user.password:
        history.insert(0, user.password)

    deduped = []
    for item in history:
        if item and item not in deduped:
            deduped.append(item)

    return deduped[:history_limit]


def _request_ip_address(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _audit_password_reset(user, action, request, description, details=None):
    profile = UserProfile.objects.filter(user=user, is_active=True).select_related('organization').first()
    if not profile:
        return

    AuditLog.objects.create(
        organization=profile.organization,
        user=user,
        action='update',
        module='authentication',
        description=description,
        ip_address=_request_ip_address(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        new_values={
            'event': action,
            **(details or {}),
        },
    )


def _audit_password_reuse_rejected(user, request, flow):
    _audit_password_reset(
        user,
        'password_reuse_rejected',
        request,
        'Intento de reutilizacion de contrasena bloqueado',
        details={
            'flow': flow,
            'reason_code': PASSWORD_REUSE_REASON_CODE,
        },
    )


def _password_reset_frontend_url(selector, raw_token):
    base_url = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5173').rstrip('/')
    return f"{base_url}/reset-password?selector={selector}&token={raw_token}"


class LoginView(APIView):
    """
    Vista de Login
    POST /api/auth/login/
    
    Retorna tokens JWT y datos del usuario
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        profile = serializer.validated_data['profile']
        
        # Generar tokens
        refresh = RefreshToken.for_user(user)
        
        # Agregar claims personalizados al token
        refresh['organization_id'] = profile.organization_id
        refresh['role'] = profile.role
        refresh['profile_id'] = profile.id
        
        access = refresh.access_token
        access['organization_id'] = profile.organization_id
        access['role'] = profile.role
        access['profile_id'] = profile.id
        
        # Actualizar último login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Obtener todas las organizaciones del usuario
        all_profiles = UserProfile.objects.filter(
            user=user, is_active=True
        ).select_related('organization')
        
        organizations = [
            {
                'id': p.organization.id,
                'name': p.organization.name,
                'role': p.role,
                'role_display': p.get_role_display(),
                'is_current': p.id == profile.id
            }
            for p in all_profiles
        ]
        
        response_data = {
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data,
            'organizations': organizations,
        }
        if serializer.validated_data.get('temp_password_warning'):
            response_data['security_alert'] = serializer.validated_data['temp_password_warning']
        
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Vista de Logout
    POST /api/auth/logout/
    
    Invalida el refresh token
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            refresh_token_str = serializer.validated_data['refresh']
            RefreshToken(refresh_token_str)

            token_hash = RefreshTokenBlacklist.hash_token(refresh_token_str)
            RefreshTokenBlacklist.objects.get_or_create(
                token_hash=token_hash,
                defaults={
                    'token': refresh_token_str,
                    'user': request.user,
                }
            )
            
        except TokenError:
            pass  # Token ya expirado o inválido, ignorar
        
        return Response(
            {'detail': 'Sesión cerrada exitosamente.'},
            status=status.HTTP_200_OK
        )


class RefreshTokenView(APIView):
    """
    Vista para refrescar tokens
    POST /api/auth/refresh/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
            
            # Verificar que no esté en lista negra
            refresh_token_str = str(refresh)
            if RefreshTokenBlacklist.objects.filter(token_hash=RefreshTokenBlacklist.hash_token(refresh_token_str)).exists():
                return Response(
                    {'detail': 'Token inválido o expirado.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generar nuevo access token
            access = refresh.access_token
            
            response_data = {
                'access': str(access),
            }
            
            # Rotar refresh token si está configurado
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                refresh.set_jti()
                refresh.set_exp()
                response_data['refresh'] = str(refresh)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response(
                {'detail': 'Token inválido o expirado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class MeView(APIView):
    """
    Vista para obtener datos del usuario actual
    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Obtener perfil activo (del token o primario)
        organization_id = getattr(request, 'organization_id', None)
        
        if organization_id:
            profile = UserProfile.objects.filter(
                user=user,
                organization_id=organization_id,
                is_active=True
            ).select_related('organization').first()
        else:
            profile = UserProfile.objects.filter(
                user=user,
                is_active=True
            ).order_by('-is_primary').select_related('organization').first()
        
        # Obtener todas las organizaciones
        all_profiles = UserProfile.objects.filter(
            user=user, is_active=True
        ).select_related('organization')
        
        organizations = [
            {
                'id': p.organization.id,
                'name': p.organization.name,
                'role': p.role,
                'role_display': p.get_role_display(),
                'is_current': profile and p.id == profile.id
            }
            for p in all_profiles
        ]
        
        response_data = {
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data if profile else None,
            'organizations': organizations,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class SwitchOrganizationView(APIView):
    """
    Vista para cambiar de organización activa
    POST /api/auth/switch-organization/
    
    Retorna nuevos tokens con la organización seleccionada
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SwitchOrganizationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        organization_id = serializer.validated_data['organization_id']
        user = request.user
        
        profile = UserProfile.objects.filter(
            user=user,
            organization_id=organization_id,
            is_active=True
        ).select_related('organization').first()
        
        # Generar nuevos tokens
        refresh = RefreshToken.for_user(user)
        refresh['organization_id'] = profile.organization_id
        refresh['role'] = profile.role
        refresh['profile_id'] = profile.id
        
        access = refresh.access_token
        access['organization_id'] = profile.organization_id
        access['role'] = profile.role
        access['profile_id'] = profile.id
        
        # Obtener todas las organizaciones
        all_profiles = UserProfile.objects.filter(
            user=user, is_active=True
        ).select_related('organization')
        
        organizations = [
            {
                'id': p.organization.id,
                'name': p.organization.name,
                'role': p.role,
                'role_display': p.get_role_display(),
                'is_current': p.id == profile.id
            }
            for p in all_profiles
        ]
        
        response_data = {
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data,
            'organizations': organizations,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    Vista para cambiar contraseña
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        new_password = serializer.validated_data['new_password']

        if _is_password_reused(user, new_password):
            _audit_password_reuse_rejected(user, request, flow='change_password')
            return Response(
                {
                    'detail': 'No puedes reutilizar una contraseña reciente. Elige una nueva.',
                    'reason_code': PASSWORD_REUSE_REASON_CODE,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.password_history = _build_password_history(user)
        user.set_password(serializer.validated_data['new_password'])
        user.clear_temporary_password_flag()
        user.save(update_fields=['password', 'must_change_password', 'password_history', 'temporary_password_set_at'])
        
        return Response(
            {'detail': 'Contraseña actualizada exitosamente.'},
            status=status.HTTP_200_OK
        )


class PasswordResetRequestView(APIView):
    """Solicita recuperacion de contrasena sin revelar existencia del email."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].strip().lower()
        ip_address = _request_ip_address(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        now = timezone.now()
        debug_recovery_mode = settings.DEBUG and (
            request.META.get('HTTP_X_DEBUG_RECOVERY') == '1'
            or request.query_params.get('debug_recovery') == '1'
        )
        window_minutes = getattr(settings, 'PASSWORD_RESET_WINDOW_MINUTES', 60)
        max_requests = getattr(settings, 'PASSWORD_RESET_MAX_REQUESTS_PER_HOUR', 5)
        window_start = now - timedelta(minutes=window_minutes)
        user = None
        reset_url = None

        email_count = PasswordResetToken.objects.filter(email=email, requested_at__gte=window_start).count()
        ip_count = PasswordResetToken.objects.filter(ip_address=ip_address, requested_at__gte=window_start).count() if ip_address else 0

        if debug_recovery_mode or (email_count < max_requests and ip_count < max_requests):
            user = User.objects.filter(email=email, is_active=True).first()
            if user:
                expiry_minutes = getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY_MINUTES', 30)
                reset_token, raw_token = PasswordResetToken.issue_for_user(
                    user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expiry_minutes=expiry_minutes,
                )
                reset_url = _password_reset_frontend_url(reset_token.selector, raw_token)
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@isosmart.local')
                subject = 'ISO Smart - Recuperación de contraseña'
                context = {
                    'user': user,
                    'reset_url': reset_url,
                    'expiry_minutes': expiry_minutes,
                }
                if debug_recovery_mode:
                    _audit_password_reset(user, 'password_reset_request', request, 'Solicitud de recuperacion de contrasena enviada')
                else:
                    message = render_to_string('authentication/emails/password_reset_email.txt', context)
                    html_message = render_to_string('authentication/emails/password_reset_email.html', context)
                    try:
                        email_message = EmailMultiAlternatives(subject, message, from_email, [user.email])
                        email_message.attach_alternative(html_message, 'text/html')
                        email_message.send(fail_silently=False)
                        _audit_password_reset(user, 'password_reset_request', request, 'Solicitud de recuperacion de contrasena enviada')
                    except Exception:
                        logger.exception('Fallo enviando correo de recuperacion para %s', user.email)
                        reset_token.mark_used()
            else:
                PasswordResetToken.objects.create(
                    user=None,
                    email=email,
                    selector=secrets.token_hex(8),
                    token_hash=PasswordResetToken.hash_token(secrets.token_urlsafe(32)),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expires_at=now,
                    used_at=now,
                )

        response_payload = {
            'detail': 'Si el correo existe, recibirás instrucciones para restablecer tu contraseña.'
        }
        if settings.DEBUG and user and reset_url:
            response_payload['debug_reset_url'] = reset_url

        return Response(response_payload, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Confirma una nueva contrasena a partir de un token de recuperacion."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_token = serializer.validated_data['reset_token']
        user = reset_token.user
        new_password = serializer.validated_data['new_password']

        if _is_password_reused(user, new_password):
            _audit_password_reuse_rejected(user, request, flow='password_reset_confirm')
            return Response(
                {
                    'detail': 'No puedes reutilizar una contraseña reciente. Elige una nueva.',
                    'reason_code': PASSWORD_REUSE_REASON_CODE,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.password_history = _build_password_history(user)
        user.set_password(serializer.validated_data['new_password'])
        user.clear_temporary_password_flag()
        user.save(update_fields=['password', 'password_history', 'must_change_password', 'temporary_password_set_at'])

        reset_token.mark_used()
        PasswordResetToken.objects.filter(
            user=user,
            used_at__isnull=True,
        ).exclude(id=reset_token.id).update(used_at=timezone.now())
        _audit_password_reset(user, 'password_reset_confirm', request, 'Contrasena restablecida mediante recovery')

        return Response(
            {'detail': 'Contraseña restablecida exitosamente.'},
            status=status.HTTP_200_OK,
        )


class UserListView(generics.ListCreateAPIView):
    """
    Vista para listar y crear usuarios de la organización
    GET/POST /api/auth/users/
    
    Solo para org_admin
    """
    permission_classes = [IsAuthenticated, IsOrgAdmin]
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        organization_id = getattr(self.request, 'organization_id', None)
        if organization_id:
            self._sync_adminapps_users(organization_id)
            return UserProfile.objects.filter(
                organization_id=organization_id
            ).select_related('user', 'organization')
        return UserProfile.objects.none()

    def _sync_adminapps_users(self, organization_id):
        if not settings.ADMIN_APPS_INTEGRATION.get('SYNC_USERS', True):
            return

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return

        if not organization.external_id:
            return

        result = admin_apps_client.get_organization_users(
            organization.external_id,
            use_cache=False
        )

        if 'error' in result:
            logger.warning(
                "Error sincronizando usuarios desde Admin Apps: %s",
                result.get('error')
            )
            return

        users = result.get('users', [])
        for user_data in users:
            user, created = User.objects.update_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'is_active': user_data.get('is_active', True),
                }
            )

            if created:
                user.set_unusable_password()
                user.save()

            mapped_role = ROLE_MAP.get(user_data.get('role', 'user'), 'user')
            profile_defaults = {
                'role': mapped_role,
                'job_title': user_data.get('job_title', ''),
                'department': user_data.get('department', ''),
                'is_active': user_data.get('is_active', True),
            }

            try:
                UserProfile.objects.update_or_create(
                    user=user,
                    organization=organization,
                    defaults=profile_defaults,
                )
            except IntegrityError:
                # Legacy databases can still enforce unique(user_id) in user_profiles.
                # Fallback to updating the existing row by user to avoid failing the list endpoint.
                existing_profile = UserProfile.objects.filter(user=user).first()
                if existing_profile is None:
                    raise

                existing_profile.organization = organization
                for field, value in profile_defaults.items():
                    setattr(existing_profile, field, value)
                existing_profile.save(update_fields=['organization', *profile_defaults.keys()])

                logger.warning(
                    'Resolved legacy unique user profile conflict during Admin Apps sync for user=%s organization=%s',
                    user.email,
                    organization.id,
                )
    
    def create(self, request, *args, **kwargs):
        # Usar serializer de registro
        data = request.data.copy()
        data['organization_id'] = getattr(request, 'organization_id', None)
        
        serializer = UserRegistrationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Obtener el perfil creado
        profile = UserProfile.objects.get(user=user)
        
        return Response(
            UserProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para ver/editar/eliminar usuario de la organización
    GET/PUT/PATCH/DELETE /api/auth/users/<id>/
    
    Solo para org_admin
    """
    permission_classes = [IsAuthenticated, IsOrgAdmin]
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        organization_id = getattr(self.request, 'organization_id', None)
        if organization_id:
            return UserProfile.objects.filter(
                organization_id=organization_id
            ).select_related('user', 'organization')
        return UserProfile.objects.none()
    
    def perform_destroy(self, instance):
        # No eliminar el usuario, solo desactivar el perfil
        instance.is_active = False
        instance.save()
