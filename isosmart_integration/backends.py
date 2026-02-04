"""
Backend de Autenticación para ISO Smart
Valida credenciales contra Admin Apps
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .client import admin_apps_client
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AdminAppsAuthBackend(BaseBackend):
    """
    Backend de autenticación que valida credenciales contra Admin Apps
    
    Flujo:
    1. Usuario intenta login en ISO Smart
    2. ISO Smart envía credenciales a Admin Apps
    3. Admin Apps valida y retorna información del usuario
    4. ISO Smart crea/actualiza usuario local con los datos
    5. Usuario queda autenticado en ISO Smart
    
    Configuración en settings.py:
    
    AUTHENTICATION_BACKENDS = [
        'integration.backends.AdminAppsAuthBackend',
        'django.contrib.auth.backends.ModelBackend',  # Fallback local
    ]
    
    ADMIN_APPS_INTEGRATION = {
        'BASE_URL': 'http://adminapps.isosmart.local/api/integration',
        'API_KEY': 'your-secret-api-key',
        'SYNC_USERS': True,  # Crear/actualizar usuarios locales
    }
    """
    
    def authenticate(self, request, email=None, password=None, organization_id=None, **kwargs):
        """
        Autentica un usuario contra Admin Apps
        
        Args:
            email: Email del usuario
            password: Contraseña
            organization_id: ID de organización (opcional)
        
        Returns:
            User object si es válido, None si no
        """
        if not email or not password:
            return None
        
        # Llamar a Admin Apps para validar credenciales
        result = admin_apps_client.validate_credentials(
            email=email,
            password=password,
            organization_id=organization_id
        )
        
        # Verificar resultado
        if not result.get('valid'):
            logger.info(f"Autenticación fallida para {email}: {result.get('error', 'Unknown')}")
            return None
        
        user_data = result.get('user', {})
        org_data = result.get('current_organization', {})
        role = result.get('current_role', 'user')
        
        # Obtener o crear usuario local
        from django.conf import settings
        sync_users = getattr(settings, 'ADMIN_APPS_INTEGRATION', {}).get('SYNC_USERS', True)
        
        if sync_users:
            user = self._sync_user(user_data, org_data, role)
        else:
            # Solo obtener usuario existente
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warning(f"Usuario {email} no existe localmente y SYNC_USERS=False")
                return None
        
        # Guardar datos adicionales en el request para uso posterior
        if request:
            request.admin_apps_data = {
                'user': user_data,
                'organization': org_data,
                'role': role,
                'organizations': result.get('organizations', [])
            }
        
        return user
    
    def _sync_user(self, user_data, org_data, role):
        """
        Sincroniza usuario con datos de Admin Apps
        Crea si no existe, actualiza si existe
        """
        from core.models import Organization
        from authentication.models import UserProfile
        
        email = user_data.get('email')
        
        # Crear o actualizar usuario
        user, created = User.objects.update_or_create(
            email=email,
            defaults={
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'is_active': True,
            }
        )
        
        if created:
            # Nuevo usuario - establecer contraseña inutilizable
            # (la autenticación siempre va por Admin Apps)
            user.set_unusable_password()
            user.save()
            logger.info(f"Usuario {email} creado desde Admin Apps")
        
        # Sincronizar organización si existe
        if org_data:
            org_id = org_data.get('id')
            try:
                organization = Organization.objects.get(pk=org_id)
                
                # Crear o actualizar perfil
                UserProfile.objects.update_or_create(
                    user=user,
                    organization=organization,
                    defaults={
                        'role': role,
                        'is_active': True,
                    }
                )
            except Organization.DoesNotExist:
                logger.warning(f"Organización {org_id} no existe en ISO Smart")
        
        return user
    
    def get_user(self, user_id):
        """Obtiene usuario por ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class AdminAppsTokenBackend:
    """
    Utilidad para validar tokens JWT contra Admin Apps
    (Para uso con SimpleJWT si se necesita validación remota)
    """
    
    @staticmethod
    def validate_user(user_id, organization_id=None):
        """
        Valida que un usuario siga activo en Admin Apps
        Útil para verificaciones periódicas de tokens
        """
        result = admin_apps_client.get_user(user_id, organization_id)
        
        if 'error' in result:
            return False, result.get('error')
        
        return True, result.get('user')
