#!/usr/bin/env python3
"""SEC-03 event-history and redaction regressions; random synthetic values only."""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile

CHECKER = Path(__file__).with_name('check_secrets.py').resolve()


def git(*args):
    return subprocess.check_output(['git', *args], stderr=subprocess.DEVNULL).decode().strip()


def check(expected, *args):
    result = subprocess.run([sys.executable, str(CHECKER), *args], capture_output=True, text=True)
    assert result.returncode == expected, 'Unexpected guard exit status'
    assert synthetic not in result.stdout + result.stderr, 'Synthetic value leaked to logs'


with tempfile.TemporaryDirectory(prefix='sec03-fixture-') as tmp:
    os.chdir(tmp)
    git('init', '-q')
    git('config', 'user.name', 'Synthetic Guard')
    git('config', 'user.email', 'guard@example.invalid')
    synthetic = secrets.token_hex(24)
    Path('safe.txt').write_text('public fixture\n')
    git('add', '.'); git('commit', '-qm', 'safe fixture')
    check(0, '--ref', 'HEAD')
    for name in ('.env', 'local.sqlite3', '.venv/lib/site-packages/dependency.py'):
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('synthetic\n')
        git('add', name); check(1)
        git('rm', '--cached', name); path.unlink()
    Path('sample.py').write_text('api_key = "' + synthetic + '"\n')
    git('add', '.'); git('commit', '-qm', 'synthetic secret')
    check(1, '--ref', 'HEAD')
    git('rm', 'sample.py'); git('commit', '-qm', 'remove synthetic secret')
    check(0)
    check(1, '--ref', 'HEAD')
print('PASS safe history; env/database/virtualenv rejected; embedded and deleted secrets rejected; logs redacted')
