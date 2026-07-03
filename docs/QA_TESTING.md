# QA Testing Gate - AdminApps

Date: 2026-07-03

## Official Local Gate

Run from `/home/felipe/proyectos/adminapps/backend`:

```bash
. .venv/bin/activate
python manage.py check
DJANGO_ENV=production \
DJANGO_SECRET_KEY=test-secure-key-for-check-only-2026-07-03-not-a-real-secret-value \
ALLOWED_HOSTS=example.com \
CSRF_TRUSTED_ORIGINS=https://example.com \
CORS_ALLOWED_ORIGINS=https://example.com \
SECURE_SSL_REDIRECT=true \
SESSION_COOKIE_SECURE=true \
CSRF_COOKIE_SECURE=true \
SECURE_HSTS_SECONDS=31536000 \
SECURE_HSTS_INCLUDE_SUBDOMAINS=true \
SECURE_HSTS_PRELOAD=true \
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
python manage.py showmigrations --plan
USE_SQLITE_FOR_TESTS=true python manage.py test
```

Run from `/home/felipe/proyectos/adminapps/frontend`:

```bash
npm run lint
npm run build
```

## Database Permissions

AdminApps can run tests with SQLite by setting `USE_SQLITE_FOR_TESTS=true`. If CI or staging must run against PostgreSQL instead, the configured `DB_USER` needs permission to create and drop the Django test database.

Minimum DBA action for PostgreSQL:

```sql
ALTER ROLE adminapps_user CREATEDB;
```

Use an environment-specific role name. Do not grant this to a production runtime role unless the environment is explicitly isolated for CI/staging test execution.

## Gate Decision

The official pilot gate is the command set above plus frontend lint/build. A default `python manage.py test` without `USE_SQLITE_FOR_TESTS=true` may depend on local PostgreSQL privileges and is not the portable gate for this release candidate.
