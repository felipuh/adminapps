# Dictamen enterprise de recuperación y aislamiento

**GO WITH RESTRICTIONS para la preparación de staging. NO GO para reutilizar los servicios/bases existentes como staging.** No existe staging nuevo autorizado, aislado y probado. No se declara GO productivo.

## Estados separados

- GO histórico local: antecedente aportado; no recertificado aquí.
- Checkouts actuales: trazabilidad reconstruida; cambios SSO sustantivos. 1007 casos offline PASS y un fallo de compatibilidad del intérprete ISO preservado en evidencia; no equivalen a toda la aplicación PASS.
- Systemd: AdminApps/MedSupplier activos, sin certificar seguridad efectiva; ISO reiniciándose por configuración SQLite rechazada. Dependencias ISO/MedSupplier compartidas y Django fuera del pin.
- Staging: diseño/preflight preparados parcialmente; ejecución BLOCKED por capacidad, acreditación de aislamiento y autorización. NO GO para reutilizar DB/servicios existentes.
- Producción: no autorizada, no evaluada ni modificada.

## Riesgos por prioridad

**P0:** aislamiento insuficiente para admitir infraestructura actual: consumidores apuntan a los mismos destinos/usuarios PostgreSQL configurados, sin acreditación de finalidad/permisos. Recuperación debug ISO permite satisfacer su comprobación local con X-Forwarded-For falsificado cuando el bypass está habilitado; reproducción offline positiva. No se ejercitó endpoint real ni se demostró emisión efectiva de reset/login token. Mantener NO GO para cualquier perfil que habilite esa ruta hasta corregirla y probarla en copia aislada.

**P1:** disco ~150 MiB; ISO reinicia por SQLite fuera de settings_test; Django 6.0.6 compartido frente a pin 4.2.22, con fallo reproducido de carga de modelos; guard de fallback no excluye staging explícitamente; falta TLS privado compatible con SSO DEBUG=false; no hay guardrail instalado de configuración efectiva ni prueba de SQL/ACL/RLS/HTTP completo.

**P2:** evidencia histórica no corresponde al contrato actual, AdminApps tiene historia sanitizada sin ancestro común, estado de memoria de workers no vinculado a SHA, auditoría de logs acotada y sizing pendiente. Ausencia de fallos en suites focalizadas no resuelve estos puntos.

## Cambios de esta entrega

Solo documentación, inventario sanitizado y herramienta offline `tools/staging_recovery/`: preflight de plan, plantilla sin secretos y tests. No modificación de código runtime, units, settings ni .env reales. No se instalaron dependencias ni se crearon servicios/DB/clusters/volúmenes. El guardrail es una política comprobada offline, pendiente de integración en copias aisladas.

Se prepara un commit atómico local de este objetivo en AdminApps; el SHA definitivo se informa en la entrega para evitar autorreferencia. No se mezclan cambios runtime de otros productos. Los dos consumidores permanecen intactos. Sin push. Los tres HEAD iniciales fueron confirmados contra el remoto de sus ramas activas; el commit documental/de herramientas quedará localmente por delante.

## Próximo objetivo concreto

Habilitar un área de staging con capacidad suficiente y autorización explícita de creación, fuera de recursos activos. A continuación: copias de código revisadas por producto, dependencias fijadas, guardrail integrado y tests de recuperación/fallback; cluster nuevo acreditado, roles/DB/aliases independientes, secretos propios y TLS interno verificado; luego matriz completa de check/migraciones/tests/smokes/login positivo-negativo. No cambiar .env del servicio ISO ni su intérprete como reparación incidental.

La aprobación futura debe identificar almacenamiento/host y alcance de creación de procesos efímeros, DB/roles y TLS privado. No autoriza operar servicios existentes. La política de esta solicitud exige confirmar autorización antes de arrancar staging; esta entrega no la presupone.

## Límites respetados

No sudo; no start/stop/restart/enable/disable; no cambios de units; no mutación de DB o entitlements; no cambios de .env reales; no secrets/tokens/passwords/keys publicados; no dependencias globales/compartidas modificadas; no reset/force push/reescritura. No dominio, DNS, certificados, HTTPS público, Nginx público, Certbot, deploy productivo, merge, tag ni release. No staging arrancado.

Documentos de soporte: `STAGING_ISOLATION_ASSESSMENT_2026-10-29.md`, `STAGING_SECURITY_PREFLIGHT_2026-10-29.md`, `STAGING_EXECUTION_MATRIX_2026-10-29.md`. Evidencia en `docs/evidence/staging-recovery-2026-10-29/`.
