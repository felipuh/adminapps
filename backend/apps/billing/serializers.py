from django.conf import settings
from rest_framework import serializers

from .models import (
    ElectronicInvoice,
    FiscalProfile,
    InvoiceLine,
    PaymentRecord,
    ProductCatalog,
    ProductPrice,
    RecurringReportSchedule,
    RevenueSnapshot,
)


def _normalize_text(value):
    return str(value or '').strip().lower()


def _is_billing_exempt_owner_org(organization):
    if not organization or not getattr(settings, 'BILLING_OWNER_ORG_EXEMPT_ENABLED', True):
        return False

    configured_id = str(getattr(settings, 'BILLING_OWNER_ORG_ID', '') or '').strip()
    configured_code = _normalize_text(getattr(settings, 'BILLING_OWNER_ORG_CODE', ''))
    configured_name = _normalize_text(getattr(settings, 'BILLING_OWNER_ORG_NAME', ''))

    org_id = str(getattr(organization, 'id', '') or '').strip()
    org_code = _normalize_text(getattr(organization, 'code', ''))
    org_name = _normalize_text(getattr(organization, 'name', ''))

    if configured_id and org_id == configured_id:
        return True
    if configured_code and org_code == configured_code:
        return True
    if configured_name and org_name == configured_name:
        return True
    return False


class IssueInvoiceSerializer(serializers.Serializer):
    fiscal_profile = serializers.PrimaryKeyRelatedField(queryset=FiscalProfile.objects.filter(is_active=True))
    organization = serializers.PrimaryKeyRelatedField(queryset=ElectronicInvoice._meta.get_field('organization').remote_field.model.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=ProductCatalog.objects.filter(is_active=True))
    product_price = serializers.PrimaryKeyRelatedField(queryset=ProductPrice.objects.filter(is_active=True))
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=ElectronicInvoice._meta.get_field('subscription').remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default='1.00')
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default='0.00')
    due_date = serializers.DateField(required=False, allow_null=True)
    mark_paid = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        organization = attrs['organization']
        product = attrs['product']
        product_price = attrs['product_price']
        subscription = attrs.get('subscription') or organization.subscription

        if product_price.product_id != product.id:
            raise serializers.ValidationError({
                'product_price': 'El precio seleccionado no pertenece al producto indicado.'
            })

        if subscription and organization.subscription_id and subscription.id != organization.subscription_id:
            raise serializers.ValidationError({
                'subscription': 'La suscripcion debe coincidir con la suscripcion activa de la organizacion.'
            })

        attrs['subscription'] = subscription
        return attrs


class IssueSubscriptionInvoiceSerializer(serializers.Serializer):
    fiscal_profile = serializers.PrimaryKeyRelatedField(queryset=FiscalProfile.objects.filter(is_active=True))
    organization = serializers.PrimaryKeyRelatedField(queryset=ElectronicInvoice._meta.get_field('organization').remote_field.model.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=ProductCatalog.objects.filter(is_active=True))
    product_price = serializers.PrimaryKeyRelatedField(
        queryset=ProductPrice.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default='1.00')
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default='0.00')
    due_date = serializers.DateField(required=False, allow_null=True)
    mark_paid = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        organization = attrs['organization']
        product = attrs['product']
        product_price = attrs.get('product_price')

        if not organization.subscription_id:
            raise serializers.ValidationError({
                'organization': 'La organizacion no tiene una suscripcion activa asociada.'
            })

        if product_price and product_price.product_id != product.id:
            raise serializers.ValidationError({
                'product_price': 'El precio seleccionado no pertenece al producto indicado.'
            })

        attrs['subscription'] = organization.subscription
        return attrs


class RunSubscriptionBillingCycleSerializer(serializers.Serializer):
    fiscal_profile = serializers.PrimaryKeyRelatedField(queryset=FiscalProfile.objects.filter(is_active=True))
    organization = serializers.PrimaryKeyRelatedField(queryset=ElectronicInvoice._meta.get_field('organization').remote_field.model.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=ProductCatalog.objects.filter(is_active=True))
    product_price = serializers.PrimaryKeyRelatedField(
        queryset=ProductPrice.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    mark_paid = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        organization = attrs['organization']
        product = attrs['product']
        product_price = attrs.get('product_price')

        if not organization.subscription_id:
            raise serializers.ValidationError({'organization': 'La organizacion no tiene una suscripcion asociada.'})
        if product_price and product_price.product_id != product.id:
            raise serializers.ValidationError({'product_price': 'El precio seleccionado no pertenece al producto indicado.'})
        return attrs


class RunBatchBillingCycleSerializer(serializers.Serializer):
    fiscal_profile = serializers.PrimaryKeyRelatedField(queryset=FiscalProfile.objects.filter(is_active=True))
    product = serializers.PrimaryKeyRelatedField(queryset=ProductCatalog.objects.filter(is_active=True))
    product_price = serializers.PrimaryKeyRelatedField(
        queryset=ProductPrice.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    organization_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    mark_paid = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        product = attrs['product']
        product_price = attrs.get('product_price')
        if product_price and product_price.product_id != product.id:
            raise serializers.ValidationError({'product_price': 'El precio seleccionado no pertenece al producto indicado.'})
        return attrs


class HaciendaStatusUpdateSerializer(serializers.Serializer):
    hacienda_status = serializers.ChoiceField(choices=['processing', 'accepted', 'rejected', 'error'])
    hacienda_message = serializers.CharField(required=False, allow_blank=True)
    hacienda_track_id = serializers.CharField(required=False, allow_blank=True)


class CreditNoteSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)


class RecordPaymentSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['sinpe', 'bank_transfer', 'card', 'cash', 'check', 'deposit', 'other'])
    reference = serializers.CharField(required=False, allow_blank=True)
    paid_at = serializers.DateTimeField(required=False, allow_null=True)


class FiscalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalProfile
        fields = '__all__'


class ProductCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCatalog
        fields = '__all__'


class ProductPriceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductPrice
        fields = '__all__'

    def validate_cabys_code(self, value):
        if value and (not value.isdigit() or len(value) != 13):
            raise serializers.ValidationError('El codigo CAByS debe tener 13 digitos numericos.')
        return value


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = '__all__'
        read_only_fields = ['subtotal', 'tax_amount', 'total', 'created_at']


class ElectronicInvoiceListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    billing_exempt = serializers.SerializerMethodField()

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(getattr(obj, 'organization', None))

    class Meta:
        model = ElectronicInvoice
        fields = [
            'id', 'invoice_number', 'organization_name', 'product_name',
            'currency', 'total', 'status', 'hacienda_status', 'issued_at', 'due_date', 'paid_at', 'billing_exempt'
        ]


class ElectronicInvoiceDetailSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    billing_exempt = serializers.SerializerMethodField()

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(getattr(obj, 'organization', None))

    class Meta:
        model = ElectronicInvoice
        fields = '__all__'


class PaymentRecordSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    billing_exempt = serializers.SerializerMethodField()

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(getattr(obj, 'organization', None))

    class Meta:
        model = PaymentRecord
        fields = '__all__'


class RevenueSnapshotSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True, default=None)
    billing_exempt = serializers.SerializerMethodField()

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(getattr(obj, 'organization', None))

    class Meta:
        model = RevenueSnapshot
        fields = '__all__'


class ReconciliationSummarySerializer(serializers.Serializer):
    pending_payments = serializers.IntegerField()
    pending_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    confirmed_payments = serializers.IntegerField()
    confirmed_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_invoices = serializers.IntegerField()
    overdue_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    unmatched_invoices = serializers.IntegerField()
    payment_methods_count = serializers.DictField(child=serializers.IntegerField(), required=False)
    payment_methods_amount = serializers.DictField(child=serializers.CharField(), required=False)


class CreatePendingPaymentSerializer(serializers.Serializer):
    invoice = serializers.UUIDField()
    method = serializers.ChoiceField(choices=['sinpe', 'bank_transfer', 'card', 'cash', 'check', 'deposit', 'other'])
    reference = serializers.CharField(max_length=255, required=False, default='')
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(max_length=1000, required=False, default='')


class BillingSummarySerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    total_invoices = serializers.IntegerField()
    accepted_invoices = serializers.IntegerField()
    paid_invoices = serializers.IntegerField()
    pending_invoices = serializers.IntegerField()
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    accounts_receivable = serializers.DecimalField(max_digits=14, decimal_places=2)
    mrr = serializers.DecimalField(max_digits=14, decimal_places=2)
    arr = serializers.DecimalField(max_digits=14, decimal_places=2)
    active_subscriptions = serializers.IntegerField()
    trial_subscriptions = serializers.IntegerField()
    churned_last_30_days = serializers.IntegerField()
    churn_rate = serializers.FloatField()
    trial_conversion_rate = serializers.FloatField()


class RevenueByOrganizationSerializer(serializers.Serializer):
    organization__id = serializers.UUIDField()
    organization__name = serializers.CharField()
    billing_exempt = serializers.BooleanField(required=False, default=False)
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    invoices_issued = serializers.IntegerField()
    invoices_paid = serializers.IntegerField()


class RevenueTimelineSerializer(serializers.Serializer):
    period = serializers.CharField()
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    invoices_issued = serializers.IntegerField()
    invoices_paid = serializers.IntegerField()


class AccountsReceivableSerializer(serializers.Serializer):
    current = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_1_30 = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_31_60 = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_61_plus = serializers.DecimalField(max_digits=14, decimal_places=2)


class BatchBillingReportSerializer(serializers.Serializer):
    run_date = serializers.CharField()
    processed = serializers.ListField()
    skipped = serializers.ListField()
    errors = serializers.ListField()
    summary = serializers.DictField()


class RevenueByProductSerializer(serializers.Serializer):
    product__code = serializers.CharField()
    product__name = serializers.CharField()
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    invoices_paid = serializers.IntegerField()


class ProductDashboardSerializer(serializers.Serializer):
    """Full metrics for a single product in the product dashboard."""
    product_id = serializers.UUIDField()
    product_code = serializers.CharField()
    product_name = serializers.CharField()
    is_active = serializers.BooleanField()
    billing_model = serializers.CharField()
    active_subscriptions = serializers.IntegerField()
    trial_subscriptions = serializers.IntegerField()
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_invoices = serializers.IntegerField()
    paid_invoices = serializers.IntegerField()
    pending_invoices = serializers.IntegerField()
    mrr = serializers.DecimalField(max_digits=14, decimal_places=2)
    arr = serializers.DecimalField(max_digits=14, decimal_places=2)


class RecurringReportScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringReportSchedule
        fields = '__all__'
        read_only_fields = ['last_run_at', 'next_run_at', 'created_at', 'updated_at']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        frequency = attrs.get('frequency', getattr(self.instance, 'frequency', 'daily'))
        day_of_week = attrs.get('day_of_week', getattr(self.instance, 'day_of_week', None))
        day_of_month = attrs.get('day_of_month', getattr(self.instance, 'day_of_month', None))
        hour = attrs.get('hour', getattr(self.instance, 'hour', 7))
        minute = attrs.get('minute', getattr(self.instance, 'minute', 0))
        recipients = attrs.get('recipients', getattr(self.instance, 'recipients', []))

        if not recipients:
            raise serializers.ValidationError({'recipients': 'Debe indicar al menos un correo receptor.'})

        if hour < 0 or hour > 23:
            raise serializers.ValidationError({'hour': 'La hora debe estar entre 0 y 23.'})
        if minute < 0 or minute > 59:
            raise serializers.ValidationError({'minute': 'El minuto debe estar entre 0 y 59.'})

        if frequency == 'weekly':
            if day_of_week is None or day_of_week < 0 or day_of_week > 6:
                raise serializers.ValidationError({'day_of_week': 'Para frecuencia semanal use un día entre 0 (lunes) y 6 (domingo).'})
        elif frequency == 'monthly':
            if day_of_month is None or day_of_month < 1 or day_of_month > 31:
                raise serializers.ValidationError({'day_of_month': 'Para frecuencia mensual use un día entre 1 y 31.'})

        return attrs
