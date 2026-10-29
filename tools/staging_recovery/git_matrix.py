"""Inspect local Git objects/content; never integrate, fetch, or publish history."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'adminapps/docs/evidence/p0-remediation-2026-10-29/git-matrix.json'

def git(repo,*args):
    return subprocess.run(['git','--no-optional-locks','-C',str(ROOT/repo),*args],capture_output=True)

matrix={}
for repo,baseline,old in [('adminapps','9cd64e04','047d5868'),('isosmart','61bf5a27','0ce01dff'),('ISO_Smart_MedSupplier','5bfcddc9','6a5fd036')]:
    entry={'baseline':git(repo,'rev-parse',baseline).stdout.decode().strip(),'head':git(repo,'rev-parse','HEAD').stdout.decode().strip(),
           'historical_reference':old,'historical_ancestor':git(repo,'merge-base','--is-ancestor',old,baseline).returncode==0,
           'merge_base':git(repo,'merge-base',old,baseline).stdout.decode().strip() or None,
           'subsequent_commits':git(repo,'log','--format=%h %s',old+'..'+baseline,'--','backend/authentication','backend/integration','backend/apps','backend/config').stdout.decode().splitlines(),
           'baseline_status':git(repo,'status','--porcelain').stdout.decode().splitlines()}
    if repo=='adminapps':
        sha=entry['baseline'];raw=git(repo,'cat-file','commit',sha).stdout
        entry['audit_commit_integrity']=hashlib.sha1(b'commit '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==sha
        entry['audit_parent']=git(repo,'rev-parse',sha+'^').stdout.decode().strip()
        fsck=git(repo,'fsck','--connectivity-only','--no-reflogs',sha)
        entry['connectivity_exit_code']=fsck.returncode
        manifest=json.loads((ROOT/repo/'docs/security/REC-GIT-SEC-01/snapshot-manifest.json').read_text())
        matched=[];changed=[];missing=[]
        for path,expected in manifest['sha256'].items():
            data=git(repo,'show',baseline+':'+path)
            if data.returncode:missing.append(path)
            elif hashlib.sha256(data.stdout).hexdigest()==expected:matched.append(path)
            else:changed.append(path)
        entry['sanitized_manifest']={'source':manifest['source_commit'],'matched_count':len(matched),'changed':changed,'missing':missing,
            'lab04_matching_count':sum(p in matched for p in manifest['lab04_identical_files'])}
        entry['historical_fix_files']={}
        for commit in ('8e67dcb3','fe671855','dc723be2','54d201e5'):
            paths=git(repo,'diff-tree','--no-commit-id','--name-only','-r',commit).stdout.decode().splitlines()
            entry['historical_fix_files'][commit]=[{'path':p,'identical_to_fix':git(repo,'diff','--quiet',commit,baseline,'--',p).returncode==0,'present':git(repo,'cat-file','-e',baseline+':'+p).returncode==0} for p in paths]
    if repo=='isosmart':
        entry['later_sso_branch']='e212a5ed'
        entry['later_sso_merge_base']=git(repo,'merge-base',baseline,'e212a5ed').stdout.decode().strip() or None
        entry['later_sso_auth_diff']=git(repo,'diff','--stat',baseline,'e212a5ed','--','backend/authentication','backend/integration').stdout.decode().strip()
    matrix[repo]=entry
OUT.write_text(json.dumps(matrix,indent=2)+'\n')
print(json.dumps({r:{k:v for k,v in e.items() if k in ('audit_commit_integrity','audit_parent','connectivity_exit_code','historical_ancestor','sanitized_manifest','historical_fix_files','later_sso_merge_base')} for r,e in matrix.items()},indent=2))
