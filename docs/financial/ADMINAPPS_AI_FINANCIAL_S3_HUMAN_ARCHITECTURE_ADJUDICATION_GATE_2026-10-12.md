# S3 — Human Architecture Adjudication Gate

Preparación: **2026-10-12, America/Costa_Rica**. Propuesta técnica consolidada; **no acta aprobada**.
Único entregable nuevo. No reemplaza ni modifica los cinco documentos del 2026-10-09.

## A. Executive Recommendation

Recomendar las 19 selecciones de la sección C para adopción, modificación o rechazo por autoridades humanas con mandato acreditado. Mantener C-B, Ed25519/dominio D02, binding tenant/material, executor LOGIN con verificación Python, issuer independiente, ownership y ACL explícitos, FORCE RLS, SERIALIZABLE, revocación transaccional y AF_UNIX pathname con peer mutuo y relay issuer → executor. Las recomendaciones son definitivas para esta revisión, pero su eficacia depende de decisiones y parámetros vinculantes; no equivalen a implementación ni validación.

**Hallazgo nuevo F-C18:** el paquete llama «19 claims» a un conjunto que contiene **18 claves**. El AST de `_REQUIRED` y del dict de `mint_capability` confirma 18 en ambos; la lista textual ADJ C.1 también enumera 18. D02 describe las vinculaciones sin exigir una cardinalidad numérica 19. Recomendar ratificar el conjunto exacto existente mediante aclaración documental nueva; no añadir una clave para cuadrar el conteo ni reescribir los documentos anteriores. La ratificación pertenece a AJ-G01/C01 y B-C01. Las **19 decisiones AJ** sí están completas y no se confunden con los claims.

| Dimensión | Resultado efectivo |
| --- | --- |
| Recomendación técnica | 19/19 `TECHNICALLY_RECOMMENDED`, bajo las condiciones explícitas por AJ. |
| Nuevas decisiones aprobadas | 0/19; las 19 siguen `PENDING_HUMAN_APPROVAL`. |
| Bloqueos | 9/9 `BLOCKED` en los gates indicados en E; ninguno cerrado por esta revisión. |
| Primer slice | **S3-IMP-01 = BLOCKED_PENDING_AUTHORITY**; también faltan detalles de contrato y compatibilidad. |
| Host / PostgreSQL / IPC | `EVIDENCED_PARTIAL` / aislamiento real no demostrado / transporte financiero `NOT_IMPLEMENTED`. |
| Gobierno | **S3_DECISION_02A_NOT_CLOSED**; **PHASE31_5 = EXECUTION_HELD**. |

Se puede someter esta propuesta a decisión humana ahora. No se puede clasificar IMP-01 como `READY_FOR_EXPLICIT_IMPLEMENTATION_AUTHORIZATION` mientras permanezcan los prerrequisitos de F. Incluso esa clasificación futura no concedería permiso de implementación.

## B. Authority and Contract Reconciliation

Fuentes contractuales, hashes y fichas detalladas se reutilizan del [registro de integridad y reconciliación](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md#source-integrity), contrastado en H. La prioridad de lectura conserva la adopción reportada y el alcance específico D02; no inventa una jerarquía formal sin acta.

| Fuente | Hecho documental y fuerza de autoridad | Resolución propuesta |
| --- | --- | --- |
| V1.1 + A01 | V1.1 se titula propuesta; A01 modifica la propuesta y no autoriza runtime. A02 registra posteriormente `FINANCIAL_CONTRACT_V1_1 = HUMAN_APPROVED`. No se localizó en las fuentes revisadas el vínculo completo de acta, hash y mandato. | Conservar ambos registros. Custodio contractual aporta el acta original o autoridad acreditada ratifica versión, adopción, reservas y precedencia. Ausencia localizada no prueba inexistencia de aprobación. |
| D02 + ER | D02 registra `SECURITY_DECISION_02_A = HUMAN_APPROVED`; ER refiere autorización del 2026-10-09. Aprobación histórica de remediación acotada, LOGIN/Python, confianza residual en issuer/executor/control plane. | Preservar el estado histórico sin revocarlo ni ampliarlo. El registro no aporta por sí solo prueba completa de identidad/mandato para conceder los nuevos AJ. No reutilizarlo como permiso permanente de código o laboratorio. |
| A02 | `APPROVAL_PENDING`; propone verifier DB, executor NOLOGIN, esquema distinto y servicio/HSM de firma. | Mantener pendiente. No adoptar sus garantías, claims ni infraestructura por asociación con D02. Elegirlos exigiría nueva decisión/enmienda y revisión de la frontera de confianza. |
| Cinco documentos nuevos + ADJ/EVID | Propuestas, matrices y evidencia estática; firmas/selecciones efectivas pendientes. | Reutilizarlos como soporte de decisión, con F-C18 explícito. Ningún hash autentica al firmante ni acredita su mandato. |
| Solicitud actual | Autoriza adjudicación preparatoria y un resumen; prohíbe implementación/runtime/Git de publicación. | Autoridad suficiente para este trabajo documental. No atribuir al solicitante un cargo formal, ni a Codex poder de aprobación arquitectónica. |

**Qué puede resolverse dentro de los contratos existentes:** preservar la frontera LOGIN/Python D02, dominio/algoritmo/conjunto existente, FORCE RLS, separación de ownership, mínimo privilegio, grant vivo, identidad idempotente, orden presupuestario global/producto/UUID e inmutabilidad. AJ-P01/P04/P05/P06/P08 y partes de C02/P02/P07/P09 concretan esos controles sin necesidad técnica de sustituir D02. Aun así, requieren selección competente de detalles y permiso G-IMP propio; «compatible» no significa «autorizado».

**Qué exige aprobación nueva o aclaración vinculante:** AJ-G01/H01; C-B y perfil material/NUM-C/F-C18; autenticación/topología y acceso issuer; corte y propagación de revocación; enlace nuevo del ledger; todas las decisiones IPC y NUM-P/I/L. B-T01 requiere delimitar la frontera interna frente a V1.1 §3.2; si la nueva ruta sustituye una obligación TLS, se necesita excepción/enmienda explícita. B-R01 exige resolver recuperación operacional mediante alcance posterior, sin implementar status aquí. Cambiar algoritmo, mensaje firmado, claims, LOGIN/Python o ampliar amenazas protegidas requiere revisión contractual expresa, no una interpretación incidental.

## C. Proposed Decisions AJ-G/H/C/P/I

Esta matriz resume la [matriz humana existente](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md); sus fichas conservan alternativas, hashes, pruebas y STOP. Las dependencias CR/MT/DOC y NUM remiten a esa matriz; PG/IPC a sus especificaciones enlazadas en H. **AJ-G01 y G-IMP aplicable son dependencias comunes de toda implementación**, además de las expresadas por fila.

Estados separados: `TECHNICALLY_RECOMMENDED` evalúa la opción; `PENDING_HUMAN_APPROVAL` indica ausencia de adopción humana eficaz; `BLOCKED` detiene el gate dependiente. `APPROVED_WITH_VERIFIABLE_AUTHORITY` se reserva a prueba de firmante, mandato, decisión y alcance enlazados a versión/hash. **No se asigna a ningún AJ en esta entrega**; tampoco se recertifica retrospectivamente D02 con esa etiqueta.

En cada fila, **T/P** significa explícitamente `TECHNICALLY_RECOMMENDED / PENDING_HUMAN_APPROVAL`. Son dos dimensiones, no una aprobación parcial. F = dueño del contrato financiero; S = seguridad/protocolo; D = DBA/recovery governor; A = arquitectura; P = plataforma; C = custodio de evidencia; G = gobernanza. Todas son **funciones propuestas**: personas, mandato, firma y fecha efectiva **PENDING**. Las frases de acta son borradores para firmar, no actos ya adoptados.

| AJ | Opción recomendada y justificación | Riesgo residual | Compatibilidad D02 / A02 / V1.1 | Dependencias / gate bloqueado | Autoridad propuesta | Texto propuesto para acta | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AJ-G01 | Vincular adopción V1.1 y precedencia a acta/hash; conservar D02 acotado y A02 pendiente. Evita mezclar garantías incompatibles. | Autenticidad y mandato dependen de custodia verificable. | Conserva los tres estados; no borra contradicción documental. | B-G01, DOC-T01; G-ARCH dependiente y todos los G-IMP. | F+S+D, con G para mandato. | «Ratificamos la versión/hash y reservas identificadas; preservamos D02 acotado y A02 pendiente; no concedemos implementación/runtime.» | T/P |
| AJ-H01 | Mantener evidencia parcial; solicitar export existente o declaración de retención/pérdida limitada al alcance conocido. | Transcript original puede no recuperarse. | D02 requiere aislamiento antes de PASS; A02 no adoptada; FIN-11 no satisfecho por testimonio. | B-H01, DOC-T02; cierre host/G-CLOSE. | C+G. | «Aceptamos la clasificación EVIDENCED_PARTIAL y el inventario de custodia adjunto; no certificamos el run ni cleanup ausentes.» | T/P |
| AJ-C01 | C-B: JSON/base64 únicos, duplicados decodificados prohibidos y tipos exactos; ratificar F-C18. Reduce ambigüedad conservando mensaje firmado. | Consumidores desconocidos y signer comprometido. | D02 Ed25519/dominio/conjunto vigente; estrecha aceptación wire mediante nueva decisión; no adopta A02 DB-verifier; V1.1 identidad preservada. | B-C01, NUM-C01/02, inventario y CR-T01–06; IMP-01. | F+S. | «Seleccionamos C-B y ratificamos las 18 claves existentes según F-C18, sin claim nuevo; adoptamos el perfil y vectores anexos, manteniendo M(C).» | T/P |
| AJ-C02 | Perfil material común; comparar assertion tenant con organization firmado y contexto autorizado antes de DB; hash recomputado. | Igualdad no autentica origen de TenantProjection. | Concreta V1.1 §§4/6 y D02; recomputación issuer futura no adopta A02 completa. | B-C01, NUM-C01, MT-T01–03; IMP-01 y adaptador IMP-05. | F+S. | «Adoptamos el perfil material anexo y binding explícito; preservamos hashes normales y grants independientes; la recomputación issuer queda en su slice autorizado.» | T/P |
| AJ-P01 | Owner explícito migration para 15 tablas mediante migración posterior; evita depender del creador accidental de 0006. | Migration conserva poder DDL. | D02 separación y V1.1 §8 preservados; sin cambio A02. | B-P01, P04/P05/P08, catálogo objetivo, PG-T04–06; IMP-02. | D+F. | «Seleccionamos ownership explícito adminapps_financial_migration, separado de funciones/servicios; preservamos 0002–0007 y FORCE RLS.» | T/P |
| AJ-P02 | Executor LOGIN exclusivo; issuer con LOGIN/UID y lectura mínima propios; sin admisión ni escritura de grants por issuer. | Compromiso de un componente confiado; hashes sensibles. | D02 LOGIN obligatorio, distinto de A02 NOLOGIN; V1.1 segregación compatible. | B-P01, P03/P04/P05/P08, proyección/alias, PG-T01/02/05/10; IMP-03. | S+D+dueños de servicios. | «Confirmamos executor LOGIN D02 e issuer independiente; aprobamos la matriz de columnas/operaciones sin fallback general ni secreto compartido.» | T/P |
| AJ-P03 | Peer local con mapping exacto si topología confirmada; SCRAM-SHA-256 si peer no aplica o política exige secreto. Evita trust como prueba de identidad. | UID comprometido o sesiones previas; SCRAM requiere custodia y protección de canal según topología. | Compatible D02/V1.1; no importa NOLOGIN A02. Peer DB no equivale a peer IPC. | B-P01/B-D01, NUM-I03, PG-T01/10; IMP-03/06 y G-PG. | D+S+P. | «Seleccionamos el perfil de autenticación indicado en el anexo topológico, sin trust; cada principal tiene identidad exclusiva y positivos/negativos propios.» | T/P |
| AJ-P04 | ENABLE/FORCE RLS, triggers y políticas por rol; auditoría central acotada. GUC no prueba tenant. | Configuraciones futuras y plano administrador. | D02 grant/capability y V1.1 §8 compatibles; A02 pendiente. | B-P01, P01/P02/P05, matriz tabla/rol, PG-T03/04; IMP-02. | D+S+F. | «Preservamos FORCE RLS e inmutabilidad; aprobamos políticas issuer/auditor por objeto; no restauramos writes runtime ni usamos GUC como identidad.» | T/P |
| AJ-P05 | Allow-list SQL por objeto y creador: CONNECT necesario, USAGE y wrapper para executor; admission NOLOGIN dueño de funciones. | Default ACL o membership futuro puede ampliar privilegios. | D02 ACL mínima y V1.1 §8; no cambio a A02. | B-P01, P01/P02/P04, schema/defaults/SET ROLE, PG-T02/05/06; IMP-02. | D+S. | «Aprobamos ACL/defaults y memberships anexos; runtime no ejecuta admisión; executor no accede a tablas ni legacy; schemas confiables sin escritura influyente.» | T/P |
| AJ-P06 | SERIALIZABLE explícito en alias executor; retry completo de 40001 tras rollback; recomendar igual tratamiento acotado para 40P01. Conserva identidad y revalida autorización. | Abortos/latencia; commit ambiguo no se resuelve con retry. | V1.1 §5.2 permite SERIALIZABLE; no atribuir equivalencia no probada a locks; D02 conservado, A02 pendiente. | B-P01, NUM-P01, P07/P09, PG-T07–09; IMP-04. | F+D+S. | «Adoptamos SERIALIZABLE antes de SQL, orden total anexo y retry de transacción completa para 40001/40P01 solo con rollback conocido y límites aprobados; commit ambiguo es UNKNOWN.» | T/P |
| AJ-P07 | Grant estado+versión+evento atómicos bajo lock común; commit fija corte. Políticas distintas para key, producer, login y peer. | Trabajo previo al corte y propagación requieren aceptación. | D02 recheck/revocación y V1.1 lifecycle; A02 no se asume implementada. | B-P01, NUM-P02, P06/I02/I06, PG-T07/09/10 e IPC-T08; IMP-04/06. | F para grants; S+D para keys/logins; P para peers. | «Fijamos corte, propagación y trabajo en vuelo por tipo de identidad; transición grant es atómica y el issuer lector no recibe writes administrativos.» | T/P |
| AJ-P08 | Migration con autenticación limitada a ventana; seed e inspector separados del servicio que demuestra el positivo. | Plano administrador elevado permanece confiado. | D02 control plane excluido y V1.1 §§8/9; sin nueva arquitectura A02. | B-G01/B-P01, P01/P03, NUM-L01, PG-T05/10/11; IMP-02/03/06. | D+S. | «Aprobamos administración temporal, ruta bajo FORCE RLS y retiro verificable; ninguna identidad administrativa produce el positivo runtime.» | T/P |
| AJ-P09 | Preservar firma Python D02; enlace inmutable de nuevas admisiones a decision_id/grant_version; historia reconciliada sin UPDATE. | Executor confiado; recuperación operativa ausente. | D02 conservado, verifier DB A02 no aprobado; V1.1 §§6/10.5 requiere recuperación adicional. | B-R01 y aspectos B-P01; NUM-P02, P06/P07/I04, PG-T07–09; IMP-04/cierre. | F+S+D. | «Ratificamos frontera Python; aprobamos enlace nuevo sin alterar historia; inspector de laboratorio no sustituye recuperación de clientes ni habilita operación.» | T/P |
| AJ-I01 | AF_UNIX pathname en mismo host Linux; runtime→issuer→executor y retorno inverso. Reduce peers executor. | Kernel/servicios confiados; canal no durable. | D02 admite aislamiento futuro; A02 pendiente; V1.1 TLS requiere B-T01 resuelto. | B-I01/B-T01, topología/NUM-I03, I02/I03, IPC-T01/04; IMP-05. | A+S+F+dueños de servicios. | «Seleccionamos relay local y executor accesible solo al issuer; delimitamos por contrato la frontera TLS externa y el canal interno conforme al anexo.» | T/P |
| AJ-I02 | SO_PEERCRED cliente/servidor, UID exclusivo→endpoint→operación y autorización por solicitud; prohibir transferencia de FD. | Mismo UID no distingue procesos; reciclado/compromiso conserva riesgo. | Concreta D02 sin sustituir credencial/grant V1.1; A02 pendiente. | B-I01, NUM-I03, I01/I05, IPC-T01–03/08; IMP-05. | S+P. | «Adoptamos peer kernel mutuo y UIDs exclusivos; payload/GID/PID no sustituyen autoridad; verificamos identidad observada también con cualquier socket activation.» | T/P |
| AJ-I03 | Un request/response por conexión, longitud explícita, JSON UTF-8 estricto versionado y respuesta ligada a invocation/hash; límites finitos. | DoS y respuesta sin firma end-to-end. | Conserva claims D02, sin correlation firmado; V1.1 material/identidad; A02 pendiente. | B-C01/B-I01, C01/C02, NUM-I01/02, IPC-T04/05/07; IMP-05. | S+F+dueño del protocolo. | «Adoptamos esquema, prefijo/endian, errores y límites anexos; issuer recomputa material, executor valida binding; frame inválido no despacha.» | T/P |
| AJ-I04 | Resultado síncrono; como máximo un efecto DB por identidad demostrado; pérdida posterior al envío UNKNOWN, sin nueva identidad ni liberación. | Indisponibilidad puede mantener incertidumbre. | D02 ledger y V1.1 §§6/10.5; no simula recuperación A02 ni S4. | B-R01, P06/P09, IPC-T06–08 y PG-T08/09; IMP-04/05 y operación. | F+A+S. | «UNKNOWN conserva exposición y detiene automatismos; solo reconciliación autorizada permite resolverlo; retry permitido conserva identidad/hash y revalida vigencia.» | T/P |
| AJ-I05 | DAC por canal, directorios administrados y unidades dedicadas; 0710/0660 candidatos sujetos a positivos reales. | Hardening puede afectar disponibilidad; root/kernel excluidos. | D02 exige aislamiento real; A02 no adoptada; segregación V1.1 preservada. | B-I01/B-D01, NUM-I02/03, P03/I02/I06, IPC-T03/09 y PG-T10; IMP-06. | P+S. | «Aprobamos paths/owners/modos y restricciones compatibles con servicios reales; no world access, grupo global ni reutilización implícita de cuentas históricas.» | T/P |
| AJ-I06 | Manifest atribuible, parada verificada antes de borrado y PASS después de inventario; conservar ante mismatch/stop fallido. | SIGKILL exige recuperación posterior autorizada. | Concreta evidencia D02/FIN-11 sin alterar historia; A02 pendiente. | B-X01, NUM-L01, I05/P08, IPC-T07/10 y PG-T11; IMP-06/VAL. | P+C. | «Exigimos run ID, tipo/dev/inode/owner e identidad de proceso verificable; salida confirmada antes de eliminar recursos propios; fallo conserva evidencia y resulta FAIL.» | T/P |

**TLS/mTLS:** para AF_UNIX local, peer credentials, DAC y autorización de operación constituyen el modelo propuesto. TLS/mTLS es una alternativa de transporte o una exigencia específica de política; no sustituye automáticamente SO_PEERCRED. V1.1 exige TLS para su credencial productor y explícitamente no selecciona mTLS. Resolver B-T01 conserva esa obligación externa o registra una enmienda concreta; no declara que AF_UNIX ya la cumpla. Una topología remota devuelve AJ-I01/P03 a decisión.

## D. Remaining Human Approvals

Reutilizar el registro individual de selección/firma de la matriz y las firmas del [ADR](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md), sin rellenarlas como si hubieran llegado aprobaciones. Cada acto debe identificar AJ, selección o rechazo, desviaciones, documento/hash, persona, evidencia de mandato, fecha efectiva/zona, condiciones, residual aceptado y exclusiones. Una aprobación parcial solo tiene efecto dentro de su alcance y dependencias satisfechas.

Paquetes de decisión pendientes: G01 (adopción/mandato), H01 (custodia), C01/C02 (C-B/F-C18/NUM-C), P01–P05/P08 (matriz objetos/principales y administración), P06/P07/P09 (transacción/revocación/ledger/NUM-P), I01–I06 (topología/TLS/peer/protocolo/DAC/NUM-I/L). Mantener separados G-ARCH, G-IMP, G-OS, G-PG, G-IPC y G-CLOSE según los [gates existentes](ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md).

No proponer números operativos sin soporte como si fueran efectivos: bytes/profundidad, rangos por campo, skew, retry/backoff/jitter/tiempo total, timeouts/locks, retención, concurrencia/backlog, UID/GID/path y drenaje siguen pendientes. Para valores que requieran medición, aprobar primero método y experimento offline acotado, luego someter los resultados al acta. Los 60 segundos máximos sintéticos proceden de D02; no habilitan TTL productivo ni skew adicional.

## E. Critical Blockers

Los nueve siguen **BLOCKED**. «Arquitectura» indica qué decisión no puede declararse eficaz; no impide revisar ni firmar otras decisiones independientes. Resolver su componente documental no cierra automáticamente su componente runtime.

| ID / causa exacta | Qué impide | Decisión/evidencia y autoridad funcional propuesta | Criterio verificable para resolver |
| --- | --- | --- | --- |
| B-G01: adopción V1.1 sin acta/hash/mandato enlazados; D02/A02 divergentes. | G-ARCH dependiente y todos los nuevos G-IMP; por dependencia, runtime. | AJ-G01; acta original o ratificación por F+S+D con mandato acreditado por G. | DOC-T01 completo, versión/hash y reservas inequívocos; D02 acotado y A02 pendiente o enmienda explícita diferenciada. |
| B-H01: salidas/testimonio sin atribución primaria del run/cleanup. | Cierre host y cierre pleno; no preparación documental ni por sí solo IMP-01. | AJ-H01; export existente/procedencia o declaración limitada de retención por C+G. | Inventario y procedencia adjudicados cierran solo la acción documental; aislamiento/cleanup requieren evidencia primaria suficiente y aceptación competente. Aceptar pérdida no cierra el gate técnico. |
| B-C01: wire/tipos/límites/material/binding no vinculantes; ahora F-C18 confirmado. | Eficacia C01/C02, IMP-01 e interfaces dependientes. | AJ-C01/C02+G01; NUM-C01/02, inventario de consumidores/vectores por F+S. | Acta ratifica conjunto exacto y perfil completo, compatibilidad y política de errores; pruebas futuras CR/MT demuestran el comportamiento antes de aceptar implementación. |
| B-P01: owner implícito 0006, trust, issuer DB ausente, transacción/revocación/ledger incompletos. | Detalles arquitectónicos P; IMP-02–04; G-PG y cierre por evidencia. | AJ-P01–09, matriz objetos/roles, NUM-P, patch y PG-T01–11; D+F+S. | Decisiones y diseño completos para abrir implementación; posteriormente catálogo efectivo, auth real, carreras/ACL/RLS/replay y cleanup aprobados. Ningún owner desplegado se presume desde fuente. |
| B-I01: IPC no implementado y topología/UID/frames/códigos/deadlines sin decidir. | Eficacia de contrato I; IMP-05/06, G-IPC y cierre. | AJ-I01–06, NUM-I/L y protocolo; A+S+P+F. | Contrato firmado primero; después patch revisado y positivos/negativos IPC-T01–10 bajo identidades reales autorizadas, evidencia y cleanup. |
| B-T01: TLS productor V1.1 §3.2 frente a credencial en nueva ruta local. | Eficacia AJ-I01 e IMP-05; no bloquea por sí solo parser offline IMP-01. | Delimitación/versionado de frontera y exposición de credencial; F+S+A. | Acta identifica extremos y protección del enlace externo y canal interno; si sustituye obligación, enmienda/excepción expresa. No asumir cumplimiento por usar AF_UNIX. |
| B-D01: socket PG bajo raíz 0700 incompatible con propuesta de clientes en UIDs distintos sin layout DAC resuelto. | Configuración final IMP-03/06 y validación G-PG peer. | AJ-P03/I05, NUM-I03; D+P+S. | Layout aprobado separa data privado y socket accesible por traversal mínimo; positivos por UID y negativos ajenos, sin abrir data ni compartir UID. Diseño y prueba son hitos distintos. |
| B-R01: reconciliación V1.1 §§10.3/10.5 requerida, status operacional ausente y fuera de slices. | Habilitación financiera y cierre pleno; no ensayo sintético con inspector autorizado. | AJ-P09/I04 y alcance posterior de recuperación; F+A+S+D. | Contrato de recuperación adjudicado y mecanismo operacional autorizado/implementado/validado antes de operar. Inspector lab o aceptación de riesgo no bastan; ningún endpoint se construye aquí. |
| B-X01: harness ignora stop y anuncia PASS antes del cleanup. | Nueva ejecución G-PG/G-IPC y aceptación de cleanup; no aprobación del principio de diseño. | AJ-I06, IMP-06 sucesor; P+C. | Harness/hash revisados y permiso antes del run; fallos/señales/colisiones conservan recursos inciertos y el positivo demuestra salida y ausencia propias antes de PASS. |

## F. S3-IMP-01 Readiness

**S3-IMP-01 = BLOCKED_PENDING_AUTHORITY.** La propuesta de alcance es revisable; los prerrequisitos documentales vinculantes no son suficientes. No basta una autorización genérica de implementación para omitir AJ-G01/C01/C02 o NUM-C.

| Requisito | Evaluación y condición de salida |
| --- | --- |
| JSON C-B especificado | Semántica general clara, pero cardinalidad textual errónea y NUM-C pendientes. Ratificar F-C18, tipos/formatos/rangos/tamaños/profundidad, errores y política temporal exactos. |
| Compatibilidad con emisor actual | Compatible por inspección con serialización normal y conjunto de 18 claves. No demostrada mediante vectores nuevos; no se ejecutó signer/verifier. Inventariar todos los consumidores y aceptar explícitamente estrechamiento de wire. |
| Binding tenant/material | Executor recomputa hash, pero no compara explícitamente assertion.adminapps_tenant_id con organization firmado ni recibe contexto esperado local. Aprobar perfil y fuente confiable del contexto; rechazo antes de tocar alias/conexión DB. Issuer actual recibe hash, no material completo: recomputación propia corresponde a IMP-05. |
| Vectores | Catálogo CR-T01–06/MT-T01–03 existente, aún propuesto. Fijar fixtures versionadas y bytes/mensaje/firma/hash esperados; el diagnóstico JSON histórico no es vector de verificación Ed25519 nuevo. |
| Firma e identidad | Preservar Ed25519, prefijo con newline exacto, J(C) y conjunto ratificado; jti sigue invocation, correlation_id no firmado. Sin nuevos claims, dominio ni versión encubiertos. |
| Entradas inválidas sin efectos DB | Pruebas futuras con contador/doble deben demostrar cero acceso/conexión/SQL para rechazo crypto/material. Denegaciones financieras después de SQL se evalúan por contrato y rollback/auditoría, no con un requisito artificial de conexión cero. |
| Separación propuesta/aprobada | D02 histórico permanece; C-B/perfil/tipos/límites y F-C18 no son políticas aprobadas por este resumen. G-ARCH y G-IMP separados. |
| Archivos previstos | capabilities.py, executor.py, services.py, test_s3_capability_offline.py y tests financieros pertinentes del plan; módulo compartido solo con justificación y alcance aprobado. Sin migraciones, provisión issuer ni IPC en IMP-01. |
| Regresión | Wires antes tolerados pasan a rechazo; coerciones str/int/bool, formatos UUID/UTC, orden de evidence_ids y validación compartida pueden cambiar aceptación/hash. Revisar consumidores de services antes de cambiar helper común; no alterar S1/S2 por arrastre. |
| Rollback | Ante cambio de mensaje/hash normal, negativo que toca DB, excepción sin tipar o consumidor incompatible: STOP; conservar evidencia y retirar solo patch propio en copia aislada. No reset global, reescritura de pruebas históricas ni reactivar operación con parser anterior. |

Conjunto observado por AST, propuesto para ratificación, **18 claves**:

```text
alg, aud, capability_id, environment, exp, grant_id, grant_version,
iat, iss, jti, kid, material_request_hash, nbf, operation,
organization_id, producer_registration_id, product_id, version
```

Perfil base recomendado para completar NUM-C: `version` entero exacto 1; `grant_version` entero positivo compatible con su destino SQL, nunca bool; IDs UUID como strings con representación acordada; `iat/nbf/exp` strings UTC, no epoch; hash SHA-256 con representación acordada; alg/aud/operation fijos y iss/kid/environment sujetos al contexto permitido. Limitar campos y token **antes** de parsing costoso, rechazar no finitos y duplicados por clave decodificada, comparar payload UTF-8 con J(C) y exigir roundtrip base64url sin padding de ambos segmentos. Este perfil no sustituye el anexo exhaustivo pendiente ni introduce valores por defecto vinculantes.

Preservar `M(C) = b'adminapps.financial.admission-capability.v1\n' + J(C)`, donde J(C) usa sorted/compact ASCII y `allow_nan=False`. El token actual no es JWT/JWS ni JCS. El material conserva su esquema y serialización normal, incluidos `evidence_ids` ordenados como strings; endurecer tipos sin modificar silenciosamente bytes/hashes aceptados. Aprobar límites de unidades y assertion completo de V1.1; igualdad tenant no prueba procedencia externa.

Positivos futuros: token normal del emisor y vector fijo, límites frontera aprobados, material conocido con hash idéntico y tenant/contexto coincidentes. Negativos futuros: whitespace/orden/escapes alternativos; duplicados idénticos/conflictivos en ambas posiciones y claves escapadas; faltantes/extras; bool/float/null/no finitos; UUID/UTC/base64/UTF-8/tamaño/profundidad inválidos; firma/key/iss/aud/env/op incorrectos, futuro/caducado y material/tenant sustituido. Cada caso conserva esperado/observado y contador DB. **NOT_RUN en esta tarea**. Las dos sondas históricas aceptadas siguen FAIL frente a C-B propuesto; no son falsificación Ed25519.

## G. Authorized-vs-Prohibited Operations

Autorizado por esta solicitud: lectura focalizada de documentación/fuente, inspección AST sin importar producto, lectura JSON/SHA, Git de consulta, documentación nueva y verificación textual. No se necesita inferir mandato arquitectónico para ese alcance.

Prohibido aquí: implementar cualquier slice; ejecutar pruebas de producto, PostgreSQL o IPC; Host Lab; sudo; crear/modificar usuarios, roles, servicios/systemd, sockets o credenciales; migraciones; despliegue; operaciones financieras reales; integración ISO Smart/MedSupplier; proveedores/inferencia; commit, stage, push o merge. Las lecturas externas se limitaron a documentación técnica pública; no a servicios operativos del proyecto.

Secuencia recomendada de los **nueve slices**, conservando el [plan existente](ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md):

| Orden | Slice / salida esperada | Gate antes de comenzar |
| --- | --- | --- |
| 1 | S3-IMP-01: parser/binding y evidencia offline. | G01/C01/C02, NUM-C/F-C18 resueltos + G-IMP específico. |
| 2 | S3-IMP-02: ownership, ACL/RLS y migración posterior preparada. | Salida 01 revisada; P01/P04/P05/P08 y lecturas P02 + G-IMP. |
| 3 | S3-IMP-03: identidades/configuración/consulta issuer preparadas. | Salida 02; P02/P03/P08, B-D01/NUM-I03 + G-IMP. |
| 4 | S3-IMP-04: transacción, retry, revocación y ledger preparados. | Salida 03; P06/P07/P09/I04 y NUM-P + G-IMP. |
| 5 | S3-IMP-05: protocolo y adaptadores IPC, pruebas con dobles. | Salida 04; I01–I04 e interfaces I05/I06, NUM-I, B-T01 + G-IMP. |
| 6 | S3-IMP-06: hardening/lifecycle/harness y runbooks revisables. | Salida 05; I05/I06, P03/P07/P08, NUM-L y DAC + G-IMP. |
| 7 | S3-VAL-01: PostgreSQL sintético PG-T01–11. | IMP-01–06 revisados, hashes, CR/MT aceptados, G-PG y G-OS aplicable. |
| 8 | S3-VAL-02: IPC real sintético IPC-T01–10; integración DB diferenciada. | VAL-01 aceptado; G-IPC/G-OS propios y G-PG vigente si hay integración. |
| 9 | S3-CLOSE-01: cadena AJ→acta→patch/hash→permiso→run→evidencia. | VAL aceptados, custodia/autoridad resueltas y G-CLOSE humano; B-R01 impide cierre pleno. |

El orden reduce retrabajo: contrato y binding preceden SQL; identidades preceden transacciones de su principal; transporte depende de resultados/UNKNOWN; harness seguro precede todo runtime. IMP-05 no necesita una DB activa, por lo que no hay ciclo con VAL-01. AJ-H01 se tramita documentalmente en paralelo lógico, sin repetir laboratorio.

Offline con dobles prueba lógica; PostgreSQL sintético prueba invariantes/ACL/auth del entorno autorizado; IPC sintético prueba peers/transporte, e integración prueba efectos DB. El Host Lab histórico de placeholders no demuestra servicios financieros reales. Ninguna de esas capas equivale a validación operacional productiva ni autoriza operaciones financieras reales, aun después de superar VAL. Los gates externos y de recuperación permanecen independientes.

## H. Evidence and Traceability

Fuentes principales reutilizadas: [reconciliación](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md), [ADR](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_DECISION_RECORD_DRAFT_2026-10-09.md), [matriz](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md), [plan](ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md), [gates](ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md); [ADJ](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_2026-10-09.md), [EVID](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json), [OFF](ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json), [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md), [A02](ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md), [ER](ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md), [PG](ADMINAPPS_AI_FINANCIAL_S3_POSTGRESQL_ISOLATION_SPECIFICATION_2026-10-09.md), [IPC](ADMINAPPS_AI_FINANCIAL_S3_IPC_ISOLATION_SPECIFICATION_2026-10-09.md).

Contratos históricos: [V1.1](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md), [A01](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_AMENDMENT_01_DECISION_RECORD_2026-10-08.md) y [FIRM](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_IMPLEMENTATION_READINESS_2026-10-08.md). Sus hashes completos se mantienen en el registro existente, sin duplicar ni regenerar manifiestos históricos.

Trazabilidad del hallazgo F-C18: [capabilities.py](../../backend/apps/financial/capabilities.py), `_REQUIRED` línea 63 y dict del emisor línea 78, hash `b389eb73799eb13ea8af0285dbf4d6f20a3b917fe58d7707da96fadfc24f44dd`. Extracción AST de literales: 18 claves distintas en ambos, conjuntos iguales; sin import, firma ni verificación ejecutada. El primer caso `canonical` del diagnóstico JSON de EVID también contiene esas 18 claves. La discrepancia se registra aquí, sin cambiar la expectativa histórica de CR-T03 ni su fuente; su sustitución efectiva exige acta explícita.

| Comprobación de esta revisión | Resultado / límite |
| --- | --- |
| EVID: source / previous_package / preserved_scope / deliverable | 24/24, 7/7, 44/44, 1/1 hashes coincidentes. |
| OFF: preexisting / reference / deliverable | 37/37, 4/4, 6/6 hashes coincidentes. Total combinado 123 entradas superpuestas, no fuentes independientes. |
| Registro de reconciliación: fuentes y cuatro entregables hasheados | 46/46 filas con enlace/hash coincidentes. El reporte no tiene autohash; su copia está cubierta por baseline local. |
| JSON EVID/OFF | Leídos como datos. 50 outputs archivados y diagnósticos conservados; no reejecutados ni atribuidos retrospectivamente a un run. |
| Contraste estático código/contrato | F-C18; emisor recibe hash; executor recomputa material sin comparación tenant explícita ni enforcement SERIALIZABLE propio; transición grant sin atomic propio. No prueba de explotación ni de catálogo desplegado. |
| Pruebas históricas | 19/19 host y 19/19 crypto de OFF; 4/4 PG de ER, con límites ADJ. No recertificadas; trust no demuestra identidad exclusiva. |
| Producto / DB / IPC / Host Lab | NOT_RUN. Sin firma/verify criptográfico nuevo, imports Django, migraciones ni inspección privilegiada. |

Fuentes técnicas públicas consultadas para límites del diseño, sin carácter de aprobación: peer DB usa identidad OS/mapping y solo conexiones locales ([PostgreSQL 15: Peer Authentication](https://www.postgresql.org/docs/15/auth-peer.html)); SERIALIZABLE exige manejar abortos y reinicio de transacción ([Transaction Isolation](https://www.postgresql.org/docs/15/transaction-iso.html)); FORCE RLS no contiene superuser/BYPASSRLS ni priva al dueño de poder DDL ([Row Security](https://www.postgresql.org/docs/15/ddl-rowsecurity.html)); SO_PEERCRED y permisos pathname son controles distintos, con credenciales capturadas al establecer la conexión según el caso ([Linux unix(7)](https://man7.org/linux/man-pages/man7/unix.7.html)). La revalidación por solicitud consulta la política vigente sobre ese principal; no convierte SO_PEERCRED en prueba de cambios posteriores de identidad. Las selecciones arquitectónicas son inferencias de estas propiedades y de los contratos locales, no resultados runtime. La versión futura de PostgreSQL/driver/host sigue pendiente de fijarse.

## I. Git Integrity

Baseline anterior a cualquier escritura de entregables: **15.528 entradas tracked/untracked no ignoradas**, bytes SHA-256 y modo de archivos regulares; texto y modo de symlinks sin seguirlos. No certifica contenido ignorado, destinos externos de enlaces, estado runtime ni sistemas ajenos.

Rama: `hardening/p0-p1-enterprise-readiness`.
HEAD: `42f007d1fcd30743a28b0f1b998ab8c6ae93ba7c`.
Índice SHA-256: `d774b85b7f9123d243c0d094e6efe7e151ac3a1c38d8eee4a00970438dfcfd50`.
Control temporal: `/tmp/adminapps-s3-human-gate-u2ap044o/baseline.json`, SHA-256 `ab40a2014809f5a1231d1796f65896cf6cef2b7e295bcdb1b2caf79761ed9a35`. No depende de su retención para conferir autoridad.

Estado preexistente preservado:

```text
 M backend/config/settings.py
?? backend/apps/financial/
?? backend/scripts/s3_isolation_host_lab.sh
?? backend/scripts/tests/
?? backend/scripts/verify_financial_s1_postgres.sh
?? backend/scripts/verify_financial_s3_postgres.sh
?? docs/financial/
```

La comprobación final compara cada entrada preexistente, HEAD/rama/índice y status expandido `-uall`; el status resumido no basta porque docs/financial ya era untracked. Única adición prevista: este documento. Sin stage, commit, push, merge, reset, checkout ni cambios a los cinco documentos, código o contratos históricos.

<!-- FINAL_CHECK -->
Verificación final documental: **PASS** de preservación de 15.528/15.528 entradas preexistentes; única adición este resumen. HEAD/rama/índice idénticos y delta de status expandido exclusivamente este archivo. Diez secciones A–J, 19 filas AJ únicas y nueve bloqueos únicos; enlaces locales y whitespace válidos. `git diff --check` exit 0; comprobación explícita del documento untracked sin diagnósticos (exit 1 normal de `--no-index` por archivo nuevo). F-C18 contrastado además con el caso canonical de EVID: mismas 18 claves. Pruebas de producto y runtime **NOT_RUN**.
<!-- END_FINAL_CHECK -->

## J. Exact Human Actions Required

1. La instancia con poder de designación debe identificar personas para F/S/D/A/P/C/G y aportar evidencia de mandato/alcance. El usuario, su cuenta local y Codex no reciben ese poder por inferencia.
2. F+S+D resuelven AJ-G01 con acta original o ratificación enlazada a hashes V1.1/D02/A02 y reservas. Preservar D02 histórico; mantener A02 pendiente salvo aprobación expresa distinta.
3. F+S adoptan, modifican o rechazan C-B/C02; ratifican **F-C18**, el conjunto exacto, NUM-C01/02, inventario de consumidores y vectores. No pedir ejecutar IMP-01 mientras esto falte. Una exigencia real de claim adicional devuelve el diseño a versionado, no a corrección de conteo.
4. D/F/S/P adjudican P01–P09, matriz de objetos/roles, peer o SCRAM según topología, rutas data/socket, administración, orden total de locks, límites/retry, revocación/sesiones y ledger. Cada selección tiene reservas y evidencia de aceptación propias.
5. A/S/P/F adjudican I01–I06, B-T01, NUM-I/L, exposición de credencial, peer mutuo, UNKNOWN y cleanup; F/A/S resuelven alcance futuro de recuperación B-R01 antes de habilitación operacional.
6. C+G aportan evidencia existente o declaración acotada de custodia/retención y deciden AJ-H01, conservando `EVIDENCED_PARTIAL` donde no haya prueba. No ordenar un Host Lab nuevo mediante esa aceptación documental.
7. Solo tras los prerrequisitos aplicables, emitir autorización G-IMP **para el slice concreto**, con acta/hash, archivos, cambios, pruebas offline, exclusiones, revisor y rollback. Para IMP-01 usar F y el plan, incorporando las selecciones humanas efectivas; todavía no existe esa autorización.
8. Después de patch/harness revisados, emitir permisos separados G-OS/G-PG/G-IPC con comandos, hashes, entorno, identidades, recursos, custodia y teardown exactos. G-CLOSE exige evidencia suficiente; ningún permiso equivale a producción, integración, proveedor o publicación Git.

No hay firmas ni fecha efectiva de aprobación nuevas. **S3_DECISION_02A_NOT_CLOSED. PHASE31_5 = EXECUTION_HELD. S3-IMP-01 = BLOCKED_PENDING_AUTHORITY.**
