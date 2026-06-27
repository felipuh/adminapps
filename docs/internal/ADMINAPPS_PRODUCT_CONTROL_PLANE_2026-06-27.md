# AdminApps Product Control Plane - 2026-06-27

## Objetivo

AdminApps queda como plano de control neutral para habilitar productos por organizacion. El primer contrato cubierto es `MEDSUPPLIER`, sin acoplar la autorizacion del producto al modelo historico de estandares ISO.

## Cambios principales

- `ProductSystem`: catalogo global de productos controlados por AdminApps.
- `OrganizationProductEntitlement`: habilitacion de producto por organizacion, con estado, scopes, modulos, plan y suscripcion asociados.
- Semilla inicial via migracion: `ISO_SMART` y `MEDSUPPLIER`.
- API administrativa:
  - `GET /api/products/systems/`
  - `GET /api/products/systems/active/`
  - `GET|POST /api/products/entitlements/`
  - `POST /api/products/entitlements/{id}/toggle/`
  - `GET /api/products/entitlements/by_organization/?organization_id=<uuid>`
- API de integracion para productos externos:
  - `GET /api/integration/organizations/{org_id}/products/`
  - `GET /api/integration/organizations/{org_id}/products/{product_code}/validate/`
- Compatibilidad legacy: `GET /api/integration/organizations/{org_id}/modules/` incluye productos activos como entradas tipo modulo para clientes que aun consumen ese contrato.

## Seguridad 2FA

El login con 2FA ya no emite un JWT completo antes de completar TOTP. Ahora devuelve un token temporal firmado con:

- `purpose=2fa_verification`
- `scope=totp_verification_only`
- expiracion maxima de 300 segundos en la verificacion

La vista `POST /api/auth/2fa/verify/` resuelve ese token temporal sin pasar por autenticacion JWT global.

## Verificacion ejecutada

```bash
DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py makemigrations --check --dry-run
DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py check
DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py test apps.products.tests
DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py test apps.users.tests_2fa.LoginWith2FATests apps.users.tests_2fa.TwoFactorAuthRateLimitTests
DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py test apps.products apps.billing apps.users apps.api
npm run lint
npm run build
```

Resultado: backend amplio con 120 tests OK, lint frontend sin errores bloqueantes y build Vite OK.

## Nota de migraciones

`migrate --plan` muestra migraciones pendientes preexistentes de `billing`, `integration`, `token_blacklist` y `users`, ademas de las nuevas:

- `subscriptions.0002_alter_plan_modules_included`
- `products.0002_productsystem_organizationproductentitlement`

Antes de release, aplicar todo el plan en staging y verificar que la semilla de productos no choque con datos productivos manuales.
