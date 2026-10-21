"""Opt-in process boundaries. One process, one SQL principal, one URL surface.

Call configure() on an explicitly supplied settings dictionary before Django
starts. This module never loads dotenv, opens a connection, or selects secrets.
The operational settings are intentionally not activated by this module.
"""
from django.core.exceptions import ImproperlyConfigured


PROFILES = {'iam', 'control_plane', 'admin', 'events'}


def configure(namespace, profile, database):
    if profile not in PROFILES:
        raise ImproperlyConfigured('Unknown SQL runtime profile')
    if (database.get('ENGINE') != 'django.db.backends.postgresql'
            or not all(database.get(key) for key in ('NAME', 'USER', 'HOST'))
            or database.get('OPTIONS', {}).get('options')):
        raise ImproperlyConfigured('An explicit PostgreSQL principal without SET ROLE is required')
    namespace['DATABASES'] = {'default': dict(database)}
    namespace['DATABASE_ROUTERS'] = []
    namespace['ADMINAPPS_RUNTIME_PROFILE'] = profile
    namespace['ADMINAPPS_RUNTIME_ROLE'] = database['USER']
    namespace['ROOT_URLCONF'] = 'config.urls_' + profile
    namespace['BILLING_SCHEDULER_ENABLED'] = False
    middleware = list(namespace.get('MIDDLEWARE', []))
    namespace['MIDDLEWARE'] = ['config.runtime_profiles.RuntimeBoundaryMiddleware'] + middleware
    rest = dict(namespace.get('REST_FRAMEWORK', {}))
    rest['DEFAULT_AUTHENTICATION_CLASSES'] = [
        'apps.users.authentication.HumanJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]
    namespace['REST_FRAMEWORK'] = rest


def verify_connection():
    """Fail closed on identity/membership/owner drift, before resolving a handler."""
    from django.conf import settings
    from django.db import connection, connections

    if set(connections) != {'default'} or connection.vendor != 'postgresql':
        raise ImproperlyConfigured('Runtime requires one PostgreSQL connection')
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT current_user, session_user, r.rolsuper OR r.rolcreatedb
                   OR r.rolcreaterole OR r.rolreplication OR r.rolbypassrls,
                   EXISTS (SELECT FROM pg_auth_members WHERE member=r.oid OR roleid=r.oid),
                   EXISTS (SELECT FROM pg_class WHERE relowner=r.oid),
                   has_database_privilege(current_database(),'CREATE')
                     OR has_database_privilege(current_database(),'TEMP')
                     OR has_schema_privilege('public','CREATE'),
                   has_table_privilege('public.user_sessions','DELETE')
                     OR has_table_privilege('public.user_sessions','TRUNCATE')
            FROM pg_roles r WHERE r.rolname=current_user
        """)
        row = cursor.fetchone()
        profile = settings.ADMINAPPS_RUNTIME_PROFILE
        forbidden = {
            'iam': [('organizations', 'INSERT'), ('organizations', 'UPDATE'),
                    ('product_systems', 'UPDATE'), ('django_admin_log', 'INSERT')],
            'control_plane': [('django_admin_log', 'INSERT')],
            'admin': [('users_user_permissions', 'INSERT'), ('users_groups', 'INSERT'),
                      ('auth_group_permissions', 'INSERT')],
            'events': [('users', 'SELECT'), ('tenant_integration_outbox', 'INSERT'),
                       ('sso_revocation_outbox', 'UPDATE')],
        }.get(profile)
        if forbidden is None:
            raise ImproperlyConfigured('Unknown SQL runtime profile')
        for table, privilege in forbidden:
            cursor.execute('SELECT has_table_privilege(%s,%s)', ['public.' + table, privilege])
            if cursor.fetchone()[0]:
                raise ImproperlyConfigured('SQL privileges exceed the selected process profile')
    if (not row or row[:2] != (settings.ADMINAPPS_RUNTIME_ROLE,) * 2
            or any(row[2:])):
        raise ImproperlyConfigured('SQL runtime boundary rejected effective principal')
    return row[0]


class RuntimeBoundaryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        verify_connection()
        from django.conf import settings
        if settings.ADMINAPPS_RUNTIME_PROFILE == 'admin' and (
            request.headers.get('Authorization') or request.headers.get('X-API-Key')
        ):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Django Admin requiere una sesión humana por cookie.')
        return self.get_response(request)
