# S3 — Authorization Boundary & Runtime Gates

Fecha de preparación: 2026-10-09, America/Costa_Rica.
**AUTORIZACIONES FUTURAS: PENDING. S3_DECISION_02A_NOT_CLOSED.**
Documento de preparación; no es un runbook aprobado ni una orden de ejecución.

## Fronteras de autoridad

Fuente de autorización actual: solicitud de preparación documental, hash/ruta
REQUEST en el [registro de integridad](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md#source-integrity). Autoriza solo
los cinco documentos nuevos y las verificaciones estáticas de esta entrega.
D02 conserva su aprobación histórica acotada; no se vuelve permiso permanente
para implementar nuevas recomendaciones o ejecutar laboratorios.

| Gate | Resultado que puede autorizar una autoridad designada | Evidencia concreta previa | Estado actual |
| --- | --- | --- | --- |
| G-DOC | Preparar este paquete documental. | Solicitud actual, fuentes y baseline. | Alcance documental concedido por solicitud; trabajo realizado. |
| G-ARCH | Elegir/rechazar/modificar AJ individual con reservas. | ADR, matriz, hashes, mandato, parámetros y riesgos. | PENDING_HUMAN_APPROVAL |
| G-IMP | Preparar patch de un slice y pruebas offline delimitadas. | AJ aplicables resueltos, slice/archivos/cambios/exclusiones y rollback. | PENDING |
| G-OS | Provisión/uso acotado de identidades, paths y procesos de ensayo. | Runbook exacto, recursos propios, permiso de custodio y teardown. | PENDING |
| G-PG | Run PostgreSQL sintético específico. | Patch/harness revisados y SHA, comandos/entorno/auth/roles/manifest y PG-T01–11. | PENDING |
| G-IPC | Run IPC sintético específico. | Endpoints/unidades/protocolo/UIDs revisados y SHA, comandos/manifest e IPC-T01–10. | PENDING |
| G-CLOSE | Aceptar evidencia y considerar un cierre con alcance explícito. | Cadena de autoridad/resultados completa, riesgos, recuperación y cleanup adjudicados. | PENDING |

G-ARCH no implica G-IMP; G-IMP no implica G-OS/G-PG/G-IPC. G-PG no autoriza sockets
financieros ni G-IPC una DB. Integración exige ambos permisos vigentes y G-OS
cuando corresponda. G-CLOSE tampoco habilita producción, S4–S6, integración de
productos, inferencia/proveedores o Git. Sin campo aplicable resuelto, el gate no
se satisface por silencio, por nombre del rol ni por una recomendación.

## G-ARCH — Acta de arquitectura

Entrada: [ADR](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md), [matriz de 19 decisiones](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md), [plan](ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md),
fuentes/hash y [BLOCKER](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md#blockers). Debe resolver AJ-G01 y decisiones
aplicables al siguiente slice; no es necesario fingir aprobación global para
registrar una decisión parcial. Una decisión parcial no resuelve sus dependencias.

Contenido mínimo por AJ: opción elegida/rechazada, desviaciones, contrato y SHA,
firmante y evidencia de mandato, fecha efectiva/zona, condiciones, pruebas,
riesgos aceptados, exclusiones y referencia al acta. Debe distinguir interpretación
wire de D02 frente a nueva política C-B; si modifica mensaje/versión, se necesita
acto explícito distinto, no aprobación retroactiva de A02 completa.

Resolver además: vínculo de adopción V11, frontera TLS/local (B-T01), topología
local, disposición de socket PG para UIDs distintos (B-D01), perfil de material,
NUM-C/P/I/L, administración bajo FORCE RLS, tratamiento de sesiones y UNKNOWN.
Si una alternativa excede D02, volver a contrato antes de diseñar su implementación.

Salida actual: **PENDING**, sin firmantes inventados ni fecha efectiva.

## G-IMP — Permiso acotado para preparar implementación

Antes de pedir este permiso deben existir decisiones aplicables y una propuesta
revisable del slice: propósito, archivos previstos, cambios mínimos, invariantes,
pruebas, evidencia y rollback. Los nueve slices están preparados en PLAN; deben
incorporar las selecciones efectivas humanas cuando existan.

| Campo del permiso | Valor pendiente |
| --- | --- |
| Acta G-ARCH / AJ aplicables / hashes | PENDING |
| Slice(s) y orden autorizado | PENDING |
| Archivos existentes y nuevos permitidos | PENDING |
| Cambios exactos, invariantes y exclusiones | PENDING |
| Perfil wire/SQL/auth/protocolo y parámetros efectivos | PENDING |
| Pruebas offline permitidas; entorno sin DB/IPC/host privilegiado | PENDING |
| Custodio/revisor y política de rollback/preservación | PENDING |
| Firmante, mandato, firma, fecha efectiva/zona | PENDING |

Una vez autorizado, preparar patch/harness, pruebas offline y runbooks concretos
**antes** de solicitar permiso runtime. No pedir aprobación operacional para
código inexistente ni usar comandos históricos como si ejecutaran la matriz nueva.
Después de preparar el patch, registrar revisión y SHA; un cambio posterior
invalida la correspondencia del permiso runtime hasta su revisión aplicable.

## G-OS — Identidades y recursos del ensayo

No es una reedición de Host Lab. Permiso futuro restringido a lo necesario para
PG peer, IPC y servicios reales del slice. La autorización debe enumerar cuentas
nuevas o existentes autorizadas, UID/GID y exclusividad, grupos por canal,
servicios/unidades, binarios, rutas absolutas y ownership, y mecanismo exacto de
provisión/desprovisión. El custodio verifica ausencia de procesos ajenos bajo
esos UIDs; el nombre `s3*` histórico no autoriza recreación/reutilización.

Si provisioning requiere privilegios, el operador/custodio autorizado y los
comandos concretos deben figurar en el acta. El harness PG no se ejecuta como
root para resolver acceso: el data directory queda privado del principal DB y
el socket en ruta distinta administrada con traversal mínimo probado por cada UID.
HBA/mapping autentican roles; DAC del socket solo restringe acceso al endpoint.

G-OS debe describir inspección de hardening del servicio real, separación de
claves/configuración, lifecycle y recursos a conservar ante fallo. No chmod de
`/root`, cambios de política host, sudo genérico o limpieza global implícitos.
Autoridad propuesta: plataforma/custodio host + seguridad; firma y fecha PENDING.

## G-PG — PostgreSQL runtime validation

Prerrequisitos técnicos para convertir el borrador en solicitud ejecutable:

1. IMP-01–06 revisados, CR/MT y controles offline aceptados; decisiones AJ-P
   aplicables, versión PG/Python/driver y mecanismo auth explícitos. No instalar
   herramientas implícitamente. Revisión separada si versión difiere de fuentes.
2. Harness sucesor completo con SHA y comandos exactos, cwd, intérprete y
   selectores de PG-T01–11. El actual PGSCRIPT con `trust`, stop ignorado y PASS
   antes de cleanup **no es apto** como autorización del nuevo ensayo.
3. Clúster sintético privado identificado, data/socket/evidencia paths y permisos;
   TCP deshabilitado, sin puerto/socket de DB compartida. Configuración exclusiva
   rechaza DSN/variables externas; no carga `.env`, scheduler o servicios generales.
4. Identidades seed/migration/inspector/executor/issuer/runtime distintas según
   matriz; G-OS si corresponde. HBA sin fallback trust; peer exacto o SCRAM
   elegido. Si peer, positivos con UIDs distintos; si SCRAM, secretos efímeros
   separados y test de contraseña inválida sin exponerla.
5. Autorización expresa para initdb/start/roles/migraciones sintéticas/pruebas/
   stop/cleanup del run. Ninguna migración productiva ni catálogo reparado sobre
   la marcha. Error de owner/schema devuelve al slice, con nueva revisión/SHA.
6. Plan de captura: run ID, código revisado/ejecutado, command/stdout/stderr/exit
   redactados, identidad de operador/principal, versión, casos esperados/observados,
   aislamiento y SQLSTATE, conteos/deltas de decisiones/reservas/audit/ledger/budgets.
7. Catálogo allow-listed: roles sin passwords, memberships, owners/RLS/policies,
   funciones/prosecdef/search_path/ACL, schema/database/default ACL y auxiliares.
   No `pg_authid`, dumps completos de credenciales o DSN. Export antes del teardown.
8. Cleanup probado offline y plan real: confirmar salida de procesos/conexiones/
   socket propios antes de borrar recursos atribuibles. PASS solo tras inventario
   final. Stop fallido o recurso incierto se conserva y se registra FAIL.

| Campo runtime PG | Valor |
| --- | --- |
| Acta y firmantes/mandatos | PENDING |
| Fecha efectiva/zona y ventana de ejecución | PENDING |
| SHA de patch/harness/fixtures/configuración pública | PENDING |
| Versión/host sintético/principal/clúster/data/socket/evidencia | PENDING |
| Roles/UIDs/auth/map/HBA y permiso G-OS | PENDING |
| Comandos exactos revisados / cwd / variables permitidas | PENDING |
| PG-T01–11, sincronización/fault injection y criterios por caso | PENDING |
| Rollback/cleanup y custodia/retención | PENDING |
| Autorización de ejecución G-PG | PENDING |

Positivo requiere conexión saludable con principal correcto; negativo debe ser
atribuible a auth/ACL/RLS/trigger o validación esperada. Error genérico, servidor
caído o transacción ya abortada no es prueba del control. La inspección admin
puede observar invariantes, nunca sustituir al usuario del positivo.

## G-IPC — IPC runtime validation

Prerrequisitos: IMP-05/06 revisados y hashes; VAL-01 aceptado según secuencia;
G-ARCH/I01–I06 y C01/C02 efectivos; B-T01/B-D01 resueltos; protocolo completo con
límites, nombres/UIDs/paths, respuesta, errores, revocación y UNKNOWN. G-OS debe
cubrir cada proceso/cuenta/recurso. G-PG independiente si este run conecta a DB.

| Campo runtime IPC | Valor |
| --- | --- |
| Acta, firmantes/mandatos, fecha efectiva/zona | PENDING |
| Host/topología local y alcance TLS/frontera externa | PENDING |
| SHA de endpoints/clientes/unidades/harness/config/protocolo | PENDING |
| Tabla UID/GID → endpoint → operación, autenticación mutua | PENDING |
| Rutas/owner/grupo/modos/ACL; recursos manifest/run ID | PENDING |
| Bytes/profundidad/prefijo/deadlines/concurrencia/rate-limit/códigos | PENDING |
| Comandos exactos arranque/pruebas/faults/stop/cleanup | PENDING |
| IPC-T01–10: transporte aislado / integración PG declarada | PENDING |
| G-OS y G-PG para destino/run aplicables | PENDING |
| Tratamiento sesiones abiertas/revocación/UNKNOWN/retención | PENDING |
| Autorización de ejecución G-IPC | PENDING |

Ensayar transporte con contador de despacho antes de integrar PG. La identidad
se obtiene del kernel en ambas direcciones; UID/GID/PID JSON no la reemplazan.
Un intruso bloqueado por DAC no demuestra que la allow-list funciona: incluir
caso con acceso de grupo pero UID no autorizado y control positivo del servidor.
Verificar servidor sustituto y efectos de revocación en conexiones abiertas.

PG-T08/09 bajo permiso prueban efecto financiero en el canal real. Contador IPC
por sí solo no demuestra idempotencia DB. Pérdida de respuesta posterior al envío
es UNKNOWN; solo rollback confirmado permite clasificar no commit. No liberar
fondos, despachar proveedor ni fabricar invocation nueva para salir de incertidumbre.

## Evidencia y teardown comunes

Antes del run, manifest con recursos esperados y verificación de colisiones;
después de cada creación, identidad efectiva: tipo/path/dev/inode/owner y run ID.
Procesos requieren identidad que resista reciclado de PID (inicio/cgroup según
método aprobado), sin matar por coincidencia de nombre. Registrar comandos,
retornos, cronología y hash exacto ejecutado, preservando secretos fuera de logs.
El manifest no basta si su custodia o atribución es incierta.

Secuencia prevista: detener admisiones → cerrar listeners/clientes → drenar según
política → detener/esperar procesos propios → preservar evidencia externa a la
raíz temporal → verificar salida y atribución → unlink/eliminar solo recursos
propios → inventario final. Conservar evidencia y declarar FAIL ante stop fallido,
proceso vivo o mismatch. No emitir PASS anticipado, `rm -rf` indiscriminado,
`pkill` global ni limpieza de recursos históricos.

EXIT/INT/TERM se prueban según runbook; SIGKILL no ejecuta trap, por lo que la
recuperación posterior requiere manifest conservado, nueva comprobación de
ownership/proceso y autorización aplicable. No repetir Host Lab para completar
un campo de evidencia que falta del run histórico.

## G-CLOSE — Aceptación de evidencia

Solo después de las validaciones autorizadas, la autoridad revisa:
actas/mandatos, correspondencia SHA y permisos, resultados CR/MT/PG/IPC completos,
positivos y negativos reales, carreras/rollback/replay/UNKNOWN, grant/ledger,
revocación/sesiones, runtime de servicios reales, recursos residuales y límites
host aceptados. S3-CLOSE-01 prepara esa reconciliación sin cambiar evidencia.

B-R01 exige adjudicar recuperación sin construir aquí status/HTTP/S4. Evidencia
de laboratorio mediante inspector no satisface recuperación de clientes. Si
se desea cierre limitado de un subcomponente, el acta debe decirlo y conservar
lo que sigue pendiente; no permite declarar Decision 02-A plenamente cerrada.

Autoridad y firma de cierre: **PENDING**. Hasta evidencia suficiente y aceptación
formal: **S3_DECISION_02A_NOT_CLOSED**. Phase31.5 continúa **EXECUTION_HELD**.
