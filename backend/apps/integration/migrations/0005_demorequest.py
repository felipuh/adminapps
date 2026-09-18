import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('integration', '0004_integrationapikey_last_used_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DemoRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('external_id', models.UUIDField(db_index=True, unique=True)),
                ('full_name', models.CharField(max_length=160)),
                ('work_email', models.EmailField(db_index=True, max_length=254)),
                ('organization_name', models.CharField(db_index=True, max_length=200)),
                ('product_code', models.CharField(db_index=True, max_length=40)),
                ('priority', models.CharField(choices=[('document_control', 'Control documental'), ('audit_readiness', 'Preparación de auditorías'), ('findings_actions', 'Hallazgos y acciones'), ('indicators_followup', 'Indicadores y seguimiento'), ('general_evaluation', 'Evaluación general')], db_index=True, max_length=32)),
                ('status', models.CharField(choices=[('new', 'Nueva'), ('contacted', 'Contactada'), ('qualified', 'Calificada'), ('scheduled', 'Agendada'), ('closed', 'Cerrada')], db_index=True, default='new', max_length=20)),
                ('source', models.CharField(db_index=True, default='landing', max_length=80)),
                ('campaign', models.CharField(blank=True, db_index=True, max_length=120)),
                ('page_url', models.URLField(blank=True, max_length=500)),
                ('consent_given', models.BooleanField(default=False)),
                ('consented_at', models.DateTimeField()),
                ('source_service', models.CharField(max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owned_demo_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'integration_demo_requests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='demorequest',
            index=models.Index(fields=['status', 'created_at'], name='demo_req_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='demorequest',
            index=models.Index(fields=['product_code', 'priority'], name='demo_req_product_priority_idx'),
        ),
    ]
