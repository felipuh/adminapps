# S3 — Architecture Governance Reconciliation Report

Fecha de preparación: 2026-10-09, America/Costa_Rica.
**DICTAMEN DOCUMENTAL — APROBACIONES Y AUTORIZACIONES FUTURAS PENDING.**
**S3_DECISION_02A_NOT_CLOSED**.

## Executive Verdict

Se preparan cinco documentos nuevos para decidir arquitectura y delimitar
implementación incremental. No hay firmas humanas nuevas, código de producto,
migraciones aplicadas, servicios, DB, IPC o ensayos privilegiados. La trazabilidad
se apoya en fuentes locales preservadas y sus hashes; los controles runtime
continúan pendientes. Las inconsistencias materiales/dependencias se registran
como BLOCKER de su gate, sin impedir entregar un borrador revisable.

Paquete: [ADR DRAFT](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md), [matriz humana](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md), [plan por slices](ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md),
[gates](ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md) y este reporte. Solo estos cinco archivos se agregan al repositorio.

## Gobierno vigente y propuestas

| Tema | Registro existente | Reconciliación de esta entrega |
| --- | --- | --- |
| V11/A01 | Propuesta en cabecera; adopción posterior en AdminApps/A02/ER y autorizaciones reportadas. | AJ-G01/B-G01 exige acta/versionado/hash y mandato. No revocar lo registrado ni asumir acta ausente como inexistente. |
| D02 | HUMAN_APPROVED, remediación acotada; executor LOGIN y verificación Python. | Conservar frontera, claims/dominio y exclusión de compromiso del executor. Aprobación histórica no autoriza los nuevos slices. |
| A02 | APPROVAL_PENDING; plantea verifier DB, NOLOGIN, claims diferentes y HSM. | No adoptada. No mezclar con D02 ni elevar sondas wire a falla criptográfica. |
| Host | Reportes PASS y evidencia EVIDENCED_PARTIAL por atribución insuficiente. | AJ-H01: declarar retención/pérdida y aportar solo evidencia existente con procedencia; sin repetir lab. |
| PostgreSQL | ACL/función históricas bajo trust; ownership 0006 y transacción executor incompletos en fuente. | No prueba de autenticación exclusiva ni nuevo catálogo. AJ-P01–09 + validación futura. |
| IPC | Interfaces Python, sin transporte financiero implementado. | AJ-I01–06 propuestos; llamadas en proceso/fixtures no son peer authentication. |
| S1/S2 | Resultados históricos preservados. | No recertificados; FIN-01/02/03/08/09 siguen trazables. |
| Fases/productos | PHASE31_5 = EXECUTION_HELD. | Sin cambios Phase32, WP2, ISO Smart o MedSupplier. No S4–S6, proveedor/inferencia, precios reales ni producción. |

FIN-04/06 enlazan P06/P07/P09 e I04 con transacción, concurrencia, replay y
ambigüedad. FIN-08/09 enlazan P01–P05/P08 con objetos/roles/admin; FIN-11 enlaza
VAL-01/02 y cierre. FIN-05 no autoriza tarifas reales. FIN-07/10/12 y S4–S6
permanecen fuera de implementación. El diseño de UNKNOWN preserva exposición;
no crea settlement, release ni endpoint status para satisfacer FIN-10.

## Source Integrity

IDs de fuentes inmutables para este paquete. Hash SHA-256 de bytes leídos al inicio;
rutas enlazadas relativas a `docs/financial/`. Los hashes de contratos se repiten
en las fichas AJ principales; fuentes de código y evidencia se resuelven aquí.
No se modificó ninguna fuente ni manifiesto histórico. A02 y V11 conservan sus
cabeceras. Las lecturas de ISO Smart fueron solo contractuales.

| ID | Fuente | SHA-256 |
| --- | --- | --- |
| ADJ | [ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_2026-10-09.md) | `6d16f47e4d2ed6a742294a8ccd4c65399ddbb3f0271b22aab081b96a143a571a` |
| EVID | [ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json) | `57e8a44b89bc1af0598c6fc1f9691a461deaf6eb227ff413490da5e093946ec4` |
| D02 | [ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) | `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3` |
| A02 | [ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md) | `e03022a6ca4da9eeb9022b50972d30ff6628fa5a5ab9614ba3e21d6a5af9ef79` |
| OFF | [ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json](ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json) | `4bfdd21a0f1c677f3ac3f1ccb81cb6fb8731d73c78b7c11d959638aae2058e33` |
| PG | [ADMINAPPS_AI_FINANCIAL_S3_POSTGRESQL_ISOLATION_SPECIFICATION_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_POSTGRESQL_ISOLATION_SPECIFICATION_2026-10-09.md) | `374acbaae96195bb4bba0589bee4be1e24d317d40769e4ed79a2d59a241e73ec` |
| IPC | [ADMINAPPS_AI_FINANCIAL_S3_IPC_ISOLATION_SPECIFICATION_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_IPC_ISOLATION_SPECIFICATION_2026-10-09.md) | `53b333dcfbcc9a8fbdd581993aec1b19ec6936ce91aea0c03bcabc8332cf443d` |
| REC | [ADMINAPPS_AI_FINANCIAL_S3_GOVERNANCE_RECONCILIATION_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_GOVERNANCE_RECONCILIATION_2026-10-09.md) | `b2fdaa59e3094891060b8126b3825a56ae6fef958c4dd022397a96bc604891a7` |
| ER | [ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md) | `da5d01ba8f0e12c66ed068c868568bc4fa208871d478a017453562290e2eea2b` |
| HG | [ADMINAPPS_AI_FINANCIAL_S3_ISOLATION_ADMINISTRATIVE_GATE_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_ISOLATION_ADMINISTRATIVE_GATE_2026-10-09.md) | `635fd2ffe4a6e8a1dadb83efc52f63bf5af8f91585f110ee5d7bd8660f549095` |
| HR | [ADMINAPPS_AI_FINANCIAL_S3_SYSTEMCALLFILTER_VALIDATION_REMEDIATION_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_SYSTEMCALLFILTER_VALIDATION_REMEDIATION_2026-10-09.md) | `5ba1ae69baed48a33ef330411344fc1df0587ac714247b100e895eac02ce7e9c` |
| VM | [ADMINAPPS_AI_FINANCIAL_S3_EXISTING_VM_ISOLATION_EXECUTION_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_EXISTING_VM_ISOLATION_EXECUTION_2026-10-09.md) | `2a6b7228dbfbed45a5a4712ccff7cf4ad486ad00a5999e530940eb21c56ed840` |
| HC | [ADMINAPPS_AI_FINANCIAL_S3_HOST_LAB_CLOSURE_EVIDENCE_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_HOST_LAB_CLOSURE_EVIDENCE_2026-10-09.md) | `8b88cf2b23112ccfdf4df3ae94c468fc8de7e8de5182588b1557bb0b01ce853a` |
| S1 | [ADMINAPPS_AI_FINANCIAL_S1_IMPLEMENTATION_REPORT_2026-10-08.md](ADMINAPPS_AI_FINANCIAL_S1_IMPLEMENTATION_REPORT_2026-10-08.md) | `a316b93846ca3d59062011f5621134dbbc4a024ace17b225a0c1dfc30416ab88` |
| S2 | [ADMINAPPS_AI_FINANCIAL_S2_IMPLEMENTATION_REPORT_2026-10-08.md](ADMINAPPS_AI_FINANCIAL_S2_IMPLEMENTATION_REPORT_2026-10-08.md) | `c29ed6dca9ebb9eb778cf8ad605b8533eff61d097363e891d2876a6da041c0e6` |
| S3 | [ADMINAPPS_AI_FINANCIAL_S3_IMPLEMENTATION_REPORT_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_IMPLEMENTATION_REPORT_2026-10-09.md) | `ad8a853363f5891e92dd993d845b9c6ddb8685de2998027008e210e617bb2fd2` |
| FV | [ADMINAPPS_AI_FINANCIAL_S3_FINAL_VALIDATION_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_FINAL_VALIDATION_2026-10-09.md) | `c26d6a24804986e110757ddbd16a6ad6b8358dae8bc0aa0810462126adb01be6` |
| SUC | [ADMINAPPS_AI_FINANCIAL_S3_SUCCESSOR_EXECUTION_PLAN_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_SUCCESSOR_EXECUTION_PLAN_2026-10-09.md) | `41ccc2a911f2fae1e533e3d73e430676561d9a5a0d87e5fad16964e185f9fc4d` |
| V11 | [ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) | `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f` |
| A01 | [ADMINAPPS_AI_FINANCIAL_AUTHORITY_AMENDMENT_01_DECISION_RECORD_2026-10-08.md](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_AMENDMENT_01_DECISION_RECORD_2026-10-08.md) | `677cb7006c04ce35b6127e589fb46b26bb44aae491509c4fe2b0a39fb0eeacf8` |
| FIRM | [ADMINAPPS_AI_FINANCIAL_AUTHORITY_IMPLEMENTATION_READINESS_2026-10-08.md](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_IMPLEMENTATION_READINESS_2026-10-08.md) | `62ae466bd4482bb0c519d8a0bf0e198e02281084bcdadbed1aa698316e08d33d` |
| CAP | [capabilities.py](../../backend/apps/financial/capabilities.py) | `b389eb73799eb13ea8af0285dbf4d6f20a3b917fe58d7707da96fadfc24f44dd` |
| EXE | [executor.py](../../backend/apps/financial/executor.py) | `8b39ada47540612f5f5bcf8361bff7b6154847e2f62d897f29a813721eaf7e46` |
| ISS | [issuer.py](../../backend/apps/financial/issuer.py) | `9d8c3535500cbeec299a2e7df2e6ecb3c69383e8e22a9accfa50b37ead785859` |
| AUTH | [authorization.py](../../backend/apps/financial/authorization.py) | `53a314f4553842b919013e90580c0e499c010cffd91aa074ea2608e659bf13e5` |
| SVC | [services.py](../../backend/apps/financial/services.py) | `1a0b8491900b041ac9f088ffbd275d8b19212e1e960ce8c7343395ffb96d11d8` |
| MODELS | [models.py](../../backend/apps/financial/models.py) | `898e485465ee836ccef735e5310d56c63eaf8ba1fbe3a26ce3ae576a9179a876` |
| TESTS | [tests.py](../../backend/apps/financial/tests.py) | `dcfb23119739e851b306d790828b28cd7c3069e62fe5cc39ef9ea5ccb292e585` |
| M0001 | [0001_financial_s1_foundation.py](../../backend/apps/financial/migrations/0001_financial_s1_foundation.py) | `5a89a52317ccc76e576d500b2b730e90c6150e1ab6b25164f743742f6ac2f5fc` |
| M0002 | [0002_postgresql_security.py](../../backend/apps/financial/migrations/0002_postgresql_security.py) | `362abb5ef1fa481f53e930bbeeafc541171582e83892973f5600e4fdc79d9967` |
| M0003 | [0003_producer_identity_and_financial_rbac.py](../../backend/apps/financial/migrations/0003_producer_identity_and_financial_rbac.py) | `b56a6b57c11c96bc1cc2ee546ce65aa05588f3ba0e08f3afdafc14cb78466477` |
| M0004 | [0004_s3_admission_controls.py](../../backend/apps/financial/migrations/0004_s3_admission_controls.py) | `aa71f24899d1a44b8b8da0141f898d92d5e99d7f00edd2e98ffe09dff31bb92a` |
| M0005 | [0005_s3_runtime_admission_boundary.py](../../backend/apps/financial/migrations/0005_s3_runtime_admission_boundary.py) | `d2c7dfc9ddd944bda90f7b5dce17b48646928e0ee51f9727f0f98152d476a384` |
| M0006 | [0006_decision_02_a_grants_and_ledger.py](../../backend/apps/financial/migrations/0006_decision_02_a_grants_and_ledger.py) | `f99e34850afd4e375c72311138a2c98e629abd95fb9c0ee2c8a73aadf21efd58` |
| M0007 | [0007_decision_02_a_executor_boundary.py](../../backend/apps/financial/migrations/0007_decision_02_a_executor_boundary.py) | `b098ed9d9e79dee94c5fce2d8542c93316a2d09dbec4065d1b4f79fa4602057f` |
| INTSVC | [services.py](../../backend/apps/integration/services.py) | `afcb9bf36ff5a57f58db6459b22a6428dc7b41c114c5c6a968c34d1d7c386cb2` |
| INTMODEL | [models.py](../../backend/apps/integration/models.py) | `64d26271b6970261f58f6984af575bd90ab6054719cdb5d44696616d19bf2ec2` |
| HOST | [s3_isolation_host_lab.sh](../../backend/scripts/s3_isolation_host_lab.sh) | `4a50014a069289af60afacedc89b6d93468edbd3921c8c6d72c3e005d6c086a5` |
| PGSCRIPT | [verify_financial_s3_postgres.sh](../../backend/scripts/verify_financial_s3_postgres.sh) | `48898a6380fffce07647be9a8f94644b0bc3f4d74541fb5a88d4c476834a6840` |
| PGS1SCRIPT | [verify_financial_s1_postgres.sh](../../backend/scripts/verify_financial_s1_postgres.sh) | `8588a72b792ad7d93b0183a255ba10d6bf8e05d6eae4774fb3c8473dc4e1f852` |
| CRTEST | [test_s3_capability_offline.py](../../backend/scripts/tests/test_s3_capability_offline.py) | `80569387baf0e1faa8bc3948f1f84c35336bdbdd5c42e1bbcec6841c00994e74` |
| REQUEST | [Pasted text.txt](../../../../.codex/attachments/8cf73609-e88b-4967-a503-8aa3805c1d79/Pasted text.txt) | `0e3c65eefdcde8f63beaa417171f225fefcce0191faa0c7577699b0dccc7ff3e` |

### Comparaciones con hashes disponibles

| Manifiesto / campo | Comparación actual | Límite |
| --- | --- | --- |
| EVID / `source_sha256` | 24/24 MATCH | Bytes respecto del manifiesto; no autoridad ni runtime. |
| EVID / `previous_package_files_sha256` | 7/7 MATCH | Bytes respecto del manifiesto; no autoridad ni runtime. |
| EVID / `preserved_financial_scope_sha256` | 44/44 MATCH | Bytes respecto del manifiesto; no autoridad ni runtime. |
| EVID / `deliverable_sha256` | 1/1 MATCH | Bytes respecto del manifiesto; no autoridad ni runtime. |
| OFF / `deliverable_sha256` | 6/6 MATCH | Bytes respecto del manifiesto; no autoridad ni runtime. |
| OFF / `preexisting_sha256` | 37/37 MATCH | Bytes respecto del manifiesto; no autoridad ni runtime. |
| OFF / `reference_sha256` | 4/4 MATCH | Bytes respecto del manifiesto; no autoridad ni runtime. |

Las comparaciones anteriores suman 123 entradas, con superposición entre
manifiestos; **no son 123 fuentes independientes**. No hubo mismatch en esos
hashes. EVID fija el hash del dictamen ADJ y del paquete anterior. El hash de
EVID aquí registrado es una observación inicial, no una comparación con un
hash externo previo inexistente en el contexto de esta solicitud. Su estructura
JSON se pudo leer; no implica autenticación del autor ni evidencia host.

OFF incluye cuatro referencias externas: tres documentos ISO y el adjunto previo.
Se verificó su integridad sin publicar secretos ni extender búsqueda a carpetas
personales. El adjunto de solicitud actual tiene hash REQUEST distinto y alcance
documental propio. No se sobreescriben OFF, EVID ni sus entregables referenciados.

El control temporal anterior `/tmp/adminapps-s3-adjudication-x61p7exc/baseline.json`
existe y coincide con el hash consignado en EVID:
`e296d64d2cdc51d57be1b3c6518b7395f103eb0c4e99e610acf6da35c9a778c7`.
Comparación de sus 15.519 entradas con la misma convención de bytes: 15.519 MATCH.
Esta comprobación adicional no lo transforma en evidencia runtime.

El inventario actual tiene 15.523 entradas: 15.515 archivos regulares y ocho
symlinks. La diferencia de cuatro frente al inventario anterior se explica por
ADJ/EVID y dos symlinks de directorio `backend/.venv/lib64` y
`backend/venv_admin/lib64`, excluidos por la convención anterior de archivos.
Seis symlinks de binarios estaban incluidos antes por hash del destino; al
comparar esa misma convención coinciden. El inventario actual además fija texto
del enlace y modo, sin ejecutar esos binarios ni atribuir cambio temporal a una
diferencia metodológica.

### Fuentes técnicas informativas

Se consultaron fuentes primarias para verificar límites del diseño. No son actas
ni fijan una versión del futuro clúster: la versión runtime queda PENDING.

- Peer DB usa identidad OS y mapping, y aplica a conexiones locales:
  [PostgreSQL 15, Peer Authentication](https://www.postgresql.org/docs/15/auth-peer.html).
- SERIALIZABLE exige contemplar abortos y retry de transacción:
  [PostgreSQL 15, Transaction Isolation](https://www.postgresql.org/docs/15/transaction-iso.html).
- FORCE RLS no contiene al superusuario ni convierte DDL del propietario en
  frontera runtime: [PostgreSQL 15, Row Security](https://www.postgresql.org/docs/15/ddl-rowsecurity.html).
- Credenciales kernel de sockets UNIX y permisos pathname son controles distintos;
  servidor/cliente y lifecycle se deben probar:
  [Linux unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html).

La separación de ruta de datos y socket para UIDs distintos (B-D01), y la revisión
de TLS frente a canal interno (B-T01), son inferencias de diseño de esta revisión;
no resultados de un experimento ni declaraciones de incumplimiento desplegado.

## Blockers

Todos los siguientes están **OPEN — BLOCKER** del alcance indicado. Ninguno
implica explotación observada. Resolver un bloqueo documental no demuestra un
control técnico. No se detectó alteración de fuentes por hash; sí se mantienen
inconsistencias de autoridad y garantías operativas sin demostrar.

| ID | Evidencia/situación y tipo | Gate/slice bloqueado | Resolución necesaria / autoridad propuesta |
| --- | --- | --- | --- |
| B-G01 | V11 propuesta vs adopción posterior sin acta/hash/mandato enlazados; D02 y A02 divergen. Autoridad insuficiente. | G-ARCH dependiente y todos los G-IMP nuevos. | AJ-G01: acta/versionado explícito y personas designadas; dueño financiero + seguridad + DBA. |
| B-H01 | EVID/ADJ B: salidas y testimonio sin atribución primaria suficiente del run/cleanup. Evidencia histórica parcial. | Cierre host y G-CLOSE pleno; no impide preparar slices documentales. | AJ-H01: custodia, export o declaración de retención/pérdida; evidencia del servicio real futura. Custodio + gobernanza. |
| B-C01 | CAP/EXE/ISS/SVC: wire/tipos/límites/material/binding incompletos. Política propuesta no decidida. | IMP-01 e interfaces dependientes. | AJ-C01/C02, NUM-C, compatibilidad/versionado y pruebas CR/MT; protocolo + financiero. |
| B-P01 | M0006 ownership implícito; PGSCRIPT trust; issuer DB ausente; EXE sin garantía transaccional; revocación/ledger pendientes. Garantías no establecidas. | IMP-02–04 por decisión; G-PG/cierre por prueba. | AJ-P01–09, catálogo/ACL objetivo, auth/rutas, NUM-P, patch revisado y PG-T01–11; DBA + financiero + seguridad. |
| B-I01 | IPC NOT_IMPLEMENTED; topología/UID/frames/códigos/deadlines no decididos. Contrato insuficiente. | IMP-05/06 y G-IPC. | AJ-I01–I06, NUM-I/L, protocolo y peer mutuo; arquitectura + seguridad + plataforma. |
| B-T01 | V11 §3.2 exige producer credential sobre TLS; nueva ruta local runtime→issuer debe delimitar si es frontera interna distinta o cambio/excepción. Inconsistencia potencial de alcance, no incumplimiento observado. | AJ-I01 efectivo e IMP-05; no abre trabajo externo. | Dueño de contrato + seguridad define alcance con hash/versionado; mantiene enlace producer externo fuera del paquete. |
| B-D01 | PG propone socket bajo raíz 0700 y ahora se propone peer con UIDs distintos; no hay disposición DAC aprobada que pruebe ambos. Incompatibilidad de configuración candidata. | IMP-03/06 final y G-PG peer. | AJ-P03/I05: data directory privado, socket separado y traversal mínimo; positivos por UID, sin world access o UID compartido. DBA + plataforma. |
| B-R01 | V11 §10.5 prescribe reconciliación tras ambigüedad; status no existe y queda fuera de estos slices. Recuperación operativa insuficiente. | Operación y cierre pleno, no ensayos sintéticos con inspector autorizado. | AJ-P09/I04: adjudicar alcance/recuperación y eventual slice separado; sin construir HTTP/status/S4 aquí. Financiero + arquitectura + seguridad. |
| B-X01 | PGSCRIPT ignora stop y anuncia PASS antes de cleanup; sucesor no implementado. Defecto de harness para nueva ejecución. | G-PG/G-IPC y validación de cleanup. | IMP-06 con manifest/stop/ausencia final; revisión SHA y permiso posterior. Plataforma + custodio. |

No se otorgan excepciones para sortear estos gates. Las diferencias TLS/socket
se documentan sin modificar PG/IPC/V11/ADJ históricos ni presentar su diseño como
implementación existente. Opción alternativa vuelve a la autoridad y a la matriz.

## Trazabilidad y reconciliación de resultados

La matriz tiene 19 fichas completas: G01, H01, C01/C02, P01–P09 e I01–I06.
Cada una enlaza contrato/hash, hechos, selección propuesta, prueba y STOP. PLAN
asigna esos AJ a seis IMP, dos VAL y un CLOSE. GATES mantiene las autorizaciones
separadas; no contiene comandos operativos inventados para harness inexistente.

| Evidencia anterior | Tratamiento actual |
| --- | --- |
| 19/19 host y 19/19 crypto en OFF | Histórica, no repetida; no prueba procesos/credenciales/DB/IPC. |
| Whitespace no canónico y duplicado idéntico aceptados | FAIL frente a rechazo estricto propuesto. Conservados; no falsificación Ed25519 ni prueba de aprobación de A02. |
| Siete diagnósticos JSON de EVID | Observaciones de igualdad del mensaje/semántica, no nueva ejecución criptográfica. No repetidos. |
| 4/4 PG de ER | Antecedente limitado de ACL/función; “separately authenticated” acotado por ADJ a selección de rol bajo trust. No recertificado. |
| 50 outputs /tmp copiados en EVID | Contenido conservado en evidencia histórica; no reatribuir a run exitoso ni reinspeccionar host para este paquete. |
| HOST SHA coincidente | Integridad de fuente, no hash ejecutado autenticado ni cleanup. |

El orden presupuestario global/producto/UUID ya viene de V11; el orden total
adicional entre grant/identidad/registro/policy/tariff sigue propuesto. Los
reintentos acotados no toman automáticamente el valor 3 de services como norma
para executor. Los modos 0710/0660 son candidatos de ADJ, no permisos concedidos.
Las pruebas futuras siguen NOT_RUN. No se compensa falta de evidencia cambiando
expectativas ni relajando política para obtener PASS.

## Git Integrity

Rama inicial: `hardening/p0-p1-enterprise-readiness`.
HEAD inicial: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`.
Índice inicial sin cambios staged. SHA-256 inicial del índice:
`d774b85b7f9123d243c0d094e6efe7e151ac3a1c38d8eee4a00970438dfcfd50`.

Estado preexistente resumido, conservado:

```text
 M backend/config/settings.py
?? backend/apps/financial/
?? backend/scripts/s3_isolation_host_lab.sh
?? backend/scripts/tests/
?? backend/scripts/verify_financial_s1_postgres.sh
?? backend/scripts/verify_financial_s3_postgres.sh
?? docs/financial/
```

La baseline fijó bytes/modo/tipo de 15.523 entradas tracked/untracked no ignoradas,
rama/HEAD/índice/status. No certifica archivos ignorados fuera de fuentes explícitas,
metadatos no inventariados ni otros sistemas. ISO Smart solo tuvo lectura de tres
contratos; no se hicieron escrituras ni cambios de estado Phase32/WP2/MedSupplier.

Control temporal de esta tarea: `/tmp/adminapps-s3-approval-prep-ik0rkc3l/`.
Hash de `baseline.json`:
`82ce1767fa24911cdf465d0a9820f201e9ce0941192757dfbce85dc84036dc65`.
Los conteos, hashes de fuentes y resultados relevantes se conservan en este reporte;
la retención del control temporal no es requisito de cierre. No se hizo staging,
commit, push, merge, cambio de rama, reset ni checkout de trabajo preexistente.

## Verification Results

Las comprobaciones de este paquete son documentales. Se ejecutaron lecturas,
SHA-256/JSON, Git read-only y una extracción AST de nombres de tablas, sin importar
módulos de producto. No se ejecutaron los scripts host/PG/IPC, ni pytest/Django,
makemigrations/migrate, herramientas privilegiadas, contenedores o servicios.
Las pruebas del código de producto permanecen NOT_RUN por alcance expreso.

<!-- FINAL_VALIDATION_START -->
| Comprobación final | Resultado | Alcance/límite |
| --- | --- | --- |
| Fuentes leídas | PASS 42/42 | SHA inicial y final coinciden, incluida solicitud; no acredita firma humana. |
| Manifiestos históricos | PASS 123/123 entradas | Comparaciones superpuestas EVID/OFF; hashes históricos sin modificar. |
| Baseline local | PASS 15.523/15.523 entradas | Bytes/tipo/modo de archivos y enlaces; cero diferencias preexistentes. |
| Cambios nuevos | PASS 5/5 documentos previstos | Ningún otro archivo repository-local creado, eliminado o cambiado por esta tarea. |
| Rama/HEAD/índice/status | PASS | Rama/HEAD e índice SHA idénticos; staging vacío; delta status de cinco archivos nuevos. |
| Matriz y acta | PASS 19 × 12 campos; 12 secciones ADR | Hash contractual, selección propuesta, pruebas, residual, autoridad, PENDING y STOP por AJ. |
| Slices | PASS 9 × 10 campos | Dependencias/permisos, archivos, cambios, invariantes, pruebas, evidencia, rollback, aceptación, STOP y residual. |
| Coherencia de autoridad | Revisión estática completada | D02/A02 separados, selección efectiva/firma PENDING, gates independientes, cifras pendientes y NOT_CLOSED conservado. No prueba una aprobación. |
| Enlaces/UTF-8/tablas/whitespace | PASS | Cinco documentos nuevos; enlaces locales resueltos y seis referencias a anclas comprobadas. |
| Hashes de entregables | PASS 4/4 | Los otros cuatro documentos coinciden con el registro inferior; este reporte se hashea fuera de sí mismo. |
| `git diff --check` | PASS, exit 0 | stdout/stderr vacíos; cubre diff tracked. |
| `git diff --no-index --check /dev/null <documento>` | Sin diagnósticos de whitespace en los cinco | Exit 1 por diferencias de archivo nuevo; stdout/stderr vacíos. Check textual independiente también PASS. |
| Host Lab / PostgreSQL / IPC / migraciones / Django | NOT_RUN | Prohibidos por alcance actual, no omitidos de un ensayo runtime iniciado. |

Nota de método: la primera pasada del validador documental clasificó por error
el exit 1 normal de `git diff --no-index` como FAIL, aunque no hubo diagnóstico
de whitespace. Se corrigió el clasificador para aceptar 0/1 solo con stdout y
stderr vacíos. Un archivo temporal con whitespace inválido produjo diagnóstico
y exit 3; el control limpio produjo 1 sin diagnóstico. No se cambió ningún
contenido para ocultar un error ni se reinterpretó evidencia crypto/host/PG.
La comprobación explícita de espacios de los cinco Markdown ya era satisfactoria.
Los resultados de la primera pasada se conservan en el control temporal.
<!-- FINAL_VALIDATION_END -->

`git diff --check` por sí solo no revisa archivos untracked. Por ello la validación
incluye los cinco Markdown nuevos explícitamente: whitespace, UTF-8, enlaces y
anclas locales, estructura de tablas, fichas AJ/campos, slices, permisos PENDING y
trazabilidad. La revisión humana de la coherencia técnica complementa los checks
estructurales; ningún check estático demuestra aislamiento runtime.

## Generated Documents and Hashes

Los primeros cuatro documentos quedan ligados por estos hashes; este reporte
incluye sus resultados y fuentes. Su propio SHA se entrega fuera del documento
para evitar una autorreferencia circular.

| Entregable nuevo | SHA-256 |
| --- | --- |
| [ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md) | `181b20e5f1c9e22e6b0480dc513604a25856909e8c49b406199916d9b4528ea2` |
| [ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md) | `c56d6ee9f15022839cea220a748de8e357424ec46d5cdf88add0dddae617e855` |
| [ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md) | `a58fb7fd87032148a319d8442ec7708d2f8b1804d1b0f50256d7e48382a53abd` |
| [ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md](ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md) | `259a49d32aa206373891c4079f0ad35284da95602b703052804747fb77f343cf` |

## Exact Human Decisions Required

1. AJ-G01: acta/versionado de V11 y mandatos; mantener D02 y A02 separados.
2. AJ-H01: custodia/retención y aceptación explícita de evidencia parcial,
   sin certificar lo no demostrado.
3. AJ-C01/C02: C-B, esquema/binding, perfiles/límites y compatibilidad/versionado.
4. AJ-P01–P05/P08: owner, identidades, proyección issuer, autenticación peer o
   SCRAM, ruta socket/DAC, RLS/ACL/defaults y administración temporal.
5. AJ-P06/P07/P09: SERIALIZABLE/orden de locks, retry 40001/40P01, revocación y
   sesiones, ledger y recuperación/retención sin modificar historia.
6. AJ-I01–I06: topología/relay, alcance TLS, UIDs/peer mutuo, wire/cifras/códigos,
   UNKNOWN, hardening, lifecycle y cleanup.
7. Después de esas selecciones aplicables: permiso independiente G-IMP por slice;
   tras patch/harness revisados y SHA, G-OS/G-PG/G-IPC específicos; finalmente
   aceptación G-CLOSE con evidencia suficiente. Todos **PENDING**.

Este es un paquete para revisar y decidir, no una autorización operativa genérica.
**S3_DECISION_02A_NOT_CLOSED**; **PHASE31_5 = EXECUTION_HELD**.
