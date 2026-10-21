# REC-SSO-03D — contrato local de autorización v1

Fecha del mandato: 2026-10-15. Actualización: 2026-10-16, America/Costa_Rica.
Estado: implementación parcial; NO activar. A/C/H/B y E/F/G conservan su adjudicación.

## Contrato

`EffectiveAccess = Identity ∩ Client ∩ Product ∩ Tenant ∩ Session ∩ Role ∩ Scopes ∩ Entitlements ∩ ResourcePolicy`.
La identidad no es un grant. `active: true` en introspección solo acredita autenticación B.
La API requiere además `authorization.state == active`, contrato exacto `rec-sso-03d-v1`,
principal `user` y todos los bindings concordantes con la prueba CENTRAL validada en vivo.
La evidencia se devuelve por el canal de introspección existente autenticado por cliente;
no es un JWT nuevo, no se acepta del request y no se guarda en JWT LOCAL ni cachés.

Formato exacto: `PRODUCT:app.model:operation`, por ejemplo
`ISO_SMART:resources.resource:read` o `MEDSUPPLIER:medsupplier.suppliercontact:create`.
Los identificadores son case-sensitive. El catálogo Python y `catalog.json` son enumeraciones
cerradas de recursos/acciones registrados, con 187 scopes ISO_SMART y 292 MEDSUPPLIER.
No hay scope genérico write, comodines, herencia entre productos ni equivalencia de nombres.
Read/create/update/delete/approve/export solo figuran donde existe una capacidad HTTP real.
No se inventa un scope de administración: el control plane AdminApps sigue pendiente de D.
La presencia de un scope en el catálogo NO implica que el handler esté habilitado en v1.
`action_enabled` restringe la ejecución a operaciones cuya política se revisó.

Campos de `authorization`: contract, state(active|denied), principal_type(user), sub(UUID),
tenant_id(UUID central), client_id, product, role, sid(UUID B), sg(entero), av(entero), scopes(lista).
Los consumidores contrastan bindings con la introspección validada por CENTRAL y con el
perfil local vigente; `organization_id` local proviene exclusivamente del token LOCAL
vinculado a esa prueba y al UUID external_id. Un ID numérico no sustituye al UUID central.

Scopes ausentes/vacíos/desconocidos/duplicados/de otro producto: DENY. Versión, estado,
principal, rol o binding desconocidos/inconsistentes: DENY. Parámetros role/scopes/product/
tenant/client: no conceden acceso. organization/organization_id deben concordar con la sesión.
GET puede tener efectos; la decisión usa el action real del servidor, nunca solo el verbo HTTP.

## Autoridad y RBAC

AdminApps deriva grants dentro del mismo fence durable de B que valida sesión, cliente,
tenant, identidad, MFA, membresía y generación. Intersecta `entitlement.scopes` con operaciones
del rol actual de UserOrganization. El rol del usuario global no sustituye a la membresía.
No crea filas ni amplía grants a partir de datos del consumidor.

| Membresía central | ISO_SMART | MEDSUPPLIER |
|---|---|---|
| viewer / auditor | read | read |
| user | read, create, update | read, create, update |
| iso_manager | read, create, update | read |
| org_admin | read, create, update, delete | read, create, update, delete |
| admin / superadmin / desconocido | ninguno | ninguno |

Fuente: significados de User.ROLE_CHOICES, UserOrganization y CanEdit de los consumidores.
Estas son cotas técnicas conservadoras, no nuevos derechos comerciales. Las operaciones
approve/export/admin quedan sin concesión RBAC en v1 hasta revisar su política específica.
Un org_admin solo puede ejercer el scope exacto ya concedido al producto/tenant y habilitado
por la política del recurso. MEDSUPPLIER exige además MedSupplierUserScope vigente.
No se mezclan IntegrationAPIKey/cliente y usuario; una API key sola no recibe grants humanos.
Grupos/permisos Django no amplían esta tabla; cambios siguen invalidando B.

## Entitlements y ambigüedad comercial

`access_allowed` debe ser true, starts_at conocido y no futuro, ends_at no alcanzado, producto
y organización activos. Billing activo requiere entitlement active y suscripción effective
active en el vínculo canónico organization.subscription, dentro de los límites temporales
presentes. Un override distinto del vínculo canónico se retiene. Trials facturados, incluso
con suscripción trial, se retienen hasta adjudicar condiciones. No se altera el access_allowed
heredado ni se da por cerrado ninguno de los tres HIGH comerciales de B.

Los módulos legacy (document_room/rfq/quality, etc.) carecen de mapeo versionado a recursos D.
Un modules_enabled ausente, no lista o no vacío produce DENY funcional. En este contrato,
la lista explícita vacía significa que las capacidades se declaran exclusivamente por scopes
exactos. No migrar derechos comerciales a esta forma automáticamente. Quotas/planes y suscripción
compartida entre organizaciones requieren reconciliación; no se afirma cierre global.

## Consumidores y objetos

OrganizationScopedViewSetMixin ejecuta el gate D además de sus permisos existentes, incluso
cuando la vista declara permission_classes. Conserva queryset de tenant y comprueba objeto
con lookup directo/anidado. Error de objeto ajeno: 404 genérico; error de operación: 403.
Ausencia de autoridad: 503/401 según contrato A/B; no hay fallback local.

Solo `resources.resource` y `medsupplier.suppliercontact` admiten CRUD revisado sujeto a rol y
scope. Los serializers fuerzan tenant desde contexto, impiden reparenting y relacionar usuarios
sin membresía local activa; relaciones empresariales deben pertenecer al tenant y cuenta
permitidos. Campos sensibles y mutaciones anidadas sin política: DENY antes de persistencia.
La carga documentation de Resource se retiene hasta verificar cuota de almacenamiento.
El contacto conserva las auditorías existentes. Resource no recibe un outbox nuevo; transacción,
RLS y auditoría empresarial general siguen pendientes.

Lecturas estándar list/retrieve quedan sujetas a política y al queryset vigente. Acciones
adicionales habilitadas: by_type(Resource), maintenance_due(Infrastructure), gaps/by_user
(Competence), upcoming(Training), pending(Communication), stats(Document), dashboard_stats
(Measurement). Las respuestas compuestas (findings/version/traceability/AI), aprobaciones,
exports, bulk y escrituras restantes se retienen; no deben contarse como ALLOW verificado.
Assistant memory/conversations/config se retienen por falta de política de propietario.
Los handlers que NO heredan el mixin NO adquieren automáticamente esta protección; el CSV
marca estas brechas críticas, incluyendo core.export_data, leadership y foundation.

MedSupplier elimina el fallback profile→supplier_admin y el bypass superuser. Las asignaciones
mixtas/inválidas o cuentas de otra organización deniegan. Supplier con cuenta explícita conserva
ese límite; customer conserva cuenta y visibilidad compartida. Supplier viewer no obtiene
visibilidad privada. EvidencePackageEntry usa el tenant del package y también limita cuentas.
Los cuatro endpoints funcionales agregados requieren todos los scopes read correspondientes;
el cockpit exige además permiso financiero y filtra por cuentas. Relación comercial no equivale
a acceso ilimitado. Scopes locales solo restringen grants centrales. Cambios locales se leen
en cada request; invalidación ABA central de esas asignaciones locales está NOT_EVIDENCED.

## Errores, efectos y compatibilidad

No se devuelven nombres/contenido de objetos inaccesibles. Querysets excluyen objetos ajenos;
la permission chain comprueba el tenant de nuevo. Listas se prueban con selección ORM simulada:
no se afirma RLS ni consultas SQL reales. Serializers de respuesta y relaciones persistidas
corruptas necesitan pruebas DB adicionales antes de activar.
No se modifica RSA, issuer, audience, kid, familias CENTRAL/LOCAL, TTL 300 s, MFA ni transporte.
ISO conserva HttpOnly/CSRF; MedSupplier conserva Bearer/localStorage. No hay refresh central
silencioso, workers, cambios de configuración activa ni claves productivas.
B sigue exigiendo sus migraciones 0008/0009/0010, fence y provisión externos; no se aplicaron.
