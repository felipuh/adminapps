import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def classify_existing_credentials(apps, schema_editor):
    integration_api_key = apps.get_model('integration', 'IntegrationAPIKey')
    integration_api_key.objects.all().update(
        credential_format='legacy_plaintext',
        status=models.Case(
            models.When(is_active=True, then=models.Value('active')),
            default=models.Value('revoked'),
            output_field=models.CharField(),
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ('integration', '0005_demorequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='integrationapikey',
            name='key',
            field=models.CharField(
                blank=True,
                help_text='Legacy plaintext key only; secure keys are never stored here.',
                max_length=255,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name='integrationapikey',
            name='credential_id',
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='integrationapikey',
            name='credential_hash',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='integrationapikey',
            name='credential_format',
            field=models.CharField(
                choices=[
                    ('legacy_plaintext', 'Legacy plaintext'),
                    ('hashed_v1', 'Hashed v1'),
                ],
                default='hashed_v1',
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name='integrationapikey',
            name='fingerprint',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='integrationapikey',
            name='status',
            field=models.CharField(
                choices=[
                    ('created', 'Created'),
                    ('active', 'Active'),
                    ('revoked', 'Revoked'),
                    ('rotated', 'Rotated'),
                ],
                default='active',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='integrationapikey',
            name='revoked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='integrationapikey',
            name='rotated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='integrationapikey',
            name='replaced_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='replaces',
                to='integration.integrationapikey',
            ),
        ),
        migrations.RunPython(classify_existing_credentials, migrations.RunPython.noop),
        migrations.CreateModel(
            name='IntegrationAPIKeyAuditEvent',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'event_id',
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ('action', models.CharField(
                    choices=[('created', 'Created'), ('rotated', 'Rotated')],
                    max_length=16,
                )),
                ('old_fingerprint', models.CharField(blank=True, max_length=80)),
                ('new_fingerprint', models.CharField(max_length=80)),
                ('service_name', models.CharField(max_length=100)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'actor',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='integration_api_key_audit_events',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    'new_credential',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='audit_events_as_new',
                        to='integration.integrationapikey',
                    ),
                ),
                (
                    'old_credential',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='audit_events_as_old',
                        to='integration.integrationapikey',
                    ),
                ),
            ],
            options={
                'db_table': 'integration_api_key_audit_events',
                'ordering': ['-created_at'],
            },
        ),
    ]
