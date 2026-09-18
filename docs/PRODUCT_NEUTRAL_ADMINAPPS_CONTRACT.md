# Product-Neutral AdminApps Contract

## Canonical tenant provisioning identity (tenant events v1)

`apps.organizations.Organization.id` is the canonical, immutable global tenant
UUID. ISO Smart stores it in `TenantProjection.adminapps_tenant_id`; the local
`TenantProjection.id` and QMS `Organization.id` are separate IDs. One tenant may
have many QMS organizations. AdminApps owns provisioning and global status.

The active organization creation API commits the customer, settings and
`TenantIntegrationOutbox` event together. Its initial `source_version` is 1;
each changed name or status emits exactly one later version. The event envelope
uses `tenant.provisioned`, `tenant.updated` or `tenant.suspended`, schema version
1, `source=adminapps`, UUID `event_id`/`trace_id`/tenant ID, timezone-aware
`occurred_at`, optional `actor_id`, and `payload.display_name`, `payload.adminapps_status` and
`payload.lifecycle_status`. `aggregate_type=tenant` and `aggregate_id` equals
the canonical UUID. `correlation_id` is optional. Display name is a mutable
snapshot, never an identifier. Status maps `trial|active → active` and
`inactive|suspended → suspended`; an ISO Smart operation still needs a fresh
product entitlement check. Deactivation suspends access but preserves IDs and
historical QMS records. Hard deletion is unavailable until a separate governed
deprovision operation exists.

The outbox dispatcher posts the unchanged envelope over HTTPS to ISO Smart's
`/api/integration/adminapps/tenant-events/` with `X-API-Key`. The key is
configured as `ISO_SMART_TENANT_EVENT_KEY` at the producer and its SHA-256 hash
as `ADMINAPPS_TENANT_EVENT_KEY_SHA256` at the consumer; neither is in an event
or log. Retry preserves event ID and payload. ISO Smart authenticates the
service before validating the envelope and records an ingress receipt for every
valid authenticated event, including replay and processing status.

Fecha: 2026-06-29

## Objetivo

Definir el contrato producto-neutral de AdminApps como centro administrativo, comercial, financiero y de acceso para el ecosistema Smart3AI.

AdminApps debe poder gobernar productos como `ISO_SMART`, `MEDSUPPLIER` y futuros productos sin quedar amarrado a un unico producto ISO.

## Modelo canonico

| Responsabilidad | Modelo | Estado | Observacion |
| --- | --- | --- | --- |
| Catalogo de productos/sistemas | `products.ProductSystem` | Activo | Fuente de verdad producto-neutral para `ISO_SMART`, `MEDSUPPLIER` y futuros productos. |
| Habilitacion por organizacion | `products.OrganizationProductEntitlement` | Activo | Controla enabled/status/scopes/modules y relacion con plan/suscripcion. |
| Cliente/organizacion | `organizations.Organization` | Activo | Mantiene estado operativo de la organizacion. |
| Plan comercial | `subscriptions.Plan` | Activo | Define precio, ciclo, limites y modulos incluidos. |
| Suscripcion | `subscriptions.Subscription` | Activo | Controla estado financiero: `trial`, `active`, `past_due`, `cancelled`, `expired`, `suspended`. |
| Billing/catalogo fiscal | `billing.ProductCatalog` | Activo | Catalogo de facturacion/fiscal. Relacion formal: complementa a `ProductSystem`, no lo reemplaza. |
| Usuarios | `users.User` | Activo | Identidad local/AdminApps. |
| Membresias | `users.UserOrganization` | Activo | Usuario pertenece a organizacion con rol/scopes operativos. |

## Relacion ProductSystem vs ProductCatalog

`ProductSystem` es el catalogo de producto para acceso, entitlements, integracion y gobierno SaaS.

`ProductCatalog` es el catalogo de facturacion/fiscal para precios, facturacion electronica y revenue operations.

Relacion formal:

1. `ProductSystem.code` identifica el producto administrable, por ejemplo `MEDSUPPLIER`.
2. `ProductCatalog.code` identifica el producto facturable.
3. La asociacion entre ambos puede documentarse por codigo compartido o por metadata mientras no exista una foreign key dedicada.
4. `OrganizationProductEntitlement` debe usar `ProductSystem`.
5. Facturacion electronica y precios deben usar `ProductCatalog`.

No se unifican en esta etapa para evitar migraciones de alto riesgo y preservar compatibilidad con billing existente.

## Productos registrados

La migracion `products.0002_productsystem_organizationproductentitlement` registra:

| Codigo | Nombre | Estado | Billing |
| --- | --- | --- | --- |
| `ISO_SMART` | ISO Smart | active | enabled |
| `MEDSUPPLIER` | ISO Smart MedSupplier | active | enabled |

## Reglas de acceso producto-neutral

Una organizacion puede acceder a un producto solo si:

1. La organizacion esta activa.
2. El producto existe y esta `active` o `beta`.
3. Existe `OrganizationProductEntitlement` para la organizacion y el producto.
4. El entitlement esta `enabled`.
5. El entitlement esta en estado `active` o `trial`.
6. El entitlement no esta vencido por `ends_at`.
7. Si `ProductSystem.billing_enabled=True`, existe suscripcion efectiva.
8. La suscripcion efectiva esta activa: `active` o `trial`.

La suscripcion efectiva es:

1. `OrganizationProductEntitlement.subscription`, si existe.
2. Si no existe, `Organization.subscription`.

## Razones de denegacion

| Razon | Significado |
| --- | --- |
| `organization_inactive` | La organizacion no esta activa. |
| `product_not_enabled` | No existe entitlement para el producto. |
| `entitlement_disabled` | El entitlement existe pero esta deshabilitado. |
| `entitlement_inactive` | El entitlement no esta en estado activo/trial. |
| `entitlement_expired` | El entitlement vencio por fecha. |
| `product_unavailable` | El producto no esta active/beta. |
| `billing_not_configured` | Billing requerido pero no hay suscripcion efectiva. |
| `billing_blocked` | La suscripcion efectiva existe pero no permite acceso. |
| `ok` | Acceso permitido. |

## API interna de validacion

### Validar acceso a producto

```http
GET /api/integration/organizations/{organization_id}/products/{product_code}/validate/
X-API-Key: <internal-api-key>
```

Respuesta permitida:

```json
{
  "allowed": true,
  "organization_id": "<uuid>",
  "organization_status": "active",
  "product": {
    "code": "MEDSUPPLIER",
    "enabled": true,
    "status": "active",
    "is_active": true,
    "access_allowed": true,
    "access_denial_reason": "ok",
    "billing_status": "active"
  },
  "reason": "ok"
}
```

Respuesta denegada por billing:

```json
{
  "allowed": false,
  "organization_id": "<uuid>",
  "organization_status": "active",
  "product": {
    "code": "MEDSUPPLIER",
    "access_allowed": false,
    "access_denial_reason": "billing_blocked",
    "billing_status": "past_due"
  },
  "reason": "billing_blocked"
}
```

### Listar productos de una organizacion

```http
GET /api/integration/organizations/{organization_id}/products/
X-API-Key: <internal-api-key>
```

### Endpoint legacy de modulos

```http
GET /api/integration/organizations/{organization_id}/modules/
X-API-Key: <internal-api-key>
```

El endpoint legacy puede incluir entitlements de producto para compatibilidad, pero solo incluye productos cuyo `access_allowed=True`.

## Preguntas que el contrato responde

| Pregunta | Respuesta |
| --- | --- |
| ¿La organizacion existe? | `Organization` por UUID en endpoints integration. |
| ¿Esta activa? | `Organization.status == active`. |
| ¿Tiene MEDSUPPLIER habilitado? | `OrganizationProductEntitlement(product.code=MEDSUPPLIER)`. |
| ¿Tiene ISO_SMART habilitado? | `OrganizationProductEntitlement(product.code=ISO_SMART)`. |
| ¿El usuario pertenece a la organizacion? | `UserOrganization(user, organization, is_active=True)`. |
| ¿El usuario puede acceder a ese producto? | Producto: endpoint validate; usuario/rol: membresia y scopes consumidos por producto. |
| ¿Que roles/scopes tiene? | `UserOrganization.role` y `OrganizationProductEntitlement.scopes`. |
| ¿La suscripcion esta activa? | `Subscription.is_active`. |
| ¿El billing status permite acceso? | `OrganizationProductEntitlement.billing_allows_access`. |
| ¿Debe suspenderse el acceso por impago? | Si suscripcion esta `past_due`, `suspended`, `cancelled` o `expired`, `access_allowed=False`. |
| ¿Que plan tiene? | `OrganizationProductEntitlement.plan` o `Subscription.plan`. |

## Evidencia de pruebas

Comandos ejecutados:

```bash
cd /home/felipe/proyectos/adminapps/backend
DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py check
DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py makemigrations --check --dry-run
DJANGO_SETTINGS_MODULE=config.settings_test ./.venv312/bin/python manage.py test apps.products apps.billing apps.users apps.api
```

Resultados:

| Comando | Resultado |
| --- | --- |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, No changes detected |
| `test apps.products apps.billing apps.users apps.api` | PASS, 123 tests OK |

## Gate ETAPA 4

| Criterio | Estado | Evidencia |
| --- | --- | --- |
| AdminApps puede habilitar MEDSUPPLIER por organizacion. | PASS | `OrganizationProductEntitlement` + tests. |
| AdminApps puede denegar MEDSUPPLIER si no esta habilitado. | PASS | `product_not_enabled` test. |
| AdminApps puede controlar billing/suscripcion. | PASS | `billing_blocked` test y `access_allowed`. |
| Tests AdminApps pasan. | PASS | 123 tests OK. |
| No hay migraciones pendientes sin justificar. | PASS | `No changes detected`. |
| No queda contrato ISO-centrico bloqueante. | PASS con observacion | Modelos legacy ISO siguen para compatibilidad, pero contrato nuevo usa `ProductSystem`. |

## Decision

Estado: aprobado con observaciones.

Decision: ETAPA 4 completada.

Observacion: los modelos legacy `ISOStandard` y `OrganizationModule` permanecen para ISO Smart. No bloquean MedSupplier porque el contrato producto-neutral vive en `ProductSystem` y `OrganizationProductEntitlement`.
