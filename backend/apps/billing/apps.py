from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.billing'
    verbose_name = 'Billing'

    def ready(self):
        from django.conf import settings
        if getattr(settings, 'BILLING_SCHEDULER_ENABLED', False):
            # Guard against double-start in dev (reloader runs ready() twice).
            import os
            if os.environ.get('RUN_MAIN') != 'true' or os.environ.get('BILLING_SCHEDULER_FORCE', ''):
                from apps.billing.scheduler import start_scheduler
                start_scheduler()
