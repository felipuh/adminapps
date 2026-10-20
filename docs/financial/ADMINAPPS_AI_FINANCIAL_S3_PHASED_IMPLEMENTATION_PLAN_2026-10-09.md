# S3 — Phased Implementation Plan

Fecha de preparación: 2026-10-09, America/Costa_Rica.
**PLAN PROPUESTO — implementación, runtime y cierre PENDING.**
**S3_DECISION_02A_NOT_CLOSED**. No slice se inicia por publicar este documento.

## Secuencia y dependencias

Fuentes/hash: [registro](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md#source-integrity); decisiones y pruebas:
[matriz humana](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md); permisos: [gates](ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md).
Todos los cambios aquí descritos son futuros. No se crean archivos de producto,
pruebas ejecutables, migraciones, cuentas, sockets ni unidades en esta tarea.

```text
AJ-G01 + decisiones aplicables + permiso escrito de implementación
  → S3-IMP-01 → S3-IMP-02 → S3-IMP-03
  → S3-IMP-04 → S3-IMP-05 → S3-IMP-06
  → revisión de patch/harness, hashes y runbooks concretos
  → permiso PG + provisión OS acotada si peer requiere UIDs
  → S3-VAL-01
  → permiso IPC/host (y PG si integra DB)
  → S3-VAL-02
  → S3-CLOSE-01 con aceptación humana de evidencia
```

La salida de un IMP es un patch revisado y evidencia offline; **no** es PASS
runtime. Por ello IMP-05 no depende de una DB en ejecución y no se crea un ciclo
con VAL-01. Las pruebas con sockets, procesos de servicio, autenticación OS o PG
son runtime incluso si se llaman unitarias. Permanecen en VAL con permiso propio.
AJ-H01 puede continuar por vía documental; su aceptación no reemplaza ninguna
validación técnica. Cada sucesor requiere revisión de la salida anterior y de
las decisiones que le aplican, sin ampliar automáticamente el permiso.

## S3-IMP-01 — Cryptographic JSON strictness y binding

- **Dependencias y autorizaciones:** AJ-G01, AJ-C01/C02 y NUM-C01/C02 resueltos;
  permiso local que delimite parser, esquema, binding y pruebas offline.
- **Archivos previsibles:** `backend/apps/financial/capabilities.py`,
  `executor.py`, `services.py`; `backend/scripts/tests/test_s3_capability_offline.py`
  y tests financieros pertinentes. Módulo de validación nuevo solo si revisión
  justifica reutilización; nombre no decidido. Sin migraciones en este slice.
- **Cambios mínimos:** detección de duplicados por clave decodificada, wire
  exacto y base64url estricto; tipos/rangos aprobados, errores tipados; comparación
  assertion↔organization y entorno/operación antes de conexión. Conservar bytes
  firmados y material normal. Definir validación reutilizable para futuro issuer.
- **Invariantes:** 19 claims D02, Ed25519/dominio vigentes, jti estable; ningún
  efecto/conexión DB ante fallo crypto/material. No añadir correlation_id firmado
  ni adoptar claims A02. Tipos bool no sustituyen enteros.
- **Pruebas obligatorias:** CR-T01–06 y MT-T01–03 con fixtures/vectores fijos,
  errores de tamaño/profundidad aprobados, doble contador DB y consumidores
  inventariados. Rechazar orden/whitespace/escapes alternativos y todas las
  posiciones de duplicado. No repetir pruebas host ni ejecutar Django con DB.
- **Evidencia requerida:** diff y SHA, perfil aprobado, inventario de consumidores,
  bytes/vector/hash compatibles, esperado/observado por caso, contador DB cero
  en negativos; referencia separada a las dos sondas históricas sin editarlas.
- **Rollback:** retirar solo el patch del slice en copia aislada; conservar
  baseline y resultados. No reactivar operación ni cambiar fixtures históricos
  para ocultar regresión. Incompatibilidad obliga a revisar contrato/versionado.
- **Aceptación:** positivos del emisor actual sobreviven; negativos acotados y
  tipados; aprobación de compatibilidad por protocolo/financiero. Runtime sigue pendiente.
- **STOP:** perfil incompleto, cambio de M(C)/hash, consumidor discrepante,
  excepción no controlada o intento de conexión durante prueba offline.
- **Riesgos residuales:** clave/issuer confiados; igualdad tenant no prueba la
  procedencia de TenantProjection ni autorización de integración externa.

## S3-IMP-02 — PostgreSQL ownership y matriz de privilegios

- **Dependencias y autorizaciones:** salida IMP-01 revisada; AJ-P01/P04/P05/P08
  y diseño de lecturas issuer AJ-P02 aprobados. Permiso para preparar migración
  posterior y matrices SQL, sin aplicarlas ni consultar catálogo vivo.
- **Archivos previsibles:** nueva migración posterior a `0007` en
  `backend/apps/financial/migrations/` (número/nombre tras revisar historial),
  tests de migraciones/ACL y manifest de objetos del futuro harness. `models.py`
  solo si el diseño aprobado requiere estado Django; ownership puro no lo exige.
- **Cambios mínimos:** ownership explícito; precondiciones de roles/dueños;
  allow-list por objeto/creador, schema/defaults, funciones auxiliares y ruta de
  administración bajo FORCE RLS. Preparar políticas de lectura issuer mínimas
  como parte del diseño, con provisión efectiva en IMP-03/VAL-01.
- **Invariantes:** 15 tablas migration-owned; admission dueño de funciones,
  executor LOGIN solo wrapper, runtime sin admisión directa. FORCE RLS/triggers
  permanecen. No reescribir 0002–0007, usar BYPASSRLS o reparar catálogo durante test.
- **Pruebas obligatorias:** revisión estática de DDL/ACL/owner y matriz completa;
  pruebas offline de precondiciones con dobles. Diseñar PG-T02–06; ejecución real
  solo en VAL-01. No sustituir PostgreSQL por SQLite como prueba RLS.
- **Evidencia requerida:** matriz por tabla/función/schema/database/defaults y
  creador, relaciones de roles, diff/SHA y estrategia correctiva elegida. Cualquier
  referencia a catálogo debe marcarse todavía NOT_RUN.
- **Rollback:** antes de aplicar, descartar solo patch propio. Después de aplicación
  futura, deshabilitar acceso del slice y preparar corrección revisada; no restaurar
  owner inseguro ni ejecutar reverse que retire FORCE/triggers o borre historia.
  Clúster sintético solo se elimina mediante teardown autorizado y verificado.
- **Aceptación:** SQL preparado concuerda con D02, matriz cubre objetos auxiliares
  y consultas reales del issuer, sin grants implícitos; revisión DBA/seguridad.
- **STOP:** owner/estado de migraciones desconocido sin estrategia, grant amplio
  para pasar test, admin como runtime o cambio de política sin acta.
- **Riesgos residuales:** catálogo efectivo, default ACL y memberships solo se
  demostrarán en VAL-01; control plane migration permanece confiado.

## S3-IMP-03 — Identidades y autenticación independientes

- **Dependencias y autorizaciones:** IMP-02 revisado; AJ-P02/P03/P08, B-D01 y
  NUM-I03 resueltos. Elegir peer o SCRAM, map por principal, topología, lectura
  issuer y ruta administrativa. Permiso local de código/configuración sintética;
  creación de roles/cuentas/servicios todavía excluida.
- **Archivos previsibles:** `issuer.py`, `authorization.py`, constructor/configuración
  exclusiva de `executor.py`, adaptador financiero de lectura de credencial y
  plantillas del harness. `backend/apps/integration/services.py` y `models.py`
  son fuentes de contrato, **no** destinos por defecto de un refactor compartido;
  tocar esas rutas exigiría ampliar expresamente el permiso y revisar consumidores.
- **Cambios mínimos:** issuer usa alias y consulta mínima dedicada a hashed_v1
  registrado; no selecciona plaintext legacy ni fallback general. Separar DB
  issuer/executor/seed/inspector; preparar HBA/map, sin secretos reales. No
  introducir private key en settings generales ni credencial executor en runtime.
- **Invariantes:** executor LOGIN D02; issuer no admisión/escritura de grants;
  proyección mínima de columnas no dispara cargas ORM diferidas de campos excluidos.
  Control de revocación de grants usa principal administrativo separado de issuer.
- **Pruebas obligatorias:** offline con dobles y revisión de consultas/routing;
  credencial dedicada positiva, genérica/legacy/revocada negativas. Diseñar
  PG-T01/02/05/10, credencial errónea en SCRAM o UID/mapping erróneo en peer;
  aislamiento real y UIDs distintos solo en VAL con permiso OS explícito.
- **Evidencia requerida:** matriz principal→UID→rol→objeto/columnas, configuración
  sin valores secretos, consultas ORM previstas, inexistencia de fallback general,
  SHA y lista de operaciones OS/DB que requerirá el runbook posterior.
- **Rollback:** retirar adaptador/plantillas propias sin introducir fallback admin.
  Material sintético futuro se retira según permiso y política de sesiones; no
  rotar credenciales reales ni reutilizar identidades históricas.
- **Aceptación:** contrato de acceso y configuración deterministas revisados;
  data directory privado separado del socket y positivos de acceso planificados;
  ninguna identidad declarada provisionada desde un nombre en plantilla.
- **STOP:** B-P01/B-D01, shared UID/DSN, acceso a `.env`, SELECT amplio o routing
  ambiguo que pudiera usar conexión general. Cambio de mecanismo requiere nueva acta.
- **Riesgos residuales:** proyección/alias correctos offline no prueban DAC ni auth
  DB; custodia real de claves y separación entre procesos siguen pendientes.

## S3-IMP-04 — SERIALIZABLE, concurrencia, replay y recuperación

- **Dependencias y autorizaciones:** IMP-03 revisado; AJ-P06/P07/P09 e intención
  AJ-I04, NUM-P01/P02 aprobados. Permiso local de transacción, lifecycle/ledger y
  pruebas; recuperación limitada al comportamiento fail-closed y diseño de lab.
- **Archivos previsibles:** `executor.py`, `issuer.py` (transición administrativa
  de grant), `models.py`/migración posterior si se aprueba enlace ledger,
  tests financieros/harness; `services.py` solo para asegurar invariantes compartidas
  sin revivir la ruta runtime SQL. No endpoint status/settlement/release.
- **Cambios mínimos:** atomic en alias exclusivo; aislamiento antes del primer SQL
  y comprobación efectiva; retry completo de 40001 tras rollback, tratamiento
  40P01 aprobado. Grant/versión/evento atómicos; enlace inmutable nuevo según diseño.
  Respuesta de éxito solo después de commit confirmado; resultado ambiguo UNKNOWN.
- **Invariantes:** invocation/hash invariables; capability/exp/grant revalidados en
  cada intento; presupuestos global/product/UUID sin doble reserva. Ningún UPDATE
  histórico para completar ledger. Política de alias/conexión evita mezclar
  identidad o configuración entre llamadas concurrentes.
- **Pruebas obligatorias:** offline de control de flujo, rollback y códigos con
  dobles; preparar PG-T07–09 con sesiones independientes, sincronización de carreras
  e inyección documentada antes/después de commit. Cubrir policy/tariff/entitlement,
  registro/credencial/grant, dos tenants, conflicto concurrente, 40001/40P01,
  agotamiento, expiración durante retry, caída y pérdida de respuesta.
- **Evidencia requerida:** orden total de locks revisado en todas las rutas,
  límites/retry aprobados, diff/SHA, tabla de puntos de fallo, invariantes antes/después
  previstas, reglas ledger y distinción rollback conocido/commit desconocido.
- **Rollback:** patch local reversible antes de aplicación; futuras filas inmutables
  se preservan. Fallo de migración/runtime lleva a detener admisiones y corrección
  revisada, no a borrar decisiones ni liberar reservas por incertidumbre.
- **Aceptación:** revisión financiero/DBA; semántica comprobada offline y matriz
  runtime completa preparada. SERIALIZABLE/concurrencia solo PASS después de VAL-01.
- **STOP:** order/retry no aprobado, nuevo invocation en retry, éxito al cerrar
  conexión, falta rollback completo o intento de construir recuperación S4.
- **Riesgos residuales:** status operativo sigue ausente (B-R01). Inspector del lab
  puede demostrar un efecto; no habilita clientes a reconciliar en operación.

## S3-IMP-05 — IPC local y protocolo autenticado

- **Dependencias y autorizaciones:** IMP-04 revisado; AJ-I01–I04, interfaces I05/I06,
  C01/C02 y NUM-I01/I02/I03 aprobados; B-T01 resuelto con alcance/versionado. Permiso
  de implementación local de adaptadores/parser; no bind/listen/connect real.
- **Archivos previsibles:** nuevos módulos financieros de protocolo y adaptadores
  issuer/executor, nombres a fijar en permiso; `issuer.py` para material completo
  y `executor.py` para contexto ligado; nuevas pruebas offline en scripts/tests
  o financial. Ninguna vista/URL HTTP, broker o integración de producto externo.
- **Cambios mínimos:** framing versionado y acotado; un request/response por conexión;
  peer kernel mutuo y allow-list; issuer valida credencial/grant/binding y recomputa
  material; executor verifica firma/hash; respuesta identifica invocation/material.
- **Invariantes:** runtime no es peer del executor; UID no sustituye autorización
  tenant; sin FD/SQL/path arbitrarios; denegar payload inválido antes de despacho;
  claves privadas/DSN no atraviesan canal. Correlation diagnóstica no es claim firmado.
- **Pruebas obligatorias:** offline con bytes y dobles de peer/transporte; CR/MT
  relevantes; preparar IPC-T01–08 para UIDs reales. Los mocks prueban decisiones
  del código, nunca SO_PEERCRED efectivo. Replay financiero real depende de PG.
- **Evidencia requerida:** especificación wire con valores aprobados y vectores,
  tabla UID/endpoint/operación, errores seguros, hash de protocolo/patch, tests
  y contador de despacho cero en rechazos, evidencia de compatibilidad C-B.
- **Rollback:** retirar patch local; si se hubiera aplicado posteriormente, parar
  listeners propios mediante lifecycle aprobado sin borrar endpoints desconocidos.
  Conservar UNKNOWN y las identidades, sin fallback a SQL ni otro transporte.
- **Aceptación:** revisión protocolo/seguridad/financiero; todas las rutas y errores
  enumeradas, positivos/negativos offline. Transporte operativo sigue NOT_RUN.
- **STOP:** topología no local, NUM-I incompleto, parser discrepante, peer simulado
  tratado como real, server UID no verificado o TLS reemplazado sin acta.
- **Riesgos residuales:** kernel y peers confiados; no durabilidad de transporte,
  no firma integral de respuesta ni recuperación operativa por este slice.

## S3-IMP-06 — Hardening, observabilidad y lifecycle

- **Dependencias y autorizaciones:** IMP-05 revisado; AJ-I05/I06/P07/P08, NUM-L01,
  B-D01 y protocolo final aprobados. Permiso para plantillas y harness sucesores;
  ninguna instalación de unidad, sudo, chmod host, cuenta ni servicio activo.
- **Archivos previsibles:** nuevo harness sucesor de
  `backend/scripts/verify_financial_s3_postgres.sh`, harness IPC, tests offline y
  plantillas de unidades/config sintética con ubicación final por acta. Mantener
  scripts históricos como antecedentes; `s3_isolation_host_lab.sh` fuera del patch.
- **Cambios mínimos:** manifiesto de recursos, validación de paths/owners/colisiones,
  settings exclusivos, secretos efímeros fuera de argv/logs; unidades mínimas y
  DAC por canal. Data directory privado; socket PG con acceso mínimo por UID.
  Telemetría de códigos/identidad/correlación/deltas sin tokens/credenciales/prompts.
- **Invariantes:** no fallback trust/config general; no borrar tras stop fallido;
  PASS después de inventario final. Registrar nacimiento/identidad de proceso
  además del PID; detectar stale manifest, PID reciclado y symlink. Runtime no
  lee clave issuer ni material DB admin/executor.
- **Pruebas obligatorias:** offline de manifest/redacción/errores y lifecycle con
  dobles; diseñar PG-T10/11 e IPC-T03/07/08/09/10, startup parcial, INT/TERM,
  fallo de stop y recuperación posterior simulada/documentada de SIGKILL. La
  terminación real y hardening del binario requieren autorización runtime propia.
- **Evidencia requerida:** patch/SHA completo, comandos finales exactos preparados
  tras existir el harness, entorno/versiones, UID/path/permiso por recurso,
  política de sesiones/rotación y plan de cleanup con custodia/retención.
- **Rollback:** descartar plantillas no aplicadas; en runtime detener solo recursos
  del run y verificar salida antes de unlink. Mismatch/stop fallido conserva
  manifest y recursos, devuelve FAIL y solicita adjudicación específica.
- **Aceptación:** harness revisable sin éxito anticipado ni eliminación global;
  gates PG/IPC concretos y separados, permisos todavía PENDING. Cambio de SHA
  posterior requiere revalidar alcance antes de ejecución.
- **STOP:** propietario incierto, falta manifest, secretos en evidencia, world access
  para positivo, whitelist de syscalls sintética presentada como servicio real.
- **Riesgos residuales:** SIGKILL impide trap; cambios del binario pueden exigir
  ajustar hardening mediante revisión y nuevos hashes, nunca relajar para obtener PASS.

## S3-VAL-01 — PostgreSQL runtime validation

- **Dependencias y autorizaciones:** IMP-01–06 revisados y offline aceptados;
  G-ARCH/G-IMP satisfechos y **permiso G-PG nuevo**, con SHA, comandos y entorno
  concreto. G-OS específico si peer requiere UIDs distintos/provisión. No IPC
  necesario para probar executor/DB; PG-T10 exige procesos/identidades aprobados.
- **Archivos previsibles:** solo resultados nuevos del harness/fixtures autorizados,
  catálogo allow-listed, transcript y manifest en ubicación aprobada. No cambios
  de código/ACL sobre la marcha; un fallo vuelve al slice de implementación.
- **Cambios mínimos/runtime:** clúster desechable propio sin TCP/shared DB;
  provisión y migraciones únicamente autorizadas; sesiones reales por principal;
  seed/inspector separados de quien produce el positivo.
- **Invariantes:** todos los del ADR; ninguna credencial/dato real; catálogo con
  15 tablas y objetos auxiliares; auth real, sin trust. Conexión sana antes/después
  de cada negativo; transacciones/conexiones independientes para evitar falso 25P02.
- **Pruebas obligatorias:** PG-T01–11, incluida matriz executor de concurrencia y
  fallos, auth/ACL/RLS/defaults/owners, secretos y cleanup. No omisiones silenciosas;
  caso no ejecutado permanece NOT_RUN y bloquea afirmar la propiedad que cubre.
- **Evidencia requerida:** versión PG/Python/librerías, hash exacto ejecutado,
  run ID, identidades OS/session_user/current_user, aislamiento observado,
  SQLSTATE y deltas/hash de invariantes, stdout/stderr/retornos, catálogo sin
  pg_authid/secretos y prueba de salida/ausencia final.
- **Rollback:** parar admisiones/clúster propio, archivar evidencia fuera del árbol,
  comprobar proceso/socket y eliminar solo recursos atribuibles. Stop fallido
  conserva recursos y FAIL; permiso de recuperación separado cuando corresponda.
- **Aceptación:** casos completos y atribuibles, aislamiento real y finanzas sin
  doble/exceso, cleanup completo; revisión DBA/seguridad/financiero pendiente de acta.
- **STOP:** entorno/owner/SHA distinto, credenciales reales, permiso faltante, falso
  positivo por admin, negativo por servidor caído, prueba omitida o residuos.
- **Riesgos residuales:** laboratorio no certifica producción; issuer/executor
  comprometidos siguen excluidos. Resultado PG no certifica transporte IPC.

## S3-VAL-02 — IPC runtime validation

- **Dependencias y autorizaciones:** VAL-01 aceptado para el orden de este plan;
  IMP-05/06 y protocolo/identidades finales revisados; **G-IPC y G-OS nuevos**.
  Integración con DB requiere además G-PG vigente para ese run/hash/destino;
  aceptación de un run PG anterior no permite crear otro clúster tácitamente.
- **Archivos previsibles:** nueva evidencia de canales, peers, servicios y manifest;
  outputs PG solo en integración autorizada. No tocar servicios externos ni Host Lab.
- **Cambios mínimos/runtime:** arrancar únicamente servicios/cuentas/paths sintéticos
  del acta; ejecutar primero positivos/negativos de transporte con contador de
  despacho, luego integración financiera si permisos lo contemplan.
- **Invariantes:** peer mutuo/UID exclusivo, allow-list y DAC por canal; cero
  despacho para frame/peer inválido; un efecto DB máximo por invocation/hash;
  UNKNOWN preservado sin liberar/despachar/reintentar con identidad nueva.
- **Pruebas obligatorias:** IPC-T01–10; intruso y servidor sustituto con controles
  sanos; framing/límites/timeout; revocación en conexión abierta; restart/caída y
  pérdida de respuesta; aislamiento de secretos/paths; cleanup incluso fallos.
  En integración, repetir PG-T08/09 aplicables al canal real sin duplicar sin razón
  pruebas PG ya aceptadas para el mismo código/entorno.
- **Evidencia requerida:** UID/GID/PID/identidad real del peer y servidor, modos/ACL,
  hashes/unidades/protocolo, errno/código y contador despacho, deadlines medidos,
  deltas DB solo bajo permiso, manifest dev/inode/owner y ausencia final.
- **Rollback:** detener admisiones/listeners, drenar según política, cerrar clientes,
  verificar procesos propios terminados y unlink por atribución. Conservar evidencia
  y UNKNOWN; no borrar por prefijo global ni usar limpieza ajena.
- **Aceptación:** positivos y negativos por UIDs distintos e invariantes completas;
  transporte y efecto financiero se reportan separados; evidencia aceptada por
  plataforma/seguridad/financiero. Ningún resultado habilita producción.
- **STOP:** G-IPC/G-OS/G-PG faltante, UID compartido, servidor no autenticado,
  intento de otro transporte, dispatch en rechazo, UNKNOWN mal clasificado o cleanup FAIL.
- **Riesgos residuales:** comunicación local no durable; recuperación operativa y
  integración externa permanecen pendientes fuera de estos slices.

## S3-CLOSE-01 — Reconciliación final y revisión de cierre

- **Dependencias y autorizaciones:** VAL-01/02 completos, actas AJ y permisos por
  SHA disponibles; AJ-H01 y B-G01 adjudicados. Permiso de revisión de evidencia;
  la aceptación de cierre pertenece a autoridad humana G-CLOSE.
- **Archivos previsibles:** documentos nuevos de reconciliación, índices/hashes,
  acta de aceptación y excepciones; nunca modificar resultados/documentos históricos.
- **Cambios mínimos:** cruzar AJ→contrato/hash→patch→permiso→run→caso→resultado;
  resolver diferencias y evidencias perdidas con atribución, sin rellenar historia.
- **Invariantes:** FAIL/SKIP/NOT_RUN no se renombran PASS; cierre documental no
  sustituye prueba runtime. Phase31.5 EXECUTION_HELD; Phase32/WP2/productos y S4–S6
  sin cambio. Una aprobación S3 no autoriza deploy/inferencia/integración.
- **Pruebas obligatorias:** DOC-T01/02 y verificación de integridad/cobertura de
  CR/MT/PG/IPC; controles positivos/negativos y cleanup; no repetir ensayos aceptados
  salvo código nuevo, fallo o incertidumbre justificada y permiso correspondiente.
- **Evidencia requerida:** actas y mandatos, hashes, resultados completos, excepciones
  con fundamento, recursos residuales y aceptación de riesgos; recuperación/status
  explícitamente adjudicados sin afirmar que existe endpoint.
- **Rollback:** si evidencia insuficiente, mantener NOT_CLOSED y registrar acciones;
  no revertir historia ni ejecutar remediaciones bajo permiso documental.
- **Aceptación:** autoridad competente acepta evidencia suficiente y alcance exacto.
  Con B-R01 pendiente no hay habilitación operativa; tampoco cierre pleno por mera
  aceptación de riesgo. Cierre acotado, si propuesto, requiere acta de reservas.
- **STOP:** acta faltante, hash distinto, control no demostrado, recursos desconocidos,
  procedencia inventada o permiso de producción inferido.
- **Riesgos residuales:** custodios/firmantes y frontera de confianza requieren
  gobernanza permanente; este plan no fija una fecha de cierre ni promete S3 PASS.

## Inventario mínimo que debe concretar IMP-02

Los nombres son inventario estático de MODELS/M0002–M0007, **no catálogo observado**:

| Grupo de objetos | Tablas | Control propuesto por revisar |
| --- | --- | --- |
| Identidad y auditoría de permisos | `financial_producer_registrations`, `financial_producer_registration_events`, `financial_permission_audit_events` | Owner migration, RLS/append-only; issuer solo lecturas necesarias; writes administrativos gobernados. |
| Política y exposición | `financial_policies`, `financial_policy_versions`, `financial_budget_scopes`, `financial_verified_tariffs` | Owner migration; admission lee/bloquea y actualiza solo contadores permitidos; no grants executor. |
| Decisión y evidencia | `financial_admission_decisions`, `financial_reservations`, `financial_settlement_evidence`, `financial_resolution_history`, `financial_audit_events` | Inmutabilidad donde corresponde; transición controlada de estado mutable; auditor central según ACL, sin implementar S4. |
| Grants y ledger | `financial_producer_tenant_grants`, `financial_producer_tenant_grant_events`, `financial_invocation_ledger` | Corregir owner explícito; issuer SELECT mínimo de grants/eventos; administrador distinto realiza transición; ledger nuevo ligado sin UPDATE histórico. |

Completar funciones `financial_admit_reserve`, `financial_admit_reserve_capability`,
triggers/auxiliares, índices/secuencias si existen, schema/database/default ACL,
lecturas de `integration_api_keys`, organizaciones/productos/entitlements y
memberships. No conceder tablas o columnas enteras solo porque aparecen aquí.
La matriz final por operación/rol es una condición AJ-P02/P04/P05, no una ACL
ya aprobada por este inventario.
