# QA Evidence - AdminApps

Fecha de ejecucion principal: 2026-07-02 America/Costa_Rica.

## Backend

- `.venv/bin/python manage.py check`: OK.
- `.venv/bin/python manage.py check --deploy`: OK con warnings esperados si se usan valores locales de `.env`.
- `DJANGO_ENV=production ... .venv/bin/python manage.py check --deploy`: OK, sin issues, usando overrides productivos completos de prueba.
- `.venv/bin/python manage.py makemigrations --check --dry-run`: OK, sin cambios detectados.
- `.venv/bin/python manage.py test apps.api.tests_security_guardrails apps.integration.tests.IntegrationAPIKeyUsageTests`: OK, 3 tests.
- `.venv/bin/python manage.py test apps.billing.tests_scheduler_config`: OK, 3 tests.
- `.venv/bin/python manage.py test`: OK, 160 tests.
- `rg "fields\\s*=\\s*['\\\"]__all__['\\\"]" backend --glob '!**/migrations/**' --glob '!**/staticfiles/**'`: sin resultados.
- `.venv/bin/python manage.py showmigrations --plan`: ejecutado. Migraciones pendientes observadas: `products.0003_productentitlementauditlog`, `billing.0006_productcatalog_system_product`, `integration.0004_integrationapikey_last_used_at_and_more`.

## Frontend

- `npm ci`: OK, 0 vulnerabilidades reportadas.
- `npm run lint`: OK.
- `npm run build`: OK.
- `rg -n "http://landing\\.isosmart\\.local" src`: sin resultados.

Build generado:

- `dist/index.html`
- bundles principales `vendor`, `charts` e `index`.

## Observaciones

- Durante comandos Django ya no se registra inicio automatico del scheduler de billing.
- El secret usado para `check --deploy` productivo fue un valor temporal de prueba, no un secreto real.
- `VITE_LANDING_URL` queda documentado en `frontend/.env.example`; en ausencia de variable el link comercial no se muestra.
