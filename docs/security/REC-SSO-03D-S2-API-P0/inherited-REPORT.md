# REC-SSO-03D-S2 — Risk-First Authorization Coverage

**Date:** 2026-10-16  
**Scope:** authorized local/offline engineering in AdminApps, ISO Smart, and MedSupplier  
**Verdict:** `DECISION_D_S2_PARTIAL_WITH_EXPLICIT_GAPS`  
**Always:** `PRODUCTION_READY = FALSE` · `NO_DEPLOYMENT` · `NO_COMMIT` · `NO_PUSH` · `GOVERNANCE_PRESERVED`

## A. Executive Verdict

Se cerraron cinco brechas locales P0 del control plane AdminApps, se añadió un hold D para
trials no adjudicados y se verificó la protección efectiva existente de `PlanViewSet`. Las
brechas eran: escritura de settings por cualquier
usuario autenticado; asignación de membresías sin límite de organización/rol y autoedición;
promoción a `superadmin` por un actor `admin`; invitaciones con organización/rol no validados;
y registro con token de invitación no ligado al correo, token inválido aceptado como alta normal
y consumo no transaccional. Se confirmó que un entitlement `trial` no facturado podía recibir
scopes pese a que los derechos/duración del trial están pendientes; ahora Decision D lo retiene
hasta adjudicación.

Después se revisaron ModelAdmins sensibles: se alinearon roles de escritura, se acotaron algunas
operaciones por tenant/actor y se protegieron campos de privilegio y logs. La corrección del
flujo de invitaciones se probó con efectos simulados. **No** demuestra
persistencia, locks reales, HTTP E2E ni comportamiento PostgreSQL. No se implementó cobertura
global del control plane ni se modificaron los handlers críticos pendientes de ISO Smart o
MedSupplier. No se emite `DECISION_D_S2_LOCAL_CRITICAL_COVERAGE_VERIFIED`.

## B. Baseline & Integrity

| Repo | HEAD inicial/final | SHA-256 del índice inicial/final | Estado inicial |
|---|---|---|---|
| AdminApps | `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` | `183cd78b6013f56801465bf8aeb9dd31f746a5bd43389003fcf4383d1e584da3` | Dirty, cambios previos conservados |
| ISO Smart | `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` | `e6def75069870dc31a434d379b14abe9cc7d3cfcdbaa111eb8616af4d435245d` | Dirty, cambios previos conservados |
| MedSupplier | `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` | `cfd4a1341fa59cb5c51acc3c7180121b27aafa392d8027d878f975792d455165` | Dirty, cambios previos conservados |

Los HEAD y hashes del índice coinciden con el baseline heredado. No hay cambios staged. En S2
se modificó código y se añadieron pruebas solo en AdminApps; no se alteró código de ISO Smart ni
MedSupplier. El estado dirty preexistente en los tres repositorios se preservó. `git diff
--check` pasó en los tres repositorios. `manage.py check --settings=config.settings_test` pasó.
Ruff no está instalado (`NOT_EVIDENCED`).

No se aplicaron migraciones, no se usaron servicios/bases compartidos, no se cambiaron secretos
ni configuración activa, y no se ejecutaron workers.
Los parches S2 acotados por repositorio están en `adminapps-s2.diff`,
`isosmart-s2.diff` y `medsupplier-s2.diff`; los dos últimos documentan que no se hicieron cambios
S2 de código en esos repositorios.

## C. Risk-Based Authorization Triage

| Prioridad | Slice revisado | Resultado S2 |
|---|---|---|
| P0 | Settings de organización, roles, membresías e invitaciones | Correcciones locales con pruebas negativas/positivas offline |
| P0 | Planes y mutaciones de catálogo | `PlanViewSet` y mutaciones sensibles de Django Admin revisados; guards probados offline |
| P0 | Clientes/API keys y rutas administrativas no registradas/revisadas | `NOT_EVIDENCED` |
| P1 | ISO Smart leadership/foundation/exports/workflows y objetos compuestos | No modificado; continúan brechas heredadas |
| P1 | MedSupplier relaciones, exports, bulk, approvals y workflows | No modificado; continúan brechas heredadas |
| P2 | Aliases, funciones auxiliares, jobs y rutas legacy | Pendiente de reconciliación funcional |

La matriz [authorization-delta.csv](./authorization-delta.csv) distingue guardas locales nuevas
de la cobertura central D. Ninguna guarda local añadida se reporta como `D_ENFORCED`.
Los fallos pre-fix observados están resumidos en [defect-reproduction.txt](./defect-reproduction.txt).

## D. AdminApps Control Plane

- `OrganizationViewSet.organization_settings`: antes el `PATCH` usaba solo `IsAuthenticated`;
  ahora requiere `IsOrgAdmin`. El objeto sigue acotado por el queryset de organización.
- `UserOrganizationSerializer` y `UserOrganizationViewSet`: valida organización del actor,
  limita roles globales según autoridad y bloquea crear/actualizar/eliminar la propia membresía.
- `UserCreateSerializer`/`UserUpdateSerializer`: un `admin` no puede asignar `superadmin`; el
  actor no puede cambiarse su propio rol.
- `OrganizationInvitationCreateSerializer`: un org admin no puede invitar a otra organización
  ni crear roles globales; `admin` no puede emitir invitación `superadmin`.
- Se conserva el acceso de plataforma de `admin`/`superadmin` donde corresponde; los consumidores
  ISO Smart y MedSupplier siguen requiriendo sus propias pruebas/grants D.

Esto cubre slices seleccionados; no certifica todos los ViewSets de usuarios, organizaciones,
API keys/clientes ni operaciones financieras.

### Django Admin

Los permisos Django por modelo no heredaban los roles de la API. Se alinearon las capacidades
de lectura/escritura de las superficies revisadas: planes, sistemas/productos y estándares ISO
requieren `is_superadmin`; entitlements, módulos, suscripciones, facturas y métodos de pago
requieren `is_admin`. La administración de organizaciones permite altas solo a superadmins,
cambios a admins y no permite borrado; settings, invitaciones y membresías quedan limitadas por
rol y organización. `UserAdmin` limita altas/cambios a `is_org_admin`, acota usuarios al tenant,
impide la autoedición del rol, el cambio de organización en usuarios existentes y la
autoeliminación (también por acciones masivas); reserva `is_staff`/`is_superuser` al Django
superuser y filtra los roles globales por autoridad. Los logs de entitlements/módulos, actividad
de usuario y sesiones son inmutables desde Admin. `IntegrationAPIKeyAdmin` ya denegaba las tres
mutaciones y se mantiene así.

Estas son guardas de AdminApps; `is_superuser` no concede automáticamente acceso a productos
consumidores. No se certificó toda vista administrativa, grants de permisos Django en producción,
ni persistencia/efectos con base de datos real.

La regresión enfocada final ejecutó 29 pruebas de autorización (10 nuevas de Django Admin y 19
previas de usuarios/organizaciones/planes), todas PASS_OFFLINE; `manage.py check` también pasó.

La función D `entitlement_eligible` ahora deniega cualquier entitlement en estado `trial` hasta
que exista política comercial adjudicada. El estado local de autenticación/entitlement no se
reescribió; el hold se aplica en la emisión de scopes D. Un entitlement activo no-trial no
facturado conserva el ALLOW offline previo.

## E. Public/Privileged Endpoint Review

### PlanViewSet

La entrada heredada que indicaba `AllowAny` no refleja la configuración efectiva inspeccionada:

- `list`/`retrieve`: `IsAuthenticated`.
- `create`/`update`/`partial_update`/`destroy`: `IsSuperAdmin`.
- El queryset oculta planes inactivos a usuarios no administradores.
- `featured`/`compare` son GET, pero el `get_permissions()` actual también las restringe a
  `IsSuperAdmin`; no se cambió esa restricción más estricta.
- No hay mutación pública sin gate en el `ModelViewSet` registrado. No se encontraron
  `permission_classes=[]`, decoradores permisivos, ni ruta `AllowAny` para el catálogo en el
  código efectivo.

Se añadieron pruebas de resolución efectiva de permisos; no se cambió la implementación de
`PlanViewSet`. Django `is_superuser` participa en `User.is_superadmin` en AdminApps. Eso no se
propaga como grant de producto: el contrato D y las pruebas de consumidores siguen siendo gates
independientes.

### Registro e invitaciones

`RegisterSerializer` ahora exige invitación pendiente/no expirada, correo coincidente sin
distinción de mayúsculas, y autoridad vigente del invitador para roles globales. La creación del
usuario/membresía y el consumo de invitación se ejecutan dentro de `transaction.atomic()` y
vuelven a validar/leer la invitación con `select_for_update()`. Un token inexistente ya no cae
silenciosamente en registro normal.

## F. ISO Smart Coverage

Sin cambios de código en S2. La suite D existente pasó offline: 361 métodos, además de 36 pruebas
de sesión. Esto verifica solo el alcance de esos harnesses. Permanecen los huecos heredados en
leadership, foundation y function views, exports, acciones compuestas, approvals, bulk,
assistant ownership y persistencia. No se interpreta el resultado de los harnesses como cierre
de esas superficies.

## G. MedSupplier Coverage

Sin cambios de código en S2. La suite D existente pasó offline: 533 métodos, además de 36 pruebas
de sesión. Permanecen sin cierre global las relaciones/ownership persistidas, exports, bulk,
approvals, evidencias, acciones financieras y workflows compuestos. No se restauraron fallbacks
de superuser ni roles locales eliminados por D.

## H. Workflows, Exports & Bulk

No se añadieron exports ni operaciones bulk. Tampoco se habilitaron approvals por jerarquía
inferida. Los workflows críticos de ISO Smart/MedSupplier y los efectos SQL/transaccionales
siguen `NOT_EVIDENCED` o `BLOCKED` según la evidencia heredada.

## I. Functional ALLOW/DENY Tests

| Caso | Evidencia S2 |
|---|---|
| ALLOW | Org admin puede pasar el gate de `PATCH`; miembro puede leer settings |
| ALLOW | Membresía no global en la organización del actor valida |
| ALLOW | Registro con invitación válida, correo coincidente y rol autorizado ejercita el
  serializer, crea usuario/membresía simulados y marca invitación aceptada |
| DENY | Miembro no puede hacer `PATCH`; anónimo no puede leer settings |
| DENY | Membresía de otro tenant, rol global por org admin, y modificación/eliminación propia |
| DENY | `admin` no puede promoverse/promover a `superadmin` ni emitir invitación `superadmin` |
| DENY | Invitación cruzada, email distinto, token inválido/expirado o autoridad insuficiente |
| Planes | Mutaciones denegadas para usuario no-superadmin; permitidas para superadmin |

Los tests de autorización llaman directamente permisos/validadores, no ejecutan todos los
handlers HTTP. El test de registro usa mocks para efectos de negocio y no acredita persistencia.
Clasificación: `PERMISSION_GATE_PASS` para settings/planes; `HANDLER_FUNCTIONAL_PASS_OFFLINE`
con mocks solo para el registro invitado; `PERSISTENCE_NOT_EVIDENCED`;
`HTTP_E2E_NOT_EVIDENCED`.

## J. Coverage Before vs After

El inventario heredado de Decision D conserva 5.893 entradas resolver (759 AdminApps,
2.291 ISO Smart, 2.843 MedSupplier), con 1.955 entradas con gate D probado, 524 con ALLOW/DENY
de lectura/objeto, 1.430 solo DENY y 3.938 sin verificación D. Los números del resolver no son
handlers funcionales únicos.

No se añadieron ni quitaron rutas en S2; el denominador queda igual. Se agregaron 19 pruebas
focalizadas y se probaron seis caminos/políticas de control plane. La cobertura funcional única
global antes/después no se calculó y permanece `NOT_EVIDENCED`; no se presenta como 0 ni como
completa. Los inventarios originales se preservaron como
[endpoint-inventory-inherited.csv](./endpoint-inventory-inherited.csv),
[authorization-matrix-inherited.csv](./authorization-matrix-inherited.csv) y
[object-permission-matrix-inherited.csv](./object-permission-matrix-inherited.csv); la reconciliación
final de esta ejecución es solo el delta de control plane, no un inventario global revisado.
Véase [coverage-comparison.csv](./coverage-comparison.csv).

## K. Historical Regressions

| Suite actual | PASS | FAIL | ERROR |
|---|---:|---:|---:|
| AdminApps control-plane S2 | 19 | 0 | 0 |
| AdminApps Decision D successor | 57 | 0 | 0 |
| ISO Smart Decision D | 361 | 0 | 0 |
| ISO Smart D session | 36 | 0 | 0 |
| MedSupplier Decision D | 533 | 0 | 0 |
| MedSupplier D session | 36 | 0 | 0 |
| AdminApps REC-2FA-04 | 21 | 0 | 0 |
| **Total de estos métodos** | **1063** | **0** | **0** |

Las suites D/session bloquearon DB/red y reportaron cero intentos. La reconciliación de fallos
históricos A/C/H/B original permanece en el reporte heredado; no se repitieron todas las suites
originales en este slice. No hubo cambios frontend.

## L. Commercial Blockers

Los tres HIGH heredados permanecen como decisiones comerciales: trial sin suscripción válida,
`starts_at` futuro y suscripción ligada a otro tenant/principal. S2 extiende el fail-closed D al
trial no facturado no adjudicado; no adjudica derechos, duración ni capacidades, por lo que el
bloqueo comercial sigue abierto. No se adjudicaron paquetes, cuotas, ownership ni overrides.
E/F/G y el estado de migraciones 0008/0009/0010 se preservan.

## M. Acceptance Criteria

| Criterio | Estado S2 | Evidencia/límite |
|---|---|---|
| S2-01 | PARTIAL | Denominadores heredados conservados; inventario funcional global final no reconciliado |
| S2-02 | PARTIAL | Roles/membresías/invitaciones/settings seleccionados, no todo el control plane |
| S2-03 | PASS_OFFLINE | `PlanViewSet` efectivo probado; no se encontró mutación pública |
| S2-04 | NOT_MET | ISO Smart crítico incompleto |
| S2-05 | NOT_MET | MedSupplier crítico incompleto |
| S2-06 | NOT_MET | Exports/bulk funcionales no implementados |
| S2-07 | PARTIAL | Validaciones locales seleccionadas; relaciones persistidas no verificadas |
| S2-08 | PARTIAL | Endpoints y ModelAdmins sensibles seleccionados, no todo el control plane |
| S2-09 | PASS_OFFLINE | ALLOW local seleccionado; registro con efectos simulados |
| S2-10 | PASS_OFFLINE | DENY adversarial local seleccionado |
| S2-11 | PASS_OFFLINE | Sucesores D/B y sesiones actuales pasaron offline |
| S2-12 | PARTIAL | Fronteras cubiertas en suites heredadas; no auditoría integral C/H en S2 |
| S2-13 | PASS_OFFLINE | 21 pruebas REC-2FA-04 |
| S2-14 | PASS | No se adjudicó política; el trial no adjudicado permanece denegado en D |
| S2-15 | PARTIAL | Resolver vs funcional separados; handlers únicos globales no contados |
| S2-16 | PARTIAL | Evidencia histórica conservada; no todas las suites originales repetidas |
| S2-17 | PASS | HEAD e índice intactos; no staged; diffs chequeados |
| S2-18 | PARTIAL | DB/HTTP/Ruff y políticas comerciales externos/no evidenciados |
| S2-19 | PARTIAL | Gaps P0/P1 restantes priorizados abajo |
| S2-20 | PASS_NO_ACTIVATION | No se activó nada; plan heredado de rollout/rollback se mantiene |

## N. Remaining Local Gaps

1. Revisar clientes SSO/API keys y superficies administrativas restantes; probar los flujos
   sensibles con HTTP/Admin E2E y persistencia aislada autorizada.
2. Validar que serializers de User/Invitation/membership y eventos/outbox preserven auditoría y
   efectos bajo transacciones reales.
3. Completar handlers críticos de ISO Smart (leadership/foundation/export/bulk/workflows) y
   MedSupplier (ownership relacional/export/bulk/approvals/finanzas).
4. Reconciliar todos los métodos/aliases del resolver con handlers únicos y casos ALLOW/DENY;
   no asumir que un gate del primer paso prueba el resultado funcional.

## O. External Dependencies

- PostgreSQL autorizado y pruebas de persistencia/locks/rollback; no se conectó ni se aplicaron
  migraciones.
- HTTP/browser E2E y verificación de cookies/CSRF bajo un entorno local aislado.
- Adjudicación comercial de trial, fechas, ownership y cuotas.
- Ruff (no instalado); AST o `diff --check` no se reportan como sustituto.

## P. Next Engineering Slice

Continuar P0 AdminApps sobre API keys/clientes, rutas restantes y flujos transaccionales; agregar
tests positivos/negativos de handler y serializer en harness local sin servicios. Después, P1 ISO Smart exports,
leadership/foundation/workflows y MedSupplier relaciones compuestas, bulk y approvals. Mantener
fail-closed donde falte contrato comercial. Preparar DB/HTTP E2E solo tras autorizar un laboratorio
local aislado. No activar, desplegar ni revertir en este incremento.
