# S3 — Architecture Decision Record — DRAFT

Fecha de preparación: 2026-10-09, America/Costa_Rica.
Estado del acta: **DRAFT — PENDING_HUMAN_APPROVAL**.
Fecha efectiva de aprobación: **PENDING**.
Estado final de seguridad: **S3_DECISION_02A_NOT_CLOSED**.

## Executive Verdict

Paquete documental listo para revisión y decisión humana. Propone 19 decisiones
AJ y nueve slices; no registra ninguna aprobación nueva. Solo se crearon los
cinco documentos de este paquete. No se ejecutaron Host Lab, PostgreSQL, IPC,
migraciones, servicios, pruebas Django ni código de producto.

Se recomienda C-B con binding explícito; ownership y privilegios SQL mínimos;
executor LOGIN con verifier Python conforme D02; issuer y administración
separados; peer exacto para DB local, sujeto a topología; SERIALIZABLE propio;
y IPC UNIX pathname con autenticación mutua y relay issuer → executor.
Todas son **selecciones recomendadas**, sujetas a las condiciones y decisiones
individuales de la [matriz humana](ADMINAPPS_AI_FINANCIAL_S3_HUMAN_APPROVAL_MATRIX_2026-10-09.md).

Host permanece `EVIDENCED_PARTIAL`; autenticación aislada de PostgreSQL no está
demostrada; IPC financiero continúa `NOT_IMPLEMENTED`. Los resultados históricos
19/19 host, 19/19 crypto y 4/4 PG mantienen su alcance anterior. Las dos sondas
wire aceptadas conservan su FAIL frente al rechazo estricto propuesto; no son
prueba de falsificación Ed25519 ni se convierten en PASS en este paquete.

## Scope and Governance Authority

La solicitud actual autoriza preparar documentos y verificar fuentes locales.
La decisión de arquitectura, el permiso de implementación, los permisos runtime
y la aceptación de cierre son actos distintos. Este ADR no otorga ninguno.

D02 registra `HUMAN_APPROVED` para remediación histórica acotada. A02 conserva
`APPROVAL_PENDING`. V1.1 tiene cabecera de propuesta y adopción posterior
registrada en AdminApps: AJ-G01 debe vincular la versión/hash al acta original
sin borrar ninguna de las dos fuentes. No se presume que falta de acta localizada
signifique que nunca existió, ni que la cabecera invalide por sí sola D02.

Autoridades funcionales propuestas: dueño del contrato financiero, seguridad y
protocolo, DBA/recovery governor, arquitectura, plataforma y custodio de evidencia
host. El dueño del proyecto debe designar personas y mandato. Ningún nombre,
cargo efectivo, firma o poder de aprobación se infiere del usuario del sistema.

`PHASE31_5 = EXECUTION_HELD`. Phase32, WP2, ISO Smart y MedSupplier permanecen
fuera del cambio. S1/S2 no se recertifican. S4–S6, settlement/release, endpoints
HTTP/status, proveedores/inferencia, tarifas reales, producción, despliegue,
credenciales reales y commit/push/merge siguen excluidos.

## Source Integrity

El [registro de fuentes y verificación](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md#source-integrity) fija rutas,
SHA-256 completos, comparaciones históricas y límites de atribución. Cada ID de
fuente usado en este paquete se resuelve allí, incluida la fuente de código.

| Fuente contractual principal | SHA-256 de bytes leídos | Autoridad conservada |
| --- | --- | --- |
| [D02](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md) | `66af713c74bd44db4f43965c4b7a17e1410c5f65b62f22d55065e47ee2a5d3a3` | Aprobación acotada registrada; no nuevo permiso. |
| [A02](ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md) | `e03022a6ca4da9eeb9022b50972d30ff6628fa5a5ab9614ba3e21d6a5af9ef79` | Propuesta pendiente; no adoptar DB-verifier, NOLOGIN o HSM tácitamente. |
| [V11](../../../isosmart/docs/transformation/ADMINAPPS_AI_FINANCIAL_AUTHORITY_CONTRACT_V1_1_2026-10-08.md) | `2a68c54a1acaae55d5dbf7d249692d60ac6bd9bcaebce2d274f58997937d444f` | Versión propuesta con adopción posterior por reconciliar en AJ-G01. |
| [ADJ](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_2026-10-09.md) | `6d16f47e4d2ed6a742294a8ccd4c65399ddbb3f0271b22aab081b96a143a571a` | Dictamen técnico A–J, no acta aprobada. |
| [EVID](ADMINAPPS_AI_FINANCIAL_S3_SECURITY_CONTRACT_ADJUDICATION_EVIDENCE_2026-10-09.json) | `57e8a44b89bc1af0598c6fc1f9691a461deaf6eb227ff413490da5e093946ec4` | Evidencia estática anterior; hash tomado al inicio de esta tarea. |

La coincidencia de hashes prueba identidad de bytes respecto de los manifiestos,
no autenticidad del firmante, procedencia host ni ejecución. EVID no contiene su
propio hash esperado; el hash aquí ancla su copia leída, sin inventar una cadena
de custodia previa.

## Architecture Decision Register

La matriz contiene para **cada** AJ contrato/hash, situación, riesgo, alternativas,
recomendación, justificación, cambios, positivos/negativos, residual, autoridad,
`PENDING_HUMAN_APPROVAL` y STOP. El resumen siguiente no reemplaza esas fichas.

| Decisión | Selección recomendada | Implementación/validación futura |
| --- | --- | --- |
| AJ-G01 | Acta/versionado V11; conservar D02; A02 pendiente. | Entrada común, S3-CLOSE-01. |
| AJ-H01 | Evidencia host parcial, declaración de retención/pérdida; sin repetir lab. | S3-CLOSE-01. |
| AJ-C01 | C-B: wire único compatible con emisor actual. | S3-IMP-01; CR-T01–06. |
| AJ-C02 | Esquema material y enlace assertion/organization explícitos. | S3-IMP-01; MT-T01–03. |
| AJ-P01 | Ownership migration explícito de las 15 tablas. | S3-IMP-02; PG-T04/05/06. |
| AJ-P02 | Executor LOGIN D02; issuer DB y OS independientes. | S3-IMP-03; PG-T01/02/05/10. |
| AJ-P03 | Peer local exacto; SCRAM solo por elección expresa. | S3-IMP-03; PG-T01/10. |
| AJ-P04 | FORCE RLS, políticas por rol y auditoría central acotada. | S3-IMP-02; PG-T03/04. |
| AJ-P05 | Allow-list SQL por objeto/creador, sin escalamiento. | S3-IMP-02; PG-T02/05/06. |
| AJ-P06 | SERIALIZABLE por operación; retry de transacción completa. | S3-IMP-04; PG-T07/08/09. |
| AJ-P07 | Revocación transaccional y corte por tipo de identidad. | S3-IMP-04/06; PG-T07/09/10, IPC-T08. |
| AJ-P08 | Migración/seed/inspección separados del servicio. | S3-IMP-02/03/06; PG-T05/10/11. |
| AJ-P09 | Frontera Python D02; ledger y recuperación adjudicados. | S3-IMP-04; PG-T02/07/08/09. |
| AJ-I01 | UNIX pathname local, relay issuer → executor. | S3-IMP-05; IPC-T01/04. |
| AJ-I02 | Peer kernel mutuo, UID exclusivo, allow-list por operación. | S3-IMP-05; IPC-T01/02/03/08. |
| AJ-I03 | Frames versionados, parser estricto y respuesta ligada. | S3-IMP-05; IPC-T04/05/07. |
| AJ-I04 | UNKNOWN; idempotencia en DB; sin entrega durable prometida. | S3-IMP-04/05; IPC-T06/07/08, PG-T08/09. |
| AJ-I05 | DAC por canal y hardening del servicio real. | S3-IMP-06; IPC-T03/09, PG-T10. |
| AJ-I06 | Lifecycle y cleanup atribuibles por manifest. | S3-IMP-06; IPC-T07/10, PG-T11. |

Todos los estados individuales son **PENDING_HUMAN_APPROVAL**. PG-T e IPC-T
remiten a los catálogos históricos PG/IPC; CR-T, MT-T y DOC-T son identificadores
de pruebas propuestas en la matriz, no nuevos requisitos normativos aprobados.

## Security Trade-offs

| Elección propuesta | Beneficio esperado | Costo y límite que debe aceptarse |
| --- | --- | --- |
| C-B | Una representación JSON/base64 por claims válidos, sin duplicados ambiguos. | Rechaza wires antes aceptados; requiere confirmar todos los consumidores. No cambia firma, dominio ni claims. |
| Python + executor LOGIN | Conserva la frontera aprobada D02 y la implementación existente. | Un executor comprometido queda dentro de la confianza residual; DB no verifica Ed25519/tiempos. Resistir ese compromiso exige nueva decisión. |
| Peer local | Identidad del sistema operativo mapeada exactamente a rol DB, sin password del servicio. | Solo local; requiere UIDs reales exclusivos, DAC compatible y separación administrativa. Un único UID con SET ROLE no demuestra esa propiedad. |
| SERIALIZABLE | Invariante transaccional explícita y observable por executor. | Abortos y reintentos; límites, deadlines y tratamiento de 40P01 pendientes. No resuelve por sí solo commit ambiguo. |
| UNIX pathname | Frontera local con DAC y peer kernel, sin PKI/red adicional. | Confía en kernel y peers; no cifra ni firma toda la respuesta y no asegura entrega durable. Topología remota exige otra decisión. |
| Historia preservada | Evita certificar evidencia perdida o alterar ledger inmutable. | El cierre requiere decisión humana sobre límites históricos y evidencia operativa futura suficiente. |

## Recommended Selections

Flujo propuesto, sin servicios existentes que lo implementen:

```text
runtime AdminApps local (credencial producer y material)
    → issuer (UID/DB propios; hashed_v1 + grant + binding + hash; firma)
    → executor (UID/DB propios; peer + verifier público + hash)
    → PostgreSQL (grant vivo + transacción + ledger/decisión/reserva/audit)
    → respuesta ligada a invocation/material → issuer → runtime
```

Capability vigente: 19 claims; `jti` es invocation y `correlation_id` no está
firmado. Mantener Ed25519 y el prefijo exacto
`b'adminapps.financial.admission-capability.v1\n'` seguido del JSON sorted,
compact ASCII del objeto. No es JWT/JWS ni se declara JCS. C-B propone detección
de claves decodificadas duplicadas, tipos estrictos, no finitos denegados,
igualdad de payload con la serialización vigente y base64url sin padding con
roundtrip estricto. El máximo histórico de 60 segundos proviene de D02; no
habilita ampliar vigencia ni agregar tolerancia de reloj sin decisión.

El esquema de material conservaría los bytes/hash normales actuales; discrepancia
assertion↔organization, entorno u operación se rechazaría antes de DB. Validar
un UUID o comparar el assertion no acredita por sí solo la procedencia confiable
de TenantProjection. AdminApps mantiene grant, organización y entitlement como
controles independientes; integración ISO Smart permanece fuera del slice.

Ownership propuesto: migration, separado de admission NOLOGIN dueño de funciones,
executor LOGIN y nuevo issuer. Runtime no recibe signer ni acceso DB executor.
Los SELECT históricos de runtime se inventariarían por tabla: no afirmar que hoy
carece de toda lectura SQL. Issuer necesita consulta mínima específica; un GRANT
amplio sobre `IntegrationAPIKey` para hacer funcionar el ORM no es la solución.

## Conditions and Exceptions

Las condiciones siguientes bloquean el permiso dependiente, no la preparación
de este borrador. Detalle y evidencia en [reconciliación](ADMINAPPS_AI_FINANCIAL_S3_ARCHITECTURE_GOVERNANCE_RECONCILIATION_REPORT_2026-10-09.md#blockers).

- **B-G01:** acta/versionado V11 y mandatos no vinculados; AJ-G01 pendiente.
- **B-C01:** tipos, límites, compatibilidad y versión wire/material no aprobados.
- **B-P01:** matriz objeto/rol, autenticación, orden de locks, retry, revocación,
  sesiones y reconciliación de ledger pendientes.
- **B-I01:** topología, identidades, protocolo y cifras de IPC pendientes.
- **B-T01:** V11 §3.2 prescribe credencial producer sobre TLS. El canal local
  runtime→issuer no debe presentarse como cumplimiento automático: resolver si
  es frontera interna distinta o excepción/versionado explícito, con análisis
  de exposición de la credencial. El enlace producer externo no se redefine aquí.
- **B-D01:** el PG anterior propone socket bajo raíz 0700; eso no basta para
  clientes con UIDs distintos. Proponer data directory privado y socket en ruta
  separada con traversal mínimo administrado. Aprobar la disposición y probar
  positivos por cada UID; no abrir el data directory ni usar un UID compartido.
- **B-R01:** status/recuperación de ambigüedad no implementados. Los ensayos
  sintéticos pueden observar invariantes mediante inspector administrativo
  autorizado; esa inspección no es recuperación operativa ni endpoint status.
- **B-H01/B-X01:** falta procedencia host suficiente y el harness PG tiene
  cleanup inseguro para un nuevo run; no reutilizar sus PASS como aislamiento.

No hay excepción concedida. Cada desviación requiere fuente/hash, razón, alcance,
riesgo, autoridad, vencimiento/revisión y prueba compensatoria; todos PENDING.
Si exige cambiar D02, A02 o V11, preparar un acta nueva antes del slice afectado.

## Residual Risk Acceptance

| Riesgo residual | Decisiones | Autoridad funcional propuesta | Aceptación / fecha / evidencia |
| --- | --- | --- | --- |
| Compromiso root/DBA/migration o issuer/executor confiados. | AJ-G01/P02/P08/P09 | Seguridad + financiero + DBA | PENDING / PENDING / PENDING |
| Procedencia host irrecuperable dentro del alcance revisado. | AJ-H01 | Custodio host + gobernanza | PENDING / PENDING / PENDING |
| Incompatibilidad con consumidores wire no inventariados. | AJ-C01/C02 | Protocolo + financiero | PENDING / PENDING / PENDING |
| Sesión/solicitud admitida antes del corte de revocación. | AJ-P07/I02/I04 | Seguridad + DBA + financiero | PENDING / PENDING / PENDING |
| Commit ambiguo sin recuperación operativa aprobada. | AJ-P09/I04 | Financiero + arquitectura | PENDING / PENDING / PENDING |
| Disponibilidad y límites de un canal local no durable. | AJ-I01/I03/I05/I06 | Plataforma + seguridad | PENDING / PENDING / PENDING |

Aceptar un riesgo no cambia el resultado de una prueba ni crea evidencia ausente.
Los bloqueos de autorización no se eluden mediante una casilla de aceptación.

## Approval Signatures

| Función propuesta | Persona designada | Mandato/evidencia | Decisiones firmadas | Firma | Fecha efectiva/zona |
| --- | --- | --- | --- | --- | --- |
| Dueño del contrato financiero | PENDING | PENDING | PENDING | PENDING | PENDING |
| Seguridad/protocolo | PENDING | PENDING | PENDING | PENDING | PENDING |
| DBA/recovery governor | PENDING | PENDING | PENDING | PENDING | PENDING |
| Arquitectura | PENDING | PENDING | PENDING | PENDING | PENDING |
| Plataforma | PENDING | PENDING | PENDING | PENDING | PENDING |
| Custodio host/gobernanza | PENDING | PENDING | PENDING | PENDING | PENDING |

Los 19 registros individuales de selección/firma están en la matriz. La fecha
de preparación de este documento no es fecha de aprobación. Ninguna casilla
vacía ni recomendación preseleccionada constituye consentimiento.

## Implementation Authorization Boundary

**Autorización de implementación: PENDING.** Tras las decisiones aplicables,
un permiso independiente identificará slice, archivos, cambios, exclusiones,
pruebas offline y rollback. El [plan](ADMINAPPS_AI_FINANCIAL_S3_PHASED_IMPLEMENTATION_PLAN_2026-10-09.md) prepara ese alcance sin iniciar
código, migraciones, sockets ni unidades. Preparar un patch después de ese permiso
no autoriza aplicarlo a un entorno ni ejecutar su harness runtime.

## Runtime Authorization Boundary

**PostgreSQL: PENDING. IPC/host: PENDING. Integración IPC+PG: PENDING.** Primero
existirán patch/harness revisados, SHA, versiones, entorno sintético, identidades,
paths, comandos exactos, captura de evidencia y teardown verificable. Luego se
podrá emitir el permiso específico descrito en los [gates](ADMINAPPS_AI_FINANCIAL_S3_AUTHORIZATION_BOUNDARY_RUNTIME_GATES_2026-10-09.md). No hay
comandos operativos ejecutables fabricados en este paquete.

## Closure Requirements

S3-CLOSE-01 deberá reconciliar las 19 decisiones, permisos, hashes, controles
positivos y negativos PG-T01–11/IPC-T01–10, casos crypto/material, carreras y
fallos por executor, trazabilidad ledger y ausencia de recursos residuales.
Host parcial requiere adjudicación de procedencia/retención y evidencia futura
suficiente del servicio real; no basta aceptar pérdida para certificar aislamiento.
Recuperación pendiente mantiene la operación cerrada. Cualquier cierre acotado
con reservas exige alcance humano explícito, sin declarar S3 plenamente PASS.

Firma de aceptación de evidencia/cierre: **PENDING**.
**S3_DECISION_02A_NOT_CLOSED**.
