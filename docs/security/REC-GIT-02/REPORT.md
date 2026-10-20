# REC-GIT-02 — Reconciliación de worktrees y checkpoints

Fecha: 2026-10-20, America/Costa_Rica. Alcance: AdminApps, ISO Smart y MedSupplier. Auditoría y publicación en ramas aisladas; sin merge, deploy, migraciones, grants, workers ni activación operativa.

`PRODUCTION_READY = FALSE` · `PHASE31_5 = EXECUTION_HELD` · `S3_DECISION_02A_NOT_CLOSED`.

## A. Inventario y denominadores

El inventario heredado `23/337`, `22/38`, `14/25` significa **archivos rastreados modificados sin stage / archivos no rastreados individuales**, usando `git status --porcelain=v1 -uall`. No son porcentajes. En los tres índices hay cero archivos staged, cero altas rastreadas y cero borrados. La suma es **459** archivos (360 + 60 + 39), no 463. La cifra 463 excede por cuatro la única base disponible; el informe anterior conserva exactamente esos seis contadores y no aporta cuatro rutas adicionales. No se atribuyen cuatro archivos ficticios ni se declara resuelta esa discrepancia histórica. El inventario posterior a los pushes sigue en 459 porque los worktrees originales se preservaron.

| Repositorio | Rama original y HEAD local | Rastreados modificados | No rastreados (`-uall`) | Stage |
| --- | --- | ---: | ---: | ---: |
| AdminApps | `hardening/p0-p1-enterprise-readiness` · `e4dac0a96dcb535ce1cbf9550d113aa18a6ec915` | 23 | 337 | 0 |
| ISO Smart | `hardening/p0-p1-enterprise-readiness` · `0ce01dff4d2ac9fdebb470e5fd746bd16ac38c8e` | 22 | 38 | 0 |
| MedSupplier | `hardening/p0-p1-enterprise-readiness` · `6a5fd0366841d0511901e0f41a98dc1d801b9f4f` | 14 | 25 | 0 |

AdminApps está 10 commits por delante de su ref `origin/hardening`; ISO Smart, 2; MedSupplier coincide con él. Ninguna rama original recibió push. `git diff --check` pasó en los tres worktrees originales.

## B. Publicado frente a exclusivamente local

Se verificaron con `git ls-remote` los tres refs previos: AdminApps `audit/iam-isolated-20261020` = `fe671855ffae2893f6af48559e49a680e74c60b8`, AdminApps `audit/financial-isolated-20261020` = `8e67dcb374301eb39b6ed03c78b0c4568bd40980`, e ISO Smart `audit/financial-sanitized-20261020` = `c441235ae63f8807206e0b185a83ee5d1b25311f`. El commit local `e4dac0a96dcb535ce1cbf9550d113aa18a6ec915` **no es ancestro de ninguno de los dos refs AdminApps**; tampoco son ancestros del HEAD original los commits aislados financiero e IAM. El ref ISO financiero aislado tampoco es ancestro del HEAD original ISO. Se trata de reconstrucciones o ramas hermanas, no de pushes de las ramas originales.

Dos ramas nuevas recibieron push normal y lectura posterior del SHA remoto:

| Repositorio | Rama | Commits nuevos (orden) | SHA remoto verificado |
| --- | --- | --- | --- |
| MedSupplier | `audit/medsupplier-sso-reconcile-20261020` | `085cf436ab3e25d1f88994f2f5388c411110fb5f` código; `38f822c022fa8e90e427f121e5d629a0d0e02996` contratos | `38f822c022fa8e90e427f121e5d629a0d0e02996` |
| ISO Smart | `audit/isosmart-sso-reconcile-20261020` | `737d4cd70ea43488f43a549aa19d7e717cbb3940` código; `42336a467f20e87b13a690c4d38fca972f3d5d07` contratos | `42336a467f20e87b13a690c4d38fca972f3d5d07` |

Se comparó el blob de **cada** archivo pendiente en los worktrees originales con los árboles de todos sus refs de auditoría publicados. Coincidencia exacta: AdminApps **0/360**, ISO Smart **32/60**, MedSupplier **32/39**. Restan sin blob idéntico remoto **395** archivos (360 + 28 + 7). La ausencia de coincidencia exacta no implica que un parche equivalente no esté publicado: por ejemplo, los árboles ISO y MedSupplier cambian un test para eliminar la dependencia del nombre del directorio, y MedSupplier omite del login una contraseña demo embebida. Los commits previos de IAM y finanzas publicaron trabajo de la historia local por ramas aisladas, pero no incorporaron ninguno de los 360 blobs actuales del worktree AdminApps.

## C. Segmentación y dependencias

- **AdminApps IAM/sesiones humanas:** código en `users` e `integration`, migraciones 0005/0006 y 0008–0010, pruebas y documentación REC-SSO. Las rutas ya publicadas en IAM son independientes del perfil SQL completo. **Control plane/rutas:** API, organizaciones, productos, suscripciones y billing. **SQL:** migraciones y `provision_iam_runtime.sql` requieren una decisión de roles y activación. **Seguridad/pruebas:** tres pruebas API nuevas y numerosos scripts/evidencias. **Finanzas/gobernanza:** `financial`, `docs/financial`, dos cambios de billing y scripts S3 se retienen separados de IAM.
- **ISO Smart:** autenticación, sesión, frontend, autorización Decision D y contratos técnicos en la nueva rama; 32 blobs coinciden. El resto comprende `foundation` (uso IA, guardrails, migraciones 0041/0042, tests), `backend/backend/settings.py`, documentos de autoridad financiera, informe D, grants y bloqueo comercial. No se copió código financiero a la rama SSO.
- **MedSupplier:** autenticación, sesión, frontend, autorización y tenant isolation, pruebas y contratos técnicos en la nueva rama; 32 blobs coinciden. Los siete sin coincidencia son `settings.py`, `LoginPage.jsx` original con demo embebida, el test Decision A original dependiente del path, el informe D, bloqueos comerciales y dos documentos de grants. La rama publicada retira el demo embebido y conserva el resto del login funcional.

Los cambios de autenticación y Decision D en cada consumidor se publicaron en un mismo commit de código porque las suites B/D y el mixin de autorización comparten módulos. Los contratos técnicos se publicaron en un segundo commit. Las ramas consumidoras dependen del contrato central AdminApps y de los grants/datos de sesión aún no activados; publicar el código no satisface esas dependencias runtime.

## D. Seguridad, artefactos y pruebas

Se añadió por allowlist explícita; no se usó `git add -A`. Los diffs staged pasaron `git diff --cached --check`. La revisión de patrones del contenido nuevo no halló bloques de clave privada, tokens de proveedor/cloud, importes financieros reales ni correos reales en los checkpoints de consumidores. Se observaron únicamente claves y credenciales sintéticas etiquetadas para tests. El análisis por patrones tiene límites: no certifica ausencia absoluta de secretos. Los cuatro OpenAPI JSON de cada consumidor se parsearon. Ni settings operativos, ni migraciones, ni grants, ni documentos de política comercial retenida entraron en esos commits.

| Árbol auditado | Resultados nuevos |
| --- | --- |
| MedSupplier aislado | B `35/35`, D `533/533`, D sesiones `36/36`, frontend B `3/3`, frontend A `4/4`, build PASS |
| ISO Smart aislado | B `35/35`, D `361/361`, D sesiones `36/36`, frontend B `3/3`, frontend A `4/4`, build PASS |
| AdminApps original, solo offline | B `43/43` PASS con DB/red simuladas; no certifica SQL/HTTP real |

Las suites históricas C/H de ambos consumidores siguen con **11 errores cada una** por fixtures previos al estado durable B. No se reclasifican como PASS; las sucesoras B/D pasan, pero son offline con red/DB guardadas. El veredicto `P0R2_LAB03_PARTIAL_WITH_EXPLICIT_BLOCKERS` permanece: LAB03 verificó `17/17` regresiones SQL seleccionadas y `3/3` pruebas de rutas históricas, pero reveló `42501` legítimos en control plane, facturas/billing y Django Admin. Un commit no corrige esas incompatibilidades.

Los 337 archivos no rastreados AdminApps incluyen 245 en `docs/security` y 29 en `docs/financial`; por extensión, 128 JSON, 20 CSV, 17 patch y 3 diff. Tres `baseline.json` ocupan aproximadamente 8–9 MiB cada uno. Se tratan como evidencia generada o potencialmente privada y se retienen. La rama ISO financiera previa excluyó un informe con consumo/saldo real; la historia original que lo contiene sigue retenida. No se publicaron artefactos `/tmp`, dumps, logs ni evidencia financiera real.

## E. Bloqueos y riesgo de integración

AdminApps IAM/control plane/SQL no recibe nuevo checkpoint de código: LAB03 prueba incompatibilidad entre el perfil SQL mínimo y operaciones legítimas; hacen falta decisión de separación de roles/base, política de outbox y pruebas de regresión con permisos mínimos. La migración IAM y las siete migraciones `financial` siguen sin activación. Finanzas y gobernanza requieren revisión de datos privados, contratos y autoridad humana; no se sustituyen por el checkpoint financiero previo.

ISO Smart retiene guardrails/uso IA y migraciones 0041/0042 por dependencia de esquema y autoridad financiera; sus documentos financieros, grants y bloqueo comercial no se mezclaron con SSO. MedSupplier retiene el cambio de settings, grants y decisión comercial; la contraseña demo del archivo local original no se publicó en la nueva rama. Los informes D restantes contienen historia de validación y no se incorporaron automáticamente.

Las ramas IAM y financiera AdminApps son hermanas; también lo son las ramas ISO financiera y SSO. Un merge o cherry-pick requerirá reconciliar orden de commits, archivos compartidos, migraciones, ACL y contratos, con pruebas de integración y consumidores. La rama MedSupplier depende además de la autoridad central y del estado durable B/D. Ninguna rama de auditoría se considera lista para producción, ni se integró a `main` o a `hardening`.

## F. Estado final y siguiente checkpoint

Los tres índices originales siguen vacíos y los worktrees conservan `23/337`, `22/38`, `14/25`. Las ramas aisladas de consumidores están limpias tras sus commits. El siguiente checkpoint recomendado es **AdminApps IAM/control plane**, después de adjudicar perfiles SQL mínimos para organizaciones, catálogo, invitaciones, outbox y Django Admin y repetir LAB03 con ALLOW/DENY y revocación. Separadamente, ISO Smart debe resolver esquema 0041/0042 y la revisión privada de evidencia financiera antes de cualquier nuevo checkpoint de IA. Mantener `PRODUCTION_READY = FALSE`, `PHASE31_5 = EXECUTION_HELD` y `S3_DECISION_02A_NOT_CLOSED`.
