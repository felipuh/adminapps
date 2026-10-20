import concurrent.futures,json,pathlib,subprocess,shutil
root=pathlib.Path('/home/felipe/proyectos'); out=pathlib.Path('/tmp/rec-sso-03d-s2-p0r-continuation-20261019')
prior=root/'adminapps/docs/security/REC-SSO-03D-S2-P0R'
shutil.copy2(prior/'run_suite.py',out/'run_suite.py')
shutil.copy2('/tmp/p0r-continuation-reproduction.log',out/'reproduction-before.log')
shutil.copy2('/tmp/p0r-continuation-before.log',out/'development-imported-suite.log')
shutil.copy2('/tmp/p0r_continuation_snapshot.py',out/'snapshot.py')
configs=[]
for repo,filename,cwd in [('adminapps','adminapps-runs.json',root/'adminapps'),('isosmart','isosmart-runs.json',root/'isosmart/backend'),('ISO_Smart_MedSupplier','ISO_Smart_MedSupplier-runs.json',root/'ISO_Smart_MedSupplier/backend')]:
 for item in json.loads((prior/filename).read_text()):
  cmd=[arg.replace('/tmp/rec-sso-03d-s2-p0r-20261019/',str(out)+'/') for arg in item['cmd']]
  configs.append({'repo':repo,'suite':item['suite'],'cwd':str(cwd),'cmd':cmd})
configs.append({'repo':'adminapps','suite':'continuation','cwd':str(root/'adminapps'),'cmd':['backend/.venv/bin/python','-B',str(out/'run_suite.py'),str(out/'continuation.methods.json'),'backend/scripts/rec_sso_03d_api_p0_offline.py','apps.api.test_p0r_continuation']})
configs.append({'repo':'adminapps','suite':'system-check','cwd':str(root/'adminapps'),'cmd':['backend/.venv/bin/python','-B','backend/scripts/rec_sso_03d_api_p0_offline.py','--check']})
def run(item):
 with (out/(item['suite']+'.log')).open('w') as log:
  p=subprocess.run(item['cmd'],cwd=item['cwd'],stdout=log,stderr=subprocess.STDOUT,timeout=240)
 return {**item,'exit':p.returncode}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 results=[]
 for item in pool.map(run,configs):
  results.append(item);print(json.dumps({'suite':item['suite'],'exit':item['exit']}),flush=True)
(out/'runs.json').write_text(json.dumps(results,indent=2))
