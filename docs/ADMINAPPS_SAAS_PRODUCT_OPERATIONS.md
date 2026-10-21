# AdminApps SaaS Product Operations

Fecha: 2026-07-01

## Proposito

AdminApps opera como control plane central para productos SaaS independientes:

- `ISO_SMART`: ISO Smart.
- `MEDSUPPLIER`: ISO Smart MedSupplier.
- Productos futuros registrados en `products.ProductSystem`.

El acceso comercial no debe depender de modulos legacy ni de datos mostrados solo en frontend. La fuente de verdad para vender, activar, suspender o revocar productos por cliente es `products.OrganizationProductEntitlement`.

## Conceptos

| Concepto | Modelo | Uso |
| --- | --- | --- |
| Cliente / organizacion | `organizations.Organization` | Identidad comercial y tenant administrativo. |
| Producto SaaS | `products.ProductSystem` | Catalogo de sistemas vendibles y consultables por integracion. |
| Acceso contratado | `products.OrganizationProductEntitlement` | Habilita un producto para una organizacion con estado, plan, scopes y billing. |
| Auditoria de producto | `products.ProductEntitlementAuditLog` | Registra cambios sensibles sobre entitlements. |
| Plan | `subscriptions.Plan` | Plan comercial, limites y precio base. |
| Suscripcion | `subscriptions.Subscription` | Estado financiero global o vinculado al entitlement. |
| Catalogo billing | `billing.ProductCatalog` | Catalogo fiscal/facturable. Complementa a `ProductSystem`; no reemplaza el control de acceso. |
| Modulos legacy | `products.OrganizationModule` y `Plan.modules_included` | Configuracion operativa historica de ISO Smart. No otorga acceso comercial a productos SaaS. |

## Administrar productos desde UI

Flujo esperado:

1. Entrar a AdminApps con usuario administrador.
2. Ir a Organizaciones.
3. Abrir el detalle de una organizacion.
4. Abrir la pestana **Productos y accesos**.
5. Revisar las tarjetas de productos disponibles.
6. Activar `ISO_SMART`, `MEDSUPPLIER`, ambos o ninguno.
7. Cambiar a trial, suspender, revocar o cambiar plan desde las acciones de cada tarjeta.
8. Usar **Validar acceso** para confirmar la respuesta real del backend.

Cada tarjeta muestra:

- Nombre y codigo del producto.
- Estado del entitlement.
- Si el acceso esta permitido o bloqueado.
- Plan asociado.
- Estado billing efectivo.
- Vigencia.
- Scopes comerciales.
- Ultima actualizacion.
- Razon de bloqueo cuando aplica.

## Estados soportados

`OrganizationProductEntitlement.status` soporta estados comerciales como:

- `active`
- `trial`
- `suspended`
- `disabled`
- `expired`
- `cancelled`

La propiedad `access_allowed` del modelo es la decision backend que deben consumir los productos externos.

El plan comercial mostrado por API/UI se resuelve como `effective_plan`:

1. `OrganizationProductEntitlement.plan`, si existe.
2. `Subscription.plan`, si existe suscripcion efectiva.
3. `ProductSystem.default_plan`, como referencia comercial default.

`ProductSystem.default_plan` no habilita acceso pagado por si solo. Para productos con `billing_enabled=true`, un entitlement `active` sigue requiriendo suscripcion efectiva activa, salvo estado `trial`.

## Asignar ISO Smart

Crear o activar un `OrganizationProductEntitlement` con:

- `organization`: UUID del cliente.
- `product`: `ProductSystem` con `code='ISO_SMART'`.
- `enabled=true`.
- `status='active'` o `status='trial'`.
- `plan` y `subscription` cuando aplique.

Desde UI: Organizacion -> Productos y accesos -> tarjeta ISO Smart -> Activar o Trial.

## Asignar ISO Smart MedSupplier

Crear o activar un `OrganizationProductEntitlement` con:

- `organization`: UUID del cliente.
- `product`: `ProductSystem` con `code='MEDSUPPLIER'`.
- `enabled=true`.
- `status='active'` o `status='trial'`.
- `plan` y `subscription` cuando aplique.

Desde UI: Organizacion -> Productos y accesos -> tarjeta ISO Smart MedSupplier -> Activar o Trial.

## Asignar ambos productos

Crear dos entitlements independientes para la misma organizacion:

- Uno para `ISO_SMART`.
- Uno para `MEDSUPPLIER`.

Suspender o revocar uno no debe modificar el otro.

## Revocar o suspender acceso

Desde UI:

- **Suspender** llama al toggle backend con `action='disable'`; el entitlement queda bloqueado y auditado.
- **Revocar** actualiza el entitlement a `enabled=false` y `status='cancelled'`; el acceso queda bloqueado.

Ambas acciones requieren confirmacion visual y refrescan el estado desde backend.

## Validacion para productos externos

Los productos externos deben consultar AdminApps:

```http
GET /api/integration/organizations/{organization_id}/products/{product_code}/validate/
X-API-Key: <internal-api-key>
```

Las denegaciones quedan auditadas como `ProductEntitlementAuditLog(action='validated')`. Las validaciones permitidas no se auditan por defecto para evitar ruido operativo; un producto externo puede solicitar evidencia explicita usando:

```http
GET /api/integration/organizations/{organization_id}/products/{product_code}/validate/?audit=true
X-API-Key: <internal-api-key>
```

Las API keys persistidas en `integration.IntegrationAPIKey` actualizan `last_used_at` y `last_used_service` en cada uso correcto. Las claves hash configuradas por settings siguen siendo validas, pero no tienen fila persistida para registrar ultimo uso.

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
    "access_allowed": true,
    "access_denial_reason": "ok",
    "billing_status": "active"
  },
  "reason": "ok"
}
```

Respuesta bloqueada:

```json
{
  "allowed": false,
  "reason": "product_not_enabled",
  "product": {
    "code": "MEDSUPPLIER",
    "access_allowed": false
  }
}
```

## SSO e introspection

El login SSO (`POST /api/integration/sso/login/` y `POST /api/integration/sso/login/verify-2fa/`) devuelve en `tokens` dos claims compactos:

- `allowed_products`: lista de codigos de productos con acceso permitido para la organizacion seleccionada.
- `product_entitlements`: snapshot de entitlements del cliente con `code`, `status`, `access_allowed`, `access_denial_reason`, `scopes`, `plan` y `subscription`.

Estos claims tambien se incluyen dentro del access token y refresh token emitidos por AdminApps. Sirven para bootstrapping de sesion y experiencia de usuario. La decision autoritativa para acciones sensibles debe seguir usando introspection o el endpoint de validacion por producto, porque ambos consultan el estado vivo en AdminApps.

El endpoint seguro de introspection incluye productos permitidos para la organizacion del token:

```http
POST /api/integration/sso/introspect/
X-API-Key: <internal-api-key>
Content-Type: application/json

{"token": "<access-token>"}
```

La respuesta incluye `products` con:

- `code`
- `enabled`
- `status`
- `access_allowed`
- `access_denial_reason`
- `scopes`
- `modules_enabled`
- `plan`
- `subscription`
- `ends_at`

Si un producto necesita una decision puntual, debe usar el endpoint `validate` por `organization_id` y `product_code`.

## Modulos legacy

`/api/integration/organizations/{organization_id}/modules/` existe por compatibilidad. Este endpoint:

- Puede devolver modulos legacy operativos.
- Puede incluir productos SaaS solo cuando existe entitlement con `access_allowed=true`.
- No debe otorgar acceso a `ISO_SMART` o `MEDSUPPLIER` solamente porque `Plan.modules_included` contiene esos codigos.

## Auditoria

Las acciones sensibles sobre entitlements registran `ProductEntitlementAuditLog`:

- Crear entitlement.
- Activar.
- Suspender.
- Iniciar trial.
- Cambiar plan.
- Actualizar metadata/scopes/fechas.

Los logs estan disponibles por:

- Django Admin.
- `GET /api/products/entitlements/{id}/audit_logs/`
- `GET /api/products/entitlement-audit-logs/`
- UI de organizacion: pestana **Auditoria**, con filtros por accion/producto y export CSV.

## Billing y ProductCatalog

Estado actual:

- `ProductSystem` gobierna acceso SaaS.
- `ProductCatalog` gobierna facturacion/fiscal.
- `OrganizationProductEntitlement` puede apuntar a `Plan` y `Subscription`.
- `ProductCatalog.system_product` permite mapear un producto fiscal a un `ProductSystem`.

Regla operativa:

- No se debe cobrar un producto sin revisar su entitlement.
- No se debe habilitar un producto comercial sin plan/suscripcion cuando `billing_enabled=true`, salvo excepcion operativa documentada.
- Si `ProductCatalog.system_product` esta configurado, billing bloquea la emision de facturas para organizaciones sin entitlement permitido.
- Si `ProductCatalog.system_product` no esta configurado, billing mantiene compatibilidad con catalogos existentes y no aplica validacion SaaS por entitlement.

Gobierno de mapping:

- `GET /api/billing/products/mapping_audit/` devuelve resumen de items fiscales mapeados, candidatos exactos y no mapeados.
- `POST /api/billing/products/auto_map/` corre en `dry_run=true` por defecto y muestra coincidencias exactas sin modificar datos.
- `POST /api/billing/products/auto_map/` con `{"dry_run": false}` aplica solo candidatos exactos entre `ProductCatalog` y `ProductSystem`.
- La pantalla de Finanzas permite revisar el resumen, aplicar candidatos exactos con confirmacion y editar manualmente el mapping item por item.
- Los cambios manuales y automaticos de mapping quedan auditados en `users.UserActivityLog` con eventos `billing_product_mapping_updated` y `billing_product_auto_mapped`.

Comando operativo para release/DevOps:

```bash
python manage.py audit_product_catalog_mapping
```

Requiere que las migraciones de AdminApps esten aplicadas. Por defecto es read-only y devuelve JSON con `mapped`, `candidate_found` y `unmapped`.

Para aplicar solo coincidencias exactas:

```bash
python manage.py audit_product_catalog_mapping --apply
```

Este comando no crea productos SaaS nuevos y no usa coincidencias ambiguas.

Pendiente recomendado:

- Completar revision operativa de catalogos billing existentes hacia `ProductCatalog.system_product`.
- Definir si la relacion debe ser uno-a-uno o permitir varios items fiscales por producto SaaS.
- Validar en backend que productos con `billing_enabled=true` tengan plan/suscripcion antes de activarse para produccion pagada.

## Pruebas clave

Cobertura backend esperada:

- Crear entitlement de ISO Smart.
- Crear entitlement de MedSupplier.
- Cliente con ambos productos.
- Suspender producto.
- Revocar/cancelar producto.
- Trial.
- Validar acceso permitido.
- Validar acceso bloqueado.
- Confirmar que `Plan.modules_included` no habilita productos SaaS sin entitlement.
- Bloquear administracion de entitlements para usuarios sin permiso.
- Bloquear org_admin sobre organizaciones ajenas.
- Bloquear escalamiento de rol por payload.

## Readiness / smoke operativo

Antes de una demo o despliegue de staging se puede generar un reporte read-only del contrato SaaS:

```bash
python manage.py check_product_access_readiness
```

El mismo contrato esta disponible para administradores autenticados:

```http
GET /api/product-readiness/
Authorization: Bearer <admin-token>
```

El reporte confirma:

- Existencia y disponibilidad de `ISO_SMART` y `MEDSUPPLIER`.
- Conteo de entitlements activos, trial, suspendidos y cancelados.
- Organizaciones con solo ISO Smart, solo MedSupplier, ambos o ningun producto activo.
- Watchlist de planes legacy que mencionan productos SaaS en `modules_included` sin entitlement real.

El comando no modifica datos y no sustituye el smoke end-to-end de los productos consumidores.

## Limitaciones pendientes

- La linea de tiempo visual de auditoria muestra eventos de entitlements por organizacion e incluye filtros por accion/producto y export CSV.
- La relacion `ProductCatalog.system_product` existe, pero falta backfill y gobierno operativo de catalogos existentes.
- No existe endpoint dedicado para cambiar plan de entitlement con reglas comerciales avanzadas; se usa PATCH controlado sobre el entitlement.
- La suscripcion global de organizacion y la suscripcion por producto pueden coexistir; se recomienda normalizar reglas comerciales por paquete en una siguiente iteracion.

## Readiness de salida

Estado interno AdminApps: listo para revision tecnica y demo controlada del control plane SaaS.

Antes de vender formalmente o abrir produccion amplia se recomienda completar:

- Ejecutar `python manage.py audit_product_catalog_mapping` y, tras revision, `--apply` sobre catalogos reales.
- Definir regla comercial obligatoria de plan/suscripcion para productos con `billing_enabled=true`.
- Validar en staging que ISO Smart y MedSupplier consumen `validate` o introspection sin rutas legacy.
- Revisar datos reales de organizaciones, roles y API keys internas.
- Ejecutar `python manage.py check_product_access_readiness`.
- Ejecutar smoke test end-to-end con un cliente solo ISO Smart, uno solo MedSupplier y uno con ambos.
