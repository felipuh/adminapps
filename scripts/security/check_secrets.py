#!/usr/bin/env python3
"""Fail-closed audit of the complete Git index or all objects reachable from a ref.
Only paths, rule IDs and line numbers are printed. Requires Gitleaks 8.30.1.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

VERSION = '8.30.1'
ROOT = Path(__file__).resolve().parents[2]

def git(*args):
    return subprocess.check_output(['git', *args], stderr=subprocess.DEVNULL)

def forbidden(path):
    parts = path.lower().split('/')
    name = parts[-1]
    return (any(p.startswith(('.venv', 'venv')) or p in {
        'env', 'node_modules', '__pycache__', 'staticfiles', 'media', 'logs',
        '.aws', '.ssh'} for p in parts)
        or (name.startswith('.env') and not name.endswith('.example'))
        or bool(re.search(r'\.(?:pem|key|p12|pfx|keystore|jks|sqlite3?|db|log|dump|backup|bak|pyc)(?:-.*)?$', name))
        or name in {'.netrc', '.npmrc', '.pypirc', 'credentials.json'}
        or (name.startswith('credentials.') and name.endswith('.json'))
        or name.startswith(('service-account', 'service_account', 'id_rsa', 'id_ed25519')))

def entries(ref):
    if ref:
        commits = git('rev-list', ref).decode().splitlines()
        if not commits:
            raise ValueError('No reachable commits')
        rows = set()
        for commit in commits:
            for row in git('ls-tree', '-rz', commit).split(b'\0'):
                if row:
                    meta, path = row.split(b'\t', 1)
                    mode, kind, oid = meta.decode().split()
                    rows.add((mode, kind, oid, os.fsdecode(path)))
        # Commit/tag messages can also carry secrets.
        for oid in git('rev-list', '--objects', '--no-object-names', ref).decode().splitlines():
            kind = git('cat-file', '-t', oid).decode().strip()
            if kind in ('commit', 'tag'):
                rows.add(('100644', kind, oid, '__git_metadata__/' + oid))
        return sorted(rows)
    rows = []
    for row in git('ls-files', '--stage', '-z').split(b'\0'):
        if row:
            meta, path = row.split(b'\t', 1)
            mode, oid, stage = meta.decode().split()
            if stage != '0':
                raise ValueError('Unmerged index')
            rows.append((mode, 'blob', oid, os.fsdecode(path)))
    return rows

def audit(ref=None):
    binary = os.environ.get('GITLEAKS', 'gitleaks')
    try:
        version = subprocess.check_output([binary, 'version'], stderr=subprocess.DEVNULL).decode().strip()
    except (OSError, subprocess.CalledProcessError):
        raise ValueError('Install Gitleaks 8.30.1; audit cannot be skipped')
    if version != VERSION:
        raise ValueError('Gitleaks version must be ' + VERSION)
    reviewed = json.loads((ROOT / 'scripts/security/reviewed-findings.json').read_text())
    allowed = {(x['path'], x['sha256'], x['rule'], x['line']) for x in reviewed}
    failed = False
    mapping = {}
    rows = entries(ref)
    if not rows:
        raise ValueError('Empty snapshot')
    rejected = [path for mode, kind, oid, path in rows if forbidden(path) or mode in ('120000', '160000')]
    if rejected:
        for path in rejected[:20]:
            print('FAIL prohibited path/mode:', path)
        print('FAIL prohibited entries:', len(rejected))
        return 1
    with tempfile.TemporaryDirectory(prefix='adminapps-secret-audit-') as tmp:
        base = Path(tmp) / 'objects'
        base.mkdir()
        for n, (mode, kind, oid, path) in enumerate(rows):
            data = git('cat-file', kind, oid)
            dest = base / str(n)
            dest.write_bytes(data)
            mapping[str(n)] = (path, hashlib.sha256(data).hexdigest())
            if Path(path).name.startswith('.env'):
                for line in data.decode(errors='replace').splitlines():
                    if re.match(r'^\s*[A-Za-z_][A-Za-z_0-9]*\s*=\s*\S', line):
                        print('FAIL populated environment template:', path)
                        failed = True
        report = Path(tmp) / 'report.json'
        config = Path(tmp) / 'gitleaks.toml'
        config.write_text('[extend]\nuseDefault = true\n')
        result = subprocess.run([binary, 'dir', '--no-banner', '--redact=100',
            '--config=' + str(config), '--ignore-gitleaks-allow',
            '--gitleaks-ignore-path=' + str(Path(tmp) / 'no-ignores'),
            '--report-format=json', '--report-path=' + str(report), str(base)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode not in (0, 1) or not report.exists():
            raise ValueError('Gitleaks execution failed (output suppressed)')
        findings = json.loads(report.read_text())
        for x in findings:
            path, digest = mapping[Path(x['File']).name]
            if (path, digest, x['RuleID'], x['StartLine']) not in allowed:
                print('FAIL', path, x['RuleID'], 'line', x['StartLine'])
                failed = True
    print(('FAIL' if failed else 'PASS'), 'secret audit:', len(rows), 'objects/path versions')
    return 1 if failed else 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', help='Audit entire reachable history (not just tip/diff)')
    args = parser.parse_args()
    try:
        raise SystemExit(audit(args.ref))
    except (OSError, ValueError, subprocess.CalledProcessError):
        print('FAIL audit unavailable: check Git state, scanner version and review manifest')
        raise SystemExit(2)
