"""Executed in a fresh OS process with exactly one supplied SQL credential."""
import json
import lab_env
from django.conf import settings
from django.test import Client
from config.runtime_profiles import verify_connection

profile = settings.ADMINAPPS_RUNTIME_PROFILE
assert verify_connection() == 'lab04_' + profile
client = Client()
expected = {
    'iam': [('/admin/', 404), ('/api/products/systems/', 404), ('/api/auth/users/', 404)],
    'control_plane': [('/admin/', 404), ('/api/auth/login/', 404), ('/api/products/systems/', 403)],
    'admin': [('/api/auth/login/', 404), ('/api/products/systems/', 404), ('/admin/', 302)],
    'events': [('/admin/', 404), ('/api/auth/login/', 404)],
}[profile]
for path, status in expected:
    assert client.get(path).status_code == status, (profile, path)
(lab_env.ROOT / ('process-' + profile + '.json')).write_text(json.dumps({
    'profile': profile, 'current_user': verify_connection(), 'routes': expected,
    'connection_aliases': list(settings.DATABASES),
}, indent=2))
