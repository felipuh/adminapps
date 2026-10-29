# Matriz de ejecución y evidencia

Fecha: 2026-10-29. PASS significa ejecutado; FAIL significa ejecución incorrecta; BLOCKED indica dependencia/autorización; NOT RUN no ejecutado; NOT APPLICABLE fuera de alcance. GO histórico local no se revalida automáticamente.

## Ejecución realizada

| Área | Resultado | Evidencia/límite |
| --- | --- | --- |
| Inventario systemd/procesos/listeners | PASS | Solo lectura; inventory.json; no acreditación productiva |
| Trazabilidad y remoto activo | PASS | merge-base, diff/show y ls-remote; fuente en disco no prueba código cargado |
| AdminApps B offline | PASS, 43 casos | SHA 3b6ac6e807b19f02a3e1a8edfec4d57655ac32a3; Django 4.2.22 |
| ISO B offline | PASS, 35 casos | SHA 61bf5a27ac49f66cc8b57f083c752e8fe397d108; intérprete del servicio con Django 6.0.6 |
| ISO D offline, intérprete del servicio | **FAIL** antes de ejecutar casos | TypeError CheckConstraint(check=...) con Django 6.0.6; reproducido |
| ISO D offline, virtualenv alternativo | PASS, 361 casos | Mismo SHA, Django 4.2.22; no cambio del servicio |
| MedSupplier B offline | PASS, 35 casos | SHA 5bfcddc94e0ad5b8f0fe3e7449ba83b66ebc2bca; intérprete compartido Django 6.0.6 |
| MedSupplier D offline | PASS, 533 casos | Mismo SHA/intérprete; no prueba de compatibilidad completa |
| Preflight y reproducción de riesgos | PASS, 10 tests | 8 tests de política y 2 reproducciones AST; confirmación de riesgos no equivale a seguridad PASS |
| Preflight real sobre plan de ejemplo | **FAIL / ejecución BLOCKED**, exit 2 | Reserva de disco insuficiente; evidencia DB, secretos, TLS, permisos y autorización pendientes |
| Seguridad de logs | PASS solo para búsqueda acotada de valores conocidos | No auditoría exhaustiva; contadores y alcance en inventory.json |

Las cinco suites exitosas de producto suman **1007 casos**, con **cero intentos de DB y red** registrados por sus guards. ORM, persistencia, locking/transporte son simulados; firmas/adaptadores utilizan código real según suite. No son HTTP E2E, PostgreSQL, RLS real ni evidencia de staging. La ejecución FAIL permanece registrada y no se reemplaza por el PASS en otro intérprete.

Comandos reproducibles (desde raíz AdminApps para AdminApps; desde backend correspondiente para consumidores):

- `backend/.venv312/bin/python -B backend/scripts/rec_sso_03b_offline.py`
- ISO: `.venv312/bin/python -B integration/tests_b_offline.py`
- ISO: `.venv312/bin/python -B integration/tests_d_offline.py` (FAIL identificado).
- ISO: `.venv/bin/python -B integration/tests_d_offline.py` (PASS alternativo).
- MedSupplier: `/home/felipe/proyectos/isosmart/backend/.venv312/bin/python -B integration/tests_b_offline.py` y `integration/tests_d_offline.py` (solo lectura de dependencias existentes).
- `python3 -B -m unittest discover -s tools/staging_recovery -p 'test_*.py'`.

Los scripts existentes configuran settings sintéticos/dummy DB y bloquean sockets y conexiones SQL antes de importar la aplicación. Se revisó ese aislamiento antes de ejecutarlos. No se importaron .env operativos ni se ejecutó manage.py contra servicios existentes. `offline-tests.json` enlaza cada ejecución de producto con SHA, intérprete, salida, número de tests y guards.

## Matriz staging real pendiente

Todas las filas siguientes: **BLOCKED**; ninguna ejecutada en target. Requieren capacidad, autorización de creación, evidencia positiva de aislamiento y guardrail integrado.

| Producto/área | Pruebas y criterio |
| --- | --- |
| Los tres | Django check, makemigrations --check --dry-run, migrate --plan; suite focalizada sobre DB test exclusiva; integridad de esquema |
| AdminApps | Health con/sin key, key inválida; producto activo/inactivo; subscription activa/inactiva/expirada; entitlement permitido/denegado; organización inexistente; tenant isolation; respuestas/logs sanitizados |
| ISO Smart | Login permitido/denegado, entitlement activo/inactivo, timeout/autoridad caída, key inválida, respuesta malformada, sin fallback/bypass, sin tokens ante denegación, cross-tenant denegado, cookies/CSRF/expiración y refresh/revocación |
| MedSupplier | Smoke --no-fallback, autorización tenant/scopes, denegación, autoridad malformada/timeout, aislamiento tenant/account, regresión de endpoints, sesiones y refresh |
| Positivo | Tenant QA nuevo, acceso por producto, billing vigente, evidencia de autoridad central antes de emisión de sesión; source=adminapps/fallback=false donde corresponda al contrato |
| Negativo | Tenant distinto sin entitlement activo; denegación controlada sin tokens/500; no mutar SMART3AI piloto |
| Seguridad cruzada | Firmas/claves, expiración, RBAC/ABAC, scopes, lifecycle, RLS real, ausencia de acceso por defecto; log injection y sanitización |
| Fallos/rollback | Caída AdminApps, timeout, reinicio de procesos staging, restauración exclusiva staging, ausencia de efectos en servicios existentes |

No imponer HTTP 403 ni JSON access/refresh históricos a endpoints cuyo contrato actual usa cookies o AuthenticationFailed. Derivar expectativas de código/contratos actuales y justificar cualquier cambio. `check_isosmart_adminapps ... --no-fallback` y `check_medsupplier_adminapps --no-fallback` siguen siendo gates obligatorios, pero no sustituyen el SSO nuevo.

Infraestructura productiva pública, merge, tag, release y deploy productivo: **NOT APPLICABLE en esta fase**, no realizados.
