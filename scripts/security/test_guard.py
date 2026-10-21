#!/usr/bin/env python3
"""Small isolated negative tests, with synthetic credentials only."""
import os
from pathlib import Path
import subprocess
import tempfile
import secrets

checker = Path(__file__).with_name('check_secrets.py').resolve()
def git(*args):
    subprocess.run(['git', *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def check(expected, *args):
    r = subprocess.run(['python3', str(checker), *args], capture_output=True)
    assert r.returncode == expected, r.stdout.decode()
with tempfile.TemporaryDirectory() as tmp:
    os.chdir(tmp)
    git('init', '-q'); git('config', 'user.name', 'Guard Test'); git('config', 'user.email', 'test@invalid.example')
    Path('safe.py').write_text('print("offline")\n'); git('add', '.'); check(0)
    Path('.env').write_text('DB_PASSWORD=\n'); git('add', '-f', '.env'); check(1); git('rm', '--cached', '.env'); Path('.env').unlink()
    Path('backend/.venv').mkdir(parents=True); Path('backend/.venv/library.py').write_text('# library\n')
    git('add', '.'); check(1); git('rm', '-r', '--cached', 'backend')
    Path('sample.py').write_text('api_key = "'+secrets.token_hex(24)+'"\n'); git('add', 'sample.py')
    Path('sample.py').write_text('# unstaged safe decoy\n'); check(1)
    git('commit', '-qm', 'synthetic fixture'); git('add', 'sample.py'); git('commit', '-qm', 'remove fixture')
    check(0); check(1, '--ref', 'HEAD')
print('PASS guard: safe index, forbidden env/dependency, staged-only secret, deleted historical secret')
