"""LAB05-A loopback WSGI process, actual LAB04 SQL principal and runtime routes."""
import json
import os
from pathlib import Path
from wsgiref.simple_server import make_server, WSGIRequestHandler

assert os.environ.get('LAB05_HTTP') == '1'
import lab_env
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.db import connection, connections
from config.runtime_profiles import verify_connection

profile = os.environ['LAB04_PROFILE']
assert profile in ('iam', 'control_plane', 'sso')
root = lab_env.ROOT
calls = 0
if profile == 'control_plane':
    from apps.products.views import ProductSystemViewSet
    original_list = ProductSystemViewSet.list
    def counted_list(self, *args, **kwargs):
        global calls
        calls += 1
        return original_list(self, *args, **kwargs)
    ProductSystemViewSet.list = counted_list

# Observe successful protected stages without replacing authentication or SQL.
stages = {'render': 0, 'authorization': 0}
if profile == 'sso':
    from apps.integration import sso_views, authorization
    original_render = sso_views._render_session
    original_resolve = authorization.resolve
    def counted_render(*args, **kwargs):
        stages['render'] += 1
        return original_render(*args, **kwargs)
    def counted_resolve(*args, **kwargs):
        stages['authorization'] += 1
        return original_resolve(*args, **kwargs)
    sso_views._render_session = counted_render
    authorization.resolve = counted_resolve

application = get_wsgi_application()


def observed(environ, start_response):
    # Every real request has a fresh libpq session. Persist only non-secret evidence.
    connections.close_all()
    principal = verify_connection()
    with connection.cursor() as cursor:
        cursor.execute('SELECT session_user, pg_backend_pid()')
        session_user, backend_pid = cursor.fetchone()
    response = application(environ, start_response)
    if os.environ.get('LAB05_R3') == '1':
        with (root / 'r3-central-requests.jsonl').open('a') as stream:
            stream.write(json.dumps({'path': environ['PATH_INFO'],
                'method': environ['REQUEST_METHOD'], 'principal': principal,
                'backend_pid': backend_pid}) + '\n')
    (root / ('http-' + profile + '-state.json')).write_text(json.dumps({
        'principal': principal, 'session_user': session_user,
        'backend_pid': backend_pid, 'handler_calls': calls, 'protected_stages': stages,
    }))
    return response


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


port = int(os.environ.get('LAB05_R3_PORT', '0')) if os.environ.get('LAB05_R3') == '1' else 0
with make_server('127.0.0.1', port, observed, handler_class=QuietHandler) as server:
    (root / ('http-' + profile + '-ready.json')).write_text(json.dumps({
        'port': server.server_port, 'principal': verify_connection(), 'pid': os.getpid(),
    }))
    server.serve_forever()
