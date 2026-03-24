import json

from django.core.management.base import BaseCommand, CommandError

from apps.billing.models import FiscalProfile, ProductCatalog, ProductPrice
from apps.billing.services import run_billing_cycle_batch


class Command(BaseCommand):
    help = 'Run billing cycles in batch for due organizations.'

    def add_arguments(self, parser):
        parser.add_argument('--fiscal-profile', required=True, help='FiscalProfile UUID')
        parser.add_argument('--product', required=True, help='ProductCatalog UUID')
        parser.add_argument('--product-price', help='Optional ProductPrice UUID')
        parser.add_argument('--organization-id', action='append', dest='organization_ids', help='Optional organization UUID; repeatable')
        parser.add_argument('--mark-paid', action='store_true', help='Mark generated invoices as paid')

    def handle(self, *args, **options):
        try:
            fiscal_profile = FiscalProfile.objects.get(pk=options['fiscal_profile'])
        except FiscalProfile.DoesNotExist as exc:
            raise CommandError('Fiscal profile not found.') from exc

        try:
            product = ProductCatalog.objects.get(pk=options['product'])
        except ProductCatalog.DoesNotExist as exc:
            raise CommandError('Product not found.') from exc

        product_price = None
        if options.get('product_price'):
            try:
                product_price = ProductPrice.objects.get(pk=options['product_price'])
            except ProductPrice.DoesNotExist as exc:
                raise CommandError('Product price not found.') from exc

        report = run_billing_cycle_batch(
            fiscal_profile=fiscal_profile,
            product=product,
            product_price=product_price,
            organization_ids=options.get('organization_ids') or None,
            mark_paid=options['mark_paid'],
        )
        self.stdout.write(json.dumps(report, indent=2, ensure_ascii=True))
