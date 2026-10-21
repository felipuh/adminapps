import json
import lab_env
from django.db import connection, DatabaseError
from apps.organizations.models import Organization, OrganizationInvitation, TenantIntegrationOutbox
from apps.users.models import User, UserOrganization, UserActivityLog
from business_helpers import fixtures as f, pairs, results, call

base = '/api/organizations/'
org = base + f['tenant'] + '/'
foreign = base + f['foreign'] + '/'
created = call('create tenant identity', 'post', base, 201,
               {'name': 'New isolated tenant', 'email': 'created@example.invalid'})
obj = Organization.objects.get(pk=created['id'])
assert obj.status == 'inactive' and obj.trial_ends_at is None
assert TenantIntegrationOutbox.objects.filter(organization=obj).count() == 1
call('read organization', 'get', org, 200, actor='tenant_admin')
call('authorized rename', 'patch', org, 200, {'name': 'Renamed'})
call('settings preferences', 'patch', org + 'organization_settings/', 200, {'theme': 'light'}, actor='tenant_admin')
call('settings cross tenant', 'patch', foreign + 'organization_settings/', 404, {'theme': 'light'}, actor='tenant_admin')
call('settings platform field', 'patch', org + 'organization_settings/', 400, {'module_documents': True}, actor='tenant_admin')
call('tenant quota held', 'patch', org, 403, {'max_users': 500})
call('tenant trial held', 'patch', org, 400, {'status': 'trial'})
call('no physical deletion', 'delete', org, 405)
call('suspend', 'post', org + 'suspend/', 200)
call('suspended membership', 'get', org, 403, actor='tenant_admin')
call('reactivate existing contract', 'post', org + 'activate/', 200)

invite = {'organization': f['tenant'], 'email': 'registered@example.invalid', 'role': 'user'}
call('invite create', 'post', base + 'invitations/', 201, invite, actor='tenant_admin')
inv = OrganizationInvitation.objects.get(email=invite['email'])
call('invitation preview', 'post', base + 'invitations/accept/', 200, {'token': str(inv.token)}, actor=None)
call('invite foreign', 'post', base + 'invitations/', 400, {**invite, 'organization': f['foreign']}, actor='tenant_admin')
call('invite role escalation', 'post', base + 'invitations/', 400, {**invite, 'role': 'superadmin'}, actor='tenant_admin')
call('invitation reparent', 'patch', base + f'invitations/{inv.pk}/', 400, {'organization': f['foreign']})
call('viewer cannot invite', 'post', base + 'invitations/', 403, invite, actor='viewer')
call('staff cannot invite', 'post', base + 'invitations/', 403, invite, actor='staff')
call('technical credential rejected', 'post', base + 'invitations/', 403, invite, HTTP_X_API_KEY='synthetic')
call('cancel create', 'post', base + 'invitations/', 201, {**invite, 'email': 'cancel@example.invalid'}, actor='tenant_admin')
cancel = OrganizationInvitation.objects.get(email='cancel@example.invalid')
call('cancel', 'post', base + f'invitations/{cancel.pk}/cancel/', 200, actor='tenant_admin')
call('cancelled preview denied', 'post', base + 'invitations/accept/', 400, {'token': str(cancel.token)}, actor=None)
membership = UserOrganization.objects.get(user_id=f['target'])
call('membership deactivation', 'patch', f'/api/auth/memberships/{membership.pk}/', 200, {'is_active': False}, actor='tenant_admin')
call('membership reparent denied', 'patch', f'/api/auth/memberships/{membership.pk}/', 400, {'organization': f['foreign']})
call('member physical deletion denied', 'delete', f'/api/auth/memberships/{membership.pk}/', 405)
call('user physical deletion denied', 'delete', f"/api/auth/users/{f['target']}/", 405)
call('create membership', 'post', '/api/auth/memberships/', 201,
     {'user': f['target'], 'organization': f['foreign'], 'role': 'user'})

# Real writes followed by an injected SQL transport failure; inspect committed DB.
before = TenantIntegrationOutbox.objects.filter(organization_id=f['tenant']).count()
def fail_audit(execute, sql, params, many, context):
    value = execute(sql, params, many, context)
    if sql.startswith('INSERT INTO "user_activity_logs"'):
        raise DatabaseError('Synthetic audit failure after actual INSERT')
    return value
try:
    with connection.execute_wrapper(fail_audit):
        call('rollback injected', 'patch', org, 200, {'name': 'Must roll back'})
except DatabaseError:
    pass
else:
    raise AssertionError('Expected audit failure')
assert Organization.objects.get(pk=f['tenant']).name == 'Renamed'
assert TenantIntegrationOutbox.objects.filter(organization_id=f['tenant']).count() == before
assert UserActivityLog.objects.filter(module='control_plane', entity_type='organizations.organizationinvitation').exists()
results.append({'case': 'audit and tenant event rollback', 'kind': 'ALLOW', 'status': 'PASS'})

# Revoke inviter authority through a real membership mutation, then restore it.
inviter_membership = UserOrganization.objects.get(user_id=f['tenant_admin'])
call('withdraw inviter membership', 'patch', f'/api/auth/memberships/{inviter_membership.pk}/', 200, {'is_active': False})
call('revoked invitation authority', 'post', base + 'invitations/accept/', 400, {'token': str(inv.token)}, actor=None)
call('restore inviter membership', 'patch', f'/api/auth/memberships/{inviter_membership.pk}/', 200, {'is_active': True})
(lab_env.ROOT / 'runtime/invitation.json').write_text(json.dumps({'token': str(inv.token), 'id': str(inv.pk)}))
(lab_env.ROOT / 'organizations.json').write_text(json.dumps(results, indent=2))
