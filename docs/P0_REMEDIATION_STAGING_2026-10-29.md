# SMART3AI — informe consolidado de remediación P0 y aislamiento

Solicitud: 2026-10-29. Cierre: 2026-10-30, America/Costa_Rica.
Alcance: AdminApps, ISO Smart y MedSupplier; código aislado, pruebas offline y preparación. **No hubo despliegue de staging.**

## 1. Dictamen ejecutivo

**GO WITH RESTRICTIONS para continuar preparación y revisión de los cambios. NO GO para ejecutar staging sobre servicios/bases actuales. NO GO productivo.**

El riesgo reproducible de recuperación debug está eliminado del código aislado y probado contra el código vulnerable anterior. Los dos consumidores rechazan configuraciones staging inseguras y niegan fallback en ejecución, incluso por argumentos alternativos. Se prepararon y probaron dos virtualenvs independientes con Django 5.2.18 y locks con hashes. **Esto cierra objetivos de código y compatibilidad offline, no los riesgos presentes en los servicios activos.**

Matriz final: **1.124 ejecuciones de pruebas de producto PASS y 21 pruebas de preflight/política PASS**. Las suites heredan casos, por lo que estas cifras no representan casos únicos. Cero intentos de conexión de red/BD en los contadores de los harnesses de producto. Las descargas públicas de paquetes ocurrieron durante preparación de dependencias, fuera de las pruebas. El preflight de staging sigue **FAIL / ejecución BLOCKED** por falta de infraestructura y evidencia crítica.

Se trabajó en `/tmp/smart3ai-p0-20261029/`: tres repositorios bare independientes y sus worktrees, sin hardlinks al Git original. Rama en los tres: `security/p0-staging-isolation-20261029`. No se modificaron checkouts activos, sus `.env`, unidades systemd, datos, entitlements, Nginx, DNS o certificados. No se usó sudo; no hubo migraciones, conexiones a bases, push, merge, cherry-pick, reset ni reescritura de historia. Las instalaciones se limitaron a los candidatos y caché privados en `/tmp`.

## 2. Riesgos P0 cerrados en código aislado

| Riesgo | Corrección y evidencia |
|---|---|
| ISO: divulgación de credencial de recuperación mediante X-Forwarded-For, host o DEBUG | Eliminada toda modalidad HTTP de recuperación debug, incluidos header y query parameter. La respuesta solo contiene `detail`. La prueba carga el código de `61bf5a27` y reproduce enlace de reset y evasión del límite; el código nuevo no los permite. |
| ISO: confianza en IP reenviada | La recuperación ignora X-Forwarded-For. REMOTE_ADDR validado se usa para límite/auditoría, nunca para otorgar privilegios. No existe una cadena de proxies de confianza acreditada. Detrás de proxy, el límite por IP agrega solicitudes del mismo peer; permanece el límite por email. |
| ISO: fallos de correo revelaban excepción/email | Error genérico sin excepción ni email; credencial de recuperación invalidada si falla entrega. El correo legítimo continúa recibiendo el enlace; las pruebas usan correo/ORM simulados. |
| Ambos: guard que solo excluía producción | Startup valida flags efectivos antes de enmascararlos. Staging/producción rechazan bypass, fallback, DEBUG, session auth, booleanos inválidos, entornos contradictorios, settings_test y autoridad HTTPS/credencial ausentes. |
| Ambos: argumento `allow_local_fallback=True` | Ya no puede ampliar la política. Solo se permite fallback de datos con booleano True en test/demo explícitos, nunca en staging, producción, desarrollo genérico o entorno desconocido. Una denegación central nunca activa fallback. |
| MedSupplier: sesión Django alternativa y contraseña local de emergencia | SessionAuthentication dejó de ser automática; una sesión local sin JWT central es rechazada. El comando de contraseñas QA rechaza staging/producción incluso con --confirm-local. Eliminada la API key predeterminada. |
| ISO: corrección posterior SSO ausente en la línea activa | `/me` exige el profile_id y organization_id del token central y rechaza perfil ausente. Se revisó y reaplicó puntualmente la corrección de `e212a5ed`, sin integrar su historia independiente. Tres pruebas offline positivas/negativas. |

El mecanismo vulnerable emitía un **token de recuperación de contraseña**, no un access JWT directamente. Cambiar una contraseña local no sustituye AdminApps, MFA, la autorización de producto ni la introspección central. Las pruebas también verifican que denegación/indisponibilidad no emiten sesión y que flags o contraseñas locales no rescatan el login. La recuperación legítima por correo conserva su credencial específica: no se introdujo una nueva ruta de acceso.

## 3. Riesgos P0 y bloqueos abiertos

- **Operación:** los servicios siguen usando código anterior; los cierres anteriores requieren promoción revisada y ventana autorizada.
- **Aislamiento:** ISO/MedSupplier siguen referenciando los mismos destinos y usuarios PostgreSQL y compartiendo virtualenv. No existe un staging ejecutable acreditado.
- **Dependencias operativas:** AdminApps conserva Django 4.2.22 sin soporte; ISO/MedSupplier conservan 6.0.6 con conflictos. Los candidatos no fueron promovidos.
- **Configuración SSO operativa:** los settings base de consumidores no acreditan `ADMIN_APPS_SSO`, `SSO_CENTRAL_TRUST` y `SSO_LOCAL_TRUST` completos del contrato nuevo. La ausencia falla cerrada, pero bloquea login legítimo. Las pruebas aportan configuración sintética; no prueban configuración real.
- **Historia sensible:** la historia original de AdminApps contenía secretos/dependencias/datos versionados. La raíz sanitizada no revoca credenciales ni elimina copias históricas. Rotación/revocación y reconciliación de publicación siguen pendientes; no se realizaron aquí.
- **QA pendiente:** PostgreSQL real, RLS, migraciones, concurrencia, restore, TLS, HTTP SSO extremo a extremo y carga. No son reemplazados por los mocks.

No se probó explotación sobre servicios activos. Los hallazgos de destinos son referencias de configuración, no consultas al catálogo de bases ni prueba de permisos efectivos.

## 4. Reinicio de ISO Smart: causa y reparación preparada

Evidencia: systemd usa WorkingDirectory `/home/felipe/proyectos/isosmart/backend`, ejecutable en `.venv312/bin/gunicorn`, WSGI `backend.wsgi:application`. WSGI establece `backend.settings` si no existe override. El journal acotado reproduce `SQLite is only permitted with backend.settings_test` y referencia ese checkout.

El `.env` declara **USE_SQLITE_DATABASE=True**, aunque también existen DB_HOST, DB_PORT, DB_NAME, DB_USER y DB_PASSWORD. No es ausencia acreditada de variables PostgreSQL: la selección explícita de SQLite provoca el rechazo antes de conectar. `load_dotenv(BASE_DIR / '.env')` no sobrescribe variables ya presentes; se inspeccionaron referencias de unidad/proceso sin importar settings. No se observó una interpolación que explique este flag. La protección apareció en `00f35614`; no se eliminó. El entorno Python es el del checkout esperado, pero sus dependencias están desalineadas. Cambiar únicamente el flag dejaría pendiente la incompatibilidad de Django y la acreditación de destinos.

Procedimiento para una futura ventana autorizada, **no ejecutado**:

1. Confirmar propietario/finalidad de cada alias PostgreSQL y autorización de mantenimiento; separar la reparación del servicio del proyecto de staging. Conservar copia controlada de configuración y evidencia de Git; preparar rollback sin modificar datos.
2. Construir una release independiente con el código aprobado y su propio virtualenv reproducible; verificar importaciones, checks, SSO y compatibilidad de migraciones en bases nuevas acreditadas. No reutilizar settings_test ni quitar el guard SQLite.
3. Preparar fuera de la configuración activa USE_SQLITE_DATABASE=false, destino PostgreSQL autorizado, flags seguros, identidad de producto, trust de SSO y credenciales nuevas de alcance mínimo. Revisión de configuración efectiva sin imprimir valores secretos.
4. Solo con autorización de mantenimiento, aplicar release/configuración y arrancar/reiniciar mediante el operador autorizado. Ejecutar checks de salud, login central permitido/denegado, autorización de producto y observación de logs.
5. Ante fallo, volver a la release/configuración aprobadas anteriores; no inventar acceso por fallback, no habilitar SQLite y no revertir migraciones de datos sin un plan independiente probado.

Al retomar el 30 de octubre se observó un arranque reciente del host y cambio de PID. Esta ejecución no realizó acciones de gestión de servicios. Los hashes de `.env`, unidades e índices Git y los HEAD permanecen iguales antes/después; no se interpreta la continuidad de PID como evidencia.

## 5. Compatibilidad Python/Django y dependencias

| Sistema/entorno | Python | Django | Resultado |
|---|---|---|---|
| AdminApps operativo | 3.12.13 | 4.2.22, coincide con backend requirements | Sin conflictos de metadata; serie sin soporte. Objetivo de actualización pendiente. |
| ISO operativo / MedSupplier compartido | 3.12.13 | 6.0.6 frente a pin 4.2.22 | django-celery-beat 2.5.0 exige Django<5; django-timezone-field exige <6. Seis/siete discrepancias de pins directos. |
| ISO virtualenv histórico usado solo para regresión offline | 3.12.13 | 4.2.22 | Suites compatibles, cero conflictos; no se adopta como destino nuevo. |
| ISO candidato independiente | 3.12.13 | **5.2.18** | 120 distribuciones; cero conflictos y discrepancias con su `.in`; 452 pruebas PASS. |
| MedSupplier candidato independiente | 3.12.13 | **5.2.18** | 117 distribuciones; cero conflictos y discrepancias; 616 pruebas PASS. |

Ambos candidatos: DRF 3.17.1, SimpleJWT 5.5.1, PyJWT 2.10.1, cryptography 46.0.7 y psycopg2-binary 2.9.10. ISO añade celery-beat 2.8.1 y timezone-field 7.2.2 compatibles por resolución. El entorno operativo compartido tiene psycopg 3.3.4 y carece del psycopg2-binary fijado; las versiones completas están en `dependencies.json`. Existen requirements raíz/backend divergentes y CI histórica de ISO con Python 3.9; no había un lock Python único con hashes que acreditase el runtime. El candidato establece su alcance Linux x86_64/Python 3.12 y no pretende validar esa CI antigua.

Django 4.2 terminó soporte el 7 de abril de 2026; 5.2 LTS tiene soporte extendido hasta abril de 2028. La recomendación usa la versión 5.2.18 consultada al preparar el candidato. [Calendario oficial](https://www.djangoproject.com/download/), [Python compatible](https://docs.djangoproject.com/en/5.2/faq/install/).

Django 6.0 elimina el parámetro `check` de CheckConstraint, presente en modelos/migraciones ISO. La suite D falla al importar bajo 6.0.6 y pasa bajo 5.2.18. Esta elección evita cambiar migraciones históricas dentro de la remediación P0; se preserva un objetivo posterior de eliminar deprecaciones y verificar el estado de migraciones PostgreSQL. [Notas oficiales de Django 6.0](https://docs.djangoproject.com/en/6.0/releases/6.0/), [releases de celery-beat](https://github.com/celery/django-celery-beat/releases).

Los archivos `backend/requirements-staging.in`, `.lock` y `.README.md` forman **un candidato separado y probado**, no una modificación encubierta del runtime ni de los requirements operativos. Resolución y sync verificaron hashes y usaron solo wheels, con concurrencia limitada. No se acredita aquí una auditoría completa de vulnerabilidades transitivas ni la promoción productiva.

## 6. Separación de virtualenvs

**Operación: pendiente. Preparación: demostrada para los dos consumidores.**

- `/tmp/smart3ai-p0-20261029/venvs/isosmart`: aproximadamente 470 MiB.
- `/tmp/smart3ai-p0-20261029/venvs/medsupplier`: aproximadamente 483 MiB.

Se verificaron prefijos, rutas de paquetes e inodos distintos, `include-system-site-packages=false` y ausencia de site-packages operativos en sys.path. La instalación usa copia, no enlaces a dependencias operativas. Compartir el binario base inmutable de Python no comparte virtualenv. Evidencia: `runtime-isolation.json`, locks y metadata audits. AdminApps mantiene su entorno propio existente, usado en lectura para QA offline; aún necesita candidato soportado.

## 7. Bases y arquitectura de staging propuesta

Las referencias default/ai_db/audit_db de ISO y MedSupplier coinciden en endpoint, base y usuario. AdminApps tiene otra base/usuario, pero el mismo endpoint PostgreSQL local. Se registran identificadores pseudónimos comparables en `runtime-before.json` y `runtime-after.json`; no se exponen contraseñas. No se consultaron bases ni ACLs.

Arquitectura recomendada: **infraestructura separada**, red privada, tres clusters PostgreSQL nuevos (AdminApps, ISO, MedSupplier), volúmenes y backups propios. ISO y MedSupplier mantienen bases exclusivas para cada alias default/ai_db/audit_db; no basta con aislar `default`. Roles de runtime sin SUPERUSER, CREATEDB, CREATEROLE ni BYPASSRLS; rol de migración separado, no disponible al servicio; REVOKE de accesos públicos y grants explícitos por base/esquema. Credenciales e identidades de servicio distintas por producto. AdminApps sigue siendo autoridad de usuarios, tenants, productos, suscripciones y entitlements; las copias locales son proyecciones.

Los puertos ilustrativos 15440–15442 y 18440–18442 son propuestas loopback, **no reservas ni listeners creados**. TLS privado y confianza deben acreditarse. Egress de cada workload debe permitir solo sus bases y el AdminApps staging autorizado; bloquear redes/endpoints operativos. Un nombre `staging_*` o una URL HTTPS no demuestra pertenencia. Redis queda deshabilitado en el plan hasta justificar su necesidad; si se habilita, requiere instancia/volumen/credenciales propios, no solo un número de DB en Redis operativo.

Antes de migrar/sembrar, exigir: identificación y creación del cluster nuevo; propiedad y ausencia de mounts operativos; configuración efectiva de TODOS los aliases; correspondencia de roles/credenciales; reglas efectivas de red/egress; rechazo de destinos fuera de una allowlist exacta; matriz de privilegios y tests negativos contra recursos QA; backups y restauración en otro destino QA. **Este gate sigue BLOCKED: no se ha demostrado aislamiento ejecutable.**

Datos exclusivamente sintéticos: organizaciones ISO-only, Med-only, ambas, ninguna, suspendida y revocada; usuarios con MFA pendiente, roles de lectura/administración y tenant ajeno. Nunca copiar entitlements del piloto. Eliminación futura: detener solo recursos identificados como staging con autorización, revocar sus credenciales, aplicar retención acordada a backups y eliminar exclusivamente volúmenes cuyos identificadores/proveniencia estén acreditados. No se incluye un borrado automático.

## 8. QA ejecutado

Matriz final selecciona la última ejecución válida de cada suite, sin sumar repeticiones de resolución de errores:

| Suite | ISO candidato | Med candidato | AdminApps |
|---|---:|---:|---:|
| Recuperación P0 | 7 PASS | — | — |
| Política staging/fallback | 10 PASS | 12 PASS | — |
| `/me` central | 3 PASS | — | — |
| SSO B | 35 PASS | 35 PASS | 43 PASS, incluye consumidores coordinados |
| Autorización D/tenant/endpoints | 361 PASS | 533 PASS | — |
| Sesiones D | 36 PASS | 36 PASS | — |
| R1 lifecycle | — | — | 7 PASS |
| Permisos históricos del dashboard | — | — | 6 PASS |
| Total producto | **452** | **616** | **56** |

Preflight/política: **21 PASS**, de los cuales dos reproducen condiciones históricas desde commits fijados. Los casos con combinaciones de headers/flags incluyen subtests y no se multiplican en el total. Los 1.007 PASS y diez tests citados al inicio se mantienen como **evidencia histórica**, sin presentarlos como resultados nuevos.

**FAIL registrados:** suite ISO D con Django 6.0.6 (`CheckConstraint`); primera llamada AdminApps B desde cwd incorrecto; posterior coordinada con `.venv` versionado incompleto; primer fixture de permisos sin atributos DRF. Se preservan los fallos y causas. Se corrigieron cwd/selección de intérpretes/fixture y las repeticiones pasaron; el runtime operativo incompatible permanece sin modificar.

**BLOCKED:** staging efectivo, pruebas PostgreSQL/RLS/ACL y migraciones sobre destino acreditado, promoción operativa y carga representativa. **NOT RUN:** ataques online, tests sobre bases operativas, HTTP E2E de staging, backups/restore reales, frontend/browser completo y auditoría CVE transitiva completa. No se ejecutó SQL.

## 9. Regresiones

No se observaron regresiones críticas en el alcance offline probado: login central positivo, challenge MFA, rechazo de producto/tenant ajenos, roles, revocación, refresh y autorización de endpoints. La suite coordinada verifica `own ALLOW`, `foreign/local DENY`, `tenant DENY` y conservación de viewer para ambos consumidores.

Cambios intencionales: ya no existe URL de recuperación debug; fallback de datos limitado a test/demo; staging con configuración insegura falla al iniciar; comando local de contraseñas no acepta excepciones operativas; sesiones Django locales no autentican MedSupplier. Ninguno se presentó como regresión de SSO legítimo. Las pruebas legacy que esperaban el enlace debug o fallback genérico de desarrollo fueron ajustadas a la nueva política.

## 10. Preflight empresarial

Resultado del plan ejemplo: **FAIL**, salida 2, **execution_status=BLOCKED**. Detecta o exige evidencia de: capacidad, bases/roles/volúmenes compartidos, inventario de aliases, virtualenvs compartidos, rutas en uso, flags inseguros, SQLite, identidad de producto/autoridad, destino AdminApps, binds públicos, secretos ausentes, locks no reproducibles, discrepancias instaladas y Django incompatible.

Las comprobaciones locales de los dos candidatos (paths, metadata y locks) no encontraron errores. Esa prueba excluye deliberadamente acreditación de infraestructura y no elimina los bloqueos. El preflight no importa settings ni `.env`, no conecta, no inicia servicios ni migra. El inventario read-only de configuración es otra herramienta explícita.

Se corrigió un falso positivo: un proceso con cwd `/` no implica que ejecute todos sus directorios descendientes. Las rutas de virtualenv presentes en argv se incorporan a la detección. Persisten bloqueos explícitos para usuarios/procesos no inspeccionables, settings efectivos, TLS, propiedad de puertos/mounts, ACLs y egress. Ninguna variable, archivo o declaración de aprobación convierte el resultado en PASS operativo.

## 11. Capacidad disponible y requerida

Medición inicial: `/home` ~150 MiB libres; `/tmp` reside en otro filesystem con ~55 GiB libres; 3 CPU y ~1,4 GiB de RAM disponible. Tras preparación: `/tmp` ~54 GiB libres. Al retomar el host, RAM disponible cayó a ~0,75 GiB por otros procesos; solo se ejecutaron comprobaciones seriales pequeñas. La última captura de entrega muestra 5 CPU disponibles por afinidad, 1,06 GiB de RAM disponible, ~138 MiB libres en /home y ~53,4 GiB en /tmp; los recursos del host variaron entre capturas. Valores exactos en `capacity.json` e inventarios, incluida `runtime-delivery.json`.

Mediciones: venv AdminApps ~161 MiB; venv compartido operativo ~2,9 GiB; venv histórico ISO ~657 MiB; candidatos ~470/483 MiB; caché aislada ~546 MiB; repositorios/worktrees iniciales ~788 MiB. Pico medido de una suite offline: 149.788 KiB RSS. El RSS idle de servicios no es una medida fiable de carga ni de páginas intercambiadas.

Presupuesto **provisional**, no garantía de rendimiento: 4 vCPU, 8 GiB RAM y **30 GiB libres** en el destino. Asignación inicial: ~1,2 GiB para tres entornos mínimos (AdminApps por medir actualizado), ~1 GiB de código/metadata, 6 GiB para bases/WAL QA, 8 GiB de backups, 2 GiB de logs, 2 GiB de caches/build y ~10 GiB de reserva. Imágenes de contenedor no medidas ni descargadas: si se elige contenedorización, medir y ampliar antes de aprobar. Datos/WAL/logs/retención son cuotas de planificación, no consumo observado; deben calibrarse con carga y restore en infraestructura aislada.

## 12. Alternativas de staging

| Alternativa | Capacidad/disponibilidad | Interferencia y seguridad | Ventajas/desventajas | Pendientes/costo |
|---|---|---|---|---|
| **A. Infraestructura separada — recomendada** | Presupuesto provisional anterior; destino aún no elegido | Menor interferencia y separación de red/credenciales/volúmenes acreditable | Independencia de incidentes locales; requiere operación adicional | Cotización, propietario, cuotas, firewall, TLS, backups, monitorización y autorización. Sin precio inventado ni aprovisionamiento. |
| B. Otra máquina local | No hay inventario; medir CPU/RAM/disco y reserva | Aislable si no comparte volúmenes, credenciales ni red operativa abierta | Puede aprovechar hardware disponible; disponibilidad/energía/backup por demostrar | Inventario y carga, permisos, red y responsabilidad. Sin costo acreditado. |
| C. Equipo actual | Root tiene disco para preparación; /home saturado, 3 CPU al inicio/5 al cierre, RAM variable <2 GiB y swap | Mayor competencia con servicios activos y reinicio ISO | Útil para pruebas pequeñas seriales; no acredita capacidad de staging permanente | Recuperación de recursos autorizada, medición de carga, reservas y aislamiento nuevo. No se borró ni movió ningún dato crítico. |

A es la recomendación por separación operacional, no por una tarifa estimada. B es una alternativa válida si se acredita capacidad y aislamiento equivalentes. C permanece NO GO para staging ejecutable en esta corrida; disponer de disco en `/tmp` solo hizo viable preparar y probar código.

## 13. Archivos modificados

Inventario exacto por repositorio en `changed-files.json` y en los diffs de los commits.

ISO: `authentication/views.py`, prueba de recovery existente, `backend/security_policy.py`, settings/settings_test, guardrail test, `integration/client.py`, tres suites P0 offline, documentación de transformación y los tres archivos del candidato de dependencias.

MedSupplier: política/settings/settings_test, cliente de integración, autenticador SSO, comando de contraseña QA, suite staging, documento de seguridad y tres archivos del candidato.

AdminApps: preflight/inventario/metadata/matriz Git y sus pruebas; runner coordinado SSO; prueba de permisos históricos; este informe y evidencia saneada. **No se modificó lógica operativa de AdminApps.**

## 14. Commits atómicos creados

Todos son locales en `security/p0-staging-isolation-20261029`, en los repositorios independientes de `/tmp`:

| Repositorio | Hash | Objetivo |
|---|---|---|
| ISO | `eda8a136` | Eliminar recuperación debug falsificable |
| ISO | `c671214e` | Autorización staging fail-closed |
| ISO | `fd46bc78` | Preservar `/me` ligado a sesión central |
| ISO | `8fdde717` | Candidato Django 5.2 independiente y probado |
| MedSupplier | `976bbfd2` | Bloquear fallback/configuración insegura y acceso local |
| MedSupplier | `f06ce889` | Candidato independiente Django 5.2 |
| AdminApps | `0ac12ea6` | Extender preflight y auditoría offline |
| AdminApps | `67218670` | Intérpretes independientes en QA coordinado |
| AdminApps | `7d25a894` | Permisos históricos y detección precisa de rutas |

El commit documental final es descendiente de estos; su hash se registra fuera de su propio contenido en el manifiesto de entrega. No se crearon commits vacíos. No hubo publicación remota.

## 15. Matriz Git y conservación histórica

| Sistema | Checkout activo observado | Correcciones históricas | Cambios posteriores / integración |
|---|---|---|---|
| AdminApps | `9cd64e04`, rama `lab05/c1-r3-http-sso-sanitized-20261028`, limpia; un commit sobre referencia remota cacheada `3b6ac6e8` | Hash completo `9cd64e04dc7e9b33022256dc782da86e36eb7055` recalculado correctamente; padre `3b6ac6e8`, fsck connectivity exit 0. Snapshot: 632/636 archivos coinciden, ninguno perdido; 35/37 LAB04 idénticos. | Raíz sanitizada `ab54411a` sin ancestro común con `047d5868`. Cuatro diferencias: dos harnesses LAB04 ampliados para HTTP/SSO y dos manifests frontend de remediación npm. No se integró historia antigua. |
| ISO | `61bf5a27`, rama `checkpoint/rec-git-03-isosmart-20261020`, limpia | `0ce01dff` es ancestro. SSO `46eb2739` reemplaza lógica legacy por pruebas firmadas y autoridad viva; financial guardrails posteriores permanecen. | Rama sanitizada `e212a5ed` sin ancestro común: solo la diferencia funcional `/me` fue revisada y reaplicada con pruebas. |
| MedSupplier | `5bfcddc9`, rama `checkpoint/rec-git-03-medsupplier-20261020`, limpia | `6a5fd036` es ancestro. SSO `e8f2a2d8` reemplaza el login fallback histórico `2fdd9ba2`; login usa autoridad central. | `5bfcddc9` añade flujo MFA frontend. Nuevos guards cierran los mecanismos de fallback de datos todavía presentes. |

Detalles AdminApps: rutas nombradas de organizaciones/suscripciones (`fe671855`) conservadas byte a byte; servicio/modelos/migración/tests 2FA (`dc723be2`) conservados, con callers evolucionados por SSO; lifecycle frontend (`54d201e5`) conservado y `api.jsx` solo amplía el método de dashboard IA. La restricción histórica de dashboard `8e67dcb3` **no es idéntica**: ahora admite delegación de plataforma staff+permiso específico además de superadmin. Se verificaron seis casos que mantienen fuera a tenants, servicios y usuarios sin privilegios explícitos. No se declara equivalencia textual donde no existe.

Implicación: no usar merge/cherry-pick automático de la historia no sanitizada; podría reintroducir secretos y duplicar cambios ya conservados por contenido. Revisar un delta de la línea sanitizada después de acreditar publicación/rotaciones. Las referencias remotas usadas aquí son cacheadas; no se afirma haber verificado el HEAD remoto en vivo. El commit de auditoría original se conservó como ancestro, no se recreó ni sobrescribió.

Al cerrar la entrega se detectaron un índice, una referencia y cinco objetos sueltos de tamaño cero en la copia **aislada** de AdminApps. La causa no está determinada. Se respaldaron archivos y metadata, se pusieron en cuarentena solo los objetos vacíos y se restauró la referencia al mismo `7d25a894` acreditado por reflog y objetos. Se reconstruyó únicamente el índice desde ese commit. `git fsck --full` terminó con salida 0 en los tres repositorios aislados; los commits no fueron recreados. El fallo transitorio del escáner durante el daño no se contabiliza como PASS. La evidencia y los controles finales están en `isolated-git-recovery.json` y `runtime-delivery.json`.

## 16. Bloqueos pendientes

Infraestructura y presupuesto del destino; pruebas técnicas de red/volúmenes/ACL; credenciales/trust nuevas; configuración central efectiva; actualización soportada de AdminApps; promoción del candidato y migraciones bajo PostgreSQL real; actualización de CI Python; carga, observabilidad y restore; reconciliación Git/publicación y respuesta a secretos históricos. Estos puntos requieren propietarios y, donde corresponde, ventana/autorización de infraestructura. No afectan la validez de las correcciones offline ya cerradas, pero impiden GO operativo.

## 17. Plan operativo siguiente

1. Revisar commits/diffs y conservar informe, evidencia y bundles fuera del almacenamiento temporal; verificar hashes y prerequisitos Git antes de reconstruir los worktrees.
2. Aprobar la opción A o acreditar B; no contratar ni provisionar hasta esa decisión. Asignar responsable de infraestructura, seguridad, bases y release.
3. Completar el candidato soportado de AdminApps y la configuración SSO/trust de los tres productos. Promover manifests solo tras revisión de compatibilidad y pruebas PostgreSQL en destino nuevo.
4. Acreditar clusters/roles/volúmenes/egress/TLS/secrets, ejecutar preflight en ese destino y resolver todos sus bloqueos críticos. Solo entonces autorizar migraciones y datos QA sintéticos.
5. Ejecutar matriz positiva/negativa real, RLS, revocación, SSO HTTP, restores y carga. Reemitir dictamen con evidencia de ese entorno.
6. Tratar la reparación ISO como mantenimiento independiente. No reutilizar el servicio caído, las bases ni el virtualenv compartido como staging.

Evidencia de esta corrida: `docs/evidence/p0-remediation-2026-10-29/qa-final.json`, `preflight-final.json`, `git-matrix.json`, inventarios antes/después, comprobación de checkouts sin cambios, locks/metadata e informes de pruebas. Los documentos de auditoría previos permanecen intactos y se distinguen de estos resultados.
