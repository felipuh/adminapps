"""An IAM-issued bearer remains revoked in CP after SQL attacks and restart."""
import hashlib
import json
import sys
import lab_env
from django.db import connection, transaction, DatabaseError
from django.test import Client, override_settings
from django.core.exceptions import ImproperlyConfigured
from config.runtime_profiles import verify_connection
from apps.users import human_sessions as life
from apps.users.models import User, UserSession
from apps.organizations.views import OrganizationInvitationViewSet
from business_helpers import fixtures, pairs

token = pairs['viewer']['access']
refresh = pairs['viewer']['refresh']
phase = sys.argv[1]
headers = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
client = Client()
user = User.objects.get(pk=fixtures['viewer'])
calls = []
original = OrganizationInvitationViewSet.create
def observed(self, *args, **kwargs):
    calls.append(True)
    return original(self, *args, **kwargs)
OrganizationInvitationViewSet.create = observed
assert verify_connection() == 'lab04_control_plane'
if phase == 'before':
    assert client.get('/api/auth/users/me/', **headers).status_code == 200
    assert client.post('/api/auth/users/revoke_session/', {'session_id': life.HumanRefreshToken(refresh)['sid']},
                       content_type='application/json', **headers).status_code == 200
    for statement in ('DELETE FROM user_sessions WHERE user_id=%s', 'UPDATE user_sessions SET is_active=true WHERE user_id=%s'):
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(statement, [str(user.pk)])
        except DatabaseError as error:
            assert (getattr(error.__cause__, 'sqlstate', None) or getattr(error.__cause__, 'pgcode', None)) in ('42501', 'P0001')
        else:
            raise AssertionError('Authority restoration accepted')
    with override_settings(ADMINAPPS_RUNTIME_PROFILE='iam'):
        try:
            verify_connection()
        except ImproperlyConfigured:
            pass
        else:
            raise AssertionError('Control plane credential accepted in IAM process')
connection.close()
assert client.get('/api/auth/users/me/', **headers).status_code == 401
assert client.post('/api/organizations/invitations/', {
    'organization': fixtures['tenant'], 'email': 'never-created@example.invalid', 'role': 'user',
}, content_type='application/json', **headers).status_code == 401
assert not calls
assert client.post('/api/auth/users/revoke_session/', {}, content_type='application/json', **headers).status_code == 401
try:
    life.refresh_pair(refresh)
except Exception as error:
    from rest_framework.exceptions import AuthenticationFailed
    assert isinstance(error, AuthenticationFailed)
else:
    raise AssertionError('Revoked refresh accepted')
(lab_env.ROOT / ('cross-process-' + phase + '.json')).write_text(json.dumps({
    'principal': verify_connection(), 'access': 401, 'invitation': 401,
    'handler_calls': len(calls), 'refresh': 'DENIED',
    'token_sha256': hashlib.sha256(token.encode()).hexdigest(),
}, indent=2))
