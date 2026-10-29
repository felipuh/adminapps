# Preflight de seguridad y hallazgos P0/P1

Estado: preparación offline. **No instalado en servicios; no certifica configuración efectiva ni aislamiento.** Ver `tools/staging_recovery/` y evidencia de tests vinculada a los SHA auditados.

## Mecanismos reales revisados

| Mecanismo | Activación y alcance | Resultado/riesgo |
| --- | --- | --- |
| AdminApps SMART3AI_SSO_ALLOW_2FA_BYPASS | Definido en config/settings.py; deshabilitado en archivo observado | El SSO actual fija two_fa_bypassed=false; no se encontró uso del flag para permitir SSO en los módulos revisados. No demuestra seguridad universal |
| ISO ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS | Settings exige IS_DEVELOPMENT y flag; helper en authentication/views.py | Flag solicitado localmente; helper afecta recuperación debug, **no el nuevo login central** |
| ISO recuperación debug | Solicitud explícita + DEBUG o helper local; responde debug_reset_url | Helper confía en host y en X-Forwarded-For sin verificar proxy. Reproducción offline confirma que IP reenviada falsificable satisface helper con flag habilitado. **P0 condicional de recuperación**; no se explotó endpoint ni se emitió token real |
| MedSupplier ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS | Settings permite flag, default ligado a desarrollo; management command de password local | Flag solicitado; no acredita que LoginSerializer actual haga fallback. Login actual centralizado; no se declaró bypass efectivo |
| ISO ALLOW_LOCAL_AUTH_FALLBACK | Settings limita default a desarrollo; client.py permite si flag efectivo y no IS_PRODUCTION; override allow_local_fallback también existe | Gate de cliente no excluye staging por sí solo; pruebas de función real lo reproducen con settings sintéticos |
| MedSupplier ADMIN_APPS_INTEGRATION.ALLOW_LOCAL_FALLBACK | client.py: flag y no IS_PRODUCTION, también override explícito | Staging no está excluido; necesario guardrail. Denegaciones de negocio no deben reemplazarse con fallback, errores de servicio sí pueden usarlo si habilitado |
| Session auth / CSRF / DEBUG | ISO añade SessionAuthentication en desarrollo; MedSupplier configura exenciones API | Revisar rutas y perfil efectivo. No asumir que flags nominales bastan; requiere cobertura HTTP/CSRF |
| ModelBackend heredado | AUTHENTICATION_BACKENDS lo incluye; AdminAppsAuthBackend.authenticate lanza PermissionDenied y get_user retorna None | LoginSerializer actual usa central_auth; la mera presencia de ModelBackend no demuestra tokens locales sin autoridad |

Búsqueda sobre integración, settings, autenticación y API; tests/laboratorios contienen mocks explícitos. Se separaron mocks de pruebas de rutas operativas. No se afirma análisis exhaustivo de todos los posibles caminos dinámicos de cada repositorio.

## Contrato actual y guardrail requerido

central_auth verifica configuración, familia/algoritmo/firma, issuer, audience, cliente, producto, tenant, expiración, lifecycle y respuesta de introspección. Denegación central 400/401/403/404 se traduce en AuthenticationFailed; indisponibilidad/malformación genera 503 sanitizado. No imponer un 403 universal si el contrato real distingue 401/403/503. ISO entrega cookies; el JSON histórico access/refresh no es el contrato actual de ese login. Scopes/autorización y revocación requieren pruebas separadas de mera firma.

**Sí se necesita un guardrail obligatorio en el arranque de cualquier staging futuro.** Debe rechazar flags inseguros, settings de test, SQLite no autorizado, DEBUG, fallback y bypass; validar todos los aliases DB, secretos y autoridad SSO internos; impedir que un override de llamada reactive fallback. Primero están reproducidos los riesgos en funciones extraídas del AST sin importar settings ni Django. No se corrigió código de aplicaciones activas, pues una modificación en sus checkouts puede afectar reinicios automáticos. Implementación e integración del guardrail en copias aisladas sigue BLOCKED por capacidad/autorización; la herramienta preparada es un validador offline de plan, no el guardrail desplegado.

## Herramienta entregada

`python3 -B tools/staging_recovery/preflight.py tools/staging_recovery/plan.example.json`

Solo lee el manifiesto sintético y capacidad de disco; no lee .env reales, no abre red ni DB, no ejecuta shell/systemctl/migraciones. Exige tres productos, destinos/roles declarados distintos, rutas dedicadas, puertos loopback no privilegiados, flags booleanos explícitamente deshabilitados, secretos nuevos y autoridad HTTPS interna. Rechaza strings ambiguos, montajes y dependencias compartidas. Los nombres staging de un manifiesto **no acreditan origen ni permisos de la DB**.

Salida actual: plan FAIL por capacidad; execution BLOCKED. Incluso un plan estructuralmente válido retorna BLOCKED y exit 2 hasta aportar acreditación real por un flujo futuro revisado. No contiene una opción para saltarse gates mediante booleanos de autoaprobación.

La plantilla no contiene secretos. Los secretos futuros deben generarse nuevos en directorio privado no versionado o almacén local con ACL; comparar procedencia sin revelar valores ni copiar credenciales existentes. Verificar que logs no incluyan bodies de login, tokens, keys, passwords, headers ni URLs de recuperación; los clientes actuales tienen rutas de logging de excepciones que requieren prueba de sanitización con errores controlados.

## Prueba futura de aislamiento DB, antes de conectar aplicaciones

Requerir recibo de creación del cluster exclusivo, identificación del dueño, data_directory/socket/puerto bajo raíz dedicada y hora/identificador de creación. Solo después de acreditar ese endpoint se permite una conexión read-only de mantenimiento para contrastar system_identifier, current_database, session_user/current_user, pg_roles y ACL: roles sin privilegios globales, CONNECT limitado a su DB, sin permisos cross-product, aliases auxiliares explícitos y test runner incapaz de tocar bases activas. Un alias, nombre o password diferente no sustituye esa prueba. No se entrega un script que conecte indiscriminadamente al cluster existente.

## Secuencia de startup, shutdown y rollback — diseño, no ejecutable autorizado

1. Obtener capacidad y autorización explícita de creación; revisar SHA y copias aisladas, manifiesto y procedencia de secretos.
2. Provisionar recursos nuevos con registro de propiedad; acreditar DB/roles/montajes/red/TLS; ejecutar preflight sobre configuración efectiva antes de aplicaciones/migraciones.
3. Revisar migrate --plan, aplicar únicamente sobre DB acreditadas y ejecutar pruebas/fixtures sintéticos. Iniciar manualmente los procesos propios con PID y directorio registrados; ningún systemd persistente existente.
4. Health/smokes con cliente que nunca imprima credenciales y timeout acotado; --no-fallback obligatorio; pruebas positivas y negativas separadas.
5. Shutdown únicamente por PID/identidad del proceso creado, nunca pkill genérico ni systemctl sobre servicios existentes. Cerrar conexiones y preservar evidencia sanitizada.
6. Rollback: detener solo recursos propios y volver a snapshot/versión staging previamente validada; no revertir bases compartidas ni borrar directorios por patrón. Destrucción solo de recursos acreditados y autorizados.

Scripts operativos de comprobación SQL, arranque/parada, health y smoke quedan **BLOCKED**, no listos: falta arquitectura ejecutable con capacidad, TLS privado y autorización de creación. No se oculta esta limitación mediante scripts genéricos peligrosos.
