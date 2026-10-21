import json,pathlib,subprocess
root=pathlib.Path('/home/felipe/proyectos');out=pathlib.Path('/tmp/rec-sso-03d-s2-p0r-continuation-20261019')
runs=json.loads((out/'runs.json').read_text())
for item in runs:
 if item['suite'] not in ('p0r','continuation'): continue
 with (out/(item['suite']+'.log')).open('w') as log:
  result=subprocess.run(item['cmd'],cwd=item['cwd'],stdout=log,stderr=subprocess.STDOUT,timeout=120)
 item['exit']=result.returncode
 print(json.dumps({'suite':item['suite'],'exit':item['exit']}),flush=True)
(out/'runs.json').write_text(json.dumps(runs,indent=2))
front=[]
for repo in ('isosmart','ISO_Smart_MedSupplier'):
 for decision in ('a','b'):
  cmd=['node',f'scripts/test-decision-{decision}-offline.mjs']
  log=out/f'{repo}-frontend-{decision}.log'
  with log.open('w') as stream:
   result=subprocess.run(cmd,cwd=root/repo/'frontend',stdout=stream,stderr=subprocess.STDOUT)
  front.append({'repo':repo,'cmd':cmd,'exit':result.returncode,'log':log.name})
(out/'frontend-checks.json').write_text(json.dumps(front,indent=2))
