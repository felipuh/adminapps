"""Synthetic business fixtures, only under the maintenance identity."""
import json
import lab_env
from django.db import connection
from django.contrib.auth.models import Permission
from apps.users.models import User, UserOrganization
from apps.organizations.models import Organization, OrganizationSettings

with connection.cursor() as cursor:
    cursor.execute('SELECT current_user')
    assert cursor.fetchone()[0] == 'lab04_maintenance'
fixtures = {}
for key in ('tenant', 'foreign'):
    org = Organization.objects.create(code='LAB04-' + key, name=key, email=key + '@example.invalid', status='active')
    OrganizationSettings.objects.create(organization=org)
    fixtures[key] = str(org.pk)
roles = {'root': ('superadmin', True, True), 'platform': ('admin', True, False),
         'tenant_admin': ('org_admin', True, False), 'viewer': ('user', False, False),
         'staff': ('user', True, False), 'target': ('user', False, False),
         'outsider': ('user', False, False), 'disabled': ('admin', True, False)}
for key, (role, staff, superuser) in roles.items():
    org_id = fixtures['foreign' if key == 'outsider' else 'tenant']
    user = User.objects.create_user(email=key + '@example.invalid', password='Synthetic-LAB04-only!Q27',
                                   first_name='Lab', last_name=key, role=role, is_staff=staff,
                                   is_superuser=superuser, organization_id=org_id,
                                   is_active=key != 'disabled')
    UserOrganization.objects.create(user=user, organization_id=org_id, role=role, is_active=True)
    if key in ('platform', 'tenant_admin'):
        user.user_permissions.set(Permission.objects.filter(content_type__app_label__in=['users', 'organizations', 'products', 'subscriptions']))
    fixtures[key] = str(user.pk)
(lab_env.ROOT / 'runtime/fixtures.json').write_text(json.dumps(fixtures))
