# REC-SSO-03 / Decision D — reporte de implementación local

Mandato: 2026-10-15. Actualización: 2026-10-16 (America/Costa_Rica).
Repositorios del host autorizado 192.168.56.11. Evidencia: `/tmp/rec-sso-03d-kbzx0q7o`.

## A. Executive Verdict

**DECISION_D_PARTIALLY_IMPLEMENTED_WITH_EXPLICIT_BLOCKERS**

Código real implementado en los tres repositorios y **1.022 ejecuciones de métodos D/sucesoras
PASS_OFFLINE**. No equivale a cobertura global: 113 ejecuciones son invariantes B heredadas
por las nuevas clases; hay 909 métodos nuevos. Las pruebas generadas ejercitan la permission
chain de los handlers registrados, pero no sustituyen ejecución SQL/serialización completa.

**PRODUCTION_READY = FALSE. NO_DEPLOYMENT. NO_COMMIT. NO_PUSH. GOVERNANCE_PRESERVED.**

El resultado esperado de implementación completa NO se emite: hay 3.938 entradas del resolver
sin verificación D, workflows/exports/bulk retenidos y políticas comerciales/quotas pendientes.
Una parte de estas brechas requiere más implementación local, no solo dependencias externas.
Se preservan B, A, C/H y MFA. No migraciones aplicadas, consultas a bases compartidas, servicios,
workers, secretos ni configuración activa modificados. La nueva autorización puede denegar
operaciones antes aceptadas: su activación requiere completar y revisar esas políticas.

## B. Initial Git Baseline

| Repositorio | HEAD conservado | Archivos baseline | Entradas Git preexistentes |
|---|---|---:|---:|
| adminapps | `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` | 15656 | 177 |
| isosmart | `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` | 15066 | 47 |
| ISO_Smart_MedSupplier | `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` | 15005 | 24 |

Total: 45.727 archivos tracked/untracked no ignorados. `baseline.json` conserva hash por archivo,
HEAD, hash del índice y estado Git; `*.initial.diff` conserva el estado sobre HEAD antes de D.
`before/<repo>/...` contiene los originales previos de los archivos backend modificados,
incluyendo cambios A/C/H/B o ajenos que ya estaban presentes. No se deshizo ningún cambio previo.
El inventario no representa todos los archivos del host ni configura los servicios desplegados.

## C. Authorization Surface Inventory

Se cargaron los URL resolvers **reales** bajo settings sintéticos, con las listas INSTALLED_APPS
obtenidas por AST, base dummy y conexiones de red/DB bloqueadas. Cero conexiones durante discovery.
Incluye routers, aliases, rutas con format suffix, acciones, function views, APIs y Django admin.
HEAD/OPTIONS y aliases cuentan como entradas separadas; no se confunden con recursos únicos.

| Repositorio | Entradas ruta/método | Patrones distintos | Entradas API | Método no declarado por wrapper |
|---|---:|---:|---:|---:|
| adminapps | 759 | 430 | 436 | 141 |
| isosmart | 2291 | 1166 | 1568 | 286 |
| ISO_Smart_MedSupplier | 2843 | 1415 | 1856 | 416 |

Las 843 entradas UNDECLARED (incluye callbacks admin/manuales) permanecen explícitas: no se
inventan métodos permitidos. `endpoint-inventory.csv` contiene repositorio, ruta, verbo,
handler, producto, principal, recurso, tenant, operación, permisos existentes, política,
estado y prueba. Donde no se completó revisión, el campo lo indica. La enumeración de URLs
está reconciliada; el significado de todas sus políticas NO lo está.

`source-discovery.json` identifica candidatos models/permissions/serializers/views/jobs y
suites que requieren DB. `review-scope.json` distingue revisión manual de secciones, enumeración
automática y exclusiones. `*.resolver.json` conserva los módulos importados por el resolver.
Los roots legacy no montados, static/media DEBUG, proveedores, comandos/cron y workers quedan
fuera de la verificación funcional; no son implícitamente seguros. Outbox B y auto_indexing se
identificaron; no se ejecutaron jobs ni se añadió autorización en tiempo de consumo.

## D. Canonical Scope Contract

`rec-sso-03d-v1`, patrón exacto `PRODUCT:app.model:operation`; 187 scopes ISO_SMART y 292
MEDSUPPLIER. Catálogo idéntico en los tres repositorios y derivado de recursos/acciones reales.
Ejemplo: `ISO_SMART:resources.resource:read`. No comodines ni permisos write transversales.
La pertenencia al catálogo no habilita por sí sola una acción; `action_enabled` es otra restricción.

`authorization` llega por introspección viva, con contract/state/principal_type/sub/tenant/client/
product/role/sid/sg/av/scopes. Se contrasta con la prueba central, perfil local y rol vigente.
No hay scopes de request, grants JWT autoritativos, credenciales de servicio como humanos ni
privilegios globales de admin/superadmin sobre productos. `AUTHORIZATION.openapi.json` documenta
el campo aditivo. TTL 300 s, RSA y contratos A/C/H/B se conservan.

## E. AdminApps Authorization Implementation

Nuevos `backend/apps/integration/authorization.py`, `authorization_contract.py` y
`backend/scripts/rec_sso_03d_offline.py`. Modificados `session_lifecycle.py` y `sso_views.py`.
El nuevo `lifecycle.introspect` verifica B y resuelve grants **dentro del mismo fence**.
Las funciones anteriores de lifecycle se conservan por AST, verificable en lifecycle-integrity.json.
El serializer de entitlement añade elegibilidad D conservadora; un `active: true` de autenticación
puede coexistir con `authorization.state: denied`. No se crean grants persistentes nuevos ni se
cambian migraciones; se reutiliza OrganizationProductEntitlement.scopes y UserOrganization.

56 pruebas D AdminApps finales, incluyendo 43 invariantes B heredadas y 13 nuevas. Se prueban
intersección read/create para viewer, módulos desconocidos, grants ausentes, inyección de
scope/role ignorada, API key sin prueba humana, cambio de entitlement/revocación y políticas
comerciales retenidas. Persistencia/transacciones reales no probadas. El control plane de
roles/productos/entitlements de AdminApps mantiene sus permisos previos: su portado D está pendiente.

## F. RBAC & Entitlement Enforcement

El rol de membresía central limita operaciones; org_admin no supera el entitlement ni el scope
concreto, y admin/superadmin globales no generan grants de producto. MEDSUPPLIER requiere además
asignación local específica como restricción. Un iso_manager no obtiene escritura MedSupplier
por esa etiqueta. Auditor/viewer son lectura. Approve/export no se deducen de jerarquía.

Scopes desconocidos/vacíos/cruzados/duplicados y evidencia inconsistente deniegan. Starts_at
futuro, entitlement/producto/tenant inactivo, override de suscripción ajeno o trial facturado
no producen grants. módulos legacy no mapeados se retienen, sin ignorar esa restricción.
No se adjudican paquetes ni cuotas: documentos/usuarios/almacenamiento necesitan política y
contadores autoritativos. Grupos Django no añaden permisos D; sus invalidaciones B permanecen.

## G. ISO Smart Object-Level Authorization

Modificado `backend/core/organization_scoping.py`; añadidos `integration/authorization.py`,
`authorization_contract.py`, `tests_d_offline.py` y `tests_d_session_offline.py`.
El mixin añade operación a los permisos existentes, tenant autenticado obligatorio, comprobación
de objeto directo/anidado y validación de relaciones/campos sensibles. El serializer no acepta
reparenting; tenant se suministra desde la sesión. No se usa un query parameter como identidad.

361 pruebas D de API/política y 36 de sesión D/B PASS_OFFLINE. Se verifican list/detail propios,
objeto ajeno 404, filtros manipulados, create/PATCH propios y ausencia de save/delete al denegar.
Querysets/persistencia son sustitutos offline; las clases/serializers/dispatch son reales.
CRUD habilitado de forma revisada: Resource; documentos quedan en lectura y stats. Acciones
compuestas, approvals, exports, otras escrituras y assistant quedan retenidos. Leadership,
foundation y varias function views no heredan este mixin: **brecha crítica pendiente**, no cierre.

## H. MedSupplier Object-Level Authorization

Además de los archivos equivalentes ISO, modificados `medsupplier/permissions.py` y `views.py`.
Eliminados bypass superuser y fallback org_admin/iso_manager→supplier_admin. Se validan lados,
roles y cuentas; asignación supplier limitada a cuenta ya no se amplía a toda la organización.
Customers filtran por cuenta y visibilidad; supplier viewer no ve visibilidad privada.
EvidencePackageEntry incorpora lookup de tenant por package. Cockpit filtra cuentas y requiere
permiso financiero además del scope. Dashboard/effective_permissions/private_cockpit/integration_status
comprueban grants antes de consultar datos o servicios, incluyendo todos los recursos del agregado.

533 pruebas D API/política y 36 de sesión D/B PASS_OFFLINE. CRUD revisado adicional: SupplierContact,
con validación de relación y auditoría existente. No se habilitan arbitrariamente aprobaciones ni
exports. MedSupplier conserva Bearer/localStorage. Falta verificar serializers/relaciones persistidas
completas en DB, flujos positivos de cada dominio y revocación ABA de asignaciones locales; ninguna
asignación local puede ampliar la evidencia central, pero no se afirma propagación central de cambios locales.

## I. Commercial Policy Findings

`commercial-policy-blockers.md` registra los tres HIGH y sus fuentes: modelos/views/tests de
products, Organization.subscription, Subscription y Plan. El modelo heredado access_allowed se
conserva; no se ocultan sus fallos históricos. Trials facturados y overrides no canónicos se
retienen en D. Starts_at se aplica como límite de elegibilidad del nuevo grant.

Subscription carece de owner/tenant y puede vincular varias organizaciones; la coincidencia del
FK canónico no resuelve propiedad comercial final. Módulos legacy y cuotas necesitan contrato.
E/F/G permanecen independientes. No se provisionan scopes ni se convierten etiquetas legacy en
privilegios automáticamente. Endpoints anteriores fuera de D siguen siendo un bloqueo.

## J. Adversarial Security Tests

| Suite vigente | Métodos PASS_OFFLINE | FAIL | ERROR |
|---|---:|---:|---:|
| AdminApps D, incluyendo B | 56 | 0 | 0 |
| ISO D API/política | 361 | 0 | 0 |
| ISO D sesión, incluyendo B | 36 | 0 | 0 |
| MedSupplier D API/política | 533 | 0 | 0 |
| MedSupplier D sesión, incluyendo B | 36 | 0 | 0 |
| **D/sucesoras (incluye 113 métodos B repetidos)** | **1022** | **0** | **0** |
| B original AdminApps/ISO/MedSupplier | 43 / 35 / 35 | 0 | 0 |
| REC-2FA-04 original | 21 | 0 | 0 |
| Frontend A/B existentes | 8 / 7 | 0 | 0 |
| Guardrails existentes + CSRF ISO | 8 | 0 | 0 |
| Guardrail existente MedSupplier | 1 | 0 | 0 |

`security-negative-tests.md` y CSV distinguen cada caso, capa y limitación. Pruebas D usan DB
simulada y no consultan red. SessionDTests usa firma RSA y código de validate_session real.
Las denegaciones de acción también pasan por dispatch DRF con handler atrapado: no llega a
persistencia/export/evento. Las pruebas ALLOW de permisos comprueban scopes exactos sin extras.
IDs empresariales probados son numéricos; BOLA empresarial UUID en foundation no está verificado.

Intentos fallidos del harness se conservan: consulta de unicidad no simulada; tenant requerido
por serializer (corregido suministrándolo desde contexto); nombre de helper/guard en suite nueva;
CSRF sin settings de cookies/trust sintéticos. No se alteraron expectativas antiguas. La repetición
con harness completo ejecuta las 3 pruebas CSRF originales con PASS. Sin builds frontend nuevos
porque no hubo cambios frontend; los builds de B siguen siendo evidencia B. Ruff no instalado:
NOT_EVIDENCED; AST y git diff --check no lo sustituyen.

## K. Historical Regression Results

Conteos por **método** (unittest puede reportar más fallos de subtests). Baseline y final coinciden.

| Suite original | Antes P/F/E | Después P/F/E |
|---|---|---|
| REC-SSO-03A AdminApps | 7 / 20 / 3 | 7 / 20 / 3 |
| REC-SSO-03A ISO | 9 / 0 / 11 | 9 / 0 / 11 |
| REC-SSO-03A MedSupplier | 9 / 0 / 11 | 9 / 0 / 11 |
| REC-SSO-02 | 8 / 19 / 5 | 8 / 19 / 5 |
| C/H AdminApps | 2 / 4 / 12 | 2 / 4 / 12 |
| C/H ISO | 17 / 0 / 11 | 17 / 0 / 11 |
| C/H MedSupplier | 17 / 0 / 11 | 17 / 0 / 11 |

`regression-reconciliation.json` compara identidades de métodos y enlaza logs completos. Copias
hash-verificadas en inherited/ preservan las reconciliaciones B de 69 métodos históricos y 38 C/H.
No se modificó ninguna suite original. Las suites DB de recursos/permisos MedSupplier/core/
leadership no se ejecutaron: requieren DB/fixtures fuera de la modalidad sin migraciones. El
inventario source-discovery.json las enumera como BLOCKED_BY_EXTERNAL_DEPENDENCY, no como PASS.
La compatibilidad funcional de todos los casos ALLOW históricos con D sigue NOT_EVIDENCED.

## L. Endpoint Coverage Matrix

| Repositorio | Denominador real | Entradas con gate D y prueba | Lectura permiso+objeto ALLOW/DENY | Solo DENY | Autoridad de grants | Sin verificación D |
|---|---:|---:|---:|---:|---:|---:|
| adminapps | 759 | 1 | 0 | 0 | 1 | 758 |
| isosmart | 2291 | 811 | 212 | 599 | 0 | 1480 |
| ISO_Smart_MedSupplier | 2843 | 1143 | 312 | 831 | 0 | 1700 |

Total: 1.955 entradas con pruebas de gate de 5.893; 524 prueban permiso/objeto read ALLOW/DENY,
1.430 prueban denegación y 1 el resolver central. Estas entradas comparten handlers y NO equivalen
a 1.955 tests independientes. Los cuatro agregados MedSupplier tienen seis entradas GET con aliases.

`authorization-matrix.csv` enlaza cada ruta/acción a permiso y test; `object-permission-matrix.csv`
separa el objeto y lookup aplicable. Para Resource hay pruebas adicionales de list/detail/create/PATCH
completos con ORM simulado. Para el resto, una prueba de permission chain no acredita el cuerpo
completo del handler, serializers, SQL, RLS, efectos ni éxito empresarial. No se afirma cobertura total.

## M. Cross-Product Isolation

La prueba coordinada de B emite con AdminApps real/persistencia simulada y valida en codecs de
ambos consumidores; propios ALLOW, cruzados/LOCAL como CENTRAL/tenant ajeno DENY. SessionDTests
llega desde firma válida hasta gate granular y después deniega write, scopes vacíos y revocación.
El consumidor exige producto fijo y no acepta scopes del otro catálogo aunque la identidad coincida.
MFA, generación, av y sid no se sustituyen por grants. No se hizo HTTP E2E real.

## N. Acceptance Criteria D01–D22

Estados referidos al alcance indicado; los NOT_EVIDENCED impiden el veredicto completo.

| Criterio | Estado | Evidencia / límite |
|---|---|---|
| AC-D01 | NOT_EVIDENCED | Resolver enumerado: 5.893 entradas; semántica completa de métodos/principales/políticas todavía incompleta. |
| AC-D02 | PASS_OFFLINE | Contrato versionado y catálogo cerrado para consumidores; control plane AdminApps no implementado como producto D. |
| AC-D03 | PASS_OFFLINE | Ausentes/desconocidos deniegan en gate D; no equivale a cobertura fuera del gate. |
| AC-D04 | NOT_EVIDENCED | Intersección implementada; módulos legacy retenidos, cuotas y políticas de todos los recursos pendientes. |
| AC-D05 | NOT_EVIDENCED | Binding central/local y objetos probados en slice; hay endpoints fuera de D. |
| AC-D06 | PASS_OFFLINE | Resolver bajo fence B, membresía viva y scopes exactos, sin grants de request/servicio/global admin. |
| AC-D07 | NOT_EVIDENCED | ISO 811 entradas con gate; escrituras y superficies restantes incompletas. |
| AC-D08 | NOT_EVIDENCED | MedSupplier 1.143 entradas con gate, cuentas/visibilidad restringidas; cobertura funcional incompleta. |
| AC-D09 | NOT_EVIDENCED | Adversariales horizontales PASS_OFFLINE en slice; no cierre global. |
| AC-D10 | NOT_EVIDENCED | Escalamiento vertical denegado en slice; control plane y workflows restantes pendientes. |
| AC-D11 | NOT_EVIDENCED | Export/bulk/aprobaciones cubiertos solo por denegación en gate; core.export_data fuera del gate. |
| AC-D12 | PASS_OFFLINE | Enforcement en API/serializer/queryset/objeto; no depende del frontend. |
| AC-D13 | PASS_OFFLINE | B original 43+35+35 verde; funciones previas de lifecycle preservadas; SQL pendiente. |
| AC-D14 | PASS_OFFLINE | C/H con sucesoras B y firma real bidireccional; originales C/H conservan sus fallos. |
| AC-D15 | PASS_OFFLINE | 21 REC-2FA-04 y pruebas CSRF originales; código MFA intacto. |
| AC-D16 | PASS | Tres HIGH documentados; grants retenidos sin adjudicar derechos comerciales/E/F/G. |
| AC-D17 | PASS_OFFLINE | 1.022 ejecuciones de métodos D/sucesoras, cero FAIL/ERROR finales; 113 heredan B. |
| AC-D18 | PASS_OFFLINE | Mismos métodos fallidos A/C/H/02 antes/después; reconciliación B 69+38 conservada. Suites con DB no ejecutadas. |
| AC-D19 | PASS | HEAD/índice/cambios anteriores y archivos fuera del alcance preservados; ver integrity-final.json. |
| AC-D20 | PASS | PostgreSQL/HTTP real/navegador/E2E/activación declarados pendientes. |
| AC-D21 | PASS_OFFLINE | Matriz completa del denominador enumerado con pruebas o NOT_EVIDENCED; no cobertura funcional total. |
| AC-D22 | PASS | Plan escrito con secuencia, condiciones de abortar y reversión selectiva; no ejecutado. |

## O. Governance & Git Integrity

HEAD e índice conservados en los tres repositorios; cero archivos anteriores eliminados.
`integrity-final.json`, `code-hashes.json`, `lifecycle-integrity.json`, `*.decision-d.patch`,
`*.initial.diff` y `*.review.diff` separan D del baseline heredado. Los parches D incluyen nuevos
archivos que git diff habitual omite. Los originales modificados están en before/. Históricos,
MFA, migraciones, settings, financial/foundation y adjudicaciones permanecen intactos.

S3-IMP-01; S3_DECISION_02A_NOT_CLOSED; PHASE31_5 = EXECUTION_HELD; REC-2FA-04;
REC-SSO-02; REC-SSO-03A; REC-SSO-03B-CH y
DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED se preservan. No se declara cerrada
ninguna dependencia durable B ni se altera TTL. No se aplicaron ni crearon migraciones D.

## P. Remaining Blockers

**Locales, críticos:** control plane AdminApps; core.export_data y otras function views;
leadership/foundation y superficies sin mixin; respuestas con recursos compuestos, ownership de
assistant, workflows de aprobación, exports/bulk positivos y política por cada campo/estado;
validación completa de referencias persistidas y serialización; jobs con identidad delegada.
El CSV enumera las rutas concretas no verificadas. No se las considera protegidas por autenticación.

**Comerciales:** trials, propiedad/multi-organización de suscripción, módulos y cuotas; E/F/G.
**Compatibilidad:** mutaciones retenidas cambian conducta previa; los usuarios sin scopes exactos
o con módulos legacy no tendrán acceso a las superficies D. No desactivar D para recuperar acceso.
**Externos:** migraciones B 0008/0009/0010, provisión de clientes/sesiones/fence/grants,
trust por entorno, PostgreSQL transaccional/RLS/concurrencia/rollback, HTTP/E2E y navegadores.
**Herramientas:** Ruff no disponible. No dependencias descargadas.

## Q. PostgreSQL/HTTP/E2E Readiness

**BLOCKED_BY_EXTERNAL_DEPENDENCY**, además de bloqueos locales anteriores. No consultas a bases
compartidas ni migraciones. Las simulaciones no prueban row locks, triggers, RLS ni atomicidad
PostgreSQL. Los tests Django Client en proceso no constituyen HTTP de red ni navegador.
`rollout-rollback-plan.md` define pruebas, secuencia compatible y condiciones para abortar;
la reversión no se ejecutó. B mantiene todas sus pendientes de persistencia/activación.

## R. Next Integration Slice

Completar primero las políticas y sucesoras ALLOW de las rutas NOT_EVIDENCED y retenidas,
priorizando control plane, export/bulk, leadership/foundation y ownership/relaciones compuestas.
La presencia de pruebas DENY no cierra ese trabajo. Después, adjudicar contratos comerciales
sin ampliar privilegios implícitos y preparar laboratorio PostgreSQL/HTTP autorizado.

Reproducción sin settings activos/.env:

```sh
cd /home/felipe/proyectos/adminapps
backend/.venv/bin/python -B backend/scripts/rec_sso_03d_offline.py
backend/.venv/bin/python -B backend/scripts/rec_sso_03b_offline.py
backend/.venv/bin/python -B backend/scripts/rec_sso_02_2fa_regression.py
cd /home/felipe/proyectos/isosmart/backend
.venv/bin/python -B integration/tests_d_offline.py
.venv/bin/python -B integration/tests_d_session_offline.py
cd /home/felipe/proyectos/ISO_Smart_MedSupplier/backend
.venv/bin/python -B integration/tests_d_offline.py
.venv/bin/python -B integration/tests_d_session_offline.py
```

Los comandos/cwd de históricos y frontend están en checks.json. Tooling adicional reproducible:
decision_d_discover.py, decision_d_regressions.py, decision_d_existing.py, decision_d_evidence.py,
decision_d_integrity.py. Los scripts de evidencia contienen el directorio específico de este run.
El reporte/contrato/OpenAPI/plan se copian a docs/security/REC-SSO-03D de AdminApps/MedSupplier y
docs/transformation/REC-SSO-03D de ISO. Todos los cambios exactos por repo están en los parches D
y en integrity-final.json; estas evidencias son la entrega revisable, sin commit/push/despliegue.
