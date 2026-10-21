# REC-SSO-01 — Independent SSO & Product Entitlements Validation

Fecha de campaña: **2026-10-13**, America/Costa_Rica. Repositorio: `/home/felipe/proyectos/adminapps`.

## A. Executive Verdict

**FAIL — no procede cierre de seguridad. BLOCKED — validación integral de SSO y consumidores desplegados.** La investigación local está completada dentro de la autorización; no se corrigió ni aprobó producción.

El antecedente «falta organization_product_entitlements» **no se reproduce en la base configurada actualmente**: la relación existe, su migración está registrada y sus columnas coinciden con el modelo. Sí hay divergencias reales del esquema en **2FA y API keys**. La causa del HTTP 500 histórico queda **BLOCKED** hasta correlacionar su runtime, configuración efectiva y traceback sanitizado. No se sustituyó esa correlación por una hipótesis.

Se ejecutaron **33 pruebas unitarias aisladas: 25 PASS y 8 aserciones de seguridad/contrato incumplidas**. Cinco corresponden a brechas de autenticación/introspection; las otras tres prueban discrepancias o decisiones pendientes sobre billing, inicio temporal y vinculación de suscripciones. El `OK (expected failures=8)` del runner NO significa que la campaña pase. Cero conexiones de red/base en ese harness. Por separado se hicieron consultas SQL reales de solo lectura contra PostgreSQL local existente.

Sin cambios al repositorio, migraciones, generación de migraciones, datos de negocio, servicios, commits, push, deploy ni llamadas externas.

## B. Git Baseline & Integrity

**PASS.** Primera operación: `git status --short --branch`, HEAD, rama, diffs unstaged/staged. HEAD inicial/final: `b144b2505659ad39f756b9bc4530a7f24fe8c3ad`; rama `hardening/p0-p1-enterprise-readiness`, ahead 6 respecto de la referencia local origin (sin fetch).

Cambios ya existentes: `backend/config/settings.py` (+8/-1), `backend/apps/financial/`, `backend/scripts/s3_isolation_host_lab.sh`, `backend/scripts/tests/`, verificadores financieros y `docs/financial/`. Se preservaron íntegros. Los 15.536 archivos regulares del manifiesto inicial conservan SHA-256; Git, HEAD y diff son idénticos; `git diff --check` = 0. Dos enlaces de directorio `lib64` fueron excluidos por el hashing de archivos regulares, no identificados como adiciones. Archivos ignored, incluidos secretos, no están cubiertos por ese manifiesto; no se escribieron.

Evidencia: [baseline](git-baseline.txt), [final](git-final.txt), [integridad](integrity-result.json), [hashes iniciales](baseline-sha256.json), [fuentes revisadas](source-manifest.json).

No se modificó ni reabrió REC-2FA-04. Se mantienen exactamente:

- **S3-IMP-01 = BLOCKED_PENDING_AUTHORITY**
- **S3_DECISION_02A_NOT_CLOSED**
- **PHASE31_5 = EXECUTION_HELD**

## C. SSO Root Cause

Inventario activo, bajo `/api/integration/`:

| Elemento | Fuente | Resultado |
|---|---|---|
| Login SSO | `apps/integration/sso_views.py:199`, `urls.py` | PASS: localizado; autentica identidad local AdminApps, exige usuario y membresía/organización activos |
| Verificación 2FA | `sso_views.py:321`, `users/two_factor_service.py:207` | PASS de revisión: contexto firmado, consumo transaccional y revalidación de membresía |
| Introspection | `sso_views.py:407` | FAIL: verifica JWT pero no revalida identidad/membresía ni exige tenant |
| Validación por producto | `integration/views.py:450` | PASS unitario: consulta por organización y producto; entitlement ausente deniega |
| Credenciales legacy | `integration/views.py:526` | FAIL: `valid=true` sin exigir segundo factor |
| Modelos | `products/models.py`, `users/models.py`, `users/models_2fa.py`, `integration/models.py` | PASS: inventariados |
| Tests existentes | `integration/tests.py:566,657`, `products/tests.py:20,478` y pruebas transaccionales de users | BLOCKED para ejecución: usan DB/fixtures/migraciones; no se ejecutaron |

Dependencia exacta: `sso_login` / `sso_login_verify_2fa` → `_build_token_pair` → `require_commit_boundary` → `_build_token_pair_unchecked` → `_build_product_claims` → `_serialize_product_entitlements` → queryset sobre `organization_product_entitlements` filtrado por `membership.organization.id`, con joins a organización, producto, planes y suscripciones. Esta consulta se evalúa **antes** de `RefreshToken.for_user`.

**PASS, causalidad local aislada:** al inyectar `DatabaseError` en la lectura de claims, el código real produce APIException HTTP 500 genérica y no llama a emisión de tokens. Así se demuestra cómo una tabla ausente puede producir ese síntoma, pero no que lo haya causado en el runtime histórico. Los DatabaseError anteriores, en login, se convierten en 503.

**FAIL, divergencia real de esquema:** con los modelos actuales, la lectura de configuración 2FA requiere columnas inexistentes en la base inspeccionada; las consultas SQL `WHERE false` devolvieron `42703` y `42P01`. El autenticador de API keys también consulta campos ausentes. Estas causas de incompatibilidad están demostradas independientemente del antecedente de entitlements.

**BLOCKED, atribución histórica:** no se repitió login HTTP contra el servicio existente, porque puede crear desafíos/tokens, registrar actividad y escribir auditoría. Se observó Gunicorn con target `config.wsgi:application`; sus metadatos de arranque no prueban revisión ni settings cargados en memoria. El escaneo limitado del log local no encontró los errores de esquema buscados. Las hipótesis de otra DB/settings/search_path, runtime antiguo o esquema cambiado entre campañas siguen sin demostración.

## D. organization_product_entitlements Schema Diagnosis

**PASS:** está definida en `products.0002_productsystem_organizationproductentitlement`, con dependencias `products.0001`, `organizations.0003`, `subscriptions.0002` y modelo swappable de usuario. Crea `product_systems` y `organization_product_entitlements`, establece unicidad `(organization, product)` y hace seed de `ISO_SMART` / `MEDSUPPLIER` mediante RunPython. No crea habilitaciones automáticas de clientes. `products.0003` crea auditoría.

La configuración leída de `.env` y entorno apunta a development y loopback. Se usaron las credenciales ya configuradas únicamente en memoria, sin imprimirlas. Conexión con `default_transaction_read_only=on`, `statement_timeout=3000`, `connect_timeout=3`; `SHOW transaction_read_only` confirmó `on`. No se arrancó PostgreSQL.

| Comprobación SQL/metadata real | Estado | Evidencia |
|---|---|---|
| Tabla resoluble y en public; products.0002 y .0003 registradas | PASS | `local-config-schema.json`, `schema-detail.json` |
| Columnas del entitlement frente al modelo; SELECT de columnas WHERE false | PASS | Sin columnas faltantes/adicionales; consulta sin filas |
| users.0004 registrada y objetos requeridos disponibles | FAIL | Migración no registrada; faltan generation, last_totp_counter, failed_attempts, attempts_expires_at; falta two_factor_challenges |
| integration.0006 compatible con modelo actual | FAIL | No registrada; faltan 8 columnas de ciclo de vida de claves |
| Otras migraciones de apps inspeccionadas | FAIL, drift documental | integration.0007 y organizations.0004 tampoco registradas; no se atribuye a ellas el fallo SSO |
| Rol de la conexión con privilegios limitados | PASS acotado | NOSUPERUSER, NOBYPASSRLS, NOCREATEDB, NOCREATEROLE |
| RLS en entitlements y membresías | FAIL de defensa en profundidad | `relrowsecurity=false`, `relforcerowsecurity=false` en ambas tablas; no se modificaron políticas ni roles |

No hay evidencia de una migración de entitlements pendiente ni de tabla registrada pero ausente en esta DB. Sí hay evidencia de código de autenticación más nuevo que su esquema. No se ejecutaron `migrate`, `makemigrations`, bootstrap, grants ni cambios de datos. No se probó inventario comercial de entitlements reales: metadata no demuestra que un cliente tenga productos activos.

Evidencias reproducibles: [script SQL](schema_probe.py), [resultado SQL](schema-detail.json), [comparación modelo/esquema](model-schema-comparison.json), [configuración sanitizada](local-config-schema.json), [runtime](runtime-metadata.json).

## E. Product Entitlements & Tenant Isolation Matrix

AdminApps es autoridad contractual de identidad, membresías, tenant global, catálogo y entitlements. `Organization.id` es el UUID canónico; ISO Smart distingue tenant global/proyección de organización QMS. `ProductSystem` no se sustituye por catálogo de facturación o módulos legacy. AdminApps como consola no aparece como producto seeded: su acceso depende de autenticación/roles administrativos.

| Límite / escenario | Estado | Evidencia y alcance |
|---|---|---|
| Identidad/org/entitlement gobernados por AdminApps | PASS documental | `PRODUCT_NEUTRAL_ADMINAPPS_CONTRACT.md:1,40`; clientes locales usan la autoridad central |
| Org A con ISO_SMART no hereda MEDSUPPLIER | PASS unitario | Consulta enlaza org y product; entitlement ausente devuelve 403; ambos clientes normalizan código y forman endpoint específico |
| Login solicitando org B sin membresía | PASS unitario | 403 antes de `_build_token_pair` |
| Usuario sin membresía activa | PASS unitario | 403; no login válido |
| Entitlement disabled/suspended/cancelled/expired; org suspendida; producto retired | PASS unitario | Propiedades de modelos reales deniegan |
| Active con billing sin suscripción o past_due | PASS unitario | billing_not_configured / denegación |
| Trial sin suscripción | FAIL de coherencia documental | Código permite; contrato neutral exige suscripción; operaciones:72 y test existente:354 permiten excepción. No se clasifica como exploit demostrado |
| starts_at futuro | FAIL del guardrail temporal propuesto | Modelo permite antes del inicio. El contrato neutral enumera ends_at pero no starts_at: semántica requiere decisión humana |
| Suscripción vinculada a B reutilizada en entitlement A | FAIL del guardrail de vinculación propuesto | Serializer y propiedad permiten en memoria; Subscription no tiene owner tenant directo. No demuestra escritura HTTP por usuario sin permiso; contrato de compartir suscripción no está definido |
| Gestión de entitlements por viewer/auditor/user/org_admin | PASS unitario | IsAdmin exige rol global admin/superadmin; roles organizacionales ordinarios denegados |
| Administración global | PASS de revisión | ViewSet usa IsAdmin y queryset global; no confundir admin global con org_admin |
| Outage de AdminApps en ambos clientes | PASS unitario | `allowed=false`, source fail_closed; transporte sustituido explícitamente |
| Denegación comercial con fallback habilitado | PASS unitario | Ambos clientes preservan denegación y no llaman fallback |
| Claves de caché por producto y tenant | PASS unitario | Separadas por UUID/código; no prueba frescura temporal de permisos |
| Revocación de entitlement por introspection | PASS unitario limitado | Relee productos por llamada; active del token sigue true, consumidor debe comprobar access_allowed |
| Revocación de usuario/membresía/rol | FAIL | Introspection devuelve active=true sin consultar su estado vivo |
| Aislamiento SQL mediante RLS | FAIL para tablas inspeccionadas | Ausencia real de ENABLE/FORCE RLS; aislamiento de aplicación no lo sustituye |
| Aislamiento completo entre productos desplegados | BLOCKED | No se ejercitaron servicios, identidades, DB ni permisos reales de consumidores |

Los clientes se inspeccionaron/importaron localmente sin iniciar sus aplicaciones. Pruebas usan `_make_request` y resolución de ID sustituidos: verifican contrato de llamada y lógica de denegación, no integración real. El fallback de ISO Smart también depende de sus settings; esta campaña no certifica settings de un despliegue. Se conservaron hashes de fuentes de ambos repositorios.

## F. SSO / 2FA Security Findings

| ID / prioridad de revisión | Estado | Hallazgo y límite |
|---|---|---|
| SSO-01 / alta | FAIL | `validate_credentials` devuelve valid=true con factor habilitado sin OTP. Backends locales de ambos consumidores confían en valid para sincronizar/autenticar. Bypass demostrado en unidad de autoridad y trazado estático del consumidor; explotación E2E no ejecutada |
| SSO-02 / alta | FAIL | Introspection no consulta usuario/membresía ni revocación de rol; además acepta access firmado sin tenant. Dos aserciones independientes incumplidas |
| SSO-03 / alta | FAIL | SIMPLE_JWT no configura ISSUER/AUDIENCE; token firmado con iss/aud ajenos se acepta en unidad real. Login permite audience/client_id del solicitante; código fuente de consumidores tampoco configura validación iss/aud. Topología real de claves compartidas no verificada |
| SSO-04 / media | FAIL | DatabaseError escapa introspection, también puede originarse antes en require_api_key. Riesgo de respuesta no normalizada; exposición de traceback depende de DEBUG/middleware. DEBUG local bruto `release` se interpreta false; no se demostró filtración real de secretos |
| SSO-05 / alta | FAIL de configuración de claims | Tokens emiten `tenant:write` para cualquier rol en sso_views.py:131,146. No se demostró que un consumidor conceda escritura basándose solo en ese scope; política de scopes por rol pendiente |
| SSO-06 | PASS unitario | Fallo de lectura de entitlement previo a emisión no llama a RefreshToken.for_user; error de login sanitizado; no se simula success |
| SSO-07 | PASS de revisión + unidad acotada | Canal SSO/login separado por salt/purpose/scope; desafío no sirve como access JWT; TTL 300 s, nonce 256 bits, binding de contexto/generation y consumo con locks durables presentes |
| SSO-08 | BLOCKED | Anti-replay persistente, concurrencia, sesiones y revocación de tokens reales no reejecutados; requieren infraestructura/fixtures autorizadas. No se atribuye PASS nuevo a evidencias REC-2FA-04 |
| SSO-09 | NOT_TESTED | IdP externo, OIDC/SAML, callback de federación, state/nonce del navegador, PKCE, TLS y logout federado |

El SSO localizado es autenticación de credenciales en AdminApps y JWT centralizados; no se encontró un callback OIDC/SAML en las rutas y frontends inspeccionados. El nonce del desafío 2FA no equivale a state OIDC. No se declara seguro un flujo de federación que no se ejercitó.

Access configurado en AdminApps: 8 h; refresh: 7 días, rotación/blacklist activadas. Claims son snapshots; `/api/auth/refresh/` usa TokenRefreshView estándar y no un refresh SSO que reconstruya producto/membresía. Revisión estática: no afirmar revocación inmediata de access ni actualización de claims por refresh. Los consumidores tienen cachés de validación (default 300 s); el contrato debe precisar frescura e invalidación para acciones sensibles.

El fallo de entitlements ocurre antes de crear el refresh. En otras fallas posteriores puede haber consumo irreversible de desafío o fila OutstandingToken aunque no se entregue respuesta exitosa. Esto no es una concesión de acceso demostrada; tampoco se afirma atomicidad global de login. Se preserva el diseño REC-2FA que no restaura un factor consumido tras fallo del emisor.

API keys de integración autentican servicio, pero el decorador genérico no limita por producto/tenant y puede dar acceso a datos de varias organizaciones a un servicio confiable. La segmentación de servicios requiere contrato explícito, no inferirla del nombre de la key. Login SSO usa vistas Django csrf_exempt; las clases DRF de throttling no se aplican automáticamente. Protección de rate-limit perimetral/password brute force: **NOT_TESTED**; no se realizaron cargas ni intentos repetidos reales.

## G. Executed Tests and Real Evidence

1. **PASS:** captura Git inicial/final y SHA-256, sin cambios.
2. **PASS / FAIL según tabla D:** metadata y consultas reales read-only contra PostgreSQL local existente. No fixtures, migraciones, SELECT de datos personales ni peticiones autenticadas al servicio.
3. **25 PASS / 8 FAIL de aserción:** [harness](offline_tests.py), [log](offline-tests.log), [resultados](offline-results.json). Modelos no guardados, RequestFactory directo, firma/JWT reales con clave sintética, dobles explícitos de ORM/autenticación/emisión/transporte. DB dummy y barreras a conexión DB/socket; contador final 0/0. Configuración basada en settings reales sin `.env`, scheduler/logs persistentes desactivados y apps.financial excluida solo en harness. No se cambió config del repositorio.
4. **PASS de trazabilidad:** se detectó un error de fixture en el primer intento de suscripción (relación en lado incorrecto), se invalidó ese caso, corrigió y repitió la suite aislada. Todas las fallas finales son AssertionError de la condición bajo evaluación. [Corrección](harness-correction.json); intento inicial conservado. No se cuenta el TypeError como vulnerabilidad.
5. **BLOCKED:** suites APITestCase/TransactionTestCase existentes, E2E PostgreSQL/Chromium, propagación de revocación y aislamiento RLS operacional. No se ejecutaron porque crean datos/esquema o requieren entorno que no está autorizado a levantar.

Comandos reproducibles de los dos scripts, desde el repositorio:

```bash
backend/.venv/bin/python -B /tmp/adminapps-rec-sso-01-_fpvp5km/offline_tests.py
backend/.venv/bin/python -B /tmp/adminapps-rec-sso-01-_fpvp5km/schema_probe.py
```

El segundo vuelve a consultar la base local configurada y tiene guardas de development/loopback/read-only. No ejecutarlo contra otro target sin revisar autorización. Dependencias existentes del harness: Django 4.2.22, DRF 3.15.2, SimpleJWT 5.4.0, psycopg2 2.9.10, PyJWT 2.8.0. Un sondeo inicial del antiguo `venv_admin` falló por Django ausente, antes de conectar; se usó `.venv` existente, sin instalar nada.

La evidencia REC-2FA-04 proporcionada por el usuario queda como antecedente, sin repetirla. El REPORT abierto en IDE es una campaña anterior con fallos UI históricos y SSO local de laboratorio; no se usó para reemplazar ni contradecir los resultados posteriores indicados por el usuario.

## H. Files Changed / Files Preserved

**PASS: cero archivos modificados/agregados en el repositorio.** También se preservaron las fuentes de ISO Smart y MedSupplier: solo lectura/importación con bytecode deshabilitado. No hubo corrección de producto en esta campaña; las remediaciones se proponen abajo.

Se crearon únicamente scripts y evidencia de REC-SSO-01 en este directorio `/tmp/adminapps-rec-sso-01-_fpvp5km`, incluido este informe. No se escribieron secretos reales, JWT reales ni cuerpos de autenticación. Los hashes de archivos ignorados/credenciales no formaron parte de la comparación inicial; no afirmar cobertura SHA de ellos.

## I. Remaining Blockers and External Dependencies

- **BLOCKED:** atribución del 500 histórico a runtime/DB/revisión exactos y validación funcional del esquema actual con login real.
- **BLOCKED:** reparar drift de users.0004 / integration.0006 requiere autorización explícita de esquema y revisión del plan de dependencias. organizations.0004/integration.0007 quedan inventariadas, no autorizadas ni justificadas como reparación SSO.
- **BLOCKED:** pruebas integrales y anti-replay persistente requieren DB desechable/fixtures autorizadas. Los ajustes locales financial hacen especialmente improcedente un `migrate` general.
- **BLOCKED:** contrato sobre trial, inicio de vigencia, vinculación de suscripción, scopes de rol, audiencias/clientes autorizados, alcance de API keys y frescura de revocación.
- **NOT_TESTED:** IdP externo, consumidores desplegados, certificados, redirects y confianza real entre firmantes.

## J. Minimal Remediation Plan

| Causa / hallazgo | Corrección mínima propuesta | Validación requerida |
|---|---|---|
| Drift de autenticación | Identificar runtime/target; preparar revisión de las migraciones existentes users.0004 e integration.0006 y sus dependencias. No crear una migración de entitlements ni aplicar todo el árbol | Plan acotado aprobado, backup/rollback; posterior metadata y login/challenge/introspection real en entorno autorizado |
| Legacy omite 2FA | Denegar valid=true para usuario con 2FA pendiente y conducir consumidores al flujo SSO con desafío; preservar respuestas sin grant ante error | Unidad negativa con factor habilitado + regresión de login de ambos consumidores |
| Introspection no revalida | Exigir UUID/sub válidos; usuario y membresía/organización activos; devolver rol vivo, active=false ante revocación; mantener productos como evaluación independiente | Casos usuario deshabilitado, membresía revocada, tenant ausente/ajeno, cambio de rol |
| Falta iss/aud/client binding | Acordar registro/allowlist de clientes y audiencias; validación simétrica en autoridad y consumidores; política de rotación de claves | Pruebas entre productos, issuer/audience incorrectos, compatibilidad de refresh |
| DB error no normalizado | Capturar DatabaseError en el límite de introspection incluyendo require_api_key; respuesta 503 genérica sin active=true, logs sanitizados | Error en clave y en productos; asegurar que no se devuelve payload parcial |
| Scope tenant:write fijo | Derivar scopes según rol/entitlement definido por contrato y validarlos en consumidor | Viewer/auditor sin write; deny-by-default para rol desconocido |
| Semántica trial/starts_at/suscripción | Resolver contradicción documental de trial; definir fecha de inicio y si una suscripción puede compartirse; después añadir guardas mínimas | Matriz de billing/fechas/tenant en memoria y luego constraints si se autorizan |
| RLS ausente | Diseñar política para las tablas tenant-scoped y rol central administrativo; revisión DBA independiente | Ensayos SQL de tenant A/B, ausencia de contexto, roles owner/runtime; no heredar PASS de financial |

No se recomienda corregir availability devolviendo listas vacías, suprimiendo consultas, otorgando productos por plan legacy, desactivando 2FA, usando SQLite como autoridad ni habilitando fallback en producción. Se conserva el fallo cerrado observado.

## K. Explicit Human Approval Gates

**BLOCKED hasta autorización explícita del usuario/autoridad responsable**, conforme a las reglas 3, 4, 10 y fase E de esta campaña:

1. Cualquier modificación/aplicación de esquema, migración existente o nueva, datos, roles, RLS, grants o bootstrap. El target, lista exacta, efectos y rollback deben ser revisables antes de ejecución.
2. Iniciar servicios o laboratorio PostgreSQL y crear fixtures persistentes para integración/E2E.
3. Cambios contractuales entre productos: protocolo legacy/2FA, audiencias, roles/scopes, revocación, semántica comercial y alcance de servicio.
4. Conexiones a IdP/entornos externos, despliegues o cambios de producción.
5. Commit, push o publicación de cambios.

Esto no revoca la autorización ya dada para código/pruebas locales acotadas. No se aplicaron parches de producto porque no resuelven el drift por sí solos y las principales correcciones requieren compatibilidad contractual entre consumidores. El informe y las pruebas están terminados y revisables; no queda ejecución esperando un permiso implícito.

## L. Recommended Next Action

Priorizar **SSO-01 (2FA legacy), SSO-02 (revocación/introspection) y reconciliación del runtime/esquema**. Abrir una remediación acotada con decisiones explícitas de compatibilidad, usando estas pruebas como reproducción; preparar el plan exacto de migraciones existentes del target identificado para aprobación final antes de aplicarlo. Después autorizar un laboratorio desechable para demostrar login, replay, revocación y límites entre productos con persistencia real.

No ejecutar `migrate` como reparación del síntoma de entitlements: esa relación ya está presente en la base inspeccionada. No cerrar seguridad, SSO externo ni producción con esta evidencia local.
