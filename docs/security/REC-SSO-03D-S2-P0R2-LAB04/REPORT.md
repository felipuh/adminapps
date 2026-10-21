# LAB04 — Enterprise IAM, control plane & SQL privileges

2026-10-21 · America/Costa_Rica

## A. Executive Verdict

**`LAB04_PARTIAL_WITH_EXPLICIT_BLOCKERS`** para la compatibilidad integral del
ecosistema. El incremento **optativo, local y no financiero** está implementado,
verificado con PostgreSQL y publicado como entrega incremental sanitizada.
No se certifica el monolito operativo completo ni un despliegue de servicios.

Se corrigieron los `42501` de las operaciones adjudicadas de organizaciones,
settings, invitaciones, catálogo, planes, entitlements y del sitio Admin restringido.
Los roles de aplicación conservan retención y revocación. Las denegaciones de
negocio ocurren antes de las escrituras; los ataques SQL se prueban separadamente.
La alternativa implementada, su matriz y sus límites están en
[ARCHITECTURE.md](ARCHITECTURE.md).

## B. Initial Git Baseline

Los tres checkouts comenzaron limpios, sin commits pendientes respecto de sus
upstreams. Sus ramas y SHA están en [baseline.json](baseline.json). Se verificaron
los refs remotos de AdminApps al inicio y de ambos consumidores al cierre.

AdminApps partió de `ef71fdac1aff8d653e2b17a36753c96d39b3e65e`, rama
`checkpoint/rec-git-03-adminapps-20261020`. El desarrollo continúa en
`lab04/runtime-boundaries-20261021`, dentro del checkout original. No se perdió
trabajo ajeno, no se usó reset/clean/stash/rebase/force push ni merge.

La historia alcanzable contiene `backend/.env` con claves no vacías y dependencias
locales. **No se publicó esa historia**, aunque ya existiera en refs remotos.
La rama nueva `lab04/reviewed-delivery-20261021` tiene raíz independiente y contiene
únicamente el overlay revisado. No es un clon autónomo de la aplicación. Véase
[DELIVERY.md](DELIVERY.md). No se cambiaron secretos ni su configuración.

## C. LAB04-A Architecture & SQL Privileges

**PASS_POSTGRESQL_LAB**, para la frontera preparada. Cuatro procesos de prueba se
conectaron mediante SCRAM como `lab04_iam`, `lab04_control_plane`, `lab04_admin` y
`lab04_events`, con contraseñas distintas y un único alias `default` por proceso.
No se utilizó SET ROLE desde runtime. Las pruebas registran `current_user` y
`session_user` reales. El propietario `lab04_maintenance` es NOLOGIN; bootstrap
solamente administra el cluster nuevo, migraciones y fixtures.

`configure()` selecciona URLconf, autenticador humano durable y guardia del
principal. IAM no expone Admin ni catálogo; control plane no expone login/Admin;
Admin no expone API; events no expone HTTP. La credencial CP presentada como perfil
IAM se rechaza por sus permisos efectivos. Las transacciones compartidas de
usuarios, sesiones, fence y outbox se conservan en una base.

El instalador reconstruye ACL de tablas/columnas, secuencias, rutinas y defaults,
sin membresías, propiedad runtime ni funciones SECURITY DEFINER. Las secuencias
solo reciben USAGE cuando su tabla admite INSERT. Events únicamente lee outboxes;
su entrega y purga permanecen retenidas. [ACL efectivas](evidence/privileges.csv).

El instalador sigue rechazando esquemas/objetos financieros no revisados. No debe
aplicarse sin adaptación al monolito completo. La separación demostrada es de
procesos/conexiones de laboratorio; no equivale a aislamiento de contenedores,
usuarios OS ni distribución operativa de secretos. [Evidencia A](evidence/A.json).

## D. LAB04-B Organizations & Invitations

**PASS_POSTGRESQL_LAB**, 32 comprobaciones finales con handlers, serializers y
persistencia reales, más registro/consumo desde otro proceso IAM. Se probaron alta,
lectura, renombre, suspensión/reactivación, preferencias, creación/preview/cancelación
de invitaciones, membresías y desactivación. Crear una identidad tenant en el perfil
optativo produce `inactive`; no concede un trial. Cuotas/trials explícitos siguen
retenidos y el borrado físico responde 405.

Se verificaron tenant ajeno, reparenting, escalamiento de rol, viewer/staff, cabecera
técnica y pérdida de autoridad del invitante. IAM consume una invitación creada por
CP y rechaza su reutilización. Una excepción después del INSERT real de auditoría
revierte organización, evento y audit log. Auditoría registra actor/modelo/acción,
sin copiar payloads, credenciales o tokens. [B corregido](evidence/B-correction.json).

La limpieza de imports posterior a la primera prueba B introdujo un import erróneo
en el checkpoint `2d0a6bbe`; se detectó, corrigió en `8b09b751` y se repitió B completo
antes de avanzar. La entrega `b3b11be0` queda explícitamente superada por `b14ad0bc`.

## E. LAB04-C Catalog & Entitlements

**PASS_POSTGRESQL_LAB**, 37 comprobaciones. Se probaron creación/lectura/actualización
y retiro de productos, planes de catálogo inactivos, entitlements con scopes
explícitos del producto, enable/disable autorizado, estándares y módulos, auditoría
y rollback de entitlement cuando falla su audit log después de una escritura real.

Se rechazan identidades de producto reasignadas, relaciones ajenas, scopes de otro
producto, campos desconocidos, trials, cuotas, precios, nueva activación comercial
de planes, bindings comerciales y escrituras de suscripciones/facturas/pagos.
Los productos nuevos del perfil optativo no habilitan billing automáticamente.
No se conceden scopes al consumidor por el mero rol administrativo local.

La lectura autorizada de facturas se ejecutó con SQL real y queryset tenant. El
laboratorio no tiene facturas financieras reales. La API de billing/financial y
las condiciones comerciales retenidas no se certifican. [Evidencia C](evidence/C.json).

## F. LAB04-D Django Admin & Audit

**PASS_POSTGRESQL_LAB** para el sitio Admin optativo restringido: 47 comprobaciones.
Los 18 modelos revisados abren changelists como superadmin sin `42501`; se prueban
índice, login por formulario, cookies, CSRF, platform/org admin, usuario común,
staff sin admisión, deshabilitado y tenant ajeno.

Las escrituras admitidas se limitan a campos personales y estado activo de usuarios,
estado activo de membresías y tema de OrganizationSettings. Se demuestran cambios
HTTP de usuario/settings y persistencia de `django_admin_log`; un fallo después de
su INSERT revierte ambos. Se ocultan filtros de tenants ajenos, se impiden cambios
de principales/membresías superiores y se rechazan payloads de privilegios.

Altas, DELETE, acciones bulk, M2M de permisos, cambio de contraseña por Admin y
mutaciones comerciales están deshabilitados en este sitio. Se usan los flujos
autorizados de IAM/CP para esas operaciones cuando existen. Catálogo y finanzas
son de consulta aquí; no se promete paridad de escritura con el Admin histórico.
El rol SQL Admin no puede insertar usuarios/sesiones/membresías, emitir MFA ni
crear invitaciones. El sitio anterior no fue activado ni reemplazado operativamente.

Admin rechaza cualquier bearer/cabecera técnica, incluso con cookie válida.
Una cuenta deshabilitada pierde acceso por cookie; deshabilitar/reactivar no restaura
su JWT. **La cookie Django y la sesión JWT siguen siendo autoridades separadas**:
no se afirma que revocar únicamente un JWT revoque todas las cookies históricas.
[Evidencia D](evidence/D.json).

## G. LAB04-E Security Regression

**PASS_POSTGRESQL_LAB** para las pruebas conjuntas reproducidas con
`backend/.venv312/bin/python backend/lab04/run.py --stage E`.

- 17 métodos funcionales: login, MFA TOTP/backup, refresh, revocación, registro,
  concurrencia/locks, guards, rollback y separación humana/Decision B.
- 32 comprobaciones de organizaciones, 37 de catálogo y 47 de Admin.
- 56 ataques SQL denegados, incluyendo 12 intentos de asumir roles hermanos.
- Tres perfiles inseguros rechazados por el instalador: membresía saliente,
  membresía entrante y CREATEDB.
- Revocación IAM→CP verificada con el mismo token, conexión nueva y reinicio.
- Cinco comprobaciones adicionales tenant/B: rollback de organización, sesión,
  fence y ambos outboxes; suspensión durable; separación humana; reactivación sin
  resurrección; UPDATE adversarial rechazado.

No son todos escenarios únicos: se reportan métodos, peticiones e invariantes por
separado. [Evidencia conjunta E](evidence/E.json),
[clasificación de operaciones](evidence/operation-outcomes.csv).
Este CSV distingue ALLOW, autenticación/autorización, validación, tenant, gobernanza
y política SQL; aclara los redirects de login/guardado frente a redirects de rechazo.
Los campos `kind` de los logs de prueba originales son etiquetas generales, no
la clasificación final de aceptación.

## H. PostgreSQL Isolation & Results

Cada ejecución creó un directorio nuevo 0700, cluster independiente, socket Unix
privado, base vacía y roles sintéticos; sin TCP, sudo, servicios compartidos ni
workers. Se construyeron settings sintéticos sin cargar settings activos ni dotenv.
Hubo **cero migraciones financial**. Las credenciales y JWT efímeros se eliminaron
con el runtime después de verificar data_directory, ausencia de TCP y tablespaces
externos. El último cluster fue `/tmp/adminapps-lab04-iskrsglq/runtime` y ya no existe.

Los fallos de preparación del arnés se corrigieron: apertura de credenciales con
Path.open, columna equivocada en un ataque, expectativa 401/403, SQLSTATE psycopg3,
captura de salida del reinicio, fixture de producto ya sembrado y evaluación de
has_sequence_privilege sobre relaciones no-secuencia. No son PASS históricos ni
se ocultan mediante una reclasificación. La evidencia E corresponde a la ejecución
final completa, con limpieza confirmada. No se retuvieron tokens completos en los
artefactos publicados.

## I. LAB02 Revocation Invariants

El access original pasa de 200 a 401; refresh revocado es denegado. DELETE/reinsert
falla con `42501`. Tras reconexión y reinicio, el hash del access es idéntico y el
handler no se ejecuta. La misma propiedad se verifica en control plane para un
bearer emitido por IAM, incluyendo el endpoint de invitaciones. No hay DELETE,
TRUNCATE, DDL, EXECUTE auxiliar, membresías ni setval que restauren autoridad.

Las migraciones users 0005/0006, integration 0010, el instalador LAB02 y settings
activos son idénticos al baseline. [Hashes y fuentes probadas](evidence/final-source-hashes.json).
La garantía excluye al propietario/administrador capaz de alterar triggers o hacer
restore. No afirma inmunidad frente a toda escritura SQL dentro de permisos legítimos.

## J. Consumer Compatibility

ISO Smart: B **35/35** y D **36/36**, PASS_OFFLINE.
MedSupplier: B **35/35** y D **36/36**, PASS_OFFLINE.
Cero intentos de DB/red según las guardas. Son adaptadores/JWT/views reales con
transporte central y persistencia simulados; **no es HTTP E2E entre productos**.
No se modificó ningún consumidor y ambos conservaron sus HEAD y worktrees limpios.

AdminApps offline: R1 integración 7, MFA sucesora 21, sesiones humanas 25,
Decision B 43 y Decision D 57: **153 ejecuciones PASS_OFFLINE**. Las suites tienen
herencia/solapamientos. [Resúmenes](evidence/offline.json).

## K. Tests & Historical Reconciliation

Se preservan los 231 PASS / 9 FAIL / 1 ERROR históricos de LAB01, los estados LAB02
y LAB03 y las excepciones de consumidores de sus suites originales. Las suites
sucesoras ejecutadas ahora no convierten esas suites históricas en verdes.
No se editó ningún test histórico. Los módulos `lab04/test_lab.py` y
`test_extended.py` son copias del arnés con compatibilidad de driver; solo la selección
explícita de 17 métodos es aceptación del runner. No se ejecutó ni certificó la
suite financiera completa.

## L. Git Commit/Push Ledger

Cada fila usa la rama de desarrollo local `lab04/runtime-boundaries-20261021` y la
rama remota de entrega `lab04/reviewed-delivery-20261021`. El remoto es
`git@github.com:felipuh/adminapps.git`. SHA completos y corrección B:
[GIT-LEDGER.json](GIT-LEDGER.json).

| Objetivo | Estado técnico | Pruebas | Commit local | Rama publicada | SHA remoto verificado |
|---|---|---|---|---|---|
| LAB04-A | PASS_POSTGRESQL_LAB, frontera optativa | procesos, SQL, 17 métodos, reinicio | 7015205a | lab04/reviewed-delivery-20261021 | d00bd608 |
| LAB04-B | PASS_POSTGRESQL_LAB, corrección incluida | 32 casos, consumo IAM, regresiones | 2d0a6bbe + 8b09b751 | lab04/reviewed-delivery-20261021 | b3b11be0 → b14ad0bc |
| LAB04-C | PASS_POSTGRESQL_LAB, comercial retenido | 37 casos y regresiones | 25cb5562 | lab04/reviewed-delivery-20261021 | 7db3cd91 |
| LAB04-D | PASS_POSTGRESQL_LAB, Admin restringido | 47 casos y regresiones | e3dc7fde | lab04/reviewed-delivery-20261021 | 267993df |
| LAB04-E | PASS_POSTGRESQL_LAB + PASS_OFFLINE | conjunto E y 295 ejecuciones offline | ef4919cb | lab04/reviewed-delivery-20261021 | af2377f2 |

Los SHA originales no se publican por el bloqueo de historia. Los commits de
entrega contienen los mismos archivos revisados; su manifest SHA256 permite
compararlos. Hubo commits primero en el checkout de desarrollo, no solo en el
worktree de publicación. No se solicitaron aprobaciones repetidas ni hubo merge,
despliegue o push a main/master.

## M. Remaining Security/Functional Blockers

1. **BLOCKED_BY_EXTERNAL_DEPENDENCY**: perfil para el esquema financiero completo,
   Financial S3, Phase31.5, E/F/G, cuotas, trials, ownership compartido y condiciones
   comerciales. El instalador rechaza tablas financieras no revisadas.
2. **NOT_EVIDENCED**: distribución operativa de secretos, routing entre procesos,
   integración HTTP federada, perfil de servicios técnicos completos, entrega y
   retención de outboxes. El proceso events probado es únicamente lector.
3. **PARTIAL**: paridad de escritura con el Django Admin histórico. El sitio
   preparado limita escrituras a su whitelist; el resto usa CP/IAM o permanece
   retenido. No se concedieron permisos generales para abrir todas las superficies.
4. **Bloqueo Git de seguridad**: la historia original no es publicable desde esta
   ejecución. El overlay está sincronizado; sanear el repositorio completo y
   tratar sus secretos históricos requiere un trabajo separado.

Los criterios LAB04-01..18 quedan demostrados dentro del alcance descrito salvo
la compatibilidad integral/operativa de 01, 07, 09, 13 y la publicación de historia
original en 17, que conservan los límites anteriores. No se declara PASS global.

## N. Final Worktree Status

Al cerrar el checkpoint E, HEAD local `ef4919cb34a965ce8b8b564c03db419edbb091ea`,
sin upstream deliberadamente; entrega/upstream remoto
`af2377f2016caba709cbf4d7e7b65bf99297ebee`. Seis commits de ingeniería en cada rama
(A, B, corrección B, C, D, E), todos entregados; el cierre documental añade un
checkpoint posterior sin cambios funcionales.

Último status del checkpoint E:

```text
## lab04/runtime-boundaries-20261021
## lab04/reviewed-delivery-20261021...origin/lab04/reviewed-delivery-20261021
```

Cero archivos modificados/no rastreados de objetivos cerrados. No se añadieron
ignores ni se eliminó trabajo necesario. Excluidos de publicación: historia
original, .env, dependencias locales y logs/runtime privados. El SHA del cierre
documental y el último status tras su push se registran fuera del repositorio en
`/tmp/adminapps-lab04-final/git-final.json`, evitando una autorreferencia de commit.

## O. Next Engineering Slice

Revisar el esquema financiero retenido y el contrato del servicio técnico antes
de ampliar el instalador; adjudicar qué operaciones adicionales pertenecen al
Admin frente a CP; preparar una historia completa sanitizada y el plan de
activación por procesos. Esas decisiones no autorizan despliegue ni cambios de BD.

Se conservan explícitamente:

```text
PRODUCTION_READY = FALSE
NO_DEPLOYMENT
NO_SHARED_DB_MUTATION
GOVERNANCE_PRESERVED
PHASE31_5 = EXECUTION_HELD
S3-IMP-01 = BLOCKED_PENDING_AUTHORITY
S3_DECISION_02A_NOT_CLOSED
REC-2FA-04
REC-SSO-02
REC-SSO-03A
REC-SSO-03B-CH
DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED
```
