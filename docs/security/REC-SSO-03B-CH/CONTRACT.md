# REC-SSO-03B-CH — contrato de integración

Versión: `rec-sso-03b-ch-v1`. Trabajo histórico **C/H**, no B. Se conservan Decision A y REC-2FA-04. Código local; esquema/provisión/activación pendientes. `PRODUCTION_READY = FALSE`.

## Autoridad y principal
Cada POST central (`/api/integration/sso/login/`, `/sso/login/verify-2fa/`, `/sso/introspect/` bajo el mismo prefijo) exige X-API-Key de servidor y JSON `client_id`, `product`, `audience: [audiencia_exacta]`, `contract_version`. La credencial se verifica con el servicio existente y debe resolver a una fila IntegrationAPIKey hashed_v1 activa; aliases de configuración y plaintext histórico no son identidades de cliente. SSOClient se obtiene por principal_id autenticado, nunca por client_id declarado. El contrato valida las afirmaciones del request contra esa fila. OneToOne principal, client_id único, audience única, FK de producto y tenants explícitos impiden compartir la autoridad por coincidencias de nombres.

## Tokens y verificadores
- CENTRAL: RS256 exclusivamente, RSA mínimo 2048 bits, `kid` fijado en keyring y permitido por cliente, issuer central HTTPS y audiencia registrada exacta de un elemento. Requiere `auth_contract`, `token_family=CENTRAL`, producto/cliente, `sub=user_id` UUID, `tenant_id=organization_id` UUID, `exp`, `iat`, `jti`, `amr` y tipo access. Introspection no acepta refresh. Se rechazan `none`, HMAC, firmas alteradas, kids ausentes/desconocidos, cabeceras de key discovery y otros emisores. No hay descarga JWKS ni fallback.
- LOCAL: RSA del consumidor, issuer y audiencia locales distintos, `token_family=LOCAL`, mismo sujeto/tenant central y producto fijo en código. El consumidor rechaza claves RSA iguales a cualquier clave CENTRAL configurada; tampoco admite privada central en su configuración. `organization_id` local conserva su PK; `tenant_id` conserva UUID central. `sub` central no sustituye `user_id` local.
- Las claims solo se usan después de verificar firma y contexto. El consumidor compara la respuesta de introspección con claims firmadas, revalida estado/producto y solo entonces proyecta identidad. La API key se adjunta únicamente desde backend.
- Access y refresh centrales tienen 300 s, familia y tipo distintos. No se incorpora endpoint de refresh central y el consumidor no guarda el refresh central. La sesión local y su rotación no exceden exp central. La prueba central se revalida en cada autenticación local/refresh.
- Rol viewer permanece viewer; el emisor filtra la lista de productos al producto del cliente y no emite el antiguo scope transversal genérico. Esto no implementa scopes D ni concede permisos universales.

## MFA, tenancy y efectos
El challenge queda ligado a cliente, principal, producto, audiencia, tenant y versión. Un mismatch se rechaza antes de consumir TOTP/backup. Se preserva el servicio transaccional y no se revierte el consumo al fallar emisión/proyección posterior. La comprobación de estado MFA/generación continúa viva.
La proyección exige UUID central, no toma cuentas por coincidencia de email y no reasigna external_id. Tenant pedido debe coincidir con prueba firmada y respuesta central. Switch requiere prueba válida para destino. Errores de firma, configuración, esquema o autoridad no habilitan fallback.
No hay nuevas concesiones de scopes, reconciliación de usuarios ni escrituras de registro durante login. El registro es global de autoridad, sin acceso CRUD para consumidores. La auditoría de lifecycle de credenciales existente se conserva; este incremento no añade ledger durable de sesiones o de administración del registro. Los logs no incluyen JWT, códigos ni secretos. Login/MFA no son idempotentes; repetir una verificación no restaura el factor consumido. No se añade idempotency key a operaciones de autenticación.

## Transporte y errores
ISO Smart conserva HttpOnly y CSRF: no autentica bearer ni una sesión Django local como alternativa en la cadena de desarrollo. MedSupplier conserva bearer/localStorage; sus riesgos de XSS se registran aparte y no se cambia transporte. Middleware de organización usa el verificador LOCAL y autoridad viva antes de proyectar contexto.
400 entrada inválida; 401/403 denegación (incluyendo contexto/CSRF/membresía); 200 active=false para JWT inválido con cliente autenticado; 503 dependencia/contrato no disponible. Una falla posterior a consumo/emisión central puede retornar 500 sanitizado, sin devolver tokens ni reponer factor. Los consumidores convierten fallas centrales no exitosas en denegación o 503 sanitizado.

## Configuración futura, sin activar
`SSO_CENTRAL_TRUST`: `ALGORITHM='RS256'`, `ISSUER` HTTPS explícito, `PUBLIC_KEYS={kid: public_PEM}`; solo AdminApps añade `SIGNING_KID` y `PRIVATE_KEY`. Los consumidores no reciben privada central.
`SSO_LOCAL_TRUST`: mismo esquema, más `AUDIENCE` local exclusiva; privada propia y kid propio. Sus claves y emisor deben diferir de CENTRAL. En cada consumidor `ADMIN_APPS_SSO={BASE_URL, ISSUER, CLIENT_ID, AUDIENCE}` y `ADMIN_APPS_INTEGRATION={API_KEY, TIMEOUT}` son explícitos. Fuera de DEBUG el transporte central exige HTTPS. Las settings existentes no se editaron y no se instalaron claves ni registros.
No se usa una lista provisional en settings como sustituto durable. Sin tabla/filas/claves, el código falla cerrado. Aplicación del esquema y validación persistente: BLOCKED_BY_EXTERNAL_DEPENDENCY.

## Evidencia y límites
`/tmp/rec-sso-03b-ch-20261014/REPORT.md`, checks.json, test-results.json e integrity-final.json contienen comandos, resultados y hashes. Suites offline con dependencias simuladas; HTTP/E2E/PostgreSQL/concurrencia real: NOT_EVIDENCED. La disponibilidad de Ruff es NOT_EVIDENCED (no instalado; no se añadió dependencia). No se modifican los documentos históricos ni los gates S3-IMP-01, S3_DECISION_02A_NOT_CLOSED y PHASE31_5 = EXECUTION_HELD.
