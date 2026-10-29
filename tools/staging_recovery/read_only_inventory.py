"""Local read-only inventory. No Django imports, network, database, or secret output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
from dotenv import dotenv_values


def run(args):
    return subprocess.run(args,capture_output=True,text=True,check=False)


def digest(value):
    return 'ref-'+hashlib.sha256(str(value).encode()).hexdigest()[:16]


def inventory(source_root):
    result={'scope':'read-only configuration references, not database or in-memory settings attestation','services':{},'capacity':{}}
    for name,repo in [('adminapps','adminapps'),('isosmart','isosmart'),('medsupplier','ISO_Smart_MedSupplier')]:
        root=source_root/repo;backend=root/'backend';unit=name+'-backend.service'
        raw=run(['systemctl','show',unit,'-p','WorkingDirectory','-p','MainPID','-p','ActiveState','-p','SubState','-p','NRestarts','-p','ExecStart','-p','Environment','-p','EnvironmentFiles','-p','FragmentPath','-p','DropInPaths']).stdout
        props=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
        env_path=backend/'.env';env=dict(dotenv_values(env_path,interpolate=False))
        initial={}
        try:
            initial=dict(pair.split('=',1) for pair in Path('/proc/'+props['MainPID']+'/environ').read_bytes().decode().split('\0') if '=' in pair)
        except (OSError,KeyError):pass
        unit_env=dict(pair.split('=',1) for pair in shlex.split(props.get('Environment','')) if '=' in pair)
        env.update(unit_env);env.update(initial)
        record={k:props.get(k) for k in ('WorkingDirectory','MainPID','ActiveState','SubState','NRestarts','EnvironmentFiles','FragmentPath','DropInPaths')}
        record['exec_paths']=re.findall(r'path=([^ ;]+)',props.get('ExecStart',''))
        record['binds']=re.findall(r'--bind ([^ ;]+)',props.get('ExecStart',''))
        record['settings_module']=env.get('DJANGO_SETTINGS_MODULE') or ('config.settings (WSGI default)' if name=='adminapps' else 'backend.settings (WSGI default)')
        record['environment']=env.get('DJANGO_ENV',env.get('ENVIRONMENT','development'))
        record['flags']={k:env[k] if str(env[k]).lower() in ('true','false','0','1','yes','no','on','off') else 'unresolved' for k in env if k in ('DEBUG','USE_SQLITE_DATABASE','ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS','ALLOW_LOCAL_AUTH_FALLBACK','ADMIN_APPS_ALLOW_LOCAL_FALLBACK','SMART3AI_SSO_ALLOW_2FA_BYPASS')}
        record['postgres_variables_present']={k:bool(env.get(k)) for k in ('DB_HOST','DB_PORT','DB_NAME','DB_USER','DB_PASSWORD')}
        record['destinations']={}
        for alias,prefix in [('default','DB'),('ai_db','AI_DB'),('audit_db','AUDIT_DB')]:
            if name=='adminapps' and alias!='default':continue
            host=env.get(prefix+'_HOST',env.get('DB_HOST','127.0.0.1'));port=env.get(prefix+'_PORT',env.get('DB_PORT','5432'))
            db=env.get(prefix+'_NAME','UNVERIFIED');user=env.get(prefix+'_USER',env.get('DB_USER','UNVERIFIED'))
            record['destinations'][alias]={'endpoint':digest(host+':'+port),'database':digest(host+':'+port+'/'+db),'role':digest(host+':'+port+'/'+user),'declared_only':True}
        record['fingerprints']={}
        for p in (env_path,root/'.git/index',Path(props.get('FragmentPath','/nonexistent'))):
            if p.is_file():record['fingerprints'][str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
        journal=run(['journalctl','-u',unit,'-n','100','--no-pager','-o','cat']).stdout
        record['journal_sqlite_guard_count']=journal.count('SQLite is only permitted with backend.settings_test')
        record['journal_references_expected_checkout']=str(backend) in journal
        record['head']=run(['git','--no-optional-locks','-C',str(root),'rev-parse','HEAD']).stdout.strip()
        record['git_status']=run(['git','--no-optional-locks','-C',str(root),'status','--porcelain']).stdout.strip()
        record['processes']=[]
        for proc in Path('/proc').glob('[0-9]*'):
            try:
                if str((proc/'cwd').resolve(strict=True))!=str(backend):continue
                status=proc.joinpath('status').read_text()
                rss=re.search(r'VmRSS:\s+(\d+)',status)
                record['processes'].append({'pid':int(proc.name),'cwd':str(backend),'rss_KiB':int(rss[1]) if rss else None,'executable':str((proc/'exe').resolve(strict=True))})
            except (OSError,RuntimeError):pass
        result['services'][name]=record
    mem=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    result['capacity']={'cpus':len(os.sched_getaffinity(0)), 'memory_available_bytes':int(mem['MemAvailable'].split()[0])*1024,
                        'memory_total_bytes':int(mem['MemTotal'].split()[0])*1024,
                        'home_free_bytes':shutil.disk_usage(source_root).free,'tmp_free_bytes':shutil.disk_usage('/tmp').free}
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source_root',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    args.output.write_text(json.dumps(inventory(args.source_root),indent=2)+'\n')
    print('Wrote redacted read-only inventory:',args.output)
