import uuid

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def protect_tenant_id(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
        CREATE FUNCTION organizations_reject_tenant_id_change()
        RETURNS trigger LANGUAGE plpgsql AS $body$
        BEGIN
          IF NEW.id IS DISTINCT FROM OLD.id THEN
            RAISE EXCEPTION 'canonical tenant UUID is immutable';
          END IF;
          RETURN NEW;
        END $body$;
        CREATE TRIGGER organizations_immutable_tenant_id
        BEFORE UPDATE ON organizations FOR EACH ROW
        EXECUTE FUNCTION organizations_reject_tenant_id_change();
        """)


def unprotect_tenant_id(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
        DROP TRIGGER organizations_immutable_tenant_id ON organizations;
        DROP FUNCTION organizations_reject_tenant_id_change();
        """)


class Migration(migrations.Migration):
    dependencies = [('organizations', '0003_organizationfeatureflag')]
    operations = [
        migrations.CreateModel(
            name='TenantIntegrationOutbox',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('source_version', models.PositiveBigIntegerField()),
                ('envelope', models.JSONField()),
                ('status', models.CharField(max_length=20, default='pending')),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('available_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('delivered_at', models.DateTimeField(null=True, blank=True)),
                ('last_error', models.CharField(max_length=100, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(to='organizations.organization', on_delete=django.db.models.deletion.PROTECT, related_name='tenant_events')),
            ],
            options={'db_table': 'tenant_integration_outbox'},
        ),
        migrations.AddConstraint(model_name='tenantintegrationoutbox', constraint=models.UniqueConstraint(fields=['organization', 'source_version'], name='tenant_outbox_org_version_unique')),
        migrations.AddConstraint(model_name='tenantintegrationoutbox', constraint=models.CheckConstraint(check=models.Q(status__in=['pending', 'processing', 'delivered', 'failed']), name='tenant_outbox_status_valid')),
        migrations.AddIndex(model_name='tenantintegrationoutbox', index=models.Index(fields=['status', 'available_at'], name='tenant_outbox_ready_idx')),
        migrations.RunPython(protect_tenant_id, unprotect_tenant_id),
    ]
