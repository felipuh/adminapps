"""S2 producer lifecycle evidence and dedicated central financial permissions."""

import uuid

from django.db import migrations, models
import django.db.models.deletion


S2_CENTRAL_TABLES = (
    'financial_producer_registration_events',
    'financial_permission_audit_events',
)


def install_s2_postgresql_security(apps, schema_editor):
    """Extend S1 append-only/RLS protection without weakening its policies."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        for table in S2_CENTRAL_TABLES:
            cursor.execute(f'ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY')
            cursor.execute(f'ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY')
            cursor.execute(f'REVOKE ALL ON TABLE public.{table} FROM PUBLIC')
            cursor.execute(
                f'''CREATE TRIGGER {table}_append_only
                    BEFORE UPDATE OR DELETE ON public.{table}
                    FOR EACH ROW EXECUTE FUNCTION public.financial_reject_immutable_change()'''
            )
            cursor.execute(
                f'''CREATE POLICY {table}_audit_read ON public.{table}
                    FOR SELECT TO adminapps_financial_audit USING (true)'''
            )
            cursor.execute(
                f'''CREATE POLICY {table}_runtime_insert ON public.{table}
                    FOR INSERT TO adminapps_financial_runtime WITH CHECK (true)'''
            )
            cursor.execute(f'GRANT SELECT ON public.{table} TO adminapps_financial_audit')
            cursor.execute(f'GRANT INSERT ON public.{table} TO adminapps_financial_runtime')
            cursor.execute(f'ALTER TABLE public.{table} OWNER TO adminapps_financial_migration')

        # A registration itself is immutable after creation.  Lifecycle changes
        # are captured only in the protected append-only event table above.
        cursor.execute(
            '''CREATE POLICY financial_producer_registrations_runtime_insert
               ON public.financial_producer_registrations
               FOR INSERT TO adminapps_financial_runtime WITH CHECK (true)'''
        )
        cursor.execute(
            'GRANT INSERT ON public.financial_producer_registrations TO adminapps_financial_runtime'
        )


def remove_s2_postgresql_security(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        for table in S2_CENTRAL_TABLES:
            cursor.execute(f'ALTER TABLE public.{table} NO FORCE ROW LEVEL SECURITY')
            cursor.execute(f'ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY')


class Migration(migrations.Migration):

    dependencies = [('financial', '0002_postgresql_security')]

    operations = [
        migrations.CreateModel(
            name='FinancialPermissionAuditEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(choices=[('granted', 'Granted'), ('revoked', 'Revoked'), ('denied', 'Denied')], max_length=16)),
                ('permission_code', models.CharField(max_length=80)),
                ('actor_reference', models.CharField(max_length=160)),
                ('subject_reference', models.CharField(blank=True, max_length=160)),
                ('reason_code', models.CharField(blank=True, max_length=80)),
                ('correlation_id', models.UUIDField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'financial_permission_audit_events',
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ProducerRegistrationLifecycleEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('lifecycle_state', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('suspended', 'Suspended'), ('revoked', 'Revoked'), ('retired', 'Retired')], max_length=16)),
                ('actor_reference', models.CharField(max_length=160)),
                ('evidence_hash', models.CharField(max_length=128)),
                ('reason_code', models.CharField(blank=True, max_length=80)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('registration', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lifecycle_events', to='financial.producerregistration')),
            ],
            options={
                'db_table': 'financial_producer_registration_events',
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='financialpermissionauditevent',
            index=models.Index(fields=['permission_code', 'created_at'], name='financial_p_permiss_02787c_idx'),
        ),
        migrations.AddIndex(
            model_name='producerregistrationlifecycleevent',
            index=models.Index(fields=['registration', 'created_at'], name='financial_p_registr_31b952_idx'),
        ),
        migrations.AlterModelOptions(
            name='financialpolicy',
            options={
                'db_table': 'financial_policies',
                'permissions': [
                    ('financial_policy_admin', 'Can administer financial policies'),
                    ('financial_budget_admin', 'Can administer financial budgets'),
                    ('financial_tariff_approve', 'Can approve financial tariffs'),
                    ('financial_evidence_review', 'Can review financial evidence'),
                    ('financial_reconcile', 'Can authorize financial reconciliation'),
                    ('financial_manual_resolution', 'Can authorize restricted manual resolution'),
                    ('financial_audit_read', 'Can access financial audit evidence'),
                    ('financial_admin', 'Can assign financial administration permissions'),
                ],
            },
        ),
        migrations.RunPython(install_s2_postgresql_security, remove_s2_postgresql_security),
    ]
