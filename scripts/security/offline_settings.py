"""Synthetic check settings. Never import operational settings or load dotenv."""
import secrets

SECRET_KEY = secrets.token_urlsafe(48)
USE_TZ = True
AUTH_USER_MODEL = 'users.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'config.urls_control_plane'
ALLOWED_HOSTS = ['localhost']
BILLING_SCHEDULER_ENABLED = False
LOGGING_CONFIG = None
DATABASES = {'default': {'ENGINE': 'django.db.backends.dummy'}}
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.messages', 'django.contrib.auth',
    'django.contrib.contenttypes', 'django.contrib.sessions', 'rest_framework',
    'django_filters', 'apps.users', 'apps.organizations', 'apps.products',
    'apps.subscriptions', 'apps.integration', 'apps.billing', 'apps.api',
    'rest_framework_simplejwt.token_blacklist',
]
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
              'APP_DIRS': True, 'OPTIONS': {'context_processors': [
                  'django.template.context_processors.request',
                  'django.contrib.auth.context_processors.auth',
                  'django.contrib.messages.context_processors.messages']}}]
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': [
    'apps.users.authentication.HumanJWTAuthentication']}
