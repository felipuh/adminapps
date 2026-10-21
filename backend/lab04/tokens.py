import json
import lab_env
from django.test import Client

pairs = {}
for key in ('root', 'platform', 'tenant_admin', 'viewer', 'staff', 'target', 'outsider'):
    response = Client().post('/api/auth/login/', {
        'email': key + '@example.invalid', 'password': 'Synthetic-LAB04-only!Q27',
    }, content_type='application/json')
    assert response.status_code == 200
    pairs[key] = response.json()
(lab_env.ROOT / 'runtime/pairs.json').write_text(json.dumps(pairs))
