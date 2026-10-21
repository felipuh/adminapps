# Contrato SQL de autenticación — LAB02

Estado: preparado y probado exclusivamente en PostgreSQL descartable. No autoriza
instalación, activación ni cambios en bases existentes. `PRODUCTION_READY = FALSE`.

## Frontera y roles

Este perfil es para un servicio IAM en una base dedicada, esquema `public`, con
las migraciones inspeccionadas. No constituye el perfil completo del monolito ni
autoriza sus endpoints de administración comercial/financiera. El instalador
rechaza esquemas adicionales, vistas, tablas externas/particionadas, funciones
SECURITY DEFINER en `public` y tablas financieras. La extensión del perfil requiere
revisión y nuevas pruebas; no se resuelve con `GRANT ALL`.

Los nombres se reciben por parámetros; no se presume que existan roles operativos.

| Rol | Contrato |
|---|---|
| Runtime Application Role | LOGIN, sin SUPERUSER/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS, sin membresías entrantes/salientes, sin propiedad; solo grants explícitos de este perfil |
| Migration/Maintenance Role | NOLOGIN, sin privilegios globales; propietario de base, objetos y esquema (`pg_database_owner` también es válido para `public`); administración mediante identidad autorizada separada |
| Database Owner / administrador privilegiado | Puede modificar/eliminar controles; fuera de la garantía contra resurrección. Sus credenciales y membresías nunca se entregan al runtime |

Un administrador de cluster debe crear previamente los dos roles con esos
atributos, asignar la base al propietario y configurar autenticación segura por
un canal de secretos independiente. El script no crea credenciales ni roles.
Los nombres `lab02_app`, `lab02_maintenance` y `lab02_bootstrap` pertenecieron
exclusivamente al laboratorio destruido; no son nombres prescritos para producción.

## Garantía y límites

Un atacante con SQL arbitrario bajo el rol runtime y un snapshot anterior no
puede reconstruir una familia humana revocada para reusar su JWT original:

1. La fila original queda retenida. ACL deniega DELETE/TRUNCATE; triggers de
   `users.0006` prohíben ambos también cuando se accede por mantenimiento.
2. PK, familia y JTI impiden duplicar identidades ocupadas. `users.0005` impide
   mover identidad, retroceder generación o reactivar la fila terminal.
3. La autoridad del usuario no disminuye por UPDATE. No hay DELETE runtime de
   usuarios; las FK reales son NO ACTION, y el borrado ORM no puede eliminar
   la sesión protegida.
4. Runtime no es dueño, no tiene DDL, TRIGGER, REFERENCES, MAINTAIN, TEMP ni CREATE,
   ni una membresía que habilite herencia/SET ROLE. No puede desactivar triggers,
   cambiar `session_replication_role` o sustituir objetos.
5. Funciones existentes siguen SECURITY INVOKER. Las funciones de autoridad
   fijan `search_path = pg_catalog, public, pg_temp`. No se concede EXECUTE
   directo sobre rutinas de aplicación; los triggers instalados siguen funcionando.

Se retienen las propias filas como historial; no se introduce un ledger duplicado
ni una ruta privilegiada nueva. El outbox B admite SELECT/INSERT, sin modificación
o purga desde este runtime. Fence B permite solo actualizar generación/epoch;
activar/desactivar el fence pertenece al mantenimiento.

Esta garantía **no** equivale a resistir todo compromiso SQL: el runtime necesita
escribir contraseñas, usuarios, MFA y sesiones. Un atacante con ese acceso puede
alterar datos, provocar denegación de servicio o intentar obtener autoridad nueva.
Aquí se demuestra específicamente la imposibilidad de restaurar una credencial
revocada bajo el perfil instalado, sin claves de firma ni autoridad administrativa.
No se promete protección frente a restaurar un backup antiguo, cambiar triggers,
dar nuevos grants, cambiar el esquema o controlar al propietario.

## Matriz de permisos

`S/I/U/D` significan SELECT/INSERT/UPDATE/DELETE. Ninguna tabla concede TRUNCATE,
REFERENCES, TRIGGER o MAINTAIN. Sin grant option.

| Tablas | Runtime | Uso |
|---|---|---|
| `users` | S/I/U | registro, login, contraseña, disable/enable, lectura/lock de autoridad |
| `user_sessions` | S/I/U | emitir, consultar, rotar y revocar; logout actualiza estado |
| `two_factor_auth`, `two_factor_challenges` | S/I/U | configuración, consumo TOTP/backup/challenge |
| `user_organizations` | S/I/U | membresía de registro y consulta B |
| `user_activity_logs`, `two_factor_auth_logs` | S/I | auditoría append; INSERT RETURNING requiere lectura |
| `sso_sessions` | S/I/U | ciclo B y revocaciones por trigger |
| `sso_security_fence` | S + U(`generation`,`authority_epoch`) | lock/serialización y autoridad B; sin I/D |
| `sso_revocation_outbox` | S/I | emisión transaccional/idempotente de revocaciones |
| `organization_invitations` | S/U | consumir invitación preexistente |
| `django_session` | S/I/U/D | cookies y logout; no es autoridad JWT |
| Organizaciones/settings/flags, permisos/grupos, clientes B, principal API, productos, entitlements, planes y suscripciones enumerados en el SQL | S | consultas de elegibilidad/contexto |
| Secuencias que respaldan tablas con INSERT autorizado | USAGE | IDs de logs/modelos; sin UPDATE/setval |
| `django_migrations`, blacklist, tablas no enumeradas | ninguno | mantenimiento o fuera del contrato |

Las escrituras de triggers son INVOKER y requieren los permisos de sesiones,
fence y outbox anteriores. No se añade SECURITY DEFINER para evitar esas ACL.
Los métodos ORM que llaman `delete()` en usuarios/membresías y los trabajos de
limpieza de sesiones no forman parte del contrato permitido. Deben sustituirse
por desactivación/retención o tratarse como mantenimiento separado; no ampliar
grants para que esos borrados funcionen. Workers de entrega de outbox requieren
un perfil independiente todavía no verificado aquí.

## Orden de instalación futura

Solo después de revisar y autorizar un destino concreto:

1. Respaldar, validar recuperación y establecer mantenimiento sin emisión humana.
   Revisar todos los endpoints, conexiones, workers y jobs que usarían el perfil.
2. Crear roles separados por el administrador autorizado. Runtime no puede ser
   dueño de base/esquema/tabla/función ni miembro de ningún rol, incluido el dueño.
3. Aplicar el grafo IAM como mantenimiento. `users.0006_sql_revocation_boundary`
   depende de `users.0005_human_jwt_sessions` y `integration.0010_sso_authority_fence`.
   No modifica esas migraciones, ni añade estado/modelos Django.
4. Detener/desconectar todas las sesiones runtime: pueden conservar objetos
   temporales previos. El instalador rechaza conexiones runtime existentes.
5. Con conexión explícita al destino autorizado y rol efectivo de mantenimiento:

   ```sh
   psql -X --host='<destino-autorizado>' --dbname='<base-IAM>' \
     --username='<identidad-de-mantenimiento>' \
     -v runtime_role='<runtime-real>' -v maintenance_role='<propietario-real>' \
     -f backend/scripts/provision_iam_runtime.sql
   ```

   La identidad de conexión debe tener rol efectivo igual a `maintenance_role`
   mediante el mecanismo de conexión aprobado. No usar defaults de host/base,
   settings activos o contraseñas en argumentos. El ejemplo no es autorización.

6. El SQL valida propietario/roles/esquema/migración/triggers/parámetros; reconstruye
   ACL de tablas, columnas, secuencias y rutinas; retira grants de PUBLIC y defaults.
   Cualquier error revierte la transacción completa. La ejecución repetida conserva
   las ACL. Un nuevo objeto no recibe acceso runtime automático.
7. Revisar catálogo, definiciones, conexiones, membresías y privilegios efectivos;
   ejecutar las aceptaciones con conexiones nuevas y reinicio controlado.
   Cada migración posterior o cambio de roles/ACL exige repetir revisión.
8. Solo con aprobación adicional, activar conjuntamente el autenticador durable
   y sus emisores/endpoints conforme al plan R1/LAB01. Los settings activos no
   fueron cambiados en LAB02. Tokens antiguos sin binding requieren relogin.

## Recuperación y conservación

La migración 0006 es deliberadamente irreversible por el runner Django. Ante
fallos, mantener denegación/mantenimiento, las tablas y revocaciones; corregir
permisos o código hacia adelante. No restaurar DELETE/TRUNCATE, no borrar
historial y no volver al autenticador stateless como rollback de autorización.

El perfil no incluye purga de familias, fence ni outbox. Retención, volumen,
privacidad y un eventual archivo/purga requieren un diseño separado que preserve
la imposibilidad de reusar credenciales todavía válidas. Un restore antiguo
también requiere invalidar credenciales y recuperar revocaciones posteriores,
con procedimiento autorizado. LAB02 no certifica ese procedimiento operativo.

## Referencias de semántica PostgreSQL

Propiedad y membresías pueden aportar capacidades que no se eliminan revocando
un único grant: [GRANT PostgreSQL 18](https://www.postgresql.org/docs/18/sql-grant.html).
Los defaults globales y por esquema requieren tratamiento separado:
[ALTER DEFAULT PRIVILEGES](https://www.postgresql.org/docs/18/sql-alterdefaultprivileges.html).
La resolución de objetos debe usar esquemas confiables y colocar `pg_temp` al final:
[CREATE FUNCTION](https://www.postgresql.org/docs/18/sql-createfunction.html).
Las conclusiones de LAB02 se apoyan además en sus pruebas SQL, no solo en estas referencias.
