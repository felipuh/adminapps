from unittest.mock import patch

from django.test import SimpleTestCase

from apps.billing.apps import _should_start_scheduler


class BillingSchedulerStartupTests(SimpleTestCase):
    def test_management_commands_do_not_start_scheduler(self):
        for command in ('check', 'test', 'showmigrations', 'makemigrations', 'migrate'):
            with self.subTest(command=command), patch('sys.argv', ['manage.py', command]), patch.dict('os.environ', {}, clear=True):
                self.assertFalse(_should_start_scheduler())

    def test_runserver_starts_only_in_main_reloader_process(self):
        with patch('sys.argv', ['manage.py', 'runserver']), patch.dict('os.environ', {}, clear=True):
            self.assertFalse(_should_start_scheduler())

        with patch('sys.argv', ['manage.py', 'runserver']), patch.dict('os.environ', {'RUN_MAIN': 'true'}, clear=True):
            self.assertTrue(_should_start_scheduler())

    def test_force_flag_allows_explicit_scheduler_process(self):
        with patch('sys.argv', ['manage.py', 'billing_scheduler']), patch.dict('os.environ', {'BILLING_SCHEDULER_FORCE': 'true'}, clear=True):
            self.assertTrue(_should_start_scheduler())
