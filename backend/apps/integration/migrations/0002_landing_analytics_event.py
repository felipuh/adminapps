from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('integration', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LandingAnalyticsEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_name', models.CharField(db_index=True, max_length=80)),
                ('event_date', models.DateField(db_index=True, default=django.utils.timezone.localdate)),
                ('occurred_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.CharField(blank=True, db_index=True, max_length=120)),
                ('variant', models.CharField(blank=True, db_index=True, max_length=8)),
                ('persona', models.CharField(blank=True, max_length=32)),
                ('intent', models.CharField(blank=True, db_index=True, max_length=24)),
                ('location', models.CharField(blank=True, max_length=80)),
                ('session_id', models.CharField(blank=True, db_index=True, max_length=120)),
                ('page_path', models.CharField(blank=True, max_length=255)),
                ('page_url', models.TextField(blank=True)),
                ('href', models.TextField(blank=True)),
                ('referrer', models.TextField(blank=True)),
                ('source_service', models.CharField(blank=True, max_length=64)),
                ('payload', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'db_table': 'landing_analytics_events',
                'ordering': ['-occurred_at'],
            },
        ),
        migrations.AddIndex(
            model_name='landinganalyticsevent',
            index=models.Index(fields=['event_date', 'campaign', 'variant'], name='landing_ana_event_d_becf14_idx'),
        ),
        migrations.AddIndex(
            model_name='landinganalyticsevent',
            index=models.Index(fields=['event_name', 'campaign'], name='landing_ana_event_n_a61111_idx'),
        ),
    ]
