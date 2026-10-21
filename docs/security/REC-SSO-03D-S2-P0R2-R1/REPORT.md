# REC-SSO-03D-S2-P0R2-R1 — Integration readiness

2026-10-19 · America/Costa_Rica · local/offline.

## A. Executive Verdict

**P0R2_INTEGRATION_OFFLINE_VERIFIED_ACTIVATION_BLOCKED**

Ciclo completo mediante cliente Django real verificado; nueve diferencias históricas reconciliadas con adaptadores sucesores. Se corrigió una ventana de emisión desde autenticación obsoleta y se preservó la actualización legítima de hashes Django. **No hay enforcement global activo.**

`PRODUCTION_READY = FALSE` · `POSTGRESQL_DURABILITY = NOT_EVIDENCED` · `NO_DEPLOYMENT · NO_COMMIT · NO_PUSH`

## B. Baseline

Se recuperó `/tmp/rec-sso-03d-s2-p0r2-20261019`; sus fuentes/reporte coincidían con los hashes sellados. Snapshot R1: 15,813 archivos tracked/unignored, HEAD/índice y copias de fuentes previas. P0R2 inicial: 25/25 PASS. Evidencia nueva: [/tmp/rec-sso-03d-s2-p0r2-r1-20261019](/tmp/rec-sso-03d-s2-p0r2-r1-20261019).

## C. Autenticador integrado en settings sintéticos

El runner nuevo reutiliza el almacenamiento controlado P0R2 y configura en memoria `HumanJWTAuthentication` como default. Usa URLs reales, `django.test.Client`, middleware Django y cache de sesiones local. Las clases de autenticación y serializers ejecutan su implementación real; las sustituciones de ORM/atomic son explícitas. Los spies de emisión llaman al código original.

Se inspeccionan los defaults de las rutas humanas resueltas, incluidas variantes de formato, sin convertir esa inspección en cobertura funcional de cada handler. Login/MFA temporal conservan sus rutas públicas particulares; las 18 rutas técnicas/centrales quedan separadas. Cookies reales del backend cache no rescatan un bearer rechazado. Ambos settings activos permanecen intactos; [activation-settings.patch](/tmp/rec-sso-03d-s2-p0r2-r1-20261019/activation-settings.patch) prepara únicamente el reemplazo del autenticador, conservando las entradas de cookie de cada módulo. **No se aplicó ese patch.**

## D. Login → Refresh → Revoke → DENY → Relogin

`Client.post(login)` emite pareja; la API existente `users/sessions/` permite acceso. El endpoint real de refresh rota; access y refresh anteriores obtienen 401. `users/revoke_session/` revoca la familia vigente; el mismo access obtiene **401 antes del handler**, y su refresh obtiene DENY. Un login nuevo crea otro SID autorizado; el anterior sigue denegado. Logout también revoca su familia y elimina únicamente la cookie actual del backend cache probado.

La integración encontró un defecto real adicional: el emisor releía autoridad vigente, pero podía adjudicarla a una autenticación anterior a un cambio de contraseña o disable→enable. Reproducción previa: HTTP 200 en ambos casos; ahora 401 sin emitir sesión. `issue_refresh` compara contraseña y versión del snapshot autenticado con el usuario bloqueado. El serializer conserva ese 401. [integration-before.log](/tmp/rec-sso-03d-s2-p0r2-r1-20261019/integration-before.log) y [integration.log](/tmp/rec-sso-03d-s2-p0r2-r1-20261019/integration.log) muestran antes/después.

La comparación nueva inicialmente rechazaba el upgrade legítimo de hash que Django hace durante login. Se reprodujo ese 401 y corrigió `User.save(update_fields=...password...)`: bloquea y comprueba la autoridad antes de escribir, conserva el atomic y relee la versión del trigger antes de liberar el lock. Un reset concurrente durante el cálculo del hash ya no puede ser sobrescrito por el upgrade; también se reprodujo ese HTTP 200 antes de corregirlo ([hash-upgrade-race-before.log](/tmp/rec-sso-03d-s2-p0r2-r1-20261019/hash-upgrade-race-before.log)). La prueba ejecuta el setter/hasher/refresh del modelo reales y simula solo persistencia/trigger: login y acceso vuelven a ALLOW. La garantía de lock SQL requiere el laboratorio.

## E. MFA y registro

Adaptador sucesor: 21/21 métodos históricos de MFA/login pasan con sus cuerpos de aserción originales. Las observaciones de `OutstandingToken.create` se trasladan a `UserSession.create`, y las de `RefreshToken.for_user` a `HumanRefreshToken.for_user`; los intentos reales de persistir JWT completos se bloquean. Se alinean relojes sintéticos y vidas de 8h/7d que exigía aquel contrato.

TOTP, backup, límites de intentos, replay, gates previos, errores de emisión, claims, hook de extensión y alertas de contraseña temporal permanecen verificados. Cada pareja real observada en los sucesores se autentica, se revoca con el servicio y rechaza access/refresh. El método histórico de registro con invitación válida también pasa con almacenamiento adicional y prueba de revocabilidad. No se modificó el fixture histórico de invitación inválida ni su ERROR.

## F. Reconciliación de nueve regresiones

[regression-reconciliation.csv](/tmp/rec-sso-03d-s2-p0r2-r1-20261019/regression-reconciliation.csv) identifica cada método, resultado original y resultado sucesor:

| Método histórico | Original R1 | Sucesor |
|---|---|---|
| MFA b01 pareja firmada | FAIL | PASS |
| MFA b02 segundo factor previo | FAIL | PASS |
| MFA b07 respuesta/ruta | FAIL | PASS |
| MFA b09 intentos/backup | FAIL | PASS |
| Login g03 emisión única | FAIL | PASS |
| Login g04 claims/hook | FAIL | PASS |
| Login g07 TOTP/backup | FAIL | PASS |
| Login g09 alerta temporal | FAIL | PASS |
| Registro con invitación y emisión | FAIL | PASS |

Las nueve son incompatibilidades del harness anterior con la nueva persistencia, demostradas al ejecutar sus aserciones sobre el código real con almacenamiento compatible. **Los nueve FAIL originales siguen registrados; no se convierten en PASS.** El defecto de snapshot encontrado por las pruebas nuevas se reporta y corrige por separado.

## G. Revisión de migración y triggers

`0005` permanece byte a byte intacta. Grafo acíclico, dependencia `users.0004` y estado de modelos sin drift: PASS estático. UUID PK, JTI/familia únicos y FK indexada; filas heredadas retienen versión 0/familia nula. Se revisaron guards monotónicos/de revocación terminal en UPDATE, triggers de contraseña/is_active, reversa y exigencia PostgreSQL. No hay dependencia SQL nueva con B: conserva sus tablas/fence/outbox separados. No se afirma historial indeleble frente a DELETE/reinsert; requiere delimitar permisos de BD.

Se capturó el SQL del instalador con editor simulado: **ningún SQL ejecutado**. Rollback de datos/DDL, locks, concurrencia y convivencia real con `integration.0010` siguen sin verificar.

## H. Pruebas ejecutadas

| Suite final | PASS | FAIL | ERROR |
|---|---:|---:|---:|
| Integración cliente Django nueva | 7 | 0 | 0 |
| Esquema estático nuevo | 2 | 0 | 0 |
| MFA/login sucesor heredado | 21 | 0 | 0 |
| Registro sucesor heredado | 1 | 0 | 0 |
| P0R2 heredada | 25 | 0 | 0 |
| MFA original, sin adaptar | 13 | 8 | 0 |
| P0R original | 33 | 1 | 0 |
| Usuarios/Admin/autorización histórica | 29 | 0 | 1 |
| Decision B | 43 | 0 | 0 |
| Decision D | 57 | 0 | 0 |

**9 métodos nuevos declarados**; los 22 métodos de adaptadores son heredados, no métodos nuevos. Los resultados históricos sin adaptar coinciden con P0R2, incluido el ERROR de invitación. Los fallos de subtests no se cuentan como métodos adicionales. Check Django sintético, compilación y diff check: PASS. Guardas: cero conexiones BD/red. Consumidores no se repitieron: no cambiaron sus contratos/fuentes.

## I. Bloqueos de activación

Migración y garantías PostgreSQL pendientes; settings activos aún usan el autenticador anterior; legacy requiere relogin al activar. La separación de credenciales local/refresh/cookie/CENTRAL/ISO LOCAL/Med LOCAL/API key/legacy se prueba con bearer firmado y cookie válida. No se amplió logout ni se afirmó invalidación global de cookies/Django Admin. Es necesario confirmar el backend activo de cookies y el laboratorio antes de activar.

## J. Próximos pasos PostgreSQL

[POSTGRESQL-LAB.md](POSTGRESQL-LAB.md) prepara 16 escenarios concretos: persistencia entre conexiones, rotación/revocación concurrente, cambio/restauración de autoridad, rollback local+B/outbox, snapshot obsoleto, upgrade de hash, errores/locks y cookies. Incluye rollback operativo que mantiene comprobación de sesión o DENY; volver al autenticador stateless restauraría autoridad de JWT revocados.

## K. Integridad Git

Tres fuentes existentes cambiaron: `human_sessions.py`, `serializers.py`, `models.py`; se agregó el runner R1 y estos dos documentos. HEAD `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` e índice preservados; cambios anteriores intactos. Settings, autenticador, refresh, migración preparada, A/C/H/B/D, REC-2FA-04, tests originales y gobernanza histórica conservan sus bytes. `/tmp` contiene diff del incremento, hashes, comandos, resultados por método, reconciliación y sellado SHA256. Sin migraciones, bases compartidas, credenciales reales, servicios compartidos, despliegue, commit o push.
