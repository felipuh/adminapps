import uuid
from datetime import datetime, time as dt_time, timedelta
from calendar import monthrange
from decimal import Decimal

from django.db import models
from django.utils import timezone


class FiscalProfile(models.Model):
    COUNTRY_CHOICES = [
        ('CR', 'Costa Rica'),
    ]

    ENVIRONMENT_CHOICES = [
        ('sandbox', 'Sandbox'),
        ('production', 'Production'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='CR')
    legal_name = models.CharField(max_length=255)
    commercial_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=50, unique=True)
    tax_activity_code = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    hacienda_environment = models.CharField(max_length=20, choices=ENVIRONMENT_CHOICES, default='sandbox')
    hacienda_username = models.CharField(max_length=255, blank=True)
    hacienda_password = models.CharField(max_length=255, blank=True)
    # OAuth2 credentials for the Hacienda ATV API
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    certificate_file = models.CharField(max_length=255, blank=True)
    certificate_pin = models.CharField(max_length=100, blank=True)
    branch_code = models.CharField(max_length=3, default='001')
    terminal_code = models.CharField(max_length=5, default='00001')
    invoice_sequence = models.PositiveIntegerField(default=1)
    credit_note_sequence = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_fiscal_profiles'
        ordering = ['legal_name']

    def __str__(self):
        return self.commercial_name or self.legal_name

    def next_invoice_number(self):
        current = self.invoice_sequence
        return f'CR-{timezone.now().year}-{current:08d}'

    def next_consecutive_number(self, document_type_code='01'):
        if document_type_code == '03':
            sequence = f'{self.credit_note_sequence:010d}'
        else:
            sequence = f'{self.invoice_sequence:010d}'
        return f'{self.branch_code}{self.terminal_code}{document_type_code}{sequence}'

    def consume_credit_note_sequence(self):
        note_number = f'CR-NC-{timezone.now().year}-{self.credit_note_sequence:08d}'
        self.credit_note_sequence += 1
        self.save(update_fields=['credit_note_sequence', 'updated_at'])
        return note_number

    def consume_invoice_sequence(self):
        invoice_number = self.next_invoice_number()
        self.invoice_sequence += 1
        self.save(update_fields=['invoice_sequence', 'updated_at'])
        return invoice_number

    @property
    def has_hacienda_credentials(self) -> bool:
        """True when enough credentials exist to call the Hacienda ATV API."""
        return bool(
            self.client_id
            and self.client_secret
            and self.hacienda_username
            and self.hacienda_password
        )


class ProductCatalog(models.Model):
    BILLING_MODEL_CHOICES = [
        ('subscription', 'Subscription'),
        ('usage', 'Usage'),
        ('hybrid', 'Hybrid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    billing_model = models.CharField(max_length=20, choices=BILLING_MODEL_CHOICES, default='subscription')
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_products'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductPrice(models.Model):
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
        ('one_time', 'Unico'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(ProductCatalog, on_delete=models.CASCADE, related_name='prices')
    name = models.CharField(max_length=120)
    currency = models.CharField(max_length=3, default='CRC')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('13.00'))
    cabys_code = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_product_prices'
        ordering = ['product__name', 'amount']

    def __str__(self):
        return f'{self.product.code} - {self.name}'

    @property
    def has_valid_cabys_code(self):
        return self.cabys_code.isdigit() and len(self.cabys_code) == 13


class ElectronicInvoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('paid', 'Paid'),
        ('reversed', 'Reversed'),
    ]

    HACIENDA_STATUS_CHOICES = [
        ('not_sent', 'Not Sent'),
        ('processing', 'Processing'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('error', 'Error'),
    ]

    DOCUMENT_TYPE_CHOICES = [
        ('01', 'Factura Electronica'),
        ('03', 'Nota de Credito Electronica'),
        ('04', 'Tiquete Electronico'),
    ]

    SALE_CONDITION_CHOICES = [
        ('01', 'Contado'),
        ('02', 'Credito'),
        ('99', 'Otros'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('01', 'Efectivo'),
        ('02', 'Tarjeta'),
        ('03', 'Transferencia'),
        ('04', 'SINPE Movil'),
        ('99', 'Otros'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fiscal_profile = models.ForeignKey(FiscalProfile, on_delete=models.PROTECT, related_name='invoices')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT, related_name='electronic_invoices')
    subscription = models.ForeignKey('subscriptions.Subscription', on_delete=models.SET_NULL, null=True, blank=True, related_name='electronic_invoices')
    product = models.ForeignKey(ProductCatalog, on_delete=models.PROTECT, related_name='invoices')
    product_price = models.ForeignKey(ProductPrice, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    hci_key = models.CharField(max_length=80, blank=True)
    document_type_code = models.CharField(max_length=2, choices=DOCUMENT_TYPE_CHOICES, default='01')
    consecutive_number = models.CharField(max_length=20, blank=True)
    numeric_key = models.CharField(max_length=50, blank=True)
    receiver_name = models.CharField(max_length=255, blank=True)
    receiver_tax_id = models.CharField(max_length=50, blank=True)
    receiver_email = models.EmailField(blank=True)
    sale_condition = models.CharField(max_length=2, choices=SALE_CONDITION_CHOICES, default='01')
    payment_method_code = models.CharField(max_length=2, choices=PAYMENT_METHOD_CHOICES, default='03')
    currency = models.CharField(max_length=3, default='CRC')
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('1.0000'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    issued_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    hacienda_status = models.CharField(max_length=20, choices=HACIENDA_STATUS_CHOICES, default='not_sent')
    hacienda_message = models.TextField(blank=True)
    hacienda_track_id = models.CharField(max_length=100, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    xml_payload = models.TextField(blank=True)
    xml_response = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_electronic_invoices'
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number

    def recalculate_totals(self):
        lines = list(self.lines.all())
        subtotal = sum((line.subtotal for line in lines), Decimal('0.00'))
        tax_total = sum((line.tax_amount for line in lines), Decimal('0.00'))
        discount_total = sum((line.discount_amount for line in lines), Decimal('0.00'))
        self.subtotal = subtotal
        self.tax_total = tax_total
        self.discount_total = discount_total
        self.total = subtotal + tax_total - discount_total
        return self.total

    def build_compliance_preview(self):
        return {
            'country': self.fiscal_profile.country,
            'document_type': self.document_type_code,
            'emisor': {
                'legal_name': self.fiscal_profile.legal_name,
                'commercial_name': self.fiscal_profile.commercial_name,
                'tax_id': self.fiscal_profile.tax_id,
                'tax_activity_code': self.fiscal_profile.tax_activity_code,
                'email': self.fiscal_profile.email,
                'branch_code': self.fiscal_profile.branch_code,
                'terminal_code': self.fiscal_profile.terminal_code,
            },
            'receptor': {
                'name': self.receiver_name,
                'tax_id': self.receiver_tax_id,
                'email': self.receiver_email,
            },
            'documento': {
                'invoice_number': self.invoice_number,
                'consecutive_number': self.consecutive_number,
                'numeric_key': self.numeric_key,
                'sale_condition': self.sale_condition,
                'payment_method_code': self.payment_method_code,
                'currency': self.currency,
                'exchange_rate': str(self.exchange_rate),
                'subtotal': str(self.subtotal),
                'tax_total': str(self.tax_total),
                'discount_total': str(self.discount_total),
                'total': str(self.total),
                'hacienda_status': self.hacienda_status,
            },
            'lineas': [
                {
                    'description': line.description,
                    'cabys_code': line.cabys_code,
                    'quantity': str(line.quantity),
                    'unit_price': str(line.unit_price),
                    'discount_amount': str(line.discount_amount),
                    'tax_rate': str(line.tax_rate),
                    'subtotal': str(line.subtotal),
                    'tax_amount': str(line.tax_amount),
                    'total': str(line.total),
                }
                for line in self.lines.all()
            ],
        }

    def build_hacienda_document(self):
        preview = self.build_compliance_preview()
        preview['comprobante'] = {
            'clave': self.numeric_key,
            'numero_consecutivo': self.consecutive_number,
            'tipo_documento': self.document_type_code,
            'fecha_emision': self.issued_at.isoformat() if self.issued_at else None,
            'condicion_venta': self.sale_condition,
            'medio_pago': self.payment_method_code,
        }
        return preview


class InvoiceLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(ElectronicInvoice, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=255)
    cabys_code = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('13.00'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'billing_invoice_lines'
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        self.quantity = Decimal(str(self.quantity))
        self.unit_price = Decimal(str(self.unit_price))
        self.discount_amount = Decimal(str(self.discount_amount))
        self.tax_rate = Decimal(str(self.tax_rate))

        gross_subtotal = self.quantity * self.unit_price
        self.subtotal = gross_subtotal
        taxable_base = gross_subtotal - self.discount_amount
        self.tax_amount = (taxable_base * self.tax_rate) / Decimal('100.00')
        self.total = taxable_base + self.tax_amount
        super().save(*args, **kwargs)


class PaymentRecord(models.Model):
    METHOD_CHOICES = [
        ('sinpe', 'SINPE'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('deposit', 'Deposit'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('reversed', 'Reversed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(ElectronicInvoice, on_delete=models.CASCADE, related_name='payments')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT, related_name='payment_records')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='CRC')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_payment_records'
        ordering = ['-created_at']


class RevenueSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot_date = models.DateField()
    product = models.ForeignKey(ProductCatalog, on_delete=models.CASCADE, related_name='revenue_snapshots')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='revenue_snapshots')
    currency = models.CharField(max_length=3, default='CRC')
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_collected = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    invoices_issued = models.PositiveIntegerField(default=0)
    invoices_paid = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_revenue_snapshots'
        ordering = ['-snapshot_date', 'product__name']
        unique_together = ['snapshot_date', 'product', 'organization', 'currency']

    def __str__(self):
        return f'{self.snapshot_date} - {self.product.code}'

    def accumulate_invoice(self, invoice, mark_paid=False):
        self.gross_revenue += invoice.subtotal
        self.net_revenue += invoice.total
        self.tax_collected += invoice.tax_total
        self.invoices_issued += 1
        if mark_paid:
            self.invoices_paid += 1

    def register_payment(self):
        self.invoices_paid += 1


class SchedulerJobLog(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('success', 'Success'),
        ('skipped', 'Skipped'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_id = models.CharField(max_length=100)
    triggered_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    result_summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'billing_scheduler_job_logs'
        ordering = ['-triggered_at']

    def __str__(self):
        return f'{self.job_id} @ {self.triggered_at:%Y-%m-%d %H:%M} — {self.status}'


class RecurringReportSchedule(models.Model):
    REPORT_TYPE_CHOICES = [
        ('billing_summary', 'Billing Summary'),
        ('collections_snapshot', 'Collections Snapshot'),
    ]

    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    report_type = models.CharField(max_length=40, choices=REPORT_TYPE_CHOICES, default='billing_summary')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    day_of_week = models.PositiveSmallIntegerField(null=True, blank=True)
    day_of_month = models.PositiveSmallIntegerField(null=True, blank=True)
    hour = models.PositiveSmallIntegerField(default=7)
    minute = models.PositiveSmallIntegerField(default=0)
    timezone = models.CharField(max_length=64, default='America/Costa_Rica')
    recipients = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_recurring_report_schedules'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.frequency})'

    def compute_next_run(self, from_dt=None):
        base_dt = from_dt or timezone.now()
        base_dt = timezone.localtime(base_dt)
        schedule_time = dt_time(hour=int(self.hour), minute=int(self.minute), second=0)

        for offset in range(0, 370):
            candidate_date = base_dt.date() + timedelta(days=offset)

            if self.frequency == 'weekly':
                target_weekday = int(self.day_of_week if self.day_of_week is not None else 0)
                if candidate_date.weekday() != target_weekday:
                    continue

            if self.frequency == 'monthly':
                month_last_day = monthrange(candidate_date.year, candidate_date.month)[1]
                target_day = int(self.day_of_month if self.day_of_month is not None else 1)
                target_day = min(max(target_day, 1), month_last_day)
                if candidate_date.day != target_day:
                    continue

            candidate_dt = timezone.make_aware(
                datetime.combine(candidate_date, schedule_time),
                timezone.get_current_timezone(),
            )

            if candidate_dt > base_dt:
                return candidate_dt

        # Fallback safety to avoid returning None in edge cases.
        return base_dt + timedelta(days=1)

