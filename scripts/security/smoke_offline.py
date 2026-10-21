#!/usr/bin/env python3
"""Import application models under synthetic settings with DB/network forbidden."""
import ast
import os
from pathlib import Path
import secrets
import socket
import sys
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'backend'))
sys.dont_write_bytecode = True
os.environ.pop('DJANGO_SETTINGS_MODULE', None)
def blocked(*args, **kwargs):
    raise AssertionError('Offline smoke attempted network/DB')
socket.socket.connect = blocked
socket.create_connection = blocked
from django.conf import settings
settings.configure(SECRET_KEY=secrets.token_hex(32), USE_TZ=True,
    AUTH_USER_MODEL='users.User', DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
    BILLING_SCHEDULER_ENABLED=False, LOGGING_CONFIG=None,
    DATABASES={'default': {'ENGINE': 'django.db.backends.dummy'}},
    INSTALLED_APPS=['django.contrib.admin', 'django.contrib.messages', 'django.contrib.auth',
        'django.contrib.contenttypes', 'django.contrib.sessions', 'rest_framework', 'django_filters',
        'apps.users', 'apps.organizations', 'apps.products', 'apps.subscriptions',
        'apps.integration', 'apps.billing', 'apps.api', 'rest_framework_simplejwt.token_blacklist'])
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.connect = blocked
import django
django.setup()
from apps.users import models_2fa
from config import runtime_profiles
for p in (root / 'backend').rglob('*.py'):
    ast.parse(p.read_bytes(), filename=str(p.relative_to(root)))
print('PASS offline Django app/model imports + Python syntax; no active settings/DB/network')
