"""Adversarial installer inputs, only inside the fresh cluster's maintenance scope."""
import json
import os
from pathlib import Path
import subprocess
import psycopg2

root = Path(os.environ['LAB04_ROOT'])
repo = Path(__file__).resolve().parents[2]
connection = psycopg2.connect(host=str(root / 'runtime/socket'), port=56434,
                             dbname='lab04_human', user='lab04_bootstrap')
connection.autocommit = True
results = []
with connection.cursor() as cursor:
    cursor.execute('CREATE ROLE lab04_probe LOGIN')
    cases = [
        ('membership', 'GRANT lab04_admin TO lab04_probe', 'REVOKE lab04_admin FROM lab04_probe'),
        ('incoming membership', 'GRANT lab04_probe TO lab04_events', 'REVOKE lab04_probe FROM lab04_events'),
        ('createdb', 'ALTER ROLE lab04_probe CREATEDB', 'ALTER ROLE lab04_probe NOCREATEDB'),
    ]
    for label, setup, restore in cases:
        cursor.execute(setup)
        try:
            result = subprocess.run([
                'psql', '-X', '-h', str(root / 'runtime/socket'), '-p', '56434',
                '-U', 'lab04_bootstrap', '-d', 'lab04_human', '-v', 'runtime_role=lab04_probe',
                '-v', 'maintenance_role=lab04_maintenance', '-v', 'runtime_profile=iam',
                '-f', str(repo / 'backend/scripts/provision_runtime_profiles.sql'),
            ], env={**os.environ, 'PGOPTIONS': '-c role=lab04_maintenance'}, capture_output=True, text=True)
            assert result.returncode != 0 and 'Unsafe role attributes or runtime memberships' in result.stderr
            results.append({'case': label, 'status': 'DENY_SQL_POLICY'})
        finally:
            cursor.execute(restore)
    cursor.execute('DROP ROLE lab04_probe')
connection.close()
(root / 'provision-rejections.json').write_text(json.dumps(results, indent=2))
