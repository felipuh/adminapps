# Matriz explícita de aprobación

Fecha: 2026-10-14, America/Costa_Rica. **Cero aprobaciones nuevas registradas.**
Las funciones siguientes son autoridades **requeridas**, no nombramientos.
Personas, facultades verificables, firmas y fecha efectiva permanecen pendientes.
Todas las filas: **PROPOSED_PENDING_APPROVAL**.

## Decisiones humanas

| Decisión | Propuesta sometida | Autoridades requeridas | Contenido que deben adjudicar antes de implementar | Estado |
| --- | --- | --- | --- | --- |
| A | A1: deny legacy 2FA + SSO existente + cierre de rutas locales | Seguridad/identidad; responsables AdminApps, ISO, MedSupplier; soporte | 403/código, UX/recuperación, cierre fallback MedSupplier, corte y posible indisponibilidad, AC-A | PROPOSED_PENDING_APPROVAL |
| B | B1 limitado + B3 durable; consulta viva sensible; 60 s candidato solo lectura no sensible | Seguridad/identidad; tres dueños de sesión; SRE; DBA si persistencia | Rechazo vs rol vivo, versión, eventos, SLA, refresh/logout, corte, carreras y AC-B | PROPOSED_PENDING_APPROVAL |
| C | Registro/receptores estrictos y familias locales/centrales separadas; H binding | Seguridad/identidad; tres dueños API; operación claves/IdP | Inventario por entorno, audiences/clients, issuer/algoritmo, legado, defaults, refresh y AC-C | PROPOSED_PENDING_APPROVAL |
| D | Intersección explícita + enforcement dominio/objeto | Seguridad/arquitectura; permisos AdminApps/QMS/MedSupplier | Matriz por rol/producto, read, empty/unknown, namespaces, backfill, AC-D | PROPOSED_PENDING_APPROVAL |
| E | E2 recomendado; E1 alternativa válida si se versiona | Comercial/billing con facultad; productos; seguridad; data owner | Trial, elegibilidad, duración, gracia/impago/cancelación, cohortes/derechos, contrato único y AC-E | PROPOSED_PENDING_APPROVAL |
| F | F2: intervalo UTC [inicio, fin); inicio obligatorio | Comercial/productos; arquitectura/seguridad/QA | Fronteras, null fin, rangos, retroactividad, reloj, cohortes y AC-F | PROPOSED_PENDING_APPROVAL |
| G | Dueño/pagador y beneficiarios explícitos; materialización por elegir | Comercial/billing; data owner/arquitectura/seguridad; productos; DBA/cambio | Exclusividad vs sharing/account, referencias conflictivas, schema/backfill/rollback y AC-G | PROPOSED_PENDING_APPROVAL |
| H | Principal estable y allowlist dimensional para toda credencial | Seguridad/identidad; data owners; tres dueños servicio; operaciones | Tuplas permitidas, credenciales legacy/config, excepciones con caducidad, audit failure y AC-H | PROPOSED_PENDING_APPROVAL |

## Los nueve diffs

Cada fila necesita aprobación **del artefacto exacto por hash**, además de su
decisión asociada. Para candidatos incompletos, revisar un sucesor compuesto;
no firmar el hash original como si incluyera adaptaciones futuras.

| Diff | Dependencia / autoridad | Disposición recomendada y condición de aprobación | Estado |
| --- | --- | --- | --- |
| P01 A legacy | A; seguridad/identidad + tres productos | Guard parcial; S1 y AC-A o contención con impacto aceptado; no cierre de A por sí solo. | PROPOSED_PENDING_APPROVAL |
| P02 B rol | B; dueños sesión + seguridad/SRE | Guard parcial, declarar alcance introspection; sucesor para B3 y AC-B. | PROPOSED_PENDING_APPROVAL |
| P03 C contexto | C/H; identidad + dueños API | Revisar tipos/defaults, binding receptor/principal, familias/refresh; config firmada y AC-C/H. | PROPOSED_PENDING_APPROVAL |
| P04 D scopes | D/B/C; permisos de tres productos | Validar policy, refresh y enforcement; inventario scopes y AC-D. | PROPOSED_PENDING_APPROVAL |
| P05 E modelo | E; comercial/billing + productos/datos | Solo bajo E2 adjudicada; con P06 y todos writers, cohortes y AC-E. | PROPOSED_PENDING_APPROVAL |
| P06 E serializers | E; comercial/billing + API AdminApps + productos/datos | Requiere revisión PATCH null/toggle/admin y regla compartida; con P05. | PROPOSED_PENDING_APPROVAL |
| P07 F inicio | F; comercial/productos + arquitectura/QA | Revisar frontera fin y reloj único si F2; AC-F y transición firmadas. | PROPOSED_PENDING_APPROVAL |
| P08 G contrato | G; comercial/billing/data/arquitectura + productos | Texto deliberativo; no aprueba schema ni migración; elaborar plan sucesor separado. | PROPOSED_PENDING_APPROVAL |
| P09 H contrato | H; identidad/data owners/servicios/operaciones | Texto deliberativo; completar legacy/config/registro; no aprueba rotación ni grants. | PROPOSED_PENDING_APPROVAL |

## Gates de ejecución independientes

| Gate | Aprobación nueva requerida | Sin ella |
| --- | --- | --- |
| Código futuro | Alcance/repositorios/slice, política elegida, hash de propuesta y revisores | No aplicar los nueve diffs ni implementar adaptación |
| Datos/DB | DBA + data owner + seguridad + autoridad cambio: target, backup/restore, DDL/backfill exactos, locks, ventana y rollback | No inspección DB nueva, migración, seed, RLS o grants |
| IdP/keys/config | Autoridad identidad/operación: entorno, registro, material por referencia segura, distribución/rotación y corte | No conexiones, secretos nuevos ni cambios de confianza |
| Lab/E2E | Target desechable, servicios, datos sintéticos y límites explícitos | No pruebas persistentes ni ejecución de runners históricos |
| Commit/push/deploy | Mandato explícito para operación/branch/entorno y aceptación de consumidores | No commit, push ni deploy |

## Plantilla de registro para cada aprobación real

No completar por inferencia. Una firma de recepción del paquete no es aprobación
de política ni autorización de ejecución.

| Campo | Valor actual |
| --- | --- |
| Campaign / decision / diff / slice y hashes exactos | REC-SSO-03 / PENDIENTE |
| Opción aprobada, rechazada o solicitada para revisión | PENDIENTE |
| Persona y función | PENDIENTE |
| Evidencia de facultad/mandato y referencia verificable | PENDIENTE |
| Alcance: productos, entornos, operaciones, tenants/cohortes | PENDIENTE |
| Contrato y configuración versionados | PENDIENTE |
| Fecha de firma, fecha efectiva y caducidad si aplica | PENDIENTE |
| Riesgo de compatibilidad/indisponibilidad aceptado | PENDIENTE |
| Criterios de aceptación y evidencia requerida | PENDIENTE |
| Rollback, responsable de parada y condiciones de corte | PENDIENTE |
| Autorización de código / DB / IdP / lab / publicación | PENDIENTE; ninguna implícita |
| Firma/referencia durable | PENDIENTE |

S3-IMP-01 = BLOCKED_PENDING_AUTHORITY; S3_DECISION_02A_NOT_CLOSED;
PHASE31_5 = EXECUTION_HELD. Cualquier liberación pertenece a su autoridad y
campaña correspondientes; no se hereda de REC-SSO-03.

## REC-SSO-03A — Texto exacto para adjudicación humana

Fecha de preparación: 2026-10-14, America/Costa_Rica.
Estado: **PROPOSED_PENDING_APPROVAL**. **Minuta propuesta, no suscrita.**
Resultado documental:
**DECISION_A_REVISED_PROPOSAL_READY_FOR_HUMAN_APPROVAL**.
Cero aprobaciones nuevas; la fila A, P01 y todos los gates anteriores conservan
su estado. Esta adenda desarrolla A1; no convierte la instrucción de preparar la
propuesta en autorización de implementación.

Paquete sometido: [REC-SSO-03A/REPORT.md](../REC-SSO-03A/REPORT.md),
[revisión P01-A-R1](../REC-SSO-03A/DIFF_A_REVISED_PROPOSAL.md),
[compatibilidad](../REC-SSO-03A/COMPATIBILITY.md) y
[plan y aceptación](../REC-SSO-03A/IMPLEMENTATION_AND_ACCEPTANCE.md).
Versiones exactas en [SHA256SUMS sucesor](../REC-SSO-03A/SHA256SUMS).
P01-A-R1 es especificación documental; su diff ejecutable no existe ni está aprobado.

### Minuta literal para firma futura

El siguiente texto solo tendrá efecto de adjudicación de arquitectura si lo
suscriben personas con facultades verificables y completan el registro de alcance.
Mientras eso no ocurra, es exclusivamente texto propuesto:

> Adopto la opción A1 revisada de DECISION-A, descrita en REC-SSO-03A, como
> dirección arquitectónica del alcance y las versiones documentales identificados
> en este registro. AdminApps será la autoridad central de autenticación y
> verificación de segundo factor. Ninguna ruta legacy, local, de recuperación,
> renovación o cambio de organización podrá conceder o ampliar una sesión
> autenticada omitiendo el segundo factor obligatorio.
>
> La revisión de P01 deberá incluir la denegación legacy en AdminApps y la
> adaptación coordinada de ISO Smart y MedSupplier. MedSupplier deberá cerrar la
> aceptación por contraseña/perfil local y la fabricación de identidad central,
> y solo establecer sesión tras autenticación central completa y validada.
> Ambos consumidores conservarán aislamiento de tenant, validación de producto
> y permisos de dominio; completar MFA no concede autorización universal.
>
> Los errores, la indisponibilidad o las respuestas no verificables de la
> autoridad central deberán fallar cerrados, sin rescate por contraseña local,
> perfil activo o caché positiva cuando la autoridad viva sea obligatoria.
> Las regresiones serán independientes de la implementación y demostrarán
> compatibilidad entre consumidores conforme a AC-A01–AC-A12.
>
> La activación queda condicionada a resolver y registrar las dependencias de
> audience, clientes/principales, familias de token, scopes y sesiones previas
> identificadas en A-DEP-01–A-DEP-04, así como la población MFA y recuperación
> A-DEP-05. No adjudico por esta firma valores de configuración ni decisiones
> B–H que requieren sus propias autoridades. No modifico las reglas comerciales
> pendientes ni concedo excepciones de MFA por fallback demo/dev.
>
> Esta adjudicación conceptual no aprueba el diff A original como remediación
> completa ni aprueba automáticamente un diff sucesor. La implementación
> requerirá un mandato separado con repositorios, alcance, contrato,
> configuración y artefactos exactos por hash. DB/migraciones, IdP/keys,
> laboratorio/servicios y commit/push/despliegue conservarán sus gates
> independientes. No autorizo esas operaciones mediante este texto.
>
> El corte deberá contar con aceptación explícita de ambos consumidores y del
> impacto de disponibilidad. La reversión conservará las denegaciones MFA,
> el cierre de rutas locales y las garantías de REC-2FA-04; si no existe una
> versión segura compatible, se cerrará el canal afectado y se reparará hacia
> delante. No se restaurarán factores consumidos ni autorizaciones revocadas.
>
> Preservo REC-2FA-04, REC-SSO-02 y la gobernanza vigente:
> S3-IMP-01 = BLOCKED_PENDING_AUTHORITY, S3_DECISION_02A_NOT_CLOSED y
> PHASE31_5 = EXECUTION_HELD. Esta adjudicación no declara Production Ready
> ni acredita pruebas runtime no ejecutadas.

### Registro humano pendiente para esta minuta

| Campo requerido | Valor actual |
| --- | --- |
| Campaign / decisión / revisión | REC-SSO-03A / DECISION-A / P01-A-R1 documental |
| Estado de aprobación | PROPOSED_PENDING_APPROVAL |
| Disposición humana: adoptar, rechazar o pedir revisión | PENDIENTE |
| Seguridad/identidad: persona, facultad verificable, firma y referencia durable | PENDIENTE |
| AdminApps: responsable, facultad verificable, firma y referencia durable | PENDIENTE |
| ISO Smart: responsable, facultad verificable, firma y referencia durable | PENDIENTE |
| MedSupplier: responsable, facultad verificable, firma y referencia durable | PENDIENTE |
| Soporte/operaciones/cambio: responsables de corte y parada, facultades y firmas | PENDIENTE |
| Versiones documentales elegidas y hashes ratificados | PENDIENTE; candidatos en SHA256SUMS sucesor |
| Productos, entornos, canales, tenants/cohortes y población MFA | PENDIENTE; no inferir alcance universal de ejecución |
| Registro C/H: issuer, audience, client, principal y familias | PENDIENTE; A-DEP-01/02 |
| Matriz D y política B de sesiones previas/refresh/frescura | PENDIENTE; A-DEP-03/04 |
| Enrolamiento y recuperación central | PENDIENTE; A-DEP-05 |
| Impacto/ventana de indisponibilidad y tratamiento de clientes incompatibles | PENDIENTE; sin contención aislada autorizada |
| AC-A01–AC-A12 y evidencia revisada por consumidor | NOT_EXECUTED; aceptación humana PENDIENTE |
| Rollback, umbrales operativos, responsable de parada y reapertura | PENDIENTE |
| Fecha de firma, fecha efectiva y caducidad si aplica | PENDIENTE |
| Artefacto ejecutable exacto y mandato de código | PENDIENTE; no generado ni concedido |
| DB / IdP-config-keys / lab / commit-push-deploy | PENDIENTE; ninguna autorización implícita |

### Continuidad del sello histórico

La matriz anterior se conserva byte a byte en
[APPROVAL_MATRIX.before.md](../REC-SSO-03A/evidence/APPROVAL_MATRIX.before.md).
El SHA256SUMS de REC-SSO-03 no se reescribe: su entrada APPROVAL_MATRIX.md
identifica esa versión anterior. Solo esta adenda cambia la matriz actual;
los registros de decisiones, diffs y gates previos permanecen intactos.
El sello de REC-SSO-03A identifica la versión con adenda. No confundir ninguno
de los sellos con una firma humana o autorización.
