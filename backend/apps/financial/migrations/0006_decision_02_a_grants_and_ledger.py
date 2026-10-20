"""Decision 02-A live grants and immutable invocation replay ledger."""
import uuid

from django.db import migrations, models
import django.db.models.deletion


def install_decision_02_a_postgresql_security(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            DO $$
            BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'adminapps_financial_executor') THEN
                RAISE EXCEPTION 'required Decision 02-A role adminapps_financial_executor is not provisioned';
              END IF;
              IF EXISTS (
                SELECT 1 FROM pg_roles WHERE rolname = 'adminapps_financial_executor'
                  AND (rolsuper OR rolbypassrls OR rolinherit OR NOT rolcanlogin)
              ) THEN
                RAISE EXCEPTION 'executor must be LOGIN, NOSUPERUSER, NOBYPASSRLS and NOINHERIT';
              END IF;
            END $$;
            ALTER TABLE public.financial_producer_tenant_grants ENABLE ROW LEVEL SECURITY;
            ALTER TABLE public.financial_producer_tenant_grants FORCE ROW LEVEL SECURITY;
            ALTER TABLE public.financial_producer_tenant_grant_events ENABLE ROW LEVEL SECURITY;
            ALTER TABLE public.financial_producer_tenant_grant_events FORCE ROW LEVEL SECURITY;
            ALTER TABLE public.financial_invocation_ledger ENABLE ROW LEVEL SECURITY;
            ALTER TABLE public.financial_invocation_ledger FORCE ROW LEVEL SECURITY;
            REVOKE ALL ON TABLE public.financial_producer_tenant_grants,
                                      public.financial_producer_tenant_grant_events,
                                      public.financial_invocation_ledger
              FROM PUBLIC, adminapps_financial_runtime, adminapps_financial_executor;
            CREATE TRIGGER financial_producer_tenant_grant_events_append_only
              BEFORE UPDATE OR DELETE ON public.financial_producer_tenant_grant_events
              FOR EACH ROW EXECUTE FUNCTION public.financial_reject_immutable_change();
            CREATE TRIGGER financial_invocation_ledger_append_only
              BEFORE UPDATE OR DELETE ON public.financial_invocation_ledger
              FOR EACH ROW EXECUTE FUNCTION public.financial_reject_immutable_change();
            CREATE POLICY financial_executor_grant_read ON public.financial_producer_tenant_grants
              FOR SELECT TO adminapps_financial_admission USING (true);
            CREATE POLICY financial_executor_grant_lock ON public.financial_producer_tenant_grants
              FOR UPDATE TO adminapps_financial_admission USING (true) WITH CHECK (true);
            CREATE POLICY financial_executor_grant_event_read ON public.financial_producer_tenant_grant_events
              FOR SELECT TO adminapps_financial_admission USING (true);
            CREATE POLICY financial_executor_ledger_all ON public.financial_invocation_ledger
              FOR ALL TO adminapps_financial_admission USING (true) WITH CHECK (true);
            GRANT SELECT, UPDATE ON public.financial_producer_tenant_grants TO adminapps_financial_admission;
            GRANT SELECT ON public.financial_producer_tenant_grant_events TO adminapps_financial_admission;
            GRANT INSERT, SELECT ON public.financial_invocation_ledger TO adminapps_financial_admission;
        """)


class Migration(migrations.Migration):
    dependencies = [('financial', '0005_s3_runtime_admission_boundary')]

    operations = [
        migrations.CreateModel(
            name='ProducerTenantGrant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('operation', models.CharField(max_length=40)),
                ('environment', models.CharField(choices=[('controlled_test', 'Controlled test'), ('staging', 'Staging'), ('production', 'Production')], max_length=20)),
                ('state', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('revoked', 'Revoked')], default='active', max_length=16)),
                ('version', models.PositiveIntegerField(default=1)),
                ('effective_from', models.DateTimeField()),
                ('effective_until', models.DateTimeField(blank=True, null=True)),
                ('revocation_evidence_hash', models.CharField(blank=True, max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='financial_producer_grants', to='organizations.organization')),
                ('producer_registration', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tenant_grants', to='financial.producerregistration')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='financial_producer_grants', to='products.productsystem')),
            ],
            options={'db_table': 'financial_producer_tenant_grants'},
        ),
        migrations.CreateModel(
            name='ProducerTenantGrantLifecycleEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('state', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('revoked', 'Revoked')], max_length=16)),
                ('actor_reference', models.CharField(max_length=160)),
                ('evidence_hash', models.CharField(max_length=128)),
                ('reason_code', models.CharField(blank=True, max_length=80)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('grant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lifecycle_events', to='financial.producertenantgrant')),
            ],
            options={'db_table': 'financial_producer_tenant_grant_events', 'ordering': ['created_at', 'id']},
        ),
        migrations.CreateModel(
            name='FinancialInvocationLedger',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('capability_id', models.UUIDField(unique=True)),
                ('invocation_id', models.UUIDField()),
                ('material_request_hash', models.CharField(max_length=128)),
                ('issuer_id', models.CharField(max_length=120)),
                ('key_id', models.CharField(max_length=120)),
                ('capability_version', models.PositiveSmallIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('decision', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='financial.admissiondecision')),
                ('grant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financial.producertenantgrant')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organizations.organization')),
                ('producer_registration', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financial.producerregistration')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='products.productsystem')),
            ],
            options={'db_table': 'financial_invocation_ledger'},
        ),
        migrations.AddConstraint(
            model_name='producertenantgrant',
            constraint=models.UniqueConstraint(fields=('producer_registration', 'organization', 'product', 'operation', 'environment', 'version'), name='financial_producer_tenant_grant_version_unique'),
        ),
        migrations.AddConstraint(
            model_name='producertenantgrant',
            constraint=models.CheckConstraint(check=models.Q(effective_until__isnull=True) | models.Q(effective_until__gt=models.F('effective_from')), name='financial_grant_effective_range'),
        ),
        migrations.AddIndex(model_name='producertenantgrant', index=models.Index(fields=['producer_registration', 'organization', 'product', 'state'], name='financial_p_produce_2b5b97_idx')),
        migrations.AddIndex(model_name='producertenantgrantlifecycleevent', index=models.Index(fields=['grant', 'created_at'], name='financial_p_grant_i_571fdf_idx')),
        migrations.AddConstraint(
            model_name='financialinvocationledger',
            constraint=models.UniqueConstraint(fields=('producer_registration', 'organization', 'product', 'invocation_id'), name='financial_invocation_ledger_identity_unique'),
        ),
        migrations.RunPython(install_decision_02_a_postgresql_security, migrations.RunPython.noop),
    ]
