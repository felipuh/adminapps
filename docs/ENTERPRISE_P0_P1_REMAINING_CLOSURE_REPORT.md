# Enterprise P0/P1 Remaining Closure Report - ISO Smart Ecosystem

Fecha: 2026-07-03
Ramas: `hardening/p0-p1-enterprise-readiness` en AdminApps, ISO Smart y MedSupplier
Modo: local/controlado, sin deploy y sin push
Sistemas: AdminApps, ISO Smart, ISO Smart MedSupplier

## 1. Resumen ejecutivo

Demo comercial controlado: GO.
Piloto pagado acotado: GO WITH RESTRICTIONS.
MVP enterprise: preparacion avanzada con restricciones.
Produccion controlada: NO GO hasta entorno final validado.
Produccion regulada/formal: NO GO hasta WORM/SOP/validacion formal.

## 2. Estado actualizado por etapa

| Etapa | Dictamen | Justificacion |
|---|---|---|
| Demo controlado | GO | Checks, migraciones AdminApps, lint/build y suites relevantes pasan localmente. |
| Piloto pagado acotado | GO WITH RESTRICTIONS | Requiere usuarios controlados, CSP, aceptacion temporal de JWT en localStorage y monitoreo de AdminApps. |
| MVP enterprise | Avanzado con restricciones | Contratos y anti-IDOR relevantes existen, pero falta E2E live de tres servicios y hardening final de ambiente. |
| Produccion controlada | NO GO | Falta validar infraestructura final, dominios, TLS, cookies, HSTS/preload y runbooks operativos. |
| Produccion regulada/formal | NO GO | Falta WORM externo, SOPs, matriz de trazabilidad y validacion formal. |

## 3. AdminApps

### 3.1 Migraciones pendientes

Resueltas:

- `products.0003_productentitlementauditlog`
- `billing.0006_productcatalog_system_product`
- `integration.0004_integrationapikey_last_used_at_and_more`

### 3.2 DB controlada verificada

DB configurada: PostgreSQL local `127.0.0.1:5432`, base `adminapps_db`, usuario `adminapps_user`.

`pg_dump --schema-only` no pudo ejecutarse sin password interactiva; no se expusieron credenciales ni se forzo backup.

### 3.3 Resultado migrate

`python manage.py migrate`: OK. Las tres migraciones quedaron aplicadas.

### 3.4 Resultado showmigrations

`showmigrations --plan`: sin migraciones pendientes.

### 3.5 Anti-IDOR

Cobertura relevante en suites existentes de organizaciones, usuarios, productos, entitlements, billing, integration API keys y serializer exposure guardrails.

### 3.6 Contract tests

`apps.integration.tests.IntegrationContractTests` valida API key, entitlement activo, entitlement ausente, entitlement suspendido y rechazo con API key invalida.

### 3.7 Riesgos restantes

JWT en `localStorage` sigue siendo riesgo aceptable solo para piloto controlado. WORM formal fuera de alcance.

## 4. ISO Smart

### 4.1 Deploy warnings

`check --deploy` pasa con variables simuladas seguras y `SECURE_HSTS_PRELOAD=true`.

### 4.2 Fallback production guard

`core.tests_security_guardrails.LocalBypassGuardrailTests` valida que fallback local no opera en produccion y requiere flag explicito en desarrollo.

### 4.3 Anti-IDOR

Suites `core.tests`, `core.tests_asb_spm` y guardrails cubren scoping por organizacion, retrieve/list/update negativos y endpoints sensibles.

### 4.4 Contract tests

Validacion por cliente AdminApps y fail-closed documentada en `docs/CONTRACT_TESTING.md`.

### 4.5 Riesgos restantes

Falta E2E live con AdminApps real levantado y seed de entitlement final.

## 5. MedSupplier

### 5.1 E-signature

Suites existentes cubren firma sensible y bloqueo cross-tenant.

### 5.2 Audit hash chain

Hash-chain local existe como tamper-evidence, no como WORM.

### 5.3 Anti-IDOR/account scoping

`medsupplier.tests` cubre supplier/customer scoping, privados, evidence package y cross-tenant.

### 5.4 WORM/regulatory gap

Documentado en `docs/compliance/REGULATED_PRODUCTION_GAP_ANALYSIS.md` y `docs/compliance/WORM_APPEND_ONLY_PLAN.md`.

### 5.5 Riesgos restantes

Se corrigio fallback local de organizaciones/usuarios/modulos para fallar cerrado si no hay flag demo/desarrollo y nunca en produccion.

## 6. Frontends

### 6.1 Token handling

JWT sigue en `localStorage`; documentado como restriccion de piloto.

### 6.2 Logout/refresh

Los frontends limpian tokens en logout/fallo de refresh en los flujos revisados.

### 6.3 CSP/documentacion

`docs/FRONTEND_AUTH_SECURITY.md` incluye CSP recomendada y plan de migracion a cookies HttpOnly.

### 6.4 Lint/build

AdminApps, ISO Smart y MedSupplier: `npm run lint && npm run build` OK.

## 7. Evidencia QA

| Sistema | Comando | Resultado | Observacion |
|---|---|---|---|
| AdminApps backend | `python manage.py check` | OK | DB local configurada. |
| AdminApps backend | `check --deploy` con variables seguras | OK | HSTS preload simulado explicitamente. |
| AdminApps backend | `makemigrations --check --dry-run` | OK | No changes detected. |
| AdminApps backend | `DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test apps.integration apps.api apps.products apps.billing apps.users` | OK | 167 tests. |
| AdminApps frontend | `npm run lint && npm run build` | OK | Build Vite OK. |
| ISO Smart backend | `python manage.py check` | OK | Sin migraciones pendientes. |
| ISO Smart backend | `check --deploy` con variables seguras | OK | HSTS preload simulado explicitamente. |
| ISO Smart backend | `DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test core.tests_security_guardrails core.tests core.tests_asb_spm integration.tests` | OK | 73 tests. |
| ISO Smart frontend | `npm run lint && npm run build` | OK | Build Vite OK. |
| MedSupplier backend | `python manage.py check` | OK | Sin migraciones pendientes. |
| MedSupplier backend | `check --deploy` con variables seguras | OK | HSTS preload simulado explicitamente. |
| MedSupplier backend | `DJANGO_SETTINGS_MODULE=backend.settings_test python manage.py test medsupplier.tests medsupplier.tests_security_guardrails` | OK | 55 tests. |
| MedSupplier frontend | `npm run lint && npm run build` | OK | Build Vite OK. |

## 8. Riesgos cerrados

| Riesgo | Sistema | Evidencia |
|---|---|---|
| Migraciones AdminApps pendientes | AdminApps | `showmigrations --plan` sin `[ ]`; migraciones aplicadas. |
| `check --deploy` TLS/cookies/HSTS | Todos | Pasa con variables simuladas seguras. |
| Fallback local identidad en MedSupplier | MedSupplier | `MedSupplierAdminAppsClientTests` nuevos. |
| Contrato entitlement producto-neutral | AdminApps/Products | `IntegrationContractTests`. |

## 9. Riesgos pendientes

| Riesgo | Severidad | Bloquea demo | Bloquea piloto | Bloquea produccion | Recomendacion |
|---|---|---|---|---|---|
| JWT en `localStorage` | Media | No | No, con restriccion | Si | Migrar a cookies HttpOnly + CSRF. |
| E2E live tres servicios | Media | No | No, con smoke previo | Si | Levantar ambiente staging y ejecutar contrato real. |
| WORM externo ausente | Alta regulada | No | No | Si regulada | Implementar almacenamiento inmutable y SOPs. |
| Validacion formal/SOPs | Alta regulada | No | No | Si regulada | Crear paquete de validacion y trazabilidad. |

## 10. Git final

Archivos nuevos/modificados esperados:

- AdminApps docs de cierre/seguridad/contratos/auth/compliance.
- ISO Smart `backend/.env.production.example`.
- MedSupplier `backend/.env.production.example`.
- MedSupplier `backend/integration/client.py`.
- MedSupplier `backend/medsupplier/tests.py`.

## 11. Dictamen final honesto

Se puede hacer demo comercial controlada y piloto pagado acotado con restricciones explicitas. No declarar produccion controlada hasta validar entorno final. No declarar produccion regulada/formal.
