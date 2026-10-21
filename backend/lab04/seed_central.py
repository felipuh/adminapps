"""Maintenance-only synthetic central authority for CP transaction acceptance."""
import json
import lab_env
from test_lab import central, raw
from apps.users.models import User

assert raw('SELECT current_user')[0][0] == 'lab04_maintenance'
fixtures = json.loads((lab_env.ROOT / 'runtime/fixtures.json').read_text())
session = central(User.objects.get(pk=fixtures['viewer']))
(lab_env.ROOT / 'runtime/central.json').write_text(json.dumps({
    'session_id': str(session.pk), 'tenant_id': str(session.tenant_id),
}))
