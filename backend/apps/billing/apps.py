from django.apps import AppConfig


def _should_start_scheduler():
    import os
    import sys

    # Management commands import app configs too; they must not start background jobs.
    blocked_commands = {
        'check',
        'compilemessages',
        'createcachetable',
        'dbshell',
        'diffsettings',
        'dumpdata',
        'flush',
        'inspectdb',
        'loaddata',
        'makemessages',
        'makemigrations',
        'migrate',
        'sendtestemail',
        'shell',
        'showmigrations',
        'sqlflush',
        'sqlmigrate',
        'sqlsequencereset',
        'squashmigrations',
        'startapp',
        'startproject',
        'test',
    }
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command in blocked_commands:
        return False

    if os.environ.get('BILLING_SCHEDULER_FORCE', '').strip().lower() in ('1', 'true', 'yes', 'on'):
        return True

    if command == 'runserver':
        return os.environ.get('RUN_MAIN') == 'true'

    return command in {'gunicorn', 'uwsgi', 'daphne', 'uvicorn'}


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.billing'
    verbose_name = 'Billing'

    def ready(self):
        from django.conf import settings
        if getattr(settings, 'BILLING_SCHEDULER_ENABLED', False):
            if _should_start_scheduler():
                from apps.billing.scheduler import start_scheduler
                start_scheduler()
