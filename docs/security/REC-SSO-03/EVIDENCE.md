# Registro de evidencia y límites

Fecha 2026-10-14, America/Costa_Rica. Fuentes leídas estáticamente del worktree,
incluidos cambios locales. Las referencias por línea son orientativas para este
snapshot; [source-manifest.json](evidence/source-manifest.json) fija los bytes.

| ID | Fuente y localizador | Aporte |
| --- | --- | --- |
| CT1 | AdminApps `docs/PRODUCT_NEUTRAL_ADMINAPPS_CONTRACT.md`, identidad, reglas 1–8 y API validate | UUID canónico, autoridad, suscripción obligatoria con billing, membresía/scopes |
| CT2 | AdminApps `docs/ADMINAPPS_SAAS_PRODUCT_OPERATIONS.md`, conceptos, trial, validación, SSO | Excepción trial, snapshots y validación viva sensible, auditoría |
| CT3 | ISO `docs/transformation/ISO_SMART_AI_ADMINAPPS_CONTRACT.md` y `docs/adr/0002-adminapps-control-plane-boundary.md` | Proyecciones, roles QMS, errores/freshness y no reasignación de external ID |
| CT4 | MedSupplier `docs/internal/ADMINAPPS_MEDSUPPLIER_CONTRACT.md` y `docs/validation/AdminApps_Integration_Decision.md` | Producto MEDSUPPLIER, denegación y autoridad central |
| CT5 | MedSupplier `docs/security/Role_Permission_Matrix.md` | Side, roles, finanzas privadas y alcance customer |
| AA1 | AdminApps `backend/apps/integration/views.py:131,526,618` | API key sin autorización dimensional; validación legacy y lookup usuario |
| AA2 | AdminApps `backend/apps/integration/sso_views.py:110,200,322,421` | Emisión, challenge/consumo 2FA, introspection con fix local |
| AA3 | AdminApps `backend/apps/products/models.py:65,130`; `serializers.py:91,121,164`; `views.py:106,161` | Trial, fechas, suscripción efectiva, partial update y toggle |
| AA4 | AdminApps `backend/apps/organizations/models.py:131`; `backend/apps/subscriptions/models.py:80,144` | FK no única y ausencia de owner; actividad de suscripción |
| AA5 | AdminApps `backend/apps/integration/services.py:132`; `models.py`; `config/settings.py:210`; `apps/users/urls.py:36` | Lifecycle/fallback keys, duración tokens y refresh estándar |
| AA6 | AdminApps `backend/scripts/rec_sso_02_offline.py:316–370` y REC-SSO-02 `evidence/tests-after.json` | Nueve métodos, fixtures/mocks, resultados previos |
| IS1 | ISO `backend/integration/client.py:365,405`; `backends.py:56`; `authentication/serializers.py:241,413` | Contrato legacy, rechazo local sin bypass y validate fresco al login |
| IS2 | ISO `backend/integration/sso_auth.py:26,73`; `backend/backend/settings.py:174,326,335`; `authentication/cookie_auth.py` | JWT local/central, sync snapshot, cookies/CSRF y ausencia de issuer/audience en SIMPLE_JWT |
| IS3 | ISO `backend/authentication/permissions.py`; `backend/foundation/qms_organization.py:70–90` | Roles locales y control vivo de producto/actor en un caso QMS |
| IS4 | ISO `backend/authentication/views.py:161,244`; `frontend/src/services/authService.js`; `integration/middleware.py` | Sesión cookie, refresh y sync/cache |
| IS5 | ISO `backend/foundation/operational_bearer_identity.py:73–148` | Familia diagnóstica adicional para inventario C; no autoriza su emisión ni ejecución |
| MS1 | MedSupplier `backend/integration/client.py:479`; `backends.py:56`; `authentication/serializers.py:199–295,400–432` | Legacy; fallback de contraseña/perfil; ausencia de validate producto en ese serializer |
| MS2 | MedSupplier `backend/integration/sso_auth.py:26,73`; `backend/backend/settings.py:254,263` | Familias JWT, rol/tenant snapshot, HS256 sin issuer/audience configurados |
| MS3 | MedSupplier `backend/medsupplier/permissions.py:56–218`; `views.py:89,109,1092`; `integration/middleware.py:56–106,144–202` | Side/account/visibilidad, profile fallback, integration status y límites middleware |
| MS4 | MedSupplier `backend/authentication/views.py:118,215`; `frontend/src/services/authService.js`; `integration/client.py:373,522` | JWT local, refresh, localStorage, caché de validación e invalidación |
| GOV | REC-SSO-02 REPORT/DECISIONS/MIGRATION_READINESS; `evidence/REC-2FA-04-closure.json`; `docs/financial/ADMINAPPS_AI_FINANCIAL_S3_IMP_01_CONTRACT_FREEZE_HUMAN_DECISION_2026-10-12.md` | Antecedentes y estados retenidos |

Los roots exactos están en REPORT B. La documentación ISO
`docs/FRONTEND_AUTH_SECURITY.md` aún describe localStorage y plan futuro de cookies;
el código actual IS4 y CookieJWTAuthentication ya usa cookies. Esa discrepancia
documental se registra, sin editarla ni copiar la descripción histórica al diseño
futuro. MedSupplier sí conserva localStorage en el código leído.

## Comprobaciones de esta campaña

- Descubrimiento con `rg --files`; lectura con `cat`, `rg -n`, `nl`/`sed`.
  Algunas búsquedas iniciales usaron rutas tentativas inexistentes (por ejemplo
  core/product_access.py); se sustituyeron por búsqueda de archivos/callsites.
  No se interpretó un error de búsqueda como evidencia de ausencia.
- `git --no-optional-locks status`, `rev-parse`, `branch --show-current`,
  `worktree list`, `ls-files`, `diff --binary` y diff de índice: solo lectura.
- Hashes SHA-256 por lectura binaria con biblioteca estándar Python, sin importar
  Django, módulos de aplicación ni settings; `python -B` no genera bytecode.
- `git apply --check` sobre cada uno de los nueve parches, sin flags de aplicación:
  [resultado](evidence/proposals-review.json). No se verificó composición aplicando
  candidatos; se identificaron archivos compartidos mediante inspección.
- [Antecedentes](evidence/antecedent-verification.json): 40/40 SHA256SUMS coinciden.
- [Integridad final](evidence/integrity-final.json): comparación de baseline,
  hashes tracked/index, estados y antecedentes tras escribir documentación nueva.

## Lo que esta evidencia no acredita

No inspecciona DB actual, despliegues, flags activos, secretos, claves, IdP ni
tráfico. No cuenta clientes registrados reales, trials afectados ni suscripciones
compartidas. No ejecuta test nuevo, E2E, replay concurrente, refresh real, RLS ni
prueba de exploit. La ausencia de enforcement en un recorrido inspeccionado se
reporta como gap estático; no demuestra por sí sola explotabilidad desplegada.

Las migraciones `users.0004_transactional_2fa` e
`integration.0006_integration_api_key_lifecycle` se leyeron como texto y coinciden
con el plan previo. El estado DB histórico del 2026-10-13 no es el estado actual.
No se ejecutaron `manage.py`, checks, loaders de migraciones ni runners antiguos.
