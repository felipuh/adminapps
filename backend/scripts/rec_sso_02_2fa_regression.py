"""Run the existing 2FA offline contracts with additional connection guards."""

import json
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

from django.db.backends.base.base import BaseDatabaseWrapper

source = Path(__file__).resolve().parents[1] / 'apps/users/tests_2fa_contract.py'
with patch('socket.create_connection', side_effect=AssertionError('Network forbidden')) as net, \
     patch('socket.getaddrinfo', side_effect=AssertionError('DNS forbidden')) as dns, \
     patch.object(BaseDatabaseWrapper, 'connect', side_effect=AssertionError('DB forbidden')) as db:
    # The existing runner itself blocks socket.connect and socket.connect_ex.
    sys.argv = [str(source), '-v']
    code = 1
    try:
        runpy.run_path(str(source), run_name='__main__')
    except SystemExit as exc:
        code = exc.code
    print(json.dumps({'database_attempts': db.call_count,
                      'network_create_attempts': net.call_count,
                      'dns_attempts': dns.call_count, 'exit_code': code}))
    sys.exit(code or bool(db.call_count + net.call_count + dns.call_count))
