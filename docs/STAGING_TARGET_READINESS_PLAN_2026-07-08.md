# Staging/Target Readiness Plan - 2026-07-08

## Dictamen Actual

GO WITH RESTRICTIONS.

Motivo: el entorno staging/target no esta identificado en esta sesion. No hay host interno confirmado, base objetivo, runner remoto, `.env.staging` ni evidencia de smokes reales contra target.

Este documento prepara el paso ordenado a GO CONTROLADO STAGING/TARGET sin tocar produccion publica.

## Fuera De Alcance

- Dominio publico.
- DNS.
- Certificados SSL/TLS.
- HTTPS publico.
- Nginx publico.
- Certbot.
- Deploy productivo final.
- Merge a `main` o `master`.
- Release tag.

## Commits Base

AdminApps:

- Branch: `hardening/p0-p1-enterprise-readiness`
- Commit: `633053f6 feat(adminapps): add controlled ISO Smart QA provisioning evidence`

ISO Smart:

- Branch: `hardening/p0-p1-enterprise-readiness`
- Commit: `cbe74545 fix(iso-smart): enforce AdminApps product access before login`
- Commit: `fc2a670f test(iso-smart): add controlled AdminApps access smoke coverage`

MedSupplier:

- Branch: `hardening/p0-p1-enterprise-readiness`
- Sin commits nuevos pendientes.

## Inventario Pendiente Por Definir

Completar solo con presencia, alias no sensibles o referencias internas. No documentar secretos.

| Item | Estado | Evidencia Permitida |
| --- | --- | --- |
| Host o alias interno AdminApps staging | PENDIENTE | Alias interno, sin credenciales |
| Host o alias interno ISO Smart staging | PENDIENTE | Alias interno, sin credenciales |
| Host o alias interno MedSupplier staging | PENDIENTE | Alias interno, sin credenciales |
| Base de datos AdminApps staging | PENDIENTE | Nombre logico o alias, sin password |
| Base de datos ISO Smart staging | PENDIENTE | Nombre logico o alias, sin password |
| Base de datos MedSupplier staging | PENDIENTE | Nombre logico o alias, sin password |
| Rama exacta a desplegar | PENDIENTE | `hardening/p0-p1-enterprise-readiness` esperado |
| Metodo de ejecucion | PENDIENTE | CI runner, SSH controlado, manual en servidor, contenedores, systemd u otro |
| Ruta proyecto AdminApps en target | PENDIENTE | Ruta sin secretos |
| Ruta proyecto ISO Smart en target | PENDIENTE | Ruta sin secretos |
| Ruta proyecto MedSupplier en target | PENDIENTE | Ruta sin secretos |
| Python version | PENDIENTE | Version |
| Virtualenv AdminApps | PENDIENTE | Path |
| Virtualenv ISO Smart | PENDIENTE | Path |
| Virtualenv MedSupplier | PENDIENTE | Path |
| Settings module AdminApps | PENDIENTE | Nombre de modulo |
| Settings module ISO Smart | PENDIENTE | Nombre de modulo |
| Settings module MedSupplier | PENDIENTE | Nombre de modulo |
| Modo fallback requerido | PENDIENTE | Deshabilitado para smoke |
| URL interna AdminApps | PENDIENTE | URL interna sin API key |
| API key interna configurada | PENDIENTE | Presente/ausente, nunca valor |
| Usuario QA controlado | PENDIENTE | Email o alias autorizado |
| Organizacion/tenant QA positivo | PENDIENTE | Slug/codigo |
| Organizacion/tenant QA negativo | PENDIENTE | Slug/codigo |

## Variables Requeridas

Reportar por variable: presente/ausente, formato valido/invalido, entorno correcto/incorrecto. No imprimir valores.

### AdminApps

- `DJANGO_SETTINGS_MODULE`
- `DATABASE_URL` o variables DB equivalentes
- `DB_NAME`
- `DB_USER`
- `DB_HOST`
- `DB_PORT`
- `SECRET_KEY` o `DJANGO_SECRET_KEY`
- `ADMINAPPS_INTERNAL_API_KEY` o equivalente
- `ALLOWED_HOSTS`
- `DEBUG`
- Product catalog flags, si aplican
- Billing/subscription flags, si aplican
- Integration flags, si aplican

### ISO Smart

- `DJANGO_SETTINGS_MODULE`
- `DATABASE_URL` o variables DB equivalentes
- `DB_NAME`
- `DB_USER`
- `DB_HOST`
- `DB_PORT`
- `SECRET_KEY`
- `ADMINAPPS_BASE_URL` o `ADMIN_APPS_BASE_URL`
- `ADMINAPPS_API_KEY` o `ADMIN_APPS_API_KEY`
- `PRODUCT_CODE=ISO_SMART` o `ISO_SMART_PRODUCT_CODE=ISO_SMART`
- Fallback deshabilitado: `ALLOW_LOCAL_AUTH_FALLBACK=False` o equivalente
- Bypass local deshabilitado: `ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS=False` o equivalente
- `ADMINAPPS_TIMEOUT` o `ADMIN_APPS_TIMEOUT`

### MedSupplier

- `DJANGO_SETTINGS_MODULE`
- `DATABASE_URL` o variables DB equivalentes
- `DB_NAME`
- `DB_USER`
- `DB_HOST`
- `DB_PORT`
- `SECRET_KEY`
- `ADMINAPPS_BASE_URL` o `ADMIN_APPS_BASE_URL`
- `ADMINAPPS_API_KEY` o `ADMIN_APPS_API_KEY`
- `PRODUCT_CODE=MEDSUPPLIER` o equivalente
- Fallback deshabilitado: `ADMIN_APPS_ALLOW_LOCAL_FALLBACK=False` o equivalente
- Bypass local deshabilitado, si existe
- `ADMINAPPS_TIMEOUT` o `ADMIN_APPS_TIMEOUT`

## Datos Positivos Requeridos

AdminApps staging/target debe tener:

- Organizacion piloto: `SMART3AI`, `Smart3AI` o tenant definido para staging.
- Organizacion activa.
- Producto `ISO_SMART` existente, activo y sin duplicados.
- Producto `MEDSUPPLIER` existente, activo y sin duplicados.
- Subscription `ISO_SMART` activa, `billing_status=active`, no expirada, no cancelada.
- Entitlement `ISO_SMART` activo, `access_allowed=true`, `access_denial_reason=ok`.
- Subscription `MEDSUPPLIER` activa si aplica, `billing_status=active`.
- Entitlement `MEDSUPPLIER` activo, `access_allowed=true`, `access_denial_reason=ok`.

Si faltan datos:

- Usar management commands idempotentes.
- Ejecutar primero `--dry-run`.
- Confirmar que no duplica.
- Confirmar que no afecta otros productos.
- Ejecutar real solo si staging/target lo permite.
- Ejecutar segundo `--dry-run` para confirmar idempotencia.

## Prueba Negativa Controlada

No mutar el entitlement activo de SMART3AI piloto.

Tenant sugerido:

- `SMART3AI_DENIED_TEST`
- `smart3ai-denied-test`
- `ISO_SMART_DENIED_TEST`

Condicion:

- Organizacion existe.
- Producto `ISO_SMART` existe.
- Entitlement ausente o inactivo.
- Subscription ausente, inactiva o `billing_status` distinto de `active`, segun contrato.

Resultado esperado:

- Login bloqueado.
- No se emiten tokens.
- `source=adminapps`.
- `fallback=false`.
- Reason claro.
- HTTP 403 o equivalente controlado.
- Sin 500.
- Sin fallback.
- Sin bypass.

## Reglas De Seguridad

- No documentar secretos.
- No copiar `.env` reales.
- No subir valores sensibles.
- No imprimir tokens.
- No imprimir passwords.
- No imprimir API keys.
- No imprimir headers sensibles.
- No activar fallback silencioso.
- No crear bypasses.
- No usar datos productivos sensibles.

## Criterios De Dictamen

### GO CONTROLADO STAGING/TARGET

- AdminApps PASS.
- ISO Smart PASS.
- MedSupplier PASS.
- `check`, `makemigrations --check --dry-run` y `migrate --plan` PASS en los tres.
- Smoke `ISO_SMART` con `--no-fallback` PASS.
- Login real controlado ISO Smart PASS.
- Smoke `MEDSUPPLIER` con `--no-fallback` PASS.
- Prueba negativa controlada PASS.
- `source=adminapps` confirmado.
- `fallback=false` confirmado.
- Sin secretos expuestos.
- Sin bypass.
- Sin produccion publica tocada.

### GO WITH RESTRICTIONS

- Codigo correcto, pero falta host, runner, variables, credenciales o datos para ejecutar toda la matriz.
- Alguna prueba no pudo correrse por restriccion de entorno.
- La restriccion queda documentada claramente.

### NO GO

- ISO Smart permite login sin entitlement.
- ISO Smart emite tokens antes de validar AdminApps.
- Fallback se activa con `--no-fallback`.
- AdminApps responde contrato incorrecto.
- MedSupplier presenta regresion.
- Se detecta bypass.
- Se detectan secretos expuestos.
- Smokes criticos fallan por bug real.
