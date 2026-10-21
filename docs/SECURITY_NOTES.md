# Security Notes - AdminApps

## Configuracion

- Produccion debe definir `DJANGO_ENV=production`.
- Produccion debe definir `DJANGO_SECRET_KEY`; no hay fallback silencioso en ese modo.
- `DEBUG` no debe habilitarse en produccion.
- `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS` deben declararse explicitamente por entorno.
- `CORS_ALLOW_CREDENTIALS` queda desactivado por defecto y debe habilitarse solo cuando exista una necesidad documentada.
- `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` quedan activos por defecto en produccion.
- `SECURE_SSL_REDIRECT` y HSTS quedan activos por defecto en produccion y pueden ajustarse por variables de entorno.
- `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS`, `SECURE_REFERRER_POLICY` y `SECURE_CROSS_ORIGIN_OPENER_POLICY` quedan definidos.

## Serializacion

- Los serializers revisados ya no usan `fields = "__all__"`.
- Los serializers de billing exponen campos explicitos y no publican campos privados cifrados internos.
- El guardrail `backend/apps/api/tests_security_guardrails.py` debe mantenerse en CI.

## Integraciones

- La prueba `IntegrationAPIKeyUsageTests.test_integration_health_rejects_missing_api_key` cubre el caso de rechazo cuando falta API key.
- El scheduler de billing solo arranca en `runserver` dentro del proceso principal del autoreloader, procesos server conocidos o con `BILLING_SCHEDULER_FORCE=true`; no arranca en comandos administrativos.
- El frontend no incluye por defecto el dominio local de landing comercial en el bundle; se usa `VITE_LANDING_URL`.

## Pendientes recomendados

- Mantener las migraciones pendientes bajo control operativo antes de deploy.
- Migrar almacenamiento de JWT en `localStorage` hacia cookies HttpOnly/SameSite en una fase coordinada backend/frontend.
