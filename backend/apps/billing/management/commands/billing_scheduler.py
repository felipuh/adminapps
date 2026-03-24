"""
Management command: billing_scheduler

Usage:
  python manage.py billing_scheduler run_now   # Trigger the batch job immediately
  python manage.py billing_scheduler status    # Show scheduler state and last log entries
  python manage.py billing_scheduler start     # Start scheduler in current process (blocks)
"""
import json
import sys

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Manage and inspect the billing APScheduler background job.'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['run_now', 'status', 'start'],
            help='Action to perform: run_now | status | start',
        )
        parser.add_argument(
            '--fiscal-profile',
            dest='fiscal_profile',
            default=None,
            help='(Optional) UUID of a specific FiscalProfile to run for run_now.',
        )
        parser.add_argument(
            '--product',
            dest='product',
            default=None,
            help='(Optional) UUID of a specific Product to run for run_now.',
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'run_now':
            self._run_now(options)
        elif action == 'status':
            self._status()
        elif action == 'start':
            self._start()

    def _run_now(self, options):
        from apps.billing.scheduler import _run_billing_batch_job
        from apps.billing.models import FiscalProfile, ProductCatalog
        from apps.billing.services import run_billing_cycle_batch

        fp_id = options.get('fiscal_profile')
        prod_id = options.get('product')

        if fp_id and prod_id:
            # Run a targeted single pair
            try:
                fp = FiscalProfile.objects.get(pk=fp_id)
                product = ProductCatalog.objects.get(pk=prod_id)
            except (FiscalProfile.DoesNotExist, ProductCatalog.DoesNotExist) as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                sys.exit(1)
            report = run_billing_cycle_batch(fiscal_profile=fp, product=product)
            self.stdout.write(json.dumps(report, default=str, indent=2))
        else:
            # Run the full scheduler job (all active profiles × products)
            _run_billing_batch_job()
            self.stdout.write(self.style.SUCCESS('Batch job completed. Check SchedulerJobLog for results.'))

    def _status(self):
        from apps.billing.scheduler import get_scheduler
        from apps.billing.models import SchedulerJobLog

        scheduler = get_scheduler()
        if scheduler and scheduler.running:
            jobs = scheduler.get_jobs()
            self.stdout.write(self.style.SUCCESS(f'Scheduler is RUNNING — {len(jobs)} job(s) registered.'))
            for job in jobs:
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M %Z') if job.next_run_time else 'N/A'
                self.stdout.write(f'  {job.id}: next run {next_run}')
        else:
            self.stdout.write(self.style.WARNING('Scheduler is NOT running.'))

        last_logs = SchedulerJobLog.objects.order_by('-triggered_at')[:10]
        if last_logs.exists():
            self.stdout.write('\nLast 10 job executions:')
            for log in last_logs:
                finished = log.finished_at.strftime('%H:%M:%S') if log.finished_at else 'in-progress'
                self.stdout.write(
                    f'  [{log.triggered_at.strftime("%Y-%m-%d %H:%M")}] status={log.status} finished={finished}'
                )
        else:
            self.stdout.write('No job logs found.')

    def _start(self):
        """Start the scheduler in the foreground — useful for testing scheduler behavior."""
        import time
        from apps.billing.scheduler import start_scheduler, get_scheduler

        start_scheduler()
        self.stdout.write(self.style.SUCCESS('Scheduler started. Press Ctrl+C to stop.'))
        try:
            while True:
                time.sleep(30)
                scheduler = get_scheduler()
                if scheduler:
                    jobs = scheduler.get_jobs()
                    for job in jobs:
                        if job.next_run_time:
                            delta = job.next_run_time - timezone.now()
                            self.stdout.write(
                                f'Next run in {int(delta.total_seconds() / 60)} minutes '
                                f'({job.next_run_time.strftime("%H:%M %Z")})'
                            )
        except KeyboardInterrupt:
            from apps.billing.scheduler import stop_scheduler
            stop_scheduler()
            self.stdout.write(self.style.WARNING('Scheduler stopped.'))
