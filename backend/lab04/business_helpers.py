import json
import lab_env
from django.db import connection
from django.test import Client

fixtures = json.loads((lab_env.ROOT / 'runtime/fixtures.json').read_text())
pairs = json.loads((lab_env.ROOT / 'runtime/pairs.json').read_text())
results = []


def call(label, method, path, expected, data=None, actor='root', **extra):
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_user, session_user')
        identity = cursor.fetchone()
    assert identity == ('lab04_control_plane',) * 2
    headers = {'HTTP_AUTHORIZATION': 'Bearer ' + pairs[actor]['access']} if actor else {}
    response = getattr(Client(), method)(path, data or {}, content_type='application/json', **headers, **extra)
    assert response.status_code == expected, (label, response.status_code, response.content[:250])
    results.append({'case': label, 'http': expected, 'principal': identity[0],
                    'kind': 'ALLOW' if expected < 400 else 'DENY_AUTHORIZATION'})
    return response.json() if response.content else None
