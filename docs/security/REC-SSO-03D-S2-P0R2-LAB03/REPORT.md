# REC-SSO-03D-S2-P0R2-LAB03 — Runtime compatibility and least privilege

Fecha: 2026-10-20, America/Costa_Rica. Repositorio: `/home/felipe/proyectos/adminapps`.

## A. Executive Verdict

**`P0R2_LAB03_PARTIAL_WITH_EXPLICIT_BLOCKERS`**. El perfil SQL de LAB02 mantiene la revocación durable y permite los ciclos humanos, MFA, registro mediante invitación existente, alta/desactivación de usuarios, membresías y partes de Decision B. **No es compatible con todo AdminApps**: peticiones autorizadas y con serializer real fallan por `42501` al crear/suspender organizaciones, cambiar settings, crear invitaciones, escribir catálogo/planes/entitlements y abrir el índice de Django Admin. Facturas y billing también carecen de SELECT runtime. No se concedió ningún privilegio nuevo.

```text
PRODUCTION_READY = FALSE
ACTIVE_AUTHENTICATOR_UNCHANGED
NO_DEPLOYMENT
NO_COMMIT
NO_PUSH
GOVERNANCE_PRESERVED
```

Dos correcciones locales de rutas hacen alcanzables los handlers de invitaciones, facturas y métodos de pago. Son independientes de las ACL. No se activaron las siete migraciones `financial` ni se probaron los consumidores de los tres productos, workers o servicios externos.

## B. Baseline & Git Integrity

HEAD inicial y final: `b144b2505659ad39f756b9bc4530a7f24fe8c3ad`. Índice Git intacto. El estado inicial, que ya contenía modificaciones y archivos no rastreados históricos, se guardó en [git-status-before.txt](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/git-status-before.txt). Se comprobó `SHA256SUMS` completo de LAB01 y LAB02: ambos `0` errores. Se recuperaron informes LAB01, LAB02, P0R2 y R1, contrato SQL, instalador y migraciones 0005/0006. Los cuatro archivos de contrato/migración conservan los hashes de [baseline-hashes.json](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/baseline-hashes.json).

La comparación de los **15.816 archivos preexistentes** inventariados por LAB02 no detectó ausentes; antes del segundo arreglo, solo `organizations/urls.py` difería. La comprobación final se repite después de ambos cambios en la sección P. No se tocaron settings activos, secretos, migraciones históricas ni contratos comerciales.

## C. PostgreSQL Lab Isolation

Cluster PostgreSQL 18 nuevo en `/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/runtime`, directorio 0700, socket Unix privado, puerto identificador 56433, `listen_addresses=''`, sin TCP, `inet_server_addr() IS NULL`, sin sudo/root, contenedores, volumen compartido ni servicio anterior. Base vacía `lab03_human`; roles exclusivos `lab03_bootstrap`, `lab03_maintenance` NOLOGIN y `lab03_app` LOGIN/SCRAM sin propiedad ni membresías. Credenciales sintéticas 0600; firma JWT y datos de prueba efímeros. El bootstrap solo creó el cluster/roles y preparó fixtures administrativos separadamente; las peticiones HTTP y servicios de aceptación corrieron con `current_user=lab03_app`.

Se aplicaron 60 migraciones: 57 del grafo IAM LAB02 y 3 de `django.contrib.admin` necesarias para verificar Admin. **0 migraciones `financial`**. `check` y `makemigrations --check --dry-run` pasaron. El instalador LAB02 se aplicó después de las migraciones y de nuevo tras crear `django_admin_log`, sin conceder acceso automático a esa tabla. [Manifiesto](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/resource-manifest.json), [aislamiento](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/isolation-initial.json), [migraciones](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/applied-migrations.txt).

## D. Effective Runtime SQL Privileges

El catálogo observa 52 tablas. [Matriz efectiva por tabla](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/table-privileges.csv), [ACL por columna](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/column-acl.csv), [secuencias](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/sequence-acl.csv), [catálogo resumido](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/catalog-summary.json).

| Permiso efectivo | Tablas representativas |
|---|---|
| `SELECT/INSERT/UPDATE` | `users`, `user_sessions`, `user_organizations`, MFA, `sso_sessions` |
| `SELECT/INSERT` | `user_activity_logs`, `two_factor_auth_logs`, `sso_revocation_outbox` |
| `SELECT/UPDATE` | `organization_invitations` |
| `SELECT` | organizaciones, settings, productos, planes, suscripciones, entitlements, API keys, permisos Django |
| `SELECT` y `UPDATE(generation,authority_epoch)` | `sso_security_fence` |
| `SELECT/INSERT/UPDATE/DELETE` | Solo `django_session` |
| Ninguno | `django_admin_log`, `tenant_integration_outbox`, facturas, billing, módulos, auditoría de productos/API key y demás no enumeradas |

No hay DELETE/TRUNCATE sobre sesiones humanas/centrales, fence u outbox. No hay membresía runtime, CREATE/TEMP ni roles indirectos; los ocho triggers de retención siguen activos. Secuencias solo reciben USAGE cuando corresponden a INSERT permitido; `django_admin_log_id_seq` no lo tiene. Una tabla con `UPDATE` de columnas, como fence, puede aparecer sin UPDATE de tabla en el CSV; la ACL de columna documenta el permiso preciso. El instalador no concede privilegios futuros por defecto.

## E. AdminApps Module Compatibility Matrix

La [matriz por módulo, acción y tabla](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/action-matrix.csv) distingue SQL requerido, realmente concedido, transacciones, bulk, triggers, secuencias y estado funcional. Clases: **A** operación legítima verificada, **B** legítima bloqueada por SQL, **C** denegación deliberada de autoridad/retención, **D** gobernanza comercial o financiera retenida. `A/B` significa que la lectura se verificó y la escritura falló. Un requisito derivado del código sin ejecución se marca allí como tal; no se convierte en PASS.

| Módulo y acción | Tablas clave | Resultado runtime |
|---|---|---|
| Login, refresh, revocación y MFA | `users`, `user_sessions`, tablas MFA, logs | A: HTTP y escritura reales; 17 regresiones PASS |
| Registro con invitación existente | `users`, `user_organizations`, `organization_invitations` | A: registro y consumo reales |
| Usuarios: alta, rol, disable | `users`, `user_organizations`, sesiones | A: 201/200; trigger revoca credenciales |
| Usuarios/membresías: DELETE físico | `users`, `user_sessions`, `user_organizations` | C: `42501`; no elevar permisos |
| Organización: crear/suspender, settings | `organizations`, `organization_settings`, `tenant_integration_outbox` | B: `42501`; la transacción de evento requiere grants adicionales revisados |
| Invitaciones: listar/crear | `organization_invitations` | A/B: GET 200; POST `42501` después del arreglo de ruta |
| Productos/planes/entitlements | `product_systems`, `plans`, `organization_product_entitlements`, logs | A/B: lecturas 200; escrituras `42501` |
| Suscripciones, facturas, billing | `subscriptions`, `invoices`, `billing_*` | A/D: lista de suscripciones 200; factura/billing `42501`; mutaciones retenidas |
| Django Admin/cookie | `django_session`, `django_admin_log`, tablas de recursos | A/B: form login 302, SessionAuth 200, changelist usuarios 200; índice `42501` |
| API keys/grants técnicos | `integration_api_keys`, audit events, configuración de grants | SELECT permitido; rotación, auditoría y consumidores NOT_EVIDENCED |
| Outbox y auditoría | `sso_revocation_outbox`, `tenant_integration_outbox`, logs | B funciona para revocación; entrega, tenant outbox y otros logs bloqueados/no ejecutados |

## F. Functional ALLOW Evidence

Con conexión runtime y cliente Django real: bearer autorizado 200; listados de usuarios/membresías/productos/planes/suscripciones/actividad 200; usuario nuevo 201; desactivación y cambio de rol 200; membresía nueva 201; invitaciones GET 200; Django Admin login con formulario 302, changelist de usuarios 200 y `SessionAuthentication` sobre `/probe/` 200. Los serializers reales validaron alta y cambios. Las 17 pruebas seleccionadas de LAB02 volvieron a pasar sobre PostgreSQL: login/refresh/logout, MFA TOTP y backup, registro, guardas, rollback, carreras SQL, separación humana/B y revocación B. [Peticiones iniciales](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/compatibility-results.json), [rutas/Admin](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/focused-results.json), [membresías/permisos](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/more-results.json), [regresiones](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/functional-results.json).

Un 403 inicial para listar planes con un administrador no superuser se debió a que el setup directo de migraciones no había generado el fixture `view_plan`. Se creó el permiso **como mantenimiento**, se asignó explícitamente y la misma lectura pasó HTTP 200 con runtime. No se clasificó ese 403 como defecto SQL ni se concedieron grants.

## G. Adversarial DENY Evidence

Tenant ajeno: detalle de usuario/settings 404; invitación o membresía ajena 400 por serializer; intento `is_superuser` 400; viewer al crear invitación 403; bearer humano con `X-API-Key` técnico 403; JWT revocado 401 sin ejecutar handler. El DELETE de organización responde 405 explícito por contrato. DELETE de usuario/membresía y SQL DELETE/TRUNCATE sobre autoridad protegida fallaron con `42501`, distinguibles de 400/403/404/405 de la aplicación. [Denegación técnica](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/technical-deny.json), [seguridad SQL](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/security-update.json).

No se probó en este laboratorio cada estado comercial prohibido ni cada relación manipulable. En particular, no se considera que la denegación SQL accidental valide una política comercial.

## H. SQL Permission Conflicts

Errores HTTP autorizados del cliente real y causa SQL `42501`: `organization_settings` UPDATE, `organizations` INSERT/UPDATE, `product_systems` INSERT, `organization_product_entitlements` UPDATE, `plans` INSERT, `organization_invitations` INSERT, `user_organizations` DELETE, `django_admin_log` SELECT, `invoices` SELECT y `billing_products` SELECT. El DELETE ORM de usuario intentó primero `django_admin_log` y falló; aunque se diera ese permiso, el borrado de `user_sessions` seguiría prohibido. No se infirió una solución a partir del primer error de una cascada.

Falta además SQL para `tenant_integration_outbox` (lectura de versión e INSERT transaccional), logs de entitlements/módulos, gestión de permisos Django y tareas de integración. Dar DML general a estas tablas ampliaría la superficie de un runtime comprometido; no se realizó. Crear organizaciones exige evaluar evento/serialización/versionado, no solo conceder INSERT a `organizations`. Las rutas comerciales/financieras requieren adjudicación propia.

## I. Corrections Implemented

- `organizations/urls.py`: registra `invitations` antes de la ruta raíz. Antes, `/api/organizations/invitations/` terminaba en `OrganizationViewSet` y 403 «operación sin política»; después llega al serializer correcto, GET 200 y POST autorizado revela su `42501` real.
- `subscriptions/urls.py`: registra `invoices` y `payment-methods` antes de la ruta raíz. Antes, `/api/subscriptions/invoices/` daba 404 de detalle de suscripción; después llega a `InvoiceViewSet` y revela `42501` sobre `invoices`.
- Dos tests de resolución de URL (3 métodos) pasan con settings aislados, también después de eliminar el cluster. [Log](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/route-tests.log). `git diff --check` pasa.

No se cambió el SQL, modelos, migraciones, settings activos, permisos efectivos ni semántica de facturación. No se implementó una ampliación provisional del perfil de LAB02 porque la compatibilidad completa exigiría varias decisiones de autoridad y gobernanza.

## J. LAB02 Security Regression

Después de los dos cambios de rutas: sesión humana 200 → revocación 401 → DELETE/reinsert `42501` → conexión nueva 401 → refresh antiguo DENY. UPDATE para reactivar, mover familia o retroceder generación: `P0001`; DELETE/TRUNCATE de autoridad, INSERT fence y DELETE outbox: `42501`; `human_auth_version=0` conservó versión efectiva 1. Reinicio **solo del cluster descartable** y mismo JWT original: 401, handler delta 0; hash SHA256 idéntico `35b5f590257953b7d453509c3dd62b2b4fab072b9a8ee1c4e23c8bf0c9d3b8a4`. [Aceptación](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/acceptance-fixed.json), [UPDATE adversarial](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/security-update.json), [reinicio](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/acceptance-restart.json).

## K. Decision B Compatibility

Los tests seleccionados repitieron revocación B idempotente, outbox único, rollback conjunto con revocación humana y dos órdenes de carrera con locks SQL. Los triggers B y retención permanecen instalados. Clientes/productos/tenants necesarios para fixtures se prepararon como mantenimiento y se restableció `lab03_app` antes del servicio probado. Workers, entrega del outbox, grants técnicos en consumidores y los tres productos permanecen NOT_EVIDENCED.

## L. Historical Regression Results

LAB01 y LAB02 conservan sus `SHA256SUMS` sin errores. LAB02 histórico: 23/23 métodos SQL PASS y perfil SQL verificado. LAB03 ejecutó nuevamente **17/17** métodos funcionales seleccionados más **3/3** tests nuevos de resolución de URL; no se reclasificaron los 9 FAIL/1 ERROR de las 241 pruebas históricas LAB01 ni se repitieron sus diez suites completas. P0R2/R1 y Decision D siguen como evidencia heredada offline; no se atribuye a LAB03 su ejecución. Las verificaciones nuevas de Decision B se limitan a los casos descritos en K.

## M. Unverified Financial/Commercial Surfaces

`financial` tiene 0 migraciones aplicadas. `invoices` y `billing_*` existentes en el grafo IAM carecen incluso de SELECT runtime; lista de facturas y resumen billing fallaron `42501`. No se probaron altas/pagos, trials, cuotas, precios, ownership ni retención fiscal. Se clasifican **D: gobernanza retenida**, no defectos a corregir con grants automáticos. No se activaron workers ni se modificaron contratos financieros.

## N. Remaining Blockers

1. Decidir si AdminApps seguirá como monolito con perfiles separados o si IAM correrá en base/servicio dedicado. El script LAB02 exige base dedicada y rechaza objetos financieros, por lo que **no puede instalarse sin más** en una base del monolito completo.
2. Diseñar y probar permisos mínimos por tabla/columna para control plane, eventos tenant, audit logs y secuencias, conservando un rol IAM incapaz de reconstruir sesiones revocadas. Volver a ejecutar matriz ALLOW/DENY y regresión de revocación tras cada cambio.
3. Sustituir el borrado físico de usuarios/membresías por desactivación/retención o declarar 405 explícito tras decidir el contrato de API. El endpoint actual de DELETE llega a SQL `42501`; no se debe permitir DELETE/TRUNCATE de autoridad para hacerlo pasar.
4. Revisar Django Admin y sus escrituras de `django_admin_log`, permisos M2M y recursos comerciales bajo un perfil administrativo separado. El índice actual falla `42501`.
5. Resolver política de outbox, delivery y retención; validar grants técnicos y consumidores. Finance/comercial requiere adjudicación aparte.

## O. Operational Activation Dependencies

Cualquier activación futura requiere autorización del destino concreto, revisión de datos/backup/restauración, perfiles IAM/control plane/mantenimiento separados, instalación segura de migraciones y ACL, pruebas de endpoints/consumers y cambio coordinado del autenticador con emisores/refresh/revocación según R1. Ninguno de estos pasos se ejecutó aquí. `S3-IMP-01`, `S3_DECISION_02A_NOT_CLOSED`, `PHASE31_5 = EXECUTION_HELD`, `REC-2FA-04`, `REC-SSO-03A`, `REC-SSO-03B-CH` y `DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED` permanecen preservados.

## P. Cleanup & Evidence Integrity

El runtime se elimina solo después de validar manifiesto, `data_directory`, socket/ausencia TCP y PID propios. Se conservan únicamente evidencias sanitizadas, CSV, logs, hashes y diff atribuible. [Limpieza](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/cleanup-result.json), [integridad final](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/integrity-final.json), [hashes](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/SHA256SUMS), [diff](/tmp/rec-sso-03d-s2-p0r2-lab03-20261020-1/attributable.patch).

| Criterio | Estado |
|---|---|
| LAB03-01, 07, 08 | PASS — perfil, prohibiciones y catálogo preservados |
| LAB03-02, 05 | PASS — matrices y conflictos clasificados |
| LAB03-03, 04 | PARTIAL — funciones seleccionadas y denegaciones probadas; resto NOT_EVIDENCED |
| LAB03-06 | PASS para dos fallas de rutas; grants/control plane pendientes |
| LAB03-09, 10 | PASS — misma credencial revocada 401 tras reconexión/reinicio |
| LAB03-11, 12 | PASS para casos B/MFA/login seleccionados; consumidores NOT_EVIDENCED |
| LAB03-13 | PARTIAL — Admin revisado; índice bloqueado por SQL |
| LAB03-14 | PASS — cero migraciones financieras |
| LAB03-15, 16 | PASS — Git/índice intactos y limpieza propia verificada |
