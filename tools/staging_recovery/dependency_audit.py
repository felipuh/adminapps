"""Inspect metadata only; no Django setup, installs, database or network calls."""
import importlib.metadata as metadata
import json
from pathlib import Path
import sys
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

packages={canonicalize_name(d.metadata['Name']):d for d in metadata.distributions() if d.metadata['Name']}
errors=[]
for name,d in packages.items():
    for raw in d.requires or []:
        r=Requirement(raw)
        if r.marker and not r.marker.evaluate({'extra':''}):continue
        target=packages.get(canonicalize_name(r.name))
        if not target or (r.specifier and Version(target.version) not in r.specifier):
            errors.append({'package':name,'dependency':r.name,'specifier':str(r.specifier),'installed':target.version if target else None})
requirements={}
for arg in sys.argv[1:]:
    path=Path(arg);issues=[]
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith(('#','-')):continue
        r=Requirement(line);installed=packages.get(canonicalize_name(r.name))
        if r.url or not installed or (r.specifier and Version(installed.version) not in r.specifier):
            issues.append(dict(package=r.name,expected=str(r.specifier) if not r.url else 'direct_url_requires_provenance',installed=installed.version if installed else None))
    requirements[str(path)]=issues
print(json.dumps(dict(python=sys.version.split()[0],prefix=sys.prefix,packages={n:d.version for n,d in packages.items()},
    requires_python={n:d.metadata.get('Requires-Python') for n,d in packages.items() if n in ('django','django-filter','django-cors-headers','psycopg2-binary','psycopg','djangorestframework','djangorestframework-simplejwt')},
    incompatibilities=errors,manifest_mismatches=requirements),indent=2))
