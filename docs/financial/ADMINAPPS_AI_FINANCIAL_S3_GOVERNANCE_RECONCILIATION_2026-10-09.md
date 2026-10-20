# S3 Decision 02-A — Governance Reconciliation

Fecha: 2026-10-09, America/Costa_Rica. Documento E, índice del paquete.
Reconciliación repository-local realizada **sin cierre formal de S3**.

## A. Executive verdict

El SHA del script host coincide; 19/19 regresiones de sus predicados y 19/19
tests de capacidades offline pasan. Se conserva el éxito host comunicado como
antecedente, pero faltan logs primarios persistentes para adjudicar su cierre.
PostgreSQL tiene implementación parcial y resultados históricos; el aislamiento
de credenciales/procesos y transporte IPC no están demostrados.

| Estado solicitado | Adjudicación conservadora |
| --- | --- |
| S3_HOST_LAB_EXECUTION_CLOSED / S3_HOST_LAB_CLOSURE_EVIDENCED | No declarados; ejecución/cleanup reportados, cierre técnico `EVIDENCED_PARTIAL`. |
| S3_POSTGRESQL_ISOLATION_PENDING | Se mantiene; antecedentes de 4 tests no cierran autenticación ni aislamiento del sucesor. |
| S3_IPC_ISOLATION_PENDING | Se mantiene; no hay transporte financiero implementado. |
| S3_GOVERNANCE_RECONCILIATION_PENDING | Se mantiene para autoridad, archivo histórico y cierre formal; inventario local entregado. |
| S3_SUCCESSOR_PLAN_READY_FOR_APPROVAL | Listo para revisión del plan y gates, no runtime-ready. |
| S3_POSTGRESQL_AND_IPC_SUCCESSOR_SPECIFICATIONS_READY | Documentos B/C preparados; contrato wire IPC y harness ejecutables siguen pendientes. |
| S3_GOVERNANCE_RECONCILED_WITHOUT_FALSE_CLOSURE | Describe únicamente el trabajo documental de esta revisión, no sustituye acta de gobernanza. |

## B. Governance integrity y fuentes

| Clave | Fuente (ruta relativa a este directorio, salvo ISO/código) | Autoridad y uso |
| --- | --- | --- |
| D02 | [Security Decision 02-A](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) | Registra HUMAN_APPROVED para remediación acotada; no aprobación de aislamiento operativo ni cierre S3. |
| A02 | [Security Amendment 02](ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md) | APPROVAL_PENDING; exigencias adicionales son propuestas, no nuevas normas aprobadas por esta tarea. |
| ER | [Decision execution report](ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md) | Antecedente SQLite 21 run/17 pass/4 skip y PostgreSQL 4/4; quedan carreras/faults pendientes. |
| HG | [Administrative gate](ADMINAPPS_AI_FINANCIAL_S3_ISOLATION_ADMINISTRATIVE_GATE_2026-10-09.md) | Alcance sintético host, permisos, manifest y exclusiones. |
| HR | [SystemCallFilter remediation](ADMINAPPS_AI_FINANCIAL_S3_SYSTEMCALLFILTER_VALIDATION_REMEDIATION_2026-10-09.md) | Revisión histórica con SHA anterior y divergencia de token simbólico documentada en A. |
| VM | [Existing VM execution](ADMINAPPS_AI_FINANCIAL_S3_EXISTING_VM_ISOLATION_EXECUTION_2026-10-09.md) | Snapshot anterior, límites de proceso/IPC/servicios. No prueba estado actual del host. |
| V11 | `isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md` §§1–3,8–11 | Autoridad financiera y roles. Cabecera original dice propuesta; informes posteriores de AdminApps registran aprobación. Conservar ambos, reconciliar acta/versionado sin modificar ISO Smart. |
| FIRM | `isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_IMPLEMENTATION_READINESS_2026-10-08.md` | Matriz FIN-01–12 y slices S1–S6, planning-only. Amendment 01 también inspeccionado, sin modificación. |
| U | Solicitud MASTER PROMPT §§2–12 | Fuente de resultados host reportados y autorización exclusiva de trabajo local seguro. Hash del adjunto en JSON, sin presentarlo como log host. |
| OFF | [Offline evidence JSON](ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json) | Evidencia nueva: comandos/salidas/retornos/hashes y sondas diagnósticas reproducibles. |

D02 selecciona LOGIN executor/verificación Python, mientras A02 propone NOLOGIN
y verificación DB. V11 conserva cabecera de propuesta, frente a registros de
aprobación posteriores. No revocar ni inventar aprobación: pedir reconciliación
de fuente/versión a autoridad humana. Los estados Phase31.5 y Phase32 no cambian;
no se inspeccionó ni modificó runtime ISO Smart ni MedSupplier. No endpoint,
inferencia, settlement, deployment, secreto ni Git commit/push/merge autorizado.

## C–E. Matriz trazable host, PostgreSQL e IPC

REC-* son identificadores propuestos para esta reconciliación, no requisitos
normativos inventados. Cada fila remite al contrato original; `EVIDENCED_COMPLETE`
solo cubre el control estrecho descrito. Los estados distinguen implementación,
evidencia y autorización; dependencias secundarias se mantienen explícitas.

| ID / fuente | Contrato esperado | Implementación localizada | Evidencia disponible / tests de esta revisión | Estado | Gap y dependencia | Criterio de aceptación |
| --- | --- | --- | --- | --- | --- | --- |
| REC-H01 / U §2, HG | Vincular fuente al SHA validado. | `backend/scripts/s3_isolation_host_lab.sh`. | SHA coincide con `4a500…`; OFF, bash -n. | EVIDENCED_COMPLETE | Completo solo para bytes del checkout; copia protegida pendiente en H02. | Igualdad exacta del checksum del checkout; no atribuir ejecución por esa igualdad. |
| REC-H02 / U §§2,4, HG | DAC, identidades, cgroup, hardening/seccomp de probes. | `validate_systemd_probe`, predicados y DAC checks. | U reporta PASS/6 DAC; OFF reproduce 19 tests con fixtures; ningún runtime nuevo. | EVIDENCED_PARTIAL | Logs originales/host/PID/unidad y hash protegido; operador debe archivarlos. | Evidencia primaria atribuible a versión/unidad/UID, positivos y negativos; revisión del alcance host únicamente. |
| REC-H03 / U §4, HR | Historial de corrección Bash y filtro semántico. | Parser actual rechaza token simbólico, expande syscalls. | HR usa SHA anterior; bash -n y 19 regresiones actuales PASS. | EVIDENCED_PARTIAL | Falta diff/causa Bash exacta y transición HR→4a500; depende de archivos históricos. | Historial o pérdida documental declarados; no reconstruir retrospectivamente logs. |
| REC-H04 / U §2.4, HG | Cleanup completo de recursos propios. | Manifest y cleanup en script, protegido fuera del alcance. | U reporta CLEANUP_COMPLETE/ausencia; fixtures anteriores en HG, sin inspección nueva. | EVIDENCED_PARTIAL | Inventario posterior original ausente; dependencia operador. | Usuarios/grupos/rutas/unidades/procesos sintéticos ausentes y excepciones retenidas explícitas. |
| REC-H05 / U §2.4 | Compatibilidad de modo /root con hardening. | Gate exige 0700; cambio 0550→0700 reportado. | Revisión documental, sin stat/chmod sobre /root. | SOURCE_INSUFFICIENT | Baseline, ACL/dependencias y aceptación del dueño host faltantes. | Adjudicación de política del host; ningún ajuste automático. |
| REC-P01 / D02 DB, V11 §8 / FIN-08 | Roles/owners/ACL separados y mínimo privilegio. | Migraciones 0002–0007, verifier. | ER relata roles; inspección nueva encuentra ownership 0006 no explícito, defaults/memberships sin prueba completa. | EVIDENCED_PARTIAL | Catálogo/negativos PG-T02/05/06; PG-01 y autorización PG-03. | Tabla/función/schema owner y permisos efectivos conformes, sin escalamiento. |
| REC-P02 / V11 §8, D02 / FIN-08 | RLS forzado, acceso por contrato, evidencia inmutable. | 0002/0003/0005/0006, triggers/policies/grants. | Fuente presente, reportes S1/ER; no nueva DB. | EVIDENCED_PARTIAL | Matriz A/B/no-context final y roles administradores controlados. | PG-T03/04 pasa; distinguir ACL denegada de filtrado RLS y de auditor central autorizado. |
| REC-P03 / D02 capacidad, A02 §6.2 propuesto | Firma/claims/material exactos y grant vigente. | `capabilities.py`, issuer/executor, wrapper 0007. | OFF 19 tests PASS; dos sondas de wire aceptadas (FAIL del rechazo estricto propuesto); ER capability válida. | EVIDENCED_PARTIAL | Verificación solo Python, contrato wire y rol issuer pendientes; key lifecycle no operacionalizado. | Pruebas positivas/negativas en ruta real; aclarar A02 sin atribuir firma a PostgreSQL. |
| REC-P04 / D02 DB, FIRM FIN-04/06 | Grants, revocación, idempotencia y transacción serializable. | 0007 locks/ledger; services serializable; executor sin SET TRANSACTION. | ER carreras por ruta anterior; inspección nueva; no carrera nueva. | EVIDENCED_PARTIAL | Aislamiento y retry executor, atomicidad transición grant, enlace ledger/decision, matriz X01. | PG-T07/08/09 con sesiones reales e invariantes exactos; no transferir prueba de otra ruta. |
| REC-P05 / D02 trust boundary | Identidad DB solo disponible al executor. | Config inyectada; verifier `--auth=trust`. | Fuente demuestra fixture de roles, no mecanismo de autenticación exclusiva/rotación DB. | NOT_IMPLEMENTED | HBA/credenciales/secret store aprobados; PG-01/02 y aislamiento de proceso. | PG-T01/10, nueva autenticación denegada tras revocación; semántica de sesiones abiertas definida. |
| REC-P06 / D02 trust boundary, A02 §6.1 propuesto | Clave issuer y credencial executor separadas del runtime. | Interfaces Python; host fixture de clave/texto. | U DAC reportado; ninguna credencial DB real ni servicio financiero aislado evidenciado. | EVIDENCED_PARTIAL | Rol/lecturas issuer, servicio/secret store/peer isolation y autorización separada. | Accesos positivos/negativos efectivos a secretos sintéticos con procesos reales y DB bajo scope aprobado. |
| REC-P07 / U §§5.4,7,8 / FIN-11 | Runtime sintético autorizado y teardown comprobado. | Verifier existente, sucesor especificado en B. | No DB ejecutada; revisión descubre trap que oculta stop y éxito previo a cleanup. | PENDING_AUTHORIZATION | Primero PG-01/02 y SHA/runbook concreto; luego autorización humana. | PG-T01–11, catálogo, resultados y ausencia final; ninguna DB compartida. |
| REC-I01 / D02 trust boundary, VM §F/N | Transporte autenticado separado. | Solo llamadas Python, sin endpoint financiero. | Búsqueda AF_UNIX/SO_PEERCRED/FIFO/broker y callsites; no IPC ejecutado. | NOT_IMPLEMENTED | Transporte y harness inexistentes; depende IPC-01/02. | IPC-T01–10 sobre implementación revisada, no fixtures de archivos. |
| REC-I02 / D02, VM, U §6 | Peer→endpoint→operación y lifecycle inequívocos. | Placeholders runtime dirs, interfaces en código. | Documento C lista IPC-C01–08; no contrato wire/allow-list implementado. | SOURCE_INSUFFICIENT | Decisión de topología, identidades, límites, revocación y errores. | Contrato aprobado y verificable sin asumir socket/broker/worker existente. |
| REC-I03 / U §§6,8 | Denegaciones reales IPC y cleanup sin residuales. | Harness descrito, aún no implementado. | No runtime; DAC no contado como IPC. | PENDING_AUTHORIZATION | IPC-01/02, artefacto/hash/runbook y autoridad de entorno aislado. | Positivo sano, intruso denegado, cero efecto cruzado y cleanup efectivo; integración depende PG-03. |
| REC-X01 / ER blockers / FIN-04/06/11 | Matriz S3 concurrente y fallos, no doble exposición. | Tests PostgreSQL existentes: una carrera global/replay y tres tests runtime/executor. | ER registra 4/4 anteriores; ninguno nuevo; pendientes enumerados en B. | EVIDENCED_PARTIAL | Revocación/producer/policy/tariff/entitlement, tenants, conflicting replay, 40001/40P01, exhaustion, crash/ambiguous commit. | Evidencia de todos los casos aplicables por ruta executor y aceptación financiera. |
| REC-G01 / D02, A02, V11, U §3 | Autoridad/versiones/fuentes inequívocas y archivo suficiente. | Fuentes originales conservadas, A–E y OFF nuevos. | Inspección de cabeceras y diferencias; no aprobación inventada. | SOURCE_INSUFFICIENT | Acta/versionado de V11, relación D02/A02 y logs host; autoridad documental externa. | Autoridad vincula acta a versión/hash y resuelve diferencias; inventario no basta para cerrar. |
| REC-G02 / U §§4,12 | Cierre integral solo con evidencia y autoridad. | Este dictamen y plan GOV-02. | No acta de cierre concedida. | PENDING_AUTHORIZATION | H02–H05, P01–P07, I01–I03, X01/G01. | Revisión completa y aprobación formal; sin abrir S4–S6 ni gates operativos. |
| REC-O01 / U §§8–10 | Entregar documentación/verificación local preservando cambios. | A–E, test offline y OFF. | Pruebas, sintaxis/AST, links, diff/checksums en OFF. | EVIDENCED_COMPLETE | No equivale a completar controles runtime; no requiere servicio externo. | Siete archivos nuevos, fuentes previas intactas y checks locales reproducibles. |

`BLOCKED_EXTERNAL` se reserva para una dependencia externa concreta confirmada;
no se inventa proveedor/HSM/infraestructura para llenar ese estado. Los documentos
o contratos insuficientes se clasifican `SOURCE_INSUFFICIENT`; el permiso runtime
ausente se clasifica `PENDING_AUTHORIZATION`, aun si tiene prerequisitos técnicos.

## Alcance FIN-* sin ampliar S3

FIN-01/02/03/08/09 aportan autoridad/producer/tenant/RLS/RBAC existentes; esta
revisión no reabre ni recertifica S1/S2. FIN-04/05/06 aportan atomicidad, precisión
e idempotencia a S3 (REC-P04/X01); no se aprueban tarifas reales. FIN-11 define
verificación previa a activación y se vincula P07/I03/G02. FIN-07 corresponde a
settlement/evidencia posterior; FIN-10 HTTP y FIN-12 input-bound/proveedor quedan
fuera de este slice. Se conservan como dependencias de activación en FIRM, sin
marcarlas completas, implementarlas ni cambiar el estado de fases posteriores.

## F. Implementation plan

[Documento D — slices y gates](ADMINAPPS_AI_FINANCIAL_S3_SUCCESSOR_EXECUTION_PLAN_2026-10-09.md):
GOV-01 → PG-01/IPC-01 → PG-02/IPC-02 → PG-03/IPC-03 autorizados → GOV-02.
Cada slice tiene objetivo, fuentes/archivos, prerrequisitos, pruebas/evidencia,
riesgos/STOP, aceptación, autorización y cleanup. No hay comando IPC inventado
ni ejecución automática del verifier PostgreSQL antiguo.

## G. Test results

| Verificación nueva | Resultado | Límite |
| --- | --- | --- |
| SHA host | PASS, coincide `4a50014a069289af60afacedc89b6d93468edbd3921c8c6d72c3e005d6c086a5` | Fuente del checkout, no copia protegida. |
| bash -n individual: host, regresión host, verifier PG | PASS | Solo sintaxis; no dispatch de operaciones. |
| Regresión host | PASS 19/19 | Datos y expansión stubbed; no systemd-run ni host lab. |
| Nuevo `test_s3_capability_offline.py` | PASS 19/19 | Ed25519 efímero en memoria, reloj fijo; no Django setup ni DB/IPC. |
| Sonda JSON no canónico | Observado ACCEPTED; **FAIL** de rechazo estricto propuesto | No falsificación de firma; Amendment 02 §6.2 pendiente. |
| Sonda clave JSON idéntica duplicada | Observado ACCEPTED; **FAIL** de rechazo estricto propuesto | No contar exit 0 del diagnóstico como control PASS. Comando íntegro en OFF. |
| AST Python, links locales, hashes previos, whitespace | PASS; detalle en OFF | Revisiones estáticas, no prueba SQL/host. |
| PostgreSQL / IPC / host runtime | SKIP por límite de autorización | No sustituido por SQLite ni mocks como evidencia de aislamiento. |
| Suite Django completa / migraciones runtime | No ejecutadas | No código productivo cambiado; suite offline aislada evita cargar `.env`/servicios. |

No se instalaron herramientas. Disponibilidad de ShellCheck registrada en OFF;
si falta, SKIP, sin sustituirlo por un PASS. Los números históricos de ER/VM/HR
permanecen separados: no se suman a los 38 tests nuevos offline.

## H. Git & source integrity

Rama inspeccionada: `hardening/p0-p1-enterprise-readiness`.
HEAD: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`.
La rama se registra, no se certifica como rama de release aprobada.

Estado inicial: `backend/config/settings.py` modificado; sin rastrear
`backend/apps/financial/`, `backend/scripts/s3_isolation_host_lab.sh`,
`backend/scripts/tests/`, ambos verifiers PostgreSQL y `docs/financial/`.
OFF conserva hashes de 37 archivos preexistentes de ese alcance; se verifican
al finalizar. HEAD/branch no se cambian. Ningún archivo previo se modifica;
los tests y documentos nuevos permanecen sin rastrear y sin staging.

Archivos añadidos en esta tarea (A–E + evidencia + tests):

1. [A — Host Lab Closure Evidence](ADMINAPPS_AI_FINANCIAL_S3_HOST_LAB_CLOSURE_EVIDENCE_2026-10-09.md).
2. [B — PostgreSQL Isolation Specification](ADMINAPPS_AI_FINANCIAL_S3_POSTGRESQL_ISOLATION_SPECIFICATION_2026-10-09.md).
3. [C — IPC Isolation Specification](ADMINAPPS_AI_FINANCIAL_S3_IPC_ISOLATION_SPECIFICATION_2026-10-09.md).
4. [D — Successor Execution Plan](ADMINAPPS_AI_FINANCIAL_S3_SUCCESSOR_EXECUTION_PLAN_2026-10-09.md).
5. Este documento E.
6. [OFF — Offline Evidence](ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json).
7. [Tests offline](../../backend/scripts/tests/test_s3_capability_offline.py).

`git diff --check` no inspecciona por sí solo los archivos untracked: se agrega
`git diff --no-index --check /dev/null <archivo-nuevo>` por cada entrega y revisión
del contenido nuevo completo. Manifiesto de hashes de entregas (excepto el propio
JSON) en OFF; no contiene claves, DSN ni datos de clientes. Se conserva además
hash de las tres fuentes ISO leídas y del adjunto, no su contenido secreto.

## I. Remaining blockers

Faltan archivo original host y cadena Bash/SHA; aceptación de `/root`; resolución
de autoridad V11/D02/A02; contrato y credenciales del issuer; autenticación DB,
ownership final, defaults/ACL y serializable executor; transporte/peer protocol
IPC; harnesses con cleanup verificable; autorización de runtime y matriz completa
de fallos/concurrencia. Las sondas wire requieren adjudicación/remediación futura.
Ninguno se oculta detrás de los PASS offline.

## J. Next human approval

La siguiente intervención útil es revisar A–E, aportar el respaldo histórico y
resolver las decisiones concretas PG/IPC de B/C para preparar sus harnesses.
La autorización operativa solo se solicita cuando existan código, SHA, comandos,
entorno y cleanup revisados. Es una frontera exigida por la solicitud §§5.4/7/8;
este paquete no pide permiso para trabajo local ya autorizado ni habilita
automáticamente host, DB, IPC, S4–S6 o cambios de gobernanza.
