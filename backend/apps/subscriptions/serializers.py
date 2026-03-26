"""
Serializers for Subscriptions - Admin Apps
"""
from rest_framework import serializers
from .models import Plan, Subscription, Invoice, PaymentMethod


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
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_name', 'organization_name', 'status', 'days_remaining',
            'amount', 'next_billing_date',
            'current_period_start', 'current_period_end',
            'current_users', 'current_documents', 'current_storage_mb'
        ]

    def get_organization_name(self, obj):
        invoice = obj.invoices.select_related('organization').order_by('-issued_at').first()
        return invoice.organization.name if invoice and invoice.organization else None


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de suscripciones"""
    plan = PlanListSerializer(read_only=True)
    days_remaining = serializers.ReadOnlyField()
    trial_days_remaining = serializers.ReadOnlyField()
    usage_percentage = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    is_trial = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = '__all__'


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
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'number', 'organization_name', 'total', 'currency',
            'status', 'issued_at', 'due_date', 'paid_at'
        ]


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de facturas"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    subscription_plan = serializers.CharField(source='subscription.plan.name', read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'


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
