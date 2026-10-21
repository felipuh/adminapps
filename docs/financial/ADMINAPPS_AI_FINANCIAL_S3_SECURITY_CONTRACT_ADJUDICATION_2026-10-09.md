# S3 — Security Contract Adjudication

Fecha: 2026-10-09, America/Costa_Rica. **DICTAMEN TÉCNICO; APROBACIÓN HUMANA PENDIENTE.**
Continuación del paquete S3 de esta fecha. Este addendum reconcilia su lectura;
no sobrescribe documentos históricos, contratos ni actas. Los identificadores
AJ-* identifican decisiones de revisión, no requisitos normativos nuevos.

## A. Executive Verdict

**Decision 02-A sigue NOT CLOSED.** La evidencia permite preparar decisiones,
no aprobar arquitecturas ni certificar aislamiento operativo. No se ejecutó
Host Lab, PostgreSQL, IPC, código privilegiado, migración ni despliegue.

| Estado de esta entrega | Justificación y límite |
| --- | --- |
| `S3_HOST_EVIDENCE_STATUS_RECONCILED` | Inventario, procedencia, recuperación local y límites adjudicados en B. Host sigue `EVIDENCED_PARTIAL`; no cierre host. |
| `S3_CRYPTOGRAPHIC_JSON_DECISION_READY` | Representación firmada, semántica, alternativas y pruebas definidas en C. No política nueva aprobada. |
| `S3_POSTGRESQL_ARCHITECTURE_READY_FOR_APPROVAL` | Decisiones AJ-P01–P09 revisables en D; aislamiento runtime pendiente. |
| `S3_IPC_ARCHITECTURE_READY_FOR_APPROVAL` | Comparación y propuesta AJ-I01–I06 en E; transporte sigue `NOT_IMPLEMENTED`. |
| `S3_DECISION_02A_NOT_CLOSED` | Faltan decisiones humanas, implementación autorizada, evidencia operativa y aceptación de gobernanza. |

Hallazgos principales:

- Las dos sondas históricas no demuestran falsificación Ed25519. El verificador
  firma/verifica la reserialización del objeto JSON, no los bytes recibidos.
  Duplicados conflictivos pueden dar semánticas distintas entre parsers; no se
  encontró un segundo consumidor financiero que explote esa diferencia.
- `0006` omite ownership explícito de tres tablas; el owner efectivo depende
  de la identidad que migre. No se ha observado un catálogo nuevo.
- El executor no garantiza SERIALIZABLE ni reintentos. V1.1 permite locks
  equivalentes **solo con pruebas de la misma invariante**, ausentes en esa ruta.
- `--auth=trust` del verifier acredita selección de rol/ACL en el antecedente,
  no posesión exclusiva de una credencial. No hay rol ni lectura DB de issuer
  provisionados, ni servicios financieros IPC implementados.

Se recomienda, pendiente de aprobación: JSON único y estricto compatible con
el emisor actual; executor LOGIN con verificación Python según D02; ownership
de migración explícito; autenticación DB real por identidad separada;
transacción SERIALIZABLE propia del executor; y sockets UNIX pathname locales
con autenticación mutua del peer. Los valores, derechos y gates se detallan
abajo; no se convierten en controles implementados por aparecer aquí.

## B. Host Evidence Adjudication

### B.1 Inventario y fuerza probatoria

| Evidencia | Conservado/verificado ahora | Qué no acredita |
| --- | --- | --- |
| Fuente host y regresión | SHA host `4a50014a069289af60afacedc89b6d93468edbd3921c8c6d72c3e005d6c086a5`; coincide con OFF y testimonio. Sintaxis comprobada, sin ejecutar el script. | Hash de copia protegida durante el run, identidad del operador, ejecución ni cleanup. |
| OFF anterior | JSON con comandos, stdout/stderr, retornos y hashes; 37/37 fuentes y 6/6 entregables referenciados coinciden. El séptimo archivo es OFF mismo, hasheado al inicio de esta revisión. | No es un log host; integridad de bytes no equivale a procedencia autenticada. |
| 19/19 host y 19/19 crypto | Salidas históricas conservadas en OFF; no se repiten pruebas cerradas. | Fixtures y memoria no prueban procesos, credenciales, DB ni IPC. |
| Adjunto del usuario anterior | Hash `3b2b408845796f4a4f7301c8085719d6bef5ebbb8d914373c4524d07ce0b8af1` coincide. Contiene resultados reportados, no transcript original. | PASS host/DAC/seccomp y ausencia final siguen siendo afirmaciones secundarias. |
| Salidas preexistentes recuperadas | 50 archivos pequeños `/tmp/s3-*.out/.err`, `/tmp/s3_*.out/.err` y `/tmp/adminapps_s3_usage.out`, leídos sin ejecutar. Texto íntegro, SHA, tamaño y metadatos preservados en EVID. | No incluyen comando original, retorno, run ID ni SHA ejecutado. No vincularlos al run exitoso por nombre o fecha. |
| Cierre host anterior y reportes HG/HR/VM | Conservados byte por byte; documentan predicados, correcciones y limitaciones. | No sustituyen logs primarios de la ejecución posterior. |

EVID conserva las copias textuales exactas de los archivos de `/tmp`, incluso
los vacíos; SHA se calcula sobre los bytes originales. Su clasificación es
separada de la copia y no modifica su texto. Son artefactos primarios de salidas
previas **sin atribución suficiente**, no evidencia primaria autenticada del
Host Lab exitoso. UID, modo y mtime actuales no establecen cadena de custodia.

Ejemplos que evitan una adjudicación falsa:

- `s3_lab_regression.out`: 19 PASS, SHA
  `6b9c4f56f1d32e1cb3a346193fe57f6a3ab57c75ce50bdbd43521e08e3b2b8fe`.
  La etiqueta «PASS symbolic SystemCallFilter» no dice por sí sola si el test
  esperaba aceptar o rechazar el token; requiere vinculación al harness exacto.
- `s3-cleanup-final.err`: rechazo «must run as root», SHA
  `3f7817ccf26168132138aedebb12fc32b05c8aec55766b5b2eaaa403ab7a5be1`.
  Su stdout vacío no prueba cleanup exitoso.
- `s3-manifest-plan.out`, `s3-recovery-created_directory.out` y
  `s3-recovery-manifest_only.out` contienen `CLEANUP_COMPLETE`, SHA
  `82c392cd06805dd5e8004ff33c632bc987282cbfd8737ccf7b52b811cf47867a`.
  Son compatibles con fixtures descritos en HG; la coincidencia textual no
  acredita limpieza de cuentas/servicios del laboratorio histórico.

### B.2 Recuperabilidad adjudicada

| Registro | Adjudicación | Recuperación no invasiva posible |
| --- | --- | --- |
| `/proc/<PID>/status`, cgroup y contexto exactos del probe | No recuperables del proceso original una vez terminado. El script lee status/cgroup pero no imprime sus contenidos completos. | Solo un snapshot/transcript que ya los hubiera capturado. Consultar otro PID sería evidencia nueva y potencialmente de otro proceso. |
| Manifest histórico | El código elimina el manifest como última acción y el operador reportó esa eliminación. No hay copia localizada. | Backup/export anterior, si existe; no reconstruirlo del inventario planificado. No afirmar pérdida global definitiva sin revisar retención. |
| `systemctl show`, expansión de syscalls y seis controles DAC | Fuente/testimonio disponibles; transcript del run exitoso no localizado. | Captura de terminal o archivo de sesión ya existente. Logs systemd pueden corroborar arranque/parada si se retuvieron; no garantizan conservar stdout del script ni todos sus predicados. |
| Copia root, sidecar y respaldos | Existencia/retención reportadas; no inspeccionados aquí. | Custodio puede aportar export existente con hashes y procedencia. Hash tomado ahora no demuestra por sí mismo qué se ejecutó antes. |
| Error Bash original y transición de hashes HR → `4a500…` | No recuperados. Archivos financieros sin rastrear: Git no ofrece historial de esas versiones. | Backups/versionado del editor o captura ya existente, con validación humana de origen. No inferir diff exacto a partir de reportes. |
| Modo `/root` 0550 → 0700 | Relato del operador; conforme al gate del lab, compatibilidad con política general `SOURCE_INSUFFICIENT`. | Baseline/ACL y aceptación documental del responsable del host. Sin chmod ni restauración automática. |

Búsqueda realizada: documentos financieros, código/tests, nombres de evidencia
en `docs`/`backend/scripts` incluidos archivos normalmente ignorados mediante
recorrido local, y archivos S3 de primer nivel en `/tmp`. Se consultó el adjunto
ya referenciado en OFF. No se leyó `/root`, historia de shell, secretos, journal
del sistema ni estado runtime. No se hizo búsqueda indiscriminada en directorios
personales. El límite es **no localizado en este alcance**, no «nunca existió».

Recomendación AJ-H01: mantener `EVIDENCED_PARTIAL`, con evidencia runtime
primaria insuficiente y ejecución/cleanup reportados PASS. El custodio host
debe declarar qué archivos conserva y qué se perdieron; gobernanza debe decidir
si acepta esa limitación documental. Tal aceptación no convierte testimonios
en pruebas ni cierra PostgreSQL/IPC. No repetir Host Lab en esta tarea.

## C. Cryptographic JSON Contract Decision

### C.1 Contrato fuente y bytes exactos

[D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) registra
`HUMAN_APPROVED` para remediación acotada. Prescribe Ed25519, dominio, claims,
JSON sorted/compact ASCII y controles de validez. No define inequívocamente
rechazo de **todas las representaciones wire equivalentes**.
[A02 §6.2](ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md)
sí pide rechazar duplicados y codificaciones no canónicas, y verificar en DB,
pero continúa `APPROVAL_PENDING`. No promover esa propuesta a norma vigente.

Según [capabilities.py](../../backend/apps/financial/capabilities.py):

```text
C = dict de 19 claims
J(C) = json.dumps(C, sort_keys=True, separators=(',', ':'),
                  ensure_ascii=True, allow_nan=False).encode('utf-8')
M(C) = b'adminapps.financial.admission-capability.v1\n' + J(C)
signature = Ed25519.sign(private_key, M(C))
token = base64url(JSON_del_emisor).sin_padding + '.' + base64url(signature).sin_padding
```

El emisor usa los mismos parámetros de serialización para el payload, salvo
que no especifica `allow_nan=False` en ese segundo dumps; la firma ya calculó
M(C) y rechaza no finitos antes de devolver el token. **No es JWS/JWT**, no firma
la representación base64 ni el payload wire original. No se ha establecido un
estándar de canonicalización interoperable ni se afirma cumplimiento de JCS.

Claims exactos: `alg`, `aud`, `capability_id`, `environment`, `exp`, `grant_id`,
`grant_version`, `iat`, `iss`, `jti`, `kid`, `material_request_hash`, `nbf`,
`operation`, `organization_id`, `product_id`, `producer_registration_id`,
`version`. `jti` representa invocation; `correlation_id` no está firmado.
No agregar claims de A02 silenciosamente a v1.

Verificación actual: split en dos partes → base64 decode → UTF-8 →
`json.loads` ordinario → dict/conjunto exacto de claves → alg/version/aud/iss/kid
→ Ed25519 sobre **M(dict parseado)** → ventana temporal → bindings opcionales
→ devuelve ese mismo dict. Duplicados se colapsan con el último valor antes
del control del conjunto de claves y antes de verificar la firma.

### C.2 Productores, consumidores y discrepancia semántica

| Ruta | Interpretación comprobable en fuente | Límite |
| --- | --- | --- |
| `issuer.py::issue_admission_capability` | Autentica hashed_v1 y grant activo; crea dict vía mint. Recibe material hash como argumento. | No recibe JSON wire ni material completo para recomputarlo. No hay transporte implementado. |
| `FinancialExecutor.admit_reserve` | Usa el dict devuelto por verify; recalcula SHA-256 del material; pasa sus claims por parámetros SQL tipados. | No vuelve a parsear el token. No suministra `expected`; no compara expresamente tenant_assertion.adminapps_tenant_id con organization claim. |
| Hash material en `services.py` | Sorted/compact ASCII JSON de schema, assertion, producto, proveedor/modelo, límites, clase y evidence IDs ordenados. | Distinto de M(C); sin dominio, sin `allow_nan=False`, sin esquema profundo estricto. JSON de transporte aún no definido. |
| DB `0007` → `0005` | Recibe campos escalares; revalida grant/versión/tupla, luego lógica de admisión y replay. | No recibe JSON/token/firma/exp/nbf; no verifica Ed25519. La credencial executor pertenece a la frontera confiada de D02. |

Sondas históricas OFF: whitespace no canónico y duplicado idéntico de `aud`
fueron ACCEPTED. Son FAIL **del rechazo estricto propuesto**, no FAIL de firma.
La nueva comprobación stdlib de siete representaciones conserva la firma fuera
de ejecución: prueba igualdad de M(C), no una nueva ejecución criptográfica.

| Representación | M(C) respecto del original | Adjudicación |
| --- | --- | --- |
| JSON del emisor | Igual | Control positivo de representación. |
| Whitespace o reordenamiento | Igual | Malleabilidad de wire sin cambio de claims; aceptación coherente con parse/re-serialize. |
| Clave repetida con valor idéntico | Igual | El conjunto de claves no detecta multiplicidad. |
| `aud="other"` antes del `aud` válido | Igual bajo último-valor | Un parser primer-valor vería otra audiencia. El mismo token puede conservar firma válida sin volver a firmar. Es inferencia de código/igualdad de mensaje, no nuevo exploit runtime. |
| `aud="other"` al final | Distinto | El verificador actual rechaza por audiencia; para otro claim ligado a firma, cambiar el último valor requiere firma nueva. |
| Clave inicial `\u0061ud` conflictiva, seguida de `aud` válido | Igual bajo último-valor | Detectar duplicados debe hacerse sobre claves decodificadas, no por búsqueda textual. |

**Existe riesgo de discrepancia entre parsers. No hay evidencia de discrepancia
explotable entre los consumidores financieros actuales:** comparten el dict
verificado y DB no parsea JSON. Un proxy, logger con decisiones de seguridad,
otro lenguaje o futura capa IPC que interprete el wire por separado introduciría
esa segunda semántica. Deducir autorización del token bruto o usar su texto como
identidad antireplay sería incorrecto; la identidad vigente es la tupla de
invocación más hash material, no el string del token.

Controles presentes: algoritmo/dominio fijos, claves públicas allow-listed,
claims exactos, firma, issuer/audience, máximo 60 segundos y ventana nbf/exp,
material hash en executor y grant vivo en DB. Controles no completos: tipos
exactos por claim (`True == 1` no es tipo entero estricto), UUID/strings y tamaños,
operación en verifier (DB sí la comprueba), entorno esperado local, JSON/base64
wire único, rechazo tipado de todos los errores, revocación operacional de key
y credencial. La emisión normal produce valores esperados; ello no equivale
a validar un emisor defectuoso. No se probó explotación de esos casos.

### C.3 Alternativas para AJ-C01 (decisión pendiente)

| Opción | Riesgo/compatibilidad | Recomendación |
| --- | --- | --- |
| C-A: especificar parse/re-serialize v1, permitir formatos equivalentes, rechazar todos los duplicados y restringir esquema | Conserva whitespace/orden alternativo; exige parsers compatibles y que nadie autorice desde wire. El rechazo de duplicados sería una nueva política explícita. | Viable si hay consumidores que necesitan flexibilidad. No basta afirmar «JSON canónico» sin perfil y vectores. |
| C-B: exigir exactamente el wire del emisor actual, con detección de duplicados y perfil de tipos explícito | Rechaza representaciones que hoy acepta verify. Conserva M(C) y tokens emitidos normalmente; exige evaluar compatibilidad de cada consumidor. | **Recomendada**, por mínima superficie semántica y ausencia de transporte/consumidores alternativos respaldados. Aprobar interpretación/versionado antes de implementarla. |
| C-C: nuevo protocolo de canonicalización interoperable o firma de bytes originales con parser estricto | Facilita otros lenguajes, pero puede cambiar escapes, números, dominio y mensaje firmado. Firmar bytes por sí solo no elimina discrepancias de parseo. | Solo si existe necesidad documentada; usar versión/dominio nuevos y transición explícita, nunca reemplazar M(C) silenciosamente. |
| C-D: conservar conducta actual sin especificación adicional | Menor cambio inmediato; mantiene duplicados ambiguos y múltiples wires por capability. | Estado actual mientras no haya decisión; no recomendado para habilitar IPC. |

Clasificación: **ambigüedad de contrato wire y brecha frente a propuesta pendiente**.
No se confirma defecto criptográfico vigente solo por las dos sondas. Si la
autoridad confirma que «canonical» en D02 ya exigía igualdad del wire, reclasificar
como incumplimiento de D02 con acta explícita, no como una aprobación retroactiva
de A02 completa. No hay motivo para cambiar algoritmo o quitar controles.

Corrección mínima propuesta para C-B, **sin implementar**: parser que rechace
claves duplicadas decodificadas; objeto/19 claims con tipos estrictos (int no bool),
UUID/identificadores y límites acordados; prohibir no finitos; comparar payload
UTF-8 con J(C); base64url estricto y roundtrip sin padding para ambos segmentos;
mantener dominio y firma; errores como denegación segura antes de DB. Ni un
`object_pairs_hook` ni un dumps aislado resuelven todo el contrato.

Pruebas futuras: positivo con tokens del emisor actual y vectores fijos;
negativos whitespace/orden/escapes alternativos, duplicado idéntico/conflictivo
en ambas posiciones y clave escapada, faltantes/extras, tipos bool/float/null,
NaN/Infinity, UTF-8/base64 inválidos, exceso de tamaño/profundidad, firma/key/aud/
issuer/env/op inválidos, caducidad y sustitución de material. Cada denegación debe
ocurrir sin conexión/efecto DB; los positivos deben sobrevivir. Probar con todos
los consumidores aprobados. No contar estas pruebas propuestas como ejecutadas.

AJ-C02: aprobar esquema del material y enlace assertion↔organization; mínimo
rechazo de inconsistencia antes de DB, sin alterar hash/claims históricos a
escondidas. Fuente: V1.1 §§4/6 y D02 recomputación. La ruta anterior `services.py`
sí compara ese tenant; el executor nuevo carece de ese control explícito. Es un
gap de validación de ruta, no evidencia de elusión de grant. Que issuer recompute
material completo, registre issuance o use HSM es propuesta de A02 §6.1 y del
futuro adaptador IPC, no capacidad hoy implementada.

Autoridad propuesta AJ-C01/C02: responsable del contrato financiero y responsable
de seguridad/protocolo de AdminApps; nombres/mandato requieren designación.
STOP: cambio de mensaje firmado sin versión aprobada, duplicados interpretados
en más de un parser, inventar tipos como política vigente, o convertir las
sondas en PASS cambiando su expectativa sin decisión registrada.

## D. PostgreSQL Architecture Decision Matrix

Fuentes: D02 «Database boundary», V1.1 §§5.2/8, FIN-04/06/08/11, migraciones
0002–0007, issuer/executor/services y verifier. A02 aporta alternativas propuestas,
no sustituye D02. La [especificación PG anterior](ADMINAPPS_AI_FINANCIAL_S3_POSTGRESQL_ISOLATION_SPECIFICATION_2026-10-09.md)
conserva PG-T01–11 como catálogo de pruebas futuras.

Todos los AJ-P* están **PENDING_HUMAN_APPROVAL**. DBA, dueño financiero, seguridad
y custodio de plataforma son autoridades funcionales propuestas; este documento
no nombra personas ni les concede permisos. Ninguna opción autoriza conectar DB.

| Decisión / contrato fuente | Riesgo y alternativas | Recomendación e implicaciones | Pruebas necesarias | Autoridad y STOP |
| --- | --- | --- | --- | --- |
| AJ-P01 — ownership `0006`; V1.1 §8, D02, 0002/0003/0006 | Tres tablas nuevas sin `ALTER OWNER`; migrar como bootstrap puede dejarlas con ese dueño. Alternativas: ownership explícito; crear siempre como migration con precondiciones; dejar ownership implícito. | Owner explícito `adminapps_financial_migration` para grants, eventos y ledger, separado de admission/executor/runtime. Conservar FORCE RLS/triggers. Preparar migración correctiva posterior, no reescribir historial aplicado; si nunca aplicada, autoridad decide estrategia. Resolver política de administración bajo FORCE RLS, no usar BYPASSRLS para operar. | Catálogo de las 15 tablas, funciones y auxiliares; identidad de migración; DDL/GRANT/ALTER POLICY/OWNER/SET ROLE denegados a runtime/executor. Migración correcta funciona y owner inesperado detiene el ensayo. PG-T04/05/06. | DBA + dueño financiero. STOP ante owner inesperado, intento de «arreglar» catálogo durante test o falta de ruta administrativa revisada. |
| AJ-P02 — identidades exclusivas; D02 trust boundary y 0006/0007 | Executor LOGIN requerido por D02; A02 propone NOLOGIN. Issuer no tiene rol DB. Alternativas: mantener LOGIN dedicado; login de servicio + rol NOLOGIN mediante SET ROLE; fusionar issuer/executor/runtime. | Mantener LOGIN executor de D02, sin memberships elevados. Proponer login DB exclusivo issuer y UID separado con clave privada exclusiva. Lecturas issuer: credencial hashed_v1, registro/lifecycle, grant/evento; proyección mínima adaptada al ORM. No EXECUTE de admisión ni writes de grant. No compartir conexión, clave o DSN. Opción NOLOGIN exige revisar D02 y probar cada edge SET ROLE. | Positivos para cada función; issuer no ejecuta/actualiza, executor no lee tablas ni firma, runtime no obtiene ninguno. Inspeccionar flags, memberships transitivos y session_user/current_user. PG-T01/02/05/10. | Seguridad + DBA + dueño de servicios. STOP ante misma identidad/credencial, lectura issuer resuelta con admin o rol inexistente asumido como desplegado. |
| AJ-P03 — autenticación real; D02 exclusividad, verifier `--auth=trust` | `trust` no demuestra secreto ni UID exclusivo. Alternativas: peer con mapeo exacto para Unix local; SCRAM-SHA-256 con secreto único; mTLS/cert si otro host; trust solo para antigua fixture ACL. | Para candidato IPC de un host, preferir peer por UID exclusivo y mapping exacto, socket privado sin TCP; no hay contraseña que compartir. El ensayo de contraseña/revocación literal requiere perfil SCRAM separado; si política exige password, escoger SCRAM con entrega aislada y sin exposición. No inferir exclusividad de nombres de rol. | UID/password/cert correcto conecta; UID ajeno no solicita executor; credencial errónea falla; HBA sin fallback trust; control de salud antes/después; dos identidades OS reales para probar peer. PG-T01/10. | DBA + seguridad + plataforma. STOP si topología no es local para peer, mapping genérico, auth trust, fixture de un solo UID presentada como aislamiento o conexión a DB compartida. |
| AJ-P04 — RLS y tenants; V1.1 §8, D02, 0002–0007 | FORCE RLS no corrige autorización de una función central; `app.tenant_id` es controlable por sesión. Alternativas: conservar funciones centrales con grants; rediseñar contexto de tenant autenticado; conceder tablas por GUC. | Conservar RLS ENABLE/FORCE y política central explícita del admission owner, con su ACL mínima. Runtime/executor sin acceso a decisiones/reservas/audit/budget; issuer obtiene políticas SELECT específicas. No convertir GUC en identidad. Documentar lecturas históricas restantes de runtime y auditor central por tabla. | A/B/sin contexto/GUC falso; diferenciar ACL 42501 de filtrado y trigger; auditor positivo autorizado; sin writes/DDL. Issuer SELECT permitido solo por su política; no copiar USING(true) a runtime. PG-T03/04. | DBA + seguridad + dueño financiero. STOP si se retiran FORCE/trigger, se acepta no-context para un rol tenant-scoped, o se cuentan fallos de conexión como RLS. |
| AJ-P05 — mínimo privilegio; D02 DB, 0005/0007 | ACL actual incompleta para schema/defaults/CONNECT/TEMP; NOINHERIT no demuestra ausencia de SET ROLE. Alternativas: allow-list explícita por objeto y creador; defaults heredados; schema financiero nuevo. | Executor solo CONNECT necesario, USAGE public, EXECUTE wrapper; no EXECUTE legacy ni grants directos financieros. Admission NOLOGIN dueño de función, separado de tablas; revisar UPDATE usados por locks y controles contra mutación. Denegar creación en schemas confiables a runtime/PUBLIC; revisar TEMP, funciones auxiliares y defaults por creador. No migrar de schema sin necesidad aprobada. | Catálogo pg_roles/auth_members/class/policy/proc/namespace/database/default_acl; pruebas de sombra public/TEMP, objetos futuros, DDL, SET ROLE. Conexión saludable y SQLSTATE atribuible. PG-T02/05/06. | DBA + seguridad. STOP ante PUBLIC EXECUTE, esquema escribible que afecte resolución, ownership runtime o membresía administrativa. |
| AJ-P06 — SERIALIZABLE executor; V1.1 §5.2, FIN-04/06 y services:257 | Executor carece de transacción/retry explícitos; constructor puede traer configuración externa, pero fuente/fixture no la garantizan. Alternativas: transacción SERIALIZABLE por operación; default de rol/conexión con guard; locks equivalentes probados. | Transacción explícita en alias executor, aislamiento antes de SQL y comprobación efectiva; retry acotado de 40001 y política explícita para 40P01 tras rollback. Mantener invocation/hash, revalidar capability/exp/grant en cada intento. Cerrar conexión no equivale a commit confirmado. Definir orden completo grant → identidad → registro → policy/tariff → budgets global/product/UUID para todas las rutas. | Medir transaction_isolation en sesión real; carreras executor global/product/tenant, policy/tariff/entitlement/revocación, 40001/40P01 y agotamiento, rollback y respuesta perdida. PG-T07/08/09. | Dueño financiero + DBA + seguridad. STOP ante garantía externa no verificada, evidencia de otra ruta, retry con invocation nueva o commit ambiguo tratado como éxito. |
| AJ-P07 — revocación; D02 grant lock, issuer transition, A02 lifecycle propuesto | Revocar grant, producer key, issuer key, login DB y peer son controles distintos. Guardar estado/evento del grant no tiene atomic propio. Alternativas: corte solo conexiones nuevas; drenaje con corte definido; terminación selectiva administrativa. | Cambio grant+versión+evento en una transacción con lock del mismo grant; commit es frontera, admisión anterior conserva historia. Retirar key pública/peer de forma versionada y fail-closed por solicitud. Autenticación peer: retirar mapping/acceso; password: invalidar credencial/login. Elegir tratamiento de sesiones ya abiertas y efecto en vuelo; no prometer que NOLOGIN/password nuevo las termina. | Grant activo positivo, revocado/suspendido/version vieja negativo; crash estado/evento, carrera controlada; key retirada y login nuevo denegado; sesión previa/solicitud en vuelo con resultado acordado. PG-T07/09/10. | Dueño financiero para grants; seguridad/DBA para keys/logins; plataforma para peers. STOP ante estado/evento divergente, reutilizar snapshot de allow-list indefinidamente, revocar credenciales reales o matar sesiones ajenas. |
| AJ-P08 — administración separada; V1.1 §8 y FIN-09 | Fixture migra usando usuario del clúster; settings general/constructor no son separación de secretos. Alternativas: migration LOGIN de ventana; owner NOLOGIN + deploy LOGIN efímero; credencial compartida. | Mantener inicialmente owner nominal de migración con autenticación solo de ventana revisada; futuro NOLOGIN+deploy requiere acta propia. Seed/provisioning y lectura de invariantes separados del runtime. Ningún servicio recibe credencial admin; no fallback a settings generales. Registrar quién provisiona, quién migra y quién revisa; doble control según política existente. | Configuración exclusiva por principal, pruebas de inaccesibilidad a material admin, sin rol heredado/SET ROLE, revocación de acceso temporal y ausencia de secretos en logs/argv. PG-T05/10/11. | DBA/recovery governor + seguridad. STOP si éxito runtime usa conexión admin, .env real, secretos en evidencia o break-glass ordinario. |
| AJ-P09 — firma y recuperación; D02, V1.1 §6, A02 §§6.2/6.5 propuesta | Wrapper no verifica firma/tiempos; compromiso executor excluido por D02. Ledger no rellena decision_id y no almacena grant_version. Alternativas: mantener verifier Python aislado; verifier DB revisado mediante nueva enmienda. | Mantener frontera D02 explícita, sin llamar «DB-verified signature» al wrapper. Evaluar enlace inmutable de ledger a decisión/grant-version para auditoría sin UPDATE de evidencia histórica. Replay usa identidad/hash, no token wire; status tras expiración/ambigüedad requiere diseño y permiso propio, sin crear endpoint S4 aquí. | Firma/material negativos antes de SQL; prueba de general-runtime sin EXECUTE; ledger/decisión/reserva/audit/budget atómicos, conflicto y replay sin doble efecto; grant revocado antes de primer uso deniega. PG-T02/07/08/09. | Dueño del contrato + seguridad + DBA. STOP si se exige resistencia a executor comprometido manteniendo Python-only, si se «rellena» historia o si falta recuperación aprobada para habilitar operación. |

AJ-P01 es una omisión de enforcement de ownership frente al modelo vigente;
no prueba que una DB desplegada tenga dueño incorrecto. AJ-P06 es una garantía
transaccional no establecida: la excepción de locks equivalentes de V1.1 no
ha sido demostrada en executor. Proponer correcciones mínimas y sus pruebas
no autoriza escribirlas. El aislamiento PG sigue `EVIDENCED_PARTIAL` en código
y **runtime no demostrado**, independientemente de los 4/4 históricos.

La autenticación de issuer no se resuelve con un simple GRANT: el ORM actual
usa lecturas completas de `IntegrationAPIKey` y grants. Una proyección de columnas
con solo hashes/estado/identidad requiere ajustar la consulta en un slice aprobado;
no dar SELECT amplio a credenciales legacy para conseguir un positivo.

## E. IPC Architecture Decision Matrix

### E.1 Artefactos y comparación

Solo hay interfaces Python llamadas por tests dentro del mismo proceso. Los
threads de tests financieros no son workers IPC. Los directorios del Host Lab
son placeholders DAC; el socket PG del verifier es una conexión de DB.
Búsqueda focalizada de AF_UNIX/SO_PEERCRED/socket/FIFO/broker/Celery/Redis y
callsites en financial/config/scripts no encontró transporte financiero.
HTTP V1.1 no es un endpoint existente ni autorización para crearlo.

| Alternativa | Autenticación/autorización e integridad | Entrega, fallos, aislamiento y costo | Adjudicación |
| --- | --- | --- | --- |
| UNIX pathname stream sockets, UIDs exclusivos | Peer kernel en ambos sentidos; DAC de directorio/socket más allow-list por operación; capability y hash material. UID no autoriza tenant. | Solo local; framing y límites propios; pérdida de conexión deja resultado ambiguo. systemd puede aislar servicios y dirs; cleanup por inode/manifest. No entrega durable intrínseca. | **Recomendada para siguiente slice local**, pendiente de aprobación y prueba con UIDs distintos. |
| HTTP/RPC con mTLS | Certificados de cliente/servidor y políticas por identidad; capability sigue necesaria para autorización financiera. TLS protege tráfico completo. | Sirve entre hosts, pero incorpora PKI, rotación, red y superficie de listeners; tampoco garantiza exactamente un efecto. | Alternativa si se aprueba topología distribuida. Loopback o HTTP sin auth no equivalen a mTLS. |
| Broker con TLS/mTLS y ACL de productores/consumidores | Identidades de conexión y cola, capability por mensaje; riesgo de acceso amplio del broker y secretos en mensajes retenidos. | Puede persistir y redeliver; deduplicación/ledger todavía necesarios. Requiere retención, DLQ, backpressure y cleanup de recursos propios; más operación. | No justificado por volumen/durabilidad existentes. No inventar Redis/Celery financieros. |
| Pipes heredados/FIFO/colas locales | Pipes heredados dependen de supervisor confiable; FIFO/colas requieren protocolo e identidad adicional. DAC solo no identifica y autoriza cada solicitud. | Acoplamiento de lifecycle, framing y correlación; ninguna idempotencia financiera implícita. | No elegidos: no artefactos ni ventaja demostrada para servicios separados persistentes. |
| Llamada Python actual | Identidad compartida del proceso, sin autenticación entre procesos. | Simple para test de lógica, sin aislamiento de clave/credencial. | No cumple la frontera operacional pendiente de D02. |

### E.2 Propuesta concreta pendiente de aprobación

```text
runtime AdminApps local --solicitud+credencial producer--> issuer aislado
issuer --capability+material verificado--> executor aislado --rol exclusivo--> PG
executor --resultado ligado a invocation/material--> issuer --> runtime solicitante
```

AJ-I01 recomienda relay directo issuer→executor para reducir quién puede enviar
capabilities al executor; relay por runtime es alternativa válida solo con
peer autorizado y binding completo. Runtime no obtiene SQL, signer ni credencial
executor. Issuer es cliente IPC del executor, no titular de su identidad DB.
Esta topología no implementa integración ISO Smart/MedSupplier ni HTTP financiero.

| Decisión / fuente | Riesgo y alternativas | Recomendación e implicaciones | Pruebas necesarias | Autoridad y STOP |
| --- | --- | --- | --- | --- |
| AJ-I01 — transporte/topología; D02 trust boundary, VM, IPC-C01 | Relay runtime amplía peers executor; broker/mTLS amplían operación. | UNIX pathname local y cadena anterior; confirmar mismo host. Si host remoto, volver a alternativa mTLS antes de implementar. | Control positivo cadena completa; runtime/intruso→executor denegados; sin fallback directo SQL. IPC-T01/04. | Arquitectura + seguridad + dueños de servicios. STOP si se asume canal existente o se abre endpoint sin permiso. |
| AJ-I02 — identidad, auth y autorización; D02, IPC-C02/03/06 | Nombre/GID/UID en payload no prueba peer; proceso con UID compartido también es ese principal. Sockets abstractos pierden el modelo pathname propuesto. | UIDs dedicados estables administrados (no números inventados), no compartidos con productos; SO_PEERCRED kernel en cliente y servidor y allow-list UID→endpoint→operación. Sin PID como identidad durable; prohibir transferencia de FD y revalidar autorización por solicitud. | Positivo peer previsto y servidor correcto; UID intruso con grupo permitido, UID textual falso, servidor sustituto, revocación y conexiones abiertas; comprobar que no haya procesos ajenos compartiendo UID, pues SO_PEERCRED no distingue su autoridad si comparten esa identidad. IPC-T01/02/03/08. | Seguridad + plataforma. STOP con UID compartido, UID reciclado sin reconciliar, auth por grupo solamente o endpoint reemplazable. |
| AJ-I03 — protocolo/integridad; D02 JSON/material, AJ-C01/02, IPC-C04/05 | Capability firma claims/hash, no el mensaje completo; correlation_id y respuesta no están firmados. JSON tolerante y parsing repetido crean semánticas distintas. | Un frame por request/response en conexión, longitud explícita, UTF-8 estricto y schema versionado; rechazar duplicados/unknown fields conforme C aprobado, sin SQL/rutas/FD. Issuer valida producer/grant, recompone hash de material y consistencia tenant; executor lo verifica y liga respuesta a invocation/hash. Transporte local confía en kernel/DAC/peers; no afirmar firma end-to-end de la respuesta. | Frames válidos, parciales, extras, oversize, profundidad, timeout, campos repetidos/alterados, respuesta mezclada; antes de DB, contador de despacho cero en rechazo. IPC-T04/05/07. | Dueño protocolo + seguridad + dueño financiero. STOP hasta fijar por acta tamaños/profundidad/deadlines/tipos y códigos; firma de respuesta o nuevo envelope requiere decisión de versión propia. |
| AJ-I04 — replay/entrega/recuperación; D02 ledger, V1.1 §6/10.5, IPC-C07/08 | Ni socket ni ACK prueban commit; token válido puede reenviarse. Alternativas: request síncrono + idempotencia DB; entrega durable con broker; endpoint status separado. | Síncrono, sin promesa de entrega durable ni exactly-once del transporte. Retries conservan invocation/hash, DB debe asegurar un efecto como máximo; no cache antireplay local sustitutiva. Desconexión posterior al envío = UNKNOWN; detener nuevo intento con identidad nueva. Status autenticado a futuro requiere slice separado; en lab registrar ambiguo y conservar evidencia. | Duplicado concurrente/conflictivo, respuesta perdida antes/después de commit, restart, capability expirada/revocada y retry agotado. IPC-T06/07/08 más PG-T08/09 para efecto financiero. | Dueño financiero + arquitectura + seguridad. STOP si UNKNOWN se convierte en rechazo que libera fondos o retry cambia identidad; no operación sin recuperación adjudicada. |
| AJ-I05 — least privilege/DAC/systemd; D02, HG como antecedente sintético | Compartir dirs, grupos o secretos debilita separación; hardening de sleep no acredita servicios reales. | Dirs separados administrados fuera del control de callers; server con escritura solo en su dir, peers solo traversal/conexión. Proponer 0710 para dir de servicio y socket 0660 con grupo específico de cada canal, ambos sujetos a prueba y propiedad administrada. Sin grupo global de confianza; allow-list sigue obligatoria. Issuer clave y lectura DB propia; executor solo públicas/DB propia; runtime ninguna de ambas. Unidades revisadas con User/Group, NoNewPrivileges, capacidades vacías y restricciones filesystem/namespaces/syscalls compatibles con binario real. | Cruces de lectura/escritura/rename/symlink denegados con controles positivos; acceso a secretos sintéticos por identidades distintas; cgroup/seccomp del servicio real en futuro, no del sleep previo. IPC-T03/09; PG-T10. | Plataforma + seguridad. STOP si modo rompe positivo y se abre world access, si SELinux unconfined se presenta como confinamiento o si se reusan cuentas históricas sin permiso. |
| AJ-I06 — fallos/lifecycle/cleanup; IPC-C08, HG manifest | Unlink previo arbitrario o PID reciclado destruye recurso ajeno; stop fallido no debe esconderse. Alternativas: ownership manifiesto propio; administración systemd de runtime dirs; limpieza por nombres. | Registrar run ID/path/tipo/dev/inode/owner antes/después de creación; rechazar colisiones/symlinks. Parar admisiones, cerrar listeners/clientes, esperar procesos propios, preservar resultados y verificar salida antes de unlink de recursos aún atribuibles. Si hay mismatch/stop fallido, conservar y declarar FAIL. No emitir cleanup PASS antes del inventario final. | Startup parcial, excepción, INT/TERM y simulación documentada de recuperación tras SIGKILL; proceso/socket vivo y colisión ajena; cleanup exitoso deja solo evidencia declarada. IPC-T07/10. | Plataforma + custodio de evidencia. STOP ante propiedad incierta, falta manifest, proceso vivo, cleanup global o borrado de artefactos ajenos. |

Los límites numéricos de frames, deadlines, concurrencia y rate-limit no están
en las fuentes. Se recomiendan límites finitos medidos con fixtures máximas y
aprobados en el contrato wire antes de codificar. No se han escogido a escondidas.
Lo mismo aplica a nombres/UIDs/path absolutos definitivos, retención y revocación.
Esta matriz está lista **para decidir**, no es un runbook ejecutable aprobado.

## F. Risk Register

Prioridades de revisión propuestas, sin CVSS ni probabilidad inventada. «Alto»
significa que bloquea la afirmación de aislamiento/activación; no afirma explotación.

| ID | Riesgo y evidencia | Prioridad / dueño propuesto | Tratamiento y residual |
| --- | --- | --- | --- |
| R-H01 | Pérdida de atribución host; testimonios y fixtures podrían mezclarse. | Alto gobernanza / custodio host | B/AJ-H01, export y declaración de retención; no cierre host. |
| R-C01 | Duplicados y múltiples wires por firma, discrepancia futura de parsers. | Alto antes de IPC / protocolo | AJ-C01; no signature forgery demostrada. |
| R-C02 | Material/tenant sin perfil común; issuer firma hash suministrado, executor no compara tenant assertion con claim. | Alto / dueño financiero | AJ-C02/I03, pruebas de binding; grant DB sigue siendo restricción independiente. |
| R-P01 | Owner implícito de `0006`, defaults/ACL/memberships sin catálogo. | Alto / DBA | AJ-P01/04/05; no afirmar despliegue vulnerable observado. |
| R-P02 | Trust y roles nominales tomados como credenciales aisladas; issuer sin identidad DB. | Alto / seguridad/DBA | AJ-P02/03/08, autenticación positiva/negativa por principal real. |
| R-P03 | SERIALIZABLE/retry no garantizados en executor y matriz de carreras incompleta. | Alto / financiero/DBA | AJ-P06 y PG-T09; locks existentes no se descartan, equivalencia pendiente. |
| R-P04 | Revocación parcial, sesiones abiertas y estado/evento no atómicos. | Alto / financiero/seguridad | AJ-P07; definir linealización y qué ocurre con trabajo en vuelo. |
| R-P05 | Ledger incompleto para trazabilidad directa de decisión/versión grant. | Medio / financiero/DBA | AJ-P09; probar reconciliación, no reescribir filas inmutables. |
| R-I01 | Ausencia de transporte, auth de peer, framing y recuperación. | Alto / arquitectura/plataforma | AJ-I01–I06 antes de prueba real; no endpoint creado. |
| R-I02 | Respuesta perdida/commit ambiguo puede causar reintento incorrecto. | Alto / financiero | Misma identidad; status futuro separado; operación no habilitada. |
| R-X01 | Harness PG elimina tras stop ignorado e imprime éxito antes de cleanup. | Alto para futuro ensayo / plataforma | Corregir harness bajo permiso posterior; verificar terminación antes de borrar. |
| R-G01 | V1.1 propuesta vs adopción posterior; A02 y D02 divergentes. | Alto gobernanza / dueño de contrato | Vincular acta a hash y alcance; no revocar ni asumir aprobación tácita. |
| R-T01 | Compromiso root/DBA/issuer/executor confiado. | Residual explícito / seguridad | D02 excluye esa protección; aprobar aceptación acotada o cambiar frontera mediante nueva decisión. |

## G. Requirements & Evidence Reconciliation

Fuentes y precedencia de lectura:

| Clave | Fuente | Uso y autoridad |
| --- | --- | --- |
| D02 | [Security Decision 02-A](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) | Registro HUMAN_APPROVED acotado; no autorización nueva runtime. |
| A02 | [Security Amendment 02](ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md) | APPROVAL_PENDING; DB-verifier/NOLOGIN/rechazo wire/HSM son propuestas. |
| V11/FIRM | `isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md` §§4–8/10; `ADMINAPPS_AI_FINANCIAL_AUTHORITY_IMPLEMENTATION_READINESS_2026-10-08.md` | Cabecera V11 propuesta, adopción posterior registrada en AdminApps. Conservar ambas y pedir acta/versionado; no editar ISO Smart. Hashes de tres fuentes ISO coinciden con OFF. |
| HG/HR/VM | [Gate](ADMINAPPS_AI_FINANCIAL_S3_ISOLATION_ADMINISTRATIVE_GATE_2026-10-09.md), [remediation](ADMINAPPS_AI_FINANCIAL_S3_SYSTEMCALLFILTER_VALIDATION_REMEDIATION_2026-10-09.md), [VM](ADMINAPPS_AI_FINANCIAL_S3_EXISTING_VM_ISOLATION_EXECUTION_2026-10-09.md) | Historial de laboratorio/fixtures; no trasladar a servicios financieros. |
| ER | [Execution report](ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md) | 4/4 PG reportados y estado parcial; «separately authenticated» queda acotado aquí a selección de identidad bajo trust, no secreto exclusivo probado. |
| REC/OFF | [Reconciliation previa](ADMINAPPS_AI_FINANCIAL_S3_GOVERNANCE_RECONCILIATION_2026-10-09.md), [OFF](ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json) | Historial de siete entregables y resultados offline; no reescribir sus hashes. |
| EVID | [Evidencia de esta adjudicación](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json) | Checks nuevos estáticos, preservación y copias atribuibles solo a archivos preexistentes. |

| Reconciliación previa / contrato | Implementación/evidencia real | Adjudicación actual y aceptación pendiente |
| --- | --- | --- |
| REC-H01–H05 / HG | Fuente coincide, OFF y 50 outputs recuperados; relato host persiste. | H01 bytes verificables; H02–H04 `EVIDENCED_PARTIAL`; H05 `SOURCE_INSUFFICIENT`. AJ-H01 exige procedencia/retención y revisión del dueño host. |
| REC-P03 / D02, A02 §6.2 | Mensaje firmado identificado; dos aceptaciones históricas; siete diagnósticos de representación. | `EVIDENCED_PARTIAL`; AJ-C01 listo para decidir. No elevar dos FAIL propuestos a defecto aprobado ni ocultarlos. |
| REC-P01/P02 / V11 §8, D02 | Ownership previo explícito, `0006` implícito, FORCE RLS/ACL fuente. | `EVIDENCED_PARTIAL`; AJ-P01/04/05 y catálogo/negativos necesarios. |
| REC-P04/X01 / V11 §§5.2/6 | Locks/ledger y ruta services; executor sin enforcement propio; 4/4 históricos de alcance limitado. | `EVIDENCED_PARTIAL`; AJ-P06/07/09 y matriz executor real antes de aceptar equivalencia/serialización. |
| REC-P05/P06 / D02 | Config inyectada y trust; sin issuer role/service ni credencial exclusiva operacional. | Aislamiento de autenticación `NOT_IMPLEMENTED` en harness; procesos reales no evidenciados. AJ-P02/03/08. |
| REC-I01/I02 / D02, VM | Interfaces Python y dirs DAC. | Transporte `NOT_IMPLEMENTED`; protocolo `SOURCE_INSUFFICIENT` hasta AJ-I01–I06/C01/C02 aprobados. Propuesta técnica lista no significa contrato vigente. |
| REC-P07/I03 / FIRM FIN-11 | Harness antiguo con gaps; sucesores no listos para runtime. | `PENDING_AUTHORIZATION` con prerrequisitos técnicos; no permiso solicitado para ejecutables aún inexistentes. |
| REC-G01/G02 / autoridad y cierre | Fuentes/versiones preservadas; aprobación final ausente. | `SOURCE_INSUFFICIENT` para acta V11; cierre `PENDING_AUTHORIZATION` y evidencia incompleta. Decision 02-A NOT CLOSED. |

FIN-01/02/03/08/09 se conservan sin recertificar S1/S2. FIN-04/06/11 enlazan las
decisiones PG/IPC; FIN-05 no autoriza tarifas reales. FIN-07/10/12 y S4–S6 no se
implementan. Phase31.5 y Phase32, contratos de otros productos, claves, servicios
y entornos permanecen sin cambios. Una decisión sobre pérdida histórica puede
cerrar una acción documental, nunca inventar prueba técnica ausente.

## H. Pruebas estáticas ejecutadas y resultados

| Comprobación nueva | Resultado | Alcance |
| --- | --- | --- |
| Rama y HEAD | PASS, rama esperada y HEAD previo | Identidad Git local, no aprobación de release. |
| Integridad de fuentes históricas | PASS 37/37; entregables referenciados 6/6; referencias externas 4/4 | Hashes comparados con OFF. Siete archivos del paquete anterior intactos incluyendo OFF. |
| AST Python | PASS 19 archivos | Parse sin imports, Django setup, bytecode ni ejecución del módulo. |
| `bash -n` individual | PASS 4 scripts | Host, regresión host y ambos verifiers; sin dispatch/source. |
| Diagnóstico JSON stdlib | PASS de 7 observaciones de igualdad/desigualdad y discrepancia de parsers | No firma, clave, petición ni conexión. No es PASS de rechazo estricto. Script reproducible en EVID. |
| Copias de outputs anteriores | PASS de roundtrip texto UTF-8/SHA para 50 archivos | Archiva contenido preexistente, no crea retrospectivamente logs. |
| Enlaces, whitespace y formato JSON de entregas | PASS | Links locales resueltos; `git diff --check` más check explícito de untracked. |
| Preservación final | PASS de baseline repository-local, branch/HEAD/index y fuentes referenciadas | Inventario/digests y cualquier diferencia en EVID; solo dos documentos nuevos previstos. |

No se repitieron 19/19 host ni 19/19 crypto; siguen como evidencia histórica.
PostgreSQL/IPC/Host Lab y suite Django: **NOT_RUN**, por alcance explícito. AST
no valida semántica SQL ni demuestra las recomendaciones de D/E. No se instalaron
herramientas ni se rebajó política para obtener un PASS.

## I. Estado Git y hashes

Rama: `hardening/p0-p1-enterprise-readiness`.
HEAD: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`.
Índice inicial vacío de cambios preparados; se conserva. Cero staging, commits,
pushes, merges o cambio de rama.

Estado previo conservado: `backend/config/settings.py` modificado y sin rastrear
financial app, scripts host/tests, ambos verifiers y `docs/financial/`. Esta tarea
agrega únicamente este dictamen A–J y EVID en `docs/financial/`. Los siete archivos
de la entrega precedente quedan intactos, no se recalculan sus manifiestos como
si correspondieran a una ejecución nueva.

EVID incluye hashes del alcance financiero, de las referencias leídas y de este
dictamen; no contiene secretos. El propio JSON se verifica por SHA entregado
fuera de él para evitar una referencia circular. La baseline completa de 15.519
archivos versionados/no ignorados se comparó al final; no certifica archivos
ignorados no inventariados ni sistemas externos. El artefacto temporal de control
está bajo `/tmp/adminapps-s3-adjudication-x61p7exc/`; no se usa su permanencia como
requisito de cierre: los resultados y hashes relevantes están en EVID.

## J. Next Human Approval Package

### J.1 Decisiones de arquitectura y gobernanza solicitadas

Las autoridades funcionales siguientes son candidatas basadas en FIN-08/09/11 y
D02; falta que el dueño del proyecto designe firmantes y registre su mandato.
Una casilla vacía **no es consentimiento**. La revisión puede aceptar, rechazar
o modificar cada opción; cualquier alternativa debe mantener trazabilidad.

| Acta propuesta | Selección técnica recomendada | Quién debe adjudicar | Registro pendiente |
| --- | --- | --- | --- |
| AJ-G01 | Vincular V1.1 aprobado a versión/hash; mantener D02 como remediación acotada y A02 pendiente. Resolver LOGIN/Python frente a NOLOGIN/DB sin mezclarlos. | Dueño del contrato financiero + seguridad + DBA | Firmantes, fecha, hashes, alcance y reservas: PENDING. |
| AJ-H01 | Aceptar clasificación `EVIDENCED_PARTIAL` y plan de recuperación/declaración de pérdida, sin cierre host. | Custodio host + gobernanza | Archivos aportados/no recuperables y aceptación de limitación: PENDING. |
| AJ-C01/C02 | C-B (wire estricto compatible) y esquema/material/binding tenant explícitos; decidir compatibilidad/versionado. | Dueño financiero + seguridad/protocolo | Perfil exacto, límites y vectores aprobados: PENDING. |
| AJ-P01–P05/P08 | Owner migration explícito; issuer/executor separados; executor LOGIN D02; peer local exacto o selección explícita SCRAM; RLS/ACL/admin mínimos. | DBA + seguridad + plataforma + dueño financiero | Autenticación elegida, matriz objeto/rol y provisión: PENDING. |
| AJ-P06/P07/P09 | SERIALIZABLE propio, retry con identidad estable, revocación transaccional y lifecycle por tipo de credencial; trust boundary Python y recuperación adjudicada. | Dueño financiero + DBA + seguridad | Orden locks, política de retry, sesiones en vuelo, evidencia/retención y status: PENDING. |
| AJ-I01–I06 | UNIX pathname local, relay issuer→executor, peer mutuo, protocolo acotado, sin garantía durable del canal y cleanup atribuible. | Arquitectura + seguridad + plataforma + dueño financiero | Topología, identidades, límites/códigos/deadlines, lifecycle y aceptación de riesgos: PENDING. |

Formato mínimo del acta: ID, opción elegida y desviaciones, fuente/hash, firmante
y mandato, fecha/zona, condiciones, riesgos aceptados y exclusiones. Una aceptación
de diseño no debe contener ni implicar permiso para modificar código o ejecutar.

### J.2 Autorizaciones posteriores, separadas de J.1

1. **Permiso de implementación local**: solo después de decisiones aplicables.
   Autorizar alcance exacto para parser/binding, migración correctiva, executor
   transaccional, issuer identity y harness/IPC. Preparar patch revisable, pruebas
   offline y runbooks. La presente solicitud autoriza documentos, no esos cambios.
2. **Permiso runtime PostgreSQL**: solo con patch/harness revisado y SHA, entorno
   sintético identificado, configuración sin secretos reales, comandos exactos,
   roles/auth acordados, PG-T01–11, captura de resultados y teardown verificable.
   El verifier actual con trust/cleanup insuficiente no está listo para esa firma.
3. **Permiso runtime IPC/host necesario**: solo con endpoints y unidades ya
   revisados, UIDs autorizados, paths/run manifest, comandos exactos, IPC-T01–10,
   evidencia y cleanup. No recrear Host Lab ni inferir permiso para cuentas o sudo.
   Integración DB requiere además el permiso anterior.
4. **Aceptación de evidencia y cierre**: revisión posterior de positivos,
   negativos, invariantes, fallos y recursos residuales, más adjudicación de gaps
   históricos. Solo la autoridad puede considerar cierre S3 con evidencia suficiente.

No se solicita hoy una autorización operativa genérica ni se inventan comandos
para código aún no implementado. Hasta las actas y permisos aplicables:
**STOP implementación PostgreSQL/IPC y cambios de política; S3 Decision 02-A
NOT CLOSED.** Deploy, producción, S4–S6, inferencia, credenciales reales y Git
commit/push siguen fuera del paquete.
