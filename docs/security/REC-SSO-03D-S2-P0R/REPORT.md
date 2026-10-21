# REC-SSO-03D-S2-P0R — Session Convergence, Service Grants & Functional Authorization

2026-10-19 · America/Costa_Rica · host local autorizado `192.168.56.11`.

## A. Executive Verdict

**DECISION_D_S2_P0R_PARTIAL_WITH_EXPLICIT_BLOCKERS**

**PRODUCTION_READY = FALSE · NO_DEPLOYMENT · NO_COMMIT · NO_PUSH · GOVERNANCE_PRESERVED**

Se corrigió código de AdminApps y de ambos consumidores. **40 métodos nuevos únicos PASS_OFFLINE**:
34 de API/serializers/adaptadores y seis de lifecycle central con RSA real. Siete métodos de
reproducción fallan contra el baseline anterior y pasan después de los cambios. No hubo conexión
a DB ni red en los harnesses; ORM, transporte HTTP, commits y locks fueron simulados.

El alcance corregido incluye revocación SSO explícita propia bajo el fence B, logout local repetible
con refresh firmado, grants estrictos, aislamiento de módulos por producto, consumo de invitaciones
con autoridad vigente, y clientes que no reutilizan caché ni fallback ante denegación central.
Se aumentó la cobertura funcional de cambios de plan, activación/cancelación, pagos, reducción de
entitlements, membresías, deshabilitación, contraseña y suspensión del tenant.

**No hay cierre de convergencia local/global.** `UserSession` sigue siendo un registro que
`JWTAuthentication` no consulta. La prueba nueva caracteriza que un access JWT local firmado sigue
autenticando después de desactivar esos registros. La respuesta del endpoint ahora explicita ese
límite. Tampoco están acreditadas persistencia PostgreSQL, concurrencia, provisión real ni E2E.

En las 1.421 ejecuciones seleccionadas finales hay **1.337 PASS, 24 FAIL y 60 ERROR por método**.
Los FAIL/ERROR A/C/H se conservan exactamente contra baseline; existe además **un ERROR nuevo de
fixture histórica de invitaciones** (antes PASS), descrito en J. No se presenta todo el conjunto como verde.

## B. Baseline and Integrity

Se recuperó `/tmp/rec-sso-03d-api-p0-20261016` y se consultó el reporte revisado el 19 de octubre en
`docs/security/REC-SSO-03D-S2-API-P0`. Ese directorio contenía la evidencia más reciente de 50 métodos;
los logs D/B/MFA/consumidores allí eran del 16. Esta ejecución repitió las suites relevantes.
El reporte y ledger iniciales están en [inherited-REPORT.md](inherited-REPORT.md) e
[inherited-authorization-delta.csv](inherited-authorization-delta.csv); sus originales no se editaron.

Antes de modificar código se registraron **45.786 archivos** de los tres repositorios, sus hashes,
status dirty, HEAD e índices. El snapshot completo está en `/tmp/rec-sso-03d-s2-p0r-20261019/before` y
su manifest en `baseline.json`; [baseline-summary.json](baseline-summary.json) guarda ruta, hash y resumen.
Las IP locales se inspeccionaron sin sondear servicios; incluían la dirección autorizada.

| Repositorio | HEAD conservado | Delta de código de esta ejecución |
|---|---|---|
| AdminApps | `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` | 8 archivos existentes + 3 nuevos |
| ISO Smart | `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` | `backend/integration/client.py` |
| MedSupplier | `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` | `backend/integration/client.py` |

[code-hashes.json](code-hashes.json) enumera los 13 archivos y sus hashes antes/después.
[p0r-only.patch](p0r-only.patch) compara contra el estado dirty inicial, **no contra HEAD**.
[integrity-final.json](integrity-final.json) verifica índices, HEAD, archivos preexistentes y ausencia
de eliminaciones. Settings, secretos, migraciones, suites históricas, Django Admin y core financiero
no tienen cambios nuevos. Los documentos nuevos de consumidores registran el contrato de integración.
`SHA256SUMS` sella este paquete de evidencias; no incluye su propio hash.

La reconciliación del resolver conserva las 774 entradas anteriores y añade cuatro entradas de
la nueva acción SSO (incluidos alias/OPTIONS): 778 entradas, 265 rutas y 271 handler/actions.
No se cuentan esas entradas como pruebas funcionales; véase [resolver-reconciliation.json](resolver-reconciliation.json).

## C. Local/Central Session Reconciliation

| Estado/credencial | Autoridad propietaria | Quién lo verifica | Revocación y límite |
|---|---|---|---|
| `UserSession` AdminApps | AdminApps, registro local | Listado/acción de registro | `revoke_sessions` desactiva registros propios; no invalida access JWT ni SSO |
| Access JWT humano AdminApps | SimpleJWT/AdminApps | JWTAuthentication y gates humanos | Firma/expiración y usuario vivo; no se demostró vinculación a UserSession/familia revocable |
| Refresh JWT AdminApps | SimpleJWT/blacklist | Endpoint refresh | Logout comprueba propietario y blacklist; no revoca un access ya emitido |
| Cookie de sesión Django | Django session backend | SessionAuthentication | Logout REST actual no ejecuta logout Django; no afirmar revocación de cookie |
| `SSOSession` + generación/authority_version | AdminApps central | Lifecycle B/introspection bajo fence | Logout, rotación, revocación administrativa y nueva revocación propia |
| `SSOSecurityFence` + outbox | AdminApps central | Servicios B + triggers preparados | Orden fence→session; SQL/commit/outbox durable pendientes de prueba real |
| LOCAL JWT/cookie/proyección ISO/Med | Cada consumidor para transporte/proyección | C/H/B: firma, binding y prueba central viva; D añade scopes | No son UserSession de AdminApps; prueba central revocada deniega en sucesoras B/D |
| IntegrationAPIKey y grants | AdminApps | Hash autenticado + grant por credential_id | No es sesión humana, no hereda de SSOClient; denegación sin provisión explícita |

La matriz exportable está en [session-authority.csv](session-authority.csv). No existe equivalencia
implícita entre JTI local, SID central y sesiones del consumidor.

## D. Revocation Implementation

Nueva acción `POST /api/auth/users/revoke_sso_sessions/`: `{}` revoca todas las sesiones centrales
del usuario humano autenticado; `session_id` limita a una sesión propia. Serializer UUID real,
campos estrictos y lookup por SID **y user_id**. No admite IDs que deban conservarse, ni selección
de otro principal/tenant. La respuesta separa `scope=central_sso` y `local_sessions_revoked=false`.

El servicio relee al usuario activo y elegible dentro de `locked()` de B; selecciona sesiones propias,
usa `revoke_record` y su generación/outbox existentes. Repetir devuelve cero transiciones adicionales.
Pruebas con RSA real comprueban SID ajeno/inexistente, revocación individual/todas, idempotencia,
introspección denegada, rotación denegada y generaciones anteriores inválidas. Las filas de otros
usuarios permanecen activas en la simulación. Un fallo de respuesta posterior al servicio no reactiva.

Logout local admite repetir un refresh ya blacklisted sin omitir firma, tipo, expiración ni ownership.
Access tokens, firma manipulada y refresh de otro usuario deniegan antes de auditoría.
La blacklist ejecutada no se restaura por error posterior de auditoría. El parámetro refresh sigue
siendo opcional: no se transformó silenciosamente este endpoint en logout global.

`revoke_sessions` conserva el filtro de propietario y el JTI autenticado. Su respuesta ahora declara
`scope=local_registry`, `access_tokens_revoked=false`, `central_sessions_revoked=false`.
**Esto transparenta el contrato; no soluciona la revocación de JWT locales.** Cambio/reset de contraseña,
deshabilitación y revocaciones administrativas centrales siguen dependiendo de los triggers B para
invalidación persistente que sobreviva a un ciclo deshabilitar→habilitar. No se aplicaron ni ensayaron.

[CONTRACT.md](CONTRACT.md) y [p0r-contract.openapi.json](p0r-contract.openapi.json) detallan payloads,
semántica, errores y configuración. Persistencia/rollback/concurrencia PostgreSQL: **NOT_EVIDENCED**.

## E. Service Grants Security

`INTEGRATION_API_GRANTS[credential_id]` exige fila autenticada por hash, PK, hashed_v1, actividad,
status activo y ausencia de revoked_at. Listas no vacías, strings únicos, operaciones exactas,
UUID de tenant y productos del catálogo; campos extra/operaciones desconocidas/grants incompletos
denegados. Un grant de otra credencial no puede prestarse. No se consulta SSOClient para inferirlo.

El handler de módulos antes podía devolver MEDSUPPLIER o códigos legacy a una credencial concedida
solo para ISO_SMART. Ahora filtra la consulta de entitlements y la salida completa por product_codes,
incluidas las exenciones owner. El mapping de códigos legacy sin producto adjudicado queda retenido.

Las pruebas coordinadas usan una **credencial sintética con el formato y hash reales**, pasando por
`authenticate_integration_api_key`, decorador, resolver y handlers de verdad. Se simula únicamente
persistencia/transporte. No se creó, leyó, rotó ni provisionó ninguna credencial real del entorno.
La provisión exacta sin secretos se entrega en CONTRACT.md; falta ejecutarla externamente.

## F. Consumer Compatibility

Se ejecutaron **ambos clientes reales** (`integration/client.py`) contra los siete handlers centrales
mediante transporte requests simulado que resuelve las URLs Django reales. Cada producto probó su
propio grant: ISO_SMART en ISO Smart y MEDSUPPLIER en MedSupplier. Se comprobaron contenido de
productos/módulos, membresía del tenant, ALLOW y denegación por grant retirado, credencial revocada,
tenant ajeno y producto ajeno. El endpoint de productos usa el transporte real del cliente, pues no
hay wrapper específico de esa operación; los demás usan sus métodos públicos.

Los clientes omiten caché en lecturas protegidas y propagan HTTP 401/403 como denegación explícita;
no activan fallback aunque esté habilitado en el fixture de cada cliente. ISO Smart ahora también
bloquea el fallback de transporte cuando IS_PRODUCTION=true, como ya hacía MedSupplier; se probó con timeout. El helper de módulos también deniega cuando
una respuesta negativa incluye un listado de módulos. Esto cierra rutas de autorización por datos
obsoletos/denegados dentro del alcance ejecutado.

**Límites:** no se probaron HTTP real, datos de producción, navegador, provisioning, DB de proyección
`external_id` ni todos los call sites. El resolvedor de IDs local se simuló al probar adaptadores.
Los módulos legacy sin mapping pueden dejar de aparecer; la denegación se conserva. SSOClient no
sustituye los grants de estas APIs. No se declara compatibilidad global de los consumidores.

## G. Functional ALLOW Coverage

[authorization-delta.csv](authorization-delta.csv) conserva el ledger inicial por ruta y añade evidencia
P0R por rama. No convierte metadata/HEAD/format aliases en ALLOW por haber probado un dispatch directo.
[functional-coverage.csv](functional-coverage.csv) resume las nuevas ramas y sus límites.

| Flujo | Evidencia funcional nueva | Límite |
|---|---|---|
| Cambio de plan | UUID real, plan activo, plan/amount cambiados, otro objeto intacto; plan inexistente DENY | Sin ownership compartido, pricing/E/F/G ni SQL |
| Activar/cancelar suscripción | Handlers y métodos reales cambian estado y fechas | Save simulado; no ensayo comercial global |
| Marcar factura pagada | Estado, referencia/paid_at y activación real del modelo Subscription | Save simulado; no ledger/Hacienda/confirmación financiera |
| Reducir entitlement | PATCH real deshabilita y vacía scopes; auditoría before/after real | Persistencia simulada; no trial nuevo ni scope ampliado |
| Membresía | PATCH real desactiva; reparenting ajeno DENY | Trigger SQL y carreras no ejecutados |
| Usuario | Deshabilitar otro usuario, autodeshabilitación DENY; contraseña validada/hasheada y auditoría | Access local residual; triggers B pendientes |
| Invitación | Preview y consumo/registro real, membresía y JWT firmado; revocación entre validación y consumo DENY | Fence/DB simulados |
| Organización | Suspensión idempotente y un evento; otro tenant intacto | Evento/outbox persistente no verificado |
| Servicio | Siete handlers con ambos adaptadores y clave autenticada | HTTP/ORM simulados |
| Backoffice/settings | Se repiten ramas anteriores y se agrega DENY por permiso ausente | Emisión/batches/exports/scheduler completos pendientes |

Se mantienen pendientes create/trial de suscripciones, ownership compartido, cuotas, transiciones
comerciales complejas y varias ramas de facturación/entitlements. No se ampliaron permisos para lograr ALLOW.

## H. Adversarial DENY Results

Casos ejecutados: anónimo/técnico/inactivo, claims CENTRAL en control plane humano, IDs/UUID ajenos,
campos user_id/tenant_id/current_token_jti en revocación central, grants desconocidos/incompletos,
credencial rotada/revoked_at, firma manipulada, refresh ajeno, access como refresh, scopes de otro
producto, wildcard, estado de serializer inválido, falta de suscripción para activar un producto con
billing, auto-desactivación, reparenting y falta de permisos. Las ramas que deniegan antes del handler
no se cuentan como evidencia de efectos de negocio.

[reproduction-corrected.log](reproduction-corrected.log): **7 métodos FAIL, 21 fallos incluyendo subtests,
0 ERROR sobre el código inicial**; esos siete pasan después. Reproduce grants, filtrado de módulos,
autoridad retirada del invitador, logout repetido y autorización de clientes por caché/respuesta negativa.
La primera reproducción tenía fixtures incompletas y se conserva en [reproduction.log](reproduction.log);
no se cuenta como reproducción limpia. `p0r.log` y `p0r-sessions.log` son las corridas finales nuevas.

## I. Invitation Lifecycle

La autoridad se revalida al mostrar y al consumir: invitador deshabilitado/eliminado, pérdida de
membresía, cambio de rol global o de membresía, tenant suspendido, invitador cambiado de tenant,
invitación cancelada/expirada, correo distinto, rol global no permitido, pérdida de staff/permiso de
plataforma. El invitado no puede aportar rol, organización ni is_staff.

Las pruebas adversariales validan primero un formulario válido, retiran autoridad y luego ejecutan
`serializer.save()` real: ninguna crea usuario/membresía ni marca aceptación. Se prueba registro
válido por dispatch con JWT real, replay y fence deshabilitado. El orden fence→invitación permite
coordinarse con los triggers B existentes, pero su garantía SQL real permanece pendiente.

La nueva política exige autoridad **vigente** al consumo. No se certifica continuidad histórica
si la autoridad se revoca y luego se restablece antes de consumir; no se inventó una política de
invalidación perpetua/generaciones de invitaciones. Registro sin invitación conserva su contrato.

## J. Historical Regression Results

Conteos por método; las cifras FAIL/ERROR de `unittest` pueden ser mayores por subtests.
Las suites originales están preservadas byte a byte. Se ejecutaron también sobre el snapshot inicial
para comparar sus identidades/resultados, no solo cantidades. [historical-reconciliation.json](historical-reconciliation.json).

| Suite | Métodos finales P / F / E | Comparación |
|---|---:|---|
| P0R nueva API/adaptadores | 34 / 0 / 0 | Nuevos |
| P0R nueva central RSA | 6 / 0 / 0 | Nuevos, sin recontar herencia B |
| API P0 anterior | 50 / 0 / 0 | Preservada |
| API/Admin/guardrail anteriores | 29 / 0 / 1 | Baseline 30 / 0 / 0; incompatibilidad de invitación explícita |
| AdminApps D | 57 / 0 / 0 | Incluye herencia B |
| AdminApps B | 43 / 0 / 0 | Preservada |
| REC-2FA-04 | 21 / 0 / 0 | Preservada |
| ISO D / sesión D / B | 361 / 36 / 35 PASS | Cero FAIL/ERROR |
| Med D / sesión D / B | 533 / 36 / 35 PASS | Cero FAIL/ERROR |
| AdminApps A original | 7 / 20 / 3 | Exactamente igual antes/después |
| AdminApps C/H original | 2 / 4 / 12 | Exactamente igual antes/después |
| ISO A original / C/H original | 9 / 0 / 11; 17 / 0 / 11 | Exactamente igual antes/después |
| Med A original / C/H original | 9 / 0 / 11; 17 / 0 / 11 | Exactamente igual antes/después |

Los **10 métodos Django Admin pasan**; también el guardrail de exposición de serializers.
La incompatibilidad nueva es
`UserOrganizationAuthorizationTests.test_registration_consumes_valid_invitation_with_expected_effects_offline`:
su fixture permite `invited_by=None`, no provee fence y falla en backend dummy al intentar resolverlo.
Es un **ERROR conservado**, no un PASS ni un skip. La expectativa anterior ya no representa el contrato
seguro de consumo; los nuevos tests prueban ALLOW con invitador/fence válidos y DENY sin autoridad.
No se debilitó el código ni se editó la suite para ocultar el resultado.

| Contabilidad de métodos | Cantidad |
|---|---:|
| Nuevos únicos | 40 |
| Heredados únicos ejecutados nuevamente | 891 |
| Orígenes de métodos únicos en selección final | 931 |
| Ejecuciones finales seleccionadas | 1.421 |
| PASS / FAIL / ERROR por ejecución | 1.337 / 24 / 60 |

`unique-methods.json` deduplica herencia por archivo/línea/método; los métodos parametrizados con
nombres concretos siguen separados. Las repeticiones de desarrollo, baseline y reproducciones no
inflan este total. No son 1.421 pruebas nuevas. Se conservan los logs de esas otras corridas en `/tmp`.

Django `check` con settings sintéticos/backend dummy: PASS; compilación en memoria y
`git diff --check`: PASS. Ruff, Flake8, Pylint y pytest no están instalados en los venv revisados;
linters: **NOT_EVIDENCED**. No se instalaron herramientas. Las suites se ejecutan con unittest.
Los logs reportan cero intentos de conexión DB/red. Algunos fixtures históricos fallan antes de
conectar al backend dummy; eso es un ERROR de fixture, no evidencia de SQL ejecutado.

## K. Acceptance Criteria

| Criterio | Estado | Alcance/evidencia |
|---|---|---|
| P0R-01 | PASS | Matriz local/central/consumidores y contratos identificados |
| P0R-02 | FAIL | Revocación central corregida; convergencia completa de JWT locales sigue sin implementar |
| P0R-03 | PASS_OFFLINE | Introspección/consumidores B/D rechazan prueba central revocada |
| P0R-04 | PASS_OFFLINE | Replay y generaciones centrales; no acredita un lifecycle local equivalente |
| P0R-05 | PASS_OFFLINE | Hash real y credential_id autenticado con valores sintéticos; sin provisión real |
| P0R-06 | PASS_OFFLINE | Tenant/producto exactos, ambos productos y salida de módulos |
| P0R-07 | PASS_OFFLINE | Ambos adaptadores/siete handlers ejecutados; E2E/proyección/provisión excluidos |
| P0R-08 | PASS_OFFLINE | Incremento de ramas ALLOW, no cobertura completa |
| P0R-09 | PASS_OFFLINE | DENY adversarial y ramas históricas vigentes |
| P0R-10 | PASS_OFFLINE | Gates existentes, 10 Django Admin PASS y efectos P0 probados |
| P0R-11 | PASS_OFFLINE | Autoridad vigente al consumo/preview; continuidad histórica y SQL pendientes |
| P0R-12 | PASS_OFFLINE | MFA/B/D verdes; A/C/H originales iguales al baseline |
| P0R-13 | PASS | Suites históricas intactas; ERROR nuevo no ocultado |
| P0R-14 | PASS | HEAD/índices intactos; delta aislado y hashes |
| P0R-15 | PASS | Dependencias clasificadas; PostgreSQL/E2E siguen NOT_EVIDENCED |
| P0R-16 | PASS | Holds y adjudicaciones conservados; sin habilitación comercial |

## L. Remaining Local Gaps

1. **P0 — JWT/cookie local:** definir familia/session binding, conservar sesión actual de manera
   verificable y consultar revocación en access/refresh y autenticación de cookie. El endpoint de
   registro no proporciona esa garantía. Requiere contrato explícito de logout/cambio de contraseña
   y tratamiento de tokens anteriores; no modificar settings activos para simular cierre.
2. **P0 — cobertura funcional:** billing completo, create/trial, cuotas, ownership compartido,
   condiciones de estados y referencias de las ramas no ejecutadas continúan abiertos. Los tests
   de mark_paid prueban su rama pendiente, no adjudican transiciones cancelled/refunded ni ledger.
3. **HIGH — invitación:** queda la incompatibilidad histórica y falta la decisión de continuidad
   de autoridad revocada→restaurada. El consumo depende de fence/triggers B disponibles.
4. **HIGH — módulos legacy:** sin mapping comercial a producto se omiten de la respuesta; no
   existe fallback para recuperar el acceso anterior.
5. **Fuera del delta:** revisión completa de validate_credentials, ingestas AI/landing/demo,
   segregación CLI de claves y todos los call sites de clientes. No se certifican por estas pruebas.

## M. External Dependencies

- **BLOCKED_BY_EXTERNAL_DEPENDENCY:** laboratorio PostgreSQL autorizado y aislado para probar locks,
  triggers, rollback, outbox, RLS donde corresponda, revocación durable y carreras de consumo/rotación.
  Ninguna migración se aplicó y no se accedió a bases compartidas.
- **BLOCKED_BY_EXTERNAL_DEPENDENCY:** provisión de grants para credential_id reales, tenants centrales,
  producto correcto y permisos/membresías humanos. La plantilla exacta está en CONTRACT.md; sin secretos.
- **NOT_EVIDENCED:** HTTP/navegador E2E, revocación tras reinicio, instalación de triggers y proyección
  local external_id. No hubo servicios, workers ni jobs externos iniciados.
- **BLOCKED_BY_EXTERNAL_DEPENDENCY:** adjudicaciones de trials/ownership compartido/cuotas/mapping y E/F/G.

Se preservan expresamente **S3-IMP-01**, **S3_DECISION_02A_NOT_CLOSED**,
**PHASE31_5 = EXECUTION_HELD**, **REC-2FA-04**, **REC-SSO-02**, **REC-SSO-03A**,
**REC-SSO-03B-CH** y **DECISION_B_LOCAL_CODE_IMPLEMENTED_AND_OFFLINE_VERIFIED**.
Ninguna prueba de este slice sustituye o altera esas adjudicaciones.

## N. Next Engineering Slice

Prioridad: adjudicar el contrato de revocación de JWT/cookies humanos locales y construir su
binding durable sin mezclarlo con SSOSession. Después, probar B/invitaciones en PostgreSQL aislado
con autorización específica, provisionar grants por credential_id y verificar adaptadores con datos
reales controlados. Completar las ramas P0 del ledger sin liberar trials, cuotas ni E/F/G.

Reproducción local (sin settings activos, DB o red):

```sh
cd /home/felipe/proyectos/adminapps
backend/.venv/bin/python -B backend/scripts/rec_sso_03d_api_p0_offline.py apps.api.test_p0r
backend/.venv/bin/python -B backend/scripts/rec_sso_03d_p0r_sessions_offline.py
backend/.venv/bin/python -B backend/scripts/rec_sso_03d_api_p0_offline.py
backend/.venv/bin/python -B backend/scripts/rec_sso_03d_api_p0_offline.py --check
```

Los archivos `*-runs.json` registran los comandos de todas las suites y sus exit codes; los logs
A/C/H y el test histórico incompatible deben seguir informando sus fallos, no se suprimen.
