#!/usr/bin/env python3
"""Install checksum-pinned Linux x64 scanner and repository hooks (no secrets)."""
import hashlib
import io
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import urllib.request

assert platform.system() == 'Linux' and platform.machine() == 'x86_64'
root = Path(__file__).resolve().parents[2]
data = urllib.request.urlopen('https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz').read()
assert hashlib.sha256(data).hexdigest() == '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb'
dest = Path.home() / '.local/bin/gitleaks'
dest.parent.mkdir(parents=True, exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(data)) as archive:
    dest.write_bytes(archive.extractfile('gitleaks').read())
dest.chmod(0o755)
subprocess.run(['git', 'config', '--local', 'core.hooksPath', str(root / '.githooks')], check=True)
print('Installed Gitleaks 8.30.1 and hooks. Put ~/.local/bin in PATH.')
