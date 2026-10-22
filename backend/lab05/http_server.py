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

profile = settings.ADMINAPPS_RUNTIME_PROFILE
assert profile in ('iam', 'control_plane')
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

application = get_wsgi_application()


def observed(environ, start_response):
    # Every real request has a fresh libpq session. Persist only non-secret evidence.
    connections.close_all()
    principal = verify_connection()
    with connection.cursor() as cursor:
        cursor.execute('SELECT session_user, pg_backend_pid()')
        session_user, backend_pid = cursor.fetchone()
    response = application(environ, start_response)
    (root / ('http-' + profile + '-state.json')).write_text(json.dumps({
        'principal': principal, 'session_user': session_user,
        'backend_pid': backend_pid, 'handler_calls': calls,
    }))
    return response


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


with make_server('127.0.0.1', 0, observed, handler_class=QuietHandler) as server:
    (root / ('http-' + profile + '-ready.json')).write_text(json.dumps({
        'port': server.server_port, 'principal': verify_connection(), 'pid': os.getpid(),
    }))
    server.serve_forever()
