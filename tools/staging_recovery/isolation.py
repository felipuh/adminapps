"""Offline structural/local evidence checks. Never attest remote DB ACLs or deploy."""
import ast
from email.parser import Parser
import hashlib
import os
from pathlib import Path
import re
import shutil


def overlaps(a, b):
    a, b = Path(a).resolve(), Path(b).resolve()
    return a == b or a in b.parents or b in a.parents


def contains_active_path(candidate, active):
    candidate, active = Path(candidate).resolve(), Path(active).resolve()
    # An unrelated shell in / or /srv does not execute every descendant repo.
    return candidate == active or candidate in active.parents


def active_paths():
    """Read own visible processes; inability to inspect is a blocker, not absence."""
    paths, incomplete = set(), False
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            if int(proc.name) == os.getpid():
                continue
            paths.add(str((proc/'cwd').resolve(strict=True)))
            for arg in (proc/'cmdline').read_bytes().decode(errors='replace').split('\0'):
                executable = Path(arg)
                if executable.is_absolute() and executable.parent.name == 'bin' and executable.name in ('python', 'python3', 'python3.12', 'gunicorn', 'celery'):
                    paths.add(str(executable.parent.parent.resolve()))
        except FileNotFoundError:
            continue  # exited process
        except (OSError, RuntimeError):
            incomplete = True
    return paths, incomplete


def inspect_capacity(target, required, measured=None):
    if not isinstance(required, dict) or any(type(required.get(k)) is not int or required[k] <= 0 for k in ('disk_bytes','memory_bytes','cpus')):
        return ['measured_capacity_budget_required']
    if measured is None:
        try:
            mem = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
            measured = dict(disk_bytes=shutil.disk_usage(target).free,
                            memory_bytes=int(mem['MemAvailable'].split()[0])*1024, cpus=len(os.sched_getaffinity(0)))
        except (OSError, ValueError, KeyError):
            return ['target_capacity_unverified']
    return ['insufficient_'+k for k in required if k in ('disk_bytes','memory_bytes','cpus') and
            (type(measured.get(k)) is not int or measured[k] < required[k])]


def validate_inventory(plan):
    errors=[];databases=set();roles=set();volumes={};paths=[];secrets=set()
    apps=plan.get('applications',{}) if isinstance(plan,dict) else {}
    if not isinstance(apps,dict):return ['invalid_inventory']
    for product,app in apps.items():
        if not isinstance(app,dict):continue
        prefix=product+':'
        for key in ('source_path','venv_path','data_path'):
            value=app.get(key)
            if not isinstance(value,str):continue
            if any(overlaps(value,p) for p in paths):errors.append(prefix+'overlapping_paths')
            paths.append(value)
        dbs=app.get('databases',[])
        if not isinstance(dbs,list):continue
        aliases=set()
        for db in dbs:
            if not isinstance(db,dict):continue
            if db.get('engine')!='django.db.backends.postgresql':errors.append(prefix+'operational_postgresql_required')
            if any(not isinstance(db.get(k),str) or not db[k].strip() for k in ('alias','host','port','name','role','cluster_id','volume_id')):
                errors.append(prefix+'complete_database_destination_required');continue
            if db['alias'] in aliases:errors.append(prefix+'duplicate_database_alias')
            aliases.add(db['alias'])
            identity=(db['host'].lower(),db['port'],db['name'])
            role=(db['cluster_id'],db['role'])
            if identity in databases:errors.append(prefix+'shared_database_destination')
            if role in roles:errors.append(prefix+'shared_database_role')
            if db['volume_id'] in volumes and volumes[db['volume_id']]!=product:errors.append(prefix+'shared_database_volume')
            databases.add(identity);roles.add(role);volumes[db['volume_id']]=product
        required={'default'} if product=='ADMINAPPS' else {'default','ai_db','audit_db'}
        if not required.issubset(aliases):errors.append(prefix+'database_alias_inventory_incomplete')
        # These are provenance requirements only. No self-asserted value clears execution blockers.
        if not isinstance(app.get('secret_references'),dict) or any(not app['secret_references'].get(k) for k in ('django','database','sso')):
            errors.append(prefix+'secret_provenance_missing')
        if product!='ADMINAPPS' and (app.get('authority_product')!=product or app.get('identity_authority')!='ADMINAPPS'):
            errors.append(prefix+'incorrect_authority_or_product')
        references=app.get('secret_references',{})
        if isinstance(references,dict):
            for reference in references.values():
                if not isinstance(reference,str) or reference in secrets:errors.append(prefix+'independent_secret_reference_required')
                else:secrets.add(reference)
        redis=app.get('redis')
        if not isinstance(redis,dict) or redis.get('enabled') is not False:
            errors.append(prefix+'redis_isolation_requires_evidence')
    return errors


def inspect_local(plan, running=None):
    errors=[]
    if running is None:
        running,incomplete=active_paths()
        if incomplete:errors.append('active_process_inventory_incomplete')
    for product,app in plan.get('applications',{}).items():
        if not isinstance(app,dict):continue
        prefix=product+':'
        for key in ('source_path','venv_path','data_path'):
            value=app.get(key)
            if not isinstance(value,str):continue
            if not Path(value).is_dir():errors.append(prefix+key+'_not_inspectable')
            if any(contains_active_path(value,p) for p in running):errors.append(prefix+key+'_used_by_active_process')
        venv=Path(app.get('venv_path','/nonexistent'))
        try:
            config=dict(line.split('=',1) for line in (venv/'pyvenv.cfg').read_text().splitlines() if '=' in line)
            if {k.strip():v.strip() for k,v in config.items()}.get('include-system-site-packages')!='false':
                errors.append(prefix+'venv_not_independent')
        except OSError:errors.append(prefix+'venv_unverified')
        lock=app.get('dependency_lock',{})
        try:
            path=Path(lock['path']);raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=lock['sha256']:raise ValueError()
            lines=raw.decode().replace('\\\n',' ').splitlines()
            pins={}
            for line in lines:
                line=line.strip()
                if not line or line.startswith('#'):continue
                match=re.fullmatch(r'([A-Za-z0-9_.-]+)==([0-9][A-Za-z0-9.+-]*)\s+(?:--hash=sha256:[a-f0-9]{64}\s*)+',line)
                if not match:raise ValueError()
                pins[re.sub(r'[-_.]+','-',match[1]).lower()]=match[2]
            if not pins:raise ValueError()
            installed={}
            for meta in venv.glob('lib/python*/site-packages/*.dist-info/METADATA'):
                metadata=Parser().parsestr(meta.read_text())
                installed[re.sub(r'[-_.]+','-',metadata['Name']).lower()]=metadata['Version']
            if any(installed.get(n)!=version for n,version in pins.items()):errors.append(prefix+'dependency_lock_mismatch')
            if set(installed)-set(pins)-{'pip','setuptools','wheel'}:errors.append(prefix+'unlocked_installed_dependencies')
            django=installed.get('django','')
            if not django or django.startswith(('1.','2.','3.','4.','5.0.','5.1.')):
                errors.append(prefix+'unsupported_django_baseline')
            if django.startswith('6.'):
                source=Path(app['source_path'])/'backend'
                if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='CheckConstraint' and any(k.arg=='check' for k in n.keywords) for p in source.rglob('*.py') for n in ast.walk(ast.parse(p.read_text()))):
                    errors.append(prefix+'django6_removed_check_argument')
        except (OSError,KeyError,ValueError,TypeError,UnicodeError,SyntaxError):errors.append(prefix+'reproducible_dependency_lock_unverified')
    return errors
