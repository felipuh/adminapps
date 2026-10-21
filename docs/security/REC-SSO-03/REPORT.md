# REC-SSO-03 — Cross-Product Security Contract Adjudication

Fecha: 2026-10-14, America/Costa_Rica. Campaña exclusivamente de análisis y
gobernanza. Estado de todas las propuestas: **PROPOSED_PENDING_APPROVAL**.

## A. Executive Verdict

**GOVERNANCE_PACKAGE_READY_FOR_HUMAN_REVIEW**. Existe evidencia suficiente para
someter alternativas y bloqueos a decisión humana: se revisaron los tres
repositorios, los contratos, los nueve métodos fallidos y los nueve diffs de
REC-SSO-02. El veredicto califica este paquete documental; no la seguridad del
runtime, la aprobación de las decisiones ni la preparación de producción.

**Ninguna decisión aprobada, ninguna remediación completada en REC-SSO-03 y
ninguna declaración de Production Ready.** No se aplicaron diffs ni se ejecutaron
pruebas de aplicación. Los 23 PASS / 9 FAIL y 21/21 de 2FA son evidencia histórica
de REC-SSO-02, con los límites de dobles y transporte sustituido allí descritos.

Hallazgos que condicionan la adjudicación:

1. **A es prioridad 1:** el contrato legacy autentica tras contraseña aunque haya
   2FA. MedSupplier además conserva un recorrido local que puede aceptar contraseña
   y perfil activo sin identidad AdminApps; denegar en AdminApps no basta.
2. **C/H son prioridad 2:** registrar `client_id/aud` no liga por sí solo al
   llamador de introspection. Los validadores JWT de ambos productos carecen de
   `ISSUER/AUDIENCE` en su configuración fuente y aceptan familias de tokens locales
   y centrales. La transición debe separar esas familias explícitamente.
3. **D es prioridad 3:** recortar scopes emitidos no añade enforcement en APIs.
   ISO Smart usa roles locales/QMS; MedSupplier añade side, account y visibilidad.
4. **B es prioridad 4:** comparar el rol actual solo protege introspection. No
   invalida por sí mismo sesiones locales, refresh, cachés ni tokens tras
   revocación/reactivación o cambio de rol de ida y vuelta.
5. **E/F/G y resto de H son prioridad 5:** E enfrenta contratos contradictorios;
   F y G prueban ausencia de la política candidata, no un exploit HTTP. La decisión
   comercial sigue perteneciendo a una autoridad humana verificable.

Se mantienen sin transición de estado:

- **S3-IMP-01 = BLOCKED_PENDING_AUTHORITY**.
- **S3_DECISION_02A_NOT_CLOSED**.
- **PHASE31_5 = EXECUTION_HELD**.
- **REC-2FA-04 preservado**, incluido su cierre histórico y sus límites; no se
  reinterpreta como PASS nuevo de SSO o IdP.
- **Fail-closed y deny-by-default** como requisitos de las propuestas. Los gaps
  existentes se documentan; no se certifica que todos los recorridos ya los cumplan.

## B. Git Integrity

| Repositorio descubierto | HEAD | Rama | Baseline |
| --- | --- | --- | --- |
| `/home/felipe/proyectos/adminapps` | `b144b2505659ad39f756b9bc4530a7f24fe8c3ad` | `hardening/p0-p1-enterprise-readiness` | Cambios locales REC-SSO-02 y financieros presentes |
| `/home/felipe/proyectos/isosmart` | `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` | misma rama | Cambios locales financieros/foundation/settings presentes |
| `/home/felipe/proyectos/ISO_Smart_MedSupplier` | `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` | misma rama | Limpio |

Los tres índices estaban limpios. [Baseline](evidence/baseline.json) conserva
status detallado, HEAD, rama, worktrees, hashes de diff tracked/index y entradas
Git tracked/untracked no ignoradas: **15.575 / 15.053 / 14.992**, respectivamente.
Archivos regulares se comparan por SHA-256; symlinks por destino, sin seguirlos.
No se afirma cobertura global de ignored, secretos o metadatos Git. Los 40
artefactos enumerados en SHA256SUMS de REC-SSO-02 —incluidos logs ignorados— sí
se verificaron adicionalmente: **40/40 coinciden**.

Se leyó `isosmart/AGENTS.md`; no se hallaron AGENTS.md en AdminApps, MedSupplier
ni sus padres inspeccionados. No se usaron agentes delegados. No hubo fetch,
staging, commit, push, deploy, migración, servicio, DB, autenticación real,
conexión externa ni carga de `.env`/settings de aplicación.

Solo se añadieron artefactos bajo `adminapps/docs/security/REC-SSO-03/`.
**Integridad final PASS: 45.620/45.620 entradas de baseline intactas, cero
cambios o eliminaciones preexistentes y cero archivos nuevos fuera del paquete.**
La [comparación final](evidence/integrity-final.json) es la evidencia de
preservación, incluidos los cambios locales y antecedentes. Los nueve targets
siguen coincidiendo con el manifiesto previo (G/H siguen ausentes); los nueve
`git apply --check` individuales retornaron 0, **sin aplicar**. Esto acredita
contexto de parche, no corrección, composición ni runtime.
Los siete documentos cubren A–L, A–H y P01–P09; enlaces locales y whitespace
verificados en [document-checks.json](evidence/document-checks.json).
[SHA256SUMS](SHA256SUMS) sella los artefactos de esta campaña.

## C. Nine-Failure Traceability Matrix

Fuentes de resultados: [tests-after.json](../REC-SSO-02/evidence/tests-after.json)
y `backend/scripts/rec_sso_02_offline.py:316–370`. Cada fila es un método fallido;
viewer/auditor contiene dos subcasos. No son nueve vulnerabilidades explotadas.
Los identificadores de evidencia se resuelven en [EVIDENCE.md](EVIDENCE.md).

| ID / método DecisionTests | Causa y observación demostrada | Contrato / consumidor afectado | Decisión / diff / prioridad |
| --- | --- | --- | --- |
| NF01 `test_legacy_2fa_requires_second_factor` | `validate_credentials` devuelve `valid=true` sin verificar segundo factor (AA1). | Identidad central/MFA; ambos backends consumen `valid` y crean sesión (IS1/MS1). | A / A / 1 |
| NF02 `test_wrong_audience_is_rejected` | Introspection no valida audiencia; acepta token sintético de audience no registrada (AA2). | Confianza SSO; ambos validadores locales también requieren adaptación (IS2/MS2). | C + H / C / 2 |
| NF03 `test_missing_audience_is_rejected` | Token sin aud no es rechazado por esa política (AA2). | Igual contrato, ausencia de claim no debe significar audiencia universal. | C / C / 2 |
| NF04 `test_viewer_and_auditor_never_receive_write_scope` | Emisión fija `tenant:write` independientemente del rol (AA2). | Rol/membresía × producto; ISO CanEdit/QMS y MedSupplier side/account (IS3/MS3). | D / D / 3 |
| NF05 `test_write_scope_requires_entitlement` | Org admin recibe write aunque el producto esté denegado (AA2). | Entitlement autoritativo (CT1/CT2); ambos deben exigir decisión efectiva en API. | D / D / 3 |
| NF06 `test_role_revocation_does_not_return_old_role` | Introspection relee membresía pero retorna rol del token (AA2). La aserción permite rechazo O rol vivo; no elige política. | Frescura CT2/CT3, perfiles y refresh de ambos (IS2/MS2/IS4/MS4). | B / B / 4 |
| NF07 `test_trial_requires_subscription_candidate` | Trial con billing sin suscripción permite acceso (AA3). CT1 exige suscripción; CT2 exime trial. | Conflicto comercial explícito; afecta ISO_SMART y MEDSUPPLIER, no autoridad para cambiar la regla. | E / E-model + E-serializers / 5 |
| NF08 `test_future_start_denies_candidate` | starts_at futuro no afecta access_allowed (AA3); contrato vigente enumera fin, no inicio. | Vigencia pendiente; ambos reciben allowed/reason y snapshots. | F / F / 5 |
| NF09 `test_foreign_subscription_denies_candidate` | Modelo/serializer aceptan suscripción activa también referenciada por otra org (AA3/AA4). Objetos en memoria; no escritura HTTP ni ownership contractual probado. | Dueño/beneficiarios sin definir (CT1/CT2); ambos productos comerciales. | G / G contractual / 5 |

**H no tiene una aserción independiente en estos nueve métodos.** Su fundamento
adicional es `require_api_key`/servicios (AA1/AA5). No se inventa un décimo fallo
ni se fuerza correspondencia 1:1: C y D tienen dos fallos; E tiene dos diffs.

## D. Human Decisions A–H

[DECISIONS.md](DECISIONS.md) contiene problema, alternativas, recomendación,
impacto en cada producto, retrocompatibilidad, rollout, aceptación positiva y
negativa y autoridad para **cada** A–H. Todas: **PROPOSED_PENDING_APPROVAL**.
Los roles de aprobación son requisitos; no nombran personas ni les atribuyen
facultades no verificadas.

## E. Nine Proposed Diffs Assessment

[DIFF_ASSESSMENT.md](DIFF_ASSESSMENT.md) evalúa individualmente los nueve candidatos,
incluidos defectos que impiden tratarlos como paquete ejecutable. Los originales
permanecen en REC-SSO-02. No hay nueva propuesta Python ni parche combinado.

## F. ISO Smart Compatibility

**REQUIRES_COORDINATED_ADAPTATION; RUNTIME_NOT_TESTED.** La revisión de código
confirma piezas reutilizables: rechazo de login local sin bypass explícito,
validación fresca de ISO_SMART al login, cookies/CSRF y validación autoritativa en
creación QMS. No demuestra cobertura universal de permisos ni revocación.
[Matriz A–H y por diff](COMPATIBILITY.md#iso-smart).

## G. MedSupplier Compatibility

**BLOCKED_BY_STATIC_GAPS; RUNTIME_NOT_TESTED.** El cliente de producto falla
cerrado ante denegación explícita, pero el login admite un recorrido local con
perfil activo; su serializer no valida producto antes de emitir JWT. El endpoint
de integration status sí consulta MEDSUPPLIER, lo que no prueba enforcement en
todas las operaciones. El middleware legacy tiene condiciones de omisión y usa
módulos; no sustituye esa prueba. [Matriz](COMPATIBILITY.md#medsupplier).

## H. Security Contract Recommendations

Proponer un contrato versionado común, sin modificar todavía CT1–CT5:

- Identidad `(issuer, subject)` y tenant global UUID inequívocos; IDs locales solo
  en proyecciones/adapter explícito. No reatribuir identidad por email o nombre.
- Resultado de autenticación distingue desafío, autenticación completa y
  denegación; solo la segunda puede abrir sesión. Preservar consumo irreversible
  y commit boundary de REC-2FA-04.
- Confianza comprobada por firma, algoritmo, tipo, issuer, audiencia receptora,
  cliente y contexto. Un registro público no autentica a un servicio. H limita
  introspection por principal, operación, tenant y producto.
- Autorización efectiva = identidad vigente ∩ membresía/tenant ∩ producto vigente
  ∩ scopes concedidos ∩ permisos del dominio/objeto. `active=true`, rol global,
  plan o `allowed_products` aislados no conceden acceso universal.
- Añadir versión de política/decisión, `evaluated_at`, `expires_at`, razón estable
  y trace ID. Sin respuesta verificable y suficientemente fresca: denegar.
  No usar una caché positiva ante caída cuando la operación exige consulta viva.
- Mantener respuestas vigentes de introspection (200 inactive, 401 credencial,
  400 payload, 503 autoridad no disponible); adaptar errores del consumidor según
  CT3: 401 identidad, 403 permiso, 503 frescura/autoridad. Nuevas razones F/G deben
  preservar `allowed=false`; razón desconocida nunca concede permiso.
- Política comercial E/F/G única, explícita y auditada. No extrapolar aprobación
  financiera o de una fase histórica al contrato de esta campaña.

## I. Implementation Slices

[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) separa código sin nuevas
migraciones, cambios contractuales/configuración, DB e IdP. Prioridad de
adjudicación: **A → C/H-binding → D → B → E/F/G/H-resto**. Las dependencias de
implementación pueden requerir trabajo conjunto; no autorizan alterar este orden
de atención al riesgo ni omitir gates.

## J. Acceptance Criteria

La [matriz de aceptación](IMPLEMENTATION_PLAN.md#acceptance-criteria) enlaza NF01–09
con positivos y negativos por decisión y agrega H, rutas alternas y revocación.
Ningún criterio runtime se marca PASS en REC-SSO-03. Un contrato comercial
adjudicado distinto de la aserción candidata exige un test sucesor trazable; no
un skip/expectedFailure ni borrar el resultado histórico.

## K. Explicit Approval Matrix

[APPROVAL_MATRIX.md](APPROVAL_MATRIX.md) registra decisiones y nueve diffs,
firmantes requeridos, alcance, precondiciones y campos sin completar. La
aprobación conceptual de A–H no aprueba automáticamente un diff, configuración,
DB, IdP, laboratorio ni despliegue.

## L. Next Authorized Action

**Acción actualmente autorizada:** revisión humana de este paquete, empezando
por A y el cierre de rutas alternativas de MedSupplier; registrar adjudicaciones
en la matriz con identidad/facultad verificable, opción, alcance, evidencia,
fecha efectiva, aceptación y rollback. Se puede continuar revisión documental.

**Acción futura que requiere mandato nuevo:** implementar el slice expresamente
aprobado con su alcance y repositorios; después autorizar por separado laboratorio
persistente, DB/IdP, commit/push/deploy si correspondiera. No se solicita ni se
presume autorización automática al entregar este paquete. Los tres bloqueos de
gobernanza siguen vigentes aunque se apruebe una decisión REC-SSO-03.
