#!/usr/bin/env python3
"""Run focused SEC-02 checks using this interpreter and checkout only.

Dependency installation is a separate, online step. All checks deny networking,
database connections and reads of private configuration/data.
"""
import os
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def child():
    def audit(event, args):
        if event in ('socket.connect', 'socket.getaddrinfo'):
            raise RuntimeError('SEC02 network forbidden')
        if event == 'exec' and Path(args[0].co_filename).resolve() == ROOT / 'backend/config/settings.py':
            raise RuntimeError('SEC02 operational settings execution forbidden')
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = Path(os.fsdecode(args[0]))
            if path.name.startswith('.env') or path.suffix in ('.db', '.sqlite', '.sqlite3'):
                raise RuntimeError('SEC02 private/operational file forbidden')
    sys.addaudithook(audit)
    from django.db.backends.base.base import BaseDatabaseWrapper
    def blocked(*args, **kwargs):
        raise RuntimeError('SEC02 database forbidden')
    BaseDatabaseWrapper.connect = blocked
    import psycopg2
    psycopg2.connect = blocked
    sys.path[:0] = [str(ROOT / 'backend'), str(Path(__file__).parent)]
    target = sys.argv[2]
    sys.argv = sys.argv[2:]
    if target == 'imports':
        os.environ['DJANGO_SETTINGS_MODULE'] = 'offline_settings'
        import django
        django.setup()
        import importlib
        for name in ('apps.users.models_2fa', 'config.runtime_profiles',
                     'config.urls_iam', 'config.urls_control_plane',
                     'config.urls_admin', 'config.urls_events', 'lab04.run'):
            importlib.import_module(name)
        print('PASS LAB04 runner, models and four runtime URL profiles')
    else:
        runpy.run_path(str(ROOT / target), run_name='__main__')


def main():
    commands = [
        ['backend/manage.py', 'check', '--settings=offline_settings'],
        ['imports'], ['scripts/security/smoke_offline.py'],
        ['backend/scripts/rec_sso_03d_p0r2_offline.py'],
        ['backend/scripts/rec_sso_03d_p0r2_r1_offline.py', 'integration'],
        ['backend/scripts/rec_sso_03d_p0r2_r1_offline.py', 'successor-mfa'],
    ]
    # Do not forward operational credentials, Python paths or Django settings.
    env = {'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1'}
    for command in commands:
        subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()),
                        '--child', *command], cwd=ROOT, env=env, check=True)
    print('SEC02 backend checks PASS (memory persistence tests; not PostgreSQL/HTTP E2E)')


if __name__ == '__main__':
    child() if '--child' in sys.argv else main()
