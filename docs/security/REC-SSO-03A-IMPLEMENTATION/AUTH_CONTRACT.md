# Decision A — contrato de autenticación local con autoridad central

Implementación local autorizada el 2026-10-14. Los registros anteriores siguen siendo antecedentes; este documento no activa despliegues ni modifica gates independientes.

`POST /api/auth/login/` acepta `{email, password, organization_id?}` o, para completar el mismo desafío central, `{challenge_token, otp_code}`. El OTP admite TOTP o código de respaldo y se verifica exclusivamente en AdminApps.

- Desafío: HTTP 200, `{requires_2fa:true, challenge_token, challenge_expires_in}`. Sin user/profile autenticados, access, refresh ni cookie de sesión concedida. ISO borra cookies previas al responder al desafío.
- Éxito: HTTP 200, `{requires_2fa:false, user, profile, organizations}`. MedSupplier añade `access` y `refresh`; ISO conserva cookies HttpOnly y exige CSRF, también para login y refresh.
- Rechazo central/contexto/producto/proyección: HTTP 401. Indisponibilidad, contrato/configuración/esquema no verificable: HTTP 503 sanitizado. Campos inválidos: HTTP 400. No fallback a contraseña local, perfil, superusuario, flags o caché positiva.
- AdminApps legacy: contraseña incorrecta → 401 sin revelar estado MFA; contraseña correcta con factor habilitado → 403, `valid:false`, `code:second_factor_required`. Error DB/key/MFA → 503, `valid:false`.

Configuración requerida del consumidor: `ADMIN_APPS_SSO` con `BASE_URL` (raíz de integración, sin trailing endpoint), `ISSUER`, `CLIENT_ID` y `AUDIENCE`, todos explícitos. No se derivan de nombres de producto. Se compara audience de la prueba exactamente con `[AUDIENCE]`. Producción exige HTTPS. Se reutiliza la API key existente; no se crean claves ni registros.

La prueba central debe estar activa, firmada y con contrato `decision-a-v1` y `amr` que incluya contraseña; si el factor central está habilitado, introspection exige OTP y la generación MFA vigente. Los UUID de sujeto/tenant son obligatorios. El producto de cada consumidor es fijo e independiente: ISO_SMART o MEDSUPPLIER.

La sesión local conserva `central_proof`, `central_sub`, `auth_contract`, tenant, perfil y rol. Cada acceso y refresh vuelve a consultar introspection sin caché; no basta un bool del navegador. Perfil activo, organización activa, UUID externo, email, vínculo de sujeto y rol deben coincidir. La sesión no excede el expiry central. No se almacena refresh central; su expiración requiere login central nuevo.

Una proyección nueva usa `username=adminapps:<UUID>`. Una proyección existente requiere ese vínculo o `ADMIN_APPS_USER_BINDINGS` explícito (UUID → PK). Email/slug coincidente no establece identidad. Se preservan lockout/desactivación y constraints; no se reasigna perfil o UUID externo para superar errores. Una restricción owner requiere `OWNER_ORGANIZATION_EXTERNAL_ID` exacto.

Un switch a tenant distinto exige login/challenge central nuevo. Los refresh/JWT antiguos y sesiones Django sin prueba no conceden autenticación. El consumo central sigue siendo irreversible aunque falle sincronización o emisión local después; no se añade una transacción que restaure el segundo factor.

Audiences/clientes/principales registrados y separación criptográfica quedan pendientes (C/H en la matriz histórica); revocación durable y transición operativa de sesiones, B; scopes y enforcement de dominio/objeto, D. Los permisos QMS y supplier/customer existentes no se reemplazan por MFA ni por `tenant:write`. Sin pruebas HTTP/ORM/concurrencia reales, no se declara E2E ni preparación de producción.
