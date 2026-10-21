import lab_env
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.core.management import call_command

executor = MigrationExecutor(connection)
targets = executor.loader.graph.leaf_nodes()
assert not executor.loader.applied_migrations
assert all(app != 'financial' for app, _ in targets)
executor.migrate(targets)
# Permissions/content types are fixtures, created exclusively as maintenance.
call_command('migrate', interactive=False, verbosity=0)
call_command('check')
with connection.cursor() as cursor:
    cursor.execute("SELECT count(*) FROM django_migrations WHERE app='financial'")
    assert cursor.fetchone()[0] == 0
