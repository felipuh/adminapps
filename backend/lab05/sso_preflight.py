"""Real HTTP prerequisite reproduction, not cross-product acceptance.

Uses unchanged IAM/CP URL surfaces. No token bodies or credentials are retained.
Exit zero means the documented blocker was reproduced, never an E2E PASS.
"""
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(os.environ['LAB04_ROOT'])
HERE = Path(__file__).resolve().parent
processes, streams, cases = [], [], []
ports = {}


def call(profile, path, expected, payload, token=None, headers=None):
    conn = http.client.HTTPConnection('127.0.0.1', ports[profile], timeout=15)
    supplied = {'Content-Type': 'application/json', **(headers or {})}
    if token:
        supplied['Authorization'] = 'Bearer ' + token
    start = time.monotonic()
    try:
        conn.request('POST', path, json.dumps(payload), supplied)
        response = conn.getresponse()
        body = response.read()
        elapsed = round((time.monotonic() - start) * 1000, 3)
        assert response.status == expected, (profile, path, response.status, expected)
        content_type = response.getheader('Content-Type', '')
    finally:
        conn.close()
    observed = json.loads((ROOT / ('http-' + profile + '-state.json')).read_text())
    assert observed['principal'] == observed['session_user'] == 'lab04_' + profile
    cases.append({'profile': profile, 'path': path, 'method': 'POST',
                  'status': expected, 'elapsed_ms': elapsed, **observed})
    return json.loads(body) if content_type.startswith('application/json') else None


try:
    for profile in ('iam', 'control_plane'):
        stream = (ROOT / ('http-' + profile + '.log')).open('w')
        streams.append(stream)
        process = subprocess.Popen([sys.executable, str(HERE / 'http_server.py')],
            env={**os.environ, 'LAB05_HTTP': '1', 'LAB04_PROFILE': profile,
                 'LAB04_ROLE': 'lab04_' + profile}, stdout=stream, stderr=stream)
        processes.append(process)
        ready = ROOT / ('http-' + profile + '-ready.json')
        deadline = time.monotonic() + 30
        while not ready.exists():
            assert process.poll() is None, 'HTTP process exited; inspect private local log'
            assert time.monotonic() < deadline, 'HTTP readiness timed out'
            time.sleep(.1)
        value = json.loads(ready.read_text())
        assert value['principal'] == 'lab04_' + profile
        ports[profile] = value['port']
    assert ports['iam'] != ports['control_plane']
    pair = call('iam', '/api/auth/login/', 200,
                {'email': 'root@example.invalid', 'password': 'Synthetic-LAB04-only!Q27'})
    assert isinstance(pair.get('access'), str) and isinstance(pair.get('refresh'), str)
    # These are the existing integration contract paths, not invented probes.
    for profile in ('iam', 'control_plane'):
        for endpoint in ('login/', 'introspect/', 'logout/'):
            call(profile, '/api/integration/sso/' + endpoint, 404, {},
                 headers={'X-API-Key': 'synthetic-unregistered-preflight'})
    call('iam', '/api/auth/logout/', 200, {'refresh': pair['refresh']}, pair['access'])
    (ROOT / 'http-result.json').write_text(json.dumps({
        'status': 'LAB05_C1_BLOCKED_PREREQUISITES',
        'transport': 'real loopback TCP HTTP',
        'postgresql': 'private Unix socket; IAM and CP runtime principals',
        'consumer_started': False, 'consumer_e2e_pass': False,
        'sso_authorization_exercised': False,
        'finding': 'Existing SSO login/introspect/logout paths return 404 in both runtime profiles',
        'latency_scope': 'individual prerequisite requests only; not consumer or revocation latency',
        'cases': cases,
    }, indent=2))
    print('LAB05_C1_BLOCKED_PREREQUISITES; HTTP routing blocker reproduced')
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
    (ROOT / 'http-cleanup.json').write_text(json.dumps({
        'http_processes_stopped': all(p.poll() is not None for p in processes),
        'http_process_count': len(processes),
    }, indent=2))
