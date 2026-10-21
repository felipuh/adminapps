import pathlib,json,csv,collections,shutil,hashlib
out=pathlib.Path('/tmp/rec-sso-03d-s2-p0r-20261019');docs=pathlib.Path('/home/felipe/proyectos/adminapps/docs/security/REC-SSO-03D-S2-P0R')
sources=[]
for repo in ('adminapps','isosmart','ISO_Smart_MedSupplier'):
 sources.extend(x['suite'] for x in json.loads((out/(repo+'-runs.json')).read_text()))
rows=[];origins={};totals=collections.Counter();new=set();inherited=set()
for name in sources:
 d=json.loads((out/(name+'.methods.json')).read_text());counts=collections.Counter(m['status'] for m in d['methods']);totals.update(counts)
 for m in d['methods']:
  key=(m['source'],m['line'],m['method']);origins.setdefault(key,[]).append({'suite':name,'id':m['id'],'status':m['status']})
  (new if name.startswith('p0r') else inherited).add(key)
 rows.append({'suite':name,'methods_executed':len(d['methods']),**{s:counts[s] for s in ('PASS','FAIL','ERROR','SKIP')},'unittest':d['runners']})
summary={'new_unique_methods':len(new),'inherited_unique_methods':len(inherited),'executions':sum(totals.values()),'unique_method_origins':len(origins),'statuses_per_execution':dict(totals),'suites':rows,'note':'One final selected run per suite. Development repeats, baseline and reproduction excluded. Inheritance deduplicated by source/line/method; generated concrete methods distinguished by their names.'}
(out/'test-summary.json').write_text(json.dumps(summary,indent=2))
(out/'unique-methods.json').write_text(json.dumps([{'source':k[0],'line':k[1],'method':k[2],'executions':v} for k,v in origins.items()],indent=2))
with (docs/'test-matrix.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['suite','methods_executed','PASS','FAIL','ERROR','SKIP','handler','effects','persistence']);w.writeheader()
 for r in rows:w.writerow({**{k:v for k,v in r.items() if k!='unittest'},'handler':'real code; scope per method','effects':'simulated ORM/services only','persistence':'NOT_EVIDENCED'})
# Carry the inherited branch ledger alongside the newly resolved router inventory.
with (out/'inherited/authorization-delta.csv').open() as f:old={(r['route'],r['method'],r['handler'],r['action']):r for r in csv.DictReader(f)}
with (out/'inventory/endpoint-inventory.csv').open() as f:inventory=list(csv.DictReader(f))
newmap={
 ('UserViewSet','revoke_sso_sessions','POST'):('test_central_revocation_dispatch_real_uuid_serializer_and_scope','UUID serializer; service separately executed with RSA proofs'),
 ('UserViewSet','revoke_sessions','POST'):('test_local_registry_revocation_reports_its_limit_and_keeps_owner_filter','Known access-JWT limitation characterized; not a closure'),
 ('UserViewSet','change_password','POST'):('test_user_password_change_real_serializer_hash_and_audit','Real serializer/password hash; audit/save simulated'),
 ('UserViewSet','deactivate','POST'):('test_user_disable_effect_and_self_disable_denied','is_active mutation/save; central SQL trigger not executed'),
 ('SubscriptionViewSet','change_plan','POST'):('test_subscription_change_plan_effect_and_missing_plan_deny','Real UUID serializer; plan/amount mutation'),
 ('SubscriptionViewSet','activate','POST'):('test_subscription_activation_and_cancellation_execute_model_effects','Real model transition/dates; save simulated'),
 ('SubscriptionViewSet','cancel','POST'):('test_subscription_activation_and_cancellation_execute_model_effects','Real model transition/dates; save simulated'),
 ('InvoiceViewSet','mark_paid','POST'):('test_invoice_payment_executes_subscription_activation','Real invoice/subscription transitions; save simulated'),
 ('OrganizationProductEntitlementViewSet','partial_update','PATCH'):('test_entitlement_restrictive_patch_real_serializer_and_audit','Disabled/scopes cleared; real serializer/audit payload'),
 ('UserOrganizationViewSet','partial_update','PATCH'):('test_membership_deactivation_then_foreign_reference_denied','Real serializer; disabled membership; foreign reference DENY'),
 ('OrganizationViewSet','suspend','POST'):('test_tenant_suspend_is_idempotent_and_emits_one_event','Real handler; save/event simulated once'),
 ('OrganizationInvitationViewSet','accept','POST'):('test_preview_revalidates_authority_without_consuming','Preview only; consumption tested separately through RegisterView'),
 ('RegisterView','post','POST'):('test_registration_dispatch_emits_signed_tokens_after_live_consumption','Real serializer/hash/signed JWT; user/membership/save simulated'),
 ('LogoutView','post','POST'):('test_logout_real_signed_refresh_idempotent_and_foreign_denied','Real signed refresh; blacklist/audit persistence simulated'),
}
fields=['route','method','handler','action','boundary','inherited_status','inherited_positive_test','p0r_status','p0r_evidence','effects','persistence','remaining_branches']
with (docs/'authorization-delta.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in inventory:
  k=(r['route'],r['method'],r['handler'],r['action']);prior=old.get(k,{})
  evidence=newmap.get((r['handler'].split('.')[-1],r['action'],r['method']))
  if r['additional_boundary']=='service_data_access' and r['method'] in ('GET','POST'):
   evidence=('test_both_adapters_all_seven_legacy_handlers_with_authenticated_credential','Both actual clients → router → seven real handlers; credential hash checked, ORM/HTTP transport simulated')
  if 'format' in r['route'] or r['method'] in ('HEAD','OPTIONS'):evidence=None
  w.writerow({'route':r['route'],'method':r['method'],'handler':r['handler'],'action':r['action'],'boundary':r['additional_boundary'],'inherited_status':prior.get('status','NEW_ROUTE'),'inherited_positive_test':prior.get('positive_test',''),'p0r_status':'PASS_OFFLINE' if evidence else 'NOT_EVIDENCED','p0r_evidence':evidence[0] if evidence else '', 'effects':evidence[1] if evidence else 'No additional functional branch in this slice','persistence':'NOT_EVIDENCED','remaining_branches':'Not full branch coverage; aliases/SQL/commercial policy not certified'})
# Exact original inventory entries were preserved; four entries are the new action/format/OPTIONS.
oldkeys=set(old);newkeys={(r['route'],r['method'],r['handler'],r['action']) for r in inventory}
(docs/'resolver-reconciliation.json').write_text(json.dumps({'inherited_entries':len(oldkeys),'current_entries':len(newkeys),'removed':list(oldkeys-newkeys),'added':list(newkeys-oldkeys)},indent=2))
b=json.loads((out/'baseline.json').read_text())
(docs/'baseline-summary.json').write_text(json.dumps({'full_manifest':str(out/'baseline.json'),'manifest_sha256':hashlib.sha256((out/'baseline.json').read_bytes()).hexdigest(),'repos':{k:{a:v[a] for a in ('head','index','status')}|{'file_count':len(v['files'])} for k,v in b.items()}},indent=2))
for name in ('test-summary.json','unique-methods.json','historical-reconciliation.json','checks.json','system-check.log','inventory.log','p0r-only.patch','code-hashes.json','integrity-final.json','run_suite.py','reproduce_baseline.py','reproduction.log','reproduction-corrected.log','build_report_data.py'):
 if (out/name).exists():shutil.copy2(out/name,docs/name)
for p in out.glob('*-runs.json'):shutil.copy2(p,docs/p.name)
for name in sources:
 for suffix in ('.log','.methods.json'):shutil.copy2(out/(name+suffix),docs/(name+suffix))
for p in out.glob('baseline-*.log'):shutil.copy2(p,docs/p.name)
for p in out.glob('baseline-*.methods.json'):shutil.copy2(p,docs/p.name)
for name in ('endpoint-inventory.csv','inventory-summary.json'):shutil.copy2(out/'inventory'/name,docs/name)
# Preserve the starting report and ledger explicitly; no edits to historical originals.
for name in ('REPORT.md','authorization-delta.csv','code-hashes.json','SHA256SUMS'):
 if (out/'inherited'/name).exists():shutil.copy2(out/'inherited'/name,docs/('inherited-'+name))
print(json.dumps({k:summary[k] for k in ('new_unique_methods','inherited_unique_methods','executions','unique_method_origins','statuses_per_execution')}))
