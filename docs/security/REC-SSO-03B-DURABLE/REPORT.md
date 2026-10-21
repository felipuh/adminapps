# REC-SSO-03 / Decision B — reporte final

Fecha: 2026-10-15. Host autorizado: 192.168.56.11. Evidencia: `/tmp/rec-sso-03b-durable-t4kl43cb`.

## A. Executive Verdict

**DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED**. Código implementado en los tres repositorios, 149 pruebas seleccionadas PASS_OFFLINE y dos builds frontend PASS. **Cierre durable: BLOCKED_BY_EXTERNAL_DEPENDENCY. PRODUCTION_READY = FALSE.** No se aplicaron migraciones, no hubo consultas a bases compartidas, ni servicios/secretos/configuración activa modificados. NO_DEPLOYMENT / NO_COMMIT / NO_PUSH / GOVERNANCE_PRESERVED.

El resultado no convierte las suites A/C/H originales en PASS: sus fallos siguen íntegros y se reconcilian por método. Tampoco adjudica scopes/política comercial, PostgreSQL, navegador o compatibilidad de versiones no ejecutadas.

## B. Git Baseline & Integrity

| Repositorio | HEAD conservado | Archivos previos modificados por B |
|---|---|---|
| adminapps | `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` | 4 |
| isosmart | `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` | 5 |
| ISO_Smart_MedSupplier | `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` | 6 |

Baseline de 45.708 archivos tracked/untracked no ignorados. Los 15 archivos previos editados conservan sus originales en `before/`; no hay archivos previos eliminados. HEAD e índice sin cambios en los tres repositorios. Suites históricas, código MFA, financial/foundation y adjudicaciones conservados byte a byte. Migración 0008 intacta; 0009 y 0010 creadas sin aplicar. La cobertura de integridad es el inventario Git indicado, no todo el host.

`baseline.json`, `integrity-final.json`, `code-hashes.json`, `*.initial.diff`, `*.decision-b.patch`, `*.review.diff` y `SHA256SUMS` permiten separar cambios previos de B. Los parches decision-b incluyen archivos nuevos que git diff ordinario no muestra.

## C. Historical Regression Reconciliation

Fase 0 recuperó logs originales, inventario y baselines A/C/H. `historical-reconciliation.json` conserva 69 métodos fallidos heredados con su traceback, clasificación, severidad y sucesor; `ch-successor-reconciliation.json` agrega los 38 métodos C/H afectados por sus fixtures anteriores a B. No se editó ninguna expectativa histórica.

| Suite histórica | Antes de B P/F/E | Después de B P/F/E |
|---|---|---|
| historical-03a-adminapps | 7 / 20 / 3 | 7 / 20 / 3 |
| historical-03a-isosmart | 9 / 0 / 11 | 9 / 0 / 11 |
| historical-03a-medsupplier | 9 / 0 / 11 | 9 / 0 / 11 |
| historical-02 | 8 / 19 / 5 | 8 / 19 / 5 |
| ch-adminapps | 18 / 0 / 0 | 2 / 4 / 12 |
| ch-isosmart | 28 / 0 / 0 | 17 / 0 / 11 |
| ch-medsupplier | 28 / 0 / 0 | 17 / 0 / 11 |

Conteos por método, no por subtest: los logs conservan también todos los fallos/errores individuales. Fixtures A no satisfacen el contrato C/H; fixtures C/H no contienen fence/sesión/generación B. Los sucesores ejecutan los mismos invariantes con el contrato nuevo; el rechazo temprano de una prueba histórica no se usa como evidencia de esa invariante.

Tres candidatos comerciales siguen FAIL (HIGH): trial sin suscripción, starts_at futuro y vinculación de suscripción ajena. Scopes finos siguen NOT_EVIDENCED. No se inventó una política para obtener PASS. Regresiones funcionales del alcance corregidas: logout sin revocación central, replay de refresh MedSupplier y carrera de refresh ISO; concurrencia SQL todavía pendiente.

## D. AdminApps Session Architecture

Nueva SSOSession central con UUID, usuario UUID, cliente, producto, tenant, generación, autoridad, autenticación/creación/expiración, estado, revocación/motivo, correlación y vínculo MFA por digest/generación. UserSession heredada no cumple este contrato. SSOSecurityFence ofrece contador durable, época de autoridad y activación explícita. Tokens completos y secretos no se guardan en los nuevos registros.

El JWT conserva C/H y añade lifecycle, sid, sg, av y auth_time. El JWT es compacto: proyección de nombre/membresía/productos llega por introspección viva. Firma válida por sí sola no autoriza.

## E. Durable Revocation Model

Triggers preparados invalidan por usuario, membresía/rol, tenant, cliente, credencial, MFA, producto y entitlement; cubren update/bulk/M2M y ambas direcciones de cambios ABA. Política MFA global dispone de hook administrativo. Plan/suscripción/permisos globales invalidan conservadoramente todas las sesiones. Contrato y tabla de alcances en CONTRACT.md. Disparo real de triggers: BLOCKED_BY_EXTERNAL_DEPENDENCY.

## F. Atomic Rotation & Replay Protection

Operaciones con transacción durable PostgreSQL y orden fence → sesión. Incrementos bajo row lock, generación única, restricciones de estado/tiempo, historial inmutable y challenge MFA único. Rotación cambia sg/jti y consume la generación previa; mantiene sid/av/auth_time/exp. Logout es idempotente y puede revocar su sesión incluso si esa generación ya rotó. El render/firma falla dentro de la transacción; una respuesta perdida después del commit requiere reautenticación.

Pruebas de carreras y rollback usan simulación explícita, sin atribuirles aislamiento PostgreSQL. Bloqueo global, latencia y deadlocks necesitan laboratorio. Una decisión de acceso ya concedida no constituye cancelación distribuida de una operación empresarial en curso.

## G. ISO Smart Integration

LOCAL vincula sujeto, tenant, producto y sid/sg/av a CENTRAL. Cada uso consulta AdminApps; refresh rota centralmente, verifica la nueva prueba y nunca extiende el límite absoluto. Logout revoca el request autenticado. HttpOnly/CSRF conservados, max-age acotado por exp, limpieza de estado al denegar refresh.

Medición con firma RSA y serialización reales: Set-Cookie típico access **3176 bytes**, refresh **3179 bytes**; valores JWT de escenario máximo representativo **5010/5011 bytes**, rechazados. Presupuestos de aplicación: 4096 bytes por Set-Cookie y 7000 por par en Cookie. Nginx de repositorio no fija large_client_header_buffers; configuración efectiva/proxy/navegador NOT_EVIDENCED.

La reautenticación cada 300 segundos permanece: sesiones largas, formularios y pestañas concurrentes pueden necesitar nuevo login/MFA. No se extendió TTL. Alternativas y tradeoffs en CONTRACT.md; no se implementó renovación central que amplíe vigencia.

## H. MedSupplier Integration

Misma autoridad central y binding durable con producto fijo MEDSUPPLIER, conservando transporte Bearer/body. Refresh ahora consume la generación y reemplaza ambos tokens; respuesta incompleta o denegación elimina estado frontend. Se evita persistir JWT completos en OutstandingToken para estas sesiones. No se tocaron registros reales preexistentes.

## I. Outbox & Revocation Propagation

TenantIntegrationOutbox fue evaluado: su agregado/versionado tenant no sirve directamente para sesión/generación. Nueva SSORevocationOutbox atómica, evento UUID, unicidad(session,generation), cliente/producto/tenant/trace_id, reintentos y ACK. Adaptador de entrega y reducer idempotente preparados y probados offline; no se arrancó transporte ni worker. Eventos tardíos solo aumentan la invalidación; jamás reemplazan introspección.

## J. Security Test Results

| Selección vigente | PASS_OFFLINE | FAIL | ERROR |
|---|---:|---:|---:|
| AdminApps B, incluye sucesoras C/H | 43 | 0 | 0 |
| ISO Smart B, incluye sucesoras C/H | 35 | 0 | 0 |
| MedSupplier B, incluye sucesoras C/H | 35 | 0 | 0 |
| REC-2FA-04 | 21 | 0 | 0 |
| Frontend A conservada | 8 | 0 | 0 |
| Frontend B refresh | 7 | 0 | 0 |
| **Total seleccionado** | **149** | **0** | **0** |

Dos builds Vite PASS; ESLint de archivos relevantes PASS; AST Python, JSON y git diff --check PASS. Ruff no está instalado: NOT_EVIDENCED; no se descargaron dependencias. Guards de las suites B registran cero intentos DB/red. Versiones realmente ejecutadas en versions.json. No se afirma compatibilidad con otras versiones.

Reproducción offline desde cada cwd (sin settings activos/.env backend):
```sh
cd /home/felipe/proyectos/adminapps
backend/.venv/bin/python -B backend/scripts/rec_sso_03b_offline.py
backend/.venv/bin/python -B backend/scripts/rec_sso_02_2fa_regression.py
cd /home/felipe/proyectos/isosmart/backend
.venv/bin/python -B integration/tests_b_offline.py
cd /home/felipe/proyectos/ISO_Smart_MedSupplier/backend
.venv/bin/python -B integration/tests_b_offline.py
# En cada frontend:
node scripts/test-decision-a-offline.mjs
node scripts/test-decision-b-offline.mjs
```

checks-final.py y final-runs/checks.json registran comandos/cwd/resultados de las suites vigentes e históricas. security-test-matrix.csv enlaza los casos obligatorios, adversariales y bloqueos.

## K. Cross-Product Isolation

Pruebas coordinadas offline emiten CENTRAL mediante AdminApps real con persistencia simulada y verifican con los codecs reales de ambos consumidores: propio ALLOW, consumidor ajeno/LOCAL-as-CENTRAL/tenant ajeno DENY y viewer conservado. Keyrings, issuer, audiences singleton y contrato C/H no se debilitaron. No es HTTP E2E.

## L. Acceptance Criteria

| Criterio | Estado | Alcance / límite |
|---|---|---|
| AC-B01 | PASS_OFFLINE | Modelo y contrato UUID/cliente/tenant; persistencia real pendiente |
| AC-B02 | PASS_OFFLINE | Contador monotónico, locks y constraints preparados; SQL no ejecutado |
| AC-B03 | PASS_OFFLINE | Introspección deniega estado inválido; ORM simulado |
| AC-B04 | PASS_OFFLINE | Logout central/idempotencia probado en lógica y consumidores |
| AC-B05 | PASS_OFFLINE | Denegación de usuario/cliente/tenant; triggers reales pendientes |
| AC-B06 | PASS_OFFLINE | Generación/autoridad obsoletas y ABA de lógica DENY |
| AC-B07 | PASS_OFFLINE | Replay/rotación/carreras simuladas; aislamiento real bloqueado |
| AC-B08 | PASS_OFFLINE | 35 pruebas ISO, transporte/CSRF/refresh vigente |
| AC-B09 | PASS_OFFLINE | 35 pruebas MedSupplier, refresh/logout/autoridad |
| AC-B10 | PASS_OFFLINE | Codecs e intercambio coordinado bidireccional |
| AC-B11 | PASS_OFFLINE | 69 métodos históricos + 38 C/H reconciliados; no se borran FAIL |
| AC-B12 | PASS_OFFLINE | 21 REC-2FA-04, archivos MFA intactos |
| AC-B13 | PASS_OFFLINE | 149 pruebas seleccionadas; ver límites de suites originales |
| AC-B14 | PASS | HEAD/índice/archivos previos y adjudicaciones preservados |
| AC-B15 | PASS | Dependencias PostgreSQL/E2E explícitamente clasificadas |
| AC-B16 | PASS | Plan de activación/reversión escrito, NO ejecutado |

## M. Remaining Blockers

- **Crítico externo:** 0008/0009/0010 sin aplicar; filas SSOClient, tenants y fence sin provisión real verificada. AC-CH-01/16 siguen bloqueados. Runtime sin estado activado DENY.
- **Crítico externo:** ejecución/compilación SQL, aislamiento transaccional, concurrencia, triggers, rollback y persistencia PostgreSQL.
- **Alto:** tres políticas comerciales heredadas y scopes finos D pendientes; no se adjudica acceso empresarial universal.
- **Externo:** claves/configuración de confianza por entorno, HTTP/E2E, navegador, headers efectivos, versiones mixtas, reversión y carga del fence.
- **Herramienta:** Ruff no disponible; AST/ESLint/build no sustituyen ese análisis.
- **Transporte:** eventos preparados con callback, sin worker ni integración de entrega externa activa.

## N. PostgreSQL/E2E Readiness

POSTGRES_E2E_READINESS.md define las precondiciones y matriz real con conexiones independientes, MFA, bulk/M2M, fallo de commit, ABA, reinicio, eventos, roles DB, navegador y rollback. BLOCKED_BY_EXTERNAL_DEPENDENCY. Las tablas son autoridad IAM global de AdminApps; no se reivindica RLS empresarial ni acceso directo de consumidores. Autorización de laboratorio/activación sigue siendo externa a este mandato.

## O. Next Slice — Decision D Scopes

Definir intersección rol × producto × entitlement × tenant/recurso, denegar scopes vacíos/desconocidos, resolver las políticas comerciales registradas y probar escalamiento horizontal/vertical por endpoint/objeto. Ni MFA ni sesión vigente ni un cambio de rol conceden permisos implícitos. Decision D y restantes decisiones no se cierran en B.

S3-IMP-01, S3_DECISION_02A_NOT_CLOSED y PHASE31_5 = EXECUTION_HELD conservados. REC-2FA-04, REC-SSO-02, REC-SSO-03A y REC-SSO-03B-CH mantienen su historia y adjudicación.
