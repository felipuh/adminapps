"""S3 admission bounds, request quotas, and PostgreSQL write guards."""

from django.db import migrations, models


def install_s3_postgresql_guards(apps, schema_editor):
    """Protect budget counters from accidental direct runtime mutation.

    S3's application service performs its accounting inside a serializable
    transaction.  Runtime roles retain no UPDATE grant; this trigger is a
    second database-side guard for privileged maintenance connections.
    """
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE OR REPLACE FUNCTION public.financial_guard_budget_scope_update()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
              IF current_setting('financial.admission_transition', true) IS DISTINCT FROM 'authorized' THEN
                RAISE EXCEPTION USING
                  ERRCODE = '42501',
                  MESSAGE = 'financial budget changes require the S3 admission boundary';
              END IF;
              IF (to_jsonb(NEW) - 'reserved_exposure' - 'reserved_request_count')
                   IS DISTINCT FROM (to_jsonb(OLD) - 'reserved_exposure' - 'reserved_request_count') THEN
                RAISE EXCEPTION USING
                  ERRCODE = '55000',
                  MESSAGE = 'only S3 reservation counters may change during admission';
              END IF;
              RETURN NEW;
            END;
            $$;

            CREATE TRIGGER financial_budget_scopes_guarded_update
              BEFORE UPDATE ON public.financial_budget_scopes
              FOR EACH ROW EXECUTE FUNCTION public.financial_guard_budget_scope_update();
            """
        )


def remove_s3_postgresql_guards(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('DROP TRIGGER IF EXISTS financial_budget_scopes_guarded_update ON public.financial_budget_scopes')
        cursor.execute('DROP FUNCTION IF EXISTS public.financial_guard_budget_scope_update()')


class Migration(migrations.Migration):

    dependencies = [('financial', '0003_producer_identity_and_financial_rbac')]

    operations = [
        migrations.AddField(
            model_name='financialpolicyversion',
            name='max_input_tokens',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='financialpolicyversion',
            name='max_output_tokens',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='budgetscope',
            name='request_limit',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='budgetscope',
            name='reserved_request_count',
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddConstraint(
            model_name='budgetscope',
            constraint=models.CheckConstraint(
                check=models.Q(('reserved_exposure__gte', 0), ('settled_exposure__gte', 0),
                                   ('unresolved_exposure__gte', 0), ('approved_liability__gte', 0)),
                name='financial_budget_exposure_nonnegative',
            ),
        ),
        migrations.RunPython(install_s3_postgresql_guards, remove_s3_postgresql_guards),
    ]
