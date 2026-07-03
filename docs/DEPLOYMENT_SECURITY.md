# Deployment Security

Date: 2026-07-03

## Scope

This note covers the controlled pilot readiness posture for AdminApps, ISO Smart, and MedSupplier. It does not approve regulated or formal production.

## Required Production Settings

- `DJANGO_ENV=production`
- `DEBUG=False`
- Long random `SECRET_KEY`
- Explicit `ALLOWED_HOSTS`
- Explicit `CSRF_TRUSTED_ORIGINS`
- Explicit `CORS_ALLOWED_ORIGINS`
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=31536000`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `SECURE_HSTS_PRELOAD=True` only after the final domain meets preload requirements
- `SECURE_PROXY_SSL_HEADER` configured only behind a trusted TLS-terminating proxy

## Local Verification

`check --deploy` passes with simulated production variables in the three backends when HSTS preload is explicitly enabled and the test secret is long enough. In normal local mode, warnings can remain because local HTTP development is intentionally supported.

## AdminApps Migration Evidence

AdminApps DB was confirmed as local PostgreSQL on `127.0.0.1:5432`, database `adminapps_db`, user `adminapps_user`.

Applied migrations:

- `products.0003_productentitlementauditlog`
- `billing.0006_productcatalog_system_product`
- `integration.0004_integrationapikey_last_used_at_and_more`

Post-migration checks:

- `showmigrations --plan`: those migrations are `[X]`
- `python manage.py check`: OK
- `python manage.py makemigrations --check --dry-run`: no changes detected

## Restrictions

- No deploy was performed.
- No push was performed.
- No real `.env` file was modified.
- Regulated production remains blocked until WORM storage, SOPs, traceability matrix, validation package, and human approval workflow are formally implemented.
