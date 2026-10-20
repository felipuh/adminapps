"""Offline syntax lint, isolated Django checks and migration graph; never DB I/O.

Run from repo root with backend/.venv/bin/python -B this_script.
No migrate/makemigrations command or project settings are loaded.
"""

import io
import json
from pathlib import Path
import runpy
import tabnanny
import tokenize

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'docs/security/REC-SSO-02/evidence'
ns = runpy.run_path(str(Path(__file__).with_name('rec_sso_02_offline.py')),
                    run_name='rec_sso_checks')

from django.core.checks import run_checks  # noqa: E402
from django.db.migrations.loader import MigrationLoader  # noqa: E402

paths = [ROOT / 'backend/apps/integration/sso_views.py',
         Path(__file__), Path(__file__).with_name('rec_sso_02_offline.py'),
         Path(__file__).with_name('rec_sso_02_2fa_regression.py')]
for path in paths:
    source = path.read_text()
    compile(source, str(path), 'exec')
    tabnanny.process_tokens(tokenize.generate_tokens(io.StringIO(source).readline))
print('Syntax/indentation lint PASS:', [str(p.relative_to(ROOT)) for p in paths])
messages = run_checks(databases=[])
print('Django isolated checks:', [(m.id, m.msg) for m in messages])
loader = MigrationLoader(None)
result = {}
for target in [('users', '0004_transactional_2fa'),
               ('integration', '0006_integration_api_key_lifecycle')]:
    migration = loader.disk_migrations[target]
    result['.'.join(target)] = {
        'dependencies': migration.dependencies,
        'forward_graph_not_database_plan': loader.graph.forwards_plan(target),
        'operations': [op.describe() for op in migration.operations],
    }
(EVIDENCE / 'migration-graph.json').write_text(json.dumps(result, indent=2) + '\n')
print('Database connection attempts:', ns['DB_GUARD'].call_count)
print('Network attempts:', sum(g.call_count for g in ns['NETWORK_GUARDS']))
assert not [m for m in messages if m.is_serious()]
assert not ns['DB_GUARD'].call_count
assert not sum(g.call_count for g in ns['NETWORK_GUARDS'])
