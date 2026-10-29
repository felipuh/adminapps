# Staging/target — descubrimiento y dictamen, 2026-10-29

Fecha: America/Costa_Rica. Evidencia de esta sesión, no certificación de los resultados históricos de julio.

Actualización posterior del mismo día: consultar `STAGING_ISOLATION_ASSESSMENT_2026-10-29.md` y `STAGING_READINESS_VERDICT_2026-10-29.md`. La recuperación posterior identifica los virtualenvs efectivos de systemd, la causa SQLite del reinicio, compatibilidad Django y continuidad Git/SSO. Este documento conserva la observación inicial; sus virtualenvs locales no deben interpretarse como los usados por servicios.

## 1. Dictamen

**GO WITH RESTRICTIONS para staging/target: no se identificó un target aislado verificable para la matriz completa.** No se declara GO productivo ni GO CONTROLADO STAGING/TARGET.

**NO GO para admitir los servicios locales encontrados como target en su estado observado:** hashes/ramas diferentes y configuración de bypass de pruebas incompatible con el gate. No se ha demostrado un bypass efectivo mediante login; la configuración efectiva del proceso y sus condiciones de aplicación siguen sin validar. Si un target permite acceso por bypass o falla un smoke por bug real, su dictamen debe ser NO GO.

## 2. Entorno encontrado y faltantes

Observación local en la máquina de trabajo; no se presume que sea staging ni se le asigna un alias ficticio. Usuario de inspección: `felipe`. No se encontró `~/.ssh/config`. Podman disponible, sin contenedores listados para este usuario; Docker no disponible. Estas observaciones no prueban inexistencia de infraestructura remota o contenedores de otros usuarios.

| Sistema | Ruta local de backend | Servicio systemd | Estado observado | Python local | Virtualenv local | Settings por defecto de manage.py |
| --- | --- | --- | --- | --- | --- | --- |
| AdminApps | `/home/felipe/proyectos/adminapps/backend` | `adminapps-backend.service` | active/running | 3.9.25 | `backend/.venv` | `config.settings` |
| ISO Smart | `/home/felipe/proyectos/isosmart/backend` | `isosmart-backend.service` | activating/auto-restart | 3.12.13 | `backend/.venv` | `backend.settings` |
| MedSupplier | `/home/felipe/proyectos/ISO_Smart_MedSupplier/backend` | `medsupplier-backend.service` | active/running | 3.9.25 | `backend/.venv` | `backend.settings` |

Los tres servicios declaran `User=felipe` y las rutas anteriores como WorkingDirectory. No se inspeccionaron argumentos completos, entornos de procesos ni logs que pudieran revelar secretos. Los intérpretes y settings de la tabla son locales, no están certificados como los efectivos del servicio. No se reinició ni modificó ningún servicio.

Faltan para cada sistema: host/alias staging acreditado; ruta de despliegue; método de ejecución/runner autorizado; DB exclusiva de staging y prueba de aislamiento respecto de producción; identidad de ejecución; configuración efectiva; credencial técnica y usuarios QA disponibles por canal seguro; endpoints internos; logs sanitizados y evidencia de despliegue de los hashes solicitados. Se solicitó al usuario identificación del target sin secretos; al redactar este informe no había respuesta.

El laboratorio `LAB05-C1-R3` es evidencia histórica distinta: declara clusters efímeros eliminados, proyección parcial sin migraciones completas y exclusión de MedSupplier HTTP. No sustituye este target. Referencias: `docs/security/LAB05-C1-R3/REPORT.md` y `../isosmart-lab05-c1-r2/docs/transformation/LAB05_C1_R3.md` desde la raíz AdminApps.

## 3. Código observado

Se ejecutaron `git status --short --branch`, `git branch --show-current`, `git rev-parse HEAD`, `git log --oneline -n 5`, comprobación de objetos esperados, referencias locales y listado de archivos versionados. Evidencia sanitizada: [discovery.json](evidence/staging-target-2026-10-29/discovery.json). Son hashes de checkout, **no hashes desplegados confirmados**.

| Sistema | SHA esperado | HEAD local observado | Rama observada |
| --- | --- | --- | --- |
| AdminApps | `bf2d9d646cd671cc834ea9ade79ac1b4758a7236` | `3b6ac6e807b19f02a3e1a8edfec4d57655ac32a3` | `lab05/c1-r3-http-sso-sanitized-20261028` |
| ISO Smart | `fc2a670fa829936e864722ed06ac9f7ed3c04c8b` | `61bf5a27ac49f66cc8b57f083c752e8fe397d108` | `checkpoint/rec-git-03-isosmart-20261020` |
| MedSupplier | `59678925c918830ade00c713e9a799910fb3b674` | `5bfcddc94e0ad5b8f0fe3e7449ba83b66ebc2bca` | `checkpoint/rec-git-03-medsupplier-20261020` |

Los tres objetos esperados existen localmente; ninguna rama hardening local apunta ya al hash solicitado. Las referencias `origin` inspeccionadas son caché local: no se verificó el remoto en vivo. Ningún checkout se cambió. Los cinco repositorios/worktrees inspeccionados estaban limpios inicialmente, incluidos `adminapps-secure` e `isosmart-lab05-c1-r2`. Esta entrega añade únicamente este informe y su evidencia en AdminApps, sin commit ni publicación.

## 4. Variables sin valores

Fuente: lectura estática de `backend/.env`, sin importar settings ni ejecutar Django. No acredita variables del target ni precedencia efectiva del servicio. No se copiaron contenidos de `.env`. La matriz completa de presencia está en el JSON.

| Variable/grupo | AdminApps local | ISO Smart local | MedSupplier local |
| --- | --- | --- | --- |
| DJANGO_SETTINGS_MODULE | ausente | ausente | ausente |
| DATABASE_URL | ausente | ausente | ausente |
| DB_NAME/USER/PASSWORD/HOST/PORT | presente | presente | presente |
| SECRET_KEY o DJANGO_SECRET_KEY | presente | presente | presente |
| ADMINAPPS_INTERNAL_API_KEY / ADMINAPPS_API_KEY / ADMIN_APPS_API_KEY / INTERNAL_API_KEY | ausente | presente | presente |
| ALLOWED_HOSTS, DEBUG | presente | presente | presente |
| ADMINAPPS_BASE_URL o ADMIN_APPS_BASE_URL | ausente | presente | presente |
| PRODUCT_CODE / ISO_SMART_PRODUCT_CODE / ADMIN_APPS_PRODUCT_CODE | ausente | ausente | ausente |
| ALLOW_LOCAL_AUTH_FALLBACK / ADMIN_APPS_ALLOW_LOCAL_FALLBACK | ausente | ausente | ausente |
| ADMINAPPS_TIMEOUT o ADMIN_APPS_TIMEOUT | ausente | presente | presente |
| ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS | ausente | inconsistencia detectada | inconsistencia detectada |

DB_PORT y timeout donde están presentes: formato aparente válido. DEBUG: formato aparente válido. El indicador de bypass SSO de AdminApps inspeccionado no mostró inconsistencia en el archivo. Los indicadores de bypass de consumidores requieren corrección en un target acreditado; no se cambiaron aquí. La ausencia de fallback en el archivo no certifica su desactivación efectiva. Tampoco la ausencia de una API key en variables certifica ausencia de credenciales administradas por DB u otro proveedor.

Settings por defecto definidos en manage.py no equivalen a variable presente. Los códigos de producto, flags de billing/productos, autenticidad de claves, conectividad de DB, configuración de hosts y credenciales QA del target permanecen pendientes. No se reprodujeron valores, ni siquiera de variables no secretas.

## 5. Datos AdminApps

**NO EJECUTADO en target:** organización positiva, estado/duplicados/slug, catálogos ISO_SMART y MEDSUPPLIER, subscriptions, vigencia/cancelación/billing y entitlements/access/reason. No se consultaron bases de datos ni se aprovisionaron tenants. SMART3AI piloto no fue modificado.

Cuando exista target acreditado: inspección de solo lectura; si faltan datos, management command idempotente con primer `--dry-run`, revisión de cambios y aislamiento por tenant/producto, ejecución real permitida por el target, segundo `--dry-run` sin cambios. No usar el piloto para pruebas negativas.

## 6–10. Matriz QA pendiente

Todas las filas siguientes tienen estado **NO EJECUTADO EN TARGET**, bloqueadas por identificación/aislamiento, baseline y configuración. No se atribuye PASS ni fallo funcional a una ejecución inexistente.

| Área | Pruebas requeridas |
| --- | --- |
| AdminApps QA | `check`; `makemigrations --check --dry-run`; `migrate --plan`; `test apps.products.tests apps.integration.tests` |
| AdminApps HTTP | health sin key, key inválida, key válida; validación ISO_SMART y MEDSUPPLIER; HTTP/allowed/reason/billing/source/fallback |
| ISO Smart QA | `check`; `makemigrations --check --dry-run`; `migrate --plan`; `test authentication.tests integration.tests` |
| ISO Smart smoke | `check_isosmart_adminapps --organization-slug smart3ai --no-fallback` |
| MedSupplier QA | `check`; `makemigrations --check --dry-run`; `migrate --plan`; tests focalizados disponibles |
| MedSupplier smoke | `check_medsupplier_adminapps --no-fallback`, scopes y ausencia de regresión |
| ISO positivo | login real; HTTP 200; presencia de access/refresh sin imprimirlos; trazabilidad de validate_credentials y validate_product_access antes de tokens; producto ISO_SMART |
| ISO negativo | tenant separado `smart3ai-denied-test`; entitlement ausente/inactivo; login bloqueado, sin tokens ni 500; motivo claro y HTTP 403 o equivalente controlado |

En todos los flujos aplicables deben verificarse `source=adminapps` y `fallback=false`; `--no-fallback` es obligatorio. El estado local/controlado PASS aportado por el usuario es antecedente, no resultado reejecutado en esta sesión.

## 11. Seguridad

No se imprimieron secretos ni valores de `.env`. Los `.env` locales de los tres sistemas están ignorados por git; en los índices actuales inspeccionados solo se encontraron plantillas `.env.*example`. Esto no es un escaneo completo de secretos de código, historia o logs. No se verificó ausencia de secretos en logs del target, headers, respuestas o artefactos de ejecución porque ese target no está identificado. No se crearon bypasses ni se activó fallback. Los indicadores de bypass preexistentes se registran como incompatibilidad de configuración, sin afirmar explotación demostrada.

## 12. Riesgos residuales

- No hay evidencia completa de target, código desplegado, datos, contratos HTTP, migraciones ni seguridad de ejecución.
- Divergencia entre baseline solicitado y ramas actuales; una rama mutable no fija la versión.
- ISO Smart local presenta auto-restart; causa no diagnosticada para evitar acceder a logs sin sanitización. No constituye por sí solo un bug target demostrado.
- Configuración local de bypass incompatible con admisión a staging; aislamiento y defaults efectivos pendientes.
- El laboratorio posterior cubre otro alcance y no puede heredarse como PASS para esta matriz.

## 13. Arquitectura mínima propuesta y secuencia de desbloqueo

Propuesta, **no infraestructura existente ni desplegada**: una VM/host interno dedicado, accesible por SSH controlado o runner privado; tres procesos o contenedores aislados y tres bases PostgreSQL exclusivas con usuarios de mínimo privilegio. Servicios enlazados solo a red privada o loopback con túnel; sin DNS, proxy ni TLS públicos. Separar roles de migración y runtime, datos sintéticos y tenants positivo/negativo; sin reutilizar DB, credenciales ni SMART3AI piloto productivos.

Crear directorios de despliegue separados y versiones fijadas a los tres SHA esperados, conservando los checkouts actuales. Resolver la diferencia de rama/hash antes de desplegar; no mover ramas compartidas ni usar HEAD mutable como sustituto. Instalar dependencias de esos commits en virtualenvs dedicados, verificando compatibilidad Python y PostgreSQL. Inyectar secretos desde almacén protegido, nunca desde documentación, argumentos de proceso o respuestas JSON completas. Desactivar fallback y bypass explícitamente; configurar timeout y códigos de producto correctos.

Secuencia: acreditar host/DB/runner y alcance; verificar baseline limpio; validar presencia/formato y settings efectivos con salida permitida; revisar plan de migraciones y provisionar solo el entorno aislado; ejecutar QA y datos idempotentes; smokes obligatorios sin fallback; login positivo y negativo con trazas sanitizadas; auditoría de logs; dictamen según evidencia completa. Nunca guardar tokens o bodies de login en `/tmp` compartido ni pasar keys/passwords como argumentos visibles: usar cliente que lea secretos del entorno protegido y emita únicamente campos permitidos.

Antes de considerar producción: completar toda esta matriz, resolver inconsistencias, acreditar aislamiento/operación/restauración y realizar una evaluación productiva separada con autorización explícita. Esta fase no autoriza ni certifica producción.

## 14. Límites respetados

No se tocó dominio, DNS, certificados, HTTPS público, Nginx público ni Certbot. No hubo deploy productivo, merge, tag ni release. Tampoco se efectuó deploy de staging, mutación de DB, reinicio de servicios, commit ni push. Solo inspección local y documentación sanitizada.
