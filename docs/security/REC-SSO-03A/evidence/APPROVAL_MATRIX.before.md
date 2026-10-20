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
