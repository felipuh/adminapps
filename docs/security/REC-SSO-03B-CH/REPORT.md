# REC-SSO-03B-CH — reporte final de ingeniería local

Inicio: 2026-10-14. Consolidación: 2026-10-15, America/Costa_Rica. Evidencia: `/tmp/rec-sso-03b-ch-20261014/`. El directorio conserva la fecha inicial.

## A. EXECUTIVE VERDICT

**Estado: LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED_WITH_EXTERNAL_BLOCKERS. Cierre durable C/H: BLOCKED_BY_EXTERNAL_DEPENDENCY.** No se declara `REC_SSO_03B_CH_LOCAL_IMPLEMENTATION_VERIFIED` ni cierre total `LOCAL_IMPLEMENTED_AND_OFFLINE_VERIFIED`, porque el registro persistente requiere aplicación del esquema y provisión no autorizadas en este mandato.

Implementados: registro durable en código, contrato tipado, vínculo con principal autenticado, audiencias exactas, aislamiento de productos/tenants, RSA y kids explícitos por familia, verificación central más introspección viva, sesiones locales subordinadas y protección de middleware/transporte. **103 pruebas finales PASS** de las suites nuevas/regresiones seleccionadas: 74 C/H + 21 MFA + 8 frontend. Las suites históricas completas también se ejecutaron y conservan fallos/errores contractuales detallados abajo; no se presenta el conjunto histórico como verde.

Pendientes: esquema aplicado, filas reales de clientes, claves/configuración, validación PostgreSQL/HTTP/E2E, corte y reversión ensayada. Riesgos residuales: reautenticación cada 300 s, tamaño/carga de cookies con prueba embebida, transporte MedSupplier/localStorage y XSS preexistente, revocación durable B, scopes D y decisiones E/F/G abiertas. La introspección viva no elimina carreras de revocación ni ABA de roles.

`PRODUCTION_READY = FALSE`. `NO_DEPLOYMENT`. `NO_COMMIT`. `NO_PUSH`. `HISTORICAL_GOVERNANCE_PRESERVED`. No se ejecutaron migraciones, escrituras/consultas a bases compartidas, reinicios ni cambios de secretos/configuración activa.

## B. INITIAL BASELINE

| Repositorio | HEAD inicial | Estado inicial Git | Archivos regulares inventariados |
| --- | --- | --- | --- |
| adminapps | `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` | 3 modificados tracked; 11 entradas untracked | 15629 |
| isosmart | `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` | 18 modificados tracked; 18 entradas untracked | 15054 |
| ISO_Smart_MedSupplier | `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` | 8 modificados tracked; 5 entradas untracked | 14993 |

Antes de editar se guardaron HEAD, índice, estado, hashes y diffs iniciales en baseline.json y `*.initial.diff`. Se respaldaron los 10 archivos preexistentes que se modifican en `before/<repo>/...`, incluidos archivos Decision A que ya eran untracked. Los nuevos archivos están identificados separadamente. `integrity-final.json` compara los archivos inventariados con la baseline y verifica respaldos, HEAD e índice; `*.ch.patch` compara contra los bytes previos, no contra HEAD, para excluir cambios ajenos. No se afirma cobertura sobre ignorados, symlinks, secretos o datos no inventariados.

## C. ADMINAPPS IMPLEMENTATION

`IntegrationAPIKey` existente ya ofrece hash y lifecycle, pero no cliente/producto/tenant. `ProductSystem.metadata` no garantiza unicidad de principal/audiencia. Se añade `SSOClient` con OneToOne al principal, FK producto, M2M de tenants, client_id/audience únicos, issuer, enabled, familia, algoritmo, kids permitidos, política hashed_v1 y versión. La migración `0008_ssoclient.py` se creó y se comparó offline con el estado de modelos; **no se aplicó**.

`ClientContract` es inmutable y tipado. Login, verify e introspection resuelven primero la API key real; aliases de settings y filas plaintext no son clientes SSO. El registro se busca por principal autenticado. Los parámetros declarados solo se comparan con ese contrato. Tenant debe estar en la M2M activa y en una membresía activa del usuario. Rotar una credencial no transfiere el cliente por nombre: requiere rebind explícito.

La emisión usa RSA central dedicada; filtra productos y membresías al contexto propio. La introspección verifica firma/claims/cliente y vuelve a leer usuario, membresía, rol, tenant, producto y MFA. El challenge incorpora cliente/principal/producto/audience/tenant/versión y rechaza cambios antes de consumo. No se modifica el servicio transaccional MFA.

Archivos C/H: `backend/apps/integration/models.py`, `sso_views.py`, nuevos `client_registry.py`, `trust_jwt.py`, `migrations/0008_ssoclient.py`, y `backend/scripts/rec_sso_03b_ch_offline.py`. Documentación nueva: `docs/security/REC-SSO-03B-CH/`.

## D. ISO SMART IMPLEMENTATION

El adaptador añade contexto fijo ISO_SMART a todas las llamadas, verifica RSA CENTRAL antes de introspección y compara ambas evidencias antes de proyectar. Comprueba el tenant pedido también al completar challenge. Tokens LOCAL usan issuer/audience/clave propios y UUID central; refresh/rotación no superan exp central. Middleware deja de usar el verificador JWT general y exige sesión LOCAL validada con autoridad viva.

Se preserva el rechazo bearer que ya tenía Decision A, HttpOnly y CSRF. Se añade rechazo de sesión Django local en la cadena opcional de autenticación de desarrollo. No se cambian settings activos ni frontend.

Archivos: `backend/integration/central_auth.py`, `sso_auth.py`, nuevos `trust_jwt.py`, `local_tokens.py`, `tests_ch_offline.py`; `backend/authentication/views.py`, `middleware.py`; nuevos `docs/transformation/REC_SSO_03B_CH_CONTRACT.md` y `REC_SSO_03B_CH.openapi.json`.

## E. MEDSUPPLIER IMPLEMENTATION

Mismo contrato con producto fijo MEDSUPPLIER y claves locales propias. Se mantiene bearer/localStorage y permisos de dominio. Middleware verifica familia local y autoridad viva; la carga de perfil queda ligada también a user_id/organization_id y estado activo. No hay rescate mediante check_password, perfil local, coincidencia de email o JWT histórico.

Archivos: `backend/integration/central_auth.py`, `sso_auth.py`, nuevos `trust_jwt.py`, `local_tokens.py`, `tests_ch_offline.py`; `backend/authentication/views.py`, `middleware.py`; nuevos `docs/security/REC_SSO_03B_CH_CONTRACT.md` y `REC_SSO_03B_CH.openapi.json`.

## F. CRYPTOGRAPHIC TRUST BOUNDARIES

| Dimensión | CENTRAL | LOCAL |
| --- | --- | --- |
| Algoritmo | Solo RS256, RSA ≥2048 bits | Solo RS256, RSA ≥2048 bits |
| Claves | Keyring explícito; kid autorizado además por cliente | Keyring del consumidor; no puede coincidir con CENTRAL por números RSA |
| Issuer | Central HTTPS explícito | HTTPS propio, distinto de central |
| Audience | Lista de un elemento, igualdad exacta con registro | Audiencia local propia, distinta de central |
| Familia | CENTRAL | LOCAL |
| Identidad/tenant | sub=user_id UUID; tenant_id=organization_id UUID | sub/central_sub UUID central; user_id/organization_id locales y tenant_id UUID central |
| Vigencia | 300 s; refresh central no aceptado por introspection | Expiración limitada por prueba central; revalidación viva |

Se rechazan none/HMAC, firma alterada, kid ausente/desconocido/no permitido, emisores/audiencias/familias incorrectos, claims ausentes y cabeceras de descubrimiento de claves. No hay fallback a SECRET_KEY, SMART3AI_SSO_JWT_SECRET ni SIMPLE_JWT. Consumidores no admiten privada CENTRAL configurada. Las tres copias del codec se comprueban idénticas por hash para despliegues independientes.

Las claves de pruebas se generan en memoria y son sintéticas; no se generan ni instalan claves reales. Provisionamiento y verificación de distinción entre ambas claves locales siguen pendientes. Ver CONTRACT.md y rollout-rollback-plan.md.

## G. SECURITY TEST RESULTS

Conteos por método; los subtests adversariales cubren múltiples variantes.

| Suite/check | PASS | FAIL | ERROR | Cobertura/límite |
| --- | ---: | ---: | ---: | --- |
| AdminApps CH | 18 | 0 | 0 | Endpoints, registro, RSA, principal, tenants, MFA y coordinación |
| ISO Smart CH | 28 | 0 | 0 | Serializer/adaptador, firma, sesión, refresh/rotación, middleware, cookies/CSRF |
| MedSupplier CH | 28 | 0 | 0 | Mismos controles, transporte bearer |
| REC-2FA-04 | 21 | 0 | 0 | Runner offline existente, servicio sin editar |
| Frontend ISO | 4 | 0 | 0 | Función de login real; no navegador |
| Frontend MedSupplier | 4 | 0 | 0 | Función de login real; no navegador |
| ESLint focalizado | 2 ejecuciones | 0 | 0 | Archivos de login de ambos consumidores |
| Sintaxis/definiciones duplicadas | PASS | 0 | 0 | 20 archivos Python C/H |
| git diff --check | 3 ejecuciones PASS | 0 | 0 | Worktrees de los tres repositorios |
| Estado de migración vs modelos | PASS offline | 0 | 0 | Loader sin conexión; no ejecuta migración |
| Ruff | NOT_EVIDENCED | — | — | No instalado en entornos existentes; no se instala dependencia |
| Build frontend | No aplica | — | — | Ningún archivo frontend cambiado por C/H |
| HTTP/E2E/PostgreSQL/concurrencia | NOT_EVIDENCED | — | — | Fuera de ejecución local offline autorizada |

Guards reportan cero intentos de conexión a DB/red en suites nuevas y MFA; la coordinación verifica también guards de procesos consumidores. Las primeras iteraciones detectaron 2 errores de fixtures de cookies y después 1 fallo por método duplicado en ISO; se corrigieron sin alterar tests históricos. También se ajustó el orden de límite de expiración durante rotación. first-*.log, checks-before-final-correction.json, check-run.log y logs finales conservan esa trazabilidad.

Comandos/cwd/resultados: checks.json; casos: test-results.json y security-negative-tests.md. Los resultados se reproducen con los `.venv/bin/python -B` y runners indicados allí; no se cargan settings de despliegue.

## H. CROSS-PRODUCT ISOLATION

`test_coordinated_cross_product_consumers` ejecuta el emisor real y la introspección de AdminApps con ORM simulado. ISO y MedSupplier reciben pruebas propias con **sujetos y tenants distintos**, transferidas por stdin a procesos que cargan cada consumidor real. Ambos verifican su prueba, emiten/verifican sesión local con rol viewer, rechazan prueba del otro producto y sesión local como prueba central, y rechazan otro tenant. Los tokens y claves no se escriben a fixtures/logs.

ch-adminapps.log registra `CROSS_PRODUCT_PASS ISO_SMART` y `CROSS_PRODUCT_PASS MEDSUPPLIER`. Es integración coordinada offline, no un intercambio HTTP real ni un entorno persistente.

## I. REGRESSION RESULTS

| Suite histórica sin editar | Baseline PASS/FAIL/ERROR | Código CH PASS/FAIL/ERROR |
| --- | --- | --- |
| Decision A AdminApps | 30/0/0 | 7/20/3 |
| Decision A ISO | 20/0/0 | 9/0/11 |
| Decision A MedSupplier | 20/0/0 | 9/0/11 |
| REC-SSO-02 | 22/9/1 | 8/19/5 |
| REC-2FA-04 | 21/0/0 (referencia anterior) | 21/0/0 ejecutados |

La baseline Decision A se ejecutó antes de editar. REC-SSO-02 se reprodujo con el sso_views.py inicial respaldado mediante importación aislada, sin restaurar el worktree: baseline-historical-02.log vuelve a mostrar 22/9/1.

Clasificación: los fixtures históricos SSO usan nombres de servicio como principal, firma HS/general, contrato Decision A y llamadas al emisor sin cliente tipado; el contrato nuevo los rechaza o exige datos que no suministran. Por ello no ejercitan las nuevas rutas autorizadas. Los errores de consumidores son principalmente ausencia de trust explícito y envolturas antiguas; el sucesor prueba rutas válidas y negativas con firma real. REC-SSO-02 conserva además políticas comerciales y scopes históricamente pendientes. Los fallos por subtests producen más entradas unittest que métodos: se registran ambos conteos en test-results.json. Ningún PASS sobre token antiguo denegado se usa como evidencia de scopes o autorización.

No se editan expectativas antiguas. Se reutilizan seis métodos negativos de Decision A por consumidor en la suite CH con contexto nuevo, además de pruebas nuevas de refresh, MFA, identidad y tenancy. No se afirma cero regresiones sobre contratos históricos: el corte es intencionalmente incompatible.

## J. COMPATIBILITY MATRIX

Ver compatibility-matrix.md: ambas parejas CH permiten autenticación propia offline con provisión completa; tokens históricos y cruces se rechazan. Versiones desplegadas mixtas, corte y reversión HTTP siguen NOT_EVIDENCED. Cliente/credencial deshabilitados, tenant/usuario deshabilitados, MFA pendiente, prueba vencida, refresh fuera de vigencia y configuración incompleta fallan cerrado. La estrategia coordinada de rollout/rollback está preparada y no ejecutada.

## K. ACCEPTANCE CRITERIA

PASS_OFFLINE significa prueba de código con dependencia simulada, nunca cierre de despliegue o persistencia. La columna de límites es parte del veredicto.

| Criterio | Estado | Evidencia/límite |
| --- | --- | --- |
| AC-CH-01 | BLOCKED_BY_EXTERNAL_DEPENDENCY | Modelo/contrato tipado y estado de migración implementados y probados; registro durable sin aplicar/provisionar |
| AC-CH-02 | PASS_OFFLINE | Resolución por principal, hash real y test_wrong_credential_binding; operación persistente depende de 01 |
| AC-CH-03 | PASS_OFFLINE | test_impersonation_both_directions, claim_matrix; sin defaults compartidos |
| AC-CH-04 | PASS_OFFLINE | Suplantación y challenge de otro principal rechazados |
| AC-CH-05 | PASS_OFFLINE | Coordinación ISO rechaza MedSupplier |
| AC-CH-06 | PASS_OFFLINE | Coordinación MedSupplier rechaza ISO |
| AC-CH-07 | PASS_OFFLINE | Codec y familias verificadas; claves reales/activación pendientes |
| AC-CH-08 | PASS_OFFLINE | Algoritmos/kids/firma y claves iguales rechazados |
| AC-CH-09 | PASS_OFFLINE | Tokens antiguos rechazados; suites históricas conservadas |
| AC-CH-10 | PASS_OFFLINE | Refresh real, rotación y prueba central expirada; no cierre B |
| AC-CH-11 | PASS_OFFLINE | UUID, tenant switch, principal, proyección y respuesta sin tenants ajenos |
| AC-CH-12 | PASS_OFFLINE | 21/21 REC-2FA-04 y casos MFA CH; archivos MFA intactos |
| AC-CH-13 | PASS_OFFLINE | 74/74 métodos nuevos C/H y matriz negativa |
| AC-CH-14 | PASS | integrity-final.json: inventario cubierto, HEAD/índice y backups; exclusiones expresas |
| AC-CH-15 | PASS | Matriz y plan escritos; ejecución real NOT_EVIDENCED |
| AC-CH-16 | BLOCKED_BY_EXTERNAL_DEPENDENCY | No se presenta ORM simulado ni configuración provisional como registro durable; dependencia crítica explícita |

## L. GOVERNANCE & INTEGRITY

Se preservan `S3-IMP-01`, `S3_DECISION_02A_NOT_CLOSED`, `PHASE31_5 = EXECUTION_HELD`, REC-2FA-04, REC-SSO-02 y evidencia Decision A. No se edita APPROVAL_MATRIX.md ni se renumeran decisiones: C/H son clientes/audiencias/confianza, B revocación durable y D scopes. Los archivos financial/foundation/settings y otros cambios ajenos inventariados se mantienen byte a byte.

integrity-final.json, code-hashes.json y parches por repositorio separan los 10 originales modificados del código previo y de archivos nuevos. No se hizo commit, push, reset, limpieza, migración, despliegue ni cambios de confianza activa. El inventario cubre archivos regulares tracked/untracked no ignorados, no integridad global del host.

## M. REMAINING BLOCKERS

- **Código:** no se identifica implementación local C/H pendiente dentro del contrato probado. Ruff no pudo ejecutarse y se debe ejecutar en un entorno que ya lo disponga; sintaxis/duplicados sí comprobados.
- **Configuración:** definir por entorno receiver, API key dedicada, keyrings, issuers y audiences; validar tamaño de cookies y política de 300 s. No se modificó configuración activa.
- **Esquema:** aplicar/revisar 0008 y provisionar filas/tenants; comprobar constraints y comportamiento persistente. BLOCKED_BY_EXTERNAL_DEPENDENCY, sin fallback de settings.
- **Pruebas HTTP/E2E:** PostgreSQL, persistencia, concurrencia/replay, HTTP real, navegador, versiones mixtas y rollback son NOT_EVIDENCED.
- **Autoridad externa:** aprobación separada para migraciones, claves reales, escritura compartida, activación y despliegue. No se solicita aprobación repetida para el trabajo local ya autorizado.

## N. NEXT ENGINEERING SLICE

**B — sesiones y revocación durable:** diseñar registros de sesión central/local con UUID, generación monotónica, causa/tiempo de revocación y trazabilidad por cliente/producto/tenant/usuario; logout y rotación con invalidación atómica, outbox/reintentos idempotentes, pruebas de ABA y carreras en PostgreSQL desechable. Mantener rechazo por introspección cuando la autoridad no esté disponible. Preparar código y pruebas offline antes de pedir operaciones fuera del mandato. B permanece abierto.

**D — scopes:** contrato de intersección rol × producto × entitlement × recurso/tenant, sin scope write genérico. Definir denegación para vacío/desconocido, aplicar en APIs/objetos QMS y supplier/customer y probar escalamiento horizontal/vertical. MFA/registro de cliente no conceden autorización universal. D y E/F/G permanecen abiertos.
