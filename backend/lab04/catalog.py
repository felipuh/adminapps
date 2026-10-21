import json
import lab_env
from django.db import connection, DatabaseError
from apps.products.models import ProductSystem, OrganizationProductEntitlement, ProductEntitlementAuditLog, OrganizationModule
from apps.subscriptions.models import Plan
from apps.users.models import UserActivityLog
from business_helpers import fixtures as f, results, call

products = '/api/products/'
plan = call('inactive catalog plan', 'post', '/api/subscriptions/plans/', 201, {'code': 'LAB04', 'name': 'Lab catalog'})
assert not Plan.objects.get(pk=plan['id']).is_trial_available
assert not Plan.objects.get(pk=plan['id']).is_active
call('plan update', 'patch', '/api/subscriptions/plans/' + plan['id'] + '/', 200, {'name': 'Catalog renamed'})
call('plan commercial pricing held', 'patch', '/api/subscriptions/plans/' + plan['id'] + '/', 403, {'price': '2.00'})
call('plan quota held', 'patch', '/api/subscriptions/plans/' + plan['id'] + '/', 403, {'max_users': 99})
call('plan trial held', 'patch', '/api/subscriptions/plans/' + plan['id'] + '/', 403, {'is_trial_available': True})
call('plan activation held', 'patch', '/api/subscriptions/plans/' + plan['id'] + '/', 403, {'is_active': True})
call('plan platform role insufficient', 'post', '/api/subscriptions/plans/', 403, {'code': 'DENIED', 'name': 'Denied'}, actor='platform')
call('tenant cannot see inactive plan', 'get', '/api/subscriptions/plans/' + plan['id'] + '/', 404, actor='tenant_admin')
new_product = call('product create', 'post', products + 'systems/', 201,
                   {'code': 'LAB04PRODUCT', 'slug': 'lab04-iso', 'name': 'Lab ISO', 'status': 'active'})
assert not ProductSystem.objects.get(pk=new_product['id']).billing_enabled
product = {'id': str(ProductSystem.objects.get(code='ISO_SMART').pk)}
other = call('separate product', 'post', products + 'systems/', 201,
             {'code': 'LAB04OTHER', 'slug': 'lab04-med', 'name': 'Lab Med', 'status': 'active'})
assert not ProductSystem.objects.get(pk=product['id']).billing_enabled
call('product metadata update', 'patch', products + f"systems/{product['id']}/", 200, {'description': 'Lab catalog'})
call('product identity immutable', 'patch', products + f"systems/{product['id']}/", 403, {'code': 'STOLEN'})
call('product billing held', 'patch', products + f"systems/{product['id']}/", 403, {'billing_enabled': True})
call('unknown field rejected', 'patch', products + f"systems/{product['id']}/", 400, {'is_superuser': True})
call('viewer product catalog denied', 'get', products + 'systems/', 403, actor='viewer')
call('platform catalog read', 'get', products + 'systems/', 200, actor='platform')

payload = {'organization': f['tenant'], 'product': product['id'], 'status': 'active',
           'scopes': ['ISO_SMART:core.document:read']}
call('trial default held', 'post', products + 'entitlements/', 403, {k: v for k, v in payload.items() if k != 'status'})
call('entitlement create', 'post', products + 'entitlements/', 201, payload, actor='platform')
ent = OrganizationProductEntitlement.objects.get(organization_id=f['tenant'], product_id=product['id'])
url = products + f'entitlements/{ent.pk}/'
call('foreign product scope', 'patch', url, 400, {'scopes': ['MEDSUPPLIER:catalog.product:read']}, actor='platform')
call('tenant reparent rejected', 'patch', url, 400, {'organization': f['foreign']}, actor='platform')
call('product reparent rejected', 'patch', url, 400, {'product': other['id']}, actor='platform')
call('trial toggle held', 'post', url + 'toggle/', 403, {'action': 'trial'}, actor='platform')
call('entitlement disable', 'post', url + 'toggle/', 200, {'action': 'disable'}, actor='platform')
ent.refresh_from_db(); assert not ent.enabled
call('entitlement enable explicit', 'post', url + 'toggle/', 200, {'action': 'enable'}, actor='platform')
call('tenant cannot control entitlements', 'get', url, 403, actor='tenant_admin')
call('entitlement audit', 'get', url + 'audit_logs/', 200, actor='platform')
ent.refresh_from_db(); assert ent.scopes == ['ISO_SMART:core.document:read']
assert not OrganizationProductEntitlement.objects.filter(organization_id=f['tenant'], product_id=other['id']).exists()

def fail_audit(execute, sql, params, many, context):
    value = execute(sql, params, many, context)
    if sql.startswith('INSERT INTO "product_entitlement_audit_logs"'):
        raise DatabaseError('Synthetic failure after real audit write')
    return value
before = ProductEntitlementAuditLog.objects.filter(entitlement=ent).count()
try:
    with connection.execute_wrapper(fail_audit):
        call('audit failure rollback', 'post', url + 'toggle/', 200, {'action': 'disable'})
except DatabaseError:
    pass
else:
    raise AssertionError('Expected audit failure')
ent.refresh_from_db(); assert ent.enabled
assert ProductEntitlementAuditLog.objects.filter(entitlement=ent).count() == before
results.append({'case': 'entitlement and audit rollback', 'status': 'PASS', 'kind': 'ALLOW'})

standard = call('standard create', 'post', products + 'iso-standards/', 201,
                {'code': 'LAB04', 'name': 'Lab standard', 'full_name': 'Synthetic standard', 'version': '1'})
call('module assignment', 'post', products + 'modules/', 201,
     {'organization': f['tenant'], 'iso_standard': standard['id'], 'status': 'active'}, actor='platform')
module = OrganizationModule.objects.get(organization_id=f['tenant'], iso_standard_id=standard['id'])
call('module disable', 'post', products + f'modules/{module.pk}/toggle/', 200, {'action': 'disable'}, actor='platform')
call('module trial held', 'post', products + f'modules/{module.pk}/toggle/', 403, {'action': 'trial'}, actor='platform')
call('module foreign relation rejected', 'patch', products + f'modules/{module.pk}/', 400, {'organization': f['foreign']}, actor='platform')
call('product deactivation', 'patch', products + f"systems/{product['id']}/", 200, {'status': 'retired'})
call('invoice authorized read', 'get', '/api/subscriptions/invoices/', 200, actor='tenant_admin')
call('invoice write held', 'post', '/api/subscriptions/invoices/', 403, {})
call('subscription write held', 'post', '/api/subscriptions/', 403, {})
call('payment write held', 'post', '/api/subscriptions/payment-methods/', 403, {})
assert UserActivityLog.objects.filter(module='control_plane', entity_type='products.productsystem').exists()
(lab_env.ROOT / 'catalog.json').write_text(json.dumps(results, indent=2))
