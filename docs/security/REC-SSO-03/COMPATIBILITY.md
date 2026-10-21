# Compatibilidad por revisión de código y contratos

Estado global: **REQUIRES_COORDINATED_ADAPTATION / RUNTIME_NOT_TESTED**.
No se declara compatibilidad PASS. Los tres ConsumerTests previos prueban
transporte sustituido y algunos bools, no el recorrido de login, sesión, API o
datos persistentes de cada producto. Referencias: [EVIDENCE.md](EVIDENCE.md).

## ISO Smart

Ruta descubierta: `/home/felipe/proyectos/isosmart`. El contrato CT3/ADR-0002
preserva AdminApps como autoridad y roles QMS locales sin elevación global.

| Decisión / diffs | Soporte existente demostrado en fuente | Adaptación coordinada necesaria / conclusión |
| --- | --- | --- |
| A / P01 | client.py:365 envía legacy; backend exige valid; serializer:241 rechaza local sin bypass; frontend no transporta challenge. | Añadir challenge/verify sin cookie antes del factor, UX y recuperación; bloquear rutas alternativas. Denegación estructural soportada, login 2FA futuro no implementado. |
| B / P02 | sso_auth.py sincroniza rol snapshot; cookie_auth usa JWTAuthentication; refresh deriva access del refresh. Client permite cache 300 s; QMS create sí pide producto/actor vivos. | Revocar cookie y bearer, invalidar proyecciones/cachés y refrescar estado antes de operaciones; no extrapolar QMS create a todas las APIs. Sin garantía global de frescura. |
| C / P03 | SIMPLE_JWT HS256 sin ISSUER/AUDIENCE; JWT local con organización local, central con UUID; cookie y bearer coexisten. | Validadores por familia/receptor y subject/tenant; no un issuer global que rompa cookies. Inventario/corte central/local, refresh y switch-org coordinados. |
| D / P04 | CanEdit excluye viewer/auditor; RoleBasedPermission usa jerarquía; QMS create permite roles explícitos con autoridad viva. | Intersección de scopes/entitlement con permisos QMS/objeto y auditoría de endpoints; retirar defaults a user ante rol desconocido. Emitir scopes solos no hace enforcement. |
| E / P05/P06 | login llama validate ISO_SMART con use_cache=False; cliente respeta allowed false. | UX de trial/billing, revalidación de sesiones abiertas y coordinación de provisioning; ausencia de inventario impide estimar afectados. P06 no modifica transporte pero cambia errores de escritura en AdminApps. |
| F / P07 | client propaga reason; Boolean allowed rige el login. | Tratar entitlement_not_started como deny, reloj/expiry de caché y frontera aprobada; snapshots no deben abrir anticipadamente. |
| G / P08 | CT3 prohíbe billing paralelo y reasignar external ID; consumers reciben decision comercial. | Aceptar razón versionada por vínculo, usar tenant UUID y conservar proyecciones; no backfill local automático de suscripciones. |
| H / P09 | X-API-Key, calls de producto/usuario, QMS create y contrato tenant-events. | Separar principal productor/receptor, permitir solo operaciones/tenants concretos; resolver adapters legacy ID local/global y denegar claves no registradas. |

IS2 y backends.py contienen sincronizaciones que pueden resolver usuario por
email, tratar organización numérica como PK local y reasignar perfil ante
IntegrityError; backends.py también reutiliza slug y puede alinear external_id.
CT3 prohíbe usar estos atajos para resolver drift. La transición C/B debe preservar
identidad canónica y rechazar ambigüedad, sin reasignar datos. No se prueba aquí
que esos caminos se hayan activado en producción.

El código actual usa cookies en login/refresh con CSRF y también ofrece bearer
SSO. La nota histórica FRONTEND_AUTH_SECURITY describe localStorage: debe
reconciliarse en un trabajo documental posterior, sin sustituir evidencia de código
por esa nota ni afirmar configuración desplegada.

El inventario C debe incluir además el emisor diagnóstico
`backend/foundation/operational_bearer_identity.py:73`: declara audience
`iso-smart`, client `phase31-operational-readiness`, lifetime default 900 s y
scope tenant:read. Son valores encontrados en fuente, **no registros aprobados**
para el nuevo contrato. No ejecutar ese emisor ni convertir su existencia en
excepción automática; mantiene su autoridad histórica y PHASE31_5 EXECUTION_HELD.

## MedSupplier

Ruta descubierta: `/home/felipe/proyectos/ISO_Smart_MedSupplier`. CT4 exige acceso
producto-neutral MEDSUPPLIER; CT5 exige además side/account/visibilidad.

| Decisión / diffs | Soporte existente demostrado en fuente | Adaptación coordinada necesaria / conclusión |
| --- | --- | --- |
| A / P01 | backend valida valid; serializer:255 acepta candidato con password y :277–291 permite perfil activo sin admin_apps_data. Login emite JWT local. No challenge en authService. | Cerrar fallback de identidad independientemente del flag de fallback comercial; estados 2FA, recuperación y ninguna sesión antes de verify. BLOCKED_BY_STATIC_GAPS para contención solo en servidor. |
| B / P02 | sso_auth reescribe rol/perfil desde JWT; refresh:238 deriva access sin consulta de autoridad; sync middleware tolera outage y guarda intervalo. | Revalidación de identidad/rol/producto en operaciones y refresh, invalidación local durable y cachés; logout/rotación no garantizan revocación central. |
| C / P03 | SIMPLE_JWT sin issuer/audience, HS256; JWT local con PK de org; sso_auth acepta claims centrales/locales. | Separar confianza por familia/receptor, preservar UUID y subject; actualizar login/refresh y manejo de tokens en frontend. C solo en AdminApps no protege API local. |
| D / P04 | MedSupplierContext y permisos de objeto usan roles supplier/customer, account_ids y visibility; fallback eleva org_admin/iso_manager a supplier_admin. | Añadir intersección con autorización central y revisar fallback/superuser; customer con scope write no puede mutar ni ver finanzas privadas. No reemplazar CT5 por tenant:write. |
| E / P05/P06 | cliente:373 respeta allowed=false y falla cerrado por defecto; integration_status:1104 consulta producto sin caché. LoginSerializer no llama validate producto. | Incorporar guard en login y operaciones, no solo pantalla diagnóstica; coordinar trial/provisión y mensajes de error. Sin eso no hay garantía de efecto de P05 en todo el producto. |
| F / P07 | bool/reason de validate son transportables; no hay parser cerrado de reasons en ese cliente. | Nueva razón deny, expiry de caché y enforcement API; verificar fronteras con sesiones previas. Compatibilidad sintáctica no es compatibilidad de seguridad. |
| G / P08 | cliente no decide ownership; dominio tiene SupplierAccount/account_scope propio. | No usar esos accounts como autoridad comercial central; validar producto/tenant/beneficiario vía AdminApps y reflejar deny. |
| H / P09 | X-API-Key configurada; APIs producto/usuario/módulos usan el mismo cliente. | Registro estable de principal MEDSUPPLIER, endpoints/tenants permitidos y errores; no heredar autoridad ISO por compartir código. |

**Límite concreto de la defensa legacy:** ModuleAccessMiddleware contempla ruta
MEDSUPPLIER en settings, pero sale sin comprobar si usuario u organización aún no
están disponibles; excluye `/api/auth/` y consulta módulos cacheables. No acredita
enforcement de producto para todos los bearer requests. AdminAppsSyncMiddleware
retorna True ante interrupciones temporales y guarda cache de sync; no es un
control de frescura crítica. El análisis estático no ejecutó esas combinaciones
de middleware, por lo que son casos negativos obligatorios, no exploits probados.

El cliente de **entitlements** fail-closed no elimina el fallback de **identidad**
del serializer ni el fallback de **rol de dominio** en permissions.py: son tres
puntos distintos que deben inspeccionarse en el rollout. Las pruebas previas de
ConsumerTests solo cubren el primero. Tokens frontend permanecen en localStorage;
el alcance de C/B debe incluir su invalidación y no copiar sin adaptación el
transporte cookie de ISO Smart.

## Contrato de coordinación entre repositorios

Para cada slice aprobado, fijar commits/hashes de los tres lados, versión de
contrato, fixture sintético compartido y aceptación firmada por cada consumidor.
Prueba positiva desde login hasta operación protegida; prueba negativa por API
directa con UI omitida, sesión anterior, refresh, cambio de tenant y fallo de
autoridad. Exigir resultado real del producto en entorno autorizado, además de
pruebas unitarias/contractuales. No elevar a PASS por que el servidor responda el
JSON esperado o porque los mocks tengan `allowed=false`.

Los patrones de código indican que ambos productos **pueden adaptarse**, pero
no demuestran que ya soporten íntegramente cada cambio. Configuración desplegada,
schema actual, clientes/keys y cohortes comerciales siguen NOT_TESTED y requieren
evidencia antes del rollout. No hay cambios en estos repositorios durante REC-SSO-03.
