from decimal import Decimal
import csv
import io
from datetime import date

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.users.permissions import IsAdmin, IsSuperAdmin
from apps.users.models import UserActivityLog
from .models import (
    ElectronicInvoice,
    FiscalProfile,
    PaymentRecord,
    ProductCatalog,
    ProductPrice,
    RecurringReportSchedule,
    RevenueSnapshot,
    SchedulerJobLog,
)
from .services import issue_invoice_for_organization, record_invoice_payment, run_billing_cycle_batch, run_subscription_billing_cycle
from .services import prepare_invoice_for_hacienda, update_hacienda_status, poll_hacienda_status, generate_invoice_xml, create_credit_note_for_invoice
from .services import register_pending_payment, confirm_payment_record, reject_payment_record, get_reconciliation_summary
from .services import execute_recurring_report_schedule, process_due_recurring_reports
from .serializers import (
    AccountsReceivableSerializer,
    BatchBillingReportSerializer,
    BillingSummarySerializer,
    CreatePendingPaymentSerializer,
    CreditNoteSerializer,
    ElectronicInvoiceDetailSerializer,
    ElectronicInvoiceListSerializer,
    FiscalProfileSerializer,
    HaciendaStatusUpdateSerializer,
    IssueInvoiceSerializer,
    IssueSubscriptionInvoiceSerializer,
    PaymentRecordSerializer,
    ProductCatalogSerializer,
    ProductPriceSerializer,
    ReconciliationSummarySerializer,
    RecordPaymentSerializer,
    RevenueByOrganizationSerializer,
    RevenueByProductSerializer,
    RevenueTimelineSerializer,
    RevenueSnapshotSerializer,
    RecurringReportScheduleSerializer,
    RunBatchBillingCycleSerializer,
    RunSubscriptionBillingCycleSerializer,
)


def _create_notification_event(*, user, organization, action, description, severity='low', module='billing', payload=None):
    """Persist an in-app notification event via shared activity log infrastructure."""
    UserActivityLog.objects.create(
        user=user,
        organization=organization,
        action=action,
        module='notifications',
        entity_type='BillingEvent',
        entity_id=str(getattr(organization, 'id', '') or ''),
        description=description,
        new_values={
            'severity': severity,
            'source_module': module,
            **(payload or {}),
        },
    )


class BillingSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from apps.subscriptions.models import Subscription
        from datetime import timedelta as _td

        paid_invoices = ElectronicInvoice.objects.filter(status='paid')
        receivable_invoices = ElectronicInvoice.objects.filter(status__in=['pending', 'accepted'])

        # MRR: sum of active subscriptions' monthly-equivalent amounts
        active_subs = Subscription.objects.filter(status='active').select_related('plan')
        mrr = Decimal('0.00')
        for sub in active_subs:
            cycle = getattr(sub.plan, 'billing_cycle', 'monthly')
            amount = sub.amount or Decimal('0.00')
            if cycle == 'yearly':
                mrr += amount / 12
            elif cycle == 'quarterly':
                mrr += amount / 3
            else:
                mrr += amount
        arr = mrr * 12

        # Churn metrics
        now = timezone.now()
        cutoff_30 = now - _td(days=30)
        active_count = active_subs.count()
        churned_30 = Subscription.objects.filter(status='cancelled', cancelled_at__gte=cutoff_30).count()
        denom = active_count + churned_30
        churn_rate = round(float(churned_30 / denom * 100), 2) if denom > 0 else 0.0

        started_trial = Subscription.objects.filter(trial_started_at__isnull=False).count()
        converted_trial = Subscription.objects.filter(status='active', trial_started_at__isnull=False).count()
        trial_conversion_rate = round(float(converted_trial / started_trial * 100), 2) if started_trial > 0 else 0.0

        summary = {
            'total_products': ProductCatalog.objects.count(),
            'active_products': ProductCatalog.objects.filter(is_active=True).count(),
            'total_invoices': ElectronicInvoice.objects.count(),
            'accepted_invoices': ElectronicInvoice.objects.filter(status='accepted').count(),
            'paid_invoices': paid_invoices.count(),
            'pending_invoices': ElectronicInvoice.objects.filter(status__in=['draft', 'pending']).count(),
            'gross_revenue': paid_invoices.aggregate(value=Sum('subtotal'))['value'] or Decimal('0.00'),
            'net_revenue': paid_invoices.aggregate(value=Sum('total'))['value'] or Decimal('0.00'),
            'tax_collected': paid_invoices.aggregate(value=Sum('tax_total'))['value'] or Decimal('0.00'),
            'accounts_receivable': receivable_invoices.aggregate(value=Sum('total'))['value'] or Decimal('0.00'),
            'mrr': mrr,
            'arr': arr,
            'active_subscriptions': active_count,
            'trial_subscriptions': Subscription.objects.filter(status='trial').count(),
            'churned_last_30_days': churned_30,
            'churn_rate': churn_rate,
            'trial_conversion_rate': trial_conversion_rate,
        }
        return Response(BillingSummarySerializer(summary).data)


class RevenueByProductView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = (
            RevenueSnapshot.objects.values('product__code', 'product__name')
            .annotate(
                gross_revenue=Sum('gross_revenue'),
                net_revenue=Sum('net_revenue'),
                tax_collected=Sum('tax_collected'),
                invoices_paid=Sum('invoices_paid'),
            )
            .order_by('product__name')
        )
        return Response(RevenueByProductSerializer(queryset, many=True).data)


class RevenueByOrganizationView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = (
            RevenueSnapshot.objects.filter(organization__isnull=False)
            .values('organization__id', 'organization__name')
            .annotate(
                gross_revenue=Sum('gross_revenue'),
                net_revenue=Sum('net_revenue'),
                tax_collected=Sum('tax_collected'),
                invoices_issued=Sum('invoices_issued'),
                invoices_paid=Sum('invoices_paid'),
            )
            .order_by('organization__name')
        )
        return Response(RevenueByOrganizationSerializer(queryset, many=True).data)


class RevenueTimelineView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = (
            RevenueSnapshot.objects.annotate(period_date=TruncMonth('snapshot_date'))
            .values('period_date')
            .annotate(
                gross_revenue=Sum('gross_revenue'),
                net_revenue=Sum('net_revenue'),
                tax_collected=Sum('tax_collected'),
                invoices_issued=Sum('invoices_issued'),
                invoices_paid=Sum('invoices_paid'),
            )
            .order_by('period_date')
        )
        payload = [
            {
                'period': item['period_date'].strftime('%Y-%m') if item['period_date'] else '',
                'gross_revenue': item['gross_revenue'],
                'net_revenue': item['net_revenue'],
                'tax_collected': item['tax_collected'],
                'invoices_issued': item['invoices_issued'],
                'invoices_paid': item['invoices_paid'],
            }
            for item in queryset
        ]
        return Response(RevenueTimelineSerializer(payload, many=True).data)


class AccountsReceivableView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        queryset = ElectronicInvoice.objects.filter(status__in=['pending', 'accepted'])

        def total_for(days_min=None, days_max=None, current=False):
            items = queryset
            if current:
                items = items.filter(due_date__gte=today)
            else:
                if days_min is not None:
                    items = items.filter(due_date__lt=today - timezone.timedelta(days=days_min - 1))
                if days_max is not None:
                    items = items.filter(due_date__gte=today - timezone.timedelta(days=days_max))
            return items.aggregate(value=Sum('total'))['value'] or Decimal('0.00')

        data = {
            'current': total_for(current=True),
            'overdue_1_30': total_for(days_min=1, days_max=30),
            'overdue_31_60': total_for(days_min=31, days_max=60),
            'overdue_61_plus': queryset.filter(due_date__lt=today - timezone.timedelta(days=60)).aggregate(value=Sum('total'))['value'] or Decimal('0.00'),
        }
        return Response(AccountsReceivableSerializer(data).data)


class FiscalProfileViewSet(viewsets.ModelViewSet):
    queryset = FiscalProfile.objects.all()
    serializer_class = FiscalProfileSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    filter_backends = [filters.OrderingFilter]
    ordering = ['legal_name']


class ProductCatalogViewSet(viewsets.ModelViewSet):
    queryset = ProductCatalog.objects.all()
    serializer_class = ProductCatalogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'billing_model']
    search_fields = ['code', 'name']
    ordering = ['name']


class ProductPriceViewSet(viewsets.ModelViewSet):
    queryset = ProductPrice.objects.select_related('product')
    serializer_class = ProductPriceSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'currency', 'billing_cycle', 'is_active']
    ordering = ['product__name', 'amount']


class ElectronicInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ElectronicInvoice.objects.select_related(
        'organization', 'product', 'product_price', 'subscription', 'fiscal_profile'
    ).prefetch_related('lines')
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'product', 'organization', 'currency']
    search_fields = ['invoice_number', 'organization__name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ElectronicInvoiceListSerializer
        return ElectronicInvoiceDetailSerializer

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export invoices as a CSV file for the accountant."""
        qs = self.filter_queryset(self.get_queryset())

        # Optional date range filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(issued_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(issued_at__date__lte=date_to)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            'Número Factura', 'Tipo Documento', 'Fecha Emisión', 'Fecha Vence',
            'Organización', 'RUC/Cedula', 'Email Receptor',
            'Producto', 'Moneda', 'Subtotal', 'Descuento', 'Impuesto', 'Total',
            'Estado', 'Estado Hacienda', 'Clave Numérica', 'Número Consecutivo',
        ])

        for inv in qs.order_by('-issued_at'):
            writer.writerow([
                inv.invoice_number,
                inv.get_document_type_code_display() if hasattr(inv, 'get_document_type_code_display') else inv.document_type_code,
                inv.issued_at.strftime('%Y-%m-%d %H:%M:%S') if inv.issued_at else '',
                str(inv.due_date) if inv.due_date else '',
                inv.organization.name if inv.organization else '',
                inv.receiver_tax_id or '',
                inv.receiver_email or '',
                inv.product.name if inv.product else '',
                inv.currency,
                str(inv.subtotal),
                str(inv.discount_total),
                str(inv.tax_total),
                str(inv.total),
                inv.status,
                inv.hacienda_status,
                inv.numeric_key or '',
                inv.consecutive_number or '',
            ])

        filename = f'facturas_{date.today().isoformat()}.csv'
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        invoice = self.get_object()
        invoice.recalculate_totals()
        invoice.save(update_fields=['subtotal', 'tax_total', 'discount_total', 'total'])
        return Response(ElectronicInvoiceDetailSerializer(invoice).data)

    @action(detail=False, methods=['post'])
    def issue(self, request):
        serializer = IssueInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice, _, _, _ = issue_invoice_for_organization(
            fiscal_profile=serializer.validated_data['fiscal_profile'],
            organization=serializer.validated_data['organization'],
            subscription=serializer.validated_data.get('subscription'),
            product=serializer.validated_data['product'],
            product_price=serializer.validated_data['product_price'],
            issued_by=request.user,
            quantity=serializer.validated_data['quantity'],
            discount_amount=serializer.validated_data['discount_amount'],
            due_date=serializer.validated_data.get('due_date'),
            mark_paid=serializer.validated_data['mark_paid'],
        )

        response_serializer = ElectronicInvoiceDetailSerializer(invoice)
        _create_notification_event(
            user=request.user,
            organization=invoice.organization,
            action='create',
            description=f'Factura emitida: {invoice.invoice_number} ({invoice.organization.name})',
            severity='medium',
            module='billing',
            payload={'event': 'invoice_issued', 'invoice_id': str(invoice.id)},
        )
        return Response(response_serializer.data, status=201)

    @action(detail=False, methods=['post'])
    def issue_from_subscription(self, request):
        serializer = IssueSubscriptionInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invoice, _, _, _ = issue_invoice_for_organization(
                fiscal_profile=serializer.validated_data['fiscal_profile'],
                organization=serializer.validated_data['organization'],
                subscription=serializer.validated_data['subscription'],
                product=serializer.validated_data['product'],
                product_price=serializer.validated_data.get('product_price'),
                issued_by=request.user,
                quantity=serializer.validated_data['quantity'],
                discount_amount=serializer.validated_data['discount_amount'],
                due_date=serializer.validated_data.get('due_date'),
                mark_paid=serializer.validated_data['mark_paid'],
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        return Response(ElectronicInvoiceDetailSerializer(invoice).data, status=201)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        invoice = self.get_object()
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invoice, _, _ = record_invoice_payment(
                invoice=invoice,
                method=serializer.validated_data['method'],
                reference=serializer.validated_data.get('reference', ''),
                paid_at=serializer.validated_data.get('paid_at'),
                metadata={'source': 'billing.invoice.mark_paid'},
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        _create_notification_event(
            user=request.user,
            organization=invoice.organization,
            action='update',
            description=f'Factura pagada: {invoice.invoice_number} ({invoice.organization.name})',
            severity='medium',
            module='billing',
            payload={'event': 'invoice_paid', 'invoice_id': str(invoice.id)},
        )

        return Response(ElectronicInvoiceDetailSerializer(invoice).data)

    @action(detail=False, methods=['post'])
    def run_cycle(self, request):
        serializer = RunSubscriptionBillingCycleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invoice, _, _, _ = run_subscription_billing_cycle(
                fiscal_profile=serializer.validated_data['fiscal_profile'],
                organization=serializer.validated_data['organization'],
                product=serializer.validated_data['product'],
                product_price=serializer.validated_data.get('product_price'),
                issued_by=request.user,
                mark_paid=serializer.validated_data['mark_paid'],
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        return Response(ElectronicInvoiceDetailSerializer(invoice).data, status=201)

    @action(detail=False, methods=['post'])
    def run_batch(self, request):
        serializer = RunBatchBillingCycleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = run_billing_cycle_batch(
            fiscal_profile=serializer.validated_data['fiscal_profile'],
            product=serializer.validated_data['product'],
            product_price=serializer.validated_data.get('product_price'),
            organization_ids=serializer.validated_data.get('organization_ids') or None,
            issued_by=request.user,
            mark_paid=serializer.validated_data['mark_paid'],
        )
        report_errors = report.get('errors', []) if isinstance(report, dict) else []
        _create_notification_event(
            user=request.user,
            organization=None,
            action='create',
            description='Ejecucion de batch de billing completada',
            severity='high' if report_errors else 'low',
            module='billing',
            payload={
                'event': 'billing_batch_run',
                'processed': report.get('processed_count', 0) if isinstance(report, dict) else 0,
                'errors': len(report_errors),
            },
        )
        return Response(BatchBillingReportSerializer(report).data)

    @action(detail=True, methods=['get'])
    def compliance_preview(self, request, pk=None):
        invoice = self.get_object()
        return Response(invoice.build_compliance_preview())

    @action(detail=True, methods=['post'])
    def prepare_hacienda(self, request, pk=None):
        invoice = self.get_object()
        try:
            invoice, xml_str = prepare_invoice_for_hacienda(invoice=invoice)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        return Response({
            'invoice': ElectronicInvoiceDetailSerializer(invoice).data,
            'xml_ready': bool(xml_str),
        })

    @action(detail=True, methods=['post'])
    def update_hacienda_status(self, request, pk=None):
        invoice = self.get_object()

        # poll=true → query Hacienda directly and update status automatically
        if request.data.get('poll') or request.query_params.get('poll'):
            try:
                invoice = poll_hacienda_status(invoice=invoice)
            except Exception as exc:
                return Response({'detail': str(exc)}, status=400)
            return Response({
                'invoice': ElectronicInvoiceDetailSerializer(invoice).data,
                'polled_from_hacienda': True,
            })

        # Manual status update (existing behaviour)
        serializer = HaciendaStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            invoice = update_hacienda_status(
                invoice=invoice,
                status_value=serializer.validated_data['hacienda_status'],
                message=serializer.validated_data.get('hacienda_message', ''),
                track_id=serializer.validated_data.get('hacienda_track_id', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        return Response(ElectronicInvoiceDetailSerializer(invoice).data)

    @action(detail=True, methods=['post'])
    def generate_xml(self, request, pk=None):
        invoice = self.get_object()
        if not invoice.consecutive_number or not invoice.numeric_key:
            try:
                invoice, _ = prepare_invoice_for_hacienda(invoice=invoice)
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=400)

        xml_str = generate_invoice_xml(invoice)
        invoice.xml_payload = xml_str
        invoice.save(update_fields=['xml_payload', 'updated_at'])
        return HttpResponse(xml_str, content_type='application/xml; charset=utf-8', status=200)

    @action(detail=True, methods=['post'])
    def credit_note(self, request, pk=None):
        original_invoice = self.get_object()
        serializer = CreditNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            note, snapshot = create_credit_note_for_invoice(
                original_invoice=original_invoice,
                reason=serializer.validated_data['reason'],
                issued_by=request.user,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        _create_notification_event(
            user=request.user,
            organization=note.organization,
            action='create',
            description=f'Nota de credito emitida para {original_invoice.invoice_number}',
            severity='high',
            module='billing',
            payload={
                'event': 'credit_note_created',
                'invoice_id': str(original_invoice.id),
                'credit_note_id': str(note.id),
            },
        )

        return Response(ElectronicInvoiceDetailSerializer(note).data, status=201)


class PaymentRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentRecord.objects.select_related('organization', 'invoice')
    serializer_class = PaymentRecordSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['organization', 'status', 'method', 'currency']
    ordering = ['-created_at']

    @action(detail=False, methods=['post'])
    def register_pending(self, request):
        serializer = CreatePendingPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        try:
            invoice = ElectronicInvoice.objects.get(id=d['invoice'])
        except ElectronicInvoice.DoesNotExist:
            return Response({'detail': 'Factura no encontrada.'}, status=404)
        try:
            payment = register_pending_payment(
                invoice=invoice,
                method=d['method'],
                reference=d.get('reference', ''),
                amount=d['amount'],
                notes=d.get('notes', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        _create_notification_event(
            user=request.user,
            organization=invoice.organization,
            action='create',
            description=f'Pago pendiente registrado para {invoice.invoice_number}',
            severity='medium',
            module='billing',
            payload={'event': 'payment_pending_registered', 'payment_id': str(payment.id), 'invoice_id': str(invoice.id)},
        )
        return Response(PaymentRecordSerializer(payment).data, status=201)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        payment = self.get_object()
        notes = request.data.get('notes', '')
        try:
            invoice, payment, _ = confirm_payment_record(payment=payment, notes=notes)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        _create_notification_event(
            user=request.user,
            organization=invoice.organization,
            action='update',
            description=f'Pago confirmado para {invoice.invoice_number}',
            severity='medium',
            module='billing',
            payload={'event': 'payment_confirmed', 'payment_id': str(payment.id), 'invoice_id': str(invoice.id)},
        )
        return Response(PaymentRecordSerializer(payment).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        payment = self.get_object()
        notes = request.data.get('notes', '')
        try:
            payment = reject_payment_record(payment=payment, notes=notes)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        invoice = payment.invoice
        _create_notification_event(
            user=request.user,
            organization=invoice.organization if invoice else None,
            action='update',
            description=f'Pago rechazado para {invoice.invoice_number if invoice else "factura"}',
            severity='high',
            module='billing',
            payload={'event': 'payment_rejected', 'payment_id': str(payment.id), 'invoice_id': str(invoice.id) if invoice else None},
        )
        return Response(PaymentRecordSerializer(payment).data)


class RevenueSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RevenueSnapshot.objects.select_related('product', 'organization')
    serializer_class = RevenueSnapshotSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'organization', 'currency', 'snapshot_date']
    ordering = ['-snapshot_date']


class RecurringReportScheduleViewSet(viewsets.ModelViewSet):
    queryset = RecurringReportSchedule.objects.all()
    serializer_class = RecurringReportScheduleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active', 'report_type', 'frequency']
    ordering = ['name']

    def perform_create(self, serializer):
        schedule = serializer.save()
        schedule.next_run_at = schedule.compute_next_run()
        schedule.save(update_fields=['next_run_at', 'updated_at'])

    def perform_update(self, serializer):
        schedule = serializer.save()
        schedule.next_run_at = schedule.compute_next_run(from_dt=timezone.now())
        schedule.save(update_fields=['next_run_at', 'updated_at'])

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        schedule = self.get_object()
        try:
            result = execute_recurring_report_schedule(schedule, run_time=timezone.now())
        except Exception as exc:  # noqa: BLE001
            return Response({'detail': str(exc)}, status=500)
        return Response(result)

    @action(detail=False, methods=['post'])
    def run_due(self, request):
        try:
            result = process_due_recurring_reports(triggered_at=timezone.now())
        except Exception as exc:  # noqa: BLE001
            return Response({'detail': str(exc)}, status=500)
        return Response(result)


class SchedulerStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from django.conf import settings
        from apps.billing.scheduler import get_scheduler

        scheduler = get_scheduler()
        running = bool(scheduler and scheduler.running)
        next_run = None
        reports_next_run = None
        if running:
            jobs = scheduler.get_jobs()
            for job in jobs:
                if job.id == 'billing_daily_batch' and job.next_run_time:
                    next_run = job.next_run_time.isoformat()
                if job.id == 'billing_recurring_reports' and job.next_run_time:
                    reports_next_run = job.next_run_time.isoformat()

        last_logs = list(
            SchedulerJobLog.objects.order_by('-triggered_at')[:20].values(
                'id', 'job_id', 'status', 'triggered_at', 'finished_at', 'result_summary'
            )
        )

        return Response({
            'enabled': getattr(settings, 'BILLING_SCHEDULER_ENABLED', False),
            'running': running,
            'cron': {
                'hour': getattr(settings, 'BILLING_SCHEDULER_HOUR', 6),
                'minute': getattr(settings, 'BILLING_SCHEDULER_MINUTE', 0),
            },
            'next_run': next_run,
            'reports_next_run': reports_next_run,
            'last_logs': last_logs,
        })

    def post(self, request):
        """Trigger the billing batch job on demand (same as manage.py billing_scheduler run_now)."""
        from apps.billing.scheduler import _run_billing_batch_job
        try:
            _run_billing_batch_job()
        except Exception as exc:  # noqa: BLE001
            return Response({'detail': str(exc)}, status=500)

        last_log = SchedulerJobLog.objects.order_by('-triggered_at').first()
        return Response({
            'status': last_log.status if last_log else 'unknown',
            'triggered_at': last_log.triggered_at.isoformat() if last_log else None,
            'result_summary': last_log.result_summary if last_log else {},
        })

class BillingChurnAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from apps.subscriptions.models import Subscription
        from datetime import timedelta as _td

        now = timezone.now()
        cutoff_30 = now - _td(days=30)
        cutoff_7_future = now + _td(days=7)

        active_count = Subscription.objects.filter(status='active').count()
        trial_count = Subscription.objects.filter(status='trial').count()
        churned_30 = Subscription.objects.filter(status='cancelled', cancelled_at__gte=cutoff_30).count()
        denom = active_count + churned_30
        churn_rate = round(float(churned_30 / denom * 100), 2) if denom > 0 else 0.0

        started_trial = Subscription.objects.filter(trial_started_at__isnull=False).count()
        converted_trial = Subscription.objects.filter(
            status='active', trial_started_at__isnull=False
        ).count()
        trial_conversion_rate = round(float(converted_trial / started_trial * 100), 2) if started_trial > 0 else 0.0

        # Trials expiring in the next 7 days
        expiring_trials = list(
            Subscription.objects.filter(
                status='trial',
                trial_ends_at__gte=now,
                trial_ends_at__lte=cutoff_7_future,
            ).select_related('plan').values(
                'id', 'plan__name', 'trial_ends_at',
            )
        )
        for t in expiring_trials:
            if t['trial_ends_at']:
                t['trial_ends_at'] = t['trial_ends_at'].isoformat()

        # Recently churned (last 30 days) with org detail
        churned_detail = list(
            Subscription.objects.filter(
                status='cancelled',
                cancelled_at__gte=cutoff_30,
            ).select_related('plan').values(
                'id', 'plan__name', 'cancelled_at', 'amount',
            ).order_by('-cancelled_at')[:20]
        )
        for c in churned_detail:
            if c['cancelled_at']:
                c['cancelled_at'] = c['cancelled_at'].isoformat()

        return Response({
            'active_subscriptions': active_count,
            'trial_subscriptions': trial_count,
            'churned_last_30_days': churned_30,
            'churn_rate': churn_rate,
            'trial_conversion_rate': trial_conversion_rate,
            'expiring_trials': expiring_trials,
            'churned_detail': churned_detail,
        })


class BillingReconciliationView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        """Return reconciliation summary: pending payments, confirmed, overdue and unmatched invoices."""
        date_from = request.query_params.get('date_from') or None
        date_to = request.query_params.get('date_to') or None
        summary = get_reconciliation_summary(date_from=date_from, date_to=date_to)
        return Response(ReconciliationSummarySerializer(summary).data)

    def post(self, request):
        """
        Register a pending payment for an invoice.
        Body: { invoice, method, reference, amount, notes }
        """
        serializer = CreatePendingPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        try:
            invoice = ElectronicInvoice.objects.get(id=d['invoice'])
        except ElectronicInvoice.DoesNotExist:
            return Response({'detail': 'Factura no encontrada.'}, status=404)
        try:
            payment = register_pending_payment(
                invoice=invoice,
                method=d['method'],
                reference=d.get('reference', ''),
                amount=d['amount'],
                notes=d.get('notes', ''),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        _create_notification_event(
            user=request.user,
            organization=invoice.organization,
            action='create',
            description=f'Pago pendiente registrado desde conciliacion para {invoice.invoice_number}',
            severity='medium',
            module='billing',
            payload={'event': 'reconciliation_payment_pending_registered', 'payment_id': str(payment.id), 'invoice_id': str(invoice.id)},
        )
        return Response(PaymentRecordSerializer(payment).data, status=201)


class ProductDashboardView(APIView):
    """Per-product metrics: revenue, subscriptions, MRR/ARR, invoices."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from apps.subscriptions.models import Subscription
        from decimal import Decimal as _D
        from .serializers import ProductDashboardSerializer

        products = ProductCatalog.objects.prefetch_related('prices').order_by('name')
        result = []
        for product in products:
            snap_agg = RevenueSnapshot.objects.filter(product=product).aggregate(
                gross=Sum('gross_revenue'), net=Sum('net_revenue'), tax=Sum('tax_collected'),
            )
            inv_qs = ElectronicInvoice.objects.filter(product=product)
            # Subscriptions linked to this product via invoices (Plan has no direct relation to ProductCatalog)
            sub_ids = inv_qs.filter(subscription__isnull=False).values_list('subscription_id', flat=True).distinct()
            active_subs = Subscription.objects.filter(id__in=sub_ids, status='active').count()
            trial_subs = Subscription.objects.filter(id__in=sub_ids, status='trial').count()
            mrr_subs = Subscription.objects.filter(id__in=sub_ids, status='active').select_related('plan')
            mrr = _D('0.00')
            for sub in mrr_subs:
                cycle = getattr(sub.plan, 'billing_cycle', 'monthly')
                amount = sub.amount or _D('0.00')
                if cycle == 'yearly': mrr += amount / 12
                elif cycle == 'quarterly': mrr += amount / 3
                else: mrr += amount
            result.append({
                'product_id': product.id,
                'product_code': product.code,
                'product_name': product.name,
                'is_active': product.is_active,
                'billing_model': product.billing_model,
                'active_subscriptions': active_subs,
                'trial_subscriptions': trial_subs,
                'gross_revenue': snap_agg['gross'] or _D('0.00'),
                'net_revenue': snap_agg['net'] or _D('0.00'),
                'tax_collected': snap_agg['tax'] or _D('0.00'),
                'total_invoices': inv_qs.count(),
                'paid_invoices': inv_qs.filter(status='paid').count(),
                'pending_invoices': inv_qs.filter(status__in=['draft', 'pending']).count(),
                'mrr': mrr,
                'arr': mrr * 12,
            })
        return Response(ProductDashboardSerializer(result, many=True).data)


class BillingAlertsView(APIView):
    """Operational billing alerts: overdue, Hacienda, trials, scheduler errors."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        from datetime import timedelta as _td
        from apps.subscriptions.models import Subscription

        now = timezone.now()
        today = now.date()
        alerts = []

        for inv in ElectronicInvoice.objects.filter(
            due_date__lt=today, due_date__isnull=False, status__in=['pending', 'accepted'],
        ).select_related('organization').order_by('due_date')[:10]:
            alerts.append({
                'type': 'invoice_overdue', 'severity': 'warning',
                'message': f'Factura {inv.invoice_number} de {inv.organization.name} vencida — {inv.total} {inv.currency}',
                'invoice_id': str(inv.id), 'due_date': str(inv.due_date),
            })

        for inv in ElectronicInvoice.objects.filter(
            hacienda_status__in=['rejected', 'error'],
        ).select_related('organization').order_by('-submitted_at')[:10]:
            alerts.append({
                'type': 'hacienda_rejected', 'severity': 'danger',
                'message': f'Hacienda rechazó {inv.invoice_number} ({inv.organization.name}): {(inv.hacienda_message or "sin detalle")[:80]}',
                'invoice_id': str(inv.id),
            })

        stuck_threshold = now - _td(hours=24)
        for inv in ElectronicInvoice.objects.filter(
            hacienda_status='processing', submitted_at__lt=stuck_threshold,
        ).select_related('organization').order_by('submitted_at')[:10]:
            alerts.append({
                'type': 'hacienda_pending_submit', 'severity': 'warning',
                'message': f'{inv.invoice_number} ({inv.organization.name}) lleva más de 24h en procesamiento en Hacienda.',
                'invoice_id': str(inv.id),
                'submitted_at': inv.submitted_at.isoformat() if inv.submitted_at else None,
            })

        in_3_days = now + _td(days=3)
        for sub in Subscription.objects.filter(
            status='trial', trial_ends_at__gte=now, trial_ends_at__lte=in_3_days,
        ).select_related('plan')[:10]:
            alerts.append({
                'type': 'trial_expiring_soon', 'severity': 'info',
                'message': f'Trial de {sub.plan.name} vence el {sub.trial_ends_at.strftime("%Y-%m-%d")}.',
                'subscription_id': str(sub.id),
            })

        last_log = SchedulerJobLog.objects.order_by('-triggered_at').first()
        if last_log and last_log.status == 'error':
            alerts.append({
                'type': 'scheduler_error', 'severity': 'danger',
                'message': f'El último ciclo del scheduler falló ({last_log.triggered_at.strftime("%Y-%m-%d %H:%M")}).',
                'log_id': str(last_log.id),
            })

        return Response({'alerts': alerts, 'count': len(alerts)})
