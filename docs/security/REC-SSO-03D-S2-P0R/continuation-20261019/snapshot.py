import hashlib,json,pathlib,subprocess,shutil
root=pathlib.Path('/home/felipe/proyectos')
out=pathlib.Path('/tmp/rec-sso-03d-s2-p0r-continuation-20261019')
out.mkdir(exist_ok=False)
manifest={}
for name in ('adminapps','isosmart','ISO_Smart_MedSupplier'):
 repo=root/name
 def git(*args): return subprocess.check_output(['git','-C',str(repo),*args])
 files=git('ls-files','-z','--cached','--others','--exclude-standard').decode().split('\0')
 hashes={}
 for f in sorted(set(files)-{''}):
  p=repo/f
  if p.is_file(): hashes[f]=hashlib.sha256(p.read_bytes()).hexdigest()
 index=repo/git('rev-parse','--git-path','index').decode().strip()
 manifest[name]={'head':git('rev-parse','HEAD').decode().strip(),'status':git('status','--porcelain=v1','-uall').decode(),'index_sha256':hashlib.sha256(index.read_bytes()).hexdigest(),'files':hashes}
 targets={'adminapps':['backend/apps/subscriptions/views.py','backend/apps/subscriptions/serializers.py'], 'isosmart':['backend/integration/client.py'], 'ISO_Smart_MedSupplier':['backend/integration/client.py']}[name]
 for f in targets:
  dest=out/'before'/name/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/f,dest)
(out/'baseline.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:{'head':v['head'],'files':len(v['files']),'index_sha256':v['index_sha256']} for k,v in manifest.items()},indent=2))
