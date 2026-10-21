# Políticas comerciales pendientes

No se adjudican E/F/G. Los tres HIGH originales de B permanecen abiertos fuera del gate D.

| Caso | Fuentes revisadas | Implementación D | Decisión humana pendiente |
|---|---|---|---|
| Trial sin suscripción válida | products/models.py billing_allows_access permite trial; products/views.py _validate_entitlement_can_activate exige suscripción para activación; products/tests.py preserva fixtures legacy | No grants para trial facturado; autenticación B puede seguir active | Trial gratuito sin billing vs trial con suscripción vs acceso parcial. Duración y capacidades no decididas |
| starts_at futuro | Campo starts_at y ends_at, propiedades actuales solo validan ends_at | Cota inferior estricta en evidencia D; pruebas antes/dentro/después | Confirmar política de preactivación si se desea; no se habilita por conveniencia |
| Suscripción ajena | Organization.subscription FK; entitlement override; Subscription no tiene owner/tenant; Plan.max_organizations admite varias organizaciones | Override diferente del vínculo canónico DENY | Definir ownership y delegación de suscripción multi-organización; coincidir el FK no acredita propiedad final |

El código source-of-truth de access_allowed NO fue reescrito: la nueva evidencia D es más
restrictiva. Endpoints legacy de validate/access pueden seguir publicando su resultado previo;
ningún consumidor cubierto puede usarlo como grant D. Los endpoints fuera del gate son bloqueo
crítico. No se retiran los FAIL históricos ni se afirma resolución comercial.

modules_enabled tiene ejemplos document_room/rfq/quality, sin mapeo completo al catálogo D.
Se retiene cualquier lista no vacía/desconocida; no se ignoran restricciones. No hay migración
automática desde scopes qms/supplier/customer/pilot. Planes tienen max_users/documents/storage;
creación documental, usuarios y cuotas agregadas no están habilitados/verificados por D.
Fuentes: apps/products/models.py, views.py, tests.py; apps/organizations/models.py;
apps/subscriptions/models.py; docs/ADMINAPPS_SAAS_PRODUCT_OPERATIONS.md. Sin fuentes externas.
