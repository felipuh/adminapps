"""
Serializers for Products - Admin Apps
Control de módulos ISO
"""
from rest_framework import serializers
from .models import (
    ISOStandard,
    ModuleActivityLog,
    OrganizationModule,
    OrganizationProductEntitlement,
    ProductSystem,
)


class ProductSystemSerializer(serializers.ModelSerializer):
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = ProductSystem
        fields = [
            'id', 'code', 'name', 'slug', 'description', 'product_type', 'status',
            'billing_enabled', 'default_plan', 'launch_url', 'api_base_url',
            'icon', 'metadata', 'is_available', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductSystemListSerializer(serializers.ModelSerializer):
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = ProductSystem
        fields = [
            'id', 'code', 'name', 'slug', 'product_type', 'status',
            'billing_enabled', 'icon', 'is_available',
        ]


class OrganizationProductEntitlementSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_code = serializers.CharField(source='organization.code', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    subscription_status = serializers.CharField(source='subscription.status', read_only=True, default=None)
    billing_status = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    activated_by_name = serializers.CharField(source='activated_by.full_name', read_only=True, default=None)

    class Meta:
        model = OrganizationProductEntitlement
        fields = [
            'id', 'organization', 'organization_name', 'organization_code',
            'product', 'product_code', 'product_name', 'enabled', 'plan',
            'subscription', 'subscription_status', 'billing_status', 'status',
            'starts_at', 'ends_at', 'suspended_at', 'suspension_reason',
            'modules_enabled', 'scopes', 'metadata', 'activated_by',
            'activated_by_name', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'activated_by', 'created_at', 'updated_at']

    def get_billing_status(self, obj):
        subscription = obj.subscription or getattr(obj.organization, 'subscription', None)
        if not subscription:
            return 'not_configured'
        return subscription.status


class OrganizationProductEntitlementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationProductEntitlement
        fields = [
            'organization', 'product', 'enabled', 'plan', 'subscription',
            'status', 'starts_at', 'ends_at', 'modules_enabled', 'scopes', 'metadata',
        ]

    def validate(self, attrs):
        if OrganizationProductEntitlement.objects.filter(
            organization=attrs.get('organization'),
            product=attrs.get('product'),
        ).exists():
            raise serializers.ValidationError(
                'La organizacion ya tiene configurado este producto.'
            )
        return attrs


class OrganizationProductEntitlementToggleSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['enable', 'disable', 'trial'])
    reason = serializers.CharField(required=False, allow_blank=True)
    trial_days = serializers.IntegerField(required=False, default=14, min_value=1, max_value=365)


class ISOStandardSerializer(serializers.ModelSerializer):
    """Serializer para estándares ISO"""
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = ISOStandard
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ISOStandardListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    
    class Meta:
        model = ISOStandard
        fields = [
            'id', 'code', 'name', 'version', 'status', 
            'is_base', 'monthly_price', 'icon', 'color', 'display_order'
        ]


class OrganizationModuleSerializer(serializers.ModelSerializer):
    """Serializer para módulos asignados a organizaciones"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_code = serializers.CharField(source='organization.code', read_only=True)
    iso_code = serializers.CharField(source='iso_standard.code', read_only=True)
    iso_name = serializers.CharField(source='iso_standard.name', read_only=True)
    is_active = serializers.ReadOnlyField()
    activated_by_name = serializers.CharField(source='activated_by.full_name', read_only=True, default=None)
    
    class Meta:
        model = OrganizationModule
        fields = '__all__'
        read_only_fields = ['id', 'activated_at', 'created_at', 'updated_at']


class OrganizationModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer para asignar módulos a organizaciones"""
    
    class Meta:
        model = OrganizationModule
        fields = ['organization', 'iso_standard', 'status', 'expires_at', 'internal_notes']
    
    def validate(self, attrs):
        # Verificar que no exista ya esta combinación
        org = attrs.get('organization')
        iso = attrs.get('iso_standard')
        
        if OrganizationModule.objects.filter(organization=org, iso_standard=iso).exists():
            raise serializers.ValidationError(
                f"La organización ya tiene asignado el módulo {iso.code}"
            )
        return attrs


class OrganizationModuleToggleSerializer(serializers.Serializer):
    """Serializer para activar/desactivar módulos"""
    action = serializers.ChoiceField(choices=['enable', 'disable', 'trial'])
    reason = serializers.CharField(required=False, allow_blank=True)
    trial_days = serializers.IntegerField(required=False, default=14, min_value=1, max_value=90)


class ModuleActivityLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de actividad"""
    performed_by_name = serializers.CharField(source='performed_by.full_name', read_only=True, default='Sistema')
    organization_name = serializers.CharField(source='organization_module.organization.name', read_only=True)
    iso_code = serializers.CharField(source='organization_module.iso_standard.code', read_only=True)
    
    class Meta:
        model = ModuleActivityLog
        fields = '__all__'


class OrganizationModulesOverviewSerializer(serializers.Serializer):
    """Resumen de módulos de una organización"""
    organization_id = serializers.UUIDField()
    organization_name = serializers.CharField()
    total_modules = serializers.IntegerField()
    active_modules = serializers.IntegerField()
    trial_modules = serializers.IntegerField()
    suspended_modules = serializers.IntegerField()
    modules = OrganizationModuleSerializer(many=True)
