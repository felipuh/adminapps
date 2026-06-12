"""
Django settings for Admin Apps
Sistema de Gestión de Organizaciones y Usuarios para ISO Smart
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _env_list(name, default=''):
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(',') if item.strip()]


ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development').strip().lower()
IS_PRODUCTION = ENVIRONMENT in ('production', 'prod')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-this-dev-secret-key-before-deploy')
SMART3AI_SSO_JWT_SECRET = os.environ.get('SMART3AI_SSO_JWT_SECRET', SECRET_KEY)
SMART3AI_SSO_ISSUER = os.environ.get('SMART3AI_SSO_ISSUER', 'https://sso.smart3ai.local')
SMART3AI_SSO_ALLOW_2FA_BYPASS = _env_bool('SMART3AI_SSO_ALLOW_2FA_BYPASS', default=False)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool('DEBUG', default=True)

ALLOWED_HOSTS = _env_list(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,192.168.100.100,adminapps.isosmart.local'
)

# Ensure Smart3AI reverse-proxy hosts are accepted even when env ALLOWED_HOSTS is stale.
for required_host in (
    'sso.smart3ai.local',
    'adminapps.smart3ai.local',
    'smart3ai.local',
):
    if required_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(required_host)

if IS_PRODUCTION:
    if SECRET_KEY in ('', 'change-this-dev-secret-key-before-deploy'):
        raise RuntimeError('DJANGO_SECRET_KEY must be set to a secure value in production')
    if DEBUG:
        raise RuntimeError('DEBUG must be disabled in production')
    if not ALLOWED_HOSTS:
        raise RuntimeError('ALLOWED_HOSTS must be configured in production')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'apps.organizations',
    'apps.users',
    'apps.subscriptions',
    'apps.products',
    'apps.billing',
    'apps.api',
    'apps.integration',
    'django_apscheduler',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'config.middleware.RequestIDMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'adminapps_db'),
        'USER': os.environ.get('DB_USER', 'adminapps_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
    }
}

if 'test' in sys.argv or os.environ.get('USE_SQLITE_FOR_TESTS', '').lower() == 'true':
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_default.sqlite3',
    }

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('THROTTLE_ANON_RATE', '60/minute'),
        'user': os.environ.get('THROTTLE_USER_RATE', '300/minute'),
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SMART3AI_SSO_JWT_SECRET,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

PASSWORD_HISTORY_COUNT = int(os.environ.get('PASSWORD_HISTORY_COUNT', '5'))
TEMP_PASSWORD_MAX_AGE_DAYS = int(os.environ.get('TEMP_PASSWORD_MAX_AGE_DAYS', '7'))
TEMP_PASSWORD_WARNING_DAYS = int(os.environ.get('TEMP_PASSWORD_WARNING_DAYS', '2'))

# Billing policy for owner organization (Smart3AI)
BILLING_OWNER_ORG_EXEMPT_ENABLED = _env_bool('BILLING_OWNER_ORG_EXEMPT_ENABLED', default=True)
BILLING_OWNER_ORG_ID = os.environ.get('BILLING_OWNER_ORG_ID', '').strip()
BILLING_OWNER_ORG_CODE = os.environ.get('BILLING_OWNER_ORG_CODE', '').strip()
BILLING_OWNER_ORG_NAME = os.environ.get('BILLING_OWNER_ORG_NAME', 'Smart3AI').strip()

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    *(_env_list(
        'CORS_ALLOWED_ORIGINS',
        default='http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:4173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:4173,http://192.168.100.100:3000,http://192.168.100.100:3001'
    )),
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = _env_list(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,http://192.168.100.100:3000,http://192.168.100.100:3001'
)

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-request-id',
    'x-requested-with',
    'x-organization-id',
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'config.request_context.RequestIDLogFilter',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} request_id={request_id} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} request_id={request_id} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'adminapps.log',
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['request_id'],
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('APPS_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Security headers and cookies (TLS-related settings intentionally omitted for dev phase)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = _env_bool('CSRF_COOKIE_SECURE', default=not DEBUG)

# ISO Smart Integration
ISOSMART_API_URL = os.environ.get('ISOSMART_API_URL', 'http://localhost:8000/api')
FRONTEND_BASE_URL = os.environ.get('FRONTEND_BASE_URL', 'http://localhost:3000')

# Integration API key hashes (fallback when key not stored in DB)
INTEGRATION_API_KEYS = {
    'isosmart': os.environ.get(
        'ISOSMART_API_KEY_HASH',
        '20985646232d3504aeddb985345b81ec968ed8d86a6993ab7efcfdd35cd537e7',
    ),
    'landing_analytics': os.environ.get(
        'LANDING_ANALYTICS_API_KEY_HASH',
        '0dc7befde90cc98351939f394cc9cccef2376a74c634d45a6ceb1a576f4dac3f',
    ),
}

# Billing Scheduler
BILLING_SCHEDULER_ENABLED = os.environ.get('BILLING_SCHEDULER_ENABLED', 'true').lower() == 'true'
BILLING_SCHEDULER_HOUR = int(os.environ.get('BILLING_SCHEDULER_HOUR', '6'))
BILLING_SCHEDULER_MINUTE = int(os.environ.get('BILLING_SCHEDULER_MINUTE', '0'))
APSCHEDULER_DATETIME_FORMAT = 'N j, Y, f:s a'
APSCHEDULER_RUN_NOW_TIMEOUT = 25
