# Propuestas de adjudicación humana A–H

Todas las decisiones y recomendaciones de este archivo están en
**PROPOSED_PENDING_APPROVAL**. Ninguna alternativa ha sido elegida por autoridad
humana en esta campaña. Referencias AA/IS/MS/CT: [EVIDENCE.md](EVIDENCE.md).
Aceptación indicada aquí = requisito futuro, **NOT_EXECUTED**.

## A. Legacy credential validation con 2FA — prioridad 1

**Problema demostrado:** NF01, AA1. Contraseña válida produce `valid=true` aunque
2FA esté habilitado. IS1/MS1 consumen ese booleano sin challenge. MS1 además
permite contraseña local/perfil activo sin respuesta de identidad central.

**Alternativas:** (A1) denegar legacy para cuentas 2FA y completar autenticación
por SSO existente; (A2) versionar legacy con estados challenge/verified y adaptar
ambos productos; (A3) retirar todo legacy en un corte único. Mantener una vía
password-only para una identidad con 2FA no es una alternativa admisible.

**Recomendación:** A1, con cierre coordinado de rutas alternas y adaptadores SSO
de ambos consumidores. Reutiliza la semántica transaccional existente y reduce
protocolos MFA. A2 solo si los dueños demuestran una necesidad de transición;
debe conservar idénticas garantías. El diff A solo contiene la denegación,
no los adaptadores ni el cierre de fallback. Una contención inmediata con pérdida
temporal de login 2FA requiere decisión explícita de seguridad/producto; no se
presume aceptación de esa indisponibilidad.

**Impactos:** AdminApps devuelve 403 `valid=false`, `second_factor_required`
tras contraseña correcta; conserva login/challenge/verificación SSO. ISO Smart
debe añadir estados de desafío en backend/UI y emitir cookies solo tras el
segundo factor, manteniendo CSRF. MedSupplier debe eliminar el fallback de
contraseña/perfil como autoridad central y añadir desafío/UX; no basta con que
AdminAppsAuthBackend retorne None. Ambos deben distinguir recuperación de cuenta,
error de contraseña y segundo factor sin filtrar secretos.

**Retrocompatibilidad/rollout:** rompe disponibilidad de login legacy para 2FA;
inventariar cuentas/canales sin extraer secretos en una futura intervención
autorizada. Preparar consumidores y contratos, probarlos juntos, activar la
denegación y retirar rutas antiguas. No crear sesiones parciales ni admitir
headers de bypass en producción. El cambio de guard no requiere nueva migración;
el SSO existente depende de que users.0004 esté correctamente desplegada, estado
no verificado. No modificar ni revertir REC-2FA-04.

**Aceptación +:** sin 2FA y con membresía/producto vigentes, login permitido;
con 2FA, contraseña → challenge sin sesión → TOTP/backup válido → sesión del
tenant/producto solicitado. **Aceptación −:** legacy con 2FA; código incorrecto,
expirado, replay, desafío de otro tenant/cliente, caída de autoridad, fallo de
emisión después del consumo; contraseña local utilizable/perfil activo y bypass
header no deben rescatar una denegación. No reponer factor consumido en rollback.

**Autoridad requerida:** responsables verificables de seguridad/identidad,
AdminApps, ISO Smart y MedSupplier; operaciones de soporte para recuperación y
corte. Aprobación de ventana/impacto separada de la opción técnica.

## B. Revocación y frescura — prioridad 4

**Problema demostrado:** NF06, AA2. Rol snapshot sigue retornándose aunque la
membresía viva cambió. El fix previo relee actividad de usuario/org/membresía,
pero IS2/MS2 sincronizan perfiles desde JWT y IS4/MS4 refrescan claims previos.

**Alternativas:** (B1) rechazar token al cambiar rol; (B2) devolver rol/scopes
efectivos actuales sin invalidar token; (B3) revocación durable mediante versión
de identidad/sesión y política de frescura, combinada con B1 o B2. TTL corto solo
acota una ventana y no satisface por sí mismo revocación inmediata/permanente.

**Recomendación:** B1 como contención limitada y B3 como objetivo, con una
versión monotónica que cambie ante revocación relevante; no usar comparación de
rol como sustituto. Un único resultado autoritativo de identidad/membresía/
permisos por operación sensible, sin caché positiva. Para lecturas no sensibles,
proponer máximo 60 s y nunca más allá de expiración de decisión/token/entitlement;
el número es candidato para firma, no SLA vigente. Los 300 s actuales y access
de 8 h AdminApps / 60 min productos no constituyen SLA aprobado.

**Impactos:** AdminApps debe rechazar rol obsoleto y, posteriormente, revalidar
refresh contra versión/estado vivo. ISO Smart debe incorporar revocación en
cookie y bearer, cachés/proyecciones QMS y no permitir que un JWT viejo reactive
un perfil. MedSupplier debe hacerlo en bearer/refresh/localStorage y perfiles
supplier/customer. Ningún logout local garantiza logout central ni del otro
producto; especificar alcance individual vs global.

**Retrocompatibilidad/rollout:** cambios de rol incluso de aumento fuerzan
reautenticación bajo B1. Tokens viejos sin versión necesitan expiración/corte
aprobados; evitar aceptar claims ausentes como versión actual. Diff B no requiere
DDL, pero B3 sí necesita diseño de persistencia/DB o autoridad IdP explícita.
Inventariar todas las rutas de refresh y switch-organization; desplegar validación
y contexto antes de emisión versionada y corte. Cachés incluyen subject, tenant,
producto, principal/política y versión; no reutilizar allow entre contextos.

**Aceptación +:** sesión vigente conserva acceso autorizado y reautenticación
obtiene rol actual. **Aceptación −:** revocar usuario, membresía, organización,
producto o scope bloquea operación sensible y refresh; rol admin→viewer→admin o
desactivar→reactivar no resucita tokens revocados bajo B3; logout/rotación/replay,
caída de autoridad y caché previa positiva no conceden acceso. Medir latencia de
revocación y documentar carrera consulta/uso; no prometer atomicidad distribuida.

**Autoridad requerida:** seguridad/identidad y arquitectos/propietarios de sesión
de los tres productos; SRE para capacidad/SLA; DBA si hay versión persistente.

## C. Issuer, audience y client binding — prioridad 2

**Problema demostrado:** NF02/NF03. AA2 valida issuer solo en introspection;
audiencia/cliente no se limitan. IS2/MS2 usan HS256 y misma variable de secreto
SSO como signing key configurable; no se inspeccionó si los valores desplegados
son iguales. SIMPLE_JWT no configura issuer/audience. Tokens locales usan ID
local de organización; tokens centrales usan UUID global.

**Alternativas:** (C1) registro allowlist de clientes/audiencias y validadores
estrictos por familia de token; (C2) tokens de referencia con introspection
obligatoria; (C3) migrar a emisor asimétrico/federación IdP. C2 agrega dependencia
de disponibilidad; C3 agrega operación de claves/IdP y no es requisito para
revisar el guard inicial.

**Recomendación:** C1 como paso mínimo, ligado a H para servicios, y evaluar C3
separadamente para reducir capacidad de firma en consumidores. Proponer una
audiencia de recurso específica por producto/entorno, sin wildcard; nombres y
registro exactos por firmar. No promover `smart3ai-portfolio` a audiencia universal.
El receptor debe comprobar que es destinatario y que el principal llamador está
autorizado para ese cliente/contexto. La allowlist del diff C solo comprueba
coherencia interna del token con el registro; no realiza ese binding final.

**Impactos:** AdminApps valida entrada, contexto firmado de challenge, emisión,
introspection y refresh; input inválido no se convierte silenciosamente al
portfolio por coerción/default. ISO Smart separa cookie local y bearer central,
incluidos issuer, audience, tipo de ID y subject; MedSupplier separa JWT local y
central y adapta refresh/UI. Evitar configurar un issuer global y romper todos
los tokens locales o aceptarlos como centrales. No sincronizar usuario por email
ni organización por nombre para resolver colisiones de autoridad.

**Retrocompatibilidad/rollout:** registro vacío deniega todos los nuevos login
con C; tokens sin aud/issuer y clientes anteriores pueden perder acceso. Preparar
inventario por entorno con identificadores públicos, algoritmo, origen de claves
y rotación (sin valores secretos), validadores, emisión y corte/reautenticación.
No proponer periodo permisivo sin audiencia. Registro en configuración no exige
DDL; rotación/IdP/cambio de algoritmo son intervenciones separadas autorizadas.

**Aceptación +:** token central para cada receptor y token local para su familia
correcta; string/lista aud válidas según contrato; challenge mantiene binding.
**Aceptación −:** firma, algoritmo, tipo, issuer, aud o client incorrectos/ausentes;
audiencia de otro producto; cliente registrado pero servicio no autorizado;
registro malformado; aud mixta permitida+ajena; replay de challenge entre clientes;
refresh previo al corte y token local presentado como central.

**Autoridad requerida:** identidad/seguridad, dueños de API de los tres productos
y operación IdP/claves cuando aplique. Aprobar inventario por entorno, familias,
coexistencia/corte y alcance de cada principal con H.

## D. Scopes y autorización efectiva — prioridad 3

**Problema demostrado:** NF04/NF05, AA2. Todos reciben write. El permiso efectivo
en consumidores no se deriva de ese scope por sí solo (IS3/MS3), por lo que el
fallo no demuestra una escritura HTTP indebida ya realizada.

**Alternativas:** (D1) intersección rol de membresía × scopes entitlement ×
producto/cliente registrado; (D2) capacidades por acción/objeto emitidas por
servicio de políticas central; (D3) solo roles locales y entitlement comercial.
D3 mantiene divergencia y no cierra el contrato de scopes.

**Recomendación:** D1 como mínimo con enforcement de dominio adicional. Matriz
candidata: viewer/auditor únicamente read; org_admin read/write dentro de su
tenant y producto; iso_manager/user solo capacidades mapeadas explícitamente
por producto; rol desconocido sin permisos tenant. Read también requiere
entitlement vigente; scopes vacíos = ninguno, nunca todos. Scopes identidad
openid/profile/email no autorizan datos tenant. Definir namespace por producto
en contrato versionado si se abandona `tenant:*`; no renombrarlo unilateralmente.

**Impactos:** AdminApps calcula scopes tanto en access como refresh y revalida
efectividad vía B. ISO Smart agrega intersección al permiso backend conservando
roles QMS, aislamiento y objeto; revisar también RoleBasedPermission, que usa
jerarquía ordinal en vez de la matriz explícita. MedSupplier conserva side,
account y visibilidad; un scope global write nunca convierte customer en supplier
ni viewer en editor. Auditar fallback org_admin/iso_manager→supplier_admin y
superuser en contexto MedSupplier; no asumir equivalencia comercial.

**Retrocompatibilidad/rollout:** configuración ausente produce cero scopes
tenant; entitlements actuales con lista vacía pueden perder acceso. Faltan
inventario y aprobación de mappings, no completar listas automáticamente.
Validar tipos/listas/nombres del policy config para evitar errores o concesiones
accidentales. Coordinar emisión y enforcement por producto; no habilitar solo
UI. Sin DDL para intersección, pero backfill de scopes/datos requiere gate separado.

**Aceptación +:** rol permitido + producto/tenant correctos + scope explícito +
permiso del objeto permite operación exacta. **Aceptación −:** viewer/auditor
write, desconocido, scopes vacíos o malformados, producto suspendido, tenant ajeno,
scope de otro producto, customer con write contra datos privados, permisos
revocados y refresh obsoleto. Verificar rutas REST reales y acciones personalizadas.

**Autoridad requerida:** seguridad/arquitectura, propietarios de permisos de
AdminApps, ISO Smart y MedSupplier, con responsables de dominio QMS y supplier/
customer. Billing no puede conceder por sí solo una capacidad de usuario.

## E. Trial y suscripción — prioridad 5

**Problema demostrado:** NF07 y contradicción CT1/CT2. Runtime y operación actual
eximen trial de suscripción. No es facultad de esta campaña elegir una política
comercial ni clasificar automáticamente los trials existentes como indebidos.

**Alternativas:** (E1) trial comercial explícito sin suscripción, con elegibilidad,
duración y límites propios; (E2) todo producto con billing, incluso trial, requiere
suscripción efectiva trial/active; (E3) grandfathering temporal documentado con
cohortes, fecha de fin y autoridad verificables, si comercial lo necesita.

**Recomendación propuesta:** E2 para simplificar una única autoridad de vigencia
comercial y alinear CT1; requiere aprobación comercial/facturación y reconciliar
CT2 antes de implementación. E1 es una alternativa válida si se versiona y acota;
la aserción NF07 sería entonces sustituida por criterios de trial explícitos,
preservando evidencia anterior. No se declara E2 elegida por conveniencia técnica.

**Impactos:** AdminApps cambia decisión runtime, create/update, toggle, admin y
mensajes/UI. ISO Smart puede denegar al login por billing_not_configured; debe
revalidar sesiones activas y mostrar transición/recuperación comercial.
MedSupplier debe llevar la validación al login/operaciones y comunicar el mismo
estado, además de integration status. Mantener independencia entre productos.

**Retrocompatibilidad/rollout:** E2 cortaría trials sin suscripción y también los
ligados a suscripción bloqueada antes tolerados por la excepción. Inventariar
impacto y aprobar tratamiento antes del corte. Los dos diffs no agregan DDL;
crear/asociar suscripciones o cambiar datos sí requiere intervención autorizada.
Subscription.is_active (AA4:144) evalúa solo estado active/trial, no sus fechas
trial_ends_at/current_period_end. Comercial debe resolver si esas fechas son
informativas o controles de acceso y qué proceso cambia el estado; P05/P06 no
resuelven esa discrepancia adicional. No atribuirles expiración automática.
Preparar una regla compartida para todos los puntos de escritura y evaluación;
resolver `subscription:null` como borrado explícito frente a campo omitido y
reevaluar fallback a organización. No cambiar facturas históricas.

**Aceptación + (E2):** billing deshabilitado funciona sin suscripción; trial/active
con suscripción efectiva vigente funciona; entitlement específico tiene prioridad
sobre fallback organizacional válido. **Aceptación −:** trial sin suscripción,
past_due/suspended/cancelled/expired, PATCH que borra vínculo, toggle trial/admin
que elude la regla. No confundir plan/default_plan con suscripción. Bajo E1,
probar fin/elegibilidad/límites de trial y no extensión por fallback local.

**Autoridad requerida:** titular comercial y billing con facultad verificable;
dueños de ambos productos aceptan impacto, seguridad verifica que la excepción
aprobada no amplía autorización de identidad/tenant/objeto; datos para transición.

## F. Vigencia temporal — prioridad 5

**Problema demostrado:** NF08, AA3. starts_at existe (no nullable en el modelo
actual, default timezone.now), pero no se consulta para acceso. Ends_at hoy es
inclusivo: solo rechaza `now > ends_at`. CT1 no define inicio.

**Alternativas:** (F1) inicio inclusivo y conservar fin inclusivo; (F2) intervalo
UTC aware `[starts_at, ends_at)` con fin exclusivo; (F3) starts_at solo informativo,
con activación mediante un estado/evento explícito.

**Recomendación:** F2 como contrato temporal único y verificable, con `ends_at`
null = sin fin temporal (no autorización perpetua). Inicio obligatorio; no
ampliar schema a null por el guard defensivo del diff. Rangos vacíos/invertidos
rechazados. El diff F solo añade inicio y deja fin inclusivo: **requiere revisión**
si se aprueba F2. Usar un único evaluated_at por decisión para evitar respuestas
contradictorias al cruzar una frontera durante serialización.

**Impactos:** AdminApps debe alinear is_active, reason, payload/validación y UI de
programación. ISO Smart consume la nueva denegación y no reutiliza allow fuera
de ventana; MedSupplier hace lo mismo en todas las operaciones protegidas y
renueva cachés/UX. Ninguno debe activar localmente por reloj del navegador.

**Retrocompatibilidad/rollout:** contratos con starts_at futuro dejarían de dar
acceso; igualdad con ends_at cambia bajo F2. Aprobar cohortes/fecha efectiva,
normalizar timezone y verificar datos mediante revisión futura autorizada. No
requiere columna nueva; corrección/backfill de fechas y constraints persistentes
son intervenciones separadas. No desplazar fechas automáticamente para evitar deny.

**Aceptación +:** instante exacto de inicio y dentro de ventana; ends_at null;
zona horaria equivalente produce mismo instante. **Aceptación −:** antes del
inicio, instante exacto de fin bajo F2 y después; rangos inválidos/naive, caché
que sobrevive al fin, trial aún no iniciado y cambios retroactivos no autorizados.

**Autoridad requerida:** comercial/productos para fecha efectiva y derechos
existentes; arquitectura/seguridad/QA para reloj, errores y límites de caché.

## G. Suscripción, pagador y beneficiarios — prioridad 5

**Problema demostrado:** NF09. Organization.subscription es FK no única;
Subscription no expresa dueño tenant. El test crea relaciones en memoria:
demuestra ausencia de la política candidata, no que toda compartición sea ilícita.

**Alternativas:** (G1) dueño exclusivo por tenant; (G2) dueño/pagador explícito y
beneficiarios autorizados por producto/vigencia; (G3) entidad billing account
independiente con tenants beneficiarios. G1 puede romper compras de grupo; G3
requiere mayor rediseño de datos e integración financiera.

**Recomendación:** G2 como contrato mínimo, con opción de materializarlo mediante
G3 si comercial confirma ese dominio. Por defecto no compartir sin relación
explícita; nombre, plan ni cualquier referencia previa no prueban ownership.
El diff G es texto candidato; no autoriza añadir FK ni imponer exclusividad.

**Impactos:** AdminApps necesita resolver dueño/beneficiario en todos los caminos
de escritura y runtime; preservar historial de billing. ISO Smart acepta deny
versionado por vínculo no autorizado sin crear billing paralelo. MedSupplier
también, y su SupplierAccount/customer account **no equivale** a beneficiario de
suscripción central: no inferirlo por esa relación operativa.

**Retrocompatibilidad/rollout:** inventariar ambas FK (Organization y Entitlement),
comparticiones, huérfanos y conflictos; comercial adjudica cada cohorte. Diseñar
expand/contract y backfill verificable con cuarentena/deny de ambiguos; ninguna
reasignación automática. Requiere DB, datos y contrato; no hay migración propuesta
ni presupuesto de locks/volumen conocido. No incorporar financial por dependencia
supuestamente implícita.

**Aceptación +:** dueño y beneficiario explícito vigente del producto; compra
compartida aprobada mantiene acceso exacto. **Aceptación −:** suscripción ajena no
autorizada, beneficiario revocado/expirado, otro producto, create/PATCH/toggle/admin
que altera asociación, restauración que resucita compartición revocada. Facturas
y trazabilidad se preservan tras migración/rollback.

**Autoridad requerida:** comercial/billing (pagador y derechos), data owner y
arquitectura (modelo), seguridad (aislamiento), DBA/cambio para ejecución futura,
ambos productos para compatibilidad.

## H. Principal y permisos de API keys — prioridad 2 para binding; 5 para resto

**Problema demostrado:** AA1/AA5: autenticar una key identifica servicio por nombre
y lifecycle, pero no verifica operación/producto/tenant. No hay aserción H en
los nueve fallos. Fallback configurado puede devolver nombre sin fila persistida;
no basta con `credential_id` si la key legacy carece de él.

**Alternativas:** (H1) principal inmutable registrado + allowlist por operación,
cliente, producto y tenant; (H2) credenciales separadas por tenant/producto con
política equivalente; (H3) identidad de workload/mTLS/tokens de servicio mediante
IdP con scopes equivalentes. El nombre mutable de una key no es alternativa de
autorización confiable.

**Recomendación:** H1 con menor privilegio; H2 si aislamiento operativo lo exige,
H3 como intervención posterior. Cada credencial apunta a principal estable,
incluidas legacy y configuración mediante registro explícito. Registro ausente,
dimensión desconocida o excepción vencida deniega. No hay wildcard implícito;
servicios centrales multitenant requieren lista/excepción auditada con expiración.

**Impactos:** AdminApps conserva autenticación/lifecycle y añade autorización
previa a datos/operación, incluido introspection ligado al token C. ISO Smart
declara operaciones producto/usuario/QMS y tenant events por dirección de flujo;
no reutilizar automáticamente autoridad del ingress para consultar identidad.
MedSupplier declara producto/tenant/operación y no hereda ISO_SMART por copiar
cliente. Ambos deben manejar 401/403/503 sin fallback positivo ni exponer keys.

**Retrocompatibilidad/rollout:** keys globales y credenciales de settings sin
registro perderían acceso. Inventario futuro sin plaintext; mapear principal y
credenciales, preparar registro y autorización, evaluar diferencias sin concesión
adicional, realizar corte coordinado. Registro estático podría evitar DDL pero
exige configuración gobernada; principal/relaciones durables y lifecycle requieren
diseño DB. integration.0006 no crea por sí misma permisos dimensionales. Rotación
y distribución son autorizaciones separadas; no se ejecutan aquí.

**Aceptación +:** key activa registrada autoriza exactamente servicio, operación,
cliente, producto y tenant previstos. **Aceptación −:** misma key contra tenant/
producto/operación ajenos, cliente declarado falso, nombre renombrado, registro
ausente, excepción vencida, key revocada/rotada y fallback que la resucita; DB
error en lookup, last_used o auditoría. Para eventos de seguridad obligatorios,
fallo de auditoría debe impedir acceso, política por ratificar sin exponer detalles.

**Autoridad requerida:** seguridad/identidad y data owners de tenants/productos;
operación de credenciales y responsables de servicios en los tres repositorios;
DBA/IdP según alternativa. Aprobar excepción central individualmente.
