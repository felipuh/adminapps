# SMART3AI / ADMINAPPS — ACTA FORMAL DE DESIGNACIÓN DE AUTORIDADES INTERNAS Y ADJUDICACIÓN DE DECISIONES CONTRACTUALES S3-IMP-01 (BORRADOR)

**Código del Documento:** `SMART3AI-ACTA-GOV-S3-IMP01-DRAFT-2026-10-12`<br>
**Fecha de Elaboración:** 2026-10-12<br>
**Estado Documental:** `DRAFT_PENDING_HUMAN_SIGNATURES`<br>
**Nivel de Clasificación:** Confidencial / Gobernanza Interna Smart3AI<br>
**Entorno de Aplicación Propuesto:** AdminApps — `controlled_test` (exclusivo para pruebas offline)<br>
**Dependencia Operacional:** `S3-IMP-01 = BLOCKED_PENDING_AUTHORITY` | `S3_DECISION_02A_NOT_CLOSED` | `PHASE31_5 = EXECUTION_HELD`

---

## A. IDENTIFICACIÓN DE SMART3AI Y ADMINAPPS

### A.1 Naturaleza del Proyecto y de la Organización
1. **Smart3AI:** Iniciativa empresarial y proyecto de base tecnológica desarrollado de manera conjunta por sus socios fundadores. Se deja constancia expresa de que a la fecha del presente documento no se afirma ni presupone la existencia de personería jurídica mercantil registrada, estatutos sociales inscritos, nombramientos de representación legal formalizados ante registro público mercantil ni poderes notariales registrados, al no haberse aportado evidencia documental de los mismos. La gobernanza aquí articulada corresponde a un régimen de **acuerdo interno de socios y asignación funcional de responsabilidades**, propuesto para las decisiones arquitectónicas, de seguridad y de producto del software, pendiente de adopción verificable; no acredita facultades jurídicas externas.
2. **AdminApps:** Plataforma de software empresarial bajo gestión y desarrollo técnico en el repositorio `/home/felipe/proyectos/adminapps`. En su subsistema de backend financiero (`backend/apps/financial/`), se implementa la arquitectura de control transaccional por capabilities criptográficas de autoridad financiera (S3).
3. **Rol del Redactor:** El presente borrador ha sido elaborado por el equipo técnico actuando en calidad combinada de *Enterprise Software Architect*, *Security Governance Lead* y *Technical Secretary* para Smart3AI, a efectos de someterlo formalmente a la consideración, deliberación y suscripción de los tres socios de Smart3AI.

---

## B. ALCANCE DE LA SESIÓN DE GOBERNANZA

### B.1 Propósito
El presente acto documental tiene por único objeto:
1. Someter a la aceptación formal de los tres socios de Smart3AI la **propuesta de designación de autoridades internas**, distribución de mandatos y régimen de segregación de funciones (cuatro ojos / *four-eyes principle*).
2. Presentar de forma consolidada las **seis decisiones contractuales y normativas** requeridas para resolver el bloqueo de la fase S3-IMP-01:
   - `AJ-G01`: Ratificación de versión y alcance contractual V1.1, preservación de D02 y estado de A02.
   - `AJ-C01`: Selección de perfil de wire format, gramática JSON estricta y Ed25519.
   - `AJ-C02`: Adopción del modelo de material (Material9), assertion (Assertion4), binding estricto y contexto confiable.
   - `F-C18`: Ratificación del conjunto cerrado de exactamente 18 claims de capability.
   - `NUM-C01`: Adopción del perfil normativo sintético `S3-CONTROLLED-TEST-CAPACITY-V1` ($L_R=64, L_E=256, N_E=32, B_M=9169$).
   - `NUM-C02`: Adjudicación de parámetros temporales UTC20, skew cero y TTL sintético `0 < (exp - iat).total_seconds() <= 60`, con `iat <= nbf < exp` y `nbf <= now < exp`.

### B.2 Carácter Exclusivamente Documental y No Concesión de Permisos de Ejecución
1. El presente documento es una **propuesta formal para decisión humana**; no constituye aprobación tácita ni expresa por sí mismo.
2. **NO concede autorización de implementación (`G-IMP`)**, la cual deberá ser objeto de un acto resolutivo independiente y posterior.
3. **NO implementa código, NO ejecuta migraciones, NO altera configuraciones de sistema, NO invoca bases de datos operacionales ni servicios IPC.**
4. El estado del proyecto permanece invariablemente en:
   - `S3-IMP-01 = BLOCKED_PENDING_AUTHORITY`
   - `S3_DECISION_02A_NOT_CLOSED`
   - `PHASE31_5 = EXECUTION_HELD`
   - `D02 = HISTORICALLY_APPROVED (acotado a LOGIN/Python)`
   - `A02 = APPROVAL_PENDING`

---

## C. DESIGNACIÓN PROPUESTA DE AUTORIDADES

Se somete a la ratificación unánime de los socios la siguiente estructura orgánica y funcional interna:

### C.1 Felipe Ugalde Hernández
- **Cargos y Roles Propuestos:**
  - *Chief Technology Officer* (CTO) de Smart3AI.
  - Responsable de Arquitectura Técnica y Gobernanza de Contratos de Software.
  - Líder de Desarrollo Técnico y Especificaciones Formales.
  - Responsable Propuesto de Arquitectura y Modelo de Datos.
- **Alcance de Atribuciones:**
  - Definición y custodia de especificaciones arquitectónicas, interfaces de software, contratos de claims y modelos matemáticos/algorítmicos.
  - Liderazgo en el diseño e implementación de parches de código bajo mandatos autorizados.
- **Limitación Crítica de Segregación:**
  - **Incompatibilidad Absoluta de Auto-Aprobación:** Felipe Ugalde Hernández **no puede actuar como único aprobador de ningún cambio, parche o especificación que él mismo elabore, proponga o implemente**. Todo cambio en código o contratos críticos requerirá revisión y aprobación cruzada independiente.

### C.2 Adrián Garita
- **Cargos y Roles Propuestos:**
  - Responsable de Operaciones de Smart3AI.
  - Responsable de Infraestructura y Seguridad Operativa.
  - Revisor de Controles de Despliegue, Aislamiento de Procesos y Segregación de Ambientes.
- **Alcance de Atribuciones:**
  - Supervisión de los entornos de ejecución, políticas de red, cortafuegos, contenedores, servicios de soporte y pipeline de entrega.
  - Validación del cumplimiento operativo de límites de recursos y procedimientos de despliegue.
- **Condición de Competencia Técnica Específica:**
  - **No Presunción de Competencia Criptográfica o DBA Profunda:** La competencia para evaluar y aprobar criptografía asimétrica especializada (curvas elípticas Ed25519, representación canónica del emisor actual (sin sustitución por RFC 8785)) o controles transaccionales internos de base de datos a bajo nivel (PostgreSQL DBA controls) **no se presume por el cargo de operaciones y debe ser verificada o sustentada mediante dictamen técnico acreditado**. Su rol se enfoca primariamente en la disciplina operativa, disponibilidad y control de segregación.

### C.3 Félix Guzmán
- **Cargos y Roles Propuestos:**
  - Responsable de Producto y Área Comercial de Smart3AI.
  - Candidato a Autoridad Funcional Financiera del Negocio.
- **Alcance de Atribuciones:**
  - Validación del alcance de negocio, adecuación al mercado, alineación estratégica y preservación de valor del producto.
  - Definición y ratificación de límites de exposición financiera, políticas de tolerancia de negocio y asunción informada de riesgos funcionales y comerciales.
- **Límites de Función:**
  - No aprueba directamente implementaciones algorítmicas de bajo nivel ni configuraciones de infraestructura de red, sino el impacto financiero, comercial y legal-funcional derivado de los controles.

### C.4 Principios del Régimen de Gobierno Conjunto
1. **Aceptación Formal Obligatoria:** Las designaciones anteriores adquirirán vigencia interna única y exclusivamente tras aceptación verificable de los tres socios por uno de los mecanismos de la sección J, vinculada a versión/hash, identidad y mandato; no se presume adopción por consignar sus nombres.
2. **Colegialidad en Decisiones Críticas:** Las seis decisiones de S3-IMP-01 (AJ-G01, AJ-C01, AJ-C02, F-C18, NUM-C01 y NUM-C02) requieren **aceptación expresa y unánime de Felipe Ugalde Hernández, Adrián Garita y Félix Guzmán para cada decisión**. Abstención, silencio o aceptación parcial no satisfacen esta regla. La regla misma sigue siendo **PROPUESTA** hasta su adopción verificable por los tres socios; no sustituye las competencias exigidas en D.2.
3. **Segregación entre Arquitectura e Implementación:** La aprobación formal de una arquitectura, contrato o ficha de decisión técnica **no constituye ni autoriza automáticamente la implementación de código**. La implementación requiere un permiso de ejecución explícito (`G-IMP`), alcance de archivos delimitado y revisión independiente; no concede operaciones Git por inferencia.
4. **Reserva Legal:** Esta propuesta de acuerdo interno no acredita personería, representación legal, poderes registrados ni facultades frente a terceros. Su eventual aceptación interna no equivale a autorización jurídica externa.

---

## D. MANDATOS, LÍMITES Y SEGREGACIÓN DE FUNCIONES

### D.1 Principio de Separación de Deberes (*Separation of Duties / Four-Eyes*)
Para salvaguardar la integridad de los activos financieros y prevenir riesgos de colusión o error material:
1. **Regla de Doble Control:** Ninguna pieza de software que participe en la emisión, verificación, validación o ejecución de capabilities financieras podrá pasar a entornos de prueba integrados o staging sin la revisión formal de al menos un par calificado distinto del autor del cambio.
2. **Desacoplamiento de Roles en S3:**
   - **Autor / Implementador:** Diseña y escribe el código fuente de los parches bajo el alcance delimitado.
   - **Revisor de Seguridad / Operaciones:** Valida que el parche no introduzca aperturas no autorizadas, que respete los límites de memoria/tiempo y que no interactúe con componentes prohibidos.
   - **Autoridad Funcional Financiera:** Valida que los claims y límites monetarios/transaccionales se mantengan dentro del apetito de riesgo corporativo.

### D.2 Matriz de Competencias y Quórum Decisorio

| Tipo de Decisión | Quórum Requerido | Autoridades Mínimas Convocadas | Requisito de Aprobación |
| --- | --- | --- | --- |
| **Designación de funciones y mandatos** | Unánime (propuesto) | Los tres socios | Aceptación verificable de funciones, competencias, límites y regla de unanimidad; mandato enlazado a identidad y versión/hash. |
| **Adopción arquitectónica: AJ-G01** | Unánime (propuesto) | Los tres socios + funciones F/S/D/G acreditadas | Dueño financiero (F), seguridad/protocolo (S), responsable de frontera de datos/DBA (D) y gobernanza de mandatos (G); ratificar trazabilidad V1.1/D02/A02 y reservas. |
| **Adopción arquitectónica: AJ-C01, AJ-C02, F-C18** | Unánime (propuesto) | Los tres socios + F/S acreditadas | Dictamen técnico independiente competente en Ed25519, representación firmada y binding; aceptación funcional financiera y revisión operativa. |
| **Adopción arquitectónica: NUM-C01, NUM-C02** | Unánime (propuesto) | Los tres socios + arquitectura, seguridad y F acreditadas | Evaluación de capacidad/reloj, viabilidad operativa y aceptación expresa del riesgo sintético. |
| **Autorización de implementación (`G-IMP`)** | Ambas autoridades designadas (propuesto) | Seguridad/Operaciones + autoridad financiera | Aceptación expresa de ambas, mandatos y competencias verificados, seis decisiones adoptadas y requisitos K completos. Si Felipe implementa, no aprueba este permiso; no basta el cargo de operaciones para avalar criptografía. |
| **Revisión independiente del parche** | Revisor calificado distinto del autor | Revisor designado por G-IMP | Dictamen verificable sobre diff/hash, invariantes y evidencia offline; ausencia de competencia acreditada bloquea aceptación. |
| **Autorización runtime** | Según cada gate separado | Autoridades competentes de G-OS/G-PG/G-IPC | Permisos nuevos, explícitos y acotados según GATES; fuera del presente acto y de G-IMP. |
| **Aceptación final de gobernanza** | Según G-CLOSE | Autoridades y custodio designados | Aceptación separada de evidencia, riesgos y cierre con alcance expreso; ninguna firma de arquitectura cierra S3. |

Las funciones personales de C son candidatas: **no se acredita aquí cobertura efectiva de F/S/D/G ni se designan revisores**. Antes de adoptar cada decisión debe documentarse quién cubre cada competencia y con qué mandato/evidencia; si falta pericia criptográfica o DBA, se requiere revisor técnico independiente acreditado y autoridad competente designada para aceptar el dictamen. La unanimidad de socios no reemplaza ese requisito. Ningún hash por sí solo autentica al firmante o su mandato.

---

## E. FUENTES CONTRACTUALES Y HASHES CRIPTOGRÁFICOS

A efectos de trazabilidad absoluta y verificación de integridad byte a byte, se relacionan las fuentes documentales, normativas y de código base inspeccionadas, con sus respectivos resúmenes criptográficos SHA-256:

| ID | Documento / Recurso | Ruta en Espacio de Trabajo / Repositorio | SHA-256 |
| --- | --- | --- | --- |
| **FRZ** | Contract Freeze S3-IMP-01 | [ADMINAPPS_AI_FINANCIAL_S3_IMP_01_CONTRACT_FREEZE_HUMAN_DECISION_2026-10-12.md](./ADMINAPPS_AI_FINANCIAL_S3_IMP_01_CONTRACT_FREEZE_HUMAN_DECISION_2026-10-12.md) | `d0c0c16bb7b15bcc5fe006c9751993b518999182c6d3cb926eeefbbbcb3a492f` |
| **NUM** | Propuesta Normativa NUM-C01 | [ADMINAPPS_AI_FINANCIAL_S3_NUM_C01_DOMAIN_POLICY_PROPOSAL_2026-10-12.md](./ADMINAPPS_AI_FINANCIAL_S3_NUM_C01_DOMAIN_POLICY_PROPOSAL_2026-10-12.md) | `633afc9ba2890d68b02e6d0785a1b5fa5b1a902603f1b6a71edc5b59d2157462` |
| **HAG** | Human Architecture Adjudication Gate | [ADMINAPPS_AI_FINANCIAL_S3_HUMAN_ARCHITECTURE_ADJUDICATION_GATE_2026-10-12.md](./ADMINAPPS_AI_FINANCIAL_S3_HUMAN_ARCHITECTURE_ADJUDICATION_GATE_2026-10-12.md) | `0eff5f24accc9696eafb13c14f46038dc1fd50ed78e0c54c894f278c9100fef3` |
| **REC** | Reconciliation Report | [ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md) | `926339d1ef8da26808a71f802043bcef3e35c62fadd49e70c74935bf391d307d` |
| **ADR** | Architecture Decision Record Draft | [ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md) | `181b20e5f1c9e22e6b0480dc513604a25856909e8c49b406199916d9b4528ea2` |
| **MAT** | Human Approval Matrix | [ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md) | `c56d6ee9f15022839cea220a748de8e357424ec46d5cdf88add0dddae617e855` |
| **PLAN** | Phased Implementation Plan | [ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md) | `a58fb7fd87032148a319d8442ec7708d2f8b1804d1b0f50256d7e48382a53abd` |
| **GATES** | Authorization Boundary Runtime Gates | [ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md) | `259a49d32aa206373891c4079f0ad35284da95602b703052804747fb77f343cf` |
| **ADJ** | Security Contract Adjudication | [ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_2026-10-09.md) | `6d16f47e4d2ed6a742294a8ccd4c65399ddbb3f0271b22aab081b96a143a571a` |
| **EVID** | Adjudication Evidence JSON | [ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json](./ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json) | `57e8a44b89bc1af0598c6fc1f9691a461deaf6eb227ff413490da5e093946ec4` |
| **OFF** | Offline Evidence JSON | [ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json](./ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json) | `4bfdd21a0f1c677f3ac3f1ccb81cb6fb8731d73c78b7c11d959638aae2058e33` |
| **D02** | Security Decision 02-A | [ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) | `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3` |
| **A02** | Security Amendment 02 | [ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md) | `e03022a6ca4da9eeb9022b50972d30ff6628fa5a5ab9614ba3e21d6a5af9ef79` |
| **ER** | Decision 02-A Execution Report | [ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md](./ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md) | `da5d01ba8f0e12c66ed068c868568bc4fa208871d478a017453562290e2eea2b` |
| **CAP** | Capabilities Source Code | `backend/apps/financial/capabilities.py` | `b389eb73799eb13ea8af0285dbf4d6f20a3b917fe58d7707da96fadfc24f44dd` |
| **EXE** | Executor Source Code | `backend/apps/financial/executor.py` | `8b39ada47540612f5f5bcf8361bff7b6154847e2f62d897f29a813721eaf7e46` |
| **ISS** | Issuer Source Code | `backend/apps/financial/issuer.py` | `9d8c3535500cbeec299a2e7df2e6ecb3c69383e8e22a9accfa50b37ead785859` |
| **SVC** | Services Source Code | `backend/apps/financial/services.py` | `1a0b8491900b041ac9f088ffbd275d8b19212e1e960ce8c7343395ffb96d11d8` |
| **AUTH** | Authorization Source Code | `backend/apps/financial/authorization.py` | `53a314f4553842b919013e90580c0e499c010cffd91aa074ea2608e659bf13e5` |
| **MODELS**| Financial Models Code | `backend/apps/financial/models.py` | `898e485465ee836ccef735e5310d56c63eaf8ba1fbe3a26ce3ae576a9179a876` |
| **TESTS** | Financial Unit Tests Code | `backend/apps/financial/tests.py` | `dcfb23119739e851b306d790828b28cd7c3069e62fe5cc39ef9ea5ccb292e585` |
| **M0007** | Migration 0007 Code | `backend/apps/financial/migrations/0007_decision_02_a_executor_boundary.py` | `b098ed9d9e79dee94c5fce2d8542c93316a2d09dbec4065d1b4f79fa4602057f` |
| **M0005** | Migration 0005 Code | `backend/apps/financial/migrations/0005_s3_runtime_admission_boundary.py` | `d2c7dfc9ddd944bda90f7b5dce17b48646928e0ee51f9727f0f98152d476a384` |
| **CRTEST**| Offline Capability Test Script | `backend/scripts/tests/test_s3_capability_offline.py` | `80569387baf0e1faa8bc3948f1f84c35336bdbdd5c42e1bbcec6841c00994e74` |
| **REQ** | Backend Requirements File | `backend/requirements.txt` | `cf804dcb0092c3daaa97831806e1eefa2c91edcabdb1a7e4f9ca21dea7bfb29f` |
| **V11** | External Contract V1.1 (Read-Only) | `../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md` | `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f` |
| **A01** | External Amendment 01 (Read-Only) | `../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_AMENDMENT_01_DECISION_RECORD_2026-10-08.md` | `677cb7006c04ce35b6127e589fb46b26bb44aae491509c4fe2b0a39fb0eeacf8` |
| **TP** | External Models (Read-Only) | `../../../isosmart/backend/foundation/models.py` | `4fa28f1cbff3aa132dcb41d867253903cf36f319d3b170b97cd0786cdf62d09d` |

---

## F. SEIS DECISIONES PROPUESTAS (FICHAS FORMALES)

A continuación se presentan las seis fichas de decisión en estado `PENDING_HUMAN_APPROVAL`, estructuradas conforme a la metodología de arquitectura de seguridad para su adopción, rechazo o modificación fundada por las autoridades humanas:

```
================================================================================
FICHA DE DECISIÓN: AJ-G01
================================================================================
1. IDENTIFICADOR: AJ-G01 (Alcance Contractual, Preservación D02 y Estado A02)
2. ESTADO ACTUAL: PENDING_HUMAN_APPROVAL
3. OPCIÓN PROPUESTA:
   - Ratificar formalmente la adopción del Contrato de Autoridad Financiera V1.1
     (V11) y la enmienda A01 como marco contractual rector para el subsistema S3.
   - Preservar íntegramente la aprobación histórica conferida en D02, estrictamente
     acotada a la remediación histórica LOGIN/Python del ejecutor de capabilities;
     no constituye permiso permanente de implementación, laboratorio o runtime.
   - Mantener el documento A02 en estado formal APPROVAL_PENDING hasta tanto se
     adjudique la totalidad del paquete normativo y se determine la estructura
     definitiva de firma.
   - Resolver el vínculo pendiente de V1.1 con acta/hash/mandato: V11 se titula
     propuesta y A02 registra FINANCIAL_CONTRACT_V1_1 = HUMAN_APPROVED sin
     cadena completa localizada; no confundir ese registro con aprobación de A02.
     Aportar acta original o ratificación nueva con reservas y precedencia;
     no inventar aprobación retrospectiva ni inferir inexistencia de la original.
4. JUSTIFICACIÓN TÉCNICA:
   Permite estabilizar la línea base normativa sin incurrir en regresiones
   contractuales, reconociendo el antecedente de D02 sin expandir su alcance de
   manera subrepticia a producción o staging, y manteniendo la trazabilidad hacia
   los repositorios vinculados.
5. EVIDENCIA DE RESPALDO:
   V11 (§§1–12), A01, D02 (`66af713c...`), A02 (`e03022a6...`), HAG (§B.1).
6. COMPATIBILIDAD Y LIMITACIONES:
   No altera contratos externos; circunscribe el reconocimiento de D02 al
   perímetro técnico donde fue emitido.
7. RIESGOS RESIDUALES:
   Riesgo de que terceros interpreten la ratificación de V1.1 como autorización
   de operación financiera. Se mitiga mediante la declaración expresa de no
   operabilidad financiera en esta acta.
8. AUTORIDADES REQUERIDAS:
   Aceptación expresa y unánime de Felipe Ugalde Hernández, Adrián Garita y
   Félix Guzmán, bajo la regla propuesta C.4 y las competencias/mandatos D.2.
9. DISPOSICIÓN: PENDING (Adoptar / Modificar / Rechazar)
================================================================================
```

```
================================================================================
FICHA DE DECISIÓN: AJ-C01
================================================================================
1. IDENTIFICADOR: AJ-C01 (Wire Format, Gramática y Criptografía Asimétrica)
2. ESTADO ACTUAL: PENDING_HUMAN_APPROVAL
3. OPCIÓN PROPUESTA:
   - Adoptar el perfil de representación C-B: serialización JSON en formato wire
     estricto, canónico, ordenado lexicográficamente por claves, compacto
     (separadores ',' y ':'), garantizando representación ASCII pura
     (ensure_ascii=True), sin espacios en blanco superfluos, sin caracteres de
     escape no canónicos, depth 1 a nivel raíz de claims.
   - Ratificar Ed25519 (algoritmo único admisible, llaves públicas de 32 bytes,
     firmas desnudas de 64 bytes).
   - Preservar la construcción de la representación firmada M(C) sin alteraciones
     ni agregados de headers/metadatos no contemplados.
4. JUSTIFICACIÓN TÉCNICA:
   Propone rechazar ambigüedad léxica JSON y duplicidad de claves decodificadas.
   Preserva Ed25519 y la representación del emisor actual: sin fallback permisivo,
   sin sustituir por JWT/JWS/JCS, sin cambiar dominio ni versión criptográfica.
   No demuestra seguridad de claves, autenticidad del contexto ni control runtime.
5. EVIDENCIA DE RESPALDO:
   FRZ (§§C–D), EVID (caso canonical en stdlib_json_representation_diagnostic,
   J(C)=695 bytes, M(C)=739 bytes), CAP (mint_capability / verify_capability); diagnóstico de representación,
   no evidencia de verificación Ed25519 nueva.
6. COMPATIBILIDAD Y LIMITACIONES:
   Incompatibilidad con consumidores que envíen JSON formateado (pretty-printed)
   o con secuencias de escape arbitrarias. Exige estricto cumplimiento del wire
   format a la entrada del verificador.
7. RIESGOS RESIDUALES:
   Rechazo de payloads válidos en semántica pero no estrictos en formato wire.
   Su aceptación humana sigue pendiente; estrechar el wire afecta compatibilidad.
8. AUTORIDADES REQUERIDAS:
   Aceptación expresa y unánime de Felipe Ugalde Hernández, Adrián Garita y
   Félix Guzmán, bajo la regla propuesta C.4 y las competencias/mandatos D.2.
9. DISPOSICIÓN: PENDING (Adoptar / Modificar / Rechazar)
================================================================================
```

```
================================================================================
FICHA DE DECISIÓN: AJ-C02
================================================================================
1. IDENTIFICADOR: AJ-C02 (Modelo de Material, Tenant Assertion y Contexto Confiable)
2. ESTADO ACTUAL: PENDING_HUMAN_APPROVAL
3. OPCIÓN PROPUESTA:
   - Seleccionar el modelo de material de 9 campos canónicos (Material9).
   - Exigir un sub-objeto de assertion de 4 campos cerrados (Assertion4):
     `adminapps_tenant_id`, `tenant_projection_id`,
     `tenant_projection_source_event_id`, `tenant_projection_source_version`.
   - Implementar enlace criptográfico y contextual estricto (binding) entre
     el token de capability, el material JSON canónico y el contexto de ejecución.
   - Declarar mandato obligatorio de Contexto Confiable suministrado exclusivamente
     por canales autenticados fuera de banda (out-of-band authenticated context),
     rechazando de plano identidades o parámetros de tenant provenientes del
     cuerpo (body) no autenticado de la petición.
4. JUSTIFICACIÓN TÉCNICA:
   Propone prevenir sustitución de contexto mediante binding tenant/material
   validado antes de DB. Igualdad de datos no autentica a un caller; proyección,
   frescura y procedencia del contexto requieren controles de su autoridad.
   No equivale a control implementado ni cierra la confianza residual D02.
5. EVIDENCIA DE RESPALDO:
   FRZ (§§D.2, E.2), MV1 (material sintético canónico de 480 bytes, SHA-256
   `bd57f7c7520b3f2206c520b23123eec23a282bab06fb59b6dddbd93b3e576da6`),
   HAG (§B.1), EXE.
6. COMPATIBILIDAD Y LIMITACIONES:
   Los fixtures históricos de pruebas de integración con assertions de dos campos
   serán incompatibles con este esquema. Requiere fixtures sintéticos nuevos
   bajo G-IMP explícito, sin reescribir fixtures históricos.
7. RIESGOS RESIDUALES:
   Si el canal autenticado proveedor del contexto falla o se desincroniza, las
   peticiones legítimas serán denegadas como CAPABILITY_BINDING_DENIED según FRZ D.2.
8. AUTORIDADES REQUERIDAS:
   Aceptación expresa y unánime de Felipe Ugalde Hernández, Adrián Garita y
   Félix Guzmán, bajo la regla propuesta C.4 y las competencias/mandatos D.2.
9. DISPOSICIÓN: PENDING (Adoptar / Modificar / Rechazar)
================================================================================
```

```
================================================================================
FICHA DE DECISIÓN: F-C18
================================================================================
1. IDENTIFICADOR: F-C18 (Ratificación del Conjunto Cerrado de 18 Claims)
2. ESTADO ACTUAL: PENDING_HUMAN_APPROVAL
3. OPCIÓN PROPUESTA:
   - Ratificar que la estructura formal de una capability de autoridad financiera
     S3 contiene **exactamente 18 claims únicos y obligatorios**, sin supresión
     ni adición de campos:
     1. `alg`
     2. `aud`
     3. `capability_id`
     4. `environment`
     5. `exp`
     6. `grant_id`
     7. `grant_version`
     8. `iat`
     9. `iss`
     10. `jti`
     11. `kid`
     12. `material_request_hash`
     13. `nbf`
     14. `operation`
     15. `organization_id`
     16. `producer_registration_id`
     17. `product_id`
     18. `version`
   - Aclarar en esta acta las menciones históricas a "19 claims", sin modificar
     las fuentes: son 18 claims criptográficos y 19 decisiones arquitectónicas
     generales del paquete S3; estas seis decisiones habilitantes no son 19 claims.
   - Prohibir taxativamente la incorporación de claims arbitrarios o extensiones
     dinámicas no normalizadas en el contrato.
4. JUSTIFICACIÓN TÉCNICA:
   La extracción por Árbol de Sintaxis Abstracta (AST) sobre `capabilities.py`
   demuestra que tanto `_REQUIRED` como el diccionario de
   emisión en `mint_capability` constan de exactamente 18 claves. La ratificación
   cierra la discrepancia con documentos que mencionaban 19 claims debido a un
   conteo documental incorrecto; no se atribuye una causa no acreditada.
5. EVIDENCIA DE RESPALDO:
   CAP (`b389eb73...`, líneas de definición de constantes y retorno), FRZ (§§B.1,
   CR-T03), EVID.
6. COMPATIBILIDAD Y LIMITACIONES:
   Totalmente compatible con la implementación base de `capabilities.py`. Cualquier
   payload cuyo conjunto de claves no coincida exactamente deberá rechazarse
   con `CAPABILITY_CLAIMS_INVALID`; cardinalidad sola no basta.
7. RIESGOS RESIDUALES:
   La cardinalidad no prueba tipos, firma, binding ni contexto confiable;
   su comprobación forma parte del perfil propuesto, sujeto a pruebas futuras.
8. AUTORIDADES REQUERIDAS:
   Aceptación expresa y unánime de Felipe Ugalde Hernández, Adrián Garita y
   Félix Guzmán, bajo la regla propuesta C.4 y las competencias/mandatos D.2.
9. DISPOSICIÓN: PENDING (Adoptar / Modificar / Rechazar)
================================================================================
```

```
================================================================================
FICHA DE DECISIÓN: NUM-C01
================================================================================
1. IDENTIFICADOR: NUM-C01 (Límites Numéricos de Capacidad Sintética en controlled_test)
2. ESTADO ACTUAL: PENDING_HUMAN_APPROVAL
3. OPCIÓN PROPUESTA:
   - Adoptar formalmente el perfil de política `S3-CONTROLLED-TEST-CAPACITY-V1`,
     con los siguientes límites numéricos máximos para el material canónico:
     - `L_R = 64`: Longitud máxima de `request_class`, en caracteres/bytes ASCII.
     - `L_E = 256`: Longitud máxima de cada `evidence_id`, en bytes ASCII.
     - `N_E = 32`: Cantidad máxima de referencias en `evidence_ids` por solicitud.
     - `B_M = 9169`: Cota máxima derivada de bytes para el material JSON canónico.
   - Derivación matemática formal verificada:
     $B_M = 818 + L_R + (N_E \times (L_E + 3) - 1) = 818 + 64 + (32 \times (256 + 3) - 1) = 9169\text{ bytes}$.
   - **DECLARACIÓN EXPRESA DE RESTRICCIÓN DE DOMINIO:**
     Los presentes valores constituyen una **propuesta normativa sintética nueva**,
     diseñada con carácter prudencial y defensivo para pruebas unitarias y offline
     en AdminApps (`controlled_test`). **NO se presentan ni deben interpretarse
     como máximos históricos derivados del dominio de producción, ni son
     extensibles a los contratos operativos de ISO Smart, MedSupplier, ambientes
     de staging o producción.**
4. JUSTIFICACIÓN TÉCNICA:
   Propone una cota finita cuya aritmética está documentada en NUM. Su aplicación
   temprana debe verificarse bajo G-IMP; la cota por sí sola no demuestra control
   de recursos implementado ni inmunidad frente a agotamiento de memoria.
5. EVIDENCIA DE RESPALDO:
   NUM (`633afc9ba2890d68b02e6d0785a1b5fa5b1a902603f1b6a71edc5b59d2157462`),
   FRZ (§§C, D.4), validación offline Python stdlib con digest SHA-256
   `9f466f58842e5a90e16fdfaf520326beb60c267672c9dd7f3e34de4e8462bcb7`.
6. COMPATIBILIDAD Y LIMITACIONES:
   Solo en fixtures sintéticos AdminApps controlled_test, si se aprueba, quien emita una `request_class` > 64 caracteres,
   un `evidence_id` > 256 bytes o más de 32 evidencias será rechazado
   tajantemente (`MATERIAL_REQUEST_INVALID`). No se dispone a la fecha de un
   censo empírico de todos los productores externos posibles.
7. RIESGOS RESIDUALES:
   Riesgo de rechazo prematuro de transacciones legítimas con estructuras de
   evidencia mayores en caso de extender este perfil sin recalibración previa.
   Por ello se acota estrictamente a `controlled_test`.
8. AUTORIDADES REQUERIDAS:
   Aceptación expresa y unánime de Felipe Ugalde Hernández, Adrián Garita y
   Félix Guzmán, bajo la regla propuesta C.4 y las competencias/mandatos D.2.
9. DISPOSICIÓN: PENDING (Adoptar / Modificar / Rechazar)
================================================================================
```

```
================================================================================
FICHA DE DECISIÓN: NUM-C02
================================================================================
1. IDENTIFICADOR: NUM-C02 (Parámetros Temporales, Sincronización y Ventana TTL)
2. ESTADO ACTUAL: PENDING_HUMAN_APPROVAL
3. OPCIÓN PROPUESTA:
   - Formato temporal estricto UTC20 (`YYYY-MM-DDTHH:MM:SSZ`), con sufijo 'Z',
     sin microsegundos y sin desplazamientos numéricos de zona horaria (+HH:MM).
   - Tolerancia de desincronización horaria (clock skew): **exactamente cero
     segundos (`skew = 0`)**.
   - Contrato temporal propuesto, sin tolerancias implícitas:
     iat <= nbf < exp
     0 < (exp - iat).total_seconds() <= 60
     nbf <= now < exp
     TTL medido desde iat; no desde nbf. Con UTC20, emisión sintética entera 1–60 s.
   - now local UTC aware, tomado una vez por verificación y conservando precisión
     de microsegundos, sin truncar; nunca tiempo aportado por caller no confiable.
     UTC20 sin fracciones aplica a iat/nbf/exp, no al reloj de verificación.
     Proponer revalidación en memoria inmediatamente antes de DB; no garantiza
     expiración atómica al commit. Sin autorización productiva.
4. JUSTIFICACIÓN TÉCNICA:
   Limita la vigencia sintética desde emisión sin gracia antes de nbf ni después
   de exp; no sustituye controles de replay ni garantiza un reloj seguro.
5. EVIDENCIA DE RESPALDO:
   D02 (ventana sintética), CAP (`_iso`, `_time`, `verify_capability`),
   CRTEST, FRZ (§D.3). FRZ exige exp > nbf; CAP histórico compara nbf <= exp
   y TTL desde iat. Se registra esa diferencia sin modificar código ni fuentes.
   El borrador previo medía exp - nbf por error; esta ficha lo corrige a exp - iat.
6. COMPATIBILIDAD Y LIMITACIONES:
   Requiere que los emisores sintéticos en las pruebas mantengan sincronización
   compatible con el validador. Claims con fracciones o sin 'Z' deberán denegarse
   como CAPABILITY_TIME_INVALID; now fuera de [nbf, exp), CAPABILITY_EXPIRED
   según FRZ D.2. No presentar estos rechazos propuestos como ya implementados.
7. RIESGOS RESIDUALES:
   Un desfase entre relojes puede denegar solicitudes legítimas con skew cero.
   Riesgo pendiente de aceptación humana exclusivamente para fixtures sintéticos
   AdminApps `controlled_test`; no se acredita sincronización ni reloj seguro.
8. AUTORIDADES REQUERIDAS:
   Aceptación expresa y unánime de Felipe Ugalde Hernández, Adrián Garita y
   Félix Guzmán, bajo la regla propuesta C.4 y las competencias/mandatos D.2.
9. DISPOSICIÓN: PENDING (Adoptar / Modificar / Rechazar)
================================================================================
```

---

## G. COMPATIBILIDAD Y RIESGOS RESIDUALES

Las fichas F son propuestas normativas pendientes: todo rechazo o control allí descrito es requisito futuro, no evidencia de implementación. Se preservan los 18 claims exactos de FRZ/CAP, Ed25519, `M(C) = b'adminapps.financial.admission-capability.v1\n' + J(C)`, versión 1 y SHA-256 del material conforme. El orden canónico de `evidence_ids` conserva multiplicidad; se prohíben deduplicación, truncamiento y normalizaciones que cambien el hash. No se alteran comportamientos S1/S2 ni se habilitan PostgreSQL/IPC.

### G.1 Incompatibilidades Históricas Documentadas
1. **Assertion de Cuatro Campos vs. Fixtures Históricos:**
   - La suite de tests preexistente en `backend/apps/financial/tests.py` y ciertos escenarios del ejecutor histórico utilizaban estructuras abreviadas de tenant assertion (con únicamente dos campos).
   - Bajo el perfil propuesto en AJ-C02 (Assertion4), tales estructuras serán **rechazadas**.
   - No se alterarán los tests históricos para disfrazar este cambio; en su lugar, se mantendrán separados y se documentará formalmente que la nueva ruta impone el esquema de cuatro campos.
2. **Validación Temprana de UUID vs. Expectativa de Error de Firma:**
   - Ciertas pruebas negativas históricas inyectaban cadenas alfanuméricas inválidas en identificadores UUID esperando recibir `CAPABILITY_SIGNATURE_INVALID`.
   - Bajo la gramática estricta de C-B y la validación léxica previa, la solicitud fallará tempranamente con `CAPABILITY_CLAIMS_INVALID` o `CAPABILITY_MALFORMED`, sin llegar a computar Ed25519. Es la precedencia propuesta de FRZ D.2; no permite renombrar resultados históricos como PASS.
3. **Estrechamiento Normativo de Entradas (Límites NUM-C01):**
   - Entradas con `request_class` mayor a 64 bytes o más de 32 identificadores de evidencia deberán rechazarse completas, sin truncamiento ni deduplicación, solo bajo el perfil sintético aprobado. No existía límite estricto previo en la implementación histórica, lo cual constituía una vulnerabilidad potencial.

### G.2 Riesgos Residuales Pendientes de Aceptación Humana
1. **Ausencia de Censo Integral de Productores Externos:** No se cuenta con una base de datos de telemetría de todos los clientes potenciales fuera de AdminApps. El perfil numérico candidato se limita a fixtures sintéticos AdminApps controlled_test, pero requerirá un censo formal antes de pensar en una migración hacia producción.
2. **Verificación Pre-DB vs. Momento de Commit:** La propuesta revalida en memoria antes de DB, pero no garantiza expiración atómica al commit. La DB actual no recibe iat/nbf/exp; persiste el riesgo de commit posterior a exp. No se acredita mitigación mediante descarte de colas o ausencia de I/O; su tratamiento pertenece al gate correspondiente, fuera de S3-IMP-01.

---

## H. CONDICIONES Y EXCLUSIONES OPERATIVAS

Para garantizar que el proceso de gobernanza no introduzca alteraciones en la infraestructura ni ponga en riesgo la estabilidad del sistema, se fijan las siguientes exclusiones taxativas:

### H.1 Exclusiones de Infraestructura y Datos
1. **Prohibición de Conexión a PostgreSQL Operacional:** Queda terminantemente prohibido habilitar, conectar o requerir instancias vivas de PostgreSQL para las validaciones documentales o las futuras pruebas offline derivadas de esta acta.
2. **Prohibición de IPC y Sockets de Red:** No se autoriza la apertura de sockets de dominio UNIX, conexiones TCP/IP ni comunicación entre procesos con subsistemas externos.
3. **Prohibición de Ejecución en Host Lab:** Queda expresamente excluida la reactivación o ejecución de scripts en el entorno de Host Lab (`s3_isolation_host_lab.sh` o análogos).
4. **Prohibición de Migraciones de Base de Datos:** No se permite la aplicación (`migrate`) de las migraciones pendientes `0005` o `0007` en ningún motor de persistencia.
5. **Prohibición de Modificaciones a Nivel de Sistema Operativo:** No se ejecutarán comandos mediante `sudo`, ni modificaciones a servicios `systemd`, políticas de `seccomp`, `sysctl` o reglas de firewall.
6. **Prohibición Absoluta de Fondos u Operaciones Financieras Reales:** Ninguna capability emitida o evaluada bajo este marco tiene validez económica ni vinculación con fondos bancarios, pasarelas de pago o cuentas reales.
7. **No Integración con ISO Smart o MedSupplier:** Queda vetada la invocación o cruce de datos con entornos operacionales de repositorios externos hermanos.
8. **Otras Exclusiones:** No autoriza credenciales reales, staging/producción, S4–S6, stage, commit, push, merge, reset ni checkout. Arquitectura y G-IMP no conceden permisos operativos por inferencia.

---

## I. REGISTRO DE ADOPCIÓN, RECHAZO O MODIFICACIÓN

La siguiente matriz deberá ser completada por los tres socios al momento de su sesión deliberativa formal. La aceptación debe ser individual y expresa por cada socio para cada decisión, vinculada al hash definitivo y al mandato; una firma genérica no suple selecciones omitidas. En este borrador, todos los campos permanecen deliberadamente en estado de propuesta pendiente (`PENDING`):

| Decisión | Opción Propuesta | Pronunciamiento Humano (Adoptar / Modificar / Rechazar) | Modificaciones o Reservas Aprobadas | Fecha y Hora Efectiva (America/Costa_Rica) |
| --- | --- | :---: | --- | :---: |
| **AJ-G01** | Ratificar V1.1, preservar D02, mantener A02 pendiente | `PENDING` | *Sin completar* | *Sin completar* |
| **AJ-C01** | Wire C-B estricto, Ed25519, representación M(C) | `PENDING` | *Sin completar* | *Sin completar* |
| **AJ-C02** | Material9, Assertion4, binding estricto, contexto confiable | `PENDING` | *Sin completar* | *Sin completar* |
| **F-C18** | Ratificar exactamente 18 claims únicos de capability | `PENDING` | *Sin completar* | *Sin completar* |
| **NUM-C01** | Límites sintéticos: $L_R=64, L_E=256, N_E=32, B_M=9169$ | `PENDING` | *Sin completar* | *Sin completar* |
| **NUM-C02** | UTC20; skew=0; `iat <= nbf < exp`; `0 < (exp - iat).total_seconds() <= 60`; `nbf <= now < exp` | `PENDING` | *Sin completar* | *Sin completar* |

---

## J. FIRMAS Y EVIDENCIA DE MANDATO

El presente documento carece de validez ejecutiva hasta tanto sea suscrito por los tres socios identificados. Se prohíbe el uso de firmas simuladas, marcas temporales inventadas o presunciones de consentimiento.

### J.1 Socio 1 — Dirección Técnica y Arquitectura
- **Nombre Completo:** Felipe Ugalde Hernández
- **Cargo / Función Asignada:** Chief Technology Officer (CTO) & Responsable de Arquitectura Técnica
- **Documento de Identificación:** __________________________________________________
- **Mecanismo de Aceptación:** [ ] Firma Digital Calificada / [ ] Firma Manuscrita / [ ] Acta de Asamblea
- **Mandato Invocado:** Socio Fundador / Responsable de Arquitectura Técnica Smart3AI
- **Firma:** __________________________________________________
- **Fecha y Hora de Suscripción:** __________________________________________________
- **Huella Digital del Documento (SHA-256 Definitivo):** __________________________________________________

### J.2 Socio 2 — Operaciones y Seguridad de Infraestructura
- **Nombre Completo:** Adrián Garita
- **Cargo / Función Asignada:** Responsable de Operaciones e Infraestructura
- **Documento de Identificación:** __________________________________________________
- **Mecanismo de Aceptación:** [ ] Firma Digital Calificada / [ ] Firma Manuscrita / [ ] Acta de Asamblea
- **Mandato Invocado:** Socio Fundador / Responsable de Operaciones Smart3AI
- **Firma:** __________________________________________________
- **Fecha y Hora de Suscripción:** __________________________________________________
- **Huella Digital del Documento (SHA-256 Definitivo):** __________________________________________________

### J.3 Socio 3 — Producto y Autoridad Funcional Financiera
- **Nombre Completo:** Félix Guzmán
- **Cargo / Función Asignada:** Responsable de Producto & Autoridad Funcional Financiera Candidata
- **Documento de Identificación:** __________________________________________________
- **Mecanismo de Aceptación:** [ ] Firma Digital Calificada / [ ] Firma Manuscrita / [ ] Acta de Asamblea
- **Mandato Invocado:** Socio Fundador / Responsable Comercial y de Producto Smart3AI
- **Firma:** __________________________________________________
- **Fecha y Hora de Suscripción:** __________________________________________________
- **Huella Digital del Documento (SHA-256 Definitivo):** __________________________________________________

---

## K. CONDICIONES PARA AUTORIZACIÓN POSTERIOR G-IMP

### K.1 Criterios de Desbloqueo Previo de S3-IMP-01
El inicio de la fase de implementación técnica (`S3-IMP-01`) no podrá tener lugar bajo ninguna circunstancia sin el cumplimiento estricto y acumulativo de las siguientes condiciones previas:
1. **Designación Válida y Aceptada:** Perfeccionamiento de la designación de autoridades con las firmas de los tres socios en la Sección J de esta acta.
2. **Adopción Eficaz de las Seis Decisiones:** Pronunciamiento expreso unánime verificable de los tres socios, con competencias D.2 acreditadas, sobre las seis fichas (AJ-G01, AJ-C01, AJ-C02, F-C18, NUM-C01, NUM-C02).
3. **Ratificación de Parámetros y Riesgos:** Aceptación expresa de la cota $B_M=9169$ bytes, el skew cero y la limitación a `controlled_test`.
4. **Aceptación Formal de Incompatibilidades:** Asunción documentada de que los fixtures con assertions históricos serán incompatibles con la nueva ruta.
5. **Emisión de Autorización G-IMP Independiente:** Expedición de un acta o documento resolutivo separado que confiera específicamente el permiso `G-IMP`.
6. **Asignación de Implementador y Revisor Independiente:** Designación formal de la persona a cargo de escribir el código y del revisor par independiente, garantizando que Felipe Ugalde Hernández no actúe como único aprobador de su propio desarrollo.
7. **Contenido Verificable de G-IMP:** Identificar firmantes y mandatos, acta definitiva y SHA-256 calculado fuera de su contenido, decisiones adoptadas y reservas, baseline del parche, archivos exactos existentes/nuevos, implementador, revisor independiente competente y custodio de evidencia. Registrar fecha efectiva/zona solo cuando exista aceptación auténtica. Un cambio de bytes exige nuevo hash y nueva vinculación de aceptación; no insertar un autohash circular en el acta.
8. **Permiso de Pruebas Delimitado:** Enumerar pruebas offline permitidas CR-T01–06/MT-T01–03, entorno y datos sintéticos, resultados/artefactos exigidos, condición Z, aceptación K.3, STOP/rollback K.4 y exclusiones H. Todos esos campos deben resolverse expresamente; no hay permiso implícito por aprobar arquitectura.

### K.2 Delimitación Estricta del Futuro Parche (Alcance de Archivos)
Los siguientes archivos son **candidatos**, sin permiso vigente. La futura autorización `G-IMP` deberá enumerar explícitamente los que autorice, incluidos tests existentes/nuevos; ninguna fila concede permiso ni permite añadir archivos por inferencia:

| Archivo Candidato | Naturaleza del Cambio Autorizable |
| --- | --- |
| `backend/apps/financial/capabilities.py` | Implementación de parser estricto C-B, decodificación base64url sin relleno superfluo, validación de 18 claims exactos, chequeo temporal UTC20/skew=0 y manejo tipado de excepciones. Preservación intacta de `mint_capability` normal y construcción de $M(C)$. |
| `backend/apps/financial/executor.py` | Exigencia de contexto confiable fuera de banda, validación de Assertion4, binding estricto entre token y material, captura de snapshot inmutable y barrera de rechazo previo a cualquier interacción con base de datos. |
| `backend/apps/financial/services.py` | Incorporación de validador puro desacoplado o adaptador de ruta protegida sin alterar las firmas transaccionales preexistentes de S1 y S2. |
| `backend/scripts/tests/test_s3_capability_offline.py` | Incorporación de vectores de prueba offline complementarios para la verificación de fronteras sin tocar el oráculo histórico. |
| `backend/scripts/tests/test_s3_imp01_contract_offline.py` *(Nuevo archivo propuesto)* | Módulo exclusivo y dedicado para la matriz de pruebas offline CR-T01 a CR-T06 y MT-T01 a MT-T03 con dobles terminales para verificar condición Z en los casos offline; no certifican aislamiento runtime. |

**Prohibición Expresa:** Cualquier edición a `models.py`, `authorization.py`, migraciones de base de datos, `settings.py`, scripts de sistema o repositorios vinculados fuera del permiso provocará **STOP del parche y revisión de la vigencia de G-IMP**. No se revierten cambios preexistentes ajenos.

### K.3 Criterios de Aceptación para las Pruebas Futuras (Garantía de Efecto Cero en DB)
1. **Preservación de Invariantes Criptográficos:** Los 18 claims deben preservarse íntegros; la función de representación firmada $M(C)$ y el hash SHA-256 no pueden sufrir alteraciones.
2. **Cero Efectos en Base de Datos ante Rechazos Pre-DB (`Condición Z`):**
   - Ante cualquier falla de formato wire, error léxico, reclamo ausente, firma inválida, expiración, desalineación de tenant o binding incorrecto, la ejecución **debe abortar antes de cualquier interacción con la capa de persistencia**.
   - Se verificará que exista:
     - Cero lecturas o escrituras a tablas de base de datos o registro de alias.
     - Cero apertura de conexiones (`connection`, `ensure_connection`).
     - Cero creación de cursores SQL (`connection.cursor()`).
     - Cero transacciones atómicas (`transaction.atomic()`).
     - Cero SQL, cero ORM y cero efectos financieros.
   - Las pruebas deberán instrumentarse con dobles de prueba que lancen excepción crítica si cualquier método de base de datos es invocado durante un rechazo criptográfico o de binding pre-DB.
   - Condición Z no aplica a decisiones financieras legítimas dentro de la frontera PostgreSQL: requieren su contrato transaccional y permiso G-PG independiente. Ausencia de resultados runtime no demuestra aislamiento.
3. **Evidencia de Aceptación:** Revisor independiente deberá contrastar diff y hashes con G-IMP, resultados positivos/negativos CR-T01–06/MT-T01–03, bytes/M(C)/firma/hash del emisor normal, límites NUM-C01, fronteras temporales NUM-C02 con microsegundos de now, multiplicidad de evidencia y rechazo Assertion4 histórico. Preservar fixtures y resultados históricos, comportamientos S1/S2 y exclusiones; sin controles runtime ni cierre de S3 atribuidos a tests offline.

### K.4 Condiciones STOP y Rollback Controlado
**STOP obligatorio:** mandato/decisión/permiso faltante o hash/baseline divergente; archivo fuera del alcance; cambio de claims, dominio, versión, M(C) o hash de material conforme; fallback permisivo; binding basado en caller no autenticado; rechazo pre-DB que toque DB/ORM/SQL/transacciones; excepción sin tipar, consumidor incompatible no adjudicado o incumplimiento de pruebas/exclusiones. Conservar evidencia del fallo sin fabricar PASS y someterlo a autoridades competentes antes de reanudar.

**Rollback:** detener el trabajo y retirar únicamente el parche propio identificado contra su baseline en copia aislada, bajo el procedimiento explícito de G-IMP; preservar índice, cambios ajenos, fixtures y evidencia históricos. Prohibidos reset global, borrado indiscriminado y reactivar operación con el parser anterior. Cualquier ampliación de alcance requiere autorización nueva verificable; este borrador no autoriza ejecutar rollback de producto.

---
*Fin del Acta Formal de Designación de Autoridades y Adjudicación de Decisiones S3-IMP-01 (Borrador).*
