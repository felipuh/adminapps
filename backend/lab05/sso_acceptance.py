"""LAB05-C1-R1 real HTTP/SQL acceptance. Secrets never enter retained evidence."""
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(os.environ['LAB04_ROOT'])
HERE = Path(__file__).resolve().parent
processes, streams, cases = [], [], []
ports = {}
import jwt
import psycopg2
client = json.loads((ROOT / 'runtime/sso-client.json').read_text())
trust = json.loads((ROOT / 'runtime/central-trust.json').read_text())
context = {k: client[k] for k in ('client_id', 'audience', 'product', 'contract_version')}
headers = {'X-API-Key': client['credential']}
base = '/api/integration/sso/'

def sso(name, endpoint, expected, payload=None, supplied=None, denied=False):
    before = cases[-1]['protected_stages'].copy() if cases and cases[-1]['profile'] == 'sso' else None
    result = call('sso', base + endpoint, expected, {**context, **(payload or {})},
                  headers=headers if supplied is None else supplied)
    cases[-1]['scenario'] = name
    if denied:
        assert result.get('active') is not True and 'tokens' not in result
        if before is not None:
            assert cases[-1]['protected_stages'] == before
            cases[-1]['protected_stages_unchanged'] = True
    return result



def call(profile, path, expected, payload, token=None, headers=None):
    conn = http.client.HTTPConnection('127.0.0.1', ports[profile], timeout=15)
    supplied = {'Content-Type': 'application/json', **(headers or {})}
    if token:
        supplied['Authorization'] = 'Bearer ' + token
    start = time.monotonic()
    try:
        conn.request('POST', path, json.dumps(payload), supplied)
        response = conn.getresponse()
        body = response.read()
        elapsed = round((time.monotonic() - start) * 1000, 3)
        assert response.status == expected, (profile, path, response.status, expected)
        content_type = response.getheader('Content-Type', '')
    finally:
        conn.close()
    observed = json.loads((ROOT / ('http-' + profile + '-state.json')).read_text())
    assert observed['principal'] == observed['session_user'] == 'lab04_' + profile
    cases.append({'profile': profile, 'path': path, 'method': 'POST',
                  'status': expected, 'elapsed_ms': elapsed, **observed})
    return json.loads(body) if content_type.startswith('application/json') else None


try:
    for profile in ('iam', 'control_plane', 'sso'):
        stream = (ROOT / ('http-' + profile + '.log')).open('w')
        streams.append(stream)
        process = subprocess.Popen([sys.executable, str(HERE / 'http_server.py')],
            env={**os.environ, 'LAB05_HTTP': '1', 'LAB04_PROFILE': profile,
                 'LAB04_ROLE': 'lab04_' + profile}, stdout=stream, stderr=stream)
        processes.append(process)
        ready = ROOT / ('http-' + profile + '-ready.json')
        deadline = time.monotonic() + 30
        while not ready.exists():
            assert process.poll() is None, 'HTTP process exited; inspect private local log'
            assert time.monotonic() < deadline, 'HTTP readiness timed out'
            time.sleep(.1)
        value = json.loads(ready.read_text())
        assert value['principal'] == 'lab04_' + profile
        ports[profile] = value['port']
    assert len(set(ports.values())) == 3
    credentials = {'email': 'viewer@example.invalid', 'password': client['password'],
                   'organization_id': client['tenant']}
    pair = sso('registered_login', 'login/', 200, credentials)['tokens']
    token = pair['access_token']
    decoded = jwt.decode(token, trust['PUBLIC_KEYS'][trust['SIGNING_KID']],
                         algorithms=['RS256'], audience=client['audience'][0], issuer=trust['ISSUER'])
    assert jwt.get_unverified_header(token)['kid'] == trust['SIGNING_KID']
    assert decoded['token_family'] == 'CENTRAL' and decoded['product'] == 'ISO_SMART'
    assert decoded['tenant_id'] == client['tenant'] and decoded['client_id'] == client['client_id']
    active = sso('live_introspection', 'introspect/', 200, {'token': token})
    assert active['active'] is True and active['authorization']['state'] == 'active'
    assert active['authorization']['scopes'] == ['ISO_SMART:core.document:read']
    sso('unregistered_principal', 'login/', 401, credentials,
        {'X-API-Key': client['unregistered']}, denied=True)
    sso('wrong_client', 'login/', 401, {**credentials, 'client_id': 'not-registered'}, denied=True)
    sso('wrong_audience_request', 'login/', 401, {**credentials, 'audience': ['wrong']}, denied=True)
    sso('wrong_product_request', 'login/', 401, {**credentials, 'product': 'MEDSUPPLIER'}, denied=True)
    sso('foreign_tenant', 'login/', 403, {**credentials, 'organization_id': client['foreign']}, denied=True)
    sso('forged_headers', 'login/', 401, credentials,
        {'X-Client-ID': client['client_id'], 'X-Product': 'ISO_SMART',
         'X-Tenant-ID': client['tenant'], 'X-Role': 'superadmin'}, denied=True)
    for claim, value in [('aud', ['wrong']), ('iss', 'https://wrong.example.invalid'),
                         ('tenant_id', client['foreign']), ('product', 'MEDSUPPLIER'), ('exp', int(time.time())-1)]:
        altered = dict(decoded, **{claim: value})
        if claim == 'tenant_id':
            altered['organization_id'] = value
        proof = jwt.encode(altered, trust['PRIVATE_KEY'], algorithm='RS256',
                           headers={'kid': trust['SIGNING_KID']})
        sso('wrong_token_' + claim, 'introspect/', 401 if claim == 'tenant_id' else 200,
            {'token': proof}, denied=True)
    from cryptography.hazmat.primitives.asymmetric import rsa
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    proof = jwt.encode(decoded, other_key, algorithm='RS256', headers={'kid': trust['SIGNING_KID']})
    sso('invalid_signature', 'introspect/', 200, {'token': proof}, denied=True)
    proof = jwt.encode(decoded, client['unregistered'], algorithm='HS256', headers={'kid': trust['SIGNING_KID']})
    sso('wrong_algorithm', 'introspect/', 200, {'token': proof}, denied=True)
    proof = jwt.encode(decoded, trust['PRIVATE_KEY'], algorithm='RS256', headers={'kid': 'unknown'})
    sso('wrong_kid', 'introspect/', 200, {'token': proof}, denied=True)
    sso('2fa_route_missing_payload', 'login/verify-2fa/', 400, denied=True)
    rotated = sso('rotate', 'rotate/', 200, {'token': token})['tokens']['access_token']
    sso('old_generation', 'introspect/', 401, {'token': token}, denied=True)
    assert sso('rotated_active', 'introspect/', 200, {'token': rotated})['active'] is True
    assert sso('logout', 'logout/', 200, {'token': rotated})['revoked'] is True
    sso('revoked_new_connection', 'introspect/', 401, {'token': rotated}, denied=True)
    sso('revoked_reconnect_again', 'introspect/', 401, {'token': rotated}, denied=True)
    sso('revoked_rotation', 'rotate/', 401, {'token': rotated}, denied=True)
    import pyotp
    challenge = sso('2fa_challenge', 'login/', 200, {**credentials, 'email': 'target@example.invalid'})
    assert challenge['requires_2fa'] is True and 'tokens' not in challenge
    payload = {'challenge_token': challenge['challenge_token'], 'otp_code': pyotp.TOTP(client['otp_secret']).now()}
    mfa_pair = sso('2fa_verify', 'login/verify-2fa/', 200, payload)['tokens']
    mfa_live = sso('2fa_introspection', 'introspect/', 200, {'token': mfa_pair['access_token']})
    assert mfa_live['active'] is True and mfa_live['amr'] == ['pwd', 'otp']
    replay = sso('2fa_replay', 'login/verify-2fa/', 403, payload, denied=True)
    assert replay['code'] == 'invalid_or_expired_challenge'
    assert sso('2fa_logout', 'logout/', 200, {'token': mfa_pair['access_token']})['revoked'] is True
    sql_creds = json.loads((ROOT / 'runtime/credentials-lab04_sso.json').read_text())
    db = psycopg2.connect(dbname='lab04_human', user='lab04_sso', password=sql_creds['password'],
                          host=str(ROOT / 'runtime/socket'), port=56434)
    db.autocommit = True
    sql_cases = []
    with db.cursor() as q:
        q.execute("SELECT state,revoked_at IS NOT NULL,revocation_reason FROM sso_sessions WHERE id=%s", [decoded['sid']])
        assert q.fetchone() == ('revoked', True, 'logout')
        q.execute("SELECT count(*) FROM sso_revocation_outbox WHERE session_id=%s AND reason='logout'", [decoded['sid']])
        assert q.fetchone()[0] == 1
        for statement in ["DELETE FROM sso_sessions WHERE id=%s", "TRUNCATE sso_sessions",
                          "UPDATE sso_sessions SET state='active',revoked_at=NULL,generation=generation+1 WHERE id=%s",
                          "UPDATE integration_sso_clients SET enabled=false",
                          "UPDATE product_systems SET billing_enabled=true",
                          "UPDATE users SET is_superuser=true"]:
            try:
                q.execute(statement, [decoded['sid']] if '%s' in statement else None)
            except psycopg2.Error as exc:
                assert exc.pgcode in ('42501', 'P0001', '23514')
                sql_cases.append({'statement': statement, 'sqlstate': exc.pgcode})
            else:
                raise AssertionError('SQL authority escape')
        q.execute("SELECT table_name, privilege_type FROM information_schema.role_table_grants WHERE grantee=current_user ORDER BY 1,2")
        grants = q.fetchall()
    db.close()
    # Fresh HTTP connections after actual rejected SQL mutations still reject revoked authority.
    sso('revocation_retained_after_sql', 'introspect/', 401, {'token': rotated}, denied=True)
    for profile in ('iam', 'control_plane'):
        for endpoint in ('login/', 'login/verify-2fa/', 'introspect/', 'logout/', 'rotate/'):
            call(profile, base + endpoint, 404, context, headers=headers)
    for path in ('/api/integration/health/', '/api/integration/organizations/',
                 '/api/integration/landing-analytics/events/', '/api/integration/demo-requests/',
                 '/api/integration/ai-usage/', '/api/products/systems/', '/api/billing/',
                 '/api/auth/login/', '/admin/'):
        call('sso', path, 404, {}, headers=headers)
    sso_cases = [c for c in cases if c['profile'] == 'sso']
    assert len({c['backend_pid'] for c in sso_cases}) == len(sso_cases)
    (ROOT / 'http-result.json').write_text(json.dumps({
        'status': 'LAB05_C1_R1_CENTRAL_SSO_HTTP_PASS',
        'transport': 'real loopback TCP HTTP', 'postgresql': 'disposable private Unix socket',
        'consumer_started': False, 'consumer_e2e_pass': False,
        'trust': {'family': 'CENTRAL', 'algorithm': 'RS256', 'kid_verified': True,
                  'issuer_verified': True, 'audience_verified': True, 'tenant_product_verified': True},
        'pending': ['consumer E2E and protected consumer handlers'],
        'sql_cases': sql_cases, 'sso_table_grants': grants, 'cases': cases,
    }, indent=2))
    print('LAB05_C1_R1_CENTRAL_SSO_HTTP_PASS')

finally:
    for process in processes:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    for stream in streams:
        stream.close()
    (ROOT / 'http-cleanup.json').write_text(json.dumps({
        'http_processes_stopped': all(p.poll() is not None for p in processes),
        'http_process_count': len(processes),
    }, indent=2))
