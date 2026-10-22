"""Real HTTP acceptance; synthetic credentials/JWTs never enter output or artifacts."""
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(os.environ['LAB04_ROOT'])
HERE = Path(__file__).resolve().parent
processes = []
streams = []
ports = {}
results = []


def state(profile):
    return json.loads((ROOT / ('http-' + profile + '-state.json')).read_text())


def call(profile, method, path, expected, payload=None, token=None, headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', ports[profile], timeout=15)
    supplied = {'Content-Type': 'application/json', **(headers or {})}
    if token:
        supplied['Authorization'] = 'Bearer ' + token
    try:
        connection.request(method, path, json.dumps(payload) if payload is not None else None, supplied)
        response = connection.getresponse()
        body = response.read()
        assert response.status == expected, (profile, method, path, response.status, expected)
    finally:
        connection.close()
    observed = state(profile)
    assert observed['principal'] == observed['session_user'] == 'lab04_' + profile
    results.append({'profile': profile, 'method': method, 'path': path,
                    'status': expected, **observed})
    return json.loads(body) if body and response.getheader('Content-Type', '').startswith('application/json') else None


try:
    for profile in ('iam', 'control_plane'):
        stream = (ROOT / ('http-' + profile + '.log')).open('w')
        streams.append(stream)
        process = subprocess.Popen([sys.executable, str(HERE / 'http_server.py')],
            env={**os.environ, 'LAB05_HTTP': '1', 'LAB04_PROFILE': profile, 'LAB04_ROLE': 'lab04_' + profile},
            stdout=stream, stderr=stream)
        processes.append(process)
        ready = ROOT / ('http-' + profile + '-ready.json')
        deadline = time.monotonic() + 30
        while not ready.exists():
            assert process.poll() is None, 'HTTP process exited; inspect private local log'
            assert time.monotonic() < deadline, 'HTTP readiness timed out'
            time.sleep(0.1)
        value = json.loads(ready.read_text())
        assert value['principal'] == 'lab04_' + profile
        ports[profile] = value['port']
    assert ports['iam'] != ports['control_plane']
    call('iam', 'GET', '/api/products/systems/', 404)
    call('iam', 'GET', '/admin/', 404)
    call('control_plane', 'POST', '/api/auth/login/', 404, {})
    call('control_plane', 'GET', '/admin/', 404)
    pair = call('iam', 'POST', '/api/auth/login/', 200, {
        'email': 'root@example.invalid', 'password': 'Synthetic-LAB04-only!Q27'})
    token = pair['access']
    call('control_plane', 'GET', '/api/products/systems/', 200, token=token)
    before = state('control_plane')
    assert before['handler_calls'] == 1
    call('iam', 'POST', '/api/auth/logout/', 200, {'refresh': pair['refresh']}, token=token)
    for headers in ({}, {'X-API-Key': 'synthetic-technical-header', 'X-Service-Token': 'synthetic'}):
        call('control_plane', 'GET', '/api/products/systems/', 401, token=token, headers=headers)
        after = state('control_plane')
        assert after['handler_calls'] == before['handler_calls']
        assert after['backend_pid'] != before['backend_pid']
        before = after
    call('control_plane', 'GET', '/api/products/systems/', 403,
         headers={'X-API-Key': 'synthetic-technical-header'})
    assert state('control_plane')['handler_calls'] == 1
    # Restart only the cluster provisioned by our parent, inside its private root.
    subprocess.run(['pg_ctl', '-D', str(ROOT / 'runtime/data'), '-l', str(ROOT / 'runtime/server.log'),
                    '-m', 'fast', '-w', 'restart'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    call('control_plane', 'GET', '/api/products/systems/', 401, token=token)
    assert state('control_plane')['handler_calls'] == 1
    assert state('control_plane')['backend_pid'] != before['backend_pid']
    call('iam', 'POST', '/api/auth/refresh/', 401, {'refresh': pair['refresh']})
    (ROOT / 'http-result.json').write_text(json.dumps({
        'status': 'LAB05_A_HTTP_RUNTIME_PASS', 'transport': 'real loopback TCP HTTP',
        'postgresql': 'private Unix socket, real profile logins, restarted',
        'revoked_handler_delta': 0, 'cases': results,
    }, indent=2))
    print('LAB05_A_HTTP_RUNTIME_PASS; real SQL principals, fresh connections and PostgreSQL restart')
finally:
    for process in processes:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    for stream in streams:
        stream.close()
