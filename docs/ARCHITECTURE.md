# AdminApps Architecture Notes

Date: 2026-07-03

## Active Backend

The active Django backend is `backend/config`.

Evidence:

- `backend/manage.py` sets `DJANGO_SETTINGS_MODULE=config.settings`.
- `backend/config/settings.py` defines the active `INSTALLED_APPS`, database, DRF, JWT, and integration settings.
- `backend/config/urls.py` is the active `ROOT_URLCONF`.
- `backend/config/wsgi.py` sets `DJANGO_SETTINGS_MODULE=config.settings`.

## Legacy Backend Tree

The `backend/adminapps` tree is legacy/deprecated for this hardening phase.

Evidence:

- `backend/adminapps/settings.py` still exists and has its own `ROOT_URLCONF`.
- Runtime entrypoints do not point to `adminapps.settings`.
- `backend/debug_script.py` references `adminapps.settings` and should not be used for production or QA evidence.

Do not add new features or fixes under `backend/adminapps` unless a dependency analysis proves that path is still active. Keep changes in `backend/config` and `backend/apps`.

## Migration State

The following migrations exist in code and were detected as unapplied in the configured local database during preflight:

- `products.0003_productentitlementauditlog`
- `billing.0006_productcatalog_system_product`
- `integration.0004_integrationapikey_last_used_at_and_more`

`makemigrations --check --dry-run` reported no model changes without migrations. Because the configured default database points to PostgreSQL from `backend/.env`, this phase did not apply migrations automatically. Apply them only against a confirmed local/control database, not production.

## Integration Contract

AdminApps is the commercial authority for organizations, users, products, entitlements, and billing state. Product systems should call the integration API with an explicit API key and deny access when AdminApps returns no entitlement or an inactive entitlement.

Fallback API key hashes are allowed only for development/test. Staging and production must use explicit `ISOSMART_API_KEY_HASH` / `LANDING_ANALYTICS_API_KEY_HASH` values or persisted `IntegrationAPIKey` rows.
