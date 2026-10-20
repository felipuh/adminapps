# S3 Decision 02-A — PostgreSQL Isolation Specification

Fecha: 2026-10-09, America/Costa_Rica. Documento B.
Estado: `S3_POSTGRESQL_ISOLATION_PENDING`. Especificación lista para revisión;
runtime no autorizado. Rutas de código relativas a la raíz de AdminApps.

## Contrato y autoridad

Fuentes: [Decision 02-A](ADMINAPPS_AI_FINANCIAL_SECURITY_DECISION_02_A_2026-10-09.md),
[ejecución 02-A](ADMINAPPS_AI_FINANCIAL_S3_DECISION_02_A_EXECUTION_REPORT_2026-10-09.md),
[Amendment 02](ADMINAPPS_AI_FINANCIAL_AUTHORITY_SECURITY_AMENDMENT_02_2026-10-09.md)
y V1.1 §8 / FIN-08, FIN-11 del repositorio ISO Smart, inspeccionados solo para
trazabilidad. Decision 02-A registra aprobación acotada; Amendment 02 sigue
`APPROVAL_PENDING`. Sus diferencias no se resuelven promoviendo la propuesta a
contrato aprobado: Decision exige executor LOGIN y verificación en Python;
Amendment propone NOLOGIN y verificación criptográfica dentro de la frontera DB.

AdminApps conserva organización canónica, productos y entitlements; ISO Smart es
productor independiente. No se agrega un contrato para MedSupplier ni un worker
financiero inexistente. Identidades PostgreSQL siguientes están definidas en
scripts/migraciones; **no son un inventario observado de una base desplegada**.

## Identidades y privilegios encontrados

| Identidad | Definición localizada | Alcance esperado y puntos por verificar |
| --- | --- | --- |
| `adminapps_financial_migration` | `verify_financial_s3_postgres.sh`; migraciones 0002/0003 | LOGIN; NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOINHERIT/NOBYPASSRLS en fixture. Propietario explícito de las 12 tablas iniciales. Uso solo administrativo. |
| `adminapps_financial_runtime` | 0002–0005, revocación 0007 | NOLOGIN en fixture; login auxiliar `adminapps_financial_runtime_evidence` puede SET ROLE. Sin EXECUTE de ambas funciones de admisión; sin tablas decisión/reserva/audit/budget; conserva SELECT de registro/lifecycle/integration_api_keys y ciertos SELECT históricos sujetos a RLS. No describirlo como sin ningún acceso a tablas. |
| `adminapps_financial_admission` | 0005/0007 | NOLOGIN, NOINHERIT, NOSUPERUSER, NOBYPASSRLS; propietario de ambas funciones SECURITY DEFINER. SELECT/INSERT acotados y UPDATE para locks/budgets/grant; políticas centrales `USING(true)` deliberadas. Separado de propietario de tablas. |
| `adminapps_financial_executor` | 0006/0007 y verifier | LOGIN, NOINHERIT, NOSUPERUSER, NOBYPASSRLS. USAGE public + EXECUTE función capability, sin grants directos financieros. Provisión productiva y autenticación exclusiva ausentes. |
| producer / audit / reconciliation | 0002 y verifier | NOLOGIN en fixture. Audit lee tablas iniciales con políticas centrales; reconciliation SELECT de reservas/evidence/history. Producer sin acceso financiero concedido en esos artefactos. Verificar permisos efectivos y memberships transitivos, no solo nombres. |
| Issuer Python | `issuer.py`, `authorization.py` | Autentica credencial hashed_v1, busca grant y evento activo; clave privada inyectada. No hay rol DB dedicado del issuer ni provisión de su lectura de grants/credenciales. No asignarle migration/superuser para hacerlo funcionar. |

`config/settings.py` define una conexión Django general configurable mediante
variables DB_* y un fallback SQLite para tests. No prueba separación de servicio
y administración. No se leyó `.env`. `FinancialExecutor` recibe una configuración
DB por constructor; no existe secret store, rotación DB, revocación de login ni
contrato de pool de conexiones implementado. La transición de producer/grant es
revocación de autorización de aplicación, distinta de revocación de autenticación DB.

## Gaps verificables y modelo de amenazas

| ID de análisis (no requisito normativo nuevo) | Riesgo / evidencia de fuente | Tratamiento y alcance |
| --- | --- | --- |
| PG-R01 | Suplantación de usuario DB: verifier usa `initdb --auth=trust`; un nombre de rol distinto no acredita posesión exclusiva de credencial. | Mantener evidencia histórica como ACL/función. Diseñar autenticación sintética explícita antes de afirmar aislamiento de credenciales. |
| PG-R02 | 0006 activa FORCE RLS en grants/eventos/ledger, pero no tiene `ALTER TABLE ... OWNER TO adminapps_financial_migration`. | Dueño depende del principal creador; el verifier migra como administrador del clúster temporal. Inventariar propietarios de las 15 tablas, fail si runtime/executor/admission son dueños; reconciliar las tres nuevas con dueño dedicado. |
| PG-R03 | 0007 recibe campos sin firma/exp/nbf; `executor.py` verifica Ed25519 antes del SQL. | Acceso arbitrario con identidad executor queda en frontera de confianza excluida. No afirmar que DB valida firma. Debe demostrarse inaccesibilidad de esa identidad para runtime. |
| PG-R04 | `executor.py` no establece SERIALIZABLE/reintentos; `services.py::_admit_once` sí. La carrera existente llama `_admit`, no la nueva ruta executor. | Medir aislamiento efectivo en la sesión executor y ejecutar allí la matriz concurrente; no transferir evidencia de otra ruta. Operación SQL atómica no equivale a aislamiento serializable. |
| PG-R05 | RLS S1 usa `app.tenant_id`, un contexto controlable por SQL. 0005 quita acceso a decisiones/reservas pero deja políticas y algunos SELECT. | Tenant A/B según tabla y rol final; cambiar GUC no es autenticación de tenant. Admisión normal por grant+capability; no restaurar grants para satisfacer pruebas viejas. |
| PG-R06 | Fixed `search_path=pg_catalog, public`; no política explícita de CONNECT/TEMP, CREATE public ni ALTER DEFAULT PRIVILEGES en migraciones financieras. | Auditar schema/database ACL, ownership, PUBLIC, funciones auxiliares, objetos futuros y resolución de nombres. Ausencia en fuente no demuestra privilegio explotable desplegado. |
| PG-R07 | NOINHERIT no constituye una prueba de ausencia de memberships/SET ROLE; precondiciones no comprueban todos los atributos del fixture. | Matriz real de SET ROLE, CREATEROLE/CREATEDB, ownership y DDL con roles no administradores. |
| PG-R08 | `transition_producer_tenant_grant` guarda estado y evento sin `transaction.atomic` propio; wrapper DB bloquea grant, issuer lee último evento. | Ensayar revocación concurrente, falla entre estado/evento y sesiones existentes; definir punto de linealización. No afirmar fallo runtime sin prueba. |
| PG-R09 | Ledger append-only, unicidad y ON CONFLICT presentes; insert no rellena `decision_id`. | Probar correlación real con decisión, conflictos y rollback, incluida respuesta perdida. El FK opcional no demuestra enlace completo registrado. |
| PG-R10 | Probes offline aceptaron whitespace no canónico y clave JSON idéntica duplicada. | FAIL frente a rechazo estricto propuesto por Amendment 02 §6.2; no prueba falsificación de firma. Definir contrato wire y remediación separada, sin modificar código productivo en esta tarea. |

El superusuario/BYPASSRLS evade RLS; FORCE aplica al propietario ordinario, pero
no convierte a su dueño en una frontera contra cambios DDL. Debe comprobarse
separación de ownership. Véase [PostgreSQL 15, RLS](https://www.postgresql.org/docs/15/ddl-rowsecurity.html).
`trust` acepta el nombre solicitado por quien alcanza el servidor, según
[autenticación trust](https://www.postgresql.org/docs/15/auth-trust.html).
Las funciones privilegiadas requieren esquemas confiables y EXECUTE restringido;
los privilegios por defecto de objetos futuros son una inspección distinta de
las ACL actuales: [CREATE FUNCTION](https://www.postgresql.org/docs/15/sql-createfunction.html#SQL-CREATEFUNCTION-SECURITY),
[ALTER DEFAULT PRIVILEGES](https://www.postgresql.org/docs/15/sql-alterdefaultprivileges.html).
Estas fuentes técnicas no crean requisitos contractuales ni fijan la versión
del futuro clúster; registrar y revisar la versión autorizada antes de ejecutarlo.

## Harness propuesto, no servicio creado

Reutilizar fixtures de `FinancialAdmissionServiceTests` y
`FinancialAdmissionPostgresRuntimeRoleTests`: dos organizaciones sintéticas
elegibles, dos productos, credencial sintética, grants A activo/B ausente o
revocado, política/tarifa/budgets sintéticos y Ed25519 efímero. Separar conexión
de seed/inspección administrativa de conexiones runtime/executor. El administrador
puede observar invariantes; nunca produce la evidencia positiva de autorización.

El verifier existente es un punto de partida, **no un harness de aislamiento
listo para ejecutar**. Conserva `--auth=trust`, hereda configuración, usa
`pg_ctl ... || true` y `rm -rf` sin comprobar terminación, e imprime éxito antes
del trap. No demuestra cleanup completo por ese mensaje. El S1 verifier no
provisiona executor aunque aplica migraciones actuales hasta 0007; revisarlo antes
de reutilizarlo, sin ejecutarlo ahora.

Antes del runtime, preparar un sucesor que:

1. Rechace root, colisiones, symlinks, variables/DSN externas y rutas ambiguas.
   Cargue settings exclusivos sintéticos sin `.env`/servicios/scheduler. Registre
   manifest de recursos con run ID y hashes antes de crear recursos.
2. Use clúster privado y efímero, socket absoluto dentro de su raíz 0700, TCP
   deshabilitado; no conecte a 5432, host público ni socket compartido. HBA de
   prueba aprobada y sin `trust` para el ensayo de autenticación. Credenciales
   aleatorias efímeras por principal o peer mappings aprobados: elegir en gate,
   no asumir. No secretos en argv, evidencia, Git o shell tracing.
3. Cree roles únicamente en ese clúster; aplique migraciones solo con autorización
   explícita para la base sintética. Detecte y falle ante ownership equivocado;
   no lo corrija silenciosamente para obtener PASS.
4. Archive catálogo allow-listed: pg_roles sin contraseñas, pg_auth_members,
   pg_class owner/RLS, pg_policy, pg_proc owner/prosecdef/proconfig/ACL,
   pg_namespace ACL, pg_database CONNECT/TEMP, pg_default_acl y versiones.
   No consultar pg_authid ni volcar DSN/secretos.
5. Produzca resultados por caso con identidad efectiva, SQLSTATE, conteos/hashes
   de invariantes antes/después. Una excepción genérica, desconexión, timeout o
   ausencia de fixtures es ERROR, no prueba de denegación. Comprobar conexión
   sana mediante SELECT 1 antes/después; usar conexiones/transacciones separadas
   para que un error previo no provoque un falso negativo `25P02`.
6. Capture evidencia fuera del árbol temporal antes de teardown. Detenga solo
   procesos del run, pruebe ausencia de PID/socket/conexiones y luego elimine
   exclusivamente recursos propios verificados. Si falla stop, conservar
   manifest y recursos para adjudicación; devolver FAIL y no borrar a ciegas.
   Manejar EXIT/INT/TERM; SIGKILL exige recuperación posterior con manifest.

## Matriz positiva y negativa de aceptación futura

| Caso | Positivo | Negativo y observación exigida |
| --- | --- | --- |
| PG-T01 login/rol | Executor auténtico conecta con session_user/current_user esperados. | Credencial inválida, otro usuario y login revocado denegados; conexiones nuevas separadas de sesiones preexistentes. No atribuirlo a `trust`. |
| PG-T02 ACL función | Capability válida, grant vigente, admisión executor exitosa. | Runtime no ejecuta legacy ni capability; executor no ejecuta legacy. SQLSTATE 42501 y cero cambios de reserva/decisión/audit/ledger/budgets. |
| PG-T03 tenants/productos | A admite A mediante grant; B solo mediante grant B aprobado. | A sin grant B, producto/entorno/operación incorrectos rechazados; B no recibe datos A. Para tablas cuyo SELECT está revocado, ambos SELECT deben fallar, no devolver filas filtradas. |
| PG-T04 RLS | Auditor central accede solo según su rol; lecturas tenant-scoped aplicables devuelven filas esperadas. | No-context, GUC falso, INSERT/UPDATE/DELETE/TRUNCATE y RLS disable no autorizados; distinguir ACL, RLS y trigger mediante SQLSTATE y resultado real. |
| PG-T05 ownership/DDL | Migration/admission separados conforme a matriz de objetos. | Runtime/executor sin SET ROLE elevado, ALTER POLICY/OWNER, GRANT, CREATE ROLE/DB ni escritura schema confiable; sin membresía transitiva privilegiada. |
| PG-T06 funciones/defaults | Ruta SECURITY DEFINER prevista y ACL exactas. | PUBLIC y rol sin grants no invocan admission; objetos sombra TEMP/public no alteran resolución. Objetos nuevos sintéticos bajo dueño previsto no heredan grants indebidos. |
| PG-T07 grants/revocación | Grant activo se revalida en DB. | Suspendido/revocado/version vieja/ausente denegados; revocación confirmada antes de admisión impide efecto. Carrera controlada y fallo entre estado/evento quedan registrados. |
| PG-T08 integridad/replay | Firma pública válida y replay idéntico retorna misma decisión sin exposición extra. | Firma/hash/tenant/producto alterados, caducado, futuro o key ausente rechazados; replay concurrente conflictivo sin doble reserva. |
| PG-T09 concurrencia executor | Sesiones independientes vía FinancialExecutor con aislamiento efectivo registrado y presupuesto exacto. | Cross-product/global, tenant independiente, policy/tariff/entitlement/grant races, 40001/40P01, agotamiento retry, crash y respuesta perdida sin exceso ni decisión ambigua tratada como éxito. |
| PG-T10 secretos/procesos | Issuer firma y executor usa solo su credencial sintética. | Runtime no lee clave/credencial ni obtiene DB principal executor; issuer no obtiene credencial executor. Requiere aislamiento real autorizado separado, no fixtures de texto. |
| PG-T11 cleanup | Run termina y evidencia se archiva. | Falla de startup/test/stop y señal no borra recursos ajenos ni oculta recursos vivos. No PASS hasta inventario final de ausencia. |

Criterio de aceptación: matriz aplicable completa, controles positivos reales,
negativos atribuibles, invariantes financieros, fuentes/hashes y cleanup
comprobados. No se cierra PostgreSQL con AST, SQLite ni estas pruebas en memoria.

## Comandos y autorización futura

Comando existente, **solo referencia del antecedente y no ejecutar hasta corregir
los gates descritos y aprobar el SHA resultante**:

```sh
bash backend/scripts/verify_financial_s3_postgres.sh
```

Los selectores de tests concretos para el procedimiento sucesor son:

```text
apps.financial.tests.FinancialAdmissionPostgresConcurrencyTests
apps.financial.tests.FinancialAdmissionPostgresRuntimeRoleTests
```

El sucesor deberá ejecutar `.venv312/bin/python manage.py test` con esos selectores
dentro de sus settings y clúster sintéticos ya verificados y agregar PG-T01–11.
No hay aún comando aprobado para el conjunto ampliado; inventar uno lo haría
parecer implementado. El [plan D](ADMINAPPS_AI_FINANCIAL_S3_SUCCESSOR_EXECUTION_PLAN_2026-10-09.md)
separa revisión de contrato, harness y autorización runtime. No se aplicaron
migraciones, conectó DB, rotó credencial ni levantó contenedor en esta revisión.
