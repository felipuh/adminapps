# ADMINAPPS — S3-IMP-01 Contract Freeze & Human Decision Gate

Preparado el **2026-10-12, America/Costa_Rica**. Único documento nuevo de esta tarea.
**Propuesta para decisión; no aprobación, implementación ni autorización de ejecución.**
Registro limitado a **AJ-G01, AJ-C01, AJ-C02, F-C18, NUM-C01 y NUM-C02**.

## A. Executive Verdict

**S3-IMP-01 = BLOCKED_PENDING_AUTHORITY.** Se entrega un contrato candidato C-B
preciso, con conjunto de claims, esquema material, comparaciones, errores,
compatibilidad, pruebas y seis decisiones listas para selección humana. Hay tres
cifras de capacidad material sin evidencia suficiente: longitud de request_class,
longitud de evidence_id y cantidad de evidence_ids. Se propone una medición
offline delimitada en D.4, seguida de ratificación de sus valores; no se inventan
defaults. El freeze es documental y condicional, no un perfil ya vigente.

Las selecciones técnicas recomendadas son: preservar D02 LOGIN/Python; adoptar
C-B sin cambiar M(C); ratificar **18 claims**; exigir assertion completo V1.1 y
contexto esperado confiable; conservar SHA-256/material e identidad idempotente;
usar reloj UTC sin skew y máximo sintético de 60 segundos. Cada selección sigue
**PENDING_HUMAN_APPROVAL**. Aprobaciones nuevas registradas: **0**.

La inspección encontró dos efectos de compatibilidad concretos: el assertion
abreviado de los tests históricos no cumple V1.1 §4; algunos negativos históricos
esperan error de firma aunque su UUID ya sería inválido bajo el nuevo esquema.
Ningún test, resultado, contrato o fixture histórico se modifica para ocultarlo.

Se mantienen **S3_DECISION_02A_NOT_CLOSED**, **PHASE31_5 = EXECUTION_HELD**,
AJ-G01/C01/C02 pendientes y A02 `APPROVAL_PENDING`. No se reabren decisiones
PG/IPC/host ajenas a IMP-01. No hay código implementado ni pruebas de producto
ejecutadas en esta tarea.

## B. Contract Authority

### B.1 Fuentes y hashes de los bytes inspeccionados

Los IDs de esta tabla se usan en cada decisión. SHA-256 identifica bytes, no
autentica persona, firma, mandato ni ejecución. Los enlaces ISO Smart son de
solo lectura. Los cinco documentos del 2026-10-09 se reutilizan sin sustituirlos.

| ID | Fuente | SHA-256 |
| --- | --- | --- |
| HAG | [ADMINAPPS_AI_FINANCIAL_S3_HUMAN_ARCHITECTURE_ADJUDICATION_GATE_2026-10-12.md](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_ARCHITECTURE_ADJUDICATION_GATE_2026-10-12.md) | `0eff5f24accc9696eafb13c14f46038dc1fd50ed78e0c54c894f278c9100fef3` |
| REC | [ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md) | `926339d1ef8da26808a71f802043bcef3e35c62fadd49e70c74935bf391d307d` |
| ADR | [ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md) | `181b20e5f1c9e22e6b0480dc513604a25856909e8c49b406199916d9b4528ea2` |
| MAT | [ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md) | `c56d6ee9f15022839cea220a748de8e357424ec46d5cdf88add0dddae617e855` |
| PLAN | [ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md) | `a58fb7fd87032148a319d8442ec7708d2f8b1804d1b0f50256d7e48382a53abd` |
| GATES | [ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md) | `259a49d32aa206373891c4079f0ad35284da95602b703052804747fb77f343cf` |
| ADJ | [ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_2026-10-09.md) | `6d16f47e4d2ed6a742294a8ccd4c65399ddbb3f0271b22aab081b96a143a571a` |
| EVID | [ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json) | `57e8a44b89bc1af0598c6fc1f9691a461deaf6eb227ff413490da5e093946ec4` |
| OFF | [ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json](ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json) | `4bfdd21a0f1c677f3ac3f1ccb81cb6fb8731d73c78b7c11d959638aae2058e33` |
| D02 | [ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) | `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3` |
| A02 | [ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md) | `e03022a6ca4da9eeb9022b50972d30ff6628fa5a5ab9614ba3e21d6a5af9ef79` |
| ER | [ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md) | `da5d01ba8f0e12c66ed068c868568bc4fa208871d478a017453562290e2eea2b` |
| V11 | [ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) | `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f` |
| A01 | [ADMINAPPS_AI_FINANCIAL_AUTHORITY_AMENDMENT_01_DECISION_RECORD_2026-10-08.md](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_AMENDMENT_01_DECISION_RECORD_2026-10-08.md) | `677cb7006c04ce35b6127e589fb46b26bb44aae491509c4fe2b0a39fb0eeacf8` |
| CAP | [capabilities.py](../../backend/apps/financial/capabilities.py) | `b389eb73799eb13ea8af0285dbf4d6f20a3b917fe58d7707da96fadfc24f44dd` |
| EXE | [executor.py](../../backend/apps/financial/executor.py) | `8b39ada47540612f5f5bcf8361bff7b6154847e2f62d897f29a813721eaf7e46` |
| ISS | [issuer.py](../../backend/apps/financial/issuer.py) | `9d8c3535500cbeec299a2e7df2e6ecb3c69383e8e22a9accfa50b37ead785859` |
| SVC | [services.py](../../backend/apps/financial/services.py) | `1a0b8491900b041ac9f088ffbd275d8b19212e1e960ce8c7343395ffb96d11d8` |
| AUTH | [authorization.py](../../backend/apps/financial/authorization.py) | `53a314f4553842b919013e90580c0e499c010cffd91aa074ea2608e659bf13e5` |
| MODELS | [models.py](../../backend/apps/financial/models.py) | `898e485465ee836ccef735e5310d56c63eaf8ba1fbe3a26ce3ae576a9179a876` |
| TESTS | [tests.py](../../backend/apps/financial/tests.py) | `dcfb23119739e851b306d790828b28cd7c3069e62fe5cc39ef9ea5ccb292e585` |
| M0007 | [0007_decision_02_a_executor_boundary.py](../../backend/apps/financial/migrations/0007_decision_02_a_executor_boundary.py) | `b098ed9d9e79dee94c5fce2d8542c93316a2d09dbec4065d1b4f79fa4602057f` |
| M0005 | [0005_s3_runtime_admission_boundary.py](../../backend/apps/financial/migrations/0005_s3_runtime_admission_boundary.py) | `d2c7dfc9ddd944bda90f7b5dce17b48646928e0ee51f9727f0f98152d476a384` |
| CRTEST | [test_s3_capability_offline.py](../../backend/scripts/tests/test_s3_capability_offline.py) | `80569387baf0e1faa8bc3948f1f84c35336bdbdd5c42e1bbcec6841c00994e74` |
| REQ | [requirements.txt](../../backend/requirements.txt) | `cf804dcb0092c3daaa97831806e1eefa2c91edcabdb1a7e4f9ca21dea7bfb29f` |
| TP | [models.py](../../../isosmart/backend/foundation/models.py) | `4fa28f1cbff3aa132dcb41d867253903cf36f319d3b170b97cd0786cdf62d09d` |

Comprobaciones documentales: **46/46** filas con enlace/hash del registro REC
coinciden; EVID: **24/24 + 7/7 + 44/44 + 1/1**; OFF: **37/37 + 4/4 + 6/6**.
Las 123 entradas de EVID/OFF se superponen; no son 123 fuentes independientes.
CAP `_REQUIRED` y el dict de `mint_capability`, extraídos por AST sin importar
producto, contienen exactamente las mismas **18 claves distintas**.

### B.2 Aprobación registrada versus autoridad acreditada

| Fuente / cláusulas | Qué consta | Qué NO consta o NO concede |
| --- | --- | --- |
| V11 §§1–12 y A01 | Cabecera de propuesta; A01 cambia la propuesta, sin permiso runtime. A02 §1 registra posteriormente `FINANCIAL_CONTRACT_V1_1 = HUMAN_APPROVED`. Se preserva esa adopción registrada, incluida identidad, TLS/credencial dedicada, assertion, material e idempotencia. | No se localizó acta primaria que vincule firmante competente, mandato, hash, alcance, reservas y fecha efectiva. No atribuir aprobación independiente a cada cláusula por una etiqueta global. Tarifas, input bounds, operación e implementación conservan gates propios. |
| D02, Decision | `SECURITY_DECISION_02_A = HUMAN_APPROVED`: Ed25519, dominio v1, bindings enumerados, JSON sorted/compact ASCII, intervalo sintético ≤60 s, issuer autentica credencial/registro/scope/grant, executor verifica firma y recomputa hash. | No prescribe inequívocamente rechazo de todo wire equivalente, tipos/rangos exhaustivos ni nuevos permisos. ER relata autorización del 2026-10-09; falta cadena primaria verificable de identidad/mandato para los actos nuevos. |
| D02, Database boundary / Threat boundary | Executor LOGIN/NOINHERIT/NOSUPERUSER/NOBYPASSRLS; owner admission NOLOGIN separado; ACL mínima, grant vivo, ledger, FORCE RLS e inmutabilidad; compromiso de issuer/executor/control plane fuera de protección declarada. | No significa verifier Ed25519 en DB, aislamiento OS demostrado ni aprobación permanente de slices/labs. Este contrato no subsana transacciones, revocación ni ledger. |
| A02 §§6/10 | Propuesta pendiente de verifier DB, executor NOLOGIN, claims diferentes, HSM/servicio de firma y validación ampliada issuer. | Ninguna cláusula nueva de A02 queda aprobada por D02, propiedad del repo, autoría de código o identidad del operador. |
| HAG, REC, ADR, MAT, PLAN, GATES, ADJ | Recomendaciones, dependencias, resultados históricos y campos pendientes. | No actas humanas nuevas. Las menciones a «19 claims» son discrepancia documental F-C18, no un claim adicional. |

**Recomendación AJ-G01:** reconocer la adopción registrada de V11, ratificar sus
bytes y reservas mediante autoridad acreditada, y preservar D02 como decisión
específica acotada para S3. A02 permanece pendiente. No formular una precedencia
general fuera de esta frontera; no borrar cabeceras ni aprobar A02 indirectamente.

**Acto concreto para cerrar AJ-G01:** F (dueño contractual financiero), S
(seguridad/protocolo) y D (DBA/responsable de la frontera de datos), con mandato
acreditado por la instancia de gobierno competente, aportan acta original
autenticada o firman una ratificación nueva que identifica V11/D02/A02 por sus
SHA-256, adopción, reservas, alcance LOGIN/Python, A02 pendiente, fecha/zona y
exclusión de permisos de implementación/runtime. Custodio identifica procedencia
y mecanismo verificable de firma/aceptación. No basta escribir un nombre/cargo o
«aprobado» en el repositorio. Ausencia localizada no demuestra inexistencia del
acta original. Una ratificación nueva no inventa una fecha de aprobación pasada.

**Decisiones nuevas necesarias para C-B:** rechazo de duplicados y wires
equivalentes; tipos/formatos/límites exactos; precedencia de errores; contexto
esperado obligatorio; assertion completo y consecuencias de compatibilidad;
ratificación F-C18; NUM-C01/02. Se proponen como endurecimiento nuevo de aceptación
v1, no reclasificación automática de la historia ni modificación de M(C).

## C. Exact 18-Claim Contract

En esta sección «propuesto» requiere AJ-C01/F-C18/NUM-C. JSON string se convierte
en `str` exacto y JSON integer en `int` exacto: no bool, float, decimal, null,
array, objeto ni coerción `str()`/`int()` de entrada no confiable. Solo el objeto
raíz con estas claves; ninguna opcional o adicional.

Convenciones propuestas:

- **UUID36:** string ASCII lowercase `8-4-4-4-12` hexadecimal, longitud 36;
  parse UUID y roundtrip idéntico. Sin braces, URN, mayúsculas, espacios o forma
  compacta. No imponer versión/variant ni rechazar nil por formato: los UUID
  sintéticos existentes `UUID(int=n)` no son necesariamente UUIDv4. Existencia y
  autoridad son comprobaciones distintas. El mint sí genera capability_id uuid4.
- **ID120:** string ASCII que satisface completamente
  `[A-Za-z0-9][A-Za-z0-9._:/-]*`, entre 1 y 120 bytes/caracteres; comparación exacta
  sensible a mayúsculas, sin trim, casefold, percent-decoding o normalización.
  La longitud 120 deriva de MODELS ledger; la gramática es selección nueva.
- **UTC20:** string de 20 bytes `YYYY-MM-DDTHH:MM:SSZ`, año 0001–9999, calendario
  válido, hora 00–23 y minuto/segundo 00–59. Sin fracción, offset, espacio,
  fecha compacta, leap second, epoch o zona local. CAP `_iso` emite UTC sin
  microsegundos; el rechazo de variantes hoy parseables es nuevo.

| # | Claim | Tipo y valor/perfil propuesto | Hecho comprobado / selección nueva |
| --- | --- | --- | --- |
| 1 | alg | string exacto `Ed25519` (7 bytes) | Constante CAP/D02; tipo estricto nuevo. |
| 2 | aud | string exacto `adminapps-financial-admission` (29) | CAP/D02. |
| 3 | capability_id | string UUID36 | CAP genera uuid4; formato exigido nuevo. No sustituye identidad idempotente. |
| 4 | environment | string, uno de `controlled_test`, `staging`, `production`, además igualdad al contexto local | Enumeración MODELS/AUTH/V11; enforcement pre-DB nuevo. Para este slice solo fixtures controlled_test; enumerar otros valores no autoriza usarlos. |
| 5 | exp | string UTC20 | CAP/D02, política D.3. |
| 6 | grant_id | string UUID36 | CAP hace str; SQL UUID; enforcement nuevo. |
| 7 | grant_version | integer exacto, 1…2147483647 | MODELS PositiveIntegerField y EXE/M0007 integer; CAP hoy coacciona int. Rango pre-DB nuevo. |
| 8 | iat | string UTC20 | CAP/D02, política D.3. |
| 9 | iss | string ID120; igual al issuer configurado localmente | CAP compara issuer; longitud MODELS 120; gramática nueva. |
| 10 | jti | string UUID36; igual a invocation_id esperado | CAP usa str(invocation_id), EXE/M0007 UUID; sin claim invocation_id adicional. |
| 11 | kid | string ID120; miembro activo del keyring local de ese issuer | CAP selecciona Ed25519PublicKey; formato/lifecycle local exigidos nuevos, sin revocación remota implementada. |
| 12 | material_request_hash | string exactamente 64 hex lowercase `[0-9a-f]{64}` | SVC SHA-256 hexdigest; MODELS permite 128 pero eso no cambia SHA-256; formato pre-DB nuevo. |
| 13 | nbf | string UTC20 | CAP lo emite igual a iat; D.3 conserva posibilidad de nbf posterior dentro del intervalo. |
| 14 | operation | string exacto `admit_reserve` (13); igual a operación solicitada/autorizada | CAP emite, M0007 compara; verifier actual no exige este valor por sí solo. |
| 15 | organization_id | string UUID36; igualdad E.2 | CAP str, SQL UUID, V11 tenant canónico. |
| 16 | producer_registration_id | string UUID36; igualdad al productor autenticado del contexto | ISS deriva del principal AUTH; no tomar de body del productor como prueba. |
| 17 | product_id | string UUID36; igualdad al material/contexto | CAP str, SQL UUID; comparación local explícita nueva. |
| 18 | version | integer exacto `1` | CAP constante 1; comparación actual permite igualdad Python bool/float, tipo estricto nuevo. |

No se añaden correlation_id, invocation_id, schema_version, datos de proyección,
perfil C-B ni autenticación de contexto al conjunto firmado. `correlation_id`
permanece diagnóstico fuera de firma y de identidad idempotente; su UUID se
valida antes de DB para impedir errores de casting, sin convertirlo en autoridad.

## D. Proposed C-B Profile

### D.1 Bytes, parser y firma

Definición que conserva CAP sin sustituirlo por JWT, JWS o JCS:

```text
J(C) = json.dumps(C, sort_keys=True, separators=(',', ':'),
                  ensure_ascii=True, allow_nan=False).encode('utf-8')
M(C) = b'adminapps.financial.admission-capability.v1\n' + J(C)
S = Ed25519.sign(private_key, M(C))
T = base64url_no_padding(J(C)) + '.' + base64url_no_padding(S)
```

El prefijo es de **44 bytes**, incluido un LF final `0a`, sin CR, BOM ni otro
separador. Se firma M(C), no T ni el base64 ni un hash sustituto. Ed25519 simple,
sin cambiar a Ed25519ph/ctx ni implementar una primitiva propia. El payload
del mint usa otro dumps sin `allow_nan=False`; como la firma ya lo exige y el
perfil excluye floats, ambos producen los mismos bytes para entradas válidas.

Orden obligatorio de la frontera futura, antes de cualquier objeto/conexión DB:

1. Validar configuración pública local y existencia/procedencia del contexto
   confiable; entrada token `str` exacto ASCII. Aplicar longitud global antes de
   split/decoding; exactamente un punto y dos segmentos no vacíos.
2. Cada segmento solo `[A-Za-z0-9_-]+`, sin `=`, `+`, `/`, whitespace, controles
   o no ASCII. Longitud módulo 4 distinta de 1; padding solo interno al decoder.
   Decode estricto y re-encode sin padding exactamente igual al original para
   rechazar pad bits no nulos/representaciones alternativas. Payload ≤915 bytes;
   firma exactamente 64 bytes, segmento firma exactamente 86 caracteres.
3. Payload UTF-8 estricto, sin BOM ni bytes inválidos, una sola raíz JSON objeto,
   sin texto extra. Control de profundidad/longitudes antes de construcción
   recursiva costosa (scanner consciente de strings/escapes o parser acotado;
   no contar braces dentro de strings). Prohibir constantes NaN/Infinity y
   -Infinity, claves duplicadas **decodificadas** en todo objeto, idénticas o
   conflictivas, en cualquier posición. No escoger primero/último. Detectar
   duplicados antes de formar dict. Prohibir floats/exponentes y strings con
   surrogate aislado, controles o gramática inválida conforme al esquema.
4. Exactamente las 18 claves, tipos y perfiles no temporales C; formato y ventana
   UTC se adjudican después de la firma según D.2. El wire decodificado
   debe ser byte a byte J(C): sin whitespace, orden diferente, escape equivalente,
   slash escapado, `-0` u otra forma numérica. JSON válido no equivale a C-B válido.
5. Comprobar constantes version/alg/aud/iss; resolver kid únicamente en el
   keyring público local del issuer, nunca URL/ruta/clave suministrada en token.
   Debe resultar Ed25519PublicKey, cargada de material raw de exactamente 32
   bytes si se usa ese formato. Verificar S sobre M(C) con la biblioteca
   `cryptography`; toda InvalidSignature deniega. No usar claims para autorizar
   hasta completar firma, tiempo y binding. Tipado previo no autentica claims.
6. Ventana D.3, contexto E.2, material E.1 y recomputación de hash; también
   correlation_id válido. Solo entonces se permite alcanzar el límite de DB.
   El material se valida y se congela/copia de forma acotada: mismo snapshot
   validado, hasheado y enviado a SQL; no relectura de contenedores mutables del
   caller que permita TOCTOU. No se implementa aquí transporte.

Longitudes de firma y clave pública raw (64 y 32 bytes), y `verify` que falla
con InvalidSignature, están documentadas por
[cryptography](https://cryptography.io/en/45.0.4/hazmat/primitives/asymmetric/ed25519/).
REQ fija `cryptography==46.0.3` en fuente; no se certifica instalación/runtime.
La biblioteca estándar admite duplicados con último valor y no finitos salvo
controles explícitos: [Python JSON](https://docs.python.org/3.11/library/json.html).
Las cifras máximas integer/bigint proceden de los tipos SQL usados en fuente,
no de una política de presupuesto: [PostgreSQL numeric types](https://www.postgresql.org/docs/13/datatype-numeric.html).
Estas referencias informativas no son autoridad contractual ni fijan una versión
de despliegue; se mantienen los bytes CAP como definición del formato.

### D.2 Errores y denegación sin DB

Todos los negativos pre-DB tienen resultado denegado tipado y no retry automático.
Propuesta: frontera EXE normaliza a `CapabilityDenied(code)`, subclase de
PermissionError; SVC histórico conserva su clase existente y el adaptador del
executor la traduce. No cambios globales de errores S1/S2. Código público seguro
sin token, material, firma, credencial, stack ni identidad ajena en logs.

| Etapa / condición | Código propuesto |
| --- | --- |
| Token no string/ASCII, envelope/base64/UTF-8/JSON inválidos, duplicado, wire alternativo o exceso de tamaño/profundidad | CAPABILITY_MALFORMED |
| Conjunto/tipos inválidos; UUID, ID, hash o rango de entero inválido | CAPABILITY_CLAIMS_INVALID |
| alg string bien formado pero diferente | CAPABILITY_ALGORITHM_DENIED |
| version int bien tipado pero diferente de 1 | CAPABILITY_VERSION_DENIED |
| aud/iss bien tipados pero no esperados | CAPABILITY_AUDIENCE_DENIED (preserva código histórico) |
| kid válido pero desconocido/retirado o clave de tipo incorrecto | CAPABILITY_KEY_UNKNOWN |
| Firma de 64 bytes inválida | CAPABILITY_SIGNATURE_INVALID |
| UTC20 inválido, intervalo inválido o TTL fuera de rango | CAPABILITY_TIME_INVALID |
| now anterior a nbf o igual/posterior a exp | CAPABILITY_EXPIRED (preserva código histórico para ambas fronteras) |
| Contexto ausente/no confiable, mismatch identidad/entorno/operación | CAPABILITY_BINDING_DENIED |
| Material fuera de esquema/tipos/límites, assertion incompleto, correlation_id inválido | MATERIAL_REQUEST_INVALID |
| Assertion tenant bien formado pero distinto de claim/contexto | CAPABILITY_BINDING_DENIED |
| Material válido con hash distinto del firmado | CAPABILITY_MATERIAL_DENIED |
| Configuración/reloj/biblioteca no disponible o fallo interno que impida verificar | CAPABILITY_UNAVAILABLE (nuevo; fallo seguro, cero DB) |

Precedencia: disponibilidad de configuración/contexto → envelope/recursos →
JSON/duplicados → conjunto/tipos/formatos no temporales → wire →
alg/version/aud/iss/kid → firma → tiempos → comparaciones de contexto → esquema
material/correlation → igualdad assertion → hash. Un claim UTC se tipa como string
antes de firma; su formato/calendario se adjudica en la etapa temporal. Los
errores de constantes se usan solo si su tipo es correcto. Error de firma con
longitud distinta de 64 es malformed, no InvalidSignature. Una entrada con varios
defectos recibe el primer error de esta secuencia; los tests de una propiedad
aislarán el defecto. Los límites pueden anticipar otros errores.

No escapar con AttributeError, TypeError, ValueError, OverflowError,
UnicodeError, JSONDecodeError, RecursionError u otro error de validación; traducir
errores previstos. Un fallo interno no previsto debe abortar sin DB y con fallo
seguro, nunca continuar ni tratarlo como token válido. Límites previos evitan
depender de capturar MemoryError; no se promete supervivencia a agotamiento OS.
Ningún audit pre-DB usa PostgreSQL. No registrar alias, consultar `connections`,
abrir cursor, iniciar atomic, hacer ORM, reintentar SQL ni cerrar conexión como
cleanup de un rechazo que nunca debía obtenerla.

### D.3 NUM-C02: tiempo recomendado

Conservar **skew = 0 segundos**, reloj UTC consciente de zona tomado localmente
una vez por verificación, sin fecha del caller ni reloj remoto. Fixtures inyectan
un reloj sintético explícito. No truncar el now de verificación: conservar
microsegundos. Tiempo válido si y solo si:

```text
iat <= nbf < exp
0 < (exp - iat).total_seconds() <= 60
nbf <= now < exp
```

`iat <= nbf` y `now >= nbf` implican iat no futuro. CAP emite iat=nbf y segundos
enteros; recomendar lifetime de emisión entero exacto 1…60 (bool prohibido),
manteniendo default sintético 60. Reloj ausente/naive/no utilizable: unavailable.
No gracia antes de nbf o después de exp. No exigir nbf=iat a tokens válidos ya
firmados: conservar scheduled nbf dentro del intervalo. El intervalo vacío que
el código compara con `<=` no debe aceptarse, aunque nunca tendría un now válido.

Justificación: coincide con emisor normal y ventana actual sin fabricar datos de
deriva. Riesgo residual aceptable solo por humano: desfase de relojes causa
denegaciones; no hay garantía de reloj seguro ni expiración al commit SQL. La DB
actual no recibe iat/nbf/exp. En el futuro revalidar inmediatamente antes de DB;
no afirmar que eso vuelve atómica la expiración con commit o que cierra IMP-04.
Cambiar skew exige nueva selección NUM-C02 y evidencia offline de relojes, nunca
ampliar unilateralmente los 60 segundos sintéticos ni habilitar producción.

Fronteras: now=nbf acepta; nbf−1 microsegundo deniega; exp−1 microsegundo acepta;
now=exp deniega; lifetime 1/60 acepta, 0/61 deniega; nbf<iat, nbf>=exp y fecha
imposible deniegan. No uso de wall-clock real al repetir vectores de 2026-10-09.

### D.4 NUM-C01: límites, fundamento, compatibilidad y fronteras

Todos son **propuestos** aunque su fundamento sea fuente. Un máximo de tipo no
es un límite financiero autorizado. Para una string ASCII bytes=caracteres;
longitud JSON incluye comillas/escapes/separadores; profundidad cuenta solo
contenedores con raíz=1, no aumenta por escalares.

| Parámetro | Opción concreta recomendada / fundamento | Compatibilidad y prueba de frontera |
| --- | --- | --- |
| UUID / timestamps / hash | UUID36, UTC20, SHA-256 hex64; C y fuente CAP/SVC/EXE | Mantiene representaciones normales; 35/37, 19/21 y 63/65 bytes rechazan; uppercase UUID/hash y offset timestamp rechazan. UUID nil/canonical válido por forma, sin afirmar autoridad. |
| iss/kid | ID120; max_length=120 MODELS; gramática propuesta C | 1/120 acepta por forma; vacío/121/no ASCII/control rechaza. Clave o issuer no registrado deniega aunque cumpla forma. |
| grant_version | 1…2147483647, decimal canónico ≤10 dígitos | SQL integer; 0, negativo, 2147483648, true y 1.0 deniegan. No coacción histórica int. |
| version / schema_version | integer exacto 1 | CAP/default SVC; 0/2/bool/float/null rechazan; sin nuevo campo firmado. |
| environment / operación / constantes | Enumeraciones C, igualdad a contexto confiable; el entorno más largo mide 15 bytes | Controlado normal preservado; entorno/operación ajenos deniegan pre-DB. No permiso staging/production. |
| Profundidad capability / material | Máximo 1 / 2 contenedores; capability 18 miembros; material 9 y assertion 4 | Derivado de esquemas cerrados, no número de rendimiento inventado. Objeto/lista anidados extra en claim o assertion, o contenedor dentro evidence_ids, rechaza. Braces escapados en string no cambian profundidad. |
| Payload capability / token | J(C) ≤**915 bytes**; payload base64 ≤**1220**; firma 64 bytes/86 chars; T ≤**1307 bytes** | Cota derivada de todos los máximos C simultáneos, no tamaño operacional supuesto. Construcción stdlib documental contrastada. 915/1307 con issuer/key de 120 y grant de 10 dígitos acepta si autorizado; byte adicional deniega. |
| max_input_tokens / max_output_tokens | integer exacto 0…9223372036854775807, ≤19 dígitos | EXE usa bigint; SVC rechaza negativos/bool. 0 y máximo pasan forma; −1 y máximo+1 deniegan pre-DB. Política financiera puede negar cualquier positivo posteriormente. |
| tenant_projection_source_version | integer exacto 0…9223372036854775807 | TP usa BigIntegerField y constraint >=0: **0 es válido por forma**, no presumir mínimo 1 por ejemplo V11=42. Mínimo/máximo pasan; −1/overflow/bool deniegan. No valida frescura. |
| provider / model_identifier | Gramática ID de C, máximos **120 / 200** bytes ASCII | MODELS tarifas/política; gramática nueva. Vacío/max+1/control/no ASCII deniegan; 1/max pasan forma. Registro financiero decide compatibilidad efectiva después. |
| request_class | Misma gramática ID; longitud **1…L_R**, L_R pendiente de medición | No hay máximo en SVC/V11 ni registro cerrado de clases. Rechazar formatos ajenos es selección nueva. Probar 0, 1, L_R y L_R+1. No elegir 80/120/256 por costumbre. |
| cada evidence_id | String opaca con gramática ID; longitud **1…L_E**, L_E pendiente de medición | SVC usa strings ordenados, sin contrato UUID exclusivo. No imponer UUIDv4 ni transformar ID. Probar vacío/1/L_E/L_E+1, tipo numérico/objeto/null. |
| evidence_ids | list exacta de strings; **0…N_E**, N_E pendiente de medición | Mantener sorted lexicográfico y multiplicidad histórica; no deduplicar ni convertir ints a str. Las claves JSON duplicadas están prohibidas; referencias iguales en el array conservan multiplicidad/hash. Probar 0/N_E/N_E+1 y permutaciones. |
| Material serializado | Máximo derivado **B_M = 818 + L_R + (0 si N_E=0; si no N_E×(L_E+3)−1)** bytes | 818 incluye todos los campos fijos a máximos, versión proyección de 19 dígitos, clase vacía y lista vacía. Todo ASCII sin escapes bajo gramática. Fijar B_M tras firmar L_R/L_E/N_E; no otro default. Probar máximo y max+1 antes de hashing. |
| Entrada material de objeto Python | Validar conteos/tipos/longitudes antes de copiar/ordenar/dumps; limitar enteros por rango antes de serializar | No medir con un dumps ilimitado primero. Si futuros adaptadores aceptan raw JSON, límites de frame y bytes antes de parse pertenecen a IMP-05/NUM-I; aquí no se aprueba frame IPC. |

**Experimento offline propuesto, no ejecutado ni autorizado aquí:** producir un
corpus sintético versionado a partir de fixtures existentes y contratos de cada
consumidor declarado por F/S (no consultar DB, productores vivos ni credenciales).
Cada caso debe declarar sus máximos legítimos de clase, longitud de referencia y
cantidad de referencias. Medir bytes/longitudes/conteos y reportar máximos,
distribución, cobertura de consumidores, tiempo/memoria y versiones de entorno.
Los tres candidatos serán exactamente el máximo de los límites de dominio
declarados por esos consumidores; los samples solos dan un piso, no prueban una
cota. Ejercitar candidato−1/candidato/candidato+1 y combinaciones simultáneas;
F/S deben ratificar valores finitos y capacidad antes de G-IMP. Sin consumidor
que declare un techo, no aprobar una cota operacional por el máximo observado.

Los valores a ratificar son enteros exactos L_R>=1, L_E>=1 y N_E>=0, con B_M
derivado; incluso si N_E=0, documentar el alcance «sin evidencias declaradas» y
no inferir que cubrirá futuros consumidores. No se confunden esas tres cotas con
la selección de su método de obtención.

La siguiente selección NUM-C01 puede aprobar este método y los límites derivados
ya concretos; **eso no cierra NUM-C01** hasta insertar L_R/L_E/N_E y B_M en un
registro humano vinculado a esta versión/hash. No se autoriza silenciosamente
un experimento que escriba código ni se habilita IMP-01 por aprobar el método.
Si se autoriza después, su alcance es solo un medidor offline en copia aislada y
fixtures sintéticos, sin modificar implementación/tests históricos ni ejecutar
PG/IPC. No se crea un nuevo gate genérico: es la opción acotada de NUM-C01.

### D.5 Compatibilidad y versión

La etiqueta documental **C-B / v1** no se añade a los claims. Adoptar esta opción
mantiene version=1, dominio, M(C), algoritmo, cardinalidad y hash material. Es un
estrechamiento explícito de lo aceptado: se rechazan wires/tipos que el código
toleraba. No hay fallback al parser anterior ni negociación desde el token.
Consumidores fuera de inventario o necesidad de otro esquema exigen selección
de compatibilidad por F/S antes del patch, no coerción automática.

Cambio de claves, semántica firmada, dominio, serialización o hash exige nueva
versión/decisión explícita; no reutilizar v1 para un mensaje distinto. Rotación
de claves conserva mensaje pero requiere su política propia, fuera de IMP-01.
Los registros y hashes históricos siguen inmutables. Un material abreviado no
se «actualiza» agregando campos ni rehasheándolo bajo su invocation original.

## E. Tenant / Material Binding

### E.1 Esquema exacto propuesto del material

Objeto cerrado **de nueve campos**, distinto del objeto de 18 claims:
En las tablas de material, **ID** designa solo la gramática ASCII de ID120;
cada fila fija su propio máximo, incluido 200 para model_identifier.

| Campo | Tipo / perfil |
| --- | --- |
| schema_version | int exacto 1 |
| tenant_assertion | dict exacto cerrado con los cuatro campos de abajo |
| product_id | string UUID36 |
| provider | string ID, 1…120 |
| model_identifier | string ID, 1…200 |
| max_input_tokens | int exacto 0…9223372036854775807 |
| max_output_tokens | int exacto 0…9223372036854775807 |
| request_class | string ID, 1…L_R |
| evidence_ids | list de 0…N_E strings ID, cada una 1…L_E; ordenar lexicográficamente para hash, conservar repetidas |

`tenant_assertion`, exactamente:

| Campo | Tipo / perfil |
| --- | --- |
| adminapps_tenant_id | string UUID36 |
| tenant_projection_id | string UUID36 |
| tenant_projection_source_version | int exacto 0…9223372036854775807 |
| tenant_projection_source_event_id | string UUID36 no null |

Sin `source`, estados extra, dinero, precio, moneda, policy, tarifa, correlation,
invocation ni campos desconocidos en este objeto. Duplicados decodificados
prohibidos también en assertion cuando existe texto JSON. Un dict ya colapsado
no permite recuperar duplicados: el executor no puede certificar lo perdido.
El futuro punto de entrada deberá detectar duplicados antes de crear dict y
entregar un snapshot validado; IMP-01 ofrece la frontera pura con fixtures,
IMP-05 implementará transporte/adapter. No aceptar un flag del caller que diga
«ya validado» como sustituto del camino confiable.

Preservar exactamente:

```text
material.evidence_ids = sorted(evidence_ids)  # strings; conserva multiplicidad
J_material = JSON sorted / compact / ensure_ascii=True en UTF-8
material_request_hash = SHA256(J_material).hexdigest()  # lowercase, sin dominio
```

En perfil válido no hay floats/no finitos; imponer allow_nan=False en un futuro
validador no cambia esos bytes. No usar JCS, HMAC, sal, nuevo dominio, otro hash,
orden de recepción ni deduplicación. Adaptador Python confiable puede convertir
un objeto UUID a su string canónico antes de formar el material (como hace SVC);
no convierte strings inválidas ni números arbitrarios. `schema_version=1` y
`evidence_ids=None`/omitido conservan exclusivamente los defaults de la API
Python existente: normalizar a 1 y [] antes del objeto cerrado; en JSON material
los nueve campos son explícitos y null no sustituye lista. El hash legado acepta
más cosas; la aceptación estricta se añade a la ruta nueva sin reescribir historia.

### E.2 Contexto esperado y comparaciones

Contrato del contexto **local, fuera del token y del material**, propuesto para
la interfaz futura de EXE: seis campos obligatorios tipados, inmutables por
solicitud: `producer_registration_id`, `organization_id`, `product_id`,
`invocation_id` (UUID36), `environment` (enumeración) y `operation=admit_reserve`.
Issuer esperado y keyring público son configuración local confiable, no body.
No campos extra ni defaults tomados del propio token. Los valores deben llegar
desde un adaptador interno autorizado ligado al principal autenticado, tenant
server-side y solicitud original; en tests solo un doble sintético explícito.
Un DTO con esos seis valores no autentica por sí mismo su procedencia.

El constructor/entrada de EXE deberá exigir esa dependencia confiable, no un
parámetro opcional que en ausencia acepte cualquier tenant. Hoy tal adaptador no
existe: IMP-01 puede definir la interfaz y negar contexto ausente con dobles;
no puede declarar resuelta la autenticación IPC o integración ISO Smart. No
consultar DB para «conseguir contexto» antes de verificar. Si solo está disponible
el body o el token para fabricarlo, denegar por contexto no confiable.

| Comparación obligatoria | Quién puede comprobarla / condición |
| --- | --- |
| C.iss = issuer local; C.kid ∈ keyring autorizado de ese issuer; C.aud/alg/version exactos | Verifier offline. Keyring ausente/retirado deniega; mock no demuestra propagación de revocación operacional. |
| C.organization_id = assertion.adminapps_tenant_id = contexto.organization_id | Executor pre-DB sobre strings ya canónicas; no aceptar igualdad con dos valores elegidos por caller como autenticación. |
| C.product_id = material.product_id = contexto.product_id | EXE hoy usa C.product_id al construir hash. La interfaz futura usa el contexto/material original para detectar sustitución, no lo infiere únicamente de C. |
| C.producer_registration_id = contexto.producer_registration_id | EXE pre-DB comprueba consistencia; issuer obtiene principal real de AUTH, no del argumento producer del cliente. |
| C.environment = contexto.environment = entorno configurado/autorizado | EXE pre-DB; AUTH valida environment del registro. Configuración no se deriva de C. |
| C.operation = contexto.operation = operación solicitada por método `admit_reserve` | EXE pre-DB. No despachar otra operación a partir de un claim arbitrario. |
| C.jti = contexto.invocation_id | EXE pre-DB; preservar invocation original en retries/reconciliación. |
| SHA256(J_material) = C.material_request_hash | EXE ya recomputa; debe hacerlo tras esquema/binding y sobre snapshot exacto. Hash esperado adicional solo si proviene de contexto confiable, nunca reemplaza recomputación. |
| grant_id/grant_version y tupla productor/tenant/producto/entorno/operación | Issuer consulta grant activo; DB M0007 bloquea/revalida grant. EXE puede validar forma y firma, **no** garantizar vigencia de grant offline. No exigir conexión cero para denegación SQL de grant. |
| TenantProjection active/complete/in_sync, source/event presentes y reconciliación vigente | Productor confiable V11 y futura integración/issuer según fuente disponible. EXE solo comprueba estructura/hash; no conoce frescura ni existencia remota. Firma prueba afirmación del issuer, no verdad de la proyección. |
| Organización activa, producto/entitlement/política/tarifa/budget efectivos | Frontera financiera DB existente; no se sustituyen por igualdad, UUID o GUC. |

**Issuer actual:** AUTH valida hashed_v1, registro, lifecycle, ambiente, scope;
ISS busca grant activo y evento. Recibe `material_request_hash` y no recibe
assertion/material/contexto de ejecución completos. Puede firmar un hash que
no recomputó: no atribuirle verificación de proyección/material inexistente.
**Posterior a IMP-01:** adaptar issuer para recibir el material original,
validarlo, ligar el tenant server-side al principal autorizado y recomputar hash
antes de mint (IMP-05 y su permiso). Verificación de frescura/origen necesita
fuente y ruta autenticada propia; no se añade HSM ni se adopta A02 completa.

Identidad idempotente preservada:
`(producer_registration_id, organization_id, product_id, invocation_id=jti)`.
Mismo tuple/hash debe conservar la decisión original según la frontera DB;
distinto hash implica conflicto, nunca invocation nueva para escapar. Token
wire, firma, capability_id y correlation_id no reemplazan esa identidad. Nueva
emisión puede generar otro capability_id; no es permiso para otro efecto.
Un rechazo pre-DB no escribe ledger/audit/denial ni hace cleanup PostgreSQL.

### E.3 Inventario de consumidores y compatibilidad real

Inventario por búsqueda estática de símbolos en AdminApps; no prueba ausencia de
consumidores externos/desplegados. Antes de G-IMP, F/S deben declarar el alcance
de consumidores que aprueban. No se localizaron endpoints financieros S3 ni un
segundo parser de tokens en la cadena actual.

| Consumidor / fuente | Comportamiento y efecto propuesto |
| --- | --- |
| ISS → CAP.mint | Dict de 18 claims, str UUID e int(grant_version), iat=nbf, lifetime default 60. Tokens con inputs conformes conservan bytes. Recomputación issuer queda posterior. |
| CAP.verify → EXE | Devuelve un dict único; EXE no reparsa token y hoy no pasa expected. C-B endurece parser; contexto obligatorio es cambio de interfaz explícito. |
| EXE → SVC hash → M0007 → M0005 | Hash material y escalares SQL. DB no recibe token/firma/tiempos; no afirmar verificación DB. Código SQL no cambia en IMP-01. |
| SVC.admit_and_reserve, tests S3 previos | Comparación tenant vía str y assertion abreviado. Helper común no debe endurecer esa ruta por arrastre ni cambiar hashes; validar entrada nueva separadamente. Ruta legacy no se habilita como fallback. |
| CRTEST y TESTS crypto | Fixtures normales conformes. `test_tenant_and_product_substitution_without_resigning_denied` cambia UUID a 64 letras y espera SIGNATURE_INVALID: nuevo esquema puede rechazar antes como CLAIMS_INVALID. Registrar diferencia; conservar test/expectativa histórica y añadir negativos UUID válidos mutados para probar firma. |
| TESTS `test_executor_verifies_signed_capability_and_uses_executor_identity` (≈807) | Usa assertion `{adminapps_tenant_id, source:'s3'}` y sin contexto esperado. Será rechazado por el nuevo contrato. Conservar resultado/fixture histórico; agregar sucesor explícitamente etiquetado con assertion completo/contexto. No fabricar PASS del histórico ni extender por eso scope a PG. |

Mantener un oráculo del hash legado para material histórico y probar igualdad
sin admitirlo como nueva solicitud conforme. Completar assertion bajo la misma
invocation cambia material y debe producir conflicto, no «reparación» histórica.
Si se exige continuar admitiendo assertion abreviado, es una desviación AJ-C02
que impide seleccionar esta propuesta sin cambios; no añadir un bypass implícito.

## F. Test Matrix

### F.1 Estado de evidencia y vectores

**Toda la matriz CR/MT sucesora está NOT_RUN.** Esta tarea solo ejecutó lecturas,
AST, SHA-256, aritmética/serialización stdlib documental y controles de integridad.
No se importó producto, no se generó clave ni se firmó/verificó Ed25519 nuevo.
OFF conserva 19/19 crypto y 19/19 host; ER conserva 4/4 PG dentro de sus límites.
Las dos sondas históricas (whitespace y duplicado aud idéntico) siguen ACCEPTED
y **FAIL frente a C-B propuesto**; no son falsificación de firma. EVID conserva
siete casos de representación con igualdad/desigualdad de M(C), sin una nueva
verificación Ed25519. Su caso canonical también tiene 18 claves.

Fixture documental **CV1**: reutilizar EVID `checks`, entrada
`check=stdlib_json_representation_diagnostic`, `cases[name=canonical]`, sin
reescribirla. `json_diagnostic_reproduction` contiene el script histórico como
texto, no los resultados. J(C) = **695 bytes**, SHA-256
`42dc8821b07dbd9d96eada6585e22656f9026424ec59592258a89fe1779b001b`;
M(C) = **739 bytes**, SHA-256
`03218ff31fb76f46fc09ba63f955d4c00b2ef1cf51cf8a058eb73b3ac0788dc5`.
El material_hash allí es `a` repetida 64 veces: fixture de crypto, **no** positivo
integral material/executor. `capability_id` fijo termina en 006 y iat/nbf es
2026-10-09T12:00:00Z, exp 12:01:00Z. No verificarlo contra reloj real de hoy.

Fixture documental **MV1**, cuyos bytes son la línea JSON siguiente sin newline:

```json
{"evidence_ids":[],"max_input_tokens":10,"max_output_tokens":10,"model_identifier":"synthetic-model","product_id":"00000000-0000-0000-0000-000000000003","provider":"synthetic","request_class":"synthetic","schema_version":1,"tenant_assertion":{"adminapps_tenant_id":"00000000-0000-0000-0000-000000000002","tenant_projection_id":"00000000-0000-0000-0000-000000000007","tenant_projection_source_event_id":"00000000-0000-0000-0000-000000000008","tenant_projection_source_version":42}}
```

480 bytes; SHA-256 **`bd57f7c7520b3f2206c520b23123eec23a282bab06fb59b6dddbd93b3e576da6`**.
Se calculó con stdlib como dato documental, sin llamar SVC ni demostrar executor.
Para el positivo integral futuro usar ese hash en token y contexto tenant=002,
producto=003, productor=001, invocation=004, controlled_test/admit_reserve.

Vector firmado futuro: clave exclusivamente de fixture pública/documentada,
now fijo CV1 y uuid4 de mint controlado a 006 en el harness; registrar public
key raw, J, M, firma hex, token ASCII y sus hashes. Obtenerlo del emisor CAP
**baseline por SHA**, conservar bytes y comparar emisor/verifier nuevos con
oráculo independiente sobre M. Nada de generar esperado desde la misma función
bajo prueba y llamarlo compatibilidad. No se adjunta firma inventada: extracción
y ejecución se harán bajo permiso offline explícito. Claves de prueba nunca
credenciales reales, no se reutilizan fuera del harness.

### F.2 Matriz cerrada (cada subcaso se registra individualmente)

«Acepta» significa resultado de validación offline o llegada al doble de frontera
autorizado; no una reserva. **Z** en cada negativo exige cero lecturas/escrituras
al registro de aliases, cero obtención de connection, ensure_connection, cursor,
SQL, ORM/atomic y efectos PostgreSQL. Instrumentar dobles que fallen al primer
acceso y contadores por etapa; no basta mockear cursor.execute. Positivos del
executor alcanzan un doble terminal, nunca un backend de DB real, incluido SQLite.

| ID | Positivos exactos | Negativos / esperado y frontera | Estado / antecedente |
| --- | --- | --- | --- |
| CR-T01 | (a) token emitido por mint baseline, reloj fijo; (b) CV1 con key/UUID controlados conserva J/M/firma/token byte a byte; (c) token integral MV1/contexto válido alcanza doble | Cambiar prefijo LF por CRLF/quitar LF, dominio o firmar J/T en vez de M: SIGNATURE_INVALID cuando demás campos son válidos, Z. Distinta firma por key fija/mismo M: STOP de compatibilidad | NOT_RUN; CRTEST positivo histórico; EVID solo bytes/M, no nuevo Ed25519 |
| CR-T02 | Sorted/compact ASCII exacto y base64url roundtrip; slash permitido en ID se serializa sin escape | Whitespace antes/dentro/después, orden de claves, escape `\u0061` en clave/valor equivalente, slash `\/`, whitespace fuera de JSON, BOM, `-0`: MALFORMED (o esquema previo para valor fuera de dominio), Z. Conservar misma firma cuando M decodificado coincide para demostrar rechazo de wire | NOT_RUN; whitespace histórico ACCEPTED/FAIL C-B preservado |
| CR-T03 | Exactamente 18 claves únicas (F-C18), assertion con 4 únicas | Duplicado idéntico/conflictivo de cada claim, antes/después del original y nombre escapado decodificado; repetir también adminapps_tenant_id en JSON material: rechazo de parser, Z. Duplicado desconocido también deniega, nunca primero/último | NOT_RUN; sustituir criterio textual «19» solo mediante acta F-C18; duplicado aud histórico sigue FAIL C-B |
| CR-T04 | Cada tipo C, seis UUID canónicos incluyendo fixtures no v4/nil por forma; grant 1/max; hash hex64; IDs 1/max | Para cada claim: omitido/adicional; bool/float/exponente/null/list/dict donde incompatible; string por int; NaN/±Infinity; UUID compacto/upper/URN/braces/tamaño erróneo/no hex; ID vacío/control/no ASCII/max+1; hash upper/no hex/63/65; grant 0/−1/max+1; version true/1.0: CLAIMS_INVALID o MALFORMED para léxico/no finito, Z | NOT_RUN; faltante/extra/version histórico no prueba tipado exhaustivo |
| CR-T05 | Max payload 915/token1307 y firma64/86, dentro de gramática; profundidad1; roundtrip canónico con todas las clases de longitud base64 permitidas | Token bytes/int/None; cero/dos puntos, segmento vacío; `=`, `+`, `/`, whitespace, no ASCII, len mod4=1, pad bits no cero; firma63/65; UTF-8 inválido; raíz array/escalar, trailing JSON, nesting2 y nesting extremo acotado; payload916/token1308: MALFORMED, Z. Caso JSON lexical enorme rechazado antes de parse/decodificación costosa | NOT_RUN; malformed histórico parcial |
| CR-T06 | Key/iss/aud/env/op correctos; firma válida; now=nbf y exp−1µs; TTL1/60; nbf posterior a iat y anterior a exp | Mutación de cada claim conservando tipo/forma y firma original, bitflip firma, otra clave; key desconocida/retirada/wrong type; tokens correctamente firmados con alg/aud/iss/version/env/op incorrectos; ahora nbf−1µs/exp/exp+1µs; iat>nbf, nbf>=exp, TTL0/61; UTC sin Z/offset/fracción/fecha imposible/segundo60/epoch: código D.2 y Z. Keyring/reloj ausente falla seguro. expected ausente no crea fallback | NOT_RUN; firma y ventanas históricas parciales; retirada mock no es revocación operacional |
| MT-T01 | MV1 mismo SHA; hash legacy de assertion abreviado conserva bytes sin readmisión; evidencia [] y permutaciones de IDs válidos producen mismo hash ordenado; duplicados del array conservan multiplicidad | Cambiar cualquiera de los 9 campos o cualquiera de los 4 de assertion conservando esquema y token original: MATERIAL_DENIED salvo binding previo, Z. Deduplicar array o cambiar serialización/dominio/algoritmo: STOP; bytes/hash no coinciden. No confundir SHA distinto legítimo con permiso de cambiar invocation | NOT_RUN; helper inspeccionado, MV1 stdlib documental |
| MT-T02 | assertion=claim=contexto tenant; productor/producto/jti/env/op coinciden con contexto confiable, MV1 integral | Token válidamente firmado cuyo hash coincide con material tenant B pero organization=A; assertion A/claim B; contexto tenant/productor/producto/jti/env/op diferente; contexto ausente o proveniente de body no confiable; hash suministrado sustituido: BINDING_DENIED o MATERIAL_DENIED según D.2, Z. Probar mismatch productor autorizado para otro tenant, sin declarar grant vivo por mock | NOT_RUN; gap EXE demostrado estáticamente |
| MT-T03 | Material9/assertion4; schema1; units0/max; source_version0/max; provider/model1/max; request/evidence1/L_R/L_E y count0/N_E; defaults API Python explícitos; snapshot inmutable | Assertion parcial/extra/no dict/null, campo interno omitido/extra/tipo incorrecto; units bool/float/negativo/overflow, source_version−1/overflow, schema true/2, material no finito/cíclico/nesting3; evidence no list, item int/null/objeto, countN_E+1, longitudes+1; correlation UUID inválido: MATERIAL_REQUEST_INVALID y Z. Mutación caller entre hash y SQL no altera snapshot; si no puede garantizarse, deniega antes de DB | NOT_RUN; unidades legacy no prueban nueva ruta; fronteras L_R/L_E/N_E bloqueadas hasta NUM-C01 |

Faltantes/extras se generan para **cada** clave, no una muestra. Mutaciones de
firma usan valores aún válidos de esquema para no quedar ocultas por el parser.
Se ejercitan también fallos inyectados de librería/canonicalización/configuración
y se comprueba CAPABILITY_UNAVAILABLE/denegación segura + Z. Todos los negativos
del executor comparten el contador Z, incluso cuando tests de helper puro también
existen. El harness debe fallar si la instrumentación no cubre acceso al alias.

Criterio de aceptación futura: todos los subcasos aplicables con expected,
observed, códigos, bytes/SHA, seed/fixture, entorno, contador Z y salida registrados;
cero SKIP de fronteras obligatorias; revisión humana de compatibilidad. No sumar
19/19 histórico a esta matriz ni reetiquetar un test viejo como nuevo PASS.
Si la suite histórica falla por cambio de precedencia o assertion estricto,
conservar el fallo/delta y ejecutar el sucesor aprobado; no cambiar su expectativa
en este slice. Los tests PG históricos no se ejecutan bajo permiso offline.

## G. Exact Human Decisions to Sign

Este es el **único registro nuevo de selección**; no incorpora decisiones H/P/I.
Cada ficha tiene los nueve campos exigidos. F/S/D son funciones a designar con
mandato, no personas inferidas. La selección pendiente admite adoptar opción
recomendada, rechazar o modificar explícitamente; silencio o recomendación no
cuentan. Toda modificación debe identificar el texto sustituido y sus efectos.

### AJ-G01

| Campo | Registro |
| --- | --- |
| 1. Opción recomendada | Ratificar V11 por hash y alcance registrado, conservar D02 como autorización histórica específica LOGIN/Python, A02 pendiente; acto concreto B.2. |
| 2. Evidencia fuente/hash | V11, A01, D02, A02, ER y HAG, hashes completos B.1; DOC-T01 de MAT. |
| 3. Justificación | Resolver cabecera propuesta/adopción registrada sin inventar jerarquía, firmantes o aprobación de A02. |
| 4. Compatibilidad | Conserva historia, dominio, identidad, D02 y reservas; no modifica ISO Smart ni contratos históricos. |
| 5. Riesgo residual | Hash no prueba mandato; legitimidad depende de acta/custodia verificables. |
| 6. Autoridad necesaria | F + S + D; acreditación de mandato por instancia competente de gobierno y procedencia por custodio. |
| 7. Selección humana | **PENDING**; acta original o ratificación=PENDING; nombres/mandatos/firma/fecha/zona=PENDING. |
| 8. Condiciones de aprobación | Acta enlaza hashes, cláusulas/precedencia acotada, reservas, fecha efectiva y exclusiones. DOC-T01 sin campos vacíos. Ningún permiso G-IMP/runtime implícito. |
| 9. STOP | Mandato/firma/alcance/hash no verificable; adoptar DB verifier/NOLOGIN/HSM como si D02 lo aprobara; revocar o ampliar historia por inferencia. |

### AJ-C01

| Campo | Registro |
| --- | --- |
| 1. Opción recomendada | C-B v1 conforme C/D, nuevo endurecimiento de aceptación: 18 claims, base64/wire únicos, duplicados denegados, tipos exactos, errores D.2, firma M(C) intacta. |
| 2. Evidencia fuente/hash | D02, CAP, EXE, CRTEST, TESTS, ADJ, EVID/OFF y MAT/PLAN, B.1; C y F. |
| 3. Justificación | Eliminar ambigüedad de representaciones sin cambiar algoritmo ni bytes firmados. |
| 4. Compatibilidad | Mint conforme permanece; wires alternativos y tipos tolerados dejan de pasar. Aceptar explícitamente deltas E.3, sin modificar esperado histórico. |
| 5. Riesgo residual | Compromiso issuer/executor/keyring, consumidores desconocidos y disponibilidad por parser/límites. C-B no autentica transporte ni protege executor comprometido. |
| 6. Autoridad necesaria | F + S/protocolo, con declaración de consumidores bajo su responsabilidad. |
| 7. Selección humana | **PENDING**; adoptar/rechazar/modificar=PENDING; inventario aceptado=PENDING; firmantes/mandatos/firma/fecha=PENDING. |
| 8. Condiciones de aprobación | AJ-G01, F-C18, NUM-C01/02 resueltos para eficacia; adoptar matriz CR-T01–06 como aceptación futura, no exigir un patch antes del permiso. Bytes/versión y deltas expresos en acta. |
| 9. STOP | Cambiar M/claims/dominio silenciosamente, fallback permisivo, límite indefinido, excepción sin denegación, negativo que toca DB o firma/fuente discordante. |

### AJ-C02

| Campo | Registro |
| --- | --- |
| 1. Opción recomendada | Material9/assertion4 V11, contexto confiable de seis campos fuera de claims, comparaciones E.2 y hash SHA-256 idéntico; interfaz/dobles IMP-01 y adaptación issuer posterior. |
| 2. Evidencia fuente/hash | V11 §§4/6, D02, SVC, EXE, ISS, AUTH, TP, TESTS, M0007, B.1. |
| 3. Justificación | Hash firmado y tenant válido no bastan si el assertion pertenece a otro tenant o contexto. Separar consistencia de procedencia. |
| 4. Compatibilidad | Hash válido normal no cambia; assertion abreviado se conserva como historia/oráculo y no pasa admisión nueva. Interfaz EXE exige contexto, sin default derivado del token. |
| 5. Riesgo residual | Executor no demuestra proyección remota ni grant vivo; issuer aún recibe hash. Autenticación real del adaptador permanece posterior y bloquea operación. |
| 6. Autoridad necesaria | F + S; responsables de productor/adaptador aportan declaración de procedencia/consumidores, sin presumir integración autorizada. |
| 7. Selección humana | **PENDING**; assertion completo + cambio interfaz + rechazo legacy para nuevas entradas=PENDING; firmantes/mandatos/firma/fecha=PENDING. |
| 8. Condiciones de aprobación | AJ-G01/C01/NUM-C01 eficaces; aceptar explícitamente límites de procedencia y matriz MT; fuente confiable de contexto documentada E.2, en IMP-01 solo fixture/adaptador abstracto sin autenticación operativa fingida. |
| 9. STOP | Igualdad presentada como autenticación; contexto copiado del body/token; cambiar hash/identidad/historia; validar material distinto del enviado a SQL; DB antes de rechazo. |

### F-C18

| Campo | Registro |
| --- | --- |
| 1. Opción recomendada | Ratificar exclusivamente las 18 claves de C. Interpretar «19 claims» en ADJ/ADR/MAT/PLAN como error de conteo; CR-T03 sucesor exige 18, sin reescribir esos documentos. |
| 2. Evidencia fuente/hash | CAP hash B.1, AST `_REQUIRED` y dict mint; D02 lista semántica; EVID caso canonical; HAG hallazgo F-C18. |
| 3. Justificación | Dos conjuntos reales y fixture concuerdan en 18. Las 19 decisiones AJ son otro conjunto. |
| 4. Compatibilidad | Sin cambio de token, firma ni schema; ningún claim nuevo para compensar conteo. |
| 5. Riesgo residual | Un consumidor que implementó literalmente 19 puede ser incompatible; declararlo antes del patch. |
| 6. Autoridad necesaria | F + S/protocolo, enlazado a AJ-G01/C01. |
| 7. Selección humana | **PENDING**; ratificar conjunto C y criterio CR-T03=PENDING; firmantes/mandatos/firma/fecha=PENDING. |
| 8. Condiciones de aprobación | Acta reproduce/referencia conjunto exacto y hashes, distingue corrección prospectiva de alteración de evidencia. |
| 9. STOP | Agregar claim, eliminar uno existente, afirmar ratificación automática por AST o cambiar el test histórico para cuadrar el conteo. |

### NUM-C01

| Campo | Registro |
| --- | --- |
| 1. Opción recomendada | Adoptar C/D.2/D.4/E.1: UUID36/UTC20/ID, int exactos, límites derivados (915/1220/1307; profundidad1/2), material cerrado y método offline D.4 para L_R/L_E/N_E. |
| 2. Evidencia fuente/hash | CAP/SVC/EXE/MODELS/M0007/TP/V11/MAT, B.1; aritmética documental D.4 y MV1 F.1. No hay máximo contractual de request_class/evidence_ids localizado. |
| 3. Justificación | Usar cotas de representación/destino verificables; medir capacidad de campos sin techo en fuente sin inventar cifras vigentes. |
| 4. Compatibilidad | Conserva material conforme y multiplicidad de evidencia; restringe ASCII/longitudes/tipos. Rango source_version incluye 0 como TP. Rechazo de exceso explícito, nunca truncar. |
| 5. Riesgo residual | Corpus incompleto puede elegir cotas insuficientes; capacidad real aún no medida; SQL max no garantiza viabilidad presupuestaria. |
| 6. Autoridad necesaria | F + S/protocolo; dueños de consumidores declaran máximos legítimos. |
| 7. Selección humana | **PENDING**; límites concretos=PENDING; método D.4=PENDING; L_R=PENDING, L_E=PENDING, N_E=PENDING, B_M=PENDING; evidencia de medición/firma/mandato/fecha=PENDING. |
| 8. Condiciones de aprobación | Puede aprobarse método condicionado ahora; cierre solo con tres enteros finitos justificados, B_M calculado, corpus/hash, cobertura, fronteras y aceptación humana. Experimento requiere permiso explícito offline; aprobar método no concede implementación. |
| 9. STOP | Default sin evidencia, «máximo observado» usado como cota de dominio sin declaración, overflow/truncamiento, recursos ilimitados o permiso IMP-01 con campos aún PENDING. |

### NUM-C02

| Campo | Registro |
| --- | --- |
| 1. Opción recomendada | D.3: UTC20, iat<=nbf<exp, TTL1…60 s sintético, skew0, nbf<=now<exp; reloj consciente de zona sin truncar; revalidación antes de DB. |
| 2. Evidencia fuente/hash | D02 límite sintético; CAP `_iso`, `_time`, mint/verify; CRTEST fronteras, B.1. |
| 3. Justificación | No hay datos de deriva que justifiquen ampliar ventanas; política normal existente permanece. |
| 4. Compatibilidad | Emisor normal preservado; fechas alternativas, bool lifetime y ventanas vacías se deniegan. Conservar nbf posterior a iat válido. |
| 5. Riesgo residual | Skew real/reloj comprometido afecta disponibilidad; verificación pre-DB no prueba vigencia al commit. No TTL productivo autorizado. |
| 6. Autoridad necesaria | F + S/protocolo; política operativa de reloj futura conserva su propio alcance. |
| 7. Selección humana | **PENDING**; adoptar skew0/TTL≤60/UTC20=PENDING; firmantes/mandatos/firma/fecha=PENDING. |
| 8. Condiciones de aprobación | AJ-G01/C01 enlazados, elección temporal íntegra y fronteras CR-T06 adoptadas. Una alternativa con skew exige cifras/evidencia, sin ampliar D02 incidentalmente. |
| 9. STOP | Clock del request, naive datetime normalizado implícitamente, gracia no aprobada, lifetime>60 o afirmar garantía temporal de commit que DB no verifica. |

Cada firma/aceptación debe enlazar: ID de decisión, opción/desviación, **hash de
este documento final** más hashes B.1, persona, función, mandato verificable,
acta/procedencia, fecha efectiva con zona, condiciones cumplidas/pendientes y
riesgo residual aceptado. Su autohash se calcula externamente al firmar; no
insertar un hash autorreferente imposible ni firmar una revisión que luego cambie.

## H. S3-IMP-01 Readiness

| Prerrequisito | Resultado actual / salida exacta |
| --- | --- |
| Esquema, firma y binding especificados | Propuesta C–F completa en forma paramétrica; falta adopción, tres cifras y B_M. No confundir especificación con control implementado. |
| Autoridad | AJ-G01 pendiente; acta primaria o ratificación con mandato/hashes requerida. |
| Selecciones técnicas | AJ-C01/C02, F-C18, NUM-C01/02 sin firmas; aceptar expresamente compatibilidad E.3. |
| Parámetros no cerrados | Solo L_R, L_E, N_E y B_M derivado para este contrato; D.4 propone cómo obtenerlos. Otros límites y tiempo tienen selección concreta pendiente de firma. Identidades/keyring de fixtures se fijan en pruebas; no se requieren credenciales reales. |
| Compatibilidad | Inspeccionada, no ejecutada; CV1/MV1 bytes documentados. Fixture firmado reproducible y CR/MT se generan/ejecutan tras permiso offline de implementación, no prerrequisito circular de código antes de G-IMP. |
| Contexto autenticado | Interfaz/source-of-trust definida E.2; ausencia niega. IMP-01 solo lógica/dobles, autenticación efectiva issuer/adapter fuera de slice y condición de operación posterior. |
| Autorización de patch | G-IMP específico sigue PENDING. Con seis decisiones eficaces, parámetros e inventario aceptados, podrá considerarse READY_FOR_EXPLICIT_IMPLEMENTATION_AUTHORIZATION, nunca ejecución automática. |

**Archivos previstos y alcance permitido del futuro patch**, tras permiso:

| Archivo | Cambio delimitado |
| --- | --- |
| `backend/apps/financial/capabilities.py` | Parser/base64/esquema/tiempo/errores estrictos; mantener mint normal y M(C); guards de entrada exactos sin nuevos claims. |
| `backend/apps/financial/executor.py` | Contexto confiable obligatorio, esquema/assertion/binding/hash, snapshot y barrera antes de alias/DB. No transacción/retry SQL nueva. |
| `backend/apps/financial/services.py` | Validador puro reutilizable o wrapper de nueva ruta sin cambiar hash ni comportamiento S1/S2/legacy por arrastre. No refactor financiero general. |
| `backend/scripts/tests/test_s3_capability_offline.py` y `backend/apps/financial/tests.py` | Solo adiciones sucesoras/fixtures separadas cuando no alteren oráculo/expectativas históricas. Conservar cuerpos/esperados históricos; informar divergencias E.3. No correr suite Django con DB. |
| Nuevo `backend/scripts/tests/test_s3_imp01_contract_offline.py` | Propuesto para matriz sucesora y dobles sin setup Django/DB/IPC, separando evidencia histórica. Nombre a incluir expresamente en G-IMP. |

Módulo compartido adicional solo si el permiso lo enumera y revisión justifica
extraer validación pura para imports offline. `issuer.py`, AUTH, modelos,
migraciones, settings, SQL, scripts PG/host, OS/systemd y repositorios ISO Smart/
MedSupplier son **referencias, no archivos permitidos de implementación IMP-01**.
Recomputación issuer y adaptador autenticado permanecen posteriores. Este
documento no crea endpoints ni cambió archivos de esa lista.

Pruebas offline permitibles: matriz F con bibliotecas locales, fixtures sintéticos,
dobles que bloquean DB, lector de baseline por hash y cotejo byte a byte; AST y
controles Git/documentales. Registrar versiones del intérprete/biblioteca, sin
instalar dependencias ni usar red/servicios como parte del test. Sin migraciones,
Django test DB (tampoco SQLite), sockets, procesos de servicio, PostgreSQL o IPC.

**Rollback:** STOP ante cambio de M(C)/hash normal, fallo de positivo conforme,
rechazo que toca DB, excepción no tipada, TOCTOU, consumidor incompatible no
aceptado, o fuente/hash distinto al aprobado. Conservar diff, fixtures, logs y
baseline; retirar solo patch propio en copia aislada. No reset/checkout global,
reescritura de historia ni habilitar el parser anterior como fallback operacional.
Retirada del patch deja S3 bloqueado; no borra evidencia de FAIL.

Exclusiones operativas: ningún Host Lab, PG/IPC, migración, sudo, cambio OS/
systemd, credencial real, inferencia/proveedor, operación financiera, deployment,
stage/commit/push/merge. No habilitar S4–S6, Phase31.5, Phase32, WP2 ni integración
ISO Smart/MedSupplier. Bloqueos PG/IPC/custodia/recuperación de HAG siguen fuera
de este contrato; no se solicitan de nuevo para aprobar el parser offline.

## I. Git Integrity

Baseline previo a escritura: **15.529 entradas** tracked/untracked no ignoradas
de AdminApps, bytes/modo de archivos y texto/modo de symlinks sin seguirlos.
No certifica archivos ignorados, destinos externos de enlaces ni estado runtime.

- Rama: `hardening/p0-p1-enterprise-readiness`.
- HEAD: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`.
- SHA-256 índice: `d774b85b7f9123d243c0d094e6efe7e151ac3a1c38d8eee4a00970438dfcfd50`.
- Control temporal: `/tmp/s3-imp01-contract-u2p05fxo/baseline.json`, SHA-256
  `94f2533b19ec8d6c35d585e63f16fd08fd64c483b48e2b1fc6029dff02a4232c`.
  No es segundo entregable ni evidencia de autoridad; no depende de retención
  de /tmp para conferir aprobación.

Estado preexistente:

```text
 M backend/config/settings.py
?? backend/apps/financial/
?? backend/scripts/s3_isolation_host_lab.sh
?? backend/scripts/tests/
?? backend/scripts/verify_financial_s1_postgres.sh
?? backend/scripts/verify_financial_s3_postgres.sh
?? docs/financial/
```

Verificación de preservación: **15.529/15.529 entradas preexistentes idénticas**;
ninguna modificada/eliminada; única adición este documento. Rama, HEAD e índice
idénticos. Delta de `git status --porcelain=v1 -uall`: exclusivamente este archivo,
sin entradas retiradas. **26/26 fuentes B.1** conservan sus bytes, incluidos los
contratos externos y TP. No se ejecutó stage, commit, push, merge, reset o checkout.

Verificación documental: diez secciones A–J; seis fichas con sus nueve campos;
18 claims únicos iguales al AST; enlaces locales válidos; hashes CV1/MV1,
prefijo44, cota915/1307 y fórmula B_M comprobados con stdlib. `git diff --check`
sin diagnósticos; comprobación explícita del nuevo archivo untracked con
`git diff --no-index --check /dev/null <documento>` sin diagnósticos (exit 1
normal por archivo nuevo, no un PASS de producto). Pruebas CR/MT, firma Ed25519,
PostgreSQL, IPC y Host Lab **NOT_RUN**.

## J. Next Authorization Boundary

La siguiente interacción puede ser una **selección humana de estas seis fichas**,
con acta/mandato verificable, usando este texto de respuesta como plantilla (no
está firmado ni preseleccionado):

```text
Documento/hash revisado: PENDING
Persona(s), función(es), mandato(s), evidencia y fecha/zona: PENDING
AJ-G01: [adoptar B.2 / rechazar / modificación expresa] PENDING
AJ-C01: [adoptar C-B C/D + deltas E.3 / rechazar / modificar] PENDING
AJ-C02: [adoptar material9/assertion4/contexto E / rechazar / modificar] PENDING
F-C18: [ratificar las 18 claves C y CR-T03 sucesor / rechazar] PENDING
NUM-C01: [adoptar límites derivados y método D.4 / rechazar / modificar] PENDING
  L_R, L_E, N_E, B_M y evidencia offline ratificada: PENDING
  Permiso separado para medición offline acotada, si se concede: PENDING
NUM-C02: [adoptar UTC20, skew0 y TTL sintético≤60 / rechazar / modificar] PENDING
Condiciones/compatibilidad/riesgos aceptados/exclusiones: PENDING
Acta/firma o mecanismo autenticado de aceptación: PENDING
G-IMP S3-IMP-01: NO CONCEDIDO por estas selecciones.
```

No pedir una investigación genérica adicional: solo acreditar autoridad, elegir
las opciones concretas y resolver las tres cotas por el método propuesto o
aportar valores respaldados y aceptados expresamente. Una aprobación condicional
de NUM-C01 conserva el bloqueo hasta su ratificación numérica. Una vez todos los
prerrequisitos sean eficaces, solicitar/emitir G-IMP referido al alcance H y hash
aprobado; **no iniciar código por la mera decisión de arquitectura**.

**S3-IMP-01 = BLOCKED_PENDING_AUTHORITY. S3_DECISION_02A_NOT_CLOSED.
PHASE31_5 = EXECUTION_HELD. Cero aprobaciones nuevas.**
