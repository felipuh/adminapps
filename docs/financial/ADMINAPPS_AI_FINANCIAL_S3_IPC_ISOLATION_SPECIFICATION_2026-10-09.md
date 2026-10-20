# S3 Decision 02-A — IPC Isolation Specification

Fecha: 2026-10-09, America/Costa_Rica. Documento C.
Estado: `S3_IPC_ISOLATION_PENDING`; transporte financiero `NOT_IMPLEMENTED`.
Modelo preparado para aprobación, sin sockets, procesos ni identidades creados.

## Frontera realmente encontrada

[Decision 02-A](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md)
requiere issuer/executor aislados y reconoce que no provisiona transporte
autenticado. El [Existing VM report](ADMINAPPS_AI_FINANCIAL_S3_EXISTING_VM_ISOLATION_EXECUTION_2026-10-09.md)
§§F/N pide una futura frontera local autenticada con credenciales de peer.
`issuer.py::issue_admission_capability` y
`executor.py::FinancialExecutor.admit_reserve` son interfaces Python; el test
existente instancia ambos dentro del proceso de tests. No equivalen a IPC.

Búsqueda focalizada en `backend/apps` y `backend/config`: no implementación
financiera de AF_UNIX/SO_PEERCRED/socket, FIFO, colas POSIX/System V, broker,
Celery/Redis o worker financiero con contrato propio. No se extiende esa ausencia
a todo el ecosistema. Los sockets PostgreSQL del verifier son su conexión DB,
no un canal issuer → executor. El HTTP V1.1 §10 sigue siendo propuesta interna,
sin endpoint financiero implementado; no elegir HTTP como transporte existente.

| Superficie | Propietario/grupo/permisos | Autenticación, autorización y ciclo de vida |
| --- | --- | --- |
| Llamadas Python issuer/executor | Identidad del proceso que las importe; sin permisos de endpoint. | Credencial producer hashed_v1 y grant al emitir; firma/hash al ejecutar. Sin autenticación de proceso llamante. No hay cleanup IPC. |
| `/run/smart3ai-s3-lab/issuer` | Fixture: `s3issuer:s3labipc`, 0710; raíz root:root 0711. | Placeholder DAC, sin socket. Grupo sintético compartido no es allow-list de operaciones. Eliminado según reporte del usuario, no reinspeccionado. |
| `/run/smart3ai-s3-lab/executor` | Fixture: `s3executor:s3labipc`, 0710. | Mismo límite: permisos de directorio no demuestran entrega, lectura o escritura IPC denegada. |
| Canal local autenticado futuro | No definidos aún owner/group/socket mode, UID mapping ni protocolo. | `SOURCE_INSUFFICIENT` para contrato wire; `NOT_IMPLEMENTED` para transporte. Requiere decisión de diseño antes de harness runtime. |

No se crean obligaciones de POSIX IPC, pipes o broker ausentes. Se propone UNIX
pathname socket como candidato coherente con el informe previo, **no como
decisión aprobada ni mecanismo ya utilizado**. En Linux, SO_PEERCRED permite
consultar credenciales del peer; permisos pathname y autenticación del peer
son controles distintos. Los sockets abstractos tienen otras reglas de permisos;
no intercambiarlos silenciosamente. Fuente técnica:
[Linux unix(7)](https://www.man7.org/linux/man-pages/man7/unix.7.html).

## Decisiones que bloquean implementación del transporte

| Gate | Definición que debe aprobarse | Restricción conservadora para el sucesor |
| --- | --- | --- |
| IPC-C01 topología | Quién llama a issuer, quién entrega capability al executor y quién recibe respuesta. | No asumir entrega directa issuer→executor frente a relay runtime. Ninguna ruta da SQL libre, private key ni DSN al runtime. |
| IPC-C02 identidades | UIDs/GIDs de ensayo y tabla peer → endpoint → operaciones. | No reutilizar `felipe` o identidades de productos desplegados. Nombres s3* históricos no autorizan recrearlos. GID compartido no basta para autorización. |
| IPC-C03 endpoints | Paths exclusivos del run, dueños, grupos, modos de directorio/socket, escritor que crea el endpoint. | Directorios separados por servicio; modo mínimo que permita peers aprobados. Bind solo en ruta comprobada; fail ante colisión/symlink. No unlink de un socket previo desconocido. |
| IPC-C04 protocolo | Framing, schema_version, límite de bytes/profundidad, plazo de lectura, respuesta, correlación y códigos. | Exponer solo operación `admit_reserve`; sin SQL, rutas de archivo ni comandos arbitrarios. No fijar un máximo numérico como contrato existente. Rechazar mensajes parciales/múltiples inesperados/unknown fields. |
| IPC-C05 issuer | Cómo obtiene producer credential y material completo para validar scope/grant y hash. | `issuer.py` recibe hash ya calculado; no prueba por sí solo recomputación ni TenantProjection completa. Resolver contrato sin exportar credencial o prompts a logs. |
| IPC-C06 executor | Allow-list pública issuer/kid, claim binding y correspondencia tenant_assertion ↔ organization claim. | Executor verifica firma y material antes de DB. No aceptar UID/tenant/rol del payload como autenticación del peer. |
| IPC-C07 revocación | Retirada de peer, clave y grant; efecto sobre conexiones existentes y solicitudes en vuelo. | Aplicar política por solicitud; nuevas conexiones denegadas tras corte. Registrar semántica para conexiones abiertas, no asumir que borrar archivo revoca un descriptor abierto. |
| IPC-C08 recuperación | Timeout, respuesta perdida, restart, recursos huérfanos y run manifest. | Nunca convertir error en admisión ni volver a reservar con identidad nueva; reconciliar invocation original. No afirmar endpoint status implementado. |

## Amenazas y controles a demostrar

Peers no autorizados pueden intentar conectar, suplantar UID en JSON, usar un
grupo compartido, cambiar tenant/producto/hash, reproducir mensajes, consumir
recursos con frames incompletos o sustituir paths. El harness deberá observar
denegación efectiva y ausencia de efecto financiero, no solo mode/owner.
El caller autorizado a conectar sigue necesitando credencial/grant/capability
válidos; identidad Linux no equivale a autorización de tenant.

Autenticar peer con evidencia del kernel y validar servidor según el mecanismo
aprobado; rechazar mismatch aun cuando DAC permita conexión. Mantener integridad
criptográfica de capability y recomputación del material, operaciones cerradas,
errores sin secretos y límites de recursos. El executor tiene solo claves
públicas y su configuración DB; issuer tiene signer y sus lecturas aprobadas.
No pasar descriptores de secretos/DB entre peers. Compromiso root o del executor
de confianza queda como riesgo residual explícito de Decision 02-A.

## Diseño del harness y pruebas futuras

Fixtures: tenant A/B, producer sintético con grant explícito, material acotado,
Ed25519 efímero, pares de identidades autorizadas y una identidad intrusa.
Separar tres niveles de evidencia: lógica pura (sin IPC), transporte real con
UIDs distintos y contador sintético de operación, integración DB sintética
posterior bajo S3-PG-03. Ningún nivel sustituye a otro.

| Caso | Positivo obligatorio | Negativo y evidencia efectiva |
| --- | --- | --- |
| IPC-T01 conexión | Peer aprobado conecta al endpoint correcto y operación permitida retorna respuesta acotada. | UID intruso con path conocido no conecta o recibe denegación autenticada antes de procesar; comprobar que el servidor estaba sano. |
| IPC-T02 identidad | UID/GID/PID del peer obtenido del kernel coincide con allow-list. | UID correcto solo en JSON, GID compartido/UID incorrecto y peer inesperado fallan; logs de código de rechazo y cero despacho. |
| IPC-T03 lectura/escritura | Cada servicio consume solo su canal y archivos permitidos. | Peers ajenos no reciben respuestas de otro tenant, no inyectan mensajes, no crean/sustituyen endpoint ni leen buffers/secretos ajenos. DAC de archivos se registra aparte. |
| IPC-T04 autorización | Operación exacta con grant y tenant válidos llega una vez al executor. | Tenant/producto/entorno/operación incorrectos y SQL/comando/path suministrados por caller fallan antes de cualquier efecto. |
| IPC-T05 integridad | Capability válida y material coincidente admitidos por verifier. | Firma/hash/claim alterados, expirado, issuer/kid desconocido, wire no conforme: rechazo tipado, no stack trace/secretos. |
| IPC-T06 replay | Retry idéntico conserva invocation y reconcilia el mismo resultado. | Retry concurrente/conflictivo o capability revocada no causa doble reserva; el ledger real se valida solo con PG autorizado. No inventar un nonce store IPC. |
| IPC-T07 fallos | Servidor recupera tras solicitud inválida y atiende después un control positivo. | Frame truncado/oversize/timeout/disconnect/restart no ejecuta parcialmente ni habilita fallback. Medir deadline y recursos según contrato aprobado. |
| IPC-T08 revocación | Peer/clave/grant activos funcionan antes del corte. | Conexión nueva y solicitud posterior a revocación rechazadas; conexiones previas evaluadas según semántica aprobada y estado financiero comprobado. |
| IPC-T09 aislamiento directorios | Cada servicio crea solo su endpoint dentro de su runtime dir. | Peer intenta listar/escribir/renombrar/symlink en directorio ajeno: denegación real, no inferida de chmod. |
| IPC-T10 cleanup | Cierre de clientes/listeners, salida de procesos y eliminación de recursos propios. | Interrupción/startup parcial/recurso desconocido detienen cleanup inseguro; inventory posterior sin PID, socket, directorio ni descriptor retenido del run. |

Por caso registrar run ID, hash de código, UID/GID efectivos, endpoint simbólico,
versión de protocolo, resultado esperado/observado, retorno/errno o rechazo,
contador de despacho y, solo en integración aprobada, deltas DB. No registrar
tokens, private keys, raw producer credentials, DSN ni prompts.
La denegación por servidor caído o socket inexistente no es PASS de aislamiento.

## Lifecycle y cleanup propuestos

Antes de crear: inventario sin colisiones, namespace del run, manifest externo
con owner/inode/tipo/path esperados y evidencia de creación. Arranque fail-closed:
sin signer/allow-list/config válidos no habilitar listener. No comenzar nuevas
solicitudes durante teardown; cerrar listeners/clientes, esperar solo procesos
propios y verificar su salida. Eliminar pathname únicamente si concuerda con el
recurso creado y no es symlink; luego directorios propios vacíos y fixtures.
Retener manifest y evidencia ante discrepancia. No usar kill/pkill/unlink globales
ni recrear/limpiar nombres s3* históricos por conveniencia.

`S3-IPC-02` deberá preparar código y pruebas del protocolo aprobado; hoy el
contrato wire está insuficientemente definido, por lo que no se fabrica un
endpoint para poder probarlo. `S3-IPC-03` debe emitir un comando exacto después
de contar con ese artefacto y su SHA: **no existe aún comando runtime ejecutable
de IPC financiero que pueda aprobarse honestamente**. El plan incluye este gate
como STOP. Ningún socket, pipe, cola o prueba IPC real se ejecutó ahora.
