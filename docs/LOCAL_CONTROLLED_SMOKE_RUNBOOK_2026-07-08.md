# Local Controlled Smoke Runbook - ISO Smart / AdminApps

## Alcance

Runbook para preparar y validar datos locales/controlados de ISO Smart contra AdminApps sin tocar produccion, dominio, DNS, certificados, Nginx publico ni deploy.

## Preparar Datos

1. Verificar organizacion piloto:
   `./.venv312/bin/python manage.py shell`
   - `Organization.code=SMART3AI`
   - `status=active`

2. Verificar entitlement:
   `./.venv312/bin/python manage.py provision_pilot_entitlement --organization SMART3AI --product ISO_SMART --plan pilot --scopes owner,admin,billing_exempt,all_modules --dry-run`

3. Si el dry-run planea cambios esperados y acotados, ejecutar:
   `./.venv312/bin/python manage.py provision_pilot_entitlement --organization SMART3AI --product ISO_SMART --plan pilot --scopes owner,admin,billing_exempt,all_modules`

4. Repetir dry-run y confirmar:
   - `create_plan=false`
   - `create_subscription=false`
   - `create_entitlement=false`
   - `activate_entitlement=false`
   - `access_allowed=true`
   - `access_denial_reason=ok`

## Preparar Usuario Controlado

1. Dry-run:
   `./.venv312/bin/python manage.py provision_controlled_integration_user --email iso-smart-controlled-login@smart3ai.local --organization SMART3AI --role org_admin --dry-run`

2. Ejecucion real con password efimero. No imprimir el password:
   `./.venv312/bin/python manage.py provision_controlled_integration_user --email iso-smart-controlled-login@smart3ai.local --organization SMART3AI --role org_admin --password "$QA_PASS"`

3. Repetir dry-run y confirmar que no hay cambios planeados.

## Smoke ISO Smart

Desde ISO Smart:

`./.venv312/bin/python manage.py check_isosmart_adminapps --organization-slug smart3ai --no-fallback`

PASS esperado:
- `adminapps_available=True`
- `product_access_source=adminapps`
- `iso_smart_access_enabled=True`
- `iso_smart_access_reason=ok`
- `billing_status=active`
- `fallback_allowed=False`

## Login Controlado

Ejecutar login local con cliente de pruebas HTTPS/local y password efimero en variable de entorno. Confirmar solo salida sanitizada:
- HTTP 200.
- Tokens presentes, sin imprimirlos.
- `validate_credentials` ejecutado.
- `validate_product_access` ejecutado antes de completar login.
- `allowed=true`.
- `reason=ok`.
- `source=adminapps`.
- `fallback=false`.
- `product_code=ISO_SMART`.

## Interpretacion de Errores

- 401 en health sin API key o con API key invalida: esperado.
- 403 en validate product: entitlement ausente, inactivo, billing bloqueado o producto no habilitado.
- 404: organizacion o producto inexistente, segun contrato.
- 503/error controlado: AdminApps no disponible.
- 301/DisallowedHost en harness local: ajustar `HTTP_HOST=localhost` y `secure=True`; no tocar Nginx ni certificados.

## Reglas de Seguridad

- No imprimir passwords, tokens ni API keys.
- No usar credenciales productivas.
- No inventar credenciales.
- No activar fallback silencioso.
- No usar `sudo`.
- No tocar dominio, DNS, certbot, certificados, Nginx publico ni deploy productivo.

