# Continuación de auditoría Git LAB03 — 2026-10-20

Estado: **RAMAS ORIGINALES RETENIDAS; PUBLICACIÓN AISLADA VERIFICADA**. `PRODUCTION_READY = FALSE`.

El archivo `AUDITORIA_GIT_LAB03_2026-10-20.md` citado en el traspaso no estaba disponible en el workspace ni en `/tmp` al iniciar esta continuación. Se usaron el reporte LAB03, los registros históricos conservados y los objetos Git locales. Este documento no sustituye una auditoría de código completa de los commits pendientes.

## Estado inicial y atribución

No se observaron procesos Git concurrentes. Los tres índices estaban vacíos. Inventario inicial `tracked unstaged / untracked`: AdminApps `23/337`, ISO Smart `22/38`, MedSupplier `14/25`. HEAD: AdminApps `3ef6d2145293956d1a4838673d8aab62d85af410`, ISO Smart `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e`, MedSupplier `6a5fd0366841d0511901e0f41a98dc1d801b9f4f`.

Los siete commits locales AdminApps y los dos ISO Smart declaran autor y committer Felipe; esto identifica la procedencia Git, pero por sí solo no acredita revisión de seguridad ni autorización de publicación. `2e92e48` también declara coautoría de Copilot. El reporte LAB03 atribuye el commit `3ef6d214` a los dos cambios de orden de rutas y tres pruebas de resolución. Sus cuatro archivos y el diff se contrastaron con el reporte; no incluyen evidencia privada. Los seis commits AdminApps anteriores se separan en dos de medición/costos de IA (`1e7f1d9`, `42f007d`) y cuatro de autenticación (`2e92e48`, `56bd373`, `418a516`, `b144b25`). Los dos ISO Smart (`f19fbd3`, `0ce01df`) pertenecen a medición/costos/entrega de IA. El inventario por commit y `git show --check` pasaron. No se declara una rama publicable por inferencia de autoría.

### Revisión de los ocho commits anteriores

| Repositorio / commit | Alcance verificado | Resultado de revisión |
| --- | --- | --- |
| AdminApps `1e7f1d9` | Endpoint de ingestión y dashboard, modelo/migración, UI, tests | **RETENIDO**: dashboard usa `IsAdmin` (incluye rol `admin` de tenant) con queryset de todas las organizaciones; test solo cubre un tenant. Un admin puede consultar uso/costo de otros tenants. No se mezclará la reparación financiera con IAM. |
| AdminApps `42f007d` | Endurecimiento de productor, transacción y conflicto de replay | **RETENIDO** con el commit anterior; no corrige el alcance del dashboard. |
| AdminApps `2e92e48` | Refresh frontend y contexto de sesión | 41/41 tests Node PASS; transporte de refresh separado, generación y limpieza revisados. |
| AdminApps `56bd373` | Paso 2FA frontend | Challenge no se trata como sesión final; revisión estática de diff. |
| AdminApps `418a516` | Consumo 2FA transaccional, antirreplay, migración 0004 y rutas | Suite histórica sin adaptar: 11 FAIL/21 con IAM actual. Sucesora R1 ejecuta los mismos 21 métodos: 21/21 PASS offline, DB/red 0. No equivale a migración desplegada. |
| AdminApps `b144b25` | UI de códigos de respaldo | Revisión estática de diff; build frontend PASS. |
| ISO Smart `f19fbd3` | Medición/costos, migración RLS, Value Discovery y documentos | **RETENIDO**: incluye un reporte de validación con consumo/saldo real en un repositorio público. Tratarlo como evidencia privada antes de publicar. |
| ISO Smart `0ce01df` | Entrega por outbox, reintentos y permiso SQL de worker | **RETENIDO** junto con `f19fbd3`; entrega deshabilitada por defecto en código, pero no se certifica esquema ni worker. |

El build AdminApps y los tres tests de rutas pasaron. El análisis de paths de los diffs no halló bloques de clave privada ni credenciales literales; la búsqueda por patrón no prueba ausencia total de secretos. El fallo de aislamiento del dashboard se desprende del código del commit y de `IsAdmin`; requiere prueba adversarial con dos organizaciones y corrección separada antes de publicar la historia financiera.

## Once excepciones históricas por consumidor

Las suites Decision A de ISO Smart y MedSupplier conservaron `9 PASS / 0 FAIL / 11 ERROR` en los registros del 2026-10-19. Los errores proceden de fixtures que no proveen la confianza C/H exigida. La suite C/H antigua, ejecutada en esta continuación, también produjo `11 ERROR / 28` en cada consumidor: sus pruebas no incluyen el estado durable `sid/sg/av/auth_time` exigido por B. **Ambas suites siguen rojas y no se reclasifican.**

La sucesora `tests_b_offline.py` pasó `35/35` y `tests_d_session_offline.py` pasó `36/36` en **cada** consumidor, con cero intentos de DB/red según sus guardas. B hereda las pruebas C/H y agrega fixtures de ciclo de vida; D agrega permiso granular con sesión firmada. Mapeo de cada excepción Decision A, aplicable por separado a ISO Smart y MedSupplier:

| Método Decision A en ERROR | Evidencia sucesora offline por consumidor | Límite |
| --- | --- | --- |
| `test_challenge_is_not_session` | B `test_challenge_and_verify_flow` | No navegador/HTTP |
| `test_complete_central_login` | B `test_valid_login_real_signature_before_projection` | Transporte/ORM simulados |
| `test_cross_tenant_binding_rejected` | B `test_requested_tenant_cannot_be_substituted`, `test_tenant_switch_and_uuid_binding` | Sin DB real |
| `test_current_session_live_revocation_and_role` | B `test_refresh_live_authority_and_revocation`, `test_session_profile_role_tenant_and_subject` | Autoridad central simulada |
| `test_failed_binding_mints_no_local_token` | B `test_no_email_takeover_without_subject_binding`, `test_projection_rejects_email_and_slug_collision` | Sin persistencia real |
| `test_missing_profile_or_schema_fails_sanitized` | B `test_schema_failure_sanitized` | Sin esquema instalado |
| `test_old_refresh_never_issues_access` | B `test_central_generation_binding_and_legacy_rejection`, `test_refresh_live_authority_and_revocation` | Sin carrera SQL |
| `test_owner_policy_cannot_be_bypassed` | B `test_owner_policy` | Política comercial no certificada |
| `test_refresh_bound_by_central_expiry` | B `test_refresh_with_expired_embedded_proof_is_denied`, `test_rotation_cannot_change_authority_or_extend_expiry` | Sin corte desplegado |
| `test_transport_and_json_errors_are_sanitized` | B `test_transport_and_json_errors_are_sanitized`, `test_denial_does_not_allow_reuse_cached_authority` | Red real no probada |
| `test_verify_totp_or_backup_through_central` | B `test_challenge_and_verify_flow` | MFA central/DB real no probados aquí |

Este mapeo no afirma equivalencia exacta de todos los asserts antiguos. Identifica la ruta sucesora que prueba la propiedad relevante bajo el contrato nuevo y explicita sus límites. Los resultados históricos, incluidos los once errores de cada consumidor, permanecen visibles.

## Límite de publicación

Los refs remotos originales siguieron en `f39acc54f51dd5f2679a66e1cdaace9f80c22621` (AdminApps), `52bcdf65e70851480b1a729f5ded2e93774d05c7` (ISO Smart) y `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` (MedSupplier). Son ancestros de los HEAD locales; no hay divergencia. Las tres ramas remotas indican `protected=false` y la API pública de reglas efectivas devolvió lista vacía. Las ramas originales mezclan historia financiera con IAM o incluyen la evidencia privada ISO, por lo que **no se hizo push a ninguna rama original**. No se ejecutó migración, grant, activación de settings, DB compartida ni despliegue.

### Publicación aislada posterior

Tras revisar destinos sin ref previo y reglas efectivas vacías, se usó únicamente `git push origin HEAD:refs/heads/<rama>` normal. Los refs se leyeron de nuevo del remoto después:

| Repositorio | Rama nueva | SHA remoto verificado | Contenido |
| --- | --- | --- | --- |
| AdminApps | `audit/iam-isolated-20261020` | `fe671855ffae2893f6af48559e49a680e74c60b8` | Cinco commits reconstruidos desde el ancestro remoto: refresh, 2FA, rutas. Sin financiero ni evidencia. 21 MFA, 41 frontend, 3 rutas y build PASS. |
| AdminApps | `audit/financial-isolated-20261020` | `8e67dcb374301eb39b6ed03c78b0c4568bd40980` | Dos commits financieros originales más corrección separada: dashboard de todos los tenants exige superadmin. Seis tests PASS en DB de prueba local, incluido admin de tenant ante tenant ajeno. |
| ISO Smart | `audit/financial-sanitized-20261020` | `c441235ae63f8807206e0b185a83ee5d1b25311f` | Dos commits financieros reconstruidos; árbol igual al HEAD local original salvo el documento de consumo/saldo real excluido. Nueve tests SQLite PASS. |

Ninguna de estas ramas se integró a `development`, `main` ni `hardening/p0-p1-enterprise-readiness`; no se abrió PR ni se ejecutó deploy. MedSupplier no recibió commit ni push. Los worktrees originales conservan sus cambios no rastreados y los tres índices vacíos.
