# PostgreSQL / E2E readiness — NO EJECUTADO

Estado: BLOCKED_BY_EXTERNAL_DEPENDENCY. El mandato permite preparar migraciones,
no aplicarlas ni consultar bases compartidas. No se inició PostgreSQL, workers ni
servicios. Tests con RLock/ORM simulado solo verifican decisiones de aplicación.

Precondiciones del laboratorio: autorización nueva para PostgreSQL desechable,
DB dedicada, keyrings sintéticos de tres familias, clientes provisionados y roles
DB centrales exclusivos; READ COMMITTED; relojes controlados. No usar datos reales.
Migraciones: integration.0008 → 0009 → 0010 y sus dependencias users.0004,
products.0003 y subscriptions.0002. El estado Django se comprobó sin conexión;
SQL/PLpgSQL NO fue compilado ni ejecutado contra servidor.

| Caso real requerido | Procedimiento / evidencia que debe producir |
|---|---|
| Persistencia | Emitir, cerrar conexiones/proceso, volver a introspectar; misma identidad y generación |
| Rotación concurrente | Dos conexiones y barrera sobre misma generación: solo un commit ALLOW; anterior DENY |
| Logout vs rotate | Ambas órdenes, bloqueo deliberado: tras commit logout todas las pruebas DENY |
| Autoridad vs issue/introspect | Actualizar rol/credencial/membresía bajo conexión distinta; pausa antes de commit; comprobar orden de linearización y DENY posterior |
| ABA | Rol A→B→A, usuario active→inactive→active, cliente/credencial/MFA/tenant; token anterior siempre DENY |
| Bulk/M2M/SQL | QuerySet.update, bulk_update, relación tenants clear/remove, SQL directo autorizado sobre fixture; triggers y outbox confirman |
| Estado vigente | Usuario, membresía, cliente, principal, producto y MFA vivos; expiración después de obtener locks |
| Constraints | Generación positiva/única, estado+revoked_at, ventana temporal, challenge MFA único, FK PROTECT, identidad inmutable |
| Monotonía | Updates/reinicios/rollback no reutilizan generación publicada; ABA imposible por SQL |
| Fallos parciales | Falla de firma, fallo de outbox, desconexión antes/después commit; no respuesta con sesión sin commit ni recuperación de generación consumida |
| Deadlocks | MFA/user writes + fence + SSOClient updates; errores sanitizados y ninguna emisión parcial |
| MFA | Repetir REC-2FA-04 con PostgreSQL real; challenge consumido no restaurado ante emisión fallida |
| Policy hook | Revocación global autorizada MFA, no-superuser DENY, cambios pendientes de autenticación rechazados |
| Outbox | Commit indivisible, entrega duplicada, pérdida ACK, reintentos y evento tardío; watermark nunca baja |
| Reversión | Reverse 0010 revoca activos/deshabilita fence; reapply conserva contador; 0009 no se elimina |
| Concurrencia/carga | Fence global y callbacks outbox acotados; throughput/latencias y conexiones perdidas |
| Roles DB | Consumidores sin acceso a tablas IAM; rol no privilegiado no puede desactivar triggers ni resetear fence |
| HTTP real | Login/challenge/introspection/refresh/logout por ambos clientes y errores de red/timeout/redirección |
| Navegador | HttpOnly, Secure, SameSite, CSRF, cookies grandes, proxy real, pestañas concurrentes, formulario >300 s |
| Versiones mixtas | A↔CH↔B, tokens viejos y cambio de versión: no fallback permisivo; reautenticación explícita |
| Proyección/tenant | UUID inmutable, tenant switch con nueva autenticación, email collision y rol degradado |

Cierre durable solo tras resultados reproducibles de estas pruebas. No hay
aprobación implícita de ejecución, activación, secretos, despliegue ni rollback.
