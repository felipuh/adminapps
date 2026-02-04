# =============================================================================
# CONFIGURACIÓN DE INTEGRACIÓN CON ADMIN APPS
# Agregar a settings.py de ISO Smart
# =============================================================================

# -----------------------------------------------------------------------------
# 1. AGREGAR A INSTALLED_APPS
# -----------------------------------------------------------------------------
# INSTALLED_APPS += ['integration']

# -----------------------------------------------------------------------------
# 2. AGREGAR A MIDDLEWARE (después de AuthenticationMiddleware)
# -----------------------------------------------------------------------------
# 'integration.middleware.ModuleAccessMiddleware',

# -----------------------------------------------------------------------------
# 3. AGREGAR A AUTHENTICATION_BACKENDS
# -----------------------------------------------------------------------------
# AUTHENTICATION_BACKENDS = [
#     'integration.backends.AdminAppsAuthBackend',  # Primero intenta Admin Apps
#     'authentication.backends.EmailBackend',        # Luego backend local
#     'django.contrib.auth.backends.ModelBackend',   # Fallback estándar
# ]

# -----------------------------------------------------------------------------
# 4. CONFIGURACIÓN DE CONEXIÓN A ADMIN APPS
# -----------------------------------------------------------------------------
ADMIN_APPS_INTEGRATION = {
    # URL base de la API de integración de Admin Apps
    'BASE_URL': 'http://adminapps.isosmart.local/api/integration',
    
    # API Key para autenticarse con Admin Apps
    # IMPORTANTE: Cambiar en producción y usar variable de entorno
    'API_KEY': 'isosmart-integration-key-2025',
    
    # Timeout para peticiones (segundos)
    'TIMEOUT': 10,
    
    # Tiempo de caché para datos (segundos)
    'CACHE_TTL': 300,  # 5 minutos
    
    # Sincronizar usuarios localmente cuando se autentican
    'SYNC_USERS': True,
    
    # Verificar módulos en cada petición
    'CHECK_MODULES': True,
}

# -----------------------------------------------------------------------------
# 5. PATRONES DE URL PARA VERIFICACIÓN DE MÓDULOS
# -----------------------------------------------------------------------------
MODULE_URL_PATTERNS = {
    'SCA': [r'^/api/sca/', r'^/api/context/'],
    'SIE': [r'^/api/sie/', r'^/api/stakeholders/'],
    'ASB': [r'^/api/scope/'],
    'SPM': [r'^/api/processes/'],
    'DOC': [r'^/api/documents/'],
    'RISK': [r'^/api/risks/'],
    'OBJ': [r'^/api/objectives/'],
    'AUDIT': [r'^/api/audits/'],
}

# -----------------------------------------------------------------------------
# 6. CONFIGURACIÓN DE CACHÉ (si no está configurado)
# -----------------------------------------------------------------------------
# Para que funcione el caché de la integración:
#
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-snowflake',
#     }
# }
#
# O para producción con Redis:
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }
