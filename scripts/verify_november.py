"""Offline baseline checks; no databases, servers or external API calls."""
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
           OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
JOBS = [['backend/scripts/rec_sso_03d_p0r2_r1_offline.py'], ['backend/scripts/p0_historical_permissions_offline.py'], ['-m', 'unittest', 'discover', '-s', 'tools/staging_recovery', '-p', 'test_*.py', '-v']]
CWD = ROOT
for command in JOBS:
    subprocess.run([sys.executable, '-B', *command], cwd=CWD, env=ENV, check=True)
if '--ecosystem' in sys.argv:
    # Explicit consumer interpreters are required; never infer active runtimes.
    for key in ('REC_SSO_ISO_PYTHON', 'REC_SSO_MED_PYTHON'):
        if not os.environ.get(key):
            raise SystemExit('Set ' + key + ' to an independent candidate interpreter')
    subprocess.run([sys.executable, '-B', 'backend/scripts/rec_sso_03b_offline.py'], cwd=ROOT, env=ENV, check=True)
