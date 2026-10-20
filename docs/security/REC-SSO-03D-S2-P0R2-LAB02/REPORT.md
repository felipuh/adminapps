# REC-SSO-03D-S2-P0R2-LAB02 — SQL Revocation Integrity & Database Privilege Hardening

Fecha: 2026-10-20, America/Costa_Rica. Repositorio: `/home/felipe/proyectos/adminapps`.

## A. Executive Verdict

**`P0R2_LAB02_SQL_REVOCATION_BOUNDARY_VERIFIED`**

El bypass DELETE/reinsert quedó cerrado **dentro del perfil SQL runtime dedicado verificado**. En un cluster nuevo, el perfil anterior reprodujo 200 → revocación → 401 → DELETE/reinsert → **200**. Con la migración adicional y las ACL restrictivas, el mismo procedimiento produjo `42501`, conservó **401** desde una conexión nueva y **401 después del reinicio exclusivo del cluster**, sin ejecutar el handler. Se reutilizó exactamente el JWT original del ensayo corregido; su hash coincide antes/después del reinicio. Refresh antiguo denegado y reintento de revocación idempotente.

**23 métodos SQL: 23 PASS, 0 FAIL**, más las comprobaciones separadas de aceptación, reinicio y provisionamiento. Se ejecutaron 6 métodos adversariales y 17 funcionales seleccionados; no se repitieron desde cero LAB01 ni las diez suites históricas. Las pruebas negativas de perfiles heredados/SET ROLE y la idempotencia del instalador pasaron. No se encontró otra ruta de reconstrucción dentro de este perfil.

```text
PRODUCTION_READY = FALSE
ACTIVE_AUTHENTICATOR_UNCHANGED
NO_DEPLOYMENT
NO_COMMIT
NO_PUSH
GOVERNANCE_PRESERVED
```

La garantía no cubre a un propietario capaz de alterar controles, un restore antiguo ni el funcionamiento completo del monolito bajo estos grants. Retención operativa, consumers, workers y destino real requieren revisión separada. [Resultados finales](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/results-final.json), [aceptación anterior](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/acceptance-old.json), [corregida](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/acceptance-fixed.json), [reinicio](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/acceptance-restart.json).

## B. Initial Baseline

HEAD: `b144b2505659ad39f756b9bc4530a7f24fe8c3ad`. Se registraron HEAD, hash del índice y hashes de **15.816 archivos** inventariados, incluidos los no rastreados anteriores, antes de editar. No se encontraron `AGENTS.md` aplicables. Se conservaron los cambios preexistentes, sin reset ni checkout.

Se verificó íntegramente `SHA256SUMS` de LAB01 y se recuperaron REPORT, resultados, reproducción, mitigación, catálogo, snapshot y hash de migración. También se leyeron el plan PostgreSQL y reportes R1/P0R2. Se constató que el runtime LAB01 no existía: ningún socket/PID/base previo fue reutilizado. [Baseline](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/baseline.json), [antecedentes](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/antecedents.json), [status inicial](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/git-status-before.txt).

## C. SQL Threat Model

El atacante dispone de SQL arbitrario bajo el rol de aplicación y de un snapshot sintético anterior a la revocación. El objetivo es reusar un JWT ya revocado; no posee capacidad administrativa, credenciales de mantenimiento ni clave de firma. La aplicación necesita INSERT y UPDATE legítimos; por ello la prueba incluye reconstrucciones alternativas y no se limita a observar una excepción DELETE.

Runtime: `lab02_app`, LOGIN, sin privilegios globales, propiedad ni membresías. Mantenimiento: `lab02_maintenance`, NOLOGIN, sin privilegios globales, propietario del esquema/objetos/base. El bootstrap `lab02_bootstrap` es el administrador inevitable de `initdb`, exclusivamente del cluster nuevo; no es el rol de aplicación ni el rol efectivo de migraciones. Solo se utilizó para crear recursos, comprobar aislamiento, observar metadatos administrativos y controlar el ciclo del cluster. La aplicación se conectó realmente con SCRAM como runtime; no usó SET ROLE desde bootstrap.

La autoridad del propietario no se presenta como resistente a manipulación: puede desactivar triggers, cambiar funciones o grants. Además, SQL runtime puede alterar datos de usuario/contraseña/MFA y provocar otras formas de compromiso o denegación de servicio. El resultado acredita la frontera de **credenciales revocadas**, no inmunidad completa frente a SQL arbitrario. [Contrato](SQL-RUNTIME-CONTRACT.md).

## D. Privilege Matrix

| Operación legítima | Permisos de autoridad necesarios |
|---|---|
| Emitir/login | SELECT/UPDATE usuario (incluido lock/telemetría), INSERT/SELECT sesión, INSERT auditoría |
| Consultar access | SELECT sesión y usuario en join |
| Refresh/rotación | SELECT/UPDATE usuario y sesión; generación/JTI protegidos |
| Revocar propia/otras/global | SELECT/UPDATE usuario y sesiones; no DELETE |
| Logout JWT | UPDATE terminal de sesión; no DELETE |
| Logout cookie | DELETE exclusivamente de `django_session` |
| Contraseña/disable/enable | UPDATE usuario; trigger modifica sesiones humanas, fence B, sesiones B e INSERT outbox |
| MFA | SELECT/INSERT/UPDATE configuración/challenges y SELECT/INSERT logs |
| B | SELECT/INSERT/UPDATE sesión, SELECT + UPDATE columnas generación/epoch del fence, SELECT/INSERT outbox |

El script enumera las tablas de lectura auxiliares y las escrituras permitidas. Solo `django_session` dispone de DELETE; ninguna tabla concede TRUNCATE/REFERENCES/TRIGGER/MAINTAIN. No hay grant option. Secuencias: USAGE solo para tablas con INSERT; sin UPDATE. Sin permisos sobre `django_migrations` o blacklist. Se retiran también ACL de columnas, PUBLIC y defaults, porque retirar el grant de tabla no basta para eliminar todos los grants de columnas.

La política es específica del servicio de autenticación. La creación de productos, clientes o invitaciones de fixtures se hizo por mantenimiento; ninguna operación HTTP o servicio objeto de aceptación se ejecutó como propietario. No se aumentaron grants runtime para acomodar fixtures. [Matriz SQL efectiva](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/privilege-matrix.csv), [catálogo](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/catalog-fixed.json), [snapshot ACL](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/privilege-snapshot.json).

## E. Revocation Integrity Design

Se eligió **ACL estricta + retención de las propias filas + guards existentes**. No se agregó un ledger duplicado:

- `users.0006` impide DELETE por fila y TRUNCATE por sentencia en `user_sessions`, `sso_sessions`, `sso_security_fence` y `sso_revocation_outbox`.
- `users.0005` conserva identidad/familia/autoridad y monotonicidad; PK y unicidad mantienen ocupados los identificadores anteriores. La sesión terminal nunca se elimina por las rutas runtime verificadas.
- Usuarios no tienen DELETE runtime. Las FK reales son NO ACTION; el recolector de cascadas Django no puede borrar el historial protegido. Un borrado SQL del usuario padre por mantenimiento también falló por FK.
- El runtime no es propietario, no pertenece a roles y carece de DDL, TEMP, CREATE y permisos para desactivar triggers. No puede crear un esquema/tabla sombra ni usar SET ROLE para ganar esas capacidades.
- Las seis funciones existentes de autoridad fijan `search_path` a `pg_catalog, public, pg_temp`. Todas siguen INVOKER. El catálogo no contiene funciones SECURITY DEFINER de aplicación. EXECUTE directo sobre rutinas de aplicación se retira; los triggers instalados siguen operando.
- Outbox no permite UPDATE/DELETE runtime. El fence solo permite UPDATE de generación/epoch, sin INSERT ni cambio de enabled. `sso_activation_reset()` pertenece a mantenimiento y fue denegada al runtime.

No se protege frente a modificaciones administrativas del contrato. Tampoco se incorpora purga: retirar historial requerirá otro diseño que conserve esta garantía.

## F. Code/Migration Changes

Archivos nuevos para revisión/versionado, **sin commit ni staging**:

1. `backend/apps/users/migrations/0006_sql_revocation_boundary.py`: ocho triggers de retención, una función INVOKER y rutas de esquemas fijas. Depende de `users.0005` y `integration.0010`. No cambia estado/modelos Django y es deliberadamente irreversible por el runner.
2. `backend/scripts/provision_iam_runtime.sql`: instalador parametrizado, transaccional y restrictivo. Valida roles, propiedad, esquema, migración, triggers y permisos de parámetros; exige runtime desconectado; reconstruye ACL explícitas y defaults. Rechaza membresías incluidas las que solo permiten SET ROLE.
3. `docs/security/REC-SSO-03D-S2-P0R2-LAB02/SQL-RUNTIME-CONTRACT.md` y el presente reporte: modelo, matriz, instalación, restricciones y recuperación.

Se preservaron byte por byte `users.0005` y las migraciones B. SHA256 de 0005: `bcf38638f3a31874a13ca3834ae95db113d0cce5d7145717da2be76e96f84b3c`. [Integridad](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/migration-integrity.json), [diff atribuible](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/attributable.patch), [SQL](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/provision_iam_runtime.sql), [migración](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/0006_sql_revocation_boundary.py).

El primer intento de provisionamiento detectó una referencia ambigua a `name` en el DO; abortó antes de modificar grants. Se calificó la columna y se volvió a ejecutar. Se conserva [el error inicial](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/provision-first.log). Las ejecuciones finales e idempotentes usan el archivo final. El primer snapshot intentó leer `data_directory` como mantenimiento no privilegiado y fue denegado; se eliminó esa consulta redundante sin conceder privilegios. Aislamiento y limpieza sí comprobaron ese valor con bootstrap. [Error conservado](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/final-sql-first.log).

## G. PostgreSQL Lab Isolation

Directorio exclusivo `/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1`, modo 0700, UID no root `felipe`. PostgreSQL **18.6**, `initdb` nuevo; inicialmente solo `postgres`, `template0`, `template1`. Base `lab02_human` nueva, sin tablas públicas antes de migrar. Socket privado `runtime/socket`, puerto identificador 56432, **sin listener TCP** (`listen_addresses=''`, `inet_server_addr() IS NULL`); HBA rechaza otros roles locales y hosts TCP. No sudo, contenedores, volúmenes ni servicios anteriores.

Settings sintéticos independientes, sin importar settings activos/dotenv; conexiones Python INET bloqueadas. libpq usa exclusivamente el socket explícito. Credenciales y firma efímeras bajo runtime 0600, nunca impresas. `READ COMMITTED`, fsync/synchronous_commit/full_page_writes activos. Aplicación con rol SCRAM distinto del propietario.

Se aplicaron primero las **56 migraciones IAM** del baseline para reproducir el fallo y después la 0006: **57 aplicadas**. Grafo completo: **64 nodos**, acíclico y consistente; las siete migraciones financieras solo se inspeccionaron, sin aplicarlas. No `--fake`. Django check y `makemigrations --check --dry-run`: sin problemas/drift.

[Manifiesto](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/resource-manifest.json), [aislamiento](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/isolation-initial.json), [setup](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/setup_lab.py), [plan anterior](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/migration-plan-old.json), [plan adicional](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/migration-plan-new.json), [grafo](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/full-graph.json), [checks](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/migrations-new.log), [DDL](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/schema-fixed.sql).

## H. Original Failure Reproduction

`acceptance.py old` creó usuario sintético, hizo login HTTP real, guardó el snapshot de `UserSession`, comprobó 200, revocó por servicio y comprobó 401. Bajo los grants DML antiguos ejecutó el DELETE/INSERT de `test_29`, abrió conexiones nuevas y el mismo access volvió a 200; el handler se ejecutó una vez. La fila se revocó otra vez al terminar. No se cambió LAB01 ni su FAIL histórico.

`acceptance.py fixed` ejecuta **el mismo bloque de ataque SQL**; solo cambia la expectativa del perfil. Los JWT del caso antiguo y del caso corregido son distintos fixtures; dentro de cada caso se conserva exactamente el JWT emitido originalmente. [Procedimiento](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/acceptance.py), [resultado anterior](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/acceptance-old.json).

## I. Remediation Verification

| Comprobación | Resultado real |
|---|---|
| Login previo a revocación | HTTP 200 |
| Mismo access después de revocar | HTTP 401 |
| DELETE/reinsert bajo perfil corregido | SQLSTATE `42501`; transacción abortada |
| Conexión PostgreSQL nueva, mismo JWT | HTTP 401, handler delta 0 |
| Refresh original | Denegado |
| Reintento tras pérdida simulada de respuesta | Servicio retorna 0; no revive |
| Reinicio exclusivo del cluster | PID nuevo, mismo data_directory validado |
| Mismo JWT después de reinicio | HTTP 401, handler delta 0; refresh denegado |
| Instalar de nuevo el perfil | ACL idénticas; PASS |

Hash del access corregido antes y después del reinicio: `686e64d545b6d8c64f75fff95c0884e08184d6f66ad7840bc61de06fc51730d4`. No se retuvo el JWT. [Corregido](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/acceptance-fixed.json), [reinicio](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/acceptance-restart.json), [proceso](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/restart-process.json), [idempotencia](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/provision-checks.json).

## J. Alternative SQL Bypass Tests

Seis métodos adversariales SQL, todos PASS; incluyen múltiples intentos por método:

| Ruta | Evidencia |
|---|---|
| DELETE directo humano/usuario/B/fence/outbox, TRUNCATE CASCADE | `42501` runtime |
| Borrado de instancia y QuerySet ORM, colector de usuario | DatabaseError; usuario/sesión preservados |
| DELETE de sesión por propietario, TRUNCATE protegido por propietario | `23514` por trigger; DELETE del padre con FK produce `23503` |
| INSERT con SID anterior; nuevo SID y familia/JTI ocupado | `23505` |
| ON CONFLICT DO UPDATE restaurando snapshot | `P0001`; DO NOTHING no restaura autoridad |
| MERGE … DELETE | `42501` |
| UPDATE terminal/generación/identidad/contrato; conversión legacy a SID ocupado | `P0001` o `23505`; JWT permanece 401 |
| Manipular human_auth_version | Trigger mantiene versión previa; fence decreciente rechazado |
| Transacción con escritura válida seguida de DELETE rechazado | Rollback íntegro; escritura previa ausente |
| DISABLE TRIGGER, DROP, cambio de owner/esquema, función reemplazada | `42501` |
| Esquema/tabla permanente o temporal, replication_role, COPY PROGRAM, CREATE ROLE | `42501` |
| SET ROLE mantenimiento/bootstrap/pg_write_all_data, SESSION AUTHORIZATION | `42501` |
| Función de mantenimiento y UPDATE de outbox/fence.enabled | `42501` |
| search_path modificado por atacante | Trigger cualificado revoca correctamente; JWT 401 |
| Reintento de refresh tras pérdida de respuesta | Refresh anterior denegado; solo generación nueva válida |

Además se creó un rol candidato sintético separado, sin credenciales/conexión permitida, con tres variantes de membresía: herencia+SET, solo SET y solo herencia. El instalador rechazó las tres antes de mutar ACL. No se dio esa membresía al runtime; sus ACL no variaron. El candidato se eliminó.

El catálogo confirma ausencia de grants indirectos por membresías, propiedad o PUBLIC; funciones de aplicación INVOKER sin EXECUTE runtime; no privilegios explícitos de parámetros. Las FK reales inspeccionadas no ofrecen ON DELETE CASCADE sobre la autoridad; no se simula una cascada inexistente. La defensa por triggers también prohíbe TRUNCATE CASCADE probado como propietario.

[Tests](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/test_boundary.py), [resultados](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/boundary-results.json), [observaciones SQLSTATE](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/boundary-observations.json), [log](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/boundary-first.log), [perfiles rechazados](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/provision-checks.json), [catálogo](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/catalog-fixed.json).

## K. Functional Regression Tests

**17 PASS**, usando endpoints y servicios reales sobre el runtime restringido. Se reutilizaron métodos focalizados de LAB01: ciclo durable/login/refresh/logout, dos refresh, refresh↔revocación, logout↔rotación, revocación individual/global, contraseña/actividad por ORM/bulk/SQL, guards, rollback local+B, upgrade de hash, reset concurrente, separación B, cookie/CSRF, fallo posterior a INSERT, backup MFA y concurrencia B. Se agregaron dos casos adaptados para TOTP/registro y retención/servicio B.

Revocación de otras sesiones y reintento de refresh también se verifican en el método adversarial `test_f`. Los PIDs independientes y `pg_blocking_pids` acreditan esperas reales en las carreras. No se sustituyeron almacenamiento, triggers ni transacciones. La instrumentación heredada sincroniza SQL o inyecta una excepción después de SQL real; no atribuye a PostgreSQL resultados de mocks offline.

Los fixtures de negocio B/invitación se prepararon como mantenimiento y se restableció/verificó `current_user=lab02_app` antes de ejecutar HTTP/servicios. La configuración TOTP, consumo de factores, emisión y revocación ocurrieron bajo runtime. No se ampliaron sus capacidades para aprobar casos.

Las diez suites históricas no se reejecutaron: se preservan **231 PASS, 9 FAIL, 1 ERROR** de los 241 métodos documentados por LAB01, sin reclasificar fallos ni borrar el ERROR de invitación. El FAIL SQL LAB01 permanece en su carpeta original; este laboratorio es evidencia nueva de cierre bajo otro perfil. [Funcionales](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/functional-results.json), [runner](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/functional.py), [log](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/functional-first.log), [carreras](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/functional-observations.json), [histórico heredado](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/inherited-regression-summary.json).

## L. Decision B Compatibility

Revocar una familia humana mantiene otra y B. Cambiar contraseña ejecuta revocación humana y B/fence/outbox en la misma transacción. Rollback restaura todos esos efectos; una conexión independiente no ve cambios sin commit. El servicio B conserva revocación idempotente, un evento por sesión/generación y no revoca indebidamente la familia humana. Se probaron ambas órdenes de competencia entre revocación B y cambio de contraseña con esperas SQL reales.

El snapshot final conserva **44 sesiones humanas, 7 sesiones B, 5 eventos outbox y cero OutstandingToken**. No se guardaron JWT completos en tablas. Se preservaron triggers y migraciones B, añadiendo retención y rutas fijas. La administración de clientes B para fixtures pertenece al rol de mantenimiento; el runtime solo consulta clientes.

No se iniciaron workers, servicios externos ni consumers, y no se certifica un flujo federado operativo completo. El perfil de entrega/retención del outbox queda fuera de esta ejecución. [Snapshot](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/final-sql-snapshot.json), [funcionales](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/functional-results.json).

## M. Remaining Risks

No queda un bypass de reconstrucción demostrado dentro del perfil verificado. Persisten límites operativos que impiden declarar producción lista:

- El perfil restringido de autenticación no es un sustituto probado de los permisos de todo el monolito. Los endpoints de borrado y tareas de limpieza deben revisarse antes de adoptar este perfil.
- Retención indefinida, crecimiento y eventual purga/archivo necesitan una política separada que no libere autoridad reutilizable.
- Dueños, administradores, nuevos grants/membresías, cambios de esquema o restore de estados antiguos pueden salir del modelo. No se afirma resistencia a ellos.
- No se inspeccionaron permisos, secretos, cookies ni migraciones de ningún destino compartido. Activación y backend operativo de cookies siguen pendientes de autorización/evidencia propia.
- Consumers, workers y federación completa no se validaron. Los fallos históricos siguen visibles.

## N. Operational Provisioning Contract

El [contrato versionado](SQL-RUNTIME-CONTRACT.md) define roles, tablas, instalación y recuperación. Instalar primero el grafo con 0006 como mantenimiento; desconectar runtime y aplicar el SQL con nombres explícitos, en una base dedicada previamente autorizada. Verificar definiciones, ACL efectivas, defaults, membresías y rutas; reabrir solo después de repetir aceptaciones. Cada nuevo objeto/cambio de permisos requiere revisión; el script no concede acceso automático a objetos futuros.

No activar por este informe: la autenticación durable debe cambiar junto con emisores/refresh/revocación según R1/LAB01, después de aprobación operativa. Recuperación: mantenimiento/denegación, conservar historial, corregir hacia adelante. No revertir a stateless, borrar revocaciones ni restaurar DELETE/TRUNCATE como rollback. La migración no expone una reversión destructiva.

| Criterio | Estado / evidencia |
|---|---|
| LAB02-01 | PASS — modelo y contrato de roles |
| LAB02-02 | PASS — SQL aplicado y catálogo efectivo |
| LAB02-03 | PASS — mismo ataque bloqueado; JWT 401 |
| LAB02-04 | PASS en modelo declarado — adversariales y catálogo SQL |
| LAB02-05 | PASS — reconexión con PID nuevo, 401 |
| LAB02-06 | PASS — reinicio exclusivo y mismo JWT 401 |
| LAB02-07 | PASS — refresh anterior denegado |
| LAB02-08 | PASS — guards, rollback, monotonicidad y hashes previos |
| LAB02-09 | PASS — 17 métodos funcionales y aceptación |
| LAB02-10 | PASS local/B — SQL, servicio, concurrencia; sin consumers/workers |
| LAB02-11 | PASS para perfil IAM — matriz efectiva, sin herencia ni grant option |
| LAB02-12 | PASS — solo base nueva del manifiesto |
| LAB02-13 | PASS — HEAD/índice y archivos anteriores preservados |
| LAB02-14 | PASS documental — contrato parametrizado e instalación |
| LAB02-15 | PASS documental — administrador excluido explícitamente |
| LAB02-16 | PASS — PID propio detenido y runtime exclusivo eliminado |

## O. Git/Environment Integrity

Solo se añadieron la migración 0006, el SQL de provisionamiento y dos documentos LAB02. No se editaron archivos preexistentes, settings, suites históricas, secretos, gobernanza financiera ni E/F/G. Sin despliegue, commit, push o reset. [Integridad final](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/integrity-final.json), [diff atribuible](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/attributable.patch), [status final](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/git-status-final.txt).

La limpieza volvió a comprobar `data_directory`, `listen_addresses=''` y ausencia de tablespaces externos; detuvo únicamente el PID propietario del cluster nuevo, verificó su ausencia y eliminó solo el runtime creado por LAB02. Base, roles, socket, credenciales y JWT efímeros desaparecieron con él. Logs sanitizados, DDL, scripts, matrices y resultados se retuvieron. [Limpieza](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/cleanup-result.json), [log](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/cleanup.log), [PostgreSQL](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/postgresql-server.log), [sanitización](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/sanitization.json), [inventario](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/evidence-inventory.json), [hashes](/tmp/rec-sso-03d-s2-p0r2-lab02-20261020-1/SHA256SUMS).

Se preservan:

```text
S3-IMP-01
S3_DECISION_02A_NOT_CLOSED
PHASE31_5 = EXECUTION_HELD
REC-2FA-04
REC-SSO-03A
REC-SSO-03B-CH
DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED
```

Los scripts del laboratorio son evidencia del procedimiento; su runtime ya no existe. No ejecutarlos apuntando a otra configuración. Una reproducción nueva requiere directorio y cluster nuevos y validar nuevamente el aislamiento.
