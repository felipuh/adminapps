"""
Middleware de Integración para ISO Smart
Verifica acceso a módulos según configuración en Admin Apps
"""
from django.http import JsonResponse
from django.conf import settings
from .client import admin_apps_client
import re
import logging

logger = logging.getLogger(__name__)


class ModuleAccessMiddleware:
    """
    Middleware que verifica si el módulo solicitado está habilitado
    para la organización del usuario
    
    Configuración en settings.py:
    
    MIDDLEWARE = [
        ...
        'integration.middleware.ModuleAccessMiddleware',
    ]
    
    MODULE_URL_PATTERNS = {
        'SCA': [r'^/api/sca/', r'^/api/context/'],
        'SIE': [r'^/api/sie/', r'^/api/stakeholders/'],
        'ASB': [r'^/api/scope/', r'^/api/asb/'],
        'SPM': [r'^/api/processes/', r'^/api/spm/'],
        'DOC': [r'^/api/documents/'],
        'RISK': [r'^/api/risks/'],
        'OBJ': [r'^/api/objectives/'],
        'AUDIT': [r'^/api/audits/'],
    }
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.module_patterns = getattr(settings, 'MODULE_URL_PATTERNS', {
            'SCA': [r'^/api/sca/', r'^/api/context/'],
            'SIE': [r'^/api/sie/', r'^/api/stakeholders/'],
            'ASB': [r'^/api/scope/'],
            'SPM': [r'^/api/processes/'],
            'DOC': [r'^/api/documents/'],
            'RISK': [r'^/api/risks/'],
            'OBJ': [r'^/api/objectives/'],
            'AUDIT': [r'^/api/audits/'],
        })
        
        # Compilar patrones
        self.compiled_patterns = {}
        for module, patterns in self.module_patterns.items():
            self.compiled_patterns[module] = [re.compile(p) for p in patterns]
    
    def __call__(self, request):
        # Verificar solo rutas de API
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Ignorar rutas públicas
        public_paths = ['/api/auth/', '/api/health/', '/api/public/']
        if any(request.path.startswith(p) for p in public_paths):
            return self.get_response(request)
        
        # Verificar si el usuario está autenticado
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)
        
        # Obtener organización del usuario
        organization_id = getattr(request, 'organization_id', None)
        if not organization_id:
            # Intentar obtener de la sesión o token
            organization_id = request.session.get('organization_id')
        
        if not organization_id:
            return self.get_response(request)
        
        # Determinar qué módulo se está accediendo
        module_code = self._get_module_for_path(request.path)
        if not module_code:
            return self.get_response(request)
        
        # Verificar si el módulo está habilitado
        if not self._is_module_enabled(organization_id, module_code):
            logger.warning(
                f"Acceso denegado a módulo {module_code} para organización {organization_id}"
            )
            return JsonResponse({
                'error': f'Módulo {module_code} no habilitado para su organización',
                'code': 'module_disabled'
            }, status=403)
        
        return self.get_response(request)
    
    def _get_module_for_path(self, path):
        """Determina qué módulo corresponde a la ruta"""
        for module, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.match(path):
                    return module
        return None
    
    def _is_module_enabled(self, organization_id, module_code):
        """Verifica si un módulo está habilitado (con caché)"""
        return admin_apps_client.is_module_enabled(organization_id, module_code)


class AdminAppsSyncMiddleware:
    """
    Middleware que mantiene sincronizada la información del usuario
    con Admin Apps
    
    Actualiza datos del usuario/organización periódicamente
    """
    
    SYNC_INTERVAL = 300  # 5 minutos
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Solo para usuarios autenticados
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._maybe_sync_user(request)
        
        return self.get_response(request)
    
    def _maybe_sync_user(self, request):
        """Sincroniza usuario si ha pasado el intervalo"""
        from django.core.cache import cache
        from django.utils import timezone
        
        cache_key = f'user_sync:{request.user.id}'
        last_sync = cache.get(cache_key)
        
        if last_sync is None:
            # Nunca sincronizado o caché expirada
            self._sync_user(request)
            cache.set(cache_key, timezone.now().isoformat(), self.SYNC_INTERVAL)
    
    def _sync_user(self, request):
        """Sincroniza datos del usuario desde Admin Apps"""
        organization_id = getattr(request, 'organization_id', None)
        
        result = admin_apps_client.get_user(
            request.user.id,
            organization_id=organization_id
        )
        
        if 'error' not in result:
            # Actualizar datos locales si es necesario
            user_data = result.get('user', {})
            if user_data:
                request.user.first_name = user_data.get('first_name', request.user.first_name)
                request.user.last_name = user_data.get('last_name', request.user.last_name)
                request.user.save(update_fields=['first_name', 'last_name'])
