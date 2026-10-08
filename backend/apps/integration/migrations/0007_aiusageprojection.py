import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('integration', '0006_integration_api_key_lifecycle'), ('organizations', '0004_tenantintegrationoutbox')]

    operations = [
        migrations.CreateModel(
            name='AIUsageProjection',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('source', models.CharField(max_length=80, default='iso-smart')),
                ('usage_event_id', models.UUIDField()), ('usage_record_id', models.UUIDField()),
                ('product_identifier', models.CharField(max_length=80)), ('agent_name', models.CharField(max_length=120)),
                ('capability_name', models.CharField(max_length=120)), ('execution_id', models.UUIDField()), ('correlation_id', models.UUIDField()),
                ('provider', models.CharField(max_length=120)), ('model_identifier', models.CharField(max_length=200)),
                ('attempted_at', models.DateTimeField(db_index=True)), ('attempt_status', models.CharField(max_length=24)),
                ('usage_status', models.CharField(max_length=24)), ('input_tokens', models.BigIntegerField(null=True, blank=True)),
                ('output_tokens', models.BigIntegerField(null=True, blank=True)), ('total_tokens', models.BigIntegerField(null=True, blank=True)),
                ('estimated_provider_cost', models.DecimalField(max_digits=20, decimal_places=10, null=True, blank=True)),
                ('currency', models.CharField(max_length=3, null=True, blank=True)), ('cost_status', models.CharField(max_length=24)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ai_usage_records', to='organizations.organization')),
            ],
            options={'db_table': 'integration_ai_usage_projection', 'ordering': ['-attempted_at']},
        ),
        migrations.AddConstraint(model_name='aiusageprojection', constraint=models.UniqueConstraint(fields=('source', 'usage_event_id'), name='integration_ai_usage_event_unique')),
        migrations.AddConstraint(model_name='aiusageprojection', constraint=models.UniqueConstraint(fields=('source', 'usage_record_id'), name='integration_ai_usage_record_unique')),
        migrations.AddIndex(model_name='aiusageprojection', index=models.Index(fields=['organization', 'attempted_at'], name='ai_usage_org_time_idx')),
        migrations.AddIndex(model_name='aiusageprojection', index=models.Index(fields=['product_identifier', 'model_identifier', 'attempted_at'], name='ai_usage_dims_time_idx')),
    ]
