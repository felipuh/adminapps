import collections,csv,difflib,hashlib,json,pathlib,shutil,subprocess
root=pathlib.Path('/home/felipe/proyectos');out=pathlib.Path('/tmp/rec-sso-03d-s2-p0r-continuation-20261019');prior=root/'adminapps/docs/security/REC-SSO-03D-S2-P0R';docs=prior/'continuation-20261019';docs.mkdir(exist_ok=True)
runs=json.loads((out/'runs.json').read_text());rows=[];origins={};comparison=[];counts=collections.Counter()
for run in runs:
 suite=run['suite'];p=out/(suite+'.methods.json')
 if not p.exists():continue
 data=json.loads(p.read_text());status=collections.Counter(m['status'] for m in data['methods']);counts.update(status)
 rows.append({'suite':suite,'methods':len(data['methods']),**{k:status[k] for k in ('PASS','FAIL','ERROR','SKIP')},'unittest':data['runners'],'exit':run['exit']})
 for m in data['methods']:
  key=(m['source'],m['line'],m['method']);origins[key]=m
 if suite=='continuation':continue
 old=json.loads((prior/(suite+'.methods.json')).read_text())
 a={m['id']:m['status'] for m in old['methods']};b={m['id']:m['status'] for m in data['methods']}
 comparison.append({'suite':suite,'same_method_ids_and_statuses':a==b,'changes':{k:{'before':a.get(k),'after':b.get(k)} for k in set(a)|set(b) if a.get(k)!=b.get(k)}})
new=[m for m in origins.values() if m['source'].endswith('test_p0r_continuation.py')]
summary={'new_unique_methods':len(new),'inherited_unique_methods_rerun':len(origins)-len(new),'unique_method_origins':len(origins),'selected_final_executions':sum(counts.values()),'statuses_per_execution':dict(counts),'suites':rows,'all_historical_statuses_unchanged':all(x['same_method_ids_and_statuses'] for x in comparison)}
(out/'test-summary.json').write_text(json.dumps(summary,indent=2));(out/'historical-reconciliation.json').write_text(json.dumps(comparison,indent=2));(out/'unique-methods.json').write_text(json.dumps(list(origins.values()),indent=2))
with (out/'test-matrix.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['suite','methods','PASS','FAIL','ERROR','SKIP','exit']);w.writeheader();w.writerows({k:v for k,v in row.items() if k!='unittest'} for row in rows)
# Overlay the route ledger without changing the inherited evidence.
with (prior/'authorization-delta.csv').open() as f:
 reader=csv.DictReader(f);fields=reader.fieldnames;ledger=list(reader)
newfields=['continuation_status','continuation_evidence','continuation_persistence']
with (out/'authorization-delta.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields+newfields);w.writeheader()
 for row in ledger:
  evidence=''
  if row['handler']=='apps.subscriptions.views.InvoiceViewSet' and row['action']=='mark_paid' and row['method']=='POST' and 'format' not in row['route']:
   evidence='InvoiceFunctionalContinuationTests: pending/overdue real serializer/effects; invalid references/states; replay and conflict; principal/elevation DENY'
  if row['handler']=='apps.users.views.UserViewSet' and row['action']=='revoke_sessions' and row['method']=='POST' and 'format' not in row['route']:
   evidence='LocalRegistryTokenContinuationTests: actual signed bearer dispatch; owner/current JTI derived from verified token; arbitrary keep-ID DENY; JWT revocation remains absent'
  if row['handler'] in {'apps.integration.views.get_organization', 'apps.integration.views.get_organization_users', 'apps.integration.views.get_organization_modules'} and row['method']=='GET':
   evidence='ConsumerDenialContinuationTests: both actual adapters through real router/credential hash/handler; suspended tenant 404 rejects local fallback'
  row.update(continuation_status='PASS_OFFLINE' if evidence else 'NOT_EVIDENCED',continuation_evidence=evidence,continuation_persistence='NOT_EVIDENCED');w.writerow(row)
# Only this invocation's diff; never compare accumulated work to HEAD.
targets={'adminapps':['backend/apps/subscriptions/serializers.py','backend/apps/subscriptions/views.py','backend/apps/api/test_p0r_continuation.py'],'isosmart':['backend/integration/client.py'],'ISO_Smart_MedSupplier':['backend/integration/client.py']}
changes=[];patch=[];baseline=json.loads((out/'baseline.json').read_text())
for repo,files in targets.items():
 for file in files:
  p=root/repo/file;before=out/'before'/repo/file;old=before.read_text() if before.exists() else '';newtext=p.read_text()
  patch.extend(difflib.unified_diff(old.splitlines(True),newtext.splitlines(True),fromfile=f'a/{repo}/{file}',tofile=f'b/{repo}/{file}'))
  compile(newtext,str(p),'exec')
  changes.append({'repo':repo,'path':file,'before_sha256':baseline[repo]['files'].get(file),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'compiled_in_memory':True})
(out/'code-hashes.json').write_text(json.dumps(changes,indent=2));(out/'continuation-only.patch').write_text(''.join(patch))
(out/'baseline-summary.json').write_text(json.dumps({'manifest':str(out/'baseline.json'),'manifest_sha256':hashlib.sha256((out/'baseline.json').read_bytes()).hexdigest(),'repositories':{k:{'head':v['head'],'index_sha256':v['index_sha256'],'file_count':len(v['files'])} for k,v in baseline.items()}},indent=2))
for name in ['test-summary.json','test-matrix.csv','historical-reconciliation.json','unique-methods.json','authorization-delta.csv','code-hashes.json','continuation-only.patch','baseline-summary.json','tool-availability.json','runs.json','frontend-checks.json','run_suite.py','snapshot.py']:
 shutil.copy2(out/name,docs/name)
for run in runs:
 for suffix in ('.log','.methods.json'):
  p=out/(run['suite']+suffix)
  if p.exists():shutil.copy2(p,docs/p.name)
for p in out.glob('*frontend*.log'):shutil.copy2(p,docs/p.name)
for name in ('reproduction-before.log','reproduction-5xx.log'):
 shutil.copy2(out/name,docs/name)
shutil.copy2('/tmp/p0r_continuation_run.py',docs/'run_all.py');shutil.copy2('/tmp/p0r_continuation_finish_checks.py',docs/'run_final_checks.py')
shutil.copy2(__file__,docs/'build_evidence.py')
print(json.dumps(summary,indent=2))
