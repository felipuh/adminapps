# Evaluación de los nueve diffs no aplicados

**Los nueve: PROPOSED_PENDING_APPROVAL; NO APLICADOS; runtime NOT_EXECUTED.**
Cada ficha incorpora la decisión enlazada, incluidos sus positivos/negativos y
autoridades, y detalla límites específicos del diff. Los hashes, targets y
`git apply --check` están en [proposals-review.json](evidence/proposals-review.json).
Pasar ese check no aprueba contenido, composición, política ni despliegue.

## P01 — A-legacy-deny-2fa.patch

[Original](../REC-SSO-02/proposals/A-legacy-deny-2fa.patch) · [Decisión A](DECISIONS.md#a-legacy-credential-validation-con-2fa--prioridad-1).

- **Problema:** NF01; se emite valid=true tras password sin factor.
- **Alternativas/recomendación:** guard 403 del candidato o legacy versionado con
  challenge; recomendar el guard como contención de servidor, acompañado por
  adaptación A1 y cierre de rutas locales, por reutilizar el protocolo existente.
- **AdminApps:** inserta comprobación de is_enabled antes de membresías; no emite
  challenge ni tokens y no implementa sanitización general de errores DB legacy.
- **ISO Smart:** entiende valid=false/403, pero pierde login 2FA hasta adaptar
  backend/UX cookie. **MedSupplier:** su backend deniega, pero serializer puede
  continuar por contraseña/perfil local; adaptación de ese recorrido obligatoria.
- **Retrocompatibilidad/rollout:** cuenta 2FA deja de entrar por legacy; sin DDL
  nuevo, con precondición de readiness users.0004 para SSO. Activación conjunta o
  contención con indisponibilidad aprobada, nunca fallback de contraseña.
- **Aceptación +/−:** no-2FA vigente entra; 2FA recibe 403/código exacto, sin sesión;
  SSO TOTP/backup completa; ruta local, factor inválido/replay/outage no rescatan.
- **Aprobación:** seguridad/identidad + dueños de los tres productos y soporte.
  **Disposición:** candidato parcial; no aprobar como cierre completo de A.

## P02 — B-reject-stale-role.patch

[Original](../REC-SSO-02/proposals/B-reject-stale-role.patch) · Decisión B.

- **Problema:** NF06; snapshot de rol ya revocado sigue activo en introspection.
- **Alternativas/recomendación:** rechazar por mismatch o devolver rol efectivo;
  recomendar rechazo como guard acotado, complementado por revocación durable B3.
- **AdminApps:** añade `role=parsed.get('role')` a exists(); protege ese endpoint
  y también deniega rol ausente. No toca emisión, refresh, logout ni versiones.
- **ISO Smart:** debe llamar autoridad y cerrar cookie/bearer obsoletos; hoy el
  validador local no recibe el rechazo. **MedSupplier:** misma brecha en bearer,
  refresh y perfiles; ningún efecto automático sobre MedSupplierUserScope.
- **Retrocompatibilidad/rollout:** cambios de rol de cualquier dirección fuerzan
  reautenticación; no DDL para diff, sí gate separado para B3. Integrar validación
  en consumidores antes de afirmar reducción global de la ventana de revocación.
- **Aceptación +/−:** rol igual con identidad viva permite; rol distinto/ausente
  deniega. El test de cambio ida/vuelta y reactivación requiere B3: el diff solo
  volvería a aceptar el token si el rol vuelve a coincidir.
- **Aprobación:** seguridad/identidad + propietarios de sesión/SRE de los tres.
  **Disposición:** aceptar para revisión como control parcial; insuficiente para B.

## P03 — C-register-client-audience.patch

[Original](../REC-SSO-02/proposals/C-register-client-audience.patch) · Decisiones C/H.

- **Problema:** NF02/NF03; contexto aud/client no registrado se acepta.
- **Alternativas/recomendación:** registro estático, referencia/introspection
  obligatoria o IdP; recomendar registro validado por entorno y receptor, con H.
- **AdminApps:** agrega allowlist a login/verify/introspection. No autentica cliente
  público, no liga key al receptor, no cambia SimpleJWT global ni refresh. La
  normalización previa aún convierte algunos valores inválidos a portfolio o a
  strings. Validar tipos antes de defaults; política explícita para omisión.
- **ISO Smart:** separar cookie local/bearer central, issuer/aud y UUIDs; **MedSupplier:**
  separar tokens locales/centrales, login/refresh y receptor MEDSUPPLIER. Ambos
  requieren validación local estricta, no solo cambios al emisor.
- **Retrocompatibilidad/rollout:** registro ausente deniega todo; inventario firmado,
  configuración y corte antes de activar. Sin migración propia; IdP/rotación de
  claves, si se eligen, son otros slices. No defaults amplios para salvar clientes.
- **Aceptación +/−:** cliente/aud registrados válidos funcionan; ausentes/ajenos/
  mixtos/malformados deniegan. Añadir key de otro producto con token bien formado,
  refresh y challenge cross-client: no cubiertos íntegramente por este diff.
- **Aprobación:** identidad/seguridad + tres dueños API + operación de claves.
  **Disposición:** revisar y completar; no aprobación del diff tal cual como C/H.

## P04 — D-role-product-scopes.patch

[Original](../REC-SSO-02/proposals/D-role-product-scopes.patch) · Decisión D.

- **Problema:** NF04/NF05; write incondicional en access y refresh.
- **Alternativas/recomendación:** intersección candidata o servicio de capacidades;
  recomendar intersección con política explícita y enforcement de dominio.
- **AdminApps:** elimina write constante, conserva identidad e intersecta role/
  entitlement de producto registrado. No valida estructura completa del config:
  dict/lista/string inesperados pueden lanzar error o producir conjuntos
  incorrectos. No filtra mediante un vocabulario aprobado ni renueva scopes en
  refresh estándar. No evalúa acción u objeto del consumidor.
- **ISO Smart:** intersecar con CanEdit/QMS/objeto; revisar jerarquías ordinales.
  **MedSupplier:** intersecar con side/account/visibilidad; jamás mapear tenant:write
  a supplier_admin automáticamente. Mappings desconocidos deben denegar.
- **Retrocompatibilidad/rollout:** policy/scopes ausentes quedan sin permisos tenant;
  completar inventario aprobado, validación de configuración y transición de
  sesiones. Sin DDL para algoritmo; backfill de scopes no autorizado implícitamente.
- **Aceptación +/−:** permiso explícito y producto vigente conceden solo intersección;
  viewer/auditor, vacío, unknown, entitlement negativo o revocado no reciben write;
  petición API directa debe denegarse aunque UI o token antiguo indiquen permiso.
- **Aprobación:** seguridad/arquitectura + propietarios de permisos/QMS/MedSupplier.
  **Disposición:** completar validación de tipos, refresh y consumidores antes de ejecutar.

## P05 — E-trial-subscription-model.patch

[Original](../REC-SSO-02/proposals/E-trial-subscription-model.patch) · Decisión E.

- **Problema:** NF07 y conflicto CT1/CT2; runtime permite trial sin billing efectivo.
- **Alternativas/recomendación:** E1 excepción explícita o E2 suscripción obligatoria;
  recomendar E2 para aprobación comercial, sin asumirla vigente. Solo si se aprueba,
  eliminar la excepción runtime como este diff.
- **AdminApps:** elimina return True de trial; afecta access_allowed/reason y todos
  los lectores de la propiedad, incluidos integración/billing. No valida escrituras.
- **ISO Smart:** denegará trials afectados en validate de login; requiere sesiones
  frescas y UX. **MedSupplier:** cliente recibe deny, pero falta enforcement general.
- **Retrocompatibilidad/rollout:** existentes sin suscripción o con suscripción
  bloqueada pierden acceso. No DDL; inventario/cohortes/suscripciones requieren gate
  comercial/datos. Activar junto con escritura uniforme, P06 y arreglo de toggle.
- **Aceptación +/−:** billing=false y trial con suscripción válida permiten; trial
  sin suscripción o con estados bloqueados deniega; fallback a org solo si válido.
- **Aprobación:** comercial/billing + productos + seguridad/datos.
  **Disposición:** condicional a E2; nunca desplegar aislado de P06 y rutas faltantes.

## P06 — E-trial-subscription-serializers.patch

[Original](../REC-SSO-02/proposals/E-trial-subscription-serializers.patch) · Decisión E.

- **Problema:** validación de create/update solo exige suscripción para active;
  es la cara de escritura de NF07, no una décima aserción.
- **Alternativas/recomendación:** ampliar dos guards o unificar validación de dominio
  para todo writer. Recomendar regla compartida; diff ilustra E2 pero queda incompleto.
- **AdminApps:** amplía a trial dos serializers. Toggle trial en views.py:179–187
  sigue guardando sin validar; admin/model enable también necesitan revisión.
  En PATCH `subscription:null`, validate reutiliza la suscripción de instance,
  aunque save puede borrarla: la validación puede evaluar estado distinto al final.
- **ISO Smart:** impacta onboarding y mensajes comerciales, no su transporte;
  **MedSupplier:** mismo impacto de provisión/contrato y necesidad de enforcement.
- **Retrocompatibilidad/rollout:** create trial antes válido puede dar 400; arreglar
  semántica campo omitido/null y todos los writers, con P05. Sin DDL propia; no
  crear suscripciones como efecto lateral ni ignorar registros existentes.
- **Aceptación +/−:** create/PATCH/toggle/admin admiten estado final válido; rechazan
  trial sin billing efectivo, null que elimina último vínculo y fallback bloqueado.
  PATCH que no cambia subscription conserva una válida; disabled no concede acceso.
- **Aprobación:** comercial/billing + API AdminApps + ambos productos + data owner.
  **Disposición:** REQUIRES_REVISION, no basta ampliar condiciones.

## P07 — F-entitlement-start.patch

[Original](../REC-SSO-02/proposals/F-entitlement-start.patch) · Decisión F.

- **Problema:** NF08; starts_at futuro no deniega.
- **Alternativas/recomendación:** inicio efectivo con fin inclusivo o `[inicio, fin)`;
  recomendar F2 para adjudicación, revisando diff para fin y reloj único.
- **AdminApps:** añade control/razón antes de ends_at, conserva fin inclusivo y
  múltiples llamadas timezone.now. No valida rangos ni expone evaluated_at.
- **ISO Smart:** soportar reason nueva y límite de caché; **MedSupplier:** igual,
  además de mover validación desde diagnóstico a acciones protegidas.
- **Retrocompatibilidad/rollout:** tenants con inicio futuro pierden acceso hasta
  fecha aprobada; F2 cambia también igualdad al fin. Sin DDL para propiedad;
  correcciones de datos/constraints solo tras autorización. No hacer starts_at null
  por inferencia: hoy el campo no es nullable.
- **Aceptación +/−:** t=inicio permite, t<inicio deniega; t=fin deniega bajo F2
  (el diff actual no lo cumple); nulo fin, timezone, rango inválido y caché vencida.
- **Aprobación:** comercial/productos + arquitectura/seguridad/QA.
  **Disposición:** REQUIRES_REVISION si se aprueba intervalo recomendado.

## P08 — G-subscription-binding-contract.patch

[Original](../REC-SSO-02/proposals/G-subscription-binding-contract.patch) · Decisión G.

- **Problema:** NF09; no owner/beneficiario explícito. Diff solo crea texto en ruta
  inexistente; no pretende arreglar serializer ni modelo.
- **Alternativas/recomendación:** exclusividad, dueño con beneficiarios o billing
  account. Recomendar dueño/beneficiarios explícitos, eligiendo materialización
  solo después de decisión comercial y revisión de datos.
- **AdminApps:** obliga a diseñar relación y resolver referencias conflictivas.
  **ISO Smart:** consume decisión central, no reasigna billing local.
  **MedSupplier:** no confundir SupplierAccount con beneficiario central.
- **Retrocompatibilidad/rollout:** puede denegar compras compartidas actuales;
  inventariarlas y adjudicarlas. Requiere contrato/schema/backfill/rollback futuros;
  no hay plan DDL ejecutable en el diff. Preservar facturas y UUIDs históricos.
- **Aceptación +/−:** dueño/beneficiario autorizado funciona; ajeno, revocado o
  producto distinto deniega en runtime y todo writer. Revisar referencias de las
  dos FK, no solo Entitlement.subscription.
- **Aprobación:** comercial/billing, data owner/arquitectura/seguridad, ambos
  productos; DBA/cambio únicamente para futuro plan de ejecución.
  **Disposición:** texto para deliberación; implementación BLOCKED.

## P09 — H-integration-key-scope-contract.patch

[Original](../REC-SSO-02/proposals/H-integration-key-scope-contract.patch) · Decisión H.

- **Problema:** evidencia adicional AA1/AA5, fuera de NF01–09; autenticación de key
  no limita operación ni contexto. Diff solo crea texto en ruta inexistente.
- **Alternativas/recomendación:** principal registrado, key por tenant/producto o
  workload identity; recomendar principal estable y menor privilegio con C.
- **AdminApps:** autorización dimensional y excepciones auditadas; cubrir legacy
  sin credential_id y fallback configurado, no solo keys hashed nuevas.
  **ISO Smart:** registro de operaciones QMS/identidad/producto y eventos con
  direcciones separadas. **MedSupplier:** registro MEDSUPPLIER y tenants propios.
- **Retrocompatibilidad/rollout:** clientes con key global/no registrada pierden
  acceso. Inventario, mapeo, corte y observabilidad; elegir persistencia/config
  antes de definir migración. integration.0006 no implementa este contrato;
  rotación/secretos/IdP no están autorizados por el diff.
- **Aceptación +/−:** una key registrada permite contexto exacto; misma key cruzando
  producto/tenant/operación, renombrada, revocada/rotada o fallback sin registro
  deniega; DB/auditoría no disponibles nunca amplían permisos.
- **Aprobación:** seguridad/identidad + data owners + tres dueños de servicio +
  operaciones; DBA/IdP según futura materialización.
  **Disposición:** texto para deliberación; implementación BLOCKED.

## Composición y suficiencia

P02/P03/P04 parten del mismo SHA de sso_views.py; P05/P07 del mismo SHA de models.py.
Los checks individuales no prueban que puedan concatenarse ni que sean coherentes
con refresh, configuración o política comercial. La futura implementación debe
producir un diff compuesto revisable sobre la baseline entonces vigente, con
pruebas por decisión, preservando los originales REC-SSO-02. P05/P06 son una misma
política de runtime/escritura; aplicarlos separadamente generaría divergencia.
P03 depende de H para binding del llamador y P04 de B para frescura efectiva.
**Ninguno de los nueve es un paquete suficiente para cierre transversal.**
