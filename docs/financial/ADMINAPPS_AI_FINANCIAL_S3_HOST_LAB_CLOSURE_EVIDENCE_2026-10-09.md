# S3 Decision 02-A — Host Lab Closure Evidence

Fecha: 2026-10-09, America/Costa_Rica. Documento A. Revisión repository-local;
no es acta de aprobación ni nueva ejecución host.

## Dictamen

**Cierre operativo reportado; cierre técnico host `EVIDENCED_PARTIAL`.**
No se declara `S3_HOST_LAB_EXECUTION_CLOSED` ni
`S3_HOST_LAB_CLOSURE_EVIDENCED`: falta el respaldo primario persistente de la
ejecución histórica. Esto no contradice el resultado comunicado por el operador;
delimita qué puede verificarse en el repositorio.

`S3_POSTGRESQL_ISOLATION_PENDING`, `S3_IPC_ISOLATION_PENDING` y
`S3_GOVERNANCE_RECONCILIATION_PENDING` permanecen abiertos.
El [plan sucesor](ADMINAPPS_AI_FINANCIAL_S3_SUCCESSOR_EXECUTION_PLAN_2026-10-09.md)
está preparado para revisión, con gates previos a cualquier operación.

## Procedencia y versión

| Artefacto | Evidencia y alcance |
| --- | --- |
| `backend/scripts/s3_isolation_host_lab.sh` | SHA-256 calculado en esta revisión: `4a50014a069289af60afacedc89b6d93468edbd3921c8c6d72c3e005d6c086a5`. Coincide con el suministrado; no demuestra por sí solo qué bytes ejecutó el host. |
| Copia `/root/adminapps-s3-isolation-host-lab-2026-10-09.sh` | Ruta histórica reportada, no inspeccionada ni modificada; checksum/sidecar y continuidad del host pendientes de archivo. |
| [Administrative Gate](ADMINAPPS_AI_FINANCIAL_S3_ISOLATION_ADMINISTRATIVE_GATE_2026-10-09.md) | Fuente de controles, recursos sintéticos, restricciones y cleanup; no contiene el transcript de la ejecución exitosa posterior. |
| [SystemCallFilter remediation](ADMINAPPS_AI_FINANCIAL_S3_SYSTEMCALLFILTER_VALIDATION_REMEDIATION_2026-10-09.md) | Registra hashes `ffe57b21a86fc1c3765c577bdb502fbe9367bdf27a1cb9d47591c5a3501d0b5f` y `14df0b29e45b5fa9de5c8b8c548bd58d58c641349141b55c1e7c735bf640d0df`; ambos son antecedentes, no el hash actual. |
| Solicitud del usuario, “MASTER PROMPT”, §§2–2.4 | Fuente testimonial de los resultados host posteriores. Su resumen se conserva aquí como **reportado**, no como log generado durante el laboratorio. |
| [Offline evidence](ADMINAPPS_AI_FINANCIAL_S3_OFFLINE_EVIDENCE_2026-10-09.json) | Salidas nuevas, comandos, retornos y hashes del trabajo previo. Exclusivamente comprobaciones offline de esta revisión. |

Búsqueda focalizada: documentos `docs/financial`, script y regresiones, referencias
a `4a500`, `RUNTIME VALIDATE`, `CLEANUP_COMPLETE`, `unconfined_service_t` y
archivos de log/transcript/evidence en `docs` y `backend/scripts`. No se localizaron
logs primarios de la ejecución completada en ese alcance. No se inspeccionaron
secretos ni artefactos protegidos de `/root`.

## Resultados históricos y corroboración

| Control | Antecedente reportado | Evidencia persistente / límite |
| --- | --- | --- |
| PREFLIGHT / SETUP | PASS / PASS | Procedimiento presente; falta salida original y retorno de cada fase. |
| Regresión Bash | 19/19 PASS | Harness presente y reproducido ahora: 19/19 PASS. Es una nueva regresión con fixtures, no reproducción del host. |
| DAC | 6/6 PASS | Script contiene lecturas permitidas/denegadas de clave y fixture; faltan salidas originales. No hay prueba de credencial PostgreSQL real. |
| Identidades, UID/GID, cgroup | PASS | Predicados y negativos offline presentes; faltan `/proc/<PID>/status`, cgroup y asociación PID/unidad originales. |
| systemd | PASS | Configura User/Group específicos, NoNewPrivileges, PrivateTmp, PrivateDevices, ProtectHome, ProtectSystem=strict, RestrictNamespaces y CapabilityBoundingSet vacío. Falta `systemctl show` archivado. |
| SystemCallFilter / seccomp | PASS en comprobaciones implementadas | Comparación exacta con expansión local `@system-service`, NoNewPrivs=1, Seccomp=2 y Seccomp_filters>0. Falta evidencia runtime original; no demuestra equivalencia independiente del programa BPF cargado. |
| RUNTIME VALIDATE | PASS | Reportado; no transcript primario localizado. |
| Cleanup / ausencia posterior | CLEANUP_COMPLETE / PASS | Reportado sin cuentas, grupos ni directorios sintéticos; falta inventario posterior con unidad/proceso/rutas y retorno. El manifiesto se elimina al final, según el código. |
| SELinux | Enforcing; `unconfined_service_t` | Reportado; no dominio dedicado confinado demostrado. No atribuir denegaciones DAC/systemd a SELinux. |
| PostgreSQL / IPC del host lab | NOT_IMPLEMENTED / NOT_IMPLEMENTED | Confirmado por código: no conexión DB ni endpoint IPC; directorios runtime son placeholders. |

## Correcciones y discrepancias que deben preservarse

La remediación documentada reemplazó una búsqueda literal de `@system-service`
por expansión semántica local. Sin embargo, ese documento dice que también acepta
el token simbólico; la versión actual lo **rechaza** explícitamente y la regresión
comprueba ese rechazo. No se sobrescribe el informe histórico ni se mezcla su SHA
con el actual. Se requiere el diff revisado hasta `4a500…` y su aprobación/staging.

El usuario refiere una corrección de Bash. No se encontró un registro suficiente
del error exacto, diff y versión intermedia para reconstruir su causa con certeza.
El script actual pasa `bash -n`; esto no prueba retrospectivamente esa reparación.
Archivar el error original y el diff o registrar formalmente su indisponibilidad.

## `/root`: compatibilidad documental

El cambio `0550 → 0700` es un antecedente suministrado, no una observación nueva.
El gate y `require_reviewed_root_execution()` exigen root:root `0700`; por tanto,
el modo reportado satisface el requisito del laboratorio. Quita lectura/travesía
al grupo y añade escritura al propietario. No basta para declarar compatibilidad
con la política completa del host: falta baseline aprobado, motivo del `0550`,
ACL efectivas, dependencias de backup/operación y aceptación del responsable.
Clasificación de esa compatibilidad: `SOURCE_INSUFFICIENT`.
No se propone restauración automática, chmod, lectura de secretos ni modificación
de `/root`. Copia protegida y respaldos quedan fuera de este cleanup y de esta tarea.

## Paquete necesario para adjudicación humana

1. Transcript original, fecha/zona, operador, identificación del host/boot y
   versiones; SHA del script protegido y sidecar antes de la ejecución.
2. Diff/historia de Bash y del validador hasta la versión efectivamente ejecutada.
3. Salidas y retornos de las seis denegaciones/accesos DAC, `systemctl show`,
   expansión de syscalls, UID/GID, cgroup, seccomp y contexto SELinux.
4. `CLEANUP_COMPLETE`, inventario de ausencia posterior y tratamiento explícito de
   copia/respaldos retenidos; sin recrear un manifiesto como evidencia histórica.
5. Aceptación del cambio de modo de `/root` por su autoridad de hardening y
   revisión de suficiencia de evidencia. Si faltan logs definitivamente, declarar
   la pérdida; una eventual repetición requiere autorización independiente y
   produciría evidencia nueva, nunca un sustituto retroactivo.

El cierre operativo comunicado, el cierre técnico host, la aprobación de
gobernanza y el cierre integral de S3 son cuatro decisiones diferentes. Ninguna
prueba sintética valida los servicios desplegados de AdminApps/MedSupplier,
procesos issuer/executor reales, aislamiento de productos, credenciales o IPC.
Root/DBA y control de migraciones siguen fuera del modelo protegido por el lab.
