"""API P0 dispatch/serializer probes. No project settings, DB, migrations or network."""
import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
guards = [patch(target, side_effect=AssertionError('Network forbidden')).start() for target in (
    'socket.socket.connect', 'socket.socket.connect_ex', 'socket.create_connection', 'socket.getaddrinfo')]
from django.conf import settings
settings.configure(
    SECRET_KEY='offline-api-p0-synthetic-only', USE_TZ=True, ROOT_URLCONF='config.urls',
    AUTH_USER_MODEL='users.User', ALLOWED_HOSTS=['testserver'], BILLING_SCHEDULER_ENABLED=False,
    INSTALLED_APPS=['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
                    'django.contrib.sessions', 'django.contrib.messages', 'rest_framework',
                    'django_filters', 'apps.users', 'apps.organizations', 'apps.subscriptions',
                    'apps.products', 'apps.integration', 'apps.billing', 'apps.api',
                    'rest_framework_simplejwt.token_blacklist'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.dummy'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication']},
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    MIDDLEWARE=['django.contrib.sessions.middleware.SessionMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware'],
    TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True,
                'OPTIONS': {'context_processors': ['django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages']}}],
    LOGGING_CONFIG=None,
)
from django.db.backends.base.base import BaseDatabaseWrapper
db_guard = patch.object(BaseDatabaseWrapper, 'connect', side_effect=AssertionError('Database forbidden')).start()
import django
django.setup()

if __name__ == '__main__':
    if '--check' in sys.argv:
        from django.core.management import call_command
        call_command('check')
        result = None
    else:
        labels = sys.argv[1:] or ['apps.api.test_control_plane']
        suite = unittest.defaultTestLoader.loadTestsFromNames(labels)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = dict(tests=result.testsRun if result else 0,
                   failures=len(result.failures) if result else 0, errors=len(result.errors) if result else 0,
                   database_attempts=db_guard.call_count, network_attempts=sum(g.call_count for g in guards))
    print(json.dumps(summary))
    sys.exit(bool(summary['failures'] or summary['errors'] or summary['database_attempts'] or summary['network_attempts']))
