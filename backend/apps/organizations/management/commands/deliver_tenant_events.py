"""At-least-once delivery of durable tenant facts to ISO Smart."""

import json
import os
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.organizations.models import TenantIntegrationOutbox


class Command(BaseCommand):
    help = 'Deliver pending AdminApps tenant events to the authenticated ISO Smart ingress.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        endpoint = os.environ.get('ISO_SMART_TENANT_EVENT_URL', '')
        key = os.environ.get('ISO_SMART_TENANT_EVENT_KEY', '')
        parsed = urlparse(endpoint)
        loopback_http = (
            os.environ.get('ISO_SMART_TENANT_EVENT_ALLOW_LOOPBACK_HTTP') == 'true'
            and parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost'}
        )
        if (parsed.scheme != 'https' and not loopback_http) or not parsed.netloc or not key:
            raise CommandError('HTTPS endpoint and ISO_SMART_TENANT_EVENT_KEY are required')
        for _ in range(options['limit']):
            with transaction.atomic():
                earlier = (TenantIntegrationOutbox.objects
                           .filter(organization_id=OuterRef('organization_id'),
                                   source_version__lt=OuterRef('source_version'))
                           .exclude(status='delivered'))
                row = (TenantIntegrationOutbox.objects.select_for_update(skip_locked=True)
                       .filter(Q(status__in=['pending', 'failed'], available_at__lte=timezone.now()) |
                               Q(status='processing', available_at__lte=timezone.now()))
                       .annotate(blocked=Exists(earlier)).filter(blocked=False)
                       .order_by('created_at').first())
                if row is None:
                    break
                row.status = 'processing'
                row.attempts += 1
                row.available_at = timezone.now() + timedelta(minutes=5)
                row.save(update_fields=['status', 'attempts', 'available_at'])
            request = Request(endpoint, data=json.dumps(row.envelope).encode('utf-8'), method='POST',
                              headers={'Content-Type': 'application/json', 'X-API-Key': key})
            try:
                with urlopen(request, timeout=15) as response:
                    if response.status not in (200, 201):
                        raise RuntimeError(f'HTTP {response.status}')
            except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
                row.status = 'failed'
                row.last_error = type(exc).__name__[:100]
                row.available_at = timezone.now() + timedelta(minutes=min(60, 2 ** min(row.attempts, 6)))
                row.save(update_fields=['status', 'last_error', 'available_at'])
                self.stderr.write(f'Failed event {row.id}: {row.last_error}')
            else:
                row.status = 'delivered'
                row.delivered_at = timezone.now()
                row.last_error = ''
                row.save(update_fields=['status', 'delivered_at', 'last_error'])
                self.stdout.write(f'Delivered event {row.id}')
