# Staging recovery: infraestructura y trazabilidad

Fecha: 2026-10-29, America/Costa_Rica. Esta revisión amplía `STAGING_TARGET_DISCOVERY_2026-10-29.md`; no hereda suposiciones sobre virtualenvs ni equipara divergencia Git con regresión. Se leyeron también los runbooks reales de julio. Fuente verificable: `evidence/staging-recovery-2026-10-29/inventory.json`.

## Servicios encontrados — inspección sin operación

| Producto | Unidad en /etc/systemd/system | WorkingDirectory relativo a /home/felipe/proyectos | ExecStart: ejecutable, WSGI y bind permitidos | Estado/PID observado |
| --- | --- | --- | --- | --- |
| AdminApps | adminapps-backend.service | adminapps/backend | adminapps/backend/.venv312/bin/gunicorn; config.wsgi:application; 127.0.0.1:8000 | active/running, 1135 |
| ISO Smart | isosmart-backend.service | isosmart/backend | isosmart/backend/.venv312/bin/gunicorn; backend.wsgi:application; 127.0.0.1:8001 | activating/auto-restart, 0 entre intentos |
| MedSupplier | medsupplier-backend.service | ISO_Smart_MedSupplier/backend | **isosmart/backend/.venv312/bin/gunicorn**; backend.wsgi:application; 127.0.0.1:8002 | active/running, 1149 |

Usuario/grupo: felipe. No se observaron drop-ins. Se inspeccionaron unidades efectivas con `systemctl show/cat`, exportando solo nombres de directivas y campos permitidos. `ExecStart` completo no se publica para evitar argumentos sensibles. Python de los ejecutables: 3.12.13. Django: AdminApps 4.2.22; ISO Smart y MedSupplier comparten el ejecutable con Django **6.0.6**, frente a **4.2.22** fijado por los tres requirements. El virtualenv propio `.venv312` de MedSupplier y `.venv` de ISO contienen 4.2.22, pero no son los seleccionados por sus servicios.

Los procesos activos tienen cwd coincidente con las unidades. Esto vincula directorios, no prueba que la memoria del worker corresponda al HEAD actual: no se reiniciaron procesos ni se interrogó su código cargado. Settings inferidos desde WSGI: config.settings / backend.settings. No se importaron los settings operativos; `/proc/PID/environ` refleja el entorno inicial y no necesariamente modificaciones de dotenv en el worker. Los nombres de variables, sin valores, están en el inventario.

`ss -ltnp` confirmó 8000 y 8002 en loopback; 8001 no estaba escuchando en la muestra. PostgreSQL escucha en loopback 5432. Existen otros listeners en todas las interfaces, incluidos 80, 22 y 9090: no se inspeccionó ni modificó su configuración. Por ello loopback de Gunicorn no prueba ausencia de exposición mediante un proxy existente. Podman lista cero contenedores del usuario; no se inspeccionaron contenedores root. Docker no disponible. Redis server no encontrado en PATH; ausencia de dependencia efectiva Redis no certificada. El inventario registra dependencias systemd PostgreSQL/Redis sin conectar a ellas.

## Reinicio ISO Smart

**Causa inmediata verificada:** journal reciente contiene `RuntimeError: SQLite is only permitted with backend.settings_test`. Coincide con `isosmart/backend/backend/settings.py:242`: se rechaza USE_SQLITE_DATABASE fuera del módulo de tests. El archivo local solicita SQLite y el WSGI selecciona settings operativos. El contador aumentó de 967 a 1000 durante observaciones; código de salida 1/3 y worker failed to boot. Es un rechazo de configuración, no evidencia de fallo PostgreSQL, Redis, AdminApps o puerto ocupado.

No se eliminó el guardrail, no se cambió .env ni se reinició el servicio. Existe además un bloqueo independiente de compatibilidad Django: el test D bajo el intérprete del servicio falla en `foundation/models.py:68`, `CheckConstraint(..., check=...)`, con TypeError. El mismo test pasa con Django 4.2.22 del virtualenv alternativo. Esto no repara ni certifica el servicio.

Logs: últimas 150 líneas de cada unidad dentro de dos horas; únicamente se conservan diagnósticos sanitizados y contadores de coincidencia con secretos conocidos, nunca logs crudos. No representa una auditoría completa de logs históricos.

## Mapa de bases y aislamiento

No hubo conexiones SQL. El inventario usa alias hash solo para destinos/usuarios configurados, nunca hashes de passwords/API keys.

| Configuración | Hallazgo | Aislamiento |
| --- | --- | --- |
| AdminApps DB | Host/puerto coinciden con consumidores; nombre y usuario configurados diferentes | No acreditado; permisos/propósito desconocidos |
| ISO Smart y MedSupplier DB principal | Coinciden host, puerto, nombre y usuario configurados | **No independientes en configuración PostgreSQL** |
| ISO Smart y MedSupplier AI/audit | Coinciden nombres auxiliares configurados | No acreditado; prohibida reutilización |
| ISO runtime | Guard SQLite impide iniciar | No equivale a conexión PostgreSQL efectiva |
| Staging nuevo | Ninguna DB creada | BLOCKED |

Los defaults y aliases foundation/test/AI/audit deben inventariarse en el futuro settings efectivo; tres bases principales no bastan si el código abre otras conexiones. No se infiere aislamiento a partir del nombre. No se consultaron organizaciones, entitlements, billing, usuarios reales ni permisos de estas bases.

## Git: continuidad funcional y límites

| Producto | Referencia histórica | HEAD auditado | Relación y cambios |
| --- | --- | --- | --- |
| AdminApps | bf2d9d646cd671cc834ea9ade79ac1b4758a7236 | 3b6ac6e807b19f02a3e1a8edfec4d57655ac32a3 | Sin merge-base; raíz sanitizada ab54411a. Nueve commits en la historia actual, no nueve descendientes de la referencia histórica |
| ISO Smart | fc2a670fa829936e864722ed06ac9f7ed3c04c8b | 61bf5a27ac49f66cc8b57f083c752e8fe397d108 | Referencia es ancestro; 45 commits posteriores |
| MedSupplier | 59678925c918830ade00c713e9a799910fb3b674 | 5bfcddc94e0ad5b8f0fe3e7449ba83b66ebc2bca | Referencia es ancestro; cuatro commits posteriores |

Se ejecutaron status, branch -vv, rev-parse, log --decorate -n 20, merge-base, branch --contains, diff y show (estadísticas y revisión focalizada de código). Evidencia incluye todas las rutas cambiadas, commits adicionales y divergencias con referencias cacheadas. No se cambió ninguna rama. Los HEAD iniciales coincidieron con `git ls-remote` de sus ramas activas. Las ramas hardening son históricas y no se reinterpretan como baseline desplegado.

Cambios sustantivos: AdminApps incorpora registro de clientes, credenciales hash/rotación, contrato de autorización, sesiones, revocación y fencing; ISO incorpora Decision B/D, firmas, cookies, autorización, metering y schemas foundation; MedSupplier agregó fallback local en 2fdd9ba2, posteriormente sustituyó el login por SSO central en e8f2a2d8 y agregó MFA en 5bfcddc9. El login actual pasa por central_auth, prueba firmada e introspección antes de emitir sesión local. No basta buscar un commit llamado revert: el flujo histórico validate_credentials/validate_product_access fue reemplazado semánticamente, por lo que su evidencia no certifica el nuevo contrato. No se afirma equivalencia completa de árboles ni ausencia universal de regresiones; las pruebas offline y pendientes están en la matriz.

## Capacidad y arquitectura propuesta

Observado: 3 CPU lógicas, RAM total ~3.57 GiB, disponible ~1.19 GiB, swap ~3.95 GiB, disco libre ~150 MiB. **No es factible provisionar ahora tres entornos, clusters y dependencias nuevas con reserva operativa segura.** No se borraron datos ni instalaron paquetes para forzar capacidad.

Diseño condicionado a capacidad adicional: área dedicada fuera de checkouts activos; tres copias de fuente fijadas a SHA revisados y tres virtualenvs independientes; cluster PostgreSQL nuevo con directorio/socket propios y roles runtime sin SUPERUSER/CREATEDB/CREATEROLE, dueño de migraciones separado; al menos tres DB principales más aliases auxiliares separados cuando el código los requiera. Nunca adjuntar 5432 existente ni volúmenes de otros servicios. Redis solo si lo requiere la configuración efectiva, en instancia/namespace nuevo, nunca reutilizado por nombre. Preferir despliegue efímero manual supervisado antes de servicios persistentes.

Puertos propuestos 18440–18442 exclusivamente loopback; no reservados ni arrancados. Las versiones SSO actuales rechazan HTTP cuando DEBUG está deshabilitado: se requiere diseñar TLS privado con verificación de confianza, sin certificados/dominios públicos, o resolver formalmente el perfil de transporte seguro. No desactivar verificación TLS ni habilitar DEBUG para sortear el contrato. Podman rootless puede evaluarse tras ampliar capacidad; actualmente no hay imágenes/volúmenes acreditados. Ningún compose operativo se declara listo.

La reserva de 10 GiB usada por el preflight es un umbral conservador propuesto, no un sizing medido de todo el sistema. RAM/CPU deben presupuestarse con carga y servicios existentes antes de autorizar ejecución.
