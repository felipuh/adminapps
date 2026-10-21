import json
import lab_env
from django.db import connection, DatabaseError, transaction
from apps.integration.models import SSOSession, SSORevocationOutbox, SSOSecurityFence
from apps.organizations.models import Organization, TenantIntegrationOutbox
from business_helpers import call, results

fixture = json.loads((lab_env.ROOT / 'runtime/central.json').read_text())
tenant_id = fixture['tenant_id']
session = SSOSession.objects.get(pk=fixture['session_id'])
assert session.state == 'active'
url = f'/api/organizations/{tenant_id}/'
epoch = SSOSecurityFence.objects.get(pk=1).authority_epoch
def fail_event(execute, sql, params, many, context):
    value = execute(sql, params, many, context)
    if sql.startswith('INSERT INTO "tenant_integration_outbox"'):
        raise DatabaseError('Synthetic failure after real tenant event INSERT')
    return value
try:
    with connection.execute_wrapper(fail_event):
        call('suspension rollback', 'post', url + 'suspend/', 200)
except DatabaseError:
    pass
else:
    raise AssertionError('Expected outbox failure')
session.refresh_from_db()
assert session.state == 'active'
assert Organization.objects.get(pk=tenant_id).status == 'active'
assert SSOSecurityFence.objects.get(pk=1).authority_epoch == epoch
assert not TenantIntegrationOutbox.objects.filter(organization_id=tenant_id).exists()
assert not SSORevocationOutbox.objects.filter(session=session).exists()
results.append({'case': 'tenant, Decision B, fence and both outboxes rollback', 'status': 'PASS'})
call('tenant suspension revokes B', 'post', url + 'suspend/', 200)
session.refresh_from_db(); assert session.state == 'revoked'
assert SSORevocationOutbox.objects.filter(session=session).count() == 1
assert TenantIntegrationOutbox.objects.filter(organization_id=tenant_id).count() == 1
call('human session remains separate', 'get', '/api/auth/users/me/', 200, actor='viewer')
call('reactivate tenant', 'post', url + 'activate/', 200)
session.refresh_from_db(); assert session.state == 'revoked'
try:
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("UPDATE sso_sessions SET state='active', revoked_at=NULL, generation=generation+1 WHERE id=%s", [str(session.pk)])
except DatabaseError as error:
    assert (getattr(error.__cause__, 'sqlstate', None) or getattr(error.__cause__, 'pgcode', None)) == 'P0001'
else:
    raise AssertionError('Central authority resurrection accepted')
results.append({'case': 'CP cannot resurrect central authority', 'sqlstate': 'P0001', 'status': 'PASS'})
(lab_env.ROOT / 'central-business.json').write_text(json.dumps(results, indent=2))
