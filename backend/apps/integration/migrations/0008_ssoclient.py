"""CH durable registry schema; activation requires separately authorized migration."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('integration', '0007_aiusageprojection'),
        ('products', '0003_productentitlementauditlog'),
        ('organizations', '0004_tenantintegrationoutbox'),
    ]

    operations = [
        migrations.CreateModel(
            name='SSOClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.CharField(max_length=100, unique=True)),
                ('audience', models.CharField(max_length=255, unique=True)),
                ('issuer', models.URLField(max_length=500)),
                ('enabled', models.BooleanField(default=False)),
                ('token_family', models.CharField(default='CENTRAL', max_length=16)),
                ('algorithm', models.CharField(default='RS256', max_length=16)),
                ('allowed_kids', models.JSONField(default=list)),
                ('credential_policy', models.CharField(default='hashed_v1', max_length=32)),
                ('contract_version', models.CharField(default='rec-sso-03b-ch-v1', max_length=40)),
                ('principal', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='sso_client', to='integration.integrationapikey')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sso_clients', to='products.productsystem')),
                ('tenants', models.ManyToManyField(related_name='sso_clients', to='organizations.organization')),
            ],
            options={'db_table': 'integration_sso_clients'},
        ),
    ]
