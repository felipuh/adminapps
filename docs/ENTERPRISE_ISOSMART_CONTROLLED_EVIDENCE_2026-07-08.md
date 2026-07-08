# Enterprise ISO Smart Controlled Evidence - 2026-07-08

## Dictamen

**GO CONTROLADO** para kickoff local/controlado.

No es GO completo: dominio, DNS, certificados, HTTPS publico, Nginx publico y deploy productivo quedaron fuera de alcance y no fueron tocados.

## Estado Anterior

Estado previo: **GO WITH RESTRICTIONS**.

Causa de restriccion anterior:
- El smoke ISO Smart fallaba porque la organizacion local `smart3ai` no tenia evidencia ejecutada de entitlement real `ISO_SMART`.
- El login real no estaba probado con credenciales validas y datos controlados.

## Causa Raiz Cerrada

El entorno local/controlado ya tiene alineacion entre ISO Smart y AdminApps:
- ISO Smart `smart3ai` usa `external_id=f4a99825-71c5-4aaa-b83b-09ddc662e4a4`.
- AdminApps tiene organizacion `SMART3AI / Smart3AI` activa con ese ID.
- AdminApps tiene `ProductSystem ISO_SMART` activo.
- AdminApps tiene subscription `ISO_SMART_PILOT` activa.
- AdminApps tiene entitlement `ISO_SMART` activo con `access_allowed=true` y `access_denial_reason=ok`.

## Datos Creados o Corregidos

Se creo un usuario local/controlado de integracion en AdminApps:
- Email: `iso-smart-controlled-login@smart3ai.local`
- Organizacion: `SMART3AI`
- Rol: `org_admin`
- Password: generado de forma efimera durante la prueba; no fue impreso ni documentado.

Comando creado:
- `apps/users/management/commands/provision_controlled_integration_user.py`

El comando es idempotente, acepta `--dry-run`, no imprime password y queda limitado a una organizacion existente.

## Evidencia de Idempotencia

`provision_pilot_entitlement --organization SMART3AI --product ISO_SMART --plan pilot --dry-run`:
- `create_plan=false`
- `create_subscription=false`
- `create_entitlement=false`
- `activate_entitlement=false`
- `attach_subscription=false`
- `access_allowed=true`
- `access_denial_reason=ok`

`provision_controlled_integration_user --email iso-smart-controlled-login@smart3ai.local --organization SMART3AI --role org_admin --dry-run` posterior:
- `create_user=false`
- `create_membership=false`
- `activate_user=false`
- `activate_membership=false`
- `update_membership_role=false`

## Smokes

AdminApps:
- Health sin API key: 401.
- Health con API key invalida: 401.
- Health con API key valida: 200.
- Validate `ISO_SMART`: 200, `allowed=true`, `reason=ok`, `billing_status=active`.
- Validate `MEDSUPPLIER`: 200, `allowed=true`, `reason=ok`, `billing_status=active`.

ISO Smart:
- `check_isosmart_adminapps --organization-slug smart3ai --no-fallback`: PASS.
- Evidencia: `adminapps_available=True`, `product_access_source=adminapps`, `iso_smart_access_enabled=True`, `iso_smart_access_reason=ok`, `billing_status=active`, `fallback_allowed=False`.

MedSupplier:
- `check_medsupplier_adminapps --organization-slug medsupplier-demo-e2e --no-fallback`: PASS.
- Evidencia: `adminapps_available=True`, `product_access_source=adminapps`, `medsupplier_entitlement_enabled=True`, `medsupplier_access_reason=ok`, `active_medsupplier_scopes=10`, `fallback_allowed=False`.

## Login Real Controlado

ISO Smart proceso login real local/controlado contra AdminApps:
- HTTP 200.
- Access token emitido: si.
- Refresh token emitido: si.
- Usuario: `iso-smart-controlled-login@smart3ai.local`.
- Organizacion perfil: `Smart3AI`.
- Rol perfil: `org_admin`.
- `validate_credentials` AdminApps ejecutado: 1 vez.
- `validate_product_access` AdminApps ejecutado antes de completar login: 1 vez.
- Resultado de producto: `allowed=true`, `reason=ok`, `source=adminapps`, `fallback=false`, `billing_status=active`, `product_code=ISO_SMART`, `access_denial_reason=ok`.

## QA Ejecutado

AdminApps:
- `./.venv312/bin/python manage.py check`: PASS.
- `./.venv312/bin/python manage.py makemigrations --check --dry-run`: PASS.
- `./.venv312/bin/python manage.py migrate --plan`: no planned migration operations.
- `DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py test apps.products.tests apps.integration.tests`: PASS, 35 tests.

ISO Smart:
- `./.venv312/bin/python manage.py check`: PASS.
- `./.venv312/bin/python manage.py makemigrations --check --dry-run`: PASS.
- `./.venv312/bin/python manage.py migrate --plan`: no planned migration operations.
- `DJANGO_SETTINGS_MODULE=backend.settings_test ./.venv312/bin/python manage.py test authentication.tests.LoginProductAccessPolicyTests authentication.tests.LoginLockoutTests authentication.tests.TemporaryPasswordLoginPolicyTests integration.tests.AssistantApiTests`: PASS, 13 tests.

MedSupplier:
- `./.venv312/bin/python manage.py check`: PASS.
- `./.venv312/bin/python manage.py makemigrations --check --dry-run`: PASS.
- `./.venv312/bin/python manage.py migrate --plan`: no planned migration operations.
- `DJANGO_SETTINGS_MODULE=backend.settings_test ./.venv312/bin/python manage.py test medsupplier.tests.MedSupplierAdminAppsClientTests medsupplier.tests.MedSupplierSerializerGuardrailTests medsupplier.tests.MedSupplierPermissionTests`: PASS, 43 tests.

## Seguridad y Guardrails

Confirmado en esta fase:
- No se imprimieron passwords, tokens, API keys ni credenciales.
- No se habilito fallback silencioso.
- Los smokes exigieron `--no-fallback`.
- ISO Smart valida `ISO_SMART` contra AdminApps antes de completar login.
- No se creo bypass de entitlement.
- No se tocaron dominio, DNS, certificados, certbot, Nginx publico ni deploy productivo.
- No se uso sudo.
- No se hizo push.

## Riesgos Residuales

- El login denegado por ausencia de entitlement queda cubierto por tests focalizados; no se desactivo temporalmente el entitlement real `SMART3AI/ISO_SMART` para evitar impacto local sobre la organizacion piloto.
- La validacion fue local/controlada. El paso a productivo requiere gates separados de dominio, TLS, Nginx, monitoreo, backup/restore y aprobacion humana.

## Pendientes

- Ejecutar la misma matriz en staging/target real antes de cualquier produccion.
- Definir rollback operativo formal para usuario QA si deja de usarse.
- Mantener rotacion/limpieza periodica de usuarios locales controlados.

## Fuera de Alcance Confirmado

- Dominio.
- DNS.
- Certificados.
- HTTPS publico.
- Nginx publico.
- Deploy productivo.

