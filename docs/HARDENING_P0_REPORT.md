# Hardening P0/P1 Report - AdminApps

Fecha de ejecucion principal: 2026-07-02 America/Costa_Rica.
Reporte actualizado: 2026-07-03.
Branch revisado: `hardening/p0-enterprise-readiness-20260702`.

## Alcance

- Backend Django en `backend/`.
- Frontend Vite en `frontend/`.
- No se modificaron archivos `.env` reales.
- No se ejecuto `sudo`.
- No se realizaron commits desde esta documentacion.

## Cambios aplicados

- `DEBUG` queda en `False` por defecto.
- `DJANGO_SECRET_KEY` es obligatorio en produccion; el fallback local solo aplica fuera de produccion.
- `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, cookies seguras y `CORS_ALLOW_CREDENTIALS` quedan controlados por variables de entorno.
- `SECURE_SSL_REDIRECT`, HSTS y headers de seguridad quedan controlados por entorno, activos por defecto en produccion.
- Se reemplazaron `ModelSerializer.fields = "__all__"` por campos explicitos en serializers de organizaciones, productos, suscripciones, billing y usuarios.
- Se agrego guardrail automatizado para impedir nuevos serializers con `fields = "__all__"`.
- Se agrego prueba para exigir API key en el endpoint de salud de integracion.
- Se evito que el scheduler de billing arranque durante comandos administrativos de Django como `check`, `test`, `showmigrations`, `makemigrations` y `migrate`.
- Se movio el link de landing comercial del login frontend a `VITE_LANDING_URL`; si la variable no existe, el link no se renderiza.

## Estado

Resultado: implementacion P0/P1 validada para AdminApps.

Riesgo residual: hay migraciones ya existentes pendientes de aplicar en la base local revisada: `products.0003_productentitlementauditlog`, `billing.0006_productcatalog_system_product`, `integration.0004_integrationapikey_last_used_at_and_more`. No se ejecuto `migrate` porque debe hacerse dentro de una ventana controlada de release.
