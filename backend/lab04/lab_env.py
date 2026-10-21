"""Isolated settings: never import active settings, dotenv, or external services."""
import os, sys, json, socket
from pathlib import Path
from datetime import timedelta
ROOT=Path(os.environ['LAB04_ROOT']).resolve()
REPO=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(REPO/'backend'))
# Deny every Python INET connection; PostgreSQL uses libpq and private Unix socket.
_original_connect=socket.socket.connect
def connect(self,address):
    if self.family != socket.AF_UNIX: raise RuntimeError('External network forbidden by LAB04')
    return _original_connect(self,address)
socket.socket.connect=connect
os.environ.pop('DJANGO_SETTINGS_MODULE',None)
from django.conf import settings
secret=json.loads((ROOT/'runtime'/('credentials-' + os.environ.get('LAB04_ROLE', 'lab04_iam') + '.json')).read_text())
configuration = dict(
 SECRET_KEY=secret['signing_key'],USE_TZ=True,AUTH_USER_MODEL='users.User',DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
 ROOT_URLCONF='lab_urls',ALLOWED_HOSTS=['testserver'],BILLING_SCHEDULER_ENABLED=False,
 INSTALLED_APPS=['django.contrib.admin','django.contrib.messages','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','rest_framework','django_filters',
 'apps.users','apps.organizations','apps.products','apps.subscriptions','apps.integration','apps.billing','apps.api','rest_framework_simplejwt.token_blacklist'],
 DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':'lab04_human','USER':'lab04_bootstrap' if os.environ.get('LAB04_MIGRATE')=='1' else os.environ.get('LAB04_ROLE', 'lab04_iam'),
 'PASSWORD':'' if os.environ.get('LAB04_MIGRATE')=='1' else secret['password'],'HOST':str(ROOT/'runtime/socket'),'PORT':'56434',
 'OPTIONS':{'options':'-c role=lab04_maintenance'} if os.environ.get('LAB04_MIGRATE')=='1' else {},'CONN_MAX_AGE':0}},
 MIDDLEWARE=['django.contrib.sessions.middleware.SessionMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware'],
 SESSION_ENGINE='django.contrib.sessions.backends.db',CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}},
 EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',LOGGING_CONFIG=None,
 TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}],
 PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher','django.contrib.auth.hashers.MD5PasswordHasher'],
 REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':['apps.users.authentication.HumanJWTAuthentication','rest_framework.authentication.SessionAuthentication'],
 'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated']},
 SIMPLE_JWT={'ALGORITHM':'HS256','SIGNING_KEY':secret['signing_key'],'ROTATE_REFRESH_TOKENS':True,'ACCESS_TOKEN_LIFETIME':timedelta(hours=1),'REFRESH_TOKEN_LIFETIME':timedelta(days=1)})
if os.environ.get('LAB04_PROFILE'):
 from config.runtime_profiles import configure
 configure(configuration, os.environ['LAB04_PROFILE'], configuration['DATABASES']['default'])
settings.configure(**configuration)
import django
django.setup()
from django.db import connection
with connection.cursor() as q:
 q.execute('SELECT current_database(),current_user,inet_server_addr()'); row=q.fetchone()
 assert row[0]=='lab04_human' and row[1] in (os.environ.get('LAB04_ROLE', 'lab04_iam'),'lab04_maintenance') and row[2] is None
# These models are registered by URL imports in the application.
from apps.users import models_2fa
