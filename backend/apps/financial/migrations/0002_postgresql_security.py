"""PostgreSQL-only S1 tenant isolation, grants, and immutable-evidence guards."""
from django.db import migrations


FINANCIAL_TABLES = (
    'financial_producer_registrations',
    'financial_policies',
    'financial_policy_versions',
    'financial_budget_scopes',
    'financial_verified_tariffs',
    'financial_admission_decisions',
    'financial_reservations',
    'financial_settlement_evidence',
    'financial_resolution_history',
    'financial_audit_events',
)

TENANT_TABLES = (
    'financial_policies',
    'financial_budget_scopes',
    'financial_admission_decisions',
    'financial_reservations',
    'financial_settlement_evidence',
    'financial_resolution_history',
    'financial_audit_events',
)

IMMUTABLE_TABLES = (
    'financial_producer_registrations',
    'financial_policies',
    'financial_policy_versions',
    'financial_verified_tariffs',
    'financial_admission_decisions',
    'financial_settlement_evidence',
    'financial_resolution_history',
    'financial_audit_events',
)

REQUIRED_ROLES = (
    'adminapps_financial_migration',
    'adminapps_financial_runtime',
    'adminapps_financial_producer',
    'adminapps_financial_audit',
    'adminapps_financial_reconciliation',
)


def install_postgresql_security(apps, schema_editor):
    """Install S1 controls after explicit DBA role provisioning.

    PostgreSQL roles are cluster-level principals, not Django-model data.  The
    companion bootstrap script provisions the NOINHERIT/NOBYPASSRLS roles before
    this migration is applied.  Refusing an unprovisioned PostgreSQL database is
    intentional: silently falling back to less secure grants is not safe.
    """
    if schema_editor.connection.vendor != 'postgresql':
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            DO $$
            DECLARE required_role text;
            BEGIN
              FOREACH required_role IN ARRAY ARRAY[
                'adminapps_financial_migration',
                'adminapps_financial_runtime',
                'adminapps_financial_producer',
                'adminapps_financial_audit',
                'adminapps_financial_reconciliation'
              ]
              LOOP
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = required_role) THEN
                  RAISE EXCEPTION 'required S1 financial role % is not provisioned', required_role;
                END IF;
                IF EXISTS (
                  SELECT 1 FROM pg_roles
                  WHERE rolname = required_role
                    AND (rolsuper OR rolbypassrls OR rolinherit)
                ) THEN
                  RAISE EXCEPTION 'S1 financial role % must be NOSUPERUSER, NOBYPASSRLS and NOINHERIT', required_role;
                END IF;
              END LOOP;
            END $$;

            CREATE OR REPLACE FUNCTION public.financial_reject_immutable_change()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
              RAISE EXCEPTION USING
                ERRCODE = '55000',
                MESSAGE = format('%I is append-only financial evidence', TG_TABLE_NAME);
            END;
            $$;

            CREATE OR REPLACE FUNCTION public.financial_guard_reservation_update()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
              IF current_setting('financial.reservation_transition', true) IS DISTINCT FROM 'authorized' THEN
                RAISE EXCEPTION USING
                  ERRCODE = '42501',
                  MESSAGE = 'financial reservation changes require a governed transition boundary';
              END IF;
              IF (to_jsonb(NEW) - 'state' - 'state_updated_at')
                   IS DISTINCT FROM (to_jsonb(OLD) - 'state' - 'state_updated_at') THEN
                RAISE EXCEPTION USING
                  ERRCODE = '55000',
                  MESSAGE = 'only financial reservation state fields may change';
              END IF;
              RETURN NEW;
            END;
            $$;
            """
        )

        for table in FINANCIAL_TABLES:
            cursor.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')
            cursor.execute(f'ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY')
            cursor.execute(f'REVOKE ALL ON TABLE public.{table} FROM PUBLIC')

        for table in IMMUTABLE_TABLES:
            cursor.execute(
                f'''CREATE TRIGGER {table}_append_only
                    BEFORE UPDATE OR DELETE ON public.{table}
                    FOR EACH ROW EXECUTE FUNCTION public.financial_reject_immutable_change()'''
            )

        cursor.execute(
            '''CREATE TRIGGER financial_reservations_guarded_update
               BEFORE UPDATE ON public.financial_reservations
               FOR EACH ROW EXECUTE FUNCTION public.financial_guard_reservation_update()'''
        )

        for table in TENANT_TABLES:
            cursor.execute(
                f'''CREATE POLICY {table}_tenant_read ON public.{table}
                    FOR SELECT TO adminapps_financial_runtime
                    USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)'''
            )
            cursor.execute(
                f'''CREATE POLICY {table}_audit_read ON public.{table}
                    FOR SELECT TO adminapps_financial_audit
                    USING (true)'''
            )

        for table in ('financial_admission_decisions', 'financial_settlement_evidence', 'financial_resolution_history', 'financial_audit_events'):
            cursor.execute(
                f'''CREATE POLICY {table}_tenant_insert ON public.{table}
                    FOR INSERT TO adminapps_financial_runtime
                    WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)'''
            )

        for table in ('financial_reservations', 'financial_settlement_evidence', 'financial_resolution_history'):
            cursor.execute(
                f'''CREATE POLICY {table}_reconciliation_read ON public.{table}
                    FOR SELECT TO adminapps_financial_reconciliation
                    USING (true)'''
            )

        for table in ('financial_producer_registrations', 'financial_policy_versions', 'financial_verified_tariffs'):
            cursor.execute(
                f'''CREATE POLICY {table}_audit_read ON public.{table}
                    FOR SELECT TO adminapps_financial_audit
                    USING (true)'''
            )

        cursor.execute(
            '''GRANT SELECT ON public.financial_admission_decisions,
                                public.financial_reservations,
                                public.financial_settlement_evidence,
                                public.financial_resolution_history,
                                public.financial_audit_events
               TO adminapps_financial_runtime'''
        )
        cursor.execute(
            '''GRANT INSERT ON public.financial_admission_decisions,
                                public.financial_settlement_evidence,
                                public.financial_resolution_history,
                                public.financial_audit_events
               TO adminapps_financial_runtime'''
        )
        cursor.execute(
            'GRANT SELECT ON ' + ', '.join(f'public.{table}' for table in FINANCIAL_TABLES) + ' TO adminapps_financial_audit'
        )
        cursor.execute(
            '''GRANT SELECT ON public.financial_reservations,
                                public.financial_settlement_evidence,
                                public.financial_resolution_history
               TO adminapps_financial_reconciliation'''
        )

        # Ownership is the migration role, not an application principal.  A
        # future migration connection must use this dedicated role.
        for table in FINANCIAL_TABLES:
            cursor.execute(f'ALTER TABLE public.{table} OWNER TO adminapps_financial_migration')


def remove_postgresql_security(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        for table in FINANCIAL_TABLES:
            cursor.execute(f'ALTER TABLE public.{table} NO FORCE ROW LEVEL SECURITY')
            cursor.execute(f'ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY')
        cursor.execute('DROP FUNCTION IF EXISTS public.financial_guard_reservation_update()')
        cursor.execute('DROP FUNCTION IF EXISTS public.financial_reject_immutable_change()')


class Migration(migrations.Migration):
    dependencies = [('financial', '0001_financial_s1_foundation')]

    operations = [migrations.RunPython(install_postgresql_security, remove_postgresql_security)]
