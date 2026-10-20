# Plan coordinado, reversión y aceptación de seguridad

**PROPOSED_PENDING_APPROVAL**. Todo trabajo ejecutable descrito es futuro.
Responsables indicados son funciones requeridas, sin personas o facultades
atribuidas. No hay autorización de código, DB, lab, configuración o publicación.

## Secuencia y gates

| Paso | Trabajo propuesto / responsable | Precondición y evidencia de salida |
| --- | --- | --- |
| 0. Adjudicación | Seguridad/identidad y dueños AdminApps, ISO Smart, MedSupplier; soporte/cambio para impacto. | Firmar opción A, población MFA, contrato de errores y alcance. C/H/D/B pertinentes con valores exactos, no defaults inferidos. Identidad y facultad verificables. |
| 1. Inventario autorizado | Dueños de sesión y operaciones de cada producto. | Rutas y consumidores, emisores/clientes/audiences/scopes, sesiones previas, cuentas sin factor, esquema y configuración por entorno sin extraer secretos. Inventarios DB/IdP requieren sus gates. No inventar número de afectados. |
| 2. Diseño y artefacto exacto | Equipos de los tres productos, revisores de seguridad. | Preparar P01-A-R1 compuesto y contrato/OpenAPI versionado; separar familias de sesión, transición y pruebas; hashes revisables. Mandato nuevo para escribir código. |
| 3. Regresión independiente | QA/seguridad con revisión distinta del autor del cambio. | Suites de cada repositorio con oráculo contractual externo a helpers de implementación; mismos vectores compartidos. Preservar resultados históricos y añadir evidencia sucesora. |
| 4. Laboratorio conjunto | QA/operaciones de los tres productos. | Target desechable, DB/servicios/datos sintéticos autorizados por separado. Login, sesiones, HTTP, concurrencia PostgreSQL y rollback reales; matriz de versiones completa. No mocks como única prueba. |
| 5. Preparación del corte | Dueños de producto, identidad y soporte. | Consumidores listos; rutas antiguas inventariadas y cerradas al activar; ventana, cohortes, tratamiento de sesiones previas y parada firmados. users.0004 verificada bajo gate propio, sin nueva migración implícita. |
| 6. Activación coordinada | Autoridad de cambio/operación. | Mandato de despliegue independiente, manifiesto exacto, aceptación de ambos consumidores. No activar guard aislado salvo contención explícita con cierre de bypass y pérdida de servicio aceptada. |
| 7. Observación y cierre futuro | Seguridad/QA y dueños de producto. | AC con efectos comprobados, telemetría sanitizada, ausencia de rutas alternativas y aceptación firmada. No heredar cierre de otras campañas. |

La preparación puede ser escalonada. La activación debe evitar ventanas donde
versiones antiguas puedan conceder sesiones sin MFA. Firmar antes del corte los
umbrales operativos de fallos/latencia y la ventana de observación; no se inventan
SLA. Un solo bypass confirmado o contexto cruzado aceptado obliga a detener el
canal afectado; incidencias de disponibilidad nunca justifican volver a password-only.

## Reversión segura

1. Responsable de parada: función de operación/cambio designada por cada producto,
   coordinada con seguridad; nombre y facultad pendientes en la matriz.
2. Ante bypass, error de binding, consumo duplicado, elevación de permisos o
   regresión de aislamiento: detener nuevos logins/refresh/cambio de tenant y
   operaciones afectadas según el plan firmado. Preservar evidencia sin secretos.
3. Volver únicamente a una versión previamente validada que conserve guard MFA,
   cierre local y validación de contexto. Si no existe, mantener el canal cerrado
   y reparar hacia delante. No revertir a la baseline vulnerable.
4. Ante caída de AdminApps o respuesta incierta: no emitir/extender sesión por
   contraseña local ni por caché positiva. Operaciones que exigen autoridad viva
   quedan denegadas. El tratamiento de sesiones ya verificadas respeta la política
   de frescura adjudicada; esta campaña no concede funcionamiento offline.
5. No restaurar generación anterior, contadores, backups/desafíos consumidos,
   revocaciones, claves revocadas o grants antiguos. No bajar esquema 2FA.
   Restore/DB requieren reconciliar hechos posteriores y autorización independiente.
6. Invalidar sesiones emitidas por una versión defectuosa mediante el mecanismo
   aprobado y exigir autenticación central de nuevo. El alcance y mecanismo se
   definen con B/C; no asumir que logout de un producto revoca todos.
7. Reabrir solo después de repetir negativos y positivos pertinentes en ambos
   consumidores y obtener aceptación de operación/productos. Registrar hashes,
   tiempos, fallo, contención y decisión de reapertura.

## Criterios de aceptación

**Todos NOT_EXECUTED en REC-SSO-03A.** Son exigencias para aprobación/ejecución
futuras, no evidencia de remediación. Ningún test se acepta solo por HTTP 200/403.

| ID | Escenario y resultado exigido | Evidencia / propietario |
| --- | --- | --- |
| AC-A01 | Identidad central sin MFA requerido y elegible, membresía/producto vigentes: sesión limitada al tenant/producto correcto. No convierte falta de configuración en exención. | Tests positivos de AdminApps y ambos consumidores; decisión vigente y operación protegida. |
| AC-A02 / NF01 | Legacy con contraseña correcta y MFA obligatorio: 403 valid=false/second_factor_required, sin sesión. Contraseña incorrecta no revela estado MFA. | Regresión nueva del endpoint y negativa desde ambos consumidores; conteo de sesiones/tokens cero. |
| AC-A03 / REC-2FA-04 | Contraseña → challenge sin tokens/cookie autenticada → TOTP o backup válido → sesión; inválido, expirado, replay, generación/canal ajenos deniegan. | Regresión independiente del servicio 2FA y flujos HTTP de ambos productos; conservar límites e historia de REC-2FA-04. |
| AC-A04 / MS1 | AdminApps deniega o exige MFA mientras MS tiene contraseña usable, usuario/perfil activos; también EmailBackend/ModelBackend, flag/header y superusuario. Ninguna combinación concede sesión sin central completa. | Prueba directa LoginView/serializer/cadena real; verificar que no se sintetiza prueba central ni se actualiza perfil como autenticado. Equivalente ISO para bypass. |
| AC-A05 | Timeout, DNS/TLS/red, 5xx, JSON inválido, esquema incompleto, valid no booleano, respuesta contradictoria, fallo DB/key/MFA/producto/auditoría obligatoria. Error terminal sanitizado, sin sesión ni rescate de caché. | Inyección independiente por etapa y consumidor; comprobar ausencia de cookies/access/refresh, datos protegidos y exposición de secretos. |
| AC-A06 / C/H | Token/desafío de otro cliente, audience, issuer, tenant, producto, canal o entorno; ausentes/malformados y familia local usada como central. Rechazar antes de sync o sesión. | Vectores de C/H y llamadas cruzadas entre consumidores; positiva exacta de cada registro autorizado. |
| AC-A07 / B | Sesión/refresh previo sin procedencia MFA suficiente, usuario/membresía revocados, cambio de tenant y token revocado. No ampliar sesión ni fabricar evidencia; reautenticar/denegar según corte firmado. | Login, refresh, bearer/cookie y switch-org reales; B durable requiere su evidencia, sin atribuirla al guard A. |
| AC-A08 / CT1/CT4/D | MFA válida con MEDSUPPLIER o ISO_SMART denegado no abre sesión de producto ni permite API. Scopes vacíos/desconocidos no conceden; viewer/auditor no write. | Endpoint validate fresco + API directa; preservar QMS y side/account/visibilidad; supplier/customer no se eleva por tenant:write. |
| AC-A09 | ISO mantiene CSRF/cookies seguras. En ambos frontends, challenge no activa sesión y fallo no conserva tokens de login anterior como éxito nuevo. Refresh/reintentos no saltan MFA. | Pruebas UI y HTTP del contrato propio de cada consumidor; no copiar transporte ISO a MS sin decisión. |
| AC-A10 / REC-2FA-04 | Consumo concurrente del mismo desafío/factor: como máximo un consumo efectivo autorizado. Error de emisión/sync/respuesta después del commit: sin sesión al cliente fallido y consumo permanece irreversible. Recuperación/reset no omiten MFA. | Laboratorio PostgreSQL y observación persistente bajo autorización; sin envolver consumo+emisión en una transacción que reponga el factor al fallar. |
| AC-A11 | Versiones mixtas, corte y reversión ensayados; ninguna reversión abre ruta password-only o elimina binding; versiones incompatibles quedan cerradas. | Matriz por consumidor, evidencia de parada/reapertura y aceptación de soporte/operación. |
| AC-A12 | Identidad/tenant ambiguos o colisiones email/slug/ID no reasignan perfil ni external_id para permitir login. | Casos negativos con proyecciones en conflicto; no mutación ni acceso fuera de tenant. |

## Independencia de las regresiones y trazabilidad

Las pruebas nuevas se escribirán en suites separadas por producto, con revisión
de QA/seguridad distinta del autor del cambio y fixtures contractuales comunes.
No copiar condiciones internas como oráculo ni sustituir con mocks el guard que
se pretende probar. Unitarias podrán inyectar transporte/fallos explícitos;
el laboratorio probará autenticación, ORM/transacciones, cookies/JWT y APIs
reales. Reportar por separado unidad, contrato, integración y E2E.

Usar una prueba discriminante del fallback MedSupplier que falle contra la
baseline sin cambiar el test, y repetirla sobre el sucesor autorizado. Mantener
NF01 y los nueve fallos históricos; una nueva versión del contrato agrega tests
sucesores trazables, no skips ni reescritura de resultados anteriores.
REC-2FA-04 requiere su regresión pertinente; sus PASS históricos no sustituyen
concurrencia/consumo real del futuro cambio.

Evidencia mínima por corrida: hash de código/config/contrato, target y alcance
autorizado, vector, resultado esperado/observado, efectos persistentes, identidad
del revisor, resultado por consumidor y límites de dobles. No almacenar passwords,
OTP, tokens de sesión, backup codes ni claves en evidencia. Todo criterio fallido
mantiene el canal/slice bloqueado; no declarar compatibilidad con mocks únicamente.
