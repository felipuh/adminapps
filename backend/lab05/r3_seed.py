"""Extend only the new R1 database with R3 cross-tenant fixtures."""
import json
import lab_env
from django.db import connection
from apps.users.models import UserOrganization
from apps.products.models import OrganizationProductEntitlement
from apps.integration.models import SSOClient

with connection.cursor() as cursor:
    cursor.execute('SELECT current_user')
    assert cursor.fetchone()[0] == 'lab04_maintenance'
root = lab_env.ROOT / 'runtime'
trust = json.loads((root / 'central-trust.json').read_text())
trust.pop('PRIVATE_KEY')
(root / 'r3-public-trust.json').write_text(json.dumps(trust))
fixture = json.loads((root / 'fixtures.json').read_text())
client = SSOClient.objects.get(client_id='lab05-iso-smart')
client.tenants.add(fixture['foreign'])
# One real central subject: writer in A, read-only viewer in B.
UserOrganization.objects.create(user_id=fixture['viewer'],
    organization_id=fixture['foreign'], role='viewer', is_active=True)
scopes = ['ISO_SMART:resources.resource:' + action for action in ('read', 'create', 'update')]
entitlement = OrganizationProductEntitlement.objects.get(organization_id=fixture['tenant'], product=client.product)
entitlement.scopes = scopes
entitlement.save(update_fields=['scopes'])
OrganizationProductEntitlement.objects.create(organization_id=fixture['foreign'],
    product=client.product, enabled=True, status='active', scopes=scopes)
