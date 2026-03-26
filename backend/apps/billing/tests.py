from decimal import Decimal

from django.test import override_settings
from django.utils import timezone
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from apps.billing.models import (
    ElectronicInvoice,
    FiscalProfile,
    InvoiceLine,
    ProductCatalog,
    ProductPrice,
    RecurringReportSchedule,
    RevenueSnapshot,
)
from apps.organizations.models import Organization
from apps.subscriptions.models import Plan, Subscription
from apps.users.models import User, UserActivityLog


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BillingModelAndApiTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            code='ORG00999',
            name='Finance Org',
            email='finance@example.com',
            tax_id='3101000001',
            country='Costa Rica',
        )
        self.admin_user = User.objects.create(
            email='admin-billing@example.com',
            first_name='Billing',
            last_name='Admin',
            organization=self.organization,
            role='admin',
            is_active=True,
        )
        self.admin_user.set_password('AdminBilling123!')
        self.admin_user.save(update_fields=['password'])

        self.fiscal_profile = FiscalProfile.objects.create(
            legal_name='Smart3AI SRL',
            commercial_name='Smart3AI',
            tax_id='3101123456',
            email='billing@smart3ai.com',
        )
        self.product = ProductCatalog.objects.create(
            code='ISOSMART',
            name='ISO Smart',
            billing_model='subscription',
        )
        self.product_price = ProductPrice.objects.create(
            product=self.product,
            name='Plan Base',
            amount=Decimal('100.00'),
            tax_rate=Decimal('13.00'),
            currency='CRC',
            cabys_code='0000000000000',
        )
        self.plan = Plan.objects.create(
            code='BASE',
            name='Base',
            price=Decimal('100.00'),
        )
        self.subscription = Subscription.objects.create(
            plan=self.plan,
            status='active',
            amount=Decimal('100.00'),
        )
        self.invoice = ElectronicInvoice.objects.create(
            fiscal_profile=self.fiscal_profile,
            organization=self.organization,
            subscription=self.subscription,
            product=self.product,
            product_price=self.product_price,
            invoice_number='FE-000001',
            status='paid',
            issued_at=timezone.now(),
        )

    def test_invoice_line_calculates_totals(self):
        line = InvoiceLine.objects.create(
            invoice=self.invoice,
            description='ISO Smart mensualidad',
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('10.00'),
            tax_rate=Decimal('13.00'),
        )

        self.assertEqual(line.subtotal, Decimal('100.00'))
        self.assertEqual(line.tax_amount, Decimal('11.70'))
        self.assertEqual(line.total, Decimal('101.70'))

    def test_invoice_recalculate_totals_updates_invoice_amounts(self):
        InvoiceLine.objects.create(
            invoice=self.invoice,
            description='ISO Smart mensualidad',
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('10.00'),
            tax_rate=Decimal('13.00'),
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            description='Servicio complementario',
            quantity=Decimal('1.00'),
            unit_price=Decimal('50.00'),
            discount_amount=Decimal('0.00'),
            tax_rate=Decimal('13.00'),
        )

        self.invoice.recalculate_totals()
        self.invoice.save(update_fields=['subtotal', 'tax_total', 'discount_total', 'total'])
        self.invoice.refresh_from_db()

        self.assertEqual(self.invoice.subtotal, Decimal('150.00'))
        self.assertEqual(self.invoice.discount_total, Decimal('10.00'))
        self.assertEqual(self.invoice.tax_total, Decimal('18.20'))
        self.assertEqual(self.invoice.total, Decimal('158.20'))

    def test_billing_summary_endpoint_returns_platform_totals(self):
        RevenueSnapshot.objects.create(
            snapshot_date=timezone.now().date(),
            product=self.product,
            organization=self.organization,
            gross_revenue=Decimal('150.00'),
            net_revenue=Decimal('158.20'),
            tax_collected=Decimal('18.20'),
            invoices_issued=1,
            invoices_paid=1,
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            description='ISO Smart mensualidad',
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('0.00'),
            tax_rate=Decimal('13.00'),
        )
        self.invoice.recalculate_totals()
        self.invoice.save(update_fields=['subtotal', 'tax_total', 'discount_total', 'total'])

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/summary/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_products'], 1)
        self.assertEqual(response.data['paid_invoices'], 1)
        self.assertEqual(Decimal(response.data['accounts_receivable']), Decimal('0.00'))
        self.assertEqual(Decimal(response.data['gross_revenue']), Decimal('100.00'))
        self.assertEqual(Decimal(response.data['net_revenue']), Decimal('113.00'))
        self.assertEqual(Decimal(response.data['tax_collected']), Decimal('13.00'))

    def test_revenue_by_product_endpoint_aggregates_snapshots(self):
        RevenueSnapshot.objects.create(
            snapshot_date=timezone.now().date(),
            product=self.product,
            organization=self.organization,
            gross_revenue=Decimal('100.00'),
            net_revenue=Decimal('113.00'),
            tax_collected=Decimal('13.00'),
            invoices_issued=1,
            invoices_paid=1,
        )
        RevenueSnapshot.objects.create(
            snapshot_date=timezone.now().date(),
            product=self.product,
            organization=None,
            gross_revenue=Decimal('200.00'),
            net_revenue=Decimal('226.00'),
            tax_collected=Decimal('26.00'),
            invoices_issued=2,
            invoices_paid=2,
            currency='CRC',
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/revenue/by-product/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product__code'], 'ISOSMART')
        self.assertEqual(Decimal(response.data[0]['gross_revenue']), Decimal('300.00'))
        self.assertEqual(Decimal(response.data[0]['net_revenue']), Decimal('339.00'))
        self.assertEqual(Decimal(response.data[0]['tax_collected']), Decimal('39.00'))
        self.assertEqual(response.data[0]['invoices_paid'], 3)

    def test_revenue_by_organization_endpoint_aggregates_snapshots(self):
        RevenueSnapshot.objects.create(
            snapshot_date=timezone.now().date(),
            product=self.product,
            organization=self.organization,
            gross_revenue=Decimal('100.00'),
            net_revenue=Decimal('113.00'),
            tax_collected=Decimal('13.00'),
            invoices_issued=1,
            invoices_paid=1,
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/revenue/by-organization/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['organization__name'], 'Finance Org')
        self.assertEqual(Decimal(response.data[0]['net_revenue']), Decimal('113.00'))

    @override_settings(BILLING_OWNER_ORG_EXEMPT_ENABLED=True, BILLING_OWNER_ORG_NAME='Smart3AI')
    def test_run_billing_cycle_batch_skips_owner_org(self):
        from apps.billing.services import run_billing_cycle_batch

        owner_org = Organization.objects.create(
            code='ORG88888',
            name='Smart3AI',
            email='owner@smart3ai.com',
            tax_id='3101000002',
            country='Costa Rica',
            subscription=self.subscription,
        )
        self.subscription.next_billing_date = timezone.localdate() - timezone.timedelta(days=1)
        self.subscription.save(update_fields=['next_billing_date'])

        report = run_billing_cycle_batch(
            fiscal_profile=self.fiscal_profile,
            product=self.product,
            product_price=self.product_price,
            organization_ids=[owner_org.id],
            issued_by=self.admin_user,
        )

        self.assertEqual(report['summary']['processed_count'], 0)
        self.assertEqual(report['summary']['error_count'], 0)
        self.assertEqual(report['summary']['skipped_count'], 1)
        self.assertEqual(report['skipped'][0]['reason'], 'owner_billing_exempt')
        self.assertFalse(ElectronicInvoice.objects.filter(organization=owner_org).exists())

    def test_revenue_timeline_and_accounts_receivable_endpoints(self):
        self.invoice.status = 'pending'
        self.invoice.due_date = timezone.now().date() - timezone.timedelta(days=10)
        self.invoice.subtotal = Decimal('100.00')
        self.invoice.tax_total = Decimal('13.00')
        self.invoice.total = Decimal('113.00')
        self.invoice.save(update_fields=['status', 'due_date', 'subtotal', 'tax_total', 'total'])

        RevenueSnapshot.objects.create(
            snapshot_date=timezone.now().date(),
            product=self.product,
            organization=self.organization,
            gross_revenue=Decimal('100.00'),
            net_revenue=Decimal('113.00'),
            tax_collected=Decimal('13.00'),
            invoices_issued=1,
            invoices_paid=0,
        )

        self.client.force_authenticate(user=self.admin_user)

        timeline_response = self.client.get('/api/billing/revenue/timeline/', format='json')
        self.assertEqual(timeline_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(timeline_response.data), 1)
        self.assertEqual(Decimal(timeline_response.data[0]['net_revenue']), Decimal('113.00'))

        receivable_response = self.client.get('/api/billing/accounts-receivable/', format='json')
        self.assertEqual(receivable_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(receivable_response.data['overdue_1_30']), Decimal('113.00'))

    # ------------------------------------------------------------------
    # Bank reconciliation tests
    # ------------------------------------------------------------------

    def _pending_invoice(self, total='100.00'):
        inv = ElectronicInvoice.objects.create(
            fiscal_profile=self.fiscal_profile,
            organization=self.organization,
            product=self.product,
            product_price=self.product_price,
            invoice_number=f'CR-REC-{ElectronicInvoice.objects.count():04d}',
            status='pending',
            currency='CRC',
            subtotal=Decimal(total),
            tax_total=Decimal('0.00'),
            total=Decimal(total),
        )
        return inv

    def test_register_pending_payment_creates_record_without_marking_invoice_paid(self):
        from apps.billing.services import register_pending_payment
        invoice = self._pending_invoice('200.00')

        payment = register_pending_payment(
            invoice=invoice,
            method='sinpe',
            reference='SINPE-001',
            amount=Decimal('200.00'),
            notes='Transferencia reportada por cliente',
        )

        self.assertEqual(payment.status, 'pending')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'pending')

    def test_confirm_payment_record_marks_invoice_paid(self):
        from apps.billing.services import register_pending_payment, confirm_payment_record
        invoice = self._pending_invoice('150.00')

        payment = register_pending_payment(
            invoice=invoice, method='bank_transfer', reference='TRF-002',
            amount=Decimal('150.00'),
        )
        invoice_after, payment_after, _ = confirm_payment_record(payment=payment, notes='Confirmado por banco')

        self.assertEqual(payment_after.status, 'confirmed')
        self.assertIn('Confirmado', payment_after.notes)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')

    def test_confirm_payment_non_pending_raises(self):
        from apps.billing.services import register_pending_payment, confirm_payment_record
        invoice = self._pending_invoice('120.00')
        payment = register_pending_payment(invoice=invoice, method='cash', amount=Decimal('120.00'))
        payment.status = 'confirmed'
        payment.save(update_fields=['status'])

        with self.assertRaises(ValueError):
            confirm_payment_record(payment=payment)

    def test_reject_payment_record_marks_failed(self):
        from apps.billing.services import register_pending_payment, reject_payment_record
        invoice = self._pending_invoice('80.00')
        payment = register_pending_payment(invoice=invoice, method='sinpe', amount=Decimal('80.00'))

        payment_after = reject_payment_record(payment=payment, notes='Rechazado por banco')
        self.assertEqual(payment_after.status, 'failed')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'pending')  # invoice unchanged

    def test_reconciliation_summary_endpoint(self):
        from apps.billing.services import register_pending_payment
        invoice = self._pending_invoice('300.00')
        register_pending_payment(invoice=invoice, method='sinpe', amount=Decimal('300.00'))

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/reconciliation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pending_payments', response.data)
        self.assertGreaterEqual(response.data['pending_payments'], 1)
        self.assertIn('confirmed_payments', response.data)
        self.assertIn('overdue_invoices', response.data)
        self.assertIn('unmatched_invoices', response.data)

    def test_payment_confirm_action_via_api(self):
        from apps.billing.services import register_pending_payment
        from apps.billing.models import PaymentRecord
        invoice = self._pending_invoice('175.00')
        payment = register_pending_payment(invoice=invoice, method='bank_transfer', amount=Decimal('175.00'))

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            f'/api/billing/payments/{payment.id}/confirm/',
            {'notes': 'OK'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'confirmed')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        self.assertTrue(
            UserActivityLog.objects.filter(
                module='notifications',
                organization=self.organization,
                new_values__event='payment_confirmed',
            ).exists()
        )

    def test_payment_reject_action_via_api(self):
        from apps.billing.services import register_pending_payment
        invoice = self._pending_invoice('90.00')
        payment = register_pending_payment(invoice=invoice, method='sinpe', amount=Decimal('90.00'))

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            f'/api/billing/payments/{payment.id}/reject/',
            {'notes': 'Fondos insuficientes'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'failed')
        self.assertTrue(
            UserActivityLog.objects.filter(
                module='notifications',
                organization=self.organization,
                new_values__event='payment_rejected',
            ).exists()
        )

    def test_register_pending_action_via_api_creates_notification(self):
        invoice = self._pending_invoice('140.00')

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            '/api/billing/payments/register_pending/',
            {
                'invoice': str(invoice.id),
                'method': 'sinpe',
                'reference': 'SINPE-API-140',
                'amount': '140.00',
                'notes': 'Pendiente de verificacion',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserActivityLog.objects.filter(
                module='notifications',
                organization=self.organization,
                new_values__event='payment_pending_registered',
            ).exists()
        )

    def test_create_recurring_report_schedule_sets_next_run(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            '/api/billing/reports/schedules/',
            {
                'name': 'Reporte Diario Billing',
                'report_type': 'billing_summary',
                'frequency': 'daily',
                'hour': 8,
                'minute': 30,
                'recipients': ['finance@example.com'],
                'is_active': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schedule = RecurringReportSchedule.objects.get(id=response.data['id'])
        self.assertIsNotNone(schedule.next_run_at)

    def test_run_now_recurring_report_schedule_sends_email(self):
        schedule = RecurringReportSchedule.objects.create(
            name='Cobranza Semanal',
            report_type='collections_snapshot',
            frequency='weekly',
            day_of_week=0,
            hour=9,
            minute=0,
            recipients=['finance@example.com'],
            is_active=True,
            next_run_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/billing/reports/schedules/{schedule.id}/run_now/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Cobranza Semanal', mail.outbox[0].subject)
        self.assertIn('Reporte:', mail.outbox[0].body)
        self.assertTrue(mail.outbox[0].alternatives)
        self.assertEqual(mail.outbox[0].alternatives[0][1], 'text/html')
        self.assertIn('<html>', mail.outbox[0].alternatives[0][0])

    def test_run_due_recurring_reports_processes_due_schedules(self):
        RecurringReportSchedule.objects.create(
            name='Reporte Due',
            report_type='billing_summary',
            frequency='daily',
            hour=7,
            minute=0,
            recipients=['ops@example.com'],
            is_active=True,
            next_run_at=timezone.now() - timezone.timedelta(minutes=1),
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/billing/reports/schedules/run_due/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['processed'], 1)
        self.assertEqual(len(mail.outbox), 1)
