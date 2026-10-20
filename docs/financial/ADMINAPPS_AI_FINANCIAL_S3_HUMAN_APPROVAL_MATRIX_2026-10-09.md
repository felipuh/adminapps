# S3 — Human Approval Matrix

Fecha de preparación: 2026-10-09, America/Costa_Rica.
**19 decisiones propuestas; todas PENDING_HUMAN_APPROVAL.**
**S3_DECISION_02A_NOT_CLOSED**. No implementación ni runtime autorizados.

## Convención de trazabilidad

Cada ficha incluye el hash completo del contrato principal. Los códigos de
fuentes complementarias resuelven al [registro de rutas y SHA-256](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md#source-integrity).
ADJ es el dictamen original, EVID/OFF sus evidencias, PG/IPC las especificaciones;
CAP/EXE/ISS/AUTH/SVC son fuente Python; M0002–M0007 son migraciones históricas.
Una fuente propuesta no se vuelve normativa por figurar junto a D02.

Las pruebas de cada ficha son **requeridas para el slice futuro**, no ejecutadas
en esta preparación. PG-T01–11 e IPC-T01–10 mantienen su definición en [PG](ADMINAPPS_AI_FINANCIAL_S3_POSTGRESQL_ISOLATION_SPECIFICATION_2026-10-09.md)
y [IPC](ADMINAPPS_AI_FINANCIAL_S3_IPC_ISOLATION_SPECIFICATION_2026-10-09.md); se exige positivo sano y negativo atribuible. Los nuevos IDs
siguientes sirven para trazabilidad de esta propuesta. Ninguno cambia una
expectativa histórica sin acta. Un fallo de conexión no prueba ACL/RLS/peer.

## Catálogo documental, crypto y material

| ID | Positivo futuro | Negativo futuro / criterio observable |
| --- | --- | --- |
| DOC-T01 | Acta identifica fuente/hash, firmante/mandato, decisión/alcance, fecha y reservas. | Propuesta, firma PENDING, hash distinto o aprobación de diseño usada como runtime: gate permanece cerrado. |
| DOC-T02 | Export host existente con procedencia o declaración explícita de límites/pérdida. | Nombre/mtime/testimonio/fixture sin atribución no certifica run o cleanup. |
| CR-T01 | Token normal del emisor actual y vector fijo conservan los bytes de mensaje/firma y claims. | Variación de dominio/algoritmo/claims no pasa como compatibilidad v1. |
| CR-T02 | Wire sorted/compact ASCII único aceptado. | Whitespace, orden, escapes equivalentes, base64 alternativo/padding: denegación tipada antes de DB. |
| CR-T03 | Objeto con 19 claves únicas aceptado. | Duplicado idéntico/conflictivo en ambas posiciones y clave escapada decodificada: rechazo, sin elegir primer/último valor. |
| CR-T04 | Tipos/perfiles aprobados exactos y límites frontera válidos. | Bool por int, float/null, NaN/Infinity, faltantes/extras, UUID/tiempos/identificadores inválidos: rechazo. |
| CR-T05 | UTF-8/base64url y tamaños dentro de límites aprobados. | UTF-8/base64 inválido, segmentos extra, exceso de longitud/profundidad: rechazo acotado. |
| CR-T06 | Firma/key/iss/aud/env/op/tiempo correctos. | Alteración, key no permitida/retirada, otro contexto, futuro/caducado: conexión DB cero; no afirmar revocación operacional desde mock. |
| MT-T01 | Material normal y evidence_ids según orden vigente conservan hash conocido. | Cambio silencioso de esquema/serialización rompe vector y bloquea cambio. |
| MT-T02 | Assertion y claim organization iguales, producto/contexto autorizados. | Mismatch, assertion incompleto/tipo incorrecto, material sustituido: cero conexión DB. |
| MT-T03 | Perfil material aprobado, unidades/identificadores/assertion válidos. | No finitos, bool/float donde int, límites fuera de rango, campos desconocidos o entorno/operación incorrectos: denegación segura. |

CR/MT se probarían offline con contador/doble de DB; runtime posterior confirma
la misma ruta. Para negativos posteriores al inicio de SQL, probar invariantes y
rollback según caso, no exigir conexión cero artificialmente. Las denegaciones
financieras auditables siguen el contrato aprobado; rechazo crypto no debe llegar
a SQL. Las sondas históricas preservan sus resultados originales.

## AJ-G01 — Autoridad y precedencia

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §1/12; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`; [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Decision; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: A01, A02 §1/6, FIRM FIN-08/09/11; ADJ G/J; ER autoridad. |
| Situación comprobada | V11 dice propuesta; AdminApps registra adopción posterior. D02 registra HUMAN_APPROVED acotado; A02 sigue APPROVAL_PENDING. |
| Riesgo | Mezclar versiones puede autorizar DB-verifier/NOLOGIN o trabajo no concedido. |
| Alternativas disponibles | Vincular acta original a hash y reservas; emitir ratificación explícita; revisar frontera mediante nueva enmienda. Aprobación tácita no válida. |
| Recomendación técnica | Vincular adopción V11 a acta/versionado, conservar LOGIN/Python D02 y A02 pendiente. |
| Seguridad y compatibilidad | Preserva autoridad histórica sin ampliar permisos ni borrar contradicción documental. |
| Cambios que requeriría | Acta nueva o export de acta existente con mandato y hashes; sin editar ISO Smart. Resolver B-T01 al definir la frontera de transporte. |
| Pruebas positivas y negativas | Positivo: DOC-T01: cada aprobación tiene fuente, hash, mandato, alcance y fecha efectiva. Negativo: DOC-T01: documento de propuesta, hash distinto, firma vacía o permiso runtime inferido no habilita slice. |
| Riesgo residual | Autenticidad de actas requiere custodio; un hash no la acredita. |
| Autoridad funcional competente | Dueño del contrato + seguridad + DBA; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-G01; acta/versionado o mandato sin resolver; cualquier mezcla automática D02/A02. |

## AJ-H01 — Evidencia host parcial

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Threat boundary and residual risk; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: ADJ B; EVID; OFF; HG/HR/VM/HC. |
| Situación comprobada | Fuente host coincide; EVID conserva 50 outputs sin atribución suficiente. Transcript primario del run exitoso no localizado en el alcance previo. |
| Riesgo | Testimonio, fixtures y salidas no atribuidas pueden confundirse con prueba de aislamiento/cleanup. |
| Alternativas disponibles | Aportar export existente con procedencia; declarar retención/pérdida y aceptar límite; nueva prueba solo bajo permiso futuro separado. |
| Recomendación técnica | Mantener EVIDENCED_PARTIAL y obtener declaración del custodio; no repetir Host Lab en este paquete. |
| Seguridad y compatibilidad | Conserva bytes e historia, sin transformar relatos en evidencia primaria. |
| Cambios que requeriría | Solo documentos nuevos de custodia/retención; ningún acceso a /root, journal, backups o recursos privilegiados autorizado aquí. |
| Pruebas positivas y negativas | Positivo: DOC-T02: export existente identifica origen, SHA, run y límites, o declaración identifica qué se conserva/no recuperó. Negativo: DOC-T02: stdout vacío, nombre/mtime, fixture CLEANUP_COMPLETE o hash actual sin atribución no prueba el run. |
| Riesgo residual | Evidencia original puede no recuperarse; aceptación documental no certifica operación. |
| Autoridad funcional competente | Custodio host + gobernanza; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-H01; atribución inventada, pérdida global afirmada sin fundamento o cierre host por aceptación de testimonio. |

## AJ-C01 — Wire criptográfico C-B

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Decision; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: A02 §6.2 pendiente; ADJ C; CAP; CRTEST; OFF. |
| Situación comprobada | Verifier parsea y reserializa; acepta variantes equivalentes. Dos sondas históricas aceptadas no demuestran falsificación; no hay segundo consumidor financiero probado. |
| Riesgo | Duplicados permiten semánticas distintas entre parsers; tipos y límites incompletos. |
| Alternativas disponibles | C-A parse/re-serialize sin duplicados; C-B wire único del emisor; C-C nuevo protocolo/versionado; C-D conservar conducta actual. |
| Recomendación técnica | C-B: rechazar duplicados decodificados, wire/base64 no único y tipos incompatibles; conservar 19 claims, Ed25519 y dominio. |
| Seguridad y compatibilidad | Compatible con tokens normales actuales; aceptación se estrecha explícitamente. No JCS/JWT ni cambio de mensaje firmado implícito. |
| Cambios que requeriría | S3-IMP-01: parser y esquema aprobados en CAP, vectores CRTEST; inventario de consumidores y criterio de errores antes de DB. |
| Pruebas positivas y negativas | Positivo: CR-T01/06: tokens actuales y vectores fijos conservan mensaje y firma; tiempo válido y bindings autorizados. Negativo: CR-T02–05/06: duplicados idénticos/conflictivos/escapados, whitespace/orden, tipos, no finitos, UTF-8/base64/tamaño, firma/key/aud/iss/env/op/tiempo; conexión DB cero. |
| Riesgo residual | Emisor/clave comprometidos continúan frontera confiada; consumidores desconocidos pueden requerir transición. |
| Autoridad funcional competente | Dueño financiero + seguridad/protocolo; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-C01; perfil/límites/versionado no aprobados, mensaje firmado cambiado, doble parser ambiguo o FAIL histórico renombrado PASS. |

## AJ-C02 — Material y binding tenant

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §4/6; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`; [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Decision; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: ADJ C.2/C.3; EXE; SVC; ISS; AUTH. |
| Situación comprobada | Executor recomputa hash pero no compara explícitamente assertion.adminapps_tenant_id con claim organization; issuer recibe hash sin material. |
| Riesgo | Material consistente consigo mismo puede no estar ligado al tenant firmado; validar forma no prueba origen de proyección. |
| Alternativas disponibles | Perfil mínimo y comparación explícita; adaptar issuer a material completo; nuevo esquema/hash versionado si se necesita cambiar semántica. |
| Recomendación técnica | Aprobar perfil material y comparar assertion/organization antes de DB; recomputación del issuer en adaptador futuro explícitamente aprobada. |
| Seguridad y compatibilidad | Mantener bytes/hash históricos normales, evidencia IDs ordenados y grant DB independiente. No adoptar claims adicionales de A02. |
| Cambios que requeriría | S3-IMP-01 EXE/SVC y validación compartida; S3-IMP-05 adaptador ISS. Sin integración ISO Smart ni modificación silenciosa de hashes. |
| Pruebas positivas y negativas | Positivo: MT-T01/03: material conocido mantiene hash, assertion/claim coinciden y contexto permitido. Negativo: MT-T02/03: tenant distinto, assertion incompleto/tipo inválido, material sustituido, límites inválidos; cero conexión/efecto DB. |
| Riesgo residual | Procedencia de TenantProjection no queda autenticada por igualdad; requiere integración posterior fuera de alcance. |
| Autoridad funcional competente | Dueño financiero + seguridad/protocolo; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-C01; confundir binding con autorización de grant, cambiar hash/versionado o asumir validación remota de proyección. |

## AJ-P01 — Ownership explícito

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §8; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`; [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Database boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: ADJ D; M0002/M0003/M0006; PG-R02. |
| Situación comprobada | 0002/0003 asignan owner; 0006 omite ALTER OWNER para grants, eventos y ledger. No se observó catálogo vivo. |
| Riesgo | Tablas creadas por bootstrap pueden quedar bajo dueño no previsto. |
| Alternativas disponibles | Migración correctiva posterior; creación bajo migration con precondiciones; owner implícito (no recomendado). Estrategia de historial nunca aplicado requiere acta. |
| Recomendación técnica | Owner explícito adminapps_financial_migration en las 15 tablas; conservar FORCE RLS y triggers. |
| Seguridad y compatibilidad | Separa tablas de funciones y servicios; no necesita BYPASSRLS. Administración bajo FORCE RLS debe tener ruta aprobada. |
| Cambios que requeriría | S3-IMP-02 nueva migración posterior y precondiciones; no editar 0002–0007 ni reparar owner ocultamente en tests. |
| Pruebas positivas y negativas | Positivo: PG-T04/05/06: catálogo de 15 tablas/auxiliares y migración con principal aprobado. Negativo: PG-T05: owner inesperado detiene run; runtime/executor sin ALTER OWNER/POLICY/DDL ni SET ROLE elevado. |
| Riesgo residual | El plano migration puede alterar DDL; queda gobernado fuera del runtime. |
| Autoridad funcional competente | DBA + dueño financiero; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-P01; owner efectivo desconocido/inválido, falta ruta administrativa o corrección de catálogo durante prueba. |

## AJ-P02 — Principales separados

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Database boundary/Threat boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: A02 §6.3 pendiente; ADJ D; M0006/M0007; ISS/AUTH/INTSVC/INTMODEL. |
| Situación comprobada | Executor LOGIN exigido por D02; issuer sin rol DB propio; ORM consulta objetos de credenciales/grants. |
| Riesgo | Shared UID/DSN o SELECT amplio expone capacidad de firma/ejecución y datos legacy. |
| Alternativas disponibles | Executor LOGIN exclusivo; login + rol NOLOGIN con SET ROLE (requiere revisar D02); identidad fusionada (incompatible con separación). |
| Recomendación técnica | LOGIN executor D02 y login issuer independiente con proyección mínima de hash/estado/identidad/registro/grant; sin EXECUTE de admisión ni escrituras. |
| Seguridad y compatibilidad | Preserva verificación Python y evita dar privilegios admin para cubrir necesidades ORM. UID separado del runtime para cada servicio. |
| Cambios que requeriría | S3-IMP-03 conexión/consulta exclusiva y plantilla de provisión; nombre final issuer y cuentas PENDING. No provisionar aún. |
| Pruebas positivas y negativas | Positivo: PG-T01/02/10: issuer autentica hashed_v1 y lee grant con su principal; executor ejecuta wrapper sin leer tablas. Negativo: PG-T02/05/10: issuer no admite/escribe grant/lee legacy; executor no firma; runtime no obtiene identidades; inspeccionar memberships transitivos. |
| Riesgo residual | Issuer y executor comprometidos excluidos por D02; hashes de credenciales también son material sensible. |
| Autoridad funcional competente | Seguridad + DBA + dueños de servicios; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-P01; credencial/UID compartido, issuer inexistente tratado como real o proyección resuelta con conexión general/admin. |

## AJ-P03 — Autenticación DB real

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Decision/Threat boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: ADJ D AJ-P03; PG-R01; PGSCRIPT. |
| Situación comprobada | Verifier usa --auth=trust; demuestra selección de rol/ACL, no exclusividad de credencial. |
| Riesgo | Un rol nominal puede ser solicitado por principal no autorizado; fixture de un UID no prueba peer aislado. |
| Alternativas disponibles | Peer local exacto; SCRAM-SHA-256 con secreto distinto por principal; cert/mTLS si topología remota; trust solo antecedente. |
| Recomendación técnica | Peer con mapping exacto para topología local confirmada, socket privado sin TCP. SCRAM si política exige contraseña o peer no aplica. |
| Seguridad y compatibilidad | Sin password compartido bajo peer; no confundir peer DB con SO_PEERCRED IPC. Ensayo literal de password exige perfil SCRAM propio. |
| Cambios que requeriría | S3-IMP-03/06 HBA/map y rutas sintéticas; data directory privado separado del socket accesible por UIDs aprobados (B-D01). |
| Pruebas positivas y negativas | Positivo: PG-T01/10: cada UID conecta al rol propio; SELECT de salud y session_user/current_user observados. Negativo: PG-T01/10: otro UID solicita executor y falla; mapping ajeno/login retirado falla; SCRAM elegido prueba password erróneo. Sin fallback trust. |
| Riesgo residual | Compromiso del UID o control plane; pool/sesiones abiertas necesitan AJ-P07. |
| Autoridad funcional competente | DBA + seguridad + plataforma; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-P01/B-D01; topología remota para peer, mapping genérico, socket inaccesible al positivo, mismo UID o abrir datos para hacer pasar prueba. |

## AJ-P04 — RLS y tenants

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §8; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`; [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Database boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: ADJ D; M0002–M0007; PG-R05. |
| Situación comprobada | FORCE RLS y políticas fuente presentes; función central con grants; GUC app.tenant_id controlable por sesión. |
| Riesgo | Confundir ACL, filtrado RLS y autorización de tenant; usar GUC como identidad. |
| Alternativas disponibles | Funciones centrales con grants y políticas por rol; contexto tenant autenticado rediseñado; tablas por GUC (no suficiente). |
| Recomendación técnica | Preservar ENABLE/FORCE, triggers y política central admission; políticas SELECT issuer específicas y auditoría central gobernada. |
| Seguridad y compatibilidad | Grant/capability autorizan admisión; GUC no reemplaza autenticación. Inventariar SELECT históricos runtime sin restaurar writes. |
| Cambios que requeriría | S3-IMP-02 matriz tabla/rol/operación, políticas issuer y lectura auditor de tablas nuevas bajo aprobación. |
| Pruebas positivas y negativas | Positivo: PG-T03/04: A y B acceden solo según contrato; auditor autorizado obtiene alcance documentado; issuer lee proyección permitida. Negativo: PG-T03/04: A sin grant B, no-context/GUC falso, UPDATE/DELETE/TRUNCATE/RLS disable; SQLSTATE/filtrado/trigger distinguibles. |
| Riesgo residual | Superuser y propietario DDL no están contenidos por RLS; separación administrativa esencial. |
| Autoridad funcional competente | DBA + seguridad + dueño financiero; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-P01; retirar FORCE/trigger, copiar USING(true) a runtime o contar caída DB como prueba de RLS. |

## AJ-P05 — Privilegios por objeto y creador

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Database boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`; [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §8; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`. Evidencia/complementos: ADJ D; M0005/M0007; PG-R06/07. |
| Situación comprobada | Wrapper executor restringido en fuente; defaults/schema/CONNECT/TEMP y memberships efectivos no evidenciados. |
| Riesgo | Escalamiento por SET ROLE, objetos futuros o sombra en schemas confiables. |
| Alternativas disponibles | Allow-list por objeto/creador; defaults implícitos (insuficientes); nuevo schema financiero si se aprueba necesidad. |
| Recomendación técnica | Executor CONNECT necesario, USAGE public y EXECUTE solo wrapper; admission NOLOGIN dueño de funciones; ACL/defaults mínimos. |
| Seguridad y compatibilidad | NOINHERIT no prueba ausencia de SET ROLE; fijar resolución y controlar CREATE/TEMP, funciones auxiliares y UPDATE usados para locks. |
| Cambios que requeriría | S3-IMP-02 migración posterior/manifest SQL; revisiones por creador y matrices de lectura/escritura; sin mover schema por conveniencia. |
| Pruebas positivas y negativas | Positivo: PG-T02/05/06: wrapper y funciones internas necesarias funcionan con permisos exactos; objetos sintéticos nuevos nacen con ACL prevista. Negativo: PG-T02/05/06: runtime no invoca legacy/wrapper, executor no legacy/tablas; PUBLIC/SET ROLE/DDL/sombra TEMP/public denegados o ineficaces según contrato. |
| Riesgo residual | Cambios futuros de esquema/creador necesitan revalidación; no se observó vulnerabilidad runtime. |
| Autoridad funcional competente | DBA + seguridad; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-P01; PUBLIC EXECUTE, schema escribible influyente, owner runtime o membership administrativo. |

## AJ-P06 — Transacción SERIALIZABLE y retry

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §5.1/5.2/6; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`. Evidencia/complementos: D02 Decision; ADJ D; EXE/SVC; FIRM FIN-04/06; PG-R04. |
| Situación comprobada | Executor no establece aislamiento/retry; otra ruta services sí. Equivalencia de locks no probada en executor. |
| Riesgo | Carreras de presupuesto/estado y retry con identidad nueva pueden producir efectos indebidos. |
| Alternativas disponibles | Transacción explícita; default de conexión con guard comprobado; locks equivalentes con prueba de invariante exigida por V11. |
| Recomendación técnica | SERIALIZABLE propio en alias executor antes de SQL, verificado; retry completo de 40001 tras rollback, acotado. Política explícita 40P01. |
| Seguridad y compatibilidad | Misma invocation/hash, nueva verificación capability/tiempos y grant en cada intento. Commit confirmado antes de éxito; cierre de conexión no confirma commit. |
| Cambios que requeriría | S3-IMP-04 EXE, pruebas, wrapper posterior solo si necesario; resolver alias/conexiones por principal. Orden total propuesto grant → identidad → registro → policy/tariff → budgets global/product/UUID, revisar todas las rutas. |
| Pruebas positivas y negativas | Positivo: PG-T07/08/09: aislamiento real y concurrencia independiente, un efecto por identidad y límites de todos los scopes. Negativo: PG-T09: carreras policy/tariff/entitlement/grant, 40001, 40P01, agotamiento/rollback; retry expirado deniega sin nuevo efecto; commit ambiguo UNKNOWN. |
| Riesgo residual | Abortos afectan disponibilidad; serialización no autentica peer ni recupera respuesta perdida. |
| Autoridad funcional competente | Dueño financiero + DBA + seguridad; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-P01; retries/deadlines u orden no aprobados, aislamiento externo supuesto, cambiar invocation o tratar error de commit como rollback confirmado. |

## AJ-P07 — Revocación coherente

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Database boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`; [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §3.1/6; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`. Evidencia/complementos: ADJ D; ISS transición; M0007; A02 lifecycle pendiente. |
| Situación comprobada | Transición grant guarda estado/versión y evento sin atomic propio; login, key y peer son controles distintos. |
| Riesgo | Estado/evento divergentes; creer que nuevo password/NOLOGIN elimina sesiones ya abiertas. |
| Alternativas disponibles | Corte de conexiones nuevas; drenaje con frontera; terminación selectiva administrativa autorizada. Snapshot permanente no aceptable. |
| Recomendación técnica | Estado+versión+evento en una transacción bloqueando el mismo grant; commit fija corte. Política separada por key/credencial/peer y trabajo en vuelo. |
| Seguridad y compatibilidad | Admisión anterior al corte conserva historia. Revalidar key/peer por solicitud; no equiparar revocación producer, key issuer, grant y DB. |
| Cambios que requeriría | S3-IMP-04 atomicidad/locks y S3-IMP-06 lifecycle; gobernar transición con principal administrativo, sin dar writes de grant al issuer lector. |
| Pruebas positivas y negativas | Positivo: PG-T07/10, IPC-T08: credenciales activas funcionan antes del corte; resultado en vuelo coincide con política. Negativo: PG-T07/09/10: crash intermedio, grant viejo/revocado/suspendido; login nuevo denegado; sesión previa observada; key/peer retirados deniegan nueva solicitud. |
| Riesgo residual | Trabajo autorizado antes del corte y demora de propagación requieren límite aprobado y aceptación explícita. |
| Autoridad funcional competente | Financiero para grants; seguridad/DBA para keys/logins; plataforma para peers; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-P01; estado/evento divergentes, allow-list indefinida, revocar credenciales reales o terminar sesiones ajenas. |

## AJ-P08 — Administración separada

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §8/9; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`. Evidencia/complementos: D02 Threat boundary; ADJ D; FIRM FIN-09; PGSCRIPT. |
| Situación comprobada | Fixture migra como usuario de clúster; settings/constructor no acreditan aislamiento de administración. |
| Riesgo | Servicio usa privilegio admin o material administrativo; break-glass ordinario sin trazabilidad. |
| Alternativas disponibles | Migration LOGIN de ventana; owner NOLOGIN + deploy LOGIN efímero mediante acta propia; credencial compartida (descartada). |
| Recomendación técnica | Owner nominal migration con autenticación solo de ventana; seed/inspección distintos del principal que demuestra autorización. |
| Seguridad y compatibilidad | Conserva modelo actual sin inventar rol deploy aprobado; no fallback a configuración general ni BYPASSRLS para operar. |
| Cambios que requeriría | S3-IMP-02/03/06 plantillas de provisión, ruta FORCE RLS y revocación temporal; asignación de operadores/revisores PENDING. |
| Pruebas positivas y negativas | Positivo: PG-T05/10/11: migración/seed revisados, servicios operan con identidad propia, inspector registra invariantes sin causar el positivo. Negativo: PG-T05/10/11: servicio no lee material admin/no SET ROLE; acceso temporal retirado; logs/argv sin secretos. |
| Riesgo residual | Plano administrador conserva poder elevado; exige gobernanza y auditoría. |
| Autoridad funcional competente | DBA/recovery governor + seguridad; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-G01/B-P01; admin produce éxito runtime, uso de .env real o secretos en evidencia. |

## AJ-P09 — Frontera de firma, ledger y recuperación

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Decision/Database boundary/Threat boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`; [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §6/10.5; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`. Evidencia/complementos: ADJ D; EXE/M0006/M0007; A02 §6.2/6.5 pendiente. |
| Situación comprobada | DB recibe escalares, no firma/exp/nbf; ledger no rellena decision_id ni guarda grant_version. |
| Riesgo | Prometer DB-verifier inexistente; falta enlace auditable o recuperación después de expiración/ambigüedad. |
| Alternativas disponibles | Python aislado D02; nueva enmienda con verifier DB; enlace inmutable nuevo versus UPDATE histórico (no permitido). |
| Recomendación técnica | Mantener Python D02; diseñar vínculo de decisión/grant_version para nuevas admisiones y reconciliación de historia sin reescritura. |
| Seguridad y compatibilidad | Replay por tupla de identidad/hash, nunca token wire. Expirada/revocada no habilita nueva admisión; consulta de estado necesita permiso propio. |
| Cambios que requeriría | S3-IMP-04 migración posterior/wrapper/ledger solo tras diseño aprobado; contrato de UNKNOWN y evidencia de inspector en lab, sin endpoint status o S4. |
| Pruebas positivas y negativas | Positivo: PG-T07/08/09: ledger/decisión/reserva/audit/budgets atómicos, replay mismo resultado, reconciliación exacta. Negativo: PG-T02/08/09: firma/material falla antes de SQL; runtime sin EXECUTE; conflicto/capability expirada/respuesta perdida sin nuevo efecto. |
| Riesgo residual | Executor comprometido permanece confiado; recuperación operativa ausente bloquea habilitación. |
| Autoridad funcional competente | Dueño del contrato + seguridad + DBA; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-R01; exigir resistencia a executor comprometido manteniendo Python-only, rellenar historia o equiparar inspector de laboratorio con status productivo. |

## AJ-I01 — Transporte y relay

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Threat boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`; [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §3.2/10; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`. Evidencia/complementos: ADJ E; VM; IPC-C01. |
| Situación comprobada | Solo llamadas Python; no sockets financieros, HTTP, broker o workers acreditados. |
| Riesgo | Asumir IPC existente o rebajar TLS productor sin decisión; topología distribuida incompatible con propuesta local. |
| Alternativas disponibles | UNIX pathname local; HTTP/RPC mTLS remoto; broker autenticado durable; pipes/FIFO. Relay issuer directo o runtime autorizado. |
| Recomendación técnica | Mismo host Linux con UNIX pathname; runtime → issuer → executor → issuer → runtime; executor admite peer issuer exclusivamente. |
| Seguridad y compatibilidad | Reduce peers del executor; capability conserva autorización financiera. Resolver B-T01: frontera interna o excepción a TLS expresamente versionada. |
| Cambios que requeriría | S3-IMP-05 adaptadores futuros, sin endpoint HTTP ni cambio ISO/MedSupplier. Confirmación de host y exposición de credencial producer PENDING. |
| Pruebas positivas y negativas | Positivo: IPC-T01/04: cadena autorizada completa y respuesta ligada; ambos servidores autenticados. Negativo: IPC-T01/04: runtime/intruso directo a executor denegado; sin fallback SQL, HTTP o broker. |
| Riesgo residual | Kernel y peers confiados; respuesta local no firmada end-to-end ni entrega durable. |
| Autoridad funcional competente | Arquitectura + seguridad + dueños de servicios/contrato; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-I01/B-T01; host remoto, TLS sustituido tácitamente, endpoint existente supuesto o servicio expuesto sin permiso. |

## AJ-I02 — Identidad kernel y allow-list

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Threat boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: ADJ E; IPC-C02/06/07. |
| Situación comprobada | No cuentas operativas ni autenticación mutua implementadas; nombres de Host Lab solo históricos. |
| Riesgo | UID en JSON, grupo o UID compartido pueden confundirse con principal autorizado. |
| Alternativas disponibles | UID dedicado estable + peer kernel; identidad alternativa mTLS bajo decisión remota; DAC de grupo solo (insuficiente). |
| Recomendación técnica | SO_PEERCRED en cliente y servidor; UID exclusivo → endpoint → operación; revalidar autorización en cada solicitud. |
| Seguridad y compatibilidad | PID no identidad durable; prohibir transferencia de FD. UID compartido identifica el mismo principal, no distingue autoridad de procesos. |
| Cambios que requeriría | S3-IMP-05 resolución de identidad y allow-list; S3-IMP-06 unidades. Si se propone socket activation, revisar qué peer observa realmente el cliente. |
| Pruebas positivas y negativas | Positivo: IPC-T01/02/03: UID kernel y servidor previstos, operación permitida; sin procesos ajenos con la misma identidad. Negativo: IPC-T02/03/08: UID textual falso, grupo correcto/UID incorrecto, servidor sustituto, allow-list revocada y conexión previa. |
| Riesgo residual | Compromiso/reutilización del UID o descriptor requiere controles de lifecycle y plataforma. |
| Autoridad funcional competente | Seguridad + plataforma; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-I01; UID compartido/reciclado sin reconciliar, allow-list solo de grupos o autenticación del servidor no comprobada. |

## AJ-I03 — Contrato de frames e integridad

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Decision; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`; [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §4/6; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`. Evidencia/complementos: ADJ E; IPC-C04/05/06; AJ-C01/C02. |
| Situación comprobada | JSON de transporte, límites y respuesta no definidos. Capability no firma correlation_id ni respuesta completa. |
| Riesgo | Parsing divergente, consumo no acotado, mezcla de respuestas o despacho parcial. |
| Alternativas disponibles | Frame explícito único por conexión; protocolo persistente/múltiple con revisión adicional; nuevo envelope firmado versionado si se necesita. |
| Recomendación técnica | Un request/response por conexión con longitud explícita, UTF-8/schema versionado, límites finitos y campos permitidos; issuer recomputa material, executor valida/bindea. |
| Seguridad y compatibilidad | Reutiliza C-B y esquema material aprobados; respuesta ligada a invocation/hash. Kernel/DAC/peer aportan integridad local, no firma end-to-end. |
| Cambios que requeriría | S3-IMP-05 parser/adaptadores y errores; width/endian de longitud, códigos, bytes, profundidad, deadlines y concurrencia PENDING. |
| Pruebas positivas y negativas | Positivo: IPC-T04/05/07: frame válido acotado y hash/identidad respuesta coincidentes; servidor sigue sano. Negativo: IPC-T04/05/07: truncado/extra/oversize/duplicado/profundidad/timeout/campo desconocido, mezcla respuesta; contador despacho cero antes de DB. |
| Riesgo residual | Recurso agotado/DoS requiere límites y observabilidad medidos; peer comprometido sigue residual. |
| Autoridad funcional competente | Dueño protocolo + seguridad + dueño financiero; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-C01/B-I01; números/tipos/códigos sin aprobar, doble parser o firma/respuesta/claim nuevo sin versión. |

## AJ-I04 — Entrega, replay y UNKNOWN

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Database boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`; [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) §6/10.5; SHA-256 `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f`. Evidencia/complementos: ADJ E; IPC-C07/08; PG-T08/09. |
| Situación comprobada | No protocolo de transporte/status; ledger/identidad DB existentes requieren pruebas ampliadas. |
| Riesgo | ACK o caída confundidos con commit/rechazo; nueva identidad duplica exposición. |
| Alternativas disponibles | Síncrono + idempotencia DB; broker durable con deduplicación; status autenticado futuro por slice separado. |
| Recomendación técnica | Síncrono, a lo sumo un efecto financiero por identidad probado en DB; desconexión posterior al envío UNKNOWN. |
| Seguridad y compatibilidad | Retry permitido conserva invocation/hash y revalida permiso/tiempo; ante commit ambiguo detener automatismo y reconciliar. No liberar ni despachar por incertidumbre. |
| Cambios que requeriría | S3-IMP-04/05 clasificación de resultados y fault hooks; lab observa DB mediante inspector autorizado. Recuperación operativa sigue bloqueada, sin S4/status. |
| Pruebas positivas y negativas | Positivo: IPC-T06, PG-T08: duplicado autorizado converge al resultado original, una reserva. Negativo: IPC-T06/07/08, PG-T09: duplicado conflictivo, respuesta perdida antes/después de commit, restart, expiración/revocación/agotamiento sin segunda identidad ni release. |
| Riesgo residual | Canal no durable; outage puede mantener UNKNOWN. Sin recuperación aprobada no se habilita operación. |
| Autoridad funcional competente | Dueño financiero + arquitectura + seguridad; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-R01; UNKNOWN mapeado a denegación/liberación/éxito, retry ciego o nuevo invocation. |

## AJ-I05 — DAC y hardening real

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Threat boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: ADJ E; HG/VM; IPC-C03; PG-T10. |
| Situación comprobada | Host Lab probó placeholders/sleep según reportes; no servicios financieros reales. |
| Riesgo | Grupos/directorios compartidos exponen endpoints/secretos; hardening sintético no prueba binario real. |
| Alternativas disponibles | Dirs/grupos por canal; ACL equivalente revisada; grupo global o world access (no aceptables). |
| Recomendación técnica | Dirs administrados fuera de control callers, servidor escribe solo su dir; candidatos 0710 dir/0660 socket por canal sujetos a prueba; unidades dedicadas. |
| Seguridad y compatibilidad | Peer allow-list obligatoria aunque DAC permita. Issuer firma/lee DB propia, executor públicas/DB propia; runtime sin material de ambos. |
| Cambios que requeriría | S3-IMP-06 plantillas User/Group, NoNewPrivileges, capacidades vacías y restricciones compatibles; paths/UIDs/modos finales por acta. No desplegar. |
| Pruebas positivas y negativas | Positivo: IPC-T03/09, PG-T10: peers legítimos funcionan y cada servicio consume solo material propio; restricciones observadas en procesos reales futuros. Negativo: IPC-T03/09: lectura/escritura/rename/symlink/cruces de secretos y endpoints denegados con controles sanos. |
| Riesgo residual | Root/kernel y principal comprometido excluidos; hardening puede afectar disponibilidad del binario. |
| Autoridad funcional competente | Plataforma + seguridad; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-I01/B-D01; abrir world access para positivo, afirmar SELinux unconfined como confinamiento o reutilizar cuentas históricas sin permiso. |

## AJ-I06 — Lifecycle y cleanup atribuible

| Campo | Registro propuesto |
| --- | --- |
| Contrato fuente y hash | [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) §Threat boundary; SHA-256 `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3`. Evidencia/complementos: ADJ E/F R-X01; HG manifest; IPC-C08; PGSCRIPT. |
| Situación comprobada | Harness PG ignora error de stop y anuncia éxito antes del cleanup; IPC aún no existe. |
| Riesgo | Borrar recursos ajenos o datos de proceso vivo; PASS falso oculta residuos. |
| Alternativas disponibles | Manifest con identidad/ownership; runtime dirs administrados con evidencia; limpieza por nombre (no suficiente). |
| Recomendación técnica | Run ID/path/tipo/dev/inode/owner antes/después; sin colisiones/symlinks; detener admisiones, cerrar, esperar salida y luego borrar solo recursos atribuibles. |
| Seguridad y compatibilidad | PID solo no identifica proceso tras reciclado; registrar cgroup/inicio o atributo acordado. Si stop/mismatch falla, preservar y declarar FAIL. |
| Cambios que requeriría | S3-IMP-06 sucesor de harness PG/IPC, señales EXIT/INT/TERM y recuperación tras SIGKILL; evidencia fuera de raíz a eliminar. |
| Pruebas positivas y negativas | Positivo: IPC-T10/PG-T11: salida confirmada y cero recursos vivos propios, evidencia retenida y PASS posterior al inventario. Negativo: IPC-T07/10/PG-T11: startup parcial, excepción, señales, proceso/socket vivo, symlink/colisión ajena; no borrar ni esconder error. |
| Riesgo residual | SIGKILL no ejecuta trap; recuperación posterior requiere manifest válido y permiso específico. |
| Autoridad funcional competente | Plataforma + custodio de evidencia; personas y mandato PENDING. |
| Estado | **PENDING_HUMAN_APPROVAL**; selección efectiva, firma y fecha: PENDING. |
| STOP | B-X01; propiedad incierta, manifest ausente, stop fallido, proceso vivo o cleanup global. |

## Parámetros y decisiones de detalle pendientes

No se seleccionan valores arbitrarios. Los 60 segundos máximos, 19 claims,
Ed25519/dominio y orden presupuestario global/producto/UUID proceden de fuentes
existentes; no autorizan nuevos valores de transporte. 0710/0660 son candidatos
heredados de ADJ, aún pendientes y sujetos a positivos DAC.

| Registro de detalle | Debe constar en acta | AJ / condición de salida |
| --- | --- | --- |
| NUM-C01 | Tipos por claim/material, formatos UUID/UTC, rangos enteros, tamaños de token/campo/IDs y profundidad, errores y compatibilidad. | AJ-C01/C02; antes de S3-IMP-01. Timestamps actuales son strings UTC, no asumir epoch. |
| NUM-C02 | Perfil de reloj/skew si se propone; no ampliar máximo D02 ni cambiar el mensaje firmado. | AJ-C01; antes de cambiar política temporal. |
| NUM-P01 | Máximo de intentos/backoff/jitter/presupuesto total; 40P01: retry completo acotado o fallo seguro; timeout SQL/locks y orden total. | AJ-P06; antes de S3-IMP-04. El 3 de otra ruta services no aprueba un valor para executor. |
| NUM-P02 | Momento de corte y propagación de revocación; sesiones ya abiertas, drenaje/terminación; retención ledger/audit. | AJ-P07/P09; antes de lifecycle y cualquier operación. |
| NUM-I01 | Tamaño del prefijo/endian, límite de frame/request/response, campos, nesting y esquema/códigos/versiones. | AJ-I03; antes de parser IPC. |
| NUM-I02 | Deadlines connect/read/write/operación, concurrencia, backlog, rate-limit/backpressure y uso máximo de memoria. | AJ-I03/I05; medir con fixtures máximas en futuro slice autorizado y aprobar antes del runtime. |
| NUM-I03 | UID/GID administrados, paths, owners/modes/ACL, topología, peer observables y mapping DB. | AJ-P03/I01/I02/I05; antes de implementación dependiente y provisión runtime. |
| NUM-L01 | Espera de drenaje/stop, criterio de proceso terminado, retención y permisos de evidencia, recuperación post-SIGKILL. | AJ-I06/P08; antes del harness final y runtime. |

Si medir un límite requiere código aún no autorizado, primero decidir método de
medición y autorizar un experimento offline acotado; el resultado vuelve al acta.
No usar un valor de prueba como contrato operativo por defecto.

## Registro individual de selección y firma

Esta tabla queda deliberadamente sin selección efectiva. Cada fila requiere
opción elegida o rechazo, desviaciones, fuente/hash, mandato, condiciones,
residual aceptado y enlace a acta verificable. **Una firma de arquitectura no
contiene permiso de implementar ni ejecutar.**

| AJ | Selección efectiva / desviación | Firmante y mandato | Acta / firma | Fecha efectiva y zona | Autorización implementación / runtime |
| --- | --- | --- | --- | --- | --- |
| AJ-G01 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-H01 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-C01 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-C02 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P01 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P02 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P03 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P04 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P05 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P06 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P07 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P08 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-P09 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-I01 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-I02 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-I03 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-I04 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-I05 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |
| AJ-I06 | PENDING | PENDING | PENDING | PENDING | PENDING / PENDING |

Estado global: **PENDING_HUMAN_APPROVAL**. Véanse [ADR](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md), [slices](ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md) y [gates](ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md). **S3_DECISION_02A_NOT_CLOSED**.
