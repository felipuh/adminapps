"""Django checks with settings from the new checkout, all DB/network denied."""
import os,sys,json
from unittest.mock import patch
sys.path.insert(0,os.getcwd())
guards=[patch(t,side_effect=AssertionError('Network forbidden')).start() for t in ('socket.socket.connect','socket.socket.connect_ex','socket.create_connection','socket.getaddrinfo')]
patch('dotenv.load_dotenv').start()
from django.db.backends.base.base import BaseDatabaseWrapper
db=patch.object(BaseDatabaseWrapper,'connect',side_effect=AssertionError('Database forbidden')).start()
from django.conf import settings
settings.LOGGING_CONFIG=None
settings.BILLING_SCHEDULER_ENABLED=False
import django
django.setup()
from django.core.management import call_command
call_command('check',databases=[])
print(json.dumps({'django':django.get_version(),'database_attempts':db.call_count,'network_attempts':sum(x.call_count for x in guards)}))
assert not db.call_count and not any(x.call_count for x in guards)
