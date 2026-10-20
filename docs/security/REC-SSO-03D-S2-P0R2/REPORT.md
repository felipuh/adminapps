# REC-SSO-03D-S2-P0R2 — Human JWT revocation

2026-10-19 · America/Costa_Rica · ejecución local y offline.

## A. Executive Verdict

**P0R2_LOCAL_CODE_VERIFIED_ACTIVATION_BLOCKED**

El código nuevo revoca efectivamente access y refresh humanos, probado con firma real, dispatch DRF y almacenamiento simulado. **El enforcement global no está activo**: ambos módulos de settings conservan `JWTAuthentication`, que todavía admite el access revocado. No se aplicó ninguna migración. La activación y la persistencia/concurrencia PostgreSQL siguen pendientes.

`PRODUCTION_READY = FALSE` · `NO_DEPLOYMENT` · `NO_COMMIT` · `NO_PUSH` · `GOVERNANCE_PRESERVED`

## B. Problema original y reproducción

El autenticador anterior comprobaba firma/expiración/usuario sin consultar `UserSession`. La misma prueba crítica emite un JWT, obtiene 200 en una vista DRF protegida, revoca con el servicio real y repite el mismo bearer. Con el autenticador anterior vuelve a obtener **200 y ejecuta el handler**: un FAIL esperado, cero errores. Con el nuevo obtiene **401 sin ejecutar el handler**; `AccessToken` todavía verifica su firma. También se prueba el handler existente `UserViewSet.sessions` bajo los defaults sintéticos nuevos.

Evidencias: [baseline-auth.log](/tmp/rec-sso-03d-s2-p0r2-20261019/baseline-auth.log), [focused.log](/tmp/rec-sso-03d-s2-p0r2-20261019/focused.log). `--baseline` usa la clase SimpleJWT anterior instalada, sin alterar fuentes del repositorio.

## C. Arquitectura de sesión humana

`UserSession.id` identifica la sesión; `family_id` identifica la familia estable de refresh. Access y refresh llevan `sid`, `fid`, `sg` (generación), `av` (autoridad del usuario), `hsv=1`, `token_family=ADMINAPPS_HUMAN_LOCAL` y `user_id`. El registro guarda propietario, JTI del refresh vigente, creación/expiración absoluta, generación, autoridad, actividad y revocación. **Los tokens nuevos nunca se guardan completos.**

`User.human_auth_version` es monotónica. La migración preparada incrementa esa autoridad y revoca los registros locales ante cambios de contraseña o `is_active`, incluidos SQL/bulk updates. Reactivar al usuario no revive sus JWT anteriores. Otro trigger protege identidad, familia, fechas, generación y estado terminal del registro. Estos triggers son código preparado; no se ejecutaron contra PostgreSQL.

Los servicios de emisión, refresh y revocación bloquean usuario → sesión y exigen su propia transacción durable, PostgreSQL y autocommit. Rechazan transacciones externas para impedir que un fallo posterior de auditoría deshaga una revocación. SQL, rollback y concurrencia reales: **NOT_EVIDENCED**.

## D. Cambios implementados

- `users/human_sessions.py`: emisión, comprobación, rotación, revocación propia individual/global/otras y logout.
- `users/authentication.py`: `HumanJWTAuthentication`, preparado para reemplazar al autenticador general.
- `users/human_token_views.py` y `users/urls.py`: refresh subordinado al registro; sin refresh heredado que conceda autoridad.
- `users/serializers.py` y `users/views.py`: mismo emisor para login, registro y MFA; logout, revocación y cookie actual. La auditoría conserva al actor antes de `django.logout()`.
- `users/services.py`: logout por cookie con refresh vinculado revoca su familia sin persistir el JWT nuevo; conserva la retirada por blacklist de refresh heredados.
- `users/models.py`, `users/migrations/0005_human_jwt_sessions.py`: esquema y triggers preparados.
- `users/api_authorization.py`: autoriza expresamente la nueva acción propia `revoke_session`; conserva las restricciones humanas y de campos.
- `scripts/rec_sso_03d_p0r2_offline.py`: pruebas sucesoras focalizadas y reproducción del autenticador anterior.

No se modificaron contratos ni fuentes centrales de Decision B, consumidores, billing, settings activos o gobernanza histórica.

## E. Verificación real de JWT

SimpleJWT verifica firma con el algoritmo configurado; la clase nueva fija el tipo access. Después comprueba familia y versión, tipos de claims, usuario activo/no bloqueado, propietario, sesión existente/vigente/no revocada, generación, autoridad actual, fechas y consistencia del registro. La lectura une sesión y usuario en una consulta. Estado ausente/inaccesible deniega (401/503), sin fallback a cookies tras rechazar un bearer.

Se prueban algoritmos/firma inválidos, expiración, generaciones antiguas, sesiones ausentes/ajenas, autoridad inconsistente, tipos boolean/string incorrectos, CENTRAL, ISO/MedSupplier, credenciales técnicas y JWT heredados. Las autorizaciones funcionales continúan comprobando el usuario y permisos actuales.

## F. Refresh, logout y revocación

Refresh acepta únicamente familias vigentes. Con `ROTATE_REFRESH_TOKENS=True`, cambia JTI e incrementa generación: access y refresh anteriores dejan de autenticar. Con False, mantiene generación y verifica igualmente la sesión. La familia tiene expiración absoluta; la rotación no amplía ese plazo. Una respuesta perdida no habilita el refresh antiguo. Un refresh es una credencial bearer: sin otro principal autenticado, su posesión acredita al propietario firmado; con bearer/cookie autenticada se exige el mismo propietario. No se adjudica identidad a partir del payload del cliente.

`logout/` revoca el SID autenticado aun sin refresh; un refresh suministrado debe pertenecer a la misma familia. `users/revoke_sessions/` conserva el SID autenticado y revoca las otras familias propias. Para una cookie, que no tiene SID JWT, revoca las familias JWT y conserva esa cookie, expresándolo en la respuesta. `users/revoke_session/` admite exactamente `session_id` propio o `all=true`; global incluye la sesión actual. Reintentos del servicio son idempotentes; IDs ajenos/desconocidos se rechazan sin cambios. Un segundo HTTP con access ya revocado se rechaza en autenticación.

Cambio de contraseña, reset administrativo/público y deshabilitación/reactivación convergen mediante el trigger de autoridad preparado, sin callbacks de aplicación que puedan omitirse por un bulk update. Los tests ejecutan los handlers reales de cambio/reset con el efecto del trigger simulado; su ejecución SQL sigue pendiente.

## G. Tokens y cookies

| Credencial | Autoridad y alcance |
|---|---|
| Access humano local | Nueva familia/version y `UserSession` vigente; legacy sin vínculo siempre DENY con el autenticador nuevo |
| Refresh humano local | Mismo registro/familia; legacy siempre DENY en la nueva ruta de refresh; requiere volver a iniciar sesión |
| Cookie Django / Django Admin | `SessionAuthentication`/backend Django independientes; logout REST llama a `django.logout()` y flush de la cookie actual si hay sesión en la petición |
| CENTRAL SSO | `SSOSession`, fence y contratos B existentes; ninguna sesión central se reutiliza como sesión humana local |
| LOCAL ISO Smart | Autoridad/proyección del consumidor y prueba central existentes; no es un JWT humano de AdminApps |
| LOCAL MedSupplier | Misma separación de autoridad; contrato del consumidor intacto |
| IntegrationAPIKey | Credencial técnica y grants existentes; no concede sesión humana |

Se demuestra flush con el backend cache real local y eliminación de la clave anterior. **No se afirma invalidación del backend activo de cookies ni revocación global de Django Admin/cookies**. El cambio de contraseña conserva la invalidación estándar por hash de Django; un ciclo disable/enable de cookies queda fuera del control JWT. Los caminos heredados de registry/blacklist solo retiran estado; nunca convierten un token heredado en familia válida. Al activar el nuevo autenticador, los access heredados no llegan a esos handlers.

## H. Pruebas y resultados

Conteo por método, sin promover subtests o herencia a métodos únicos:

| Suite | PASS | FAIL | ERROR |
|---|---:|---:|---:|
| P0R2 focalizada | 25 | 0 | 0 |
| P0R | 33 | 1 | 0 |
| P0R sesiones centrales | 6 | 0 | 0 |
| API P0 | 50 | 0 | 0 |
| Usuarios/Admin/autorización histórica | 29 | 0 | 1 |
| Decision B | 43 | 0 | 0 |
| Decision D | 57 | 0 | 0 |
| MFA histórica | 13 | 8 | 0 |
| C/H histórica | 2 | 4 | 12 |
| Continuación P0R | 12 | 0 | 0 |

Los 8 métodos MFA que cambian de estado y el método de emisión del registro P0R ahora fallan porque sus fixtures solo simulan `OutstandingToken`, usan backend dummy y no proveen el registro nuevo. Además esperan la persistencia antigua del JWT completo. **No se reportan como PASS ni se modifican sus tests/fixtures originales.** Los sucesores ejecutan login real, hook de claims, TOTP/backup/replay y registro con invitación real, incorporando el almacenamiento simulado nuevo; pasan y los access resultantes son revocables. No se atribuye un cierre completo a la suite histórica. El ERROR histórico de invitación permanece abierto e idéntico. B, D, C/H y las restantes suites mantienen sus estados previos. [historical-delta.json](/tmp/rec-sso-03d-s2-p0r2-20261019/historical-delta.json) enumera las nueve diferencias.

Guardas de los runners Python: cero conexiones de BD/red. Cliente AdminApps: `node --test src/services/authRefresh.test.js`, **41/41 PASS** con transporte sintético. El cliente ya usa un transporte de refresh sin access expirado adjunto. Check Django sintético, compilación y `git diff --check`: PASS. Comparación del estado de migraciones contra modelos: sin drift en `users`, sin conexión ni aplicación de migraciones. No se repitieron suites completas de consumidores porque sus contratos/fuentes no cambiaron.

## I. Migración y activación pendientes

1. Validar/aplicar **fuera de esta ejecución** `users.0005_human_jwt_sessions` sobre PostgreSQL autorizado, incluidas funciones/triggers. Verificar persistencia, orden de locks, aislamiento y rollback bajo concurrencia junto con los triggers B existentes.
2. En el módulo de settings realmente utilizado (`config.settings`, o el alternativo `adminapps.settings`), reemplazar únicamente la entrada general `rest_framework_simplejwt.authentication.JWTAuthentication` por **`apps.users.authentication.HumanJWTAuthentication`**. Conservar las entradas de cookie existentes. No se encontró otro autenticador JWT humano explícito en las vistas de aplicación; el endpoint refresh ya especifica el nuevo.
3. Activar código, esquema y wiring de manera coordinada, con relogin explícito de tokens heredados. Sin esquema/autoridad no se emiten pares nuevos autorizados. El emisor y la nueva ruta refresh ya requieren la migración una vez se publique el código.

No se ejecutó ninguno de estos pasos operativos. El autenticador general actualmente configurado sigue aceptando JWT revocados; ese defecto activo no queda oculto por las pruebas sintéticas.

## J. Integridad Git y evidencia

HEAD preservado: `b144b2505659ad39f756b9bc4530a7f24fe8c3ad`. El snapshot inicial incluye 15,807 archivos tracked/unignored y el hash del índice. Se conservaron los cambios preexistentes y los originales de tests/reportes. El incremento cambia seis fuentes existentes y agrega cinco fuentes/tests, además de este reporte nuevo.

Directorio: [/tmp/rec-sso-03d-s2-p0r2-20261019](/tmp/rec-sso-03d-s2-p0r2-20261019). Contiene `baseline.json`, copias `before/`, `p0r2-only.patch` respecto del worktree inicial, `code-hashes.json`, `integrity-final.json`, comandos, logs y resultados por método. `SHA256SUMS` sella los archivos de evidencia. Las evidencias P0R y continuación se reutilizaron sin reescribirlas.

## K. Bloqueos pendientes

Activación del autenticador; migración y pruebas PostgreSQL de persistencia/concurrencia/rollback; adaptación explícita futura de nueve métodos históricos al nuevo contrato de persistencia; ERROR original de invitación; validación del backend activo de cookies. No se afirma enforcement global ni revocación global de cookies. No se accedió a bases compartidas, secretos ni servicios compartidos; no hubo despliegue, commit o push.
