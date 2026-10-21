import json
import lab_env
from django.test import Client
from apps.organizations.models import OrganizationInvitation

inv = json.loads((lab_env.ROOT / 'runtime/invitation.json').read_text())
payload = {'email': 'registered@example.invalid', 'first_name': 'Registered', 'last_name': 'Lab',
           'password': 'Synthetic-LAB04-only!Q27', 'password_confirm': 'Synthetic-LAB04-only!Q27',
           'invitation_token': inv['token']}
response = Client().post('/api/auth/register/', payload, content_type='application/json')
assert response.status_code == 201, response.status_code
assert OrganizationInvitation.objects.get(pk=inv['id']).status == 'accepted'
assert Client().post('/api/auth/register/', payload, content_type='application/json').status_code == 400
(lab_env.ROOT / 'invitation-consumption.json').write_text(json.dumps({
    'principal': 'lab04_iam', 'register': 201, 'replay': 400, 'persisted_status': 'accepted',
}))
