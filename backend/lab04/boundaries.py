import json
import lab_env
import psycopg2
from psycopg2 import sql

results = []
catalog = []
for profile in ('iam', 'control_plane', 'admin', 'events'):
    role = 'lab04_' + profile
    secret = json.loads((lab_env.ROOT / 'runtime' / ('credentials-' + role + '.json')).read_text())
    connection = psycopg2.connect(host=str(lab_env.ROOT / 'runtime/socket'), port=56434,
                                 dbname='lab04_human', user=role, password=secret['password'])
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_user,session_user,inet_server_addr()')
        assert cursor.fetchone() == (role, role, None)
        cursor.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user")
        assert not any(cursor.fetchone())
        cursor.execute("SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user) OR roleid=(SELECT oid FROM pg_roles WHERE rolname=current_user)")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT oid,relname FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r' ORDER BY relname")
        tables = cursor.fetchall()
        for oid, table in tables:
            privileges = []
            for privilege in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER'):
                cursor.execute('SELECT has_table_privilege(%s,%s)', [oid, privilege])
                if cursor.fetchone()[0]:
                    privileges.append(privilege)
            assert not set(privileges).intersection({'TRUNCATE', 'REFERENCES', 'TRIGGER'})
            assert 'DELETE' not in privileges or (table == 'django_session' and profile != 'events')
            if privileges:
                catalog.append({'role': role, 'table': table, 'privileges': privileges})
            if 'UPDATE' not in privileges:
                cursor.execute("SELECT attname FROM pg_attribute WHERE attrelid=%s AND attnum>0 AND NOT attisdropped AND has_column_privilege(%s,attnum,'UPDATE')", [oid, oid])
                columns = [row[0] for row in cursor.fetchall()]
                assert not columns or (table == 'sso_security_fence' and set(columns) <= {'generation', 'authority_epoch'})
        cursor.execute("SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND (prosecdef OR has_function_privilege(oid,'EXECUTE'))")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SELECT count(*) FROM pg_class WHERE CASE WHEN relnamespace='public'::regnamespace AND relkind='S' THEN has_sequence_privilege(oid,'UPDATE') ELSE false END")
        assert cursor.fetchone()[0] == 0
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
                results.append({'role': role, 'sql': 'SET ROLE lab04_' + other, 'sqlstate': error.pgcode})
            else:
                raise AssertionError('Runtime assumed another profile')
    connection.close()
(lab_env.ROOT / 'boundaries.json').write_text(json.dumps(results, indent=2))
(lab_env.ROOT / 'privileges.json').write_text(json.dumps(catalog, indent=2))
