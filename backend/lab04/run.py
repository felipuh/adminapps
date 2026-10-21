"""Reproducible disposable PostgreSQL verification; never imports active settings.

Run with the project's Python environment: python lab04/run.py --stage A
Only summaries are retained. Credentials, JWTs and database files are destroyed.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile

import psycopg2
from psycopg2 import sql


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=list('ABCDE'), default='A')
    args = parser.parse_args()
    if os.geteuid() == 0:
        raise RuntimeError('Root execution forbidden')
    root = Path(tempfile.mkdtemp(prefix='adminapps-lab04-'))
    runtime = root / 'runtime'
    runtime.mkdir(mode=0o700)
    sock = runtime / 'socket'
    sock.mkdir(mode=0o700)
    data = runtime / 'data'
    env = {**os.environ, 'LAB04_ROOT': str(root), 'PYTHONDONTWRITEBYTECODE': '1'}
    for name in ('LAB04_PROFILE', 'LAB04_ROLE', 'LAB04_MIGRATE', 'LAB04_GRAPH_ALL'):
        env.pop(name, None)
    for name in ('DJANGO_SETTINGS_MODULE', 'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS', 'PGPASSWORD'):
        env.pop(name, None)
    env['PGPASSFILE'] = str(runtime / 'absent-passfile')
    env['PYTHONPATH'] = str(HERE) + os.pathsep + str(REPO / 'backend')

    def run(command, label, extra=None):
        result = subprocess.run(command, env={**env, **(extra or {})}, cwd=HERE,
                                capture_output=True, text=True)
        (root / (label + '.log')).write_text(result.stdout + result.stderr)
        if result.returncode:
            # Raw logs stay private; they can contain test assertion payloads.
            raise RuntimeError(f'{label} failed; inspect private evidence at {root}')
        print(label + ': PASS', flush=True)

    connect = dict(host=str(sock), port=56434, dbname='lab04_human', user='lab04_bootstrap')
    started = False
    try:
        run(['initdb', '-D', str(data), '--username=lab04_bootstrap', '--auth-local=trust',
             '--auth-host=reject', '--no-locale', '--encoding=UTF8'], 'initdb')
        with (data / 'postgresql.conf').open('a') as stream:
            stream.write(f"\nlisten_addresses=''\nport=56434\nunix_socket_directories='{sock}'\n"
                         "unix_socket_permissions=0700\nmax_connections=30\nshared_buffers='32MB'\n"
                         "fsync=on\nsynchronous_commit=on\nfull_page_writes=on\n"
                         "log_min_error_statement=panic\nlog_error_verbosity=terse\n")
        run(['pg_ctl', '-D', str(data), '-l', str(runtime / 'server.log'), '-w', 'start'], 'start')
        started = True
        signing_key = secrets.token_urlsafe(48)
        credentials = {}
        for profile in ('iam', 'control_plane', 'admin', 'events'):
            credentials[profile] = {'password': secrets.token_urlsafe(36), 'signing_key': signing_key}
            with open(runtime / ('credentials-lab04_' + profile + '.json'), 'x',
                      opener=lambda p, f: os.open(p, f, 0o600)) as f:
                json.dump(credentials[profile], f)
        connection = psycopg2.connect(**{**connect, 'dbname': 'postgres'})
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('data_directory'),current_setting('listen_addresses'),inet_server_addr()")
            assert cursor.fetchone() == (str(data), '', None)
            cursor.execute('SELECT datname FROM pg_database ORDER BY datname')
            assert cursor.fetchall() == [('postgres',), ('template0',), ('template1',)]
            cursor.execute('CREATE ROLE lab04_maintenance NOLOGIN')
            for profile in ('iam', 'control_plane', 'admin', 'events'):
                cursor.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD %s').format(sql.Identifier('lab04_' + profile)), [credentials[profile]['password']])
            cursor.execute('CREATE DATABASE lab04_human OWNER lab04_maintenance')
        connection.close()
        (data / 'pg_hba.conf').write_text(
            'local all lab04_bootstrap trust\n'
            'local lab04_human lab04_iam,lab04_control_plane,lab04_admin,lab04_events scram-sha-256\n'
            'local all all reject\nhost all all 0.0.0.0/0 reject\nhost all all ::0/0 reject\n')
        run(['pg_ctl', '-D', str(data), 'reload'], 'reload')
        run([sys.executable, str(HERE / 'migrate.py')], 'migrate', {'LAB04_MIGRATE': '1'})
        for profile in ('iam', 'control_plane', 'admin', 'events'):
            run(['psql', '-X', '-h', str(sock), '-p', '56434', '-U', 'lab04_bootstrap',
                 '-d', 'lab04_human', '-v', 'ON_ERROR_STOP=1', '-v', 'runtime_role=lab04_' + profile,
                 '-v', 'maintenance_role=lab04_maintenance', '-v', 'runtime_profile=' + profile,
                 '-f', str(REPO / 'backend/scripts/provision_runtime_profiles.sql')],
                'provision-' + profile, {'PGOPTIONS': '-c role=lab04_maintenance'})
        run([sys.executable, str(HERE / 'boundaries.py')], 'boundaries')
        for profile in ('iam', 'control_plane', 'admin', 'events'):
            run([sys.executable, str(HERE / 'process_probe.py')], 'process-' + profile,
                {'LAB04_PROFILE': profile, 'LAB04_ROLE': 'lab04_' + profile})
        run([sys.executable, str(HERE / 'acceptance.py'), 'fixed'], 'acceptance')
        run(['pg_ctl', '-D', str(data), '-l', str(runtime / 'server.log'),
             '-m', 'fast', '-w', 'restart'], 'restart')
        run([sys.executable, str(HERE / 'acceptance.py'), 'restart'], 'acceptance-restart')
        run([sys.executable, str(HERE / 'functional.py')], 'functional')
        (root / 'result.json').write_text(json.dumps({
            'stage': args.stage, 'status': 'PASS_POSTGRESQL_LAB',
            'private_socket': True, 'tcp': False, 'financial_migrations': 0,
            'principals': ['lab04_' + p for p in ('iam', 'control_plane', 'admin', 'events')],
        }, indent=2))
    finally:
        if started:
            connection = psycopg2.connect(**{**connect, 'dbname': 'postgres'})
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_setting('data_directory'),current_setting('listen_addresses'),inet_server_addr()")
                assert cursor.fetchone() == (str(data), '', None)
                cursor.execute("SELECT count(*) FROM pg_tablespace WHERE spcname NOT IN ('pg_default','pg_global')")
                assert cursor.fetchone()[0] == 0
            connection.close()
            run(['pg_ctl', '-D', str(data), '-m', 'fast', '-w', 'stop'], 'stop')
        shutil.rmtree(runtime)
        (root / 'cleanup.json').write_text(json.dumps({'owned_runtime_removed': not runtime.exists()}))
        print(root)


if __name__ == '__main__':
    main()
