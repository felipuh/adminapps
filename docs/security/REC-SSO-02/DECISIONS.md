# REC-SSO-02 — decisiones humanas A–H

2026-10-14, America/Costa_Rica. **Todas PENDING_HUMAN_APPROVAL**. Las recomendaciones
no adjudican autoridad ni sustituyen decisiones comerciales. Los diffs en
[proposals](proposals/manifest.json) están **NO APLICADOS**. Son candidatos de revisión,
no un paquete listo para ejecutar. Se verificó sintaxis Python en memoria; su runtime
es **NOT_TESTED**. Cada diff parte del archivo actual indicado por SHA-256 en el
manifiesto; no concatenarlos sin resolver su composición y añadir pruebas.

Se mantienen `S3-IMP-01 = BLOCKED_PENDING_AUTHORITY`,
`S3_DECISION_02A_NOT_CLOSED`, `PHASE31_5 = EXECUTION_HELD` y REC-2FA-04.

## A. Legacy y 2FA — técnica y transición de producto

**Hecho:** `validate_credentials` devuelve `valid=true` tras contraseña. Los backends
de ISO Smart y MedSupplier consumen ese booleano para sincronizar y autenticar.
No transportan un desafío ni completan el segundo factor en ese contrato.

**Recomendación:** aprobar primero denegación explícita para cuentas con 2FA
(`valid=false`, HTTP 403, `second_factor_required`) y migrar ambos consumidores al
flujo SSO de desafío/verificación ya existente. Alternativa: adaptar el contrato
legacy mediante versión nueva y negociación explícita. Nunca convertir un desafío
en autenticación completa ni aceptar un flag de bypass del consumidor.

[Diff A](proposals/A-legacy-deny-2fa.patch) propone solo la denegación. Aunque el
consumidor entiende `valid=false`, cambiaría la disponibilidad de login para esas
cuentas: falta aprobación de transición. No aplica OTP nuevo ni cambia el canal,
el consumo irreversible o los códigos backup de REC-2FA-04.

**Gate:** responsables de identidad/seguridad y ambos productos deben aprobar
semántica de error, UX, recuperación de cuenta, calendario de deprecación y pruebas
sin fallback local. Aceptación futura: TOTP y backup correctos, error, expiración,
replay y challenge sin sesión local; verificar que ningún backend alternativo
permita eludir la denegación. La validación local sigue mostrando FAIL.

## B. Revocación y frescura — técnica

**Aplicado:** cada introspection relee usuario activo y membresía activa en la
organización activa del token. Este control no cambia el formato de respuesta.

**Pendiente:** claims de rol/membresías, refresh, sesiones locales, cachés y tokens
verificados sin introspection. [Diff B](proposals/B-reject-stale-role.patch) propone
rechazar el token si el rol actual difiere del emitido; alternativa: retornar rol
vivo y definir qué ocurre con los scopes. Aprobar una sola semántica, común a los
dos consumidores. Una reactivación o un cambio de rol de ida y vuelta puede volver
a validar tokens antiguos: revocación permanente requiere versión de sesión o
identidad, corte temporal o denylist; no se introduce ese esquema aquí.

**Propuesta de frescura:** para operaciones sensibles, consulta autoritativa en
cada operación y ningún fallback positivo ante error; documentar un máximo de
obsolescencia para UI/lecturas y la invalidación de cachés. Hoy existen snapshots,
access de 8 h, refresh de 7 días y cachés de consumidor con default 300 s. Estos
valores no prueban un SLA de revocación. El refresh estándar no reconstruye los
claims de acceso del producto ni define revocación global.

**Gate:** seguridad/arquitectura y propietarios de sesiones de ambos productos:
SLA, reautenticación, logout, rotación, refresh tras revocación, comportamiento
ante indisponibilidad y carreras entre lectura y uso. No se promete atomicidad
entre introspection y una operación del consumidor.

## C. Issuer, audience y clientes — técnica

**Aplicado solo en introspection:** issuer igual al `SMART3AI_SSO_ISSUER` que ya
utiliza el emisor. No se cambia `SIMPLE_JWT`, los consumidores ni el issuer emitido.

[Diff C](proposals/C-register-client-audience.patch) propone registro de clientes
con audiencias permitidas, denegación por defecto y validación en login,
verificación 2FA e introspection. Un ejemplo de forma es
`SMART3AI_SSO_CLIENTS[client_id] = {"audiences": [audiencia_aprobada]}`;
**no hay valores de despliegue aprobados**. El diff permite solo subconjuntos
registrados, pero el registro de un cliente público no autentica al solicitante.
Las credenciales de servicio y su autorización corresponden a H.

**Gate:** inventariar emisores, claves, algoritmos, client IDs y audiencias por
entorno, incluidos los JWT locales de cada producto y `smart3ai-portfolio`.
Elegir política para tokens sin claims, coexistencia y periodo de transición.
Revisar firma simétrica compartida frente a emisor asimétrico/rotación con `kid`;
ninguno se configura aquí. Probar por separado firma, issuer, audience, cliente,
tipo de token, refresh y desafío. No aceptar la audiencia declarada por el
solicitante como prueba de autorización. SSO-03 permanece abierto globalmente.

## D. Scopes según rol y entitlement — técnica con validación de producto

**Hecho:** access y refresh incluyen `tenant:write` para todos los roles. El modelo
de usuario excluye viewer/auditor de edición, pero no existe una matriz SSO completa
aprobada para roles de membresía, scopes de producto y administración global.

[Diff D](proposals/D-role-product-scopes.patch) propone intersección entre permisos
del rol de membresía y scopes del entitlement permitido del producto registrado
para el cliente. Sin política/entitlement, no concede scopes tenant. Conserva los
scopes de identidad. Las configuraciones son nuevas y requieren contrato/versionado.

**Matriz candidata:** viewer/auditor solo lectura; org_admin escritura únicamente
en su organización y producto habilitado; iso_manager/user según capacidad
explícita aprobada; desconocido sin permisos tenant. Admin/superadmin global no
implican acceso multitenant dentro de un token tenant. Decidir si read también
requiere entitlement, si scopes vacíos significan ninguno y si los nombres deben
calificarse por producto. No inferir permisos por texto del rol ni por billing.

**Gate:** propietarios de permisos y ambos productos aprueban matriz, scopes,
casos negativos, cache/refresh y comportamiento para productos suspendidos. No
se demostró escritura E2E basada exclusivamente en el scope defectuoso.

## E. Trial y suscripciones — comercial, con implementación técnica posterior

El contrato neutral exige suscripción efectiva si hay billing. El modelo, las
operaciones documentadas y pruebas existentes permiten trial sin suscripción.
Es una contradicción contractual, no una decisión que seguridad pueda adjudicar.

Alternativas: trial comercial explícito sin suscripción, acotado por vigencia y
producto, o toda prueba requiere suscripción en estado trial/active. Se recomienda
resolver y versionar una única regla, con aprobación comercial y facturación.
[Diff de modelo](proposals/E-trial-subscription-model.patch) y
[diff de serializers](proposals/E-trial-subscription-serializers.patch) ilustran
la segunda opción. Faltan pruebas de toggles/admin, partial updates, transición
de trials existentes y mensajes consistentes; **no son una remediación aplicada**.

**Gate comercial:** elegibilidad, duración, renovación, gracia, impagos, cancelación
y derechos adquiridos. **Gate técnico:** todos los puntos de escritura y cálculo
de acceso usan la misma regla; ningún fallback comercial amplía permisos.

## F. Inicio temporal — comercial para la fecha efectiva; técnica para el reloj

Hoy `starts_at` no participa en `is_active` ni en `access_denial_reason`; el contrato
neutral enumera `ends_at` pero no define inicio. [Diff F](proposals/F-entitlement-start.patch)
propone impedir acceso antes de `starts_at` y razón `entitlement_not_started`.

**Propuesta:** UTC aware, inicio inclusivo; determinar explícitamente si fin es
exclusivo (el código actual permite igualdad). Definir `null`, rangos inválidos,
trial y cambios retroactivos. El diff no cambia la frontera de fin ni adjudica
esas opciones. Los consumidores deben aceptar la razón nueva antes de activarla.

**Gates:** comercial aprueba activación programada y tratamiento de contratos
existentes; arquitectura/QA prueban fronteras exactas, zona horaria y caché.

## G. Suscripción y organización — comercial/arquitectura de datos

`Organization.subscription` es una FK no única; Subscription no tiene owner tenant
directo. Ni el serializer ni la propiedad impiden que una suscripción referenciada
por B se use en A. Esto prueba ausencia del guardrail candidato; no una escritura
HTTP no autorizada ni que toda compartición actual sea inválida.

[Diff contractual G](proposals/G-subscription-binding-contract.patch) propone dueño
explícito y compartición solo mediante beneficiarios autorizados. La alternativa
es cuenta de facturación compartida como entidad de dominio. No se inventa una
FK ni se usa nombre/plan como prueba de pertenencia.

**Gates:** comercial define pagador y beneficiarios; datos/arquitectura inventarían
referencias y conflictos, definen migración y rollback preservando facturas;
seguridad verifica create/update/toggle/admin/runtime. No reasignar datos ni
reparar automáticamente supuestas asociaciones equivocadas.

## H. API keys de integración — técnica y autorización operativa

`require_api_key` identifica un servicio, pero no limita producto, tenant u
operación. El nombre mutable de la key y un `client_id` declarado no prueban
autoridad. Los fallos DB del decorador quedan sanitizados **solo al entrar por
introspection**, no en todos los endpoints de integración.

[Diff contractual H](proposals/H-integration-key-scope-contract.patch) propone
principal estable ligado a credential ID, con operaciones/clientes/productos/
tenants explícitos, denegación por defecto y excepciones centrales auditadas.
También debe cubrir credenciales de configuración, rotación y revocación.

**Gate:** inventario local autorizado de consumidores y necesidades, aprobación
de las autoridades de identidad y datos; pruebas con una key correcta para A que
intenta B, producto ajeno y operación ajena. No generar, rotar ni distribuir keys,
ni cambiar grants/RLS. El nombre de servicio no se convierte silenciosamente en
una nueva política global.

## Autoridad y aprobación

Se requieren decisiones firmadas por las personas con autoridad verificable de
cada dominio, con fecha efectiva, alcance, criterios de aceptación y rollback.
Este documento identifica funciones; **no designa personas ni presume facultades**.
Las propuestas financieras preexistentes mantienen sus propios gates. Aprobar
una decisión REC-SSO-02 no libera S3-IMP-01 ni PHASE31_5.
