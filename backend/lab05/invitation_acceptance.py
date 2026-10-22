"""LAB05-B: actual HTTP/SQL, no Django test client or mocked authorization.

Maintenance SQL only observes committed state or installs/removes explicit fault
triggers. Business transitions use existing IAM/CP endpoints in separate workers.
"""
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psycopg2

ROOT = Path(os.environ['LAB04_ROOT']).resolve()
HERE = Path(__file__).resolve().parent
PASSWORD = 'Synthetic-LAB05-only!Q27'
processes, streams, ports, results = [], [], {}, []
fixtures = json.loads((ROOT / 'runtime/fixtures.json').read_text())
db = psycopg2.connect(host=str(ROOT / 'runtime/socket'), port=56434,
                      dbname='lab04_human', user='lab04_bootstrap')
db.autocommit = True


def sql(query, params=()):
    with db.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall() if cursor.description else None


def call(case, profile, method, path, expected, payload=None, token=None):
    client = http.client.HTTPConnection('127.0.0.1', ports[profile], timeout=20)
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    try:
        client.request(method, path, json.dumps(payload) if payload is not None else None, headers)
        response = client.getresponse()
        body = response.read()
        # Never include response bodies, tokens or submitted credentials in failures.
        assert response.status == expected, (case, response.status, expected)
        content_type = response.getheader('Content-Type', '')
    finally:
        client.close()
    observed = json.loads((ROOT / ('http-' + profile + '-state.json')).read_text())
    assert observed['principal'] == observed['session_user'] == 'lab04_' + profile
    results.append({'case': case, 'profile': profile, 'method': method, 'path': path,
                    'status': expected, **observed})
    return json.loads(body) if body and content_type.startswith('application/json') else None


def login(actor):
    return call('IAM login ' + actor, 'iam', 'POST', '/api/auth/login/', 200,
                {'email': actor + '@example.invalid', 'password': 'Synthetic-LAB04-only!Q27'})


def invitation(label, tenant, actor):
    email = label + '@example.invalid'
    call('create invitation ' + label, 'control_plane', 'POST', '/api/organizations/invitations/',
         201, {'organization': tenant, 'email': email, 'role': 'user'}, actor)
    data = call('authorized invitation lookup ' + label, 'control_plane', 'GET',
                '/api/organizations/invitations/?search=' + email, 200, token=actor)
    entries = data.get('results') if isinstance(data, dict) else data
    assert len(entries) == 1 and entries[0]['email'] == email
    return entries[0]


def preview(label, inv, expected):
    return call(label, 'control_plane', 'POST', '/api/organizations/invitations/accept/',
                expected, {'token': inv['token']})


def register(label, inv, expected, extra=None):
    return call(label, 'iam', 'POST', '/api/auth/register/', expected, {
        'email': inv['email'], 'first_name': 'Synthetic', 'last_name': 'Invitee',
        'password': PASSWORD, 'password_confirm': PASSWORD,
        'invitation_token': inv['token'], **(extra or {})})


def absent(inv):
    assert sql('SELECT count(*) FROM users WHERE email=%s', [inv['email']])[0][0] == 0
    assert sql('SELECT status FROM organization_invitations WHERE id=%s', [inv['id']])[0][0] != 'accepted'


def fault(table, condition):
    # Identifiers/condition are fixed test code, never HTTP input. AFTER INSERT
    # proves rollback of actual PostgreSQL writes, not a mocked ORM exception.
    sql("CREATE FUNCTION lab05_fail() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
        "RAISE EXCEPTION 'LAB05 controlled transaction failure'; END $$")
    sql('CREATE TRIGGER lab05_fail AFTER INSERT ON ' + table +
        ' FOR EACH ROW WHEN (' + condition + ') EXECUTE FUNCTION lab05_fail()')


def clear_fault(table):
    sql('DROP TRIGGER lab05_fail ON ' + table)
    sql('DROP FUNCTION lab05_fail()')


try:
    assert sql("SELECT current_user,session_user,current_setting('data_directory'),"
               "current_setting('listen_addresses'),inet_server_addr()") == [
        ('lab04_bootstrap', 'lab04_bootstrap', str(ROOT / 'runtime/data'), '', None)]
    sql('SET ROLE lab04_maintenance')
    assert sql('SELECT current_user') == [('lab04_maintenance',)]
    for profile in ('iam', 'control_plane'):
        stream = (ROOT / ('http-' + profile + '.log')).open('w')
        streams.append(stream)
        proc = subprocess.Popen([sys.executable, str(HERE / 'http_server.py')],
            env={**os.environ, 'LAB05_HTTP': '1', 'LAB04_PROFILE': profile,
                 'LAB04_ROLE': 'lab04_' + profile}, stdout=stream, stderr=stream)
        processes.append(proc)
        ready = ROOT / ('http-' + profile + '-ready.json')
        deadline = time.monotonic() + 30
        while not ready.exists():
            assert proc.poll() is None, 'HTTP worker exited'
            assert time.monotonic() < deadline, 'HTTP readiness timeout'
            time.sleep(0.1)
        value = json.loads(ready.read_text())
        assert value['principal'] == 'lab04_' + profile and value['pid'] == proc.pid
        ports[profile] = value['port']
    assert ports['iam'] != ports['control_plane'] and processes[0].pid != processes[1].pid
    root = login('root')
    admin = login('tenant_admin')
    viewer = login('viewer')
    rt, at = root['access'], admin['access']
    base = '/api/organizations/'
    created = call('authorized organization creation', 'control_plane', 'POST', base, 201,
                   {'name': 'LAB05 isolated organization', 'email': 'lab05-org@example.invalid'}, rt)
    tenant = created['id']
    org = base + tenant + '/'
    assert sql('SELECT status,trial_ends_at,subscription_id FROM organizations WHERE id=%s',
               [tenant]) == [('inactive', None, None)]
    # Existing identity activation endpoint; no commercial contract/trial enabled.
    call('activate tenant identity', 'control_plane', 'POST', org + 'activate/', 200, {}, rt)
    good = invitation('lab05-good', tenant, rt)
    assert preview('public preview', good, 200)['role'] == 'user'
    register('reject registration role escalation', good, 400, {'role': 'superadmin'})
    register('reject registration scope injection', good, 400, {'scopes': ['platform:*']})
    register('reject mismatched invitation email', good, 400, {'email': 'other@example.invalid'})
    absent(good)
    registered = register('IAM consume invitation', good, 201)
    uid = registered['user']['id']
    assert sql('SELECT organization_id::text,role,is_active,is_primary FROM user_organizations WHERE user_id=%s',
               [uid]) == [(tenant, 'user', True, True)]
    assert sql('SELECT status,accepted_at IS NOT NULL FROM organization_invitations WHERE id=%s',
               [good['id']]) == [('accepted', True)]
    preview('replay preview denied', good, 400)
    register('replay registration denied', good, 400)
    # Different email also fails, without the existing-user validation shortcut.
    register('replay with new identity denied', good, 400, {'email': 'replay@example.invalid'})
    new_pair = call('invitee legitimate IAM login', 'iam', 'POST', '/api/auth/login/', 200,
                    {'email': good['email'], 'password': PASSWORD})
    call('invitee own tenant access', 'control_plane', 'GET', org, 200, token=new_pair['access'])
    call('invitee foreign tenant denied', 'control_plane', 'GET', base + fixtures['foreign'] + '/',
         404, token=new_pair['access'])
    call('tenant admin foreign read denied', 'control_plane', 'GET', org, 404, token=at)
    call('tenant admin foreign invitation read denied', 'control_plane', 'GET',
         base + 'invitations/' + good['id'] + '/', 404, token=at)
    for label, changes, actor, status in [
        ('foreign tenant invite', {'organization': tenant}, at, 400),
        ('global role escalation', {'role': 'superadmin'}, at, 400),
        ('admin role escalation', {'role': 'admin'}, at, 400),
        ('scope injection', {'scopes': ['platform:*']}, at, 400),
        ('viewer invitation denied', {}, viewer['access'], 403),
    ]:
        call(label, 'control_plane', 'POST', base + 'invitations/', status,
             {'organization': fixtures['tenant'], 'email': 'denied@example.invalid',
              'role': 'user', **changes}, actor)
    assert sql("SELECT count(*) FROM organization_invitations WHERE email='denied@example.invalid'")[0][0] == 0
    membership = sql('SELECT id FROM user_organizations WHERE user_id=%s', [fixtures['tenant_admin']])[0][0]
    member_path = '/api/auth/memberships/' + str(membership) + '/'
    target_member = sql('SELECT id FROM user_organizations WHERE user_id=%s', [fixtures['target']])[0][0]
    target_path = '/api/auth/memberships/' + str(target_member) + '/'
    call('membership role escalation denied', 'control_plane', 'PATCH', target_path, 400,
         {'role': 'superadmin'}, at)
    call('membership scope injection denied', 'control_plane', 'PATCH', target_path, 400,
         {'scopes': ['platform:*']}, at)
    call('membership tenant reassignment denied', 'control_plane', 'PATCH', target_path, 400,
         {'organization': tenant}, at)
    cancelled = invitation('lab05-cancelled', tenant, rt)
    call('cancel invitation', 'control_plane', 'POST', base + 'invitations/' + cancelled['id'] + '/cancel/',
         200, {}, rt)
    preview('cancelled preview denied', cancelled, 400)
    register('cancelled consumption denied', cancelled, 400)
    absent(cancelled)
    expired = invitation('lab05-expired', tenant, rt)
    call('expire via existing invitation update', 'control_plane', 'PATCH',
         base + 'invitations/' + expired['id'] + '/', 200,
         {'expires_at': '2000-01-01T00:00:00Z'}, rt)
    preview('expired preview denied', expired, 400)
    register('expired consumption denied', expired, 400)
    absent(expired)
    withdrawn = invitation('lab05-withdrawn', fixtures['tenant'], at)
    preview('authority valid before withdrawal', withdrawn, 200)
    call('withdraw inviter membership', 'control_plane', 'PATCH', member_path, 200,
         {'is_active': False}, rt)
    preview('withdrawn inviter preview denied', withdrawn, 400)
    register('withdrawn inviter consumption denied', withdrawn, 400)
    absent(withdrawn)
    # Live membership authorization denies access even with the existing session JWT.
    call('withdrawn inviter JWT denied', 'control_plane', 'GET', base + fixtures['tenant'] + '/',
         403, token=at)
    rollback = invitation('lab05-rollback', tenant, rt)
    fault('user_organizations', "NEW.organization_id = '" + tenant + "'::uuid")
    try:
        register('membership SQL failure rolls back registration', rollback, 500)
    finally:
        clear_fault('user_organizations')
    absent(rollback)
    register('registration succeeds after fault removed', rollback, 201)
    snapshot = sql('SELECT name FROM organizations WHERE id=%s', [tenant])
    outbox = sql('SELECT count(*) FROM tenant_integration_outbox WHERE organization_id=%s', [tenant])
    audit = sql('SELECT count(*) FROM user_activity_logs WHERE organization_id=%s', [tenant])
    fault('user_activity_logs', "NEW.module = 'control_plane' AND NEW.description = 'partial_update'")
    try:
        call('audit SQL failure rolls back tenant and outbox', 'control_plane', 'PATCH', org, 500,
             {'name': 'LAB05 must roll back'}, rt)
    finally:
        clear_fault('user_activity_logs')
    assert sql('SELECT name FROM organizations WHERE id=%s', [tenant]) == snapshot
    assert sql('SELECT count(*) FROM tenant_integration_outbox WHERE organization_id=%s', [tenant]) == outbox
    assert sql('SELECT count(*) FROM user_activity_logs WHERE organization_id=%s', [tenant]) == audit
    call('tenant update after fault removed', 'control_plane', 'PATCH', org, 200,
         {'name': 'LAB05 committed identity'}, rt)
    assert sql('SELECT source_version,status,attempts FROM tenant_integration_outbox WHERE organization_id=%s ORDER BY source_version',
               [tenant]) == [(1, 'pending', 0), (2, 'pending', 0), (3, 'pending', 0)]
    assert sql("SELECT count(*) FROM user_activity_logs WHERE organization_id=%s AND module='control_plane' AND entity_type='organizations.organizationinvitation'", [tenant])[0][0] >= 4
    call('IAM logout', 'iam', 'POST', '/api/auth/logout/', 200,
         {'refresh': new_pair['refresh']}, new_pair['access'])
    call('same revoked JWT denied in CP', 'control_plane', 'GET', org, 401, token=new_pair['access'])
    # Durable checks survive cluster restart and a fresh connection in each worker.
    db.close()
    subprocess.run(['pg_ctl', '-D', str(ROOT / 'runtime/data'), '-l', str(ROOT / 'runtime/server.log'),
                    '-m', 'fast', '-w', 'restart'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    db = psycopg2.connect(host=str(ROOT / 'runtime/socket'), port=56434, dbname='lab04_human',
                          user='lab04_bootstrap', options='-c role=lab04_maintenance')
    db.autocommit = True
    call('revocation persists after restart', 'control_plane', 'GET', org, 401, token=new_pair['access'])
    call('revoked refresh denied', 'iam', 'POST', '/api/auth/refresh/', 401, {'refresh': new_pair['refresh']})
    assert sql('SELECT status FROM organization_invitations WHERE id=%s', [good['id']]) == [('accepted',)]
    assert sql('SELECT count(*) FROM user_organizations WHERE user_id=%s AND organization_id=%s AND is_active', [uid, tenant]) == [(1,)]
    assert sql('SELECT count(*) FROM tenant_integration_outbox WHERE organization_id=%s', [tenant]) == [(3,)]
    assert sql("SELECT count(*) FROM user_activity_logs WHERE organization_id=%s AND module='control_plane'", [tenant])[0][0] > 0
    assert sql("SELECT count(*) FROM django_migrations WHERE app='financial'") == [(0,)]
    assert sql('SELECT count(*) FROM organizations WHERE trial_ends_at IS NOT NULL OR subscription_id IS NOT NULL') == [(0,)]
    assert sql('SELECT count(*) FROM pg_roles WHERE rolname IN (%s,%s) AND (rolsuper OR rolbypassrls)',
               ['lab04_iam', 'lab04_control_plane']) == [(0,)]
    assert sql("SELECT count(*) FROM pg_trigger WHERE tgname='lab05_fail'") == [(0,)]
    (ROOT / 'http-invitations-result.json').write_text(json.dumps({
        'status': 'LAB05_B_HTTP_INVITATIONS_PASS', 'cases': results,
        'transport': 'real loopback HTTP, independent IAM and CP processes',
        'membership_persisted': True, 'audit_persisted': True, 'outbox_versions': [1, 2, 3],
        'registration_rollback': True, 'tenant_audit_outbox_rollback': True,
        'postgresql_restarted': True, 'financial_migrations': 0,
        'trials_or_subscriptions': 0, 'fault_triggers_remaining': 0,
    }, indent=2))
    print('LAB05_B_HTTP_INVITATIONS_PASS; %s real HTTP cases' % len(results))
finally:
    db.close()
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
