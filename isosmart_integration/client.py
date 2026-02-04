"""
Cliente de Integración con Admin Apps para ISO Smart
Permite a ISO Smart comunicarse con Admin Apps para:
- Validar usuarios
- Obtener organizaciones
- Verificar módulos activos
"""
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class AdminAppsClient:
    """
    Cliente para comunicación con Admin Apps
    
    Configuración en settings.py:
    
    ADMIN_APPS_INTEGRATION = {
        'BASE_URL': 'http://localhost:8000/api/integration',
        'API_KEY': 'your-secret-api-key',
        'TIMEOUT': 10,
        'CACHE_TTL': 300,  # 5 minutos
    }
    """
    
    def __init__(self):
        config = getattr(settings, 'ADMIN_APPS_INTEGRATION', {})
        self.base_url = config.get('BASE_URL', 'http://localhost:8000/api/integration')
        self.api_key = config.get('API_KEY', '')
        self.timeout = config.get('TIMEOUT', 10)
        self.cache_ttl = config.get('CACHE_TTL', 300)
    
    def _get_headers(self):
        """Headers para las peticiones"""
        return {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
        }
    
    def _make_request(self, method, endpoint, data=None, use_cache=False, cache_key=None):
        """Realiza una petición a Admin Apps"""
        url = f"{self.base_url}{endpoint}"
        
        # Verificar caché si aplica
        if use_cache and cache_key:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
        
        try:
            if method == 'GET':
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
            else:
                response = requests.post(
                    url,
                    json=data,
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Guardar en caché si aplica
            if use_cache and cache_key:
                cache.set(cache_key, result, self.cache_ttl)
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout conectando a Admin Apps: {url}")
            return {'error': 'Timeout', 'code': 'timeout'}
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión a Admin Apps: {url}")
            return {'error': 'No se puede conectar a Admin Apps', 'code': 'connection_error'}
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP de Admin Apps: {e}")
            try:
                return response.json()
            except:
                return {'error': str(e), 'code': 'http_error'}
        
        except Exception as e:
            logger.exception(f"Error inesperado con Admin Apps: {e}")
            return {'error': str(e), 'code': 'unknown_error'}
    
    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================
    
    def health_check(self):
        """Verifica que Admin Apps esté disponible"""
        return self._make_request('GET', '/health/')
    
    def get_organizations(self, use_cache=True):
        """Obtiene lista de organizaciones activas"""
        cache_key = 'adminapps:organizations' if use_cache else None
        return self._make_request(
            'GET',
            '/organizations/',
            use_cache=use_cache,
            cache_key=cache_key
        )
    
    def get_organization(self, org_id, use_cache=True):
        """Obtiene detalle de una organización"""
        cache_key = f'adminapps:organization:{org_id}' if use_cache else None
        return self._make_request(
            'GET',
            f'/organizations/{org_id}/',
            use_cache=use_cache,
            cache_key=cache_key
        )
    
    def get_organization_users(self, org_id, use_cache=True):
        """Obtiene usuarios de una organización"""
        cache_key = f'adminapps:organization:{org_id}:users' if use_cache else None
        return self._make_request(
            'GET',
            f'/organizations/{org_id}/users/',
            use_cache=use_cache,
            cache_key=cache_key
        )
    
    def get_organization_modules(self, org_id, use_cache=True):
        """Obtiene módulos habilitados de una organización"""
        cache_key = f'adminapps:organization:{org_id}:modules' if use_cache else None
        return self._make_request(
            'GET',
            f'/organizations/{org_id}/modules/',
            use_cache=use_cache,
            cache_key=cache_key
        )
    
    def validate_credentials(self, email, password, organization_id=None):
        """
        Valida credenciales de un usuario
        
        Returns:
        {
            'valid': True/False,
            'user': {...},
            'organizations': [...],
            'current_organization': {...},
            'current_role': '...'
        }
        """
        data = {
            'email': email,
            'password': password,
        }
        if organization_id:
            data['organization_id'] = organization_id
        
        return self._make_request('POST', '/validate-credentials/', data=data)
    
    def get_user(self, user_id, organization_id=None):
        """Obtiene información de un usuario por ID"""
        data = {'user_id': user_id}
        if organization_id:
            data['organization_id'] = organization_id
        
        return self._make_request('POST', '/user/', data=data)
    
    def is_module_enabled(self, org_id, module_code):
        """Verifica si un módulo está habilitado para una organización"""
        result = self.get_organization_modules(org_id)
        
        if 'error' in result:
            return False
        
        modules = result.get('modules', [])
        return any(m['code'] == module_code for m in modules)
    
    def clear_cache(self, org_id=None):
        """Limpia la caché de integración"""
        if org_id:
            cache.delete(f'adminapps:organization:{org_id}')
            cache.delete(f'adminapps:organization:{org_id}:users')
            cache.delete(f'adminapps:organization:{org_id}:modules')
        else:
            # Limpiar toda la caché de adminapps (requiere patrón de eliminación)
            cache.delete('adminapps:organizations')


# Instancia singleton del cliente
admin_apps_client = AdminAppsClient()
