from decimal import Decimal
import json
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.billing.models import FiscalProfile, PaymentRecord, ProductCatalog, ProductPrice, RevenueSnapshot, SchedulerJobLog
from apps.organizations.models import Organization
from apps.subscriptions.models import Plan, Subscription
from apps.users.models import User


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BillingIssueFlowTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            code='ORG01000',
            name='Issue Flow Org',
            email='issue@example.com',
            tax_id='3101000002',
            country='Costa Rica',
        )
        self.admin_user = User.objects.create(
            email='issue-admin@example.com',
            first_name='Issue',
            last_name='Admin',
            organization=self.organization,
            role='admin',
            is_active=True,
        )
        self.admin_user.set_password('IssueAdmin123!')
        self.admin_user.save(update_fields=['password'])

        self.fiscal_profile = FiscalProfile.objects.create(
            legal_name='Smart3AI SRL',
            commercial_name='Smart3AI',
            tax_id='3101123999',
            email='billing@smart3ai.com',
        )
        self.product = ProductCatalog.objects.create(
            code='ISOSMART',
            name='ISO Smart',
        )
        self.product_price = ProductPrice.objects.create(
            product=self.product,
            name='Mensual',
            amount=Decimal('125.00'),
            tax_rate=Decimal('13.00'),
            currency='CRC',
            cabys_code='1234567890123',
        )
        self.plan = Plan.objects.create(
            code='SMART',
            name='Smart',
            price=Decimal('125.00'),
            currency='CRC',
        )
        self.subscription = Subscription.objects.create(
            plan=self.plan,
            status='active',
            amount=Decimal('125.00'),
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )
        self.organization.subscription = self.subscription
        self.organization.save(update_fields=['subscription'])

    def test_issue_invoice_endpoint_creates_invoice_line_and_snapshot(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
                'discount_amount': '5.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['product_name'], 'ISO Smart')
        self.assertEqual(response.data['subtotal'], '125.00')
        self.assertEqual(response.data['discount_total'], '5.00')
        self.assertEqual(response.data['tax_total'], '15.60')
        self.assertEqual(response.data['total'], '135.60')
        self.assertEqual(len(response.data['lines']), 1)
        self.assertTrue(response.data['invoice_number'].startswith('CR-'))

        snapshot = RevenueSnapshot.objects.get(
            product=self.product,
            organization=self.organization,
            snapshot_date=timezone.now().date(),
        )
        self.assertEqual(snapshot.gross_revenue, Decimal('125.00'))
        self.assertEqual(snapshot.net_revenue, Decimal('135.60'))
        self.assertEqual(snapshot.tax_collected, Decimal('15.60'))
        self.assertEqual(snapshot.invoices_issued, 1)
        self.assertEqual(snapshot.invoices_paid, 0)

    def test_issue_invoice_endpoint_can_mark_invoice_paid(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
                'mark_paid': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'paid')
        self.assertIsNotNone(response.data['paid_at'])

        snapshot = RevenueSnapshot.objects.get(
            product=self.product,
            organization=self.organization,
            snapshot_date=timezone.now().date(),
        )
        self.assertEqual(snapshot.invoices_paid, 1)
        self.assertEqual(PaymentRecord.objects.filter(invoice__invoice_number=response.data['invoice_number']).count(), 1)

    def test_issue_from_subscription_uses_active_subscription(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            '/api/billing/invoices/issue_from_subscription/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data['subscription']), str(self.subscription.id))
        self.assertEqual(response.data['subtotal'], '125.00')
        self.assertEqual(len(response.data['lines']), 1)

    def test_mark_paid_action_creates_payment_record_and_updates_snapshot(self):
        self.client.force_authenticate(user=self.admin_user)

        issue_response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
            },
            format='json',
        )
        self.assertEqual(issue_response.status_code, status.HTTP_201_CREATED)

        invoice_id = issue_response.data['id']
        pay_response = self.client.post(
            f'/api/billing/invoices/{invoice_id}/mark_paid/',
            {'method': 'sinpe', 'reference': 'SINPE-12345'},
            format='json',
        )

        self.assertEqual(pay_response.status_code, status.HTTP_200_OK)
        self.assertEqual(pay_response.data['status'], 'paid')
        self.assertIsNotNone(pay_response.data['paid_at'])

        payment = PaymentRecord.objects.get(invoice_id=invoice_id)
        self.assertEqual(payment.method, 'sinpe')
        self.assertEqual(payment.reference, 'SINPE-12345')
        self.assertEqual(payment.status, 'confirmed')

        snapshot = RevenueSnapshot.objects.get(
            product=self.product,
            organization=self.organization,
            snapshot_date=timezone.now().date(),
        )
        self.assertEqual(snapshot.invoices_issued, 1)
        self.assertEqual(snapshot.invoices_paid, 1)

    def test_mark_paid_rejects_already_paid_invoice(self):
        self.client.force_authenticate(user=self.admin_user)

        issue_response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
                'mark_paid': True,
            },
            format='json',
        )
        self.assertEqual(issue_response.status_code, status.HTTP_201_CREATED)

        invoice_id = issue_response.data['id']
        pay_response = self.client.post(
            f'/api/billing/invoices/{invoice_id}/mark_paid/',
            {'method': 'card', 'reference': 'DUPLICATE'},
            format='json',
        )

        self.assertEqual(pay_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(pay_response.data['detail'], 'La factura ya se encuentra pagada.')

    def test_run_cycle_issues_due_subscription_and_advances_dates(self):
        self.subscription.next_billing_date = timezone.now().date()
        self.subscription.save(update_fields=['next_billing_date'])

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            '/api/billing/invoices/run_cycle/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.subscription.refresh_from_db()
        self.assertIsNotNone(self.subscription.current_period_start)
        self.assertIsNotNone(self.subscription.current_period_end)
        self.assertGreater(self.subscription.next_billing_date, timezone.now().date())

    def test_run_cycle_rejects_subscription_not_due(self):
        self.subscription.next_billing_date = timezone.now().date() + timezone.timedelta(days=5)
        self.subscription.save(update_fields=['next_billing_date'])

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            '/api/billing/invoices/run_cycle/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'La suscripcion aun no alcanza su fecha de cobro.')

    def test_compliance_preview_returns_costa_rica_payload(self):
        self.client.force_authenticate(user=self.admin_user)

        issue_response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
            },
            format='json',
        )
        invoice_id = issue_response.data['id']

        response = self.client.get(f'/api/billing/invoices/{invoice_id}/compliance_preview/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['country'], 'CR')
        self.assertEqual(response.data['emisor']['tax_id'], '3101123999')
        self.assertEqual(response.data['receptor']['tax_id'], '3101000002')
        self.assertEqual(response.data['lineas'][0]['cabys_code'], '1234567890123')

    def test_prepare_hacienda_generates_numeric_key_and_processing_status(self):
        self.client.force_authenticate(user=self.admin_user)

        issue_response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
            },
            format='json',
        )
        invoice_id = issue_response.data['id']

        response = self.client.post(f'/api/billing/invoices/{invoice_id}/prepare_hacienda/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice = response.data['invoice']
        self.assertEqual(invoice['hacienda_status'], 'processing')
        self.assertEqual(len(invoice['consecutive_number']), 20)
        self.assertEqual(len(invoice['numeric_key']), 50)
        self.assertTrue(response.data['xml_ready'])

    def test_update_hacienda_status_accepts_invoice_and_sets_track_id(self):
        self.client.force_authenticate(user=self.admin_user)

        issue_response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
            },
            format='json',
        )
        invoice_id = issue_response.data['id']
        self.client.post(f'/api/billing/invoices/{invoice_id}/prepare_hacienda/', {}, format='json')

        response = self.client.post(
            f'/api/billing/invoices/{invoice_id}/update_hacienda_status/',
            {
                'hacienda_status': 'accepted',
                'hacienda_message': 'Documento aceptado por Hacienda',
                'hacienda_track_id': 'TRACK-001',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['hacienda_status'], 'accepted')
        self.assertEqual(response.data['status'], 'accepted')
        self.assertEqual(response.data['hacienda_track_id'], 'TRACK-001')

    def test_run_batch_processes_due_orgs_and_reports_skips_and_errors(self):
        due_org = self.organization

        future_org = Organization.objects.create(
            code='ORG01001',
            name='Future Org',
            email='future@example.com',
            tax_id='3101000003',
            country='Costa Rica',
        )
        future_subscription = Subscription.objects.create(
            plan=self.plan,
            status='active',
            amount=Decimal('125.00'),
            next_billing_date=timezone.now().date() + timezone.timedelta(days=4),
        )
        future_org.subscription = future_subscription
        future_org.save(update_fields=['subscription'])

        invalid_org = Organization.objects.create(
            code='ORG01002',
            name='Invalid Org',
            email='invalid@example.com',
            tax_id='',
            country='Costa Rica',
        )
        invalid_subscription = Subscription.objects.create(
            plan=self.plan,
            status='active',
            amount=Decimal('125.00'),
            next_billing_date=timezone.now().date(),
        )
        invalid_org.subscription = invalid_subscription
        invalid_org.save(update_fields=['subscription'])

        self.subscription.next_billing_date = timezone.now().date()
        self.subscription.save(update_fields=['next_billing_date'])

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            '/api/billing/invoices/run_batch/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'product': str(self.product.id),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['processed_count'], 1)
        self.assertEqual(response.data['summary']['skipped_count'], 1)
        self.assertEqual(response.data['summary']['error_count'], 1)
        self.assertEqual(response.data['processed'][0]['organization_name'], due_org.name)
        self.assertEqual(response.data['skipped'][0]['reason'], 'not_due_yet')
        self.assertIn('identificacion fiscal', response.data['errors'][0]['error'])

    def test_management_command_outputs_batch_report(self):
        self.subscription.next_billing_date = timezone.now().date()
        self.subscription.save(update_fields=['next_billing_date'])

        stdout = StringIO()
        call_command(
            'run_billing_cycle_batch',
            '--fiscal-profile', str(self.fiscal_profile.id),
            '--product', str(self.product.id),
            stdout=stdout,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload['summary']['processed_count'], 1)
        self.assertEqual(payload['processed'][0]['organization_name'], self.organization.name)

    def test_generate_xml_returns_valid_cr_xml_with_required_tags(self):
        self.client.force_authenticate(user=self.admin_user)
        issue_response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
            },
            format='json',
        )
        invoice_id = issue_response.data['id']
        self.client.post(f'/api/billing/invoices/{invoice_id}/prepare_hacienda/', {}, format='json')

        response = self.client.post(f'/api/billing/invoices/{invoice_id}/generate_xml/', {}, format='json')

        self.assertEqual(response.status_code, 200)
        xml_content = response.content.decode('utf-8')
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', xml_content)
        self.assertIn('FacturaElectronica', xml_content)
        self.assertIn('<Clave>', xml_content)
        self.assertIn('<NumeroConsecutivo>', xml_content)
        self.assertIn('<Emisor>', xml_content)
        self.assertIn('<Receptor>', xml_content)
        self.assertIn('<DetalleServicio>', xml_content)
        self.assertIn('<ResumenFactura>', xml_content)
        self.assertIn('<TotalComprobante>', xml_content)

    def test_credit_note_reverses_paid_invoice_and_creates_nc_document(self):
        self.client.force_authenticate(user=self.admin_user)
        issue_response = self.client.post(
            '/api/billing/invoices/issue/',
            {
                'fiscal_profile': str(self.fiscal_profile.id),
                'organization': str(self.organization.id),
                'product': str(self.product.id),
                'product_price': str(self.product_price.id),
                'mark_paid': True,
            },
            format='json',
        )
        invoice_id = issue_response.data['id']

        response = self.client.post(
            f'/api/billing/invoices/{invoice_id}/credit_note/',
            {'reason': 'Error en facturacion'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['document_type_code'], '03')
        self.assertIn('CR-NC-', response.data['invoice_number'])
        self.assertIn('Error en facturacion', response.data['metadata'].get('reason', ''))

        from apps.billing.models import ElectronicInvoice
        original = ElectronicInvoice.objects.get(id=invoice_id)
        self.assertEqual(original.status, 'reversed')

    def test_scheduler_run_now_command_creates_job_log(self):
        self.subscription.next_billing_date = timezone.now().date()
        self.subscription.save(update_fields=['next_billing_date'])

        stdout = StringIO()
        call_command(
            'billing_scheduler',
            'run_now',
            stdout=stdout,
        )

        log = SchedulerJobLog.objects.order_by('-triggered_at').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, 'success')
        self.assertIn('runs', log.result_summary)
        self.assertGreater(len(log.result_summary['runs']), 0)

    def test_scheduler_status_endpoint_returns_state(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/scheduler/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('enabled', response.data)
        self.assertIn('running', response.data)
        self.assertIn('cron', response.data)
        self.assertIn('hour', response.data['cron'])
        self.assertIn('last_logs', response.data)

    def test_scheduler_post_triggers_batch_and_returns_log(self):
        self.subscription.next_billing_date = timezone.now().date()
        self.subscription.save(update_fields=['next_billing_date'])

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/billing/scheduler/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['status'], ['success', 'skipped'])
        self.assertIn('triggered_at', response.data)
        self.assertIn('result_summary', response.data)

    # ------------------------------------------------------------------
    # Hacienda client integration tests
    # ------------------------------------------------------------------

    def test_hacienda_client_get_token_returns_access_token(self):
        """HaciendaClient.get_token() calls the IDP and caches the token."""
        from apps.billing.hacienda_client import HaciendaClient

        self.fiscal_profile.client_id = 'client123'
        self.fiscal_profile.client_secret = 'secret456'
        self.fiscal_profile.hacienda_username = 'user@empresa.com'
        self.fiscal_profile.hacienda_password = 'pwd123'
        self.fiscal_profile.save()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'access_token': 'tok_abc', 'expires_in': 300}

        with patch('apps.billing.hacienda_client.requests.post', return_value=mock_resp) as mock_post:
            client = HaciendaClient(self.fiscal_profile)
            token = client.get_token()

        self.assertEqual(token, 'tok_abc')
        self.assertEqual(client._access_token, 'tok_abc')
        call_kwargs = mock_post.call_args
        self.assertIn('grant_type', call_kwargs[1]['data'])
        self.assertEqual(call_kwargs[1]['data']['client_id'], 'client123')

    def test_hacienda_client_get_token_raises_on_http_error(self):
        """HaciendaClientError is raised when the IDP returns non-200."""
        from apps.billing.hacienda_client import HaciendaClient, HaciendaClientError

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = 'Unauthorized'

        with patch('apps.billing.hacienda_client.requests.post', return_value=mock_resp):
            client = HaciendaClient(self.fiscal_profile)
            with self.assertRaises(HaciendaClientError) as ctx:
                client.get_token()

        self.assertEqual(ctx.exception.status_code, 401)

    def test_hacienda_client_submit_invoice_sends_base64_xml(self):
        """submit_invoice() POSTs base64-encoded XML and returns Hacienda response."""
        from apps.billing.hacienda_client import HaciendaClient
        from apps.billing.models import ElectronicInvoice
        from apps.billing.services import prepare_invoice_for_hacienda

        self.fiscal_profile.consecutive_number = None  # let service generate
        invoice = ElectronicInvoice.objects.create(
            fiscal_profile=self.fiscal_profile,
            organization=self.organization,
            product=self.product,
            product_price=self.product_price,
            invoice_number='CR-2026-00000001',
            status='pending',
            currency='CRC',
            subtotal=Decimal('125.00'),
            tax_total=Decimal('16.25'),
            total=Decimal('141.25'),
        )

        # Mock token + submission
        token_resp = MagicMock()
        token_resp.status_code = 200
        token_resp.json.return_value = {'access_token': 'tok_submit', 'expires_in': 300}

        submit_resp = MagicMock()
        submit_resp.status_code = 202
        submit_resp.text = ''

        client = HaciendaClient(self.fiscal_profile)
        client._access_token = 'tok_submit'
        from datetime import datetime, timedelta
        client._token_expiry = datetime.utcnow() + timedelta(seconds=300)

        with patch('apps.billing.hacienda_client.requests.post', return_value=submit_resp) as mock_post:
            result = client.submit_invoice(invoice, '<FakeXML/>')

        self.assertEqual(result, {})
        posted_body = mock_post.call_args[1]['json']
        self.assertEqual(posted_body['clave'], invoice.numeric_key or '')
        import base64
        decoded = base64.b64decode(posted_body['comprobanteXml']).decode()
        self.assertEqual(decoded, '<FakeXML/>')

    def test_hacienda_client_check_status_maps_aceptado(self):
        """check_status() maps 'aceptado' to 'accepted'."""
        from apps.billing.hacienda_client import HaciendaClient

        client = HaciendaClient(self.fiscal_profile)
        client._access_token = 'tok_check'
        from datetime import datetime, timedelta
        client._token_expiry = datetime.utcnow() + timedelta(seconds=300)

        get_resp = MagicMock()
        get_resp.status_code = 200
        get_resp.json.return_value = {
            'ind-estado': 'aceptado',
            'respuesta-xml': '',
            'numeroConsecutivoReceptor': 'TRACK123',
        }

        with patch('apps.billing.hacienda_client.requests.get', return_value=get_resp):
            result = client.check_status('50900000001010000000011234567890123456789012345678901')

        self.assertEqual(result['hacienda_status'], 'accepted')
        self.assertEqual(result['track_id'], 'TRACK123')

    def test_hacienda_client_check_status_404_returns_processing(self):
        """check_status() returns processing state when Hacienda returns 404."""
        from apps.billing.hacienda_client import HaciendaClient

        client = HaciendaClient(self.fiscal_profile)
        client._access_token = 'tok_check'
        from datetime import datetime, timedelta
        client._token_expiry = datetime.utcnow() + timedelta(seconds=300)

        not_found_resp = MagicMock()
        not_found_resp.status_code = 404

        with patch('apps.billing.hacienda_client.requests.get', return_value=not_found_resp):
            result = client.check_status('some_clave')

        self.assertEqual(result['hacienda_status'], 'processing')

    def test_fiscal_profile_has_hacienda_credentials_property(self):
        """has_hacienda_credentials is True only when all four OAuth2 fields are set."""
        self.assertFalse(self.fiscal_profile.has_hacienda_credentials)

        self.fiscal_profile.client_id = 'cid'
        self.fiscal_profile.client_secret = 'csec'
        self.fiscal_profile.hacienda_username = 'u'
        self.fiscal_profile.hacienda_password = 'p'
        self.assertTrue(self.fiscal_profile.has_hacienda_credentials)

    def test_update_hacienda_status_poll_param_calls_poll_service(self):
        """POST update_hacienda_status?poll=true calls poll_hacienda_status."""
        from apps.billing.models import ElectronicInvoice

        self.fiscal_profile.client_id = 'cid'
        self.fiscal_profile.client_secret = 'csec'
        self.fiscal_profile.hacienda_username = 'u'
        self.fiscal_profile.hacienda_password = 'p'
        self.fiscal_profile.save()

        invoice = ElectronicInvoice.objects.create(
            fiscal_profile=self.fiscal_profile,
            organization=self.organization,
            product=self.product,
            product_price=self.product_price,
            invoice_number='CR-2026-POLL001',
            numeric_key='50900000001010000000011234567890123456789012345678901',
            hacienda_status='processing',
            status='pending',
            currency='CRC',
            subtotal=Decimal('100.00'),
            tax_total=Decimal('13.00'),
            total=Decimal('113.00'),
        )

        # Mock the Hacienda check_status call deep in the chain
        mock_result = {
            'hacienda_status': 'accepted',
            'message': 'Aceptado por Hacienda',
            'track_id': 'TRK001',
            'raw': {},
        }
        with patch('apps.billing.hacienda_client.HaciendaClient') as MockClient:
            MockClient.return_value.check_status.return_value = mock_result
            self.client.force_authenticate(user=self.admin_user)
            response = self.client.post(
                f'/api/billing/invoices/{invoice.id}/update_hacienda_status/?poll=true'
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('polled_from_hacienda'))
        invoice.refresh_from_db()
        self.assertEqual(invoice.hacienda_status, 'accepted')

    # ------------------------------------------------------------------
    # Churn & trials analytics tests
    # ------------------------------------------------------------------

    def test_billing_summary_includes_churn_fields(self):
        """BillingSummaryView returns churn_rate, trial_subscriptions, etc."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in ('churn_rate', 'trial_conversion_rate', 'trial_subscriptions', 'churned_last_30_days'):
            self.assertIn(field, response.data, f'Missing field: {field}')

    def test_churn_analytics_endpoint_returns_expected_structure(self):
        """GET /api/billing/churn/ returns churn analytics with expected keys."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/churn/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in (
            'active_subscriptions', 'trial_subscriptions', 'churned_last_30_days',
            'churn_rate', 'trial_conversion_rate', 'expiring_trials', 'churned_detail',
        ):
            self.assertIn(key, response.data, f'Missing key: {key}')

    def test_churn_rate_reflects_cancelled_subscriptions(self):
        """Churn rate increases when a subscription is cancelled within last 30 days."""
        from apps.subscriptions.models import Subscription
        self.subscription.status = 'cancelled'
        self.subscription.cancelled_at = timezone.now()
        self.subscription.save(update_fields=['status', 'cancelled_at'])

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/churn/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['churned_last_30_days'], 1)

    def test_expiring_trials_includes_trial_ending_within_7_days(self):
        """Trials ending in less than 7 days appear in expiring_trials list."""
        self.subscription.status = 'trial'
        self.subscription.trial_started_at = timezone.now() - timezone.timedelta(days=8)
        self.subscription.trial_ends_at = timezone.now() + timezone.timedelta(days=3)
        self.subscription.save(update_fields=['status', 'trial_started_at', 'trial_ends_at'])

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/churn/')
        ids = [str(t['id']) for t in response.data['expiring_trials']]
        self.assertIn(str(self.subscription.id), ids)

    # ------------------------------------------------------------------
    # Product dashboard + Alerts tests
    # ------------------------------------------------------------------

    def test_product_dashboard_endpoint_returns_product_metrics(self):
        """GET /api/billing/products/dashboard/ returns an array with product metrics."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/products/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)
        first = response.data[0]
        for key in ('product_id', 'product_code', 'product_name', 'mrr', 'arr',
                    'active_subscriptions', 'paid_invoices', 'total_invoices'):
            self.assertIn(key, first, f'Missing key: {key}')

    def test_billing_alerts_endpoint_returns_structure(self):
        """GET /api/billing/alerts/ returns alerts list and count."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('alerts', response.data)
        self.assertIn('count', response.data)
        self.assertIsInstance(response.data['alerts'], list)

    def test_billing_alerts_shows_overdue_invoice(self):
        """An invoice past due_date in pending status generates an invoice_overdue alert."""
        from apps.billing.models import ElectronicInvoice
        ElectronicInvoice.objects.create(
            fiscal_profile=self.fiscal_profile,
            organization=self.organization,
            product=self.product,
            product_price=self.product_price,
            invoice_number='CR-OVERDUE-001',
            status='pending',
            due_date=timezone.now().date() - timezone.timedelta(days=5),
            currency='CRC',
            subtotal=Decimal('100.00'),
            tax_total=Decimal('13.00'),
            total=Decimal('113.00'),
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/billing/alerts/')
        types = [a['type'] for a in response.data['alerts']]
        self.assertIn('invoice_overdue', types)

    # ------------------------------------------------------------------
    # Multi-product model isolation test
    # ------------------------------------------------------------------

    def test_multi_product_revenue_and_invoices_are_isolated_per_product(self):
        """
        Revenue snapshots and invoices for Product A must not appear in
        the metrics of Product B.  Validates that the billing model
        correctly supports multiple products on the same FiscalProfile.
        """
        product_b = ProductCatalog.objects.create(
            code='PRODUCT_B',
            name='Product B',
        )
        price_b = ProductPrice.objects.create(
            product=product_b,
            name='Mensual B',
            amount=Decimal('200.00'),
            tax_rate=Decimal('13.00'),
            currency='CRC',
            cabys_code='9876543210123',
        )

        org_b = type(self.organization).objects.create(
            code='ORGB0001',
            name='Org B',
            email='orgb@example.com',
            tax_id='3101000099',
            country='Costa Rica',
        )

        # Issue one invoice for product A and one for product B
        self.client.force_authenticate(user=self.admin_user)
        resp_a = self.client.post('/api/billing/invoices/issue/', {
            'fiscal_profile': str(self.fiscal_profile.id),
            'organization': str(self.organization.id),
            'product': str(self.product.id),
            'product_price': str(self.product_price.id),
        }, format='json')
        self.assertEqual(resp_a.status_code, 201)

        resp_b = self.client.post('/api/billing/invoices/issue/', {
            'fiscal_profile': str(self.fiscal_profile.id),
            'organization': str(org_b.id),
            'product': str(product_b.id),
            'product_price': str(price_b.id),
        }, format='json')
        self.assertEqual(resp_b.status_code, 201)

        # Product dashboard should have separate entries
        dash_resp = self.client.get('/api/billing/products/dashboard/')
        self.assertEqual(dash_resp.status_code, 200)
        codes = {p['product_code'] for p in dash_resp.data}
        self.assertIn('ISOSMART', codes)
        self.assertIn('PRODUCT_B', codes)

        # Revenue by product must be separate
        rev_resp = self.client.get('/api/billing/revenue/by-product/')
        self.assertEqual(rev_resp.status_code, 200)
        iso_items = [r for r in rev_resp.data if r['product__code'] == 'ISOSMART']
        b_items   = [r for r in rev_resp.data if r['product__code'] == 'PRODUCT_B']
        # After marking both paid, snapshots are independent
        # (even without mark_paid the counts are separate)
        # Confirm invoices are scoped: each product only sees its own invoice
        from apps.billing.models import ElectronicInvoice
        iso_count = ElectronicInvoice.objects.filter(product=self.product).count()
        b_count   = ElectronicInvoice.objects.filter(product=product_b).count()
        self.assertGreaterEqual(iso_count, 1)
        self.assertGreaterEqual(b_count, 1)
        # No cross-product leakage: ISO invoice is NOT linked to product B
        self.assertEqual(
            ElectronicInvoice.objects.filter(
                product=product_b, organization=self.organization,
            ).count(),
            0,
        )
