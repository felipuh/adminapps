"""
Billing scheduler — runs run_billing_cycle_batch daily via APScheduler.

The scheduler is started from BillingConfig.ready() when BILLING_SCHEDULER_ENABLED=True.
Each job execution saves a SchedulerJobLog entry so the frontend can show the last result.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

_scheduler = None
JOB_ID = 'billing_daily_batch'


def _run_billing_batch_job():
    """Job function executed by APScheduler on each scheduled trigger."""
    from apps.billing.models import FiscalProfile, ProductCatalog, SchedulerJobLog
    from apps.billing.services import run_billing_cycle_batch

    started_at = timezone.now()
    log = SchedulerJobLog.objects.create(
        job_id=JOB_ID,
        triggered_at=started_at,
        status='running',
    )

    profiles = FiscalProfile.objects.filter(is_active=True)
    if not profiles.exists():
        log.status = 'skipped'
        log.result_summary = {'reason': 'No active fiscal profiles found.'}
        log.finished_at = timezone.now()
        log.save(update_fields=['status', 'result_summary', 'finished_at'])
        logger.info('[billing_scheduler] No active fiscal profiles — batch skipped.')
        return

    profiles_run = []
    for fp in profiles:
        products = ProductCatalog.objects.filter(is_active=True)
        for product in products:
            try:
                report = run_billing_cycle_batch(fiscal_profile=fp, product=product)
                profiles_run.append({
                    'fiscal_profile': str(fp.id),
                    'product': str(product.id),
                    'processed': report['summary']['processed_count'],
                    'skipped': report['summary']['skipped_count'],
                    'errors': report['summary']['error_count'],
                })
            except Exception as exc:  # noqa: BLE001
                logger.exception('[billing_scheduler] Error running batch for fp=%s product=%s', fp.id, product.id)
                profiles_run.append({
                    'fiscal_profile': str(fp.id),
                    'product': str(product.id),
                    'error': str(exc),
                })

    log.status = 'success'
    log.result_summary = {'runs': profiles_run}
    log.finished_at = timezone.now()
    log.save(update_fields=['status', 'result_summary', 'finished_at'])
    logger.info('[billing_scheduler] Daily batch complete: %d profile/product pairs processed.', len(profiles_run))


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    hour = getattr(settings, 'BILLING_SCHEDULER_HOUR', 6)
    minute = getattr(settings, 'BILLING_SCHEDULER_MINUTE', 0)

    _scheduler = BackgroundScheduler(timezone='America/Costa_Rica')
    _scheduler.add_job(
        _run_billing_batch_job,
        trigger=CronTrigger(hour=hour, minute=minute),
        id=JOB_ID,
        name='Billing Daily Batch',
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
    )
    _scheduler.start()
    logger.info('[billing_scheduler] Scheduler started — cron %02d:%02d CR time.', hour, minute)


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info('[billing_scheduler] Scheduler stopped.')


def get_scheduler():
    return _scheduler
