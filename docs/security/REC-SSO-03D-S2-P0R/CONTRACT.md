# P0R: contratos de sesión y servicio

Fecha: 2026-10-19, America/Costa_Rica. Preparación local; ninguna configuración instalada.

## Revocación de sesiones

`POST /api/auth/users/revoke_sso_sessions/` exige la autenticación humana local existente.
Payload `{}` revoca todas las sesiones SSO del usuario autenticado, en todos sus clientes/tenants.
Payload `{"session_id": "<central SSOSession UUID>"}` revoca únicamente esa sesión **si pertenece al mismo usuario**.
No acepta user_id, tenant_id, client_id ni un identificador que deba conservarse.
Un JTI local, una cookie o un ID de sesión del consumidor no equivalen a un SID central.

Respuesta: `{"scope":"central_sso","revoked":1,"local_sessions_revoked":false}`.
`revoked` cuenta transiciones nuevas; repetir una revocación propia devuelve cero.
Un SID inexistente o ajeno deniega sin distinguir propietarios. UUID inválido/campos extra: 400;
principal no humano/inactivo: 401/403 según autenticador; DatabaseError: 503 sin detalles internos.
El servicio relee al usuario activo, verifica elegibilidad, bloquea el fence B y después las sesiones,
actualiza generación/authority_version y usa el outbox B existente. No modifica sesiones locales.

`POST /api/auth/users/revoke_sessions/` conserva su operación histórica sobre `UserSession`:
filtra por usuario y excluye el JTI **autenticado**, nunca un JTI arbitrario del cuerpo.
La respuesta ahora identifica `scope=local_registry`, `access_tokens_revoked=false` y
`central_sessions_revoked=false`. No es una revocación global de JWT ni de cookies Django.
**Falta adjudicar e implementar la vinculación durable del token local a una familia/sesión y su
verificación universal en access/refresh.** No existe un enlace demostrado UserSession↔SSOSession.

`POST /api/auth/logout/` conserva la revocación del refresh opcional del propio usuario.
La repetición de un refresh ya blacklisted verifica firma, expiración, tipo y propietario antes
de repetir la blacklist. Un access token no se acepta como refresh. Una falla de auditoría posterior
no deshace la blacklist ya ejecutada. El access JWT y las cookies locales no quedan revocados por ello.

Logout/rotate/introspect centrales de C/H/B conservan sus contratos. Los triggers preparados en
`0010_sso_authority_fence.py` contemplan contraseña, usuario, membresías, tenant, credenciales y
otros cambios de autoridad; su instalación/atomicidad/concurrencia permanecen NOT_EVIDENCED.

## Grants de servicio

La identidad procede de `authenticate_integration_api_key` y su verificación de hash. El grant
se busca **exclusivamente** por `credential_id` de esa fila autenticada, persistida, hashed_v1,
activa, status=active y sin revoked_at. El nombre de servicio, rol humano, cuerpo y SSOClient
no conceden permisos. Una clave rotada requiere provisión explícita para el nuevo credential_id.

La forma exacta de configuración del servidor es:

```python
INTEGRATION_API_GRANTS = {
    "<credential_id de la fila ya autenticable y autorizada>": {
        "operations": ["get_organization", "get_organization_products"],
        "tenant_ids": ["<UUID central de organización autorizado>"],
        "product_codes": ["ISO_SMART"],
    },
}
```

Es una plantilla sin identificadores reales ni secretos. Para MedSupplier, el producto es
`MEDSUPPLIER`; no se otorga automáticamente acceso a ambos productos. Cada lista debe ser
no vacía, de strings únicos y válidos. No se permiten campos extra, comodines, productos
fuera del catálogo ni operaciones desconocidas, aunque también haya una operación válida.

Las siete operaciones reconocidas son `list_organizations`, `get_organization`,
`get_organization_users`, `get_organization_modules`, `get_organization_products`,
`validate_organization_product_access` y `get_user_by_id`. Provisionar solo las efectivamente
necesarias. `get_user_by_id` requiere además `user_id` y `organization_id` explícitos; la membresía
y el tenant deben seguir activos. Los listados filtran por tenants concedidos.

`get_organization_modules` filtra entitlements y respuesta final por producto concedido.
No permite inferir scope de módulos legacy como SCA/SIE/DOC/RISK ni de exenciones owner.
El mapping comercial de esos códigos continúa pendiente; no se añadió un comodín o fallback.
Los endpoints SSO tienen contratos independientes; este grant no sustituye C/H/B/D ni habilita E/F/G.
`validate_credentials`, ingesta AI, landing/demo y lifecycle CLI de claves quedan fuera del contrato.

Los dos clientes existentes conservan sus métodos y argumentos, pero ignoran `use_cache` para
`/organizations/...` y `/user/`: deben observar revocación/grants centrales actuales.
Un HTTP 401/403 produce `allowed=false`, `authorization_denied=true` y un error sin secretos;
nunca activa fallback local, aun si la opción de desarrollo está habilitada. El helper de módulos
deniega también si una respuesta denegada contiene un listado de módulos. El fallback de errores
transportales preexistente no fue ampliado: ISO Smart ahora lo bloquea también con IS_PRODUCTION=true,
igual que MedSupplier. La prueba ejecuta timeout con el flag de fallback habilitado y producción activa.

## Invitaciones

`accept` es una vista previa pública con token: no crea usuario ni membresía. Ahora revalida
la autoridad vigente y el tenant antes de exponer la invitación.
El consumo ocurre en `RegisterSerializer.create`, dentro de su transacción existente, adquiriendo
fence B → invitación. Relee invitador, tenant y membresía; requiere invitador activo/elegible,
rol y membresía org_admin vigentes en el mismo tenant, o plataforma staff con el permiso de alta
de invitaciones y autoridad suficiente para el rol global. Sin invitador se deniega.

La identidad por correo, estado pendiente, expiración, rol válido y campos estrictos siguen
comprobándose. Después de validar el formulario, el consumo repite la verificación. No se permite
que el invitado aporte rol, organización o is_staff. No se cambió el contrato de registro público
sin invitación. Un fence ausente/no disponible impide consumir; no hay fallback.

La exclusión concurrente exige los triggers B instalados y ensayados en PostgreSQL. No existe
una prueba de continuidad histórica del invitador ante revocar→restaurar autoridad antes del consumo:
el contrato implementado comprueba autoridad vigente. Esa política adicional queda abierta.
