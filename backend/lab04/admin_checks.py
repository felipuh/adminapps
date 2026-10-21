import json
import lab_env
from django.db import connection, DatabaseError
from django.test import Client
from django.contrib.admin.models import LogEntry
from apps.users.models import User, UserOrganization
from apps.users.human_sessions import HumanRefreshToken
from apps.users.runtime_admin import site, WRITABLE
from apps.organizations.models import OrganizationSettings

f = json.loads((lab_env.ROOT / 'runtime/fixtures.json').read_text())
pairs = json.loads((lab_env.ROOT / 'runtime/pairs.json').read_text())
results = []
with connection.cursor() as cursor:
    cursor.execute('SELECT current_user,session_user')
    assert cursor.fetchone() == ('lab04_admin',) * 2


def check(label, response, status):
    assert response.status_code == status, (label, response.status_code)
    results.append({'case': label, 'http': status, 'principal': 'lab04_admin',
                    'kind': 'ALLOW' if status == 200 else 'DENY_OR_REDIRECT'})


def login(actor, accepted=True):
    client = Client(enforce_csrf_checks=True)
    client.get('/admin/login/')
    csrf = client.cookies['csrftoken'].value
    response = client.post('/admin/login/?next=/admin/', {
        'username': actor + '@example.invalid', 'password': 'Synthetic-LAB04-only!Q27',
        'csrfmiddlewaretoken': csrf, 'next': '/admin/',
    })
    check(actor + ' login', response, 302 if accepted else 200)
    return client


root = login('root')
check('root index', root.get('/admin/'), 200)
for model in site._registry:
    check(model._meta.label_lower + ' changelist', root.get(f'/admin/{model._meta.app_label}/{model._meta.model_name}/'), 200)
platform = login('platform')
check('platform index', platform.get('/admin/'), 200)
tenant = login('tenant_admin')
check('tenant index', tenant.get('/admin/'), 200)
tenant_list = tenant.get('/admin/users/user/')
check('tenant users scoped', tenant_list, 200)
assert f['foreign'].encode() not in tenant_list.content
assert b'outsider@example.invalid' not in tenant_list.content
staff = login('staff')
check('staff no admission', staff.get('/admin/'), 302)
viewer = login('viewer', False)
check('viewer no admission', viewer.get('/admin/'), 302)
disabled = login('disabled', False)
check('disabled no admission', disabled.get('/admin/'), 302)
check('technical credential denied', root.get('/admin/', HTTP_X_API_KEY='synthetic'), 403)
check('bearer cannot substitute admin cookie', root.get('/admin/', HTTP_AUTHORIZATION='Bearer ' + pairs['root']['access']), 403)
target_url = f"/admin/users/user/{f['target']}/change/"
check('tenant foreign target hidden', tenant.get(f"/admin/users/user/{f['outsider']}/change/"), 302)
check('platform protected target hidden', platform.get(f"/admin/users/user/{f['root']}/change/"), 302)
check('legitimate form', platform.get(target_url), 200)
user = User.objects.get(pk=f['target'])
payload = {key: getattr(user, key) for key in WRITABLE['users.user']}
payload = {key: value for key, value in payload.items() if value is not False}
payload['first_name'] = 'Admin edited'
payload['_save'] = 'Save'
check('CSRF missing', platform.post(target_url, payload), 403)
csrf = platform.cookies['csrftoken'].value
before = LogEntry.objects.count()
check('legitimate user write', platform.post(target_url, {**payload, 'csrfmiddlewaretoken': csrf}), 302)
user.refresh_from_db(); assert user.first_name == 'Admin edited'
assert LogEntry.objects.count() == before + 1
def fail_log(execute, sql, params, many, context):
    value = execute(sql, params, many, context)
    if sql.startswith('INSERT INTO "django_admin_log"'):
        raise DatabaseError('Synthetic failure after real admin log INSERT')
    return value
before = LogEntry.objects.count()
try:
    with connection.execute_wrapper(fail_log):
        platform.post(target_url, {**payload, 'first_name': 'Rollback', 'csrfmiddlewaretoken': csrf})
except DatabaseError:
    pass
else:
    raise AssertionError('Expected admin log failure')
user.refresh_from_db(); assert user.first_name == 'Admin edited'
assert LogEntry.objects.count() == before
results.append({'case': 'admin mutation and log rollback', 'status': 'PASS', 'principal': 'lab04_admin'})
check('privilege payload rejected', platform.post(target_url, {**payload, 'is_superuser': 'on', 'csrfmiddlewaretoken': csrf}), 403)
user.refresh_from_db(); assert not user.is_superuser
check('delete retained', root.get(f"/admin/users/user/{f['target']}/delete/"), 403)
check('password bypass denied', root.get(f"/admin/users/user/{f['target']}/password/"), 403)
membership = UserOrganization.objects.get(user_id=f['outsider'])
UserOrganization.objects.filter(pk=membership.pk).update(role='superadmin')
check('higher membership authority denied', platform.get(f'/admin/users/userorganization/{membership.pk}/change/'), 403)
UserOrganization.objects.filter(pk=membership.pk).update(role='user')
settings_obj = OrganizationSettings.objects.get(organization_id=f['tenant'])
settings_url = f'/admin/organizations/organizationsettings/{settings_obj.pk}/change/'
check('tenant settings form', tenant.get(settings_url), 200)
check('tenant settings write', tenant.post(settings_url, {
    'theme': 'dark', '_save': 'Save', 'csrfmiddlewaretoken': tenant.cookies['csrftoken'].value,
}), 302)
settings_obj.refresh_from_db(); assert settings_obj.theme == 'dark'

# Disabling a human invalidates subsequent cookie access and durable JWT authority.
User.objects.filter(pk=f['platform']).update(is_active=False)
check('disabled existing cookie', platform.get('/admin/'), 302)
User.objects.filter(pk=f['platform']).update(is_active=True)
session_id = HumanRefreshToken(pairs['platform']['refresh'])['sid']
from apps.users.models import UserSession
assert not UserSession.objects.get(pk=session_id).is_active
check('revoked bearer plus valid cookie denied', root.get('/admin/', HTTP_AUTHORIZATION='Bearer ' + pairs['platform']['access']), 403)
(lab_env.ROOT / 'admin.json').write_text(json.dumps(results, indent=2))
