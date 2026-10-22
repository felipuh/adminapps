"""Read-only static witness of ISO's financial migration dependency.

No consumer imports, settings, database connection or migrations are executed.
This follows literal core dependencies only, not a complete migration planner.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('consumer', type=Path)
    args = parser.parse_args()
    repo = args.consumer.resolve()
    start = ('authentication', '0011_application_auth_runtime_privileges')
    stop = ('core', '0011_billing_models')
    chain = []
    current = start
    seen = set()
    while True:
        assert current not in seen, 'Dependency cycle'
        seen.add(current)
        app, name = current
        relative = Path('backend') / app / 'migrations' / (name + '.py')
        source = (repo / relative).read_bytes()
        tree = ast.parse(source)
        migration = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Migration')
        assignment = next(n for n in migration.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'dependencies' for t in n.targets))
        dependencies = [ast.literal_eval(n) for n in assignment.value.elts
                        if isinstance(n, ast.Tuple) and all(isinstance(e, ast.Constant) for e in n.elts)]
        chain.append({'migration': '.'.join(current), 'path': str(relative),
                      'sha256': hashlib.sha256(source).hexdigest(),
                      'literal_dependencies': dependencies})
        if current == stop:
            assert b'billing_payments' in source and b'billing_subscriptions' in source
            break
        core = [d for d in dependencies if d[0] == 'core']
        assert len(core) == 1, 'Expected one literal core predecessor; inspect changed graph'
        current = core[0]
    print(json.dumps({
        'status': 'BLOCKED_BY_PROHIBITED_FINANCIAL_MIGRATION_DEPENDENCY',
        'consumer_head': subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip(),
        'method': 'static AST witness; not executed migrations or HTTP consumer coverage',
        'chain': chain,
        'financial_migrations_executed': 0,
    }, indent=2))


if __name__ == '__main__':
    main()
