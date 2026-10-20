"""
Serializers for Subscriptions - Admin Apps
"""
from apps.users.api_authorization import StrictInputMixin, reject_reparenting

from django.conf import settings
from rest_framework import serializers
from apps.organizations.models import Organization
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


class PlanDetailSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer completo para detalle de planes"""
    
    class Meta:
        model = Plan
        fields = [
            'id', 'code', 'name', 'description', 'price', 'currency',
            'billing_cycle', 'max_users', 'max_documents', 'max_storage_mb',
            'max_organizations', 'modules_included', 'features',
            'ai_analysis_enabled', 'ai_monthly_quota', 'is_active',
            'is_featured', 'is_trial_available', 'trial_days',
            'display_order', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
        invoices = obj.invoices.select_related('organization')
        actor = getattr(self.context.get('request'), 'user', None)
        if actor and not actor.is_admin:
            invoices = invoices.filter(organization_id=actor.organization_id)
        invoice = invoices.order_by('-issued_at').first()
        return invoice.organization if invoice and invoice.organization else None

    def get_organization_name(self, obj):
        organization = self._get_organization(obj)
        return organization.name if organization else None

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(self._get_organization(obj))


class SubscriptionDetailSerializer(StrictInputMixin, serializers.ModelSerializer):
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
        fields = [
            'id', 'plan', 'days_remaining', 'trial_days_remaining',
            'usage_percentage', 'is_active', 'is_trial', 'organization_name',
            'billing_exempt', 'status', 'trial_started_at', 'trial_ends_at',
            'started_at', 'current_period_start', 'current_period_end',
            'cancelled_at', 'next_billing_date', 'amount', 'discount_percent',
            'current_users', 'current_documents', 'current_storage_mb',
            'ai_usage_this_month', 'payment_method', 'external_subscription_id',
            'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _get_organization(self, obj):
        invoices = obj.invoices.select_related('organization')
        actor = getattr(self.context.get('request'), 'user', None)
        if actor and not actor.is_admin:
            invoices = invoices.filter(organization_id=actor.organization_id)
        invoice = invoices.order_by('-issued_at').first()
        return invoice.organization if invoice and invoice.organization else None

    def get_organization_name(self, obj):
        organization = self._get_organization(obj)
        return organization.name if organization else None

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(self._get_organization(obj))


class SubscriptionCreateSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer para crear suscripciones"""
    
    class Meta:
        model = Subscription
        fields = ['plan']
    
    def create(self, validated_data):
        subscription = Subscription.objects.create(**validated_data)
        subscription.start_trial()
        return subscription


class MarkInvoicePaidSerializer(StrictInputMixin, serializers.Serializer):
    payment_reference = serializers.CharField(
        required=False, allow_blank=True, max_length=255, trim_whitespace=False,
    )


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


class InvoiceDetailSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer completo para detalle de facturas"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    subscription_plan = serializers.CharField(source='subscription.plan.name', read_only=True)
    billing_exempt = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'number', 'subscription', 'subscription_plan',
            'organization', 'organization_name', 'subtotal', 'tax',
            'discount', 'total', 'currency', 'status', 'issued_at',
            'due_date', 'paid_at', 'period_start', 'period_end',
            'line_items', 'notes', 'payment_method', 'payment_reference',
            'billing_exempt', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        reject_reparenting(self.instance, attrs, ('organization', 'subscription'))
        organization = attrs.get('organization') or getattr(self.instance, 'organization', None)
        subscription = attrs.get('subscription') or getattr(self.instance, 'subscription', None)
        if subscription and (not organization or organization.subscription_id != subscription.pk):
            raise serializers.ValidationError({'subscription': 'La suscripción no es la relación canónica de la organización.'})
        return attrs

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(getattr(obj, 'organization', None))


class PaymentMethodSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer para métodos de pago"""
    display_name = serializers.SerializerMethodField()
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), required=False, write_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'organization', 'type', 'name', 'display_name',
            'card_last_four', 'card_brand', 'card_exp_month', 'card_exp_year',
            'bank_name', 'is_default', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, attrs):
        reject_reparenting(self.instance, attrs, ('organization',))
        actor = self.context['request'].user
        organization = attrs.get('organization') or getattr(self.instance, 'organization', None) or actor.organization
        if not organization or not organization.is_active:
            raise serializers.ValidationError({'organization': 'Se requiere una organización activa.'})
        if not actor.is_admin and str(organization.pk) != str(actor.organization_id):
            raise serializers.ValidationError({'organization': 'Organización no autorizada.'})
        attrs['organization'] = organization
        return attrs

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
