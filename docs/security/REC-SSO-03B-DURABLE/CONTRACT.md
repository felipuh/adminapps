# REC-SSO-03 / Decision B — contrato de sesiones durables

Fecha: 2026-10-15. Estado local únicamente. PRODUCTION_READY = FALSE.

C/H conserva `auth_contract=rec-sso-03b-ch-v1`, RSA separado CENTRAL/LOCAL,
issuer, audience singleton, producto fijo y cliente resuelto por credencial.
B exige adicionalmente `lifecycle=rec-sso-03b-v1`, `sid` UUID central,
`sg` entero positivo (generación), `av` entero positivo (versión de autoridad)
y `auth_time` Unix. Un JWT C/H sin estos campos requiere reautenticación.

`sid` permanece durante rotación. `jti` identifica cada token access/refresh;
no es identidad de sesión ni contador de autoridad. El contador global
SSOSecurityFence.generation incrementa bajo bloqueo de fila en cada emisión,
rotación y revocación. Nunca disminuye en una transacción confirmada. Rollback
puede recuperar números nunca publicados. `authority_epoch` cambia con cualquier
mutación relevante para invalidar autenticaciones/challenges que estén en vuelo;
no es un timestamp. `av` se asigna de la generación al emitir y aumenta al revocar.
La introspección exige coincidencia exacta de la generación/autoridad del registro.

La fila SSOSession contiene usuario UUID, cliente FK, tenant UUID, producto,
estado, autenticación/creación/expiración, revocación y motivo, correlación UUID,
jti individuales y enlace digest/generación MFA. No almacena tokens ni secretos.
El challenge MFA consumido solo puede enlazar una sesión (constraint parcial).
UserSession heredada no cumple este contrato y queda fuera de la autoridad SSO.

## Operaciones y atomicidad

AdminApps exige PostgreSQL, autocommit de entrada y transacción durable propia.
Orden de locks: fence global, SSOSession (`FOR UPDATE OF self`). Las filas de
usuario/MFA no se bloquean desde este servicio; REC-2FA-04 conserva su transacción
previa. La generación del challenge y su contexto se comprueban nuevamente.
La firma se produce dentro de la transacción; la respuesta sale después del commit.
Un fallo al firmar revierte sesión/outbox/contador. Si se pierde la respuesta tras
commit, no se vuelve a aceptar la generación anterior: nueva autenticación.

Triggers PostgreSQL BEFORE vigilan cambios relevantes incluso QuerySet.update,
bulk_update, SQL y relaciones M2M. Serializan con el mismo fence, incrementan
la época de autoridad, revocan filas y escriben outbox en la misma transacción.
Las comparaciones OLD/NEW incluyen ambas direcciones para impedir ABA.
La recepción/introspección relee las identidades, membresía, tenant, producto,
credencial y MFA vigentes. Un cambio entre autenticación del servicio y uso se
rechaza por época. No hay caché de ALLOW.

La serialización global es deliberadamente conservadora: requiere medir carga,
latencia, deadlocks e interacciones con otras transacciones antes de activación.
READ COMMITTED es la precondición del laboratorio. La decisión de introspección
se lineariza bajo el fence; no cancela operaciones empresariales ya autorizadas
ni constituye una transacción distribuida entre productos.

## Alcance de invalidación

| Evento | Alcance |
|---|---|
| Logout / revocación administrativa | Una sesión; todas sus generaciones |
| Rotación | Generación previa de una sesión; conserva vencimiento/autoridad |
| Usuario, password, bloqueo, identidad, rol global, grupos/permisos | Todas sus sesiones |
| Membresía/rol de organización | Usuario × tenant, ambos lados de un cambio |
| Tenant deshabilitado o cambio de suscripción vinculada | Todas las sesiones de tenant |
| Cliente deshabilitado o contrato modificado | Todas las sesiones de cliente |
| Credencial deshabilitada/revocada/rotada/modificada | Sesiones de clientes ligados al principal |
| Tenant retirado/agregado al cliente | Cliente × tenant |
| Estado/generación/secreto MFA | Todas las sesiones del usuario |
| Cambio global de política MFA | Hook autorizado revoke_mfa_policy; revoca todas e incrementa época |
| Producto / entitlement | Producto o tenant × producto |
| Plan/suscripción o permisos de grupo globales | Todas; política conservadora explícita |

No se emiten scopes write ni se convierten cambios de rol en autorización nueva.
Las políticas comerciales históricas pendientes permanecen abiertas en la matriz.
Cambios de configuración MFA fuera de DB requieren el hook y una ventana de
acceso cerrado; no existe detección automática de edición de archivos/settings.

## HTTP

`POST /api/integration/sso/introspect/`: contexto C/H y `token` CENTRAL access.
ALLOW solo tras validación durable y autoridad viva. Devuelve claims firmados,
active=true y proyección viva de usuario/membresía/producto. Nombre, código y
membresías se obtienen de introspección para evitar JWT/cookies grandes.
Los datos de identidad de autorización, generación y expiración deben coincidir
con el JWT. Ausencia/revocación/expiración/configuración ilegible => DENY.
Los errores contienen mensajes genéricos, nunca JWT, claves ni errores SQL.

`POST /api/integration/sso/logout/`: mismo contexto + prueba CENTRAL access del
request autenticado. Idempotente mientras la prueba criptográfica no expire:
revocar dos veces no duplica outbox ni contador. Una generación previa firmada
puede revocar su misma sesión, lo cual resuelve la carrera logout/rotate.
No puede seleccionar otro usuario/cliente/producto/tenant.

`POST /api/integration/sso/rotate/`: mismo contexto + CENTRAL access vigente.
Consume una generación completa, cambia jti y sg, y retorna `tokens` con prueba
CENTRAL nueva; NO extiende exp ni auth_time, NO usa central refresh para ampliar
la sesión. Dos solicitudes con la misma generación solo pueden confirmar una.
Los central refresh JWT emitidos no tienen una ruta de canje; se rechazan donde
se exige access. No almacenar/usar esos tokens en consumidores.

ISO y MedSupplier vinculan LOCAL a `sid`, `sub`, tenant, producto, sg, av y
exp CENTRAL. Cada uso, creación, refresh y cambio de tenant exige autoridad viva.
Refresh rota en AdminApps y vuelve a verificar la nueva prueba antes de emitir.
No existe fallback de autenticación local ni de disponibilidad. Logout usa el
request autenticado; un refresh ajeno en el body no permite seleccionar sesión.
MedSupplier conserva Bearer/body; ISO conserva cookies HttpOnly y CSRF.

ISO limita max-age al exp firmado, 4096 bytes por Set-Cookie y 7000 bytes para
el par en Cookie. Son presupuestos de aplicación, NO límites de infraestructura
medidos. Un caso demasiado grande falla cerrado. El código nginx del repositorio
no fija large_client_header_buffers; el valor efectivo activo NO fue consultado.
El backend limpia cookies en fallos de vistas de sesión. El frontend elimina su
estado al fallar refresh; el backend deniega siempre aunque sobreviva una cookie.

## Expiración y UX

300 segundos siguen siendo un máximo absoluto desde autenticación. Refresh
no aumenta ese máximo. Navegación, múltiples pestañas y formularios prolongados
pueden requerir nuevo login y MFA; peticiones con pruebas revocadas se deniegan.
Un refresh concurrente perdedor no se recupera usando el token anterior.
Alternativas pendientes de producto/seguridad: reautenticación explícita conservando
borradores seguros; TTL central mayor; protocolo de renovación central con nueva
política MFA. Solo se implementaron expiración efectiva, rechazo y limpieza del
estado local; NO se autorizó ni implementó ampliación silenciosa de TTL.
Logout con autoridad inaccesible devuelve error; limpiar UI no demuestra revocación
central. El consumidor no puede conceder acceso durante esa indisponibilidad.

## Outbox

TenantIntegrationOutbox fue inspeccionado: versiona aggregates tenant y no comparte
la granularidad sesión/generación. Se conserva su patrón transacción + outbox en
SSORevocationOutbox. UUID por evento, unique(session,generation), cliente/producto/
tenant/correlación, intentos y próxima fecha. `session_events.deliver_one` es un
adaptador invocable con transporte autenticado inyectado: reintento exponencial
acotado y ACK de event_id. Ningún worker, endpoint de ingesta o transporte real
fue activado. Receptor opcional usa watermark max; un evento tardío nunca reduce
la invalidación. El evento nunca concede acceso ni reemplaza introspección.

## Activación y reversión — NO EJECUTADAS

1. Revisión y autorización separada de laboratorio PostgreSQL desechable, roles,
   migraciones 0008, 0009 y 0010, keyrings y provisión de SSOClient/tenants.
2. Verificar todos los triggers/constraints, aislamiento/roles, SQL emitido,
   carreras reales, rollback, conexiones independientes y MFA en laboratorio.
3. E2E HTTP y navegador con cookies/configuración representativas y failover;
   matriz de versiones mixtas. Tokens anteriores exigen nueva autenticación.
4. Activación coordinada solo tras autorización externa. Nunca degradar a C/H
   sin revocación para recuperar disponibilidad.
5. Reversión segura cierra acceso y conserva registros/counters. Reverse de 0010
   revoca activos, incrementa época y deshabilita fence antes de retirar triggers.
   Reaplicar 0010 conserva contador y revoca cualquier activo previo antes de habilitar.
   Runtime B sin fence habilitado DENY. No volver a código antiguo que ignore estado.
   NO revertir 0009 para borrar historia. Restaurar backups exige corte de acceso,
   invalidación global y nuevos contadores/llaves según revisión; no hay rollback
   productivo verificado.

Las tablas nuevas son autoridad IAM global en AdminApps, no tablas empresariales
accesibles por tenant/consumidor. El rol DB central debe ser exclusivo. No se
presenta aislamiento por RLS ni PostgreSQL transaccional como probado offline.

Gobernanza: S3-IMP-01; S3_DECISION_02A_NOT_CLOSED; PHASE31_5 = EXECUTION_HELD;
REC-2FA-04; REC-SSO-02; REC-SSO-03A; REC-SSO-03B-CH preservados.
NO_DEPLOYMENT / NO_COMMIT / NO_PUSH / GOVERNANCE_PRESERVED.
