"""
Serializers for Subscriptions - Admin Apps
"""
from django.conf import settings
from rest_framework import serializers
from .models import Plan, Subscription, Invoice, PaymentMethod


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


class PlanListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de planes"""
    
    class Meta:
        model = Plan
        fields = [
            'id', 'code', 'name', 'description', 'price', 'currency',
            'billing_cycle', 'max_users', 'max_documents', 'max_storage_mb',
            'ai_analysis_enabled', 'is_active', 'is_featured', 'display_order'
        ]


class PlanDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de planes"""
    
    class Meta:
        model = Plan
        fields = '__all__'


class SubscriptionListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de suscripciones"""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    days_remaining = serializers.ReadOnlyField()
    organization_name = serializers.SerializerMethodField()
    billing_exempt = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_name', 'organization_name', 'status', 'days_remaining',
            'amount', 'next_billing_date', 'billing_exempt',
            'current_period_start', 'current_period_end',
            'current_users', 'current_documents', 'current_storage_mb'
        ]

    def _get_organization(self, obj):
        invoice = obj.invoices.select_related('organization').order_by('-issued_at').first()
        return invoice.organization if invoice and invoice.organization else None

    def get_organization_name(self, obj):
        organization = self._get_organization(obj)
        return organization.name if organization else None

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(self._get_organization(obj))


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de suscripciones"""
    plan = PlanListSerializer(read_only=True)
    days_remaining = serializers.ReadOnlyField()
    trial_days_remaining = serializers.ReadOnlyField()
    usage_percentage = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    is_trial = serializers.ReadOnlyField()
    organization_name = serializers.SerializerMethodField()
    billing_exempt = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = '__all__'

    def _get_organization(self, obj):
        invoice = obj.invoices.select_related('organization').order_by('-issued_at').first()
        return invoice.organization if invoice and invoice.organization else None

    def get_organization_name(self, obj):
        organization = self._get_organization(obj)
        return organization.name if organization else None

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(self._get_organization(obj))


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear suscripciones"""
    
    class Meta:
        model = Subscription
        fields = ['plan']
    
    def create(self, validated_data):
        subscription = Subscription.objects.create(**validated_data)
        subscription.start_trial()
        return subscription


class InvoiceListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados de facturas"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    billing_exempt = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'number', 'organization_name', 'total', 'currency',
            'status', 'issued_at', 'due_date', 'paid_at', 'billing_exempt'
        ]

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(getattr(obj, 'organization', None))


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de facturas"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    subscription_plan = serializers.CharField(source='subscription.plan.name', read_only=True)
    billing_exempt = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = '__all__'

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(getattr(obj, 'organization', None))


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer para métodos de pago"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'type', 'name', 'display_name',
            'card_last_four', 'card_brand', 'card_exp_month', 'card_exp_year',
            'bank_name', 'is_default', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_display_name(self, obj):
        return str(obj)


class SubscriptionStatsSerializer(serializers.Serializer):
    """Estadísticas de suscripciones"""
    total_active = serializers.IntegerField()
    total_trial = serializers.IntegerField()
    total_cancelled = serializers.IntegerField()
    revenue_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_last_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    churn_rate = serializers.FloatField()
