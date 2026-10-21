from .settings import *  # noqa: F401,F403

ENVIRONMENT = 'test'
IS_PRODUCTION = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
BILLING_SCHEDULER_ENABLED = False

# Use SQLite for local test execution to avoid MySQL test DB permission issues.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test.sqlite3',
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Keep test runs fast by reducing logging noise.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}
