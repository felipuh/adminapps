import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('users', '0003_remove_twofactorauth_backup_codes_and_more')]
    operations = [
        migrations.AddField('twofactorauth', 'generation', models.UUIDField(default=uuid.uuid4, editable=False)),
        migrations.AddField('twofactorauth', 'last_totp_counter', models.BigIntegerField(blank=True, null=True)),
        migrations.AddField('twofactorauth', 'failed_attempts', models.PositiveSmallIntegerField(default=0)),
        migrations.AddField('twofactorauth', 'attempts_expires_at', models.DateTimeField(blank=True, null=True)),
        migrations.CreateModel(
            name='TwoFactorChallenge',
            fields=[
                ('nonce_digest', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('version', models.PositiveSmallIntegerField(default=1)),
                ('purpose', models.CharField(max_length=40)),
                ('scope', models.CharField(max_length=40)),
                ('generation', models.UUIDField()),
                ('context_digest', models.CharField(max_length=64)),
                ('issued_at', models.DateTimeField()),
                ('expires_at', models.DateTimeField()),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'two_factor_challenges'},
        ),
    ]
