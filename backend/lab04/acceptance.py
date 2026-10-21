from test_lab import *
import sys
phase=sys.argv[1]
if phase=='restart':
 v=json.loads((ROOT/'runtime/restart-tokens.json').read_text());before=Protected.calls;pid=fresh()
 assert probe(v['access'])==401 and Protected.calls==before
 rejected(lambda:life.refresh_pair(v['refresh']))
 result={'phase':phase,'access_http':401,'refresh':'DENIED','handler_delta':Protected.calls-before,'pid':pid,'token_sha256':hashlib.sha256(v['access'].encode()).hexdigest()}
else:
 u=user();pair=login(u);t=life.HumanRefreshToken(pair['refresh']);original=UserSession.objects.get(pk=t['sid'])
 assert probe(pair['access'])==200
 assert life.revoke(u,session_id=t['sid'])==1
 before=Protected.calls;assert probe(pair['access'])==401 and Protected.calls==before
 code=None
 try:
  # Same SQL and snapshot as LAB01 test_29, unchanged in both profiles.
  with transaction.atomic():
   raw('DELETE FROM user_sessions WHERE id=%s',[t['sid']])
   fields=[f for f in UserSession._meta.concrete_fields]
   raw('INSERT INTO user_sessions ('+','.join('"'+f.column+'"' for f in fields)+') VALUES ('+','.join(['%s']*len(fields))+')',[getattr(original,f.attname) for f in fields])
 except DatabaseError as e:code=getattr(e.__cause__, 'sqlstate', None) or getattr(e.__cause__, 'pgcode', None)
 pids=[fresh(),fresh()];assert pids[0]!=pids[1]
 before=Protected.calls;after=probe(pair['access']);delta=Protected.calls-before
 result={'phase':phase,'before_revoke':200,'after_revoke':401,'delete_reinsert_sqlstate':code,'after_attack_fresh_connection':after,'handler_delta_after_attack':delta,'pids':pids,'token_sha256':hashlib.sha256(pair['access'].encode()).hexdigest(),'sid':t['sid']}
 if phase=='old':
  assert after==200 and code is None;assert life.revoke(u,session_id=t['sid'])==1
 else:
  assert after==401 and delta==0 and code=='42501'
  rejected(lambda:life.refresh_pair(pair['refresh']));result['refresh']='DENIED'
  assert life.revoke(u,session_id=t['sid'])==0;result['lost_response_retry']=0
  f=ROOT/'runtime/restart-tokens.json';f.touch(mode=0o600);f.write_text(json.dumps(pair))
(ROOT/('acceptance-'+phase+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result));connections.close_all()
