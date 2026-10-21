# REC-SSO-02 — Security Hardening & Controlled Remediation

2026-10-14, America/Costa_Rica. Repositorio `/home/felipe/proyectos/adminapps`.
Baseline: `b144b2505659ad39f756b9bc4530a7f24fe8c3ad`.

## A. Executive Verdict

**FAIL para cierre de seguridad; PASS para remediación local acotada.** Se corrigió
introspection: revalidación de usuario/membresía/organización, tenant obligatorio,
issuer del emisor actual y errores DB sanitizados sin concesión de acceso.
**BLOCKED**: legacy con 2FA, audience/clientes, scopes y rol obsoleto, decisiones
comerciales, esquema y validación operacional. **No Production Ready.**

La nueva suite tiene **32 pruebas: antes 10 PASS / 22 FAIL; después 23 PASS / 9 FAIL**.
Las 20 pruebas del grupo local pasan; las 3 de contratos de consumidores pasan;
las 9 de decisiones pendientes siguen fallando. Además, **21/21 pruebas offline
2FA existentes PASS**. Son pruebas unitarias con dobles, no E2E ni una repetición
de las 33 aserciones históricas. No hay errores de ejecución en la suite definitiva.

No se ejecutaron commits, push, deploy, migraciones, cambios de esquema, RLS,
grants, fixtures persistentes, bootstrap, servicios, autenticaciones reales ni
conexiones externas/DB. No se modificaron contratos ni archivos de consumidores.
Los cambios previos se preservaron; ver B y evidencia de integridad final.

Gobernanza preservada:

- **S3-IMP-01 = BLOCKED_PENDING_AUTHORITY**.
- **S3_DECISION_02A_NOT_CLOSED**.
- **PHASE31_5 = EXECUTION_HELD**.
- **REC-2FA-04 preservado**: se archivó su cierre como antecedente, sin adjudicar
  un nuevo PASS E2E ni reabrir sus decisiones.

## B. Baseline Integrity

**PASS.** HEAD coincide con la baseline. Rama activa
`hardening/p0-p1-enterprise-readiness`, ahead 6 frente a la referencia local de
origin; no se hizo fetch. Otras ramas locales: `development` y
`hardening/p0-enterprise-readiness-20260702`. Un único worktree, en este repositorio.
Índice inicialmente limpio; no se realizaron operaciones de staging.

Cambios preexistentes: `backend/config/settings.py` (+8/-1, inclusión financiera
y selección del backend de pruebas), `backend/apps/financial/`,
`backend/scripts/s3_isolation_host_lab.sh`, `backend/scripts/tests/`, verificadores
financieros y `docs/financial/`. No se editaron ni ejecutaron esas herramientas.
No se encontraron AGENTS.md aplicables en AdminApps ni sus directorios padre;
se leyó el de ISO Smart para la revisión de sus consumidores.

[Git inicial](evidence/baseline-git.json) y
[manifiesto inicial](evidence/baseline-files.json) cubren **15.530 archivos regulares
listados por Git como tracked o untracked no ignorados**, con SHA-256. Ignored y
symlinks no están cubiertos por ese manifiesto; no se afirma integridad byte a byte
de secretos o archivos fuera de él. La comparación final permite solo el cambio
de producción `backend/apps/integration/sso_views.py`; evidencia nueva y scripts
se inventarían aparte. Ver [integridad final](evidence/integrity-final.json) y
[Git final](evidence/git-final.json).

Resultado: **15.529 archivos de baseline intactos y un cambio autorizado**. El
primer comparador marcó ocho symlinks de entornos virtuales como nuevos porque no
repitió la exclusión del manifiesto inicial; se corrigió el alcance, sin cambiar
fuentes. Son symlinks tracked sin cambios en Git. Se conserva el intento y la
[corrección del comparador](evidence/integrity-harness-correction.json).

La evidencia temporal **sí existe** en `/tmp/adminapps-rec-sso-01-_fpvp5km` y
`/tmp/adminapps-rec-2fa-04-9kwykcss`. Se conservaron copias del informe, resultados,
comparación de esquema e integridad REC-SSO-01, y cierre REC-2FA-04, con
[hashes de procedencia](evidence/antecedent-hashes.json). Los enlaces internos del
[informe histórico](evidence/REC-SSO-01/REPORT.md) conservan su contexto original:
no todos sus archivos fueron copiados; no son evidencia nueva de esta campaña.
No se ejecutaron los scripts de DB o laboratorio históricos.

## C. Tests Before Fix

**FAIL reproducido antes del parche**:
[resultados](evidence/tests-before.json), [log](evidence/tests-before.log).
32 métodos, 10 PASS y 22 FAIL. Un método puede tener varios subcasos: unittest
reporta 33 fallos de aserción, que no equivalen a 33 métodos. Cero intentos de red
y DB; cero errores del harness en esta ejecución válida.

| Familia | Evidencia previa | Clasificación |
| --- | --- | --- |
| Legacy con 2FA habilitado | `test_legacy_2fa_requires_second_factor`: valid sigue true | FAIL; transición A pendiente |
| Usuario revocado/eliminado | `test_live_user_revocation`, `test_deleted_user` | FAIL |
| Membresía revocada/eliminada y org suspendida | `test_live_membership_revocation`, `test_deleted_membership`, `test_live_organization_revocation` | FAIL |
| Tenant ausente/ajeno; identidad inválida | `test_missing_tenant`, `test_foreign_tenant`, `test_missing_subject`, `test_invalid_identifiers` | FAIL |
| JWT issuer incorrecto/ausente | `test_wrong_issuer`, `test_missing_issuer` | FAIL |
| Audience incorrecta/ausente | DecisionTests correspondientes | FAIL; C pendiente |
| Scopes viewer/auditor y entitlement denegado | `test_viewer_and_auditor_never_receive_write_scope`, `test_write_scope_requires_entitlement` | FAIL; D pendiente |
| DatabaseError | API key lookup/last_used, usuario, membresía y productos | FAIL: error escapa o consulta viva ni siquiera ocurre |
| Rol snapshot, trial, starts_at y suscripción ajena | Cuatro escenarios de decisiones | FAIL; B/E/F/G pendientes |

El primer intento falló en bootstrap por una ruta Python incorrecta, **antes de
Django setup**; se conserva [log](evidence/harness-bootstrap-error.log). Se corrigió
el path, se obtuvo el resultado anterior y solo después se modificó producción.
No se contó el error de bootstrap como vulnerabilidad. El harness se trasladó
después a `backend/scripts/rec_sso_02_offline.py` para evitar que el discovery de
tests Django cargue una configuración standalone. La lógica de pruebas se mantuvo.

## D. Applied Local Fixes

Único archivo de producción editado:
`backend/apps/integration/sso_views.py` (+42/-1; 43 líneas de diff stat).
[Diff aplicado](evidence/applied-local.patch).

| Cambio | Contrato existente / por qué compatible | Límite |
| --- | --- | --- |
| Exige UUID de usuario y tenant | Identidad canónica UUID y login SSO siempre ligado a una membresía | No autoriza al servicio llamador para cualquier tenant; H pendiente |
| Relee User activo y UserOrganization activa con organización active | Mismos predicados que login; AdminApps es autoridad de identidad/acceso; introspection representa estado vivo | No revoca por rol, lock temporal, logout o versión de sesión |
| Rechaza issuer ausente/ajeno | `_build_token_pair_unchecked` ya emite SMART3AI_SSO_ISSUER | Solo este endpoint; no cambia verificación JWT global ni consumidores |
| Captura DatabaseError alrededor del decorador de API key y cuerpo | Denegación ante indisponibilidad de autoridad | 503 con active=false y mensaje genérico; no cambia otros endpoints |

Identidad/membresía/tenant/issuer inválidos retornan HTTP 200 `{"active": false}`;
API key ausente/inválida conserva 401; ausencia de token conserva 400. Una
introspection válida mantiene exactamente sus campos anteriores y relee productos.
No sustituye fallo por productos vacíos o permisos positivos. El error DB no expone
detalle interno. El orden permite atrapar fallos en `last_used` además de lecturas.

Fuentes contractuales: `docs/PRODUCT_NEUTRAL_ADMINAPPS_CONTRACT.md` (identidad,
autoridad y reglas de producto), `docs/ADMINAPPS_SAAS_PRODUCT_OPERATIONS.md`
(snapshots y consulta viva), login/verificación en `sso_views.py`,
`get_user_by_id` en integration/views.py y modelos de users/organizations.

No se editaron login, emisión, consumo transaccional de desafíos, backups, refresh,
settings, modelos, serializers, migraciones, frontend ni la implementación financiera.

## E. Tests After Fix

[Suite completa](evidence/tests-after.json): **23 PASS / 9 FAIL**, exit code 1
intencional por hallazgos abiertos; [log](evidence/tests-after.log).
Los fallos no se convierten en expectedFailure ni skip.

| Validación | Resultado | Alcance |
| --- | --- | --- |
| 20 pruebas LocalFixTests | PASS | JWT real sintético, RequestFactory, ORM/autenticación/persistencia sustituidos |
| 3 pruebas ConsumerTests | PASS | Código real local de clientes, transporte y resolución tenant sustituidos |
| 9 pruebas DecisionTests | FAIL | Legacy; audience ausente/ajena; 2 casos scopes; rol obsoleto; trial; inicio; vínculo de suscripción |
| 21 pruebas existentes 2FA | PASS | [Log](evidence/2fa-regression.log); no DB, concurrencia ni E2E nuevo |
| Django system checks aislados | PASS | [Log](evidence/offline-checks.log); settings sintéticos y databases=[] |
| Lint sintaxis/indentación y git diff --check | PASS | compile en memoria, tabnanny y whitespace; sin generar bytecode |
| Ruff/Flake8/Pyflakes/Pycodestyle | NOT_TESTED | No disponibles en intérpretes inspeccionados; no se instalaron paquetes |
| Proyecto completo bajo settings reales | NOT_TESTED | No se carga .env ni se arranca scheduler/servicios |
| Atomicidad real, migraciones, sesiones consumidor y aislamiento SQL | BLOCKED | Requieren autorización de infraestructura/datos |

El grupo local conserva firma/expiración/tipo de token, API key requerida,
entitlement denegado, productos vivos, error previo a emisión y desafío 2FA sin
entrega de tokens. La suite anterior 2FA añade contratos de TOTP/backup, canales,
rechazo de replay mediante dobles y errores de emisión. Eso no sustituye pruebas
PostgreSQL de locks/commit ni las pruebas reales históricas REC-2FA-04.

Comandos reproducibles desde la raíz (dependencias ya existentes, sin instalación):

```bash
backend/.venv/bin/python -B backend/scripts/rec_sso_02_offline.py --group local
backend/.venv/bin/python -B backend/scripts/rec_sso_02_offline.py --group consumers
backend/.venv/bin/python -B backend/scripts/rec_sso_02_offline.py --group decisions
backend/.venv/bin/python -B backend/scripts/rec_sso_02_offline.py
backend/.venv312/bin/python -B backend/scripts/rec_sso_02_2fa_regression.py
backend/.venv/bin/python -B backend/scripts/rec_sso_02_checks.py
git diff --check
```

`decisions` y la suite completa deben terminar con código 1 mientras no cambien los
contratos/implementación. El runner opcional `--output RUTA` guarda JSON de evidencia;
no sobrescribir `tests-before.*`. El script de checks actualiza solo el grafo JSON
local de evidencia. Claves, passwords y UUIDs son sintéticos. Los guards de red y
DB se instalan antes de Django setup en el harness nuevo. No se importan settings
reales ni .env. Las cantidades reportadas son intentos bloqueados, ambos en cero.

## F. Cross-Product Compatibility

| Contrato | ISO Smart | MedSupplier | Conclusión |
| --- | --- | --- | --- |
| Legacy password → valid/user/current_organization/current_role | integration/client.py:365 y backends.py:67 | integration/client.py:479 y backends.py:67 | Sigue vigente; bypass 2FA abierto, transición A bloqueada |
| Tenant canónico + código de producto en validación | ISO_SMART | MEDSUPPLIER | PASS de contrato aislado, no proyección DB real |
| Outage y denegación explícita de producto | fail_closed; sin fallback positivo | fail_closed; sin fallback positivo | PASS de unidad; no acredita settings desplegados |
| JWT local SIMPLE_JWT | Sin ISSUER/AUDIENCE configurados en fuente revisada | Igual | C requiere coordinación; no se cambió su autenticación |
| Introspection activa | Esquema preservado | Esquema preservado | PASS del servidor aislado; no consta uso E2E desplegado |

Se revisaron ambos backends/clientes/settings localmente; solo se importaron los
clientes, con transporte sustituido. [Fuentes y hashes](evidence/consumer-sources.json).
Las pruebas prueban denegación y construcción de petición, no login real ni
sincronización de perfiles. Los claims continúan siendo snapshots y los productos
requieren validar `access_allowed`; `active=true` no concede acceso a todo producto.

La comprobación estricta de issuer afecta tokens ajenos al emisor SSO documentado;
si un despliegue usa introspection para otros emisores, su inventario/aceptación
es un gate previo al despliegue. El código local demuestra compatibilidad del
formato, no equivalencia de configuraciones desconocidas.

## G. Proposed Contract Decisions

[Decisiones A–H](DECISIONS.md) y [nueve diffs NO APLICADOS](proposals/manifest.json).

| Decisión | Dominio | Estado |
| --- | --- | --- |
| A. Denegar/deprecar legacy 2FA o adaptar contrato versionado | Técnica + transición de ambos productos | BLOCKED |
| B. Rol, sesiones, refresh, SLA de revocación/caché | Técnica | BLOCKED; relectura básica aplicada |
| C. Emisor, audience y registro de clientes | Técnica/identidad | BLOCKED; issuer de introspection aplicado |
| D. Matriz rol × scopes × entitlement × producto | Técnica con autoridad de producto | BLOCKED |
| E. Trial sin suscripción versus suscripción obligatoria | Comercial; ejecución técnica posterior | BLOCKED |
| F. Fecha efectiva y fronteras de vigencia | Comercial y técnica temporal | BLOCKED |
| G. Dueño/beneficiarios de suscripción | Comercial y arquitectura de datos | BLOCKED |
| H. Principal y permisos de API keys | Técnica y operación de identidad | BLOCKED |

G/H tienen diffs **contractuales**, no implementación especulativa de ownership,
schema o permisos. Los otros candidatos son diffs Python con sintaxis verificada,
runtime NOT_TESTED. No representan aprobación ni una solución completa para
composición, transición de datos o despliegue. No hay nuevas autoridades designadas.
Los nueve diffs pasan `git apply --check` individualmente, sin aplicarlos;
[resultado](evidence/proposal-checks.json).

## H. Targeted Migration Readiness

[Plan acotado](MIGRATION_READINESS.md): dependencias, tablas/columnas, precondiciones,
riesgos de datos, backup, rollback y aceptación para users.0004 e integration.0006.
**PASS de revisión de archivos/grafo; BLOCKED de ejecución; NOT_TESTED del estado
DB actual.** La metadata histórica se conserva sin convertirla en inspección nueva.

No se incorporan organizations.0004, integration.0007 ni financial. No se declara
que `organization_product_entitlements` necesite reparación. La reversión de
users.0004 puede destruir estado antirreplay; la de integration.0006 no reconstruye
plaintext ni preserva por sí sola revocaciones/auditoría. El backup no está probado
en esta campaña y no se hizo un reverse de migración.

## I. Remaining Blockers

- **FAIL:** SSO-01 legacy 2FA; SSO-03 audience/confianza global; SSO-05 scopes;
  rol snapshot en SSO-02. Las tres discrepancias comerciales son decisiones
  pendientes, no exploits HTTP demostrados.
- **PASS local parcial:** SSO-02 usuario/membresía/org/tenant; SSO-03 issuer solo
  en introspection; SSO-04 DatabaseError solo dentro de este endpoint.
- **BLOCKED:** atribución del HTTP 500 histórico al runtime exacto, drift de
  esquema, anti-replay/concurrencia reales, refresh/logout y sesiones de productos.
- **BLOCKED:** aislamiento operacional/RLS y alcance de API keys; no se modifican
  aunque el informe anterior haya identificado carencias.
- **NOT_TESTED:** IdP externo, OIDC/SAML, state/nonce de navegador, PKCE, TLS,
  rate limiting real y despliegues de consumidores.

La consulta viva no es revocación permanente: reactivación puede revalidar un token
no expirado; persisten ventanas entre consulta y uso. Estas limitaciones son B,
no deben resolverse devolviendo permisos ante fallos.

## J. Human Approval Gates

1. Autoridades verificables de seguridad/identidad y ambos productos adjudican
   A–D/H, aceptan errores, versiones, transición, criterios y rollback.
2. Autoridad comercial/facturación adjudica E–G; datos/arquitectura definen el
   modelo y las migraciones que procedan, sin asumir exclusividad de suscripción.
3. DBA/operaciones y autoridad de cambio aprueban target, backup restaurable,
   plan exacto de los dos targets, locks/corte, rollback y pruebas con datos
   sintéticos. Cualquier otra migración necesita revisión y autorización separadas.
4. Autorizar explícitamente laboratorio/E2E y, posteriormente, commit/push/deploy
   si se desean. Ninguna autorización se concede en este informe.

No hace falta aprobación adicional para revisar los artefactos locales ya
preparados. Ningún gate de REC-SSO-02 libera S3-IMP-01 o PHASE31_5.

## K. Recommended Next Action

Revisar el [diff local](evidence/applied-local.patch) y adjudicar primero **A**
(bypass 2FA de legacy), **C** (confianza cliente/audience) y **D** (scopes), junto
con B para la revocación de roles/sesiones. Registrar decisiones y aceptación de
ISO Smart/MedSupplier antes de aplicar candidatos. En paralelo, someter el plan
de los dos targets de migración al gate humano de DB. Después, y solo con
autorización explícita, ejecutar laboratorio desechable y pruebas integrales.
