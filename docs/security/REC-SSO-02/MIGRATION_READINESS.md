# REC-SSO-02 — Targeted Migration Readiness

Fecha: 2026-10-14, America/Costa_Rica. **BLOCKED para ejecución.** Este plan no
autoriza migraciones, servicios, datos persistentes, RLS, grants ni bootstrap.

## Evidencia y límites

Se inspeccionaron archivos de migración y metadata histórica de REC-SSO-01 del
2026-10-13. [Comparación archivada](evidence/REC-SSO-01/model-schema-comparison.json):
`users.0004` e `integration.0006` no estaban registradas en la DB examinada.
No se abrió una conexión DB nueva: el estado actual de esa DB es **NOT_TESTED**.
`organization_product_entitlements` existe y estaba correctamente definida; no
requiere reparación según la evidencia disponible.

[Grafo offline](evidence/migration-graph.json) generado con `MigrationLoader(None)`:
lee migraciones, no ejecuta operaciones ni consulta `django_migrations`. Es un
grafo de dependencias desde cero, **no** un plan contra una DB ni una afirmación
de cuáles se aplicarían hoy. No se ejecutaron `migrate`, `makemigrations`,
`showmigrations` ni `sqlmigrate`.

## users.0004_transactional_2fa

Fuente: `backend/apps/users/migrations/0004_transactional_2fa.py`.

**Dependencias:** directa `users.0003_remove_twofactorauth_backup_codes_and_more`;
cadena users.0001–0003, organizations.0001 y auth/contenttypes según el grafo.
La FK del challenge apunta al usuario swappable. No depende de integration.0006.

**Objetos afectados:**

| Tabla | Cambio |
| --- | --- |
| `two_factor_auth` | Añade `generation` UUID con default callable; `last_totp_counter` bigint nullable; `failed_attempts` positivo con default 0; `attempts_expires_at` datetime nullable. |
| `two_factor_challenges` | Nueva tabla: `nonce_digest` varchar(64) PK, `version`, `purpose`, `scope`, `generation`, `context_digest`, `issued_at`, `expires_at`, `consumed_at` nullable, `user_id` FK. |

No cambia entitlements, secretos cifrados ni códigos backup en este target.
`users.0003` sí removió campos anteriores: si no está aplicada, **detener** y
revisarla por separado; no incorporarla como reparación automática.

**Precondiciones:** confirmar DB/runtime/revisión/settings exactos sin imprimir
secretos; comprobar que 0003 está registrada y sus columnas reales coinciden;
confirmar ausencia de ejecución parcial de 0004; revisar tipos, PK, FK, índices,
tamaño de tabla, locks y versión de PostgreSQL/Django. La implementación 2FA exige
PostgreSQL y límite de commit fuera de una transacción envolvente. El harness dummy
no certifica ese requisito. Comparar checksums de migraciones con los aprobados.

**Riesgos de datos:** DDL puede bloquear autenticación; creación/backfill de
generation no equivale a probar unicidad por fila ni anti-replay. El protocolo
liga generation también al usuario/contexto; verificar su semántica en la DB real.
Al introducir contadores y desafíos, sincronizar la ventana de cambio con procesos
que ya usan 2FA. Fallo de emisión nunca debe restaurar factor/desafío consumido.

**Pruebas futuras posteriores:** metadata y ledger coinciden; nueva fila tiene
generation y contadores correctos; challenge expira y se consume una sola vez;
TOTP y backup no reutilizables; concurrencia de dos verificaciones; revocación de
usuario/membresía antes de consumo; rollback de transacción y commit visible al
emisor; error del emisor sin replay; regresiones REC-2FA-04. Solo en entorno y con
fixtures expresamente autorizados, nunca como efecto de un smoke contra datos reales.

## integration.0006_integration_api_key_lifecycle

Fuente: `backend/apps/integration/migrations/0006_integration_api_key_lifecycle.py`.

**Dependencias:** integration.0005 y usuario swappable `users.__first__`, que aquí
resuelve users.0001. Cadena integration.0001–0005 más sus dependencias auth/users;
no exige users.0004, integration.0007, organizations.0004 ni financial.

**Objetos afectados:**

| Tabla | Cambio |
| --- | --- |
| `integration_api_keys` | `key` pasa a nullable/blank manteniendo unique; añade `credential_id` nullable unique (32), `credential_hash` (255), `credential_format` (24), `fingerprint` (80), `status` (16), `revoked_at`, `rotated_at`, `replaced_by_id` FK nullable a sí misma. |
| `integration_api_key_audit_events` | Nueva PK bigint, `event_id` UUID unique, `action`, fingerprints anterior/nuevo, `service_name`, JSON metadata, created_at; FK nullable a actor y credenciales anterior/nueva. |

**Transformación de datos real:** `classify_existing_credentials` actualiza todas
las filas: `credential_format=legacy_plaintext`, `status=active` si is_active,
`revoked` en otro caso. No hashea ni rota las claves existentes; no afirmar que
esta migración elimina plaintext. El reverse de RunPython es **noop**.

**Precondiciones:** 0005 registrada y objetos reales coherentes; identificar
drift/parcialidad sin leer valores de keys; revisar nulos/duplicados por conteos,
FK y tamaño de tabla; bloquear aplicación ciega si hay columnas o credenciales
hashed creadas por otro proceso. Confirmar soporte para legacy/hash/fallback en
código y definir ventana sin rotación concurrente. No ejecutar el RunPython dos
veces ni usar `--fake` para ocultar drift.

**Riesgos de datos:** actualización masiva y locks; recategorización incorrecta
si ya existe drift con claves hashed; metadatos hash/fingerprint vacíos para
legacy no implican corrupción por sí solos. Código antiguo puede interpretar
mal el estado revoked/rotated o claves con `key=NULL`. El audit trail posterior
es dato de seguridad y no debe perderse por una reversión rutinaria.

**Pruebas futuras posteriores:** metadata/ledger, defaults, unique/FKs; inventario
por formato/estado sin exponer secretos; keys legacy activas/inactivas; creación
hashed, rotación atómica, rechazo de key anterior y auditoría; DB error en consulta
y en last_used sin concesión; fallback nunca resucita key revocada. Pruebas con
material sintético en target desechable autorizado, sin autenticación real en el
servicio existente.

## Backup y rollback — plan, no ejecutados

1. Obtener autorización de target y ventana. Guardar snapshot consistente y
   backup cifrado de DB completa (esquema, datos y `django_migrations`) más versión
   de código/configuración y referencias seguras al material de cifrado. Custodia,
   acceso y retención acordados; ninguna key ni secreto en el informe.
2. Verificar restauración en un clon aislado expresamente autorizado; registrar
   checksums, conteos y restricciones. No basta con que el comando de backup
   termine sin error. Esta verificación es **NOT_TESTED** en REC-SSO-02.
3. Antes de DDL, revisar un plan limitado para cada target. Si propone operaciones
   ajenas o reverse de migraciones posteriores, detener. No ejecutar `migrate`
   general. No reparar/seedear entitlements ni importar financial.
4. Si falla dentro de la transacción DDL, verificar rollback efectivo y ledger;
   no asumir que ocurrió. Preferir corrección hacia delante tras diagnóstico.
5. Si ya se aplicó users.0004 y se usó, no bajar a 0003: eliminaría contadores y
   challenges y podría habilitar replay. Mantener servicio de autenticación
   cerrado durante recuperación, preservar consumos y determinar invalidación
   de sesiones/desafíos bajo B. No restaurar una copia anterior al consumo sin
   compensar el riesgo de replay.
6. Si ya se crearon keys hashed tras integration.0006, no revertir a 0005:
   `key=NULL` puede impedir NOT NULL; se perderían hash/estado/auditoría y no puede
   reconstruirse plaintext desde hash. Restaurar solo bajo plan coordinado que
   reconcilie revocaciones y rotaciones posteriores; jamás reactivar una key
   revocada al restaurar datos anteriores. Reemitir/rotar requiere autorización.

**Gate de ejecución futuro:** DBA/operaciones + seguridad + autoridad de cambio
verificable aprueban target, backup probado, plan exacto, lock budget, corte,
rollback y pruebas; responsables de producto aprueban impacto. El drift histórico
de organizations.0004/integration.0007 se inventaría aparte, no se incorpora.
