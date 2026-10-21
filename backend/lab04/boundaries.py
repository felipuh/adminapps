import json
import lab_env
import psycopg2
from psycopg2 import sql

results = []
for profile in ('iam', 'control_plane', 'admin', 'events'):
    role = 'lab04_' + profile
    secret = json.loads((lab_env.ROOT / 'runtime' / ('credentials-' + role + '.json')).read_text())
    connection = psycopg2.connect(host=str(lab_env.ROOT / 'runtime/socket'), port=56434,
                                 dbname='lab04_human', user=role, password=secret['password'])
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_user,session_user,inet_server_addr()')
        assert cursor.fetchone() == (role, role, None)
        for statement in (
            'DELETE FROM user_sessions', 'TRUNCATE user_sessions',
            'DELETE FROM sso_sessions', 'TRUNCATE sso_security_fence',
            'DELETE FROM sso_revocation_outbox',
            'ALTER TABLE user_sessions DISABLE TRIGGER ALL',
            'CREATE TABLE public.lab_escape (id integer)',
            'CREATE TEMP TABLE lab_escape (id integer)',
            'SET ROLE lab04_maintenance',
            "SET session_replication_role='replica'",
            'UPDATE sso_security_fence SET enabled=true',
        ):
            try:
                cursor.execute(statement)
            except psycopg2.Error as error:
                assert error.pgcode == '42501', (statement, error.pgcode)
                results.append({'role': role, 'sql': statement, 'sqlstate': error.pgcode})
            else:
                raise AssertionError((role, statement))
        for other in ('iam', 'control_plane', 'admin', 'events'):
            if other == profile:
                continue
            try:
                cursor.execute(sql.SQL('SET ROLE {}').format(sql.Identifier('lab04_' + other)))
            except psycopg2.Error as error:
                assert error.pgcode == '42501'
            else:
                raise AssertionError('Runtime assumed another profile')
    connection.close()
(lab_env.ROOT / 'boundaries.json').write_text(json.dumps(results, indent=2))
