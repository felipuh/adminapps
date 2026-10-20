"""
Serializers for Products - Admin Apps
Control de módulos ISO
"""
from apps.users.api_authorization import StrictInputMixin, reject_reparenting

from rest_framework import serializers
from apps.integration.authorization_contract import CATALOG
from apps.organizations.models import Organization
from .models import (
    ISOStandard,
    ModuleActivityLog,
    OrganizationModule,
    OrganizationProductEntitlement,
    ProductEntitlementAuditLog,
    ProductSystem,
)


def validate_entitlement_relations(instance, attrs):
    reject_reparenting(instance, attrs, ('organization', 'product'))
    organization = attrs.get('organization') or getattr(instance, 'organization', None)
    product = attrs.get('product') or getattr(instance, 'product', None)
    subscription = attrs.get('subscription', getattr(instance, 'subscription', None))
    if subscription and (not organization or subscription.pk != organization.subscription_id):
        raise serializers.ValidationError({'subscription': 'Suscripción ajena a la relación canónica del tenant.'})
    if 'scopes' in attrs:
        scopes = attrs['scopes']
        catalog = CATALOG.get(getattr(product, 'code', None), ())
        if (not isinstance(scopes, list) or any(not isinstance(s, str) or s not in catalog for s in scopes)
                or len(set(scopes)) != len(scopes)):
            raise serializers.ValidationError({'scopes': 'Scopes inválidos o ajenos al producto.'})


class ProductSystemSerializer(StrictInputMixin, serializers.ModelSerializer):
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
            'billing_enabled', 'default_plan', 'description', 'launch_url',
            'api_base_url', 'icon', 'is_available',
        ]


class OrganizationProductEntitlementSerializer(StrictInputMixin, serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_code = serializers.CharField(source='organization.code', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True, default=None)
    plan_code = serializers.CharField(source='plan.code', read_only=True, default=None)
    effective_plan = serializers.SerializerMethodField()
    effective_plan_name = serializers.SerializerMethodField()
    effective_plan_code = serializers.SerializerMethodField()
    subscription_status = serializers.CharField(source='subscription.status', read_only=True, default=None)
    billing_status = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    access_allowed = serializers.ReadOnlyField()
    access_denial_reason = serializers.ReadOnlyField()
    activated_by_name = serializers.CharField(source='activated_by.full_name', read_only=True, default=None)

    class Meta:
        model = OrganizationProductEntitlement
        fields = [
            'id', 'organization', 'organization_name', 'organization_code',
            'product', 'product_code', 'product_name', 'enabled', 'plan',
            'plan_name', 'plan_code', 'effective_plan', 'effective_plan_name',
            'effective_plan_code', 'subscription', 'subscription_status',
            'billing_status', 'status',
            'starts_at', 'ends_at', 'suspended_at', 'suspension_reason',
            'modules_enabled', 'scopes', 'metadata', 'activated_by',
            'activated_by_name', 'is_active', 'access_allowed',
            'access_denial_reason', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'activated_by', 'created_at', 'updated_at']

    def get_billing_status(self, obj):
        subscription = obj.subscription or getattr(obj.organization, 'subscription', None)
        if not subscription:
            return 'not_configured'
        return subscription.status

    def get_effective_plan(self, obj):
        plan = obj.effective_plan
        return str(plan.id) if plan else None

    def get_effective_plan_name(self, obj):
        plan = obj.effective_plan
        return plan.name if plan else None

    def get_effective_plan_code(self, obj):
        plan = obj.effective_plan
        return plan.code if plan else None

    def validate(self, attrs):
        validate_entitlement_relations(self.instance, attrs)
        organization = attrs.get('organization') or getattr(self.instance, 'organization', None)
        product = attrs.get('product') or getattr(self.instance, 'product', None)
        subscription = attrs.get('subscription')
        if subscription is None and self.instance is not None:
            subscription = self.instance.subscription
        subscription = subscription or getattr(organization, 'subscription', None)
        status = attrs.get('status', getattr(self.instance, 'status', None))
        enabled = attrs.get('enabled', getattr(self.instance, 'enabled', True))

        if product and product.billing_enabled and enabled and status == 'active':
            if not subscription:
                raise serializers.ValidationError({
                    'subscription': 'Un producto con billing activo requiere suscripcion efectiva para activarse.'
                })
            if not subscription.is_active:
                raise serializers.ValidationError({
                    'subscription': 'La suscripcion efectiva no permite activar este producto.'
                })
        return attrs


class OrganizationProductEntitlementCreateSerializer(StrictInputMixin, serializers.ModelSerializer):
    class Meta:
        model = OrganizationProductEntitlement
        fields = [
            'organization', 'product', 'enabled', 'plan', 'subscription',
            'status', 'starts_at', 'ends_at', 'modules_enabled', 'scopes', 'metadata',
        ]

    def validate(self, attrs):
        validate_entitlement_relations(self.instance, attrs)
        if OrganizationProductEntitlement.objects.filter(
            organization=attrs.get('organization'),
            product=attrs.get('product'),
        ).exists():
            raise serializers.ValidationError(
                'La organizacion ya tiene configurado este producto.'
            )
        product = attrs.get('product')
        organization = attrs.get('organization')
        subscription = attrs.get('subscription') or getattr(organization, 'subscription', None)
        status = attrs.get('status', 'trial')
        enabled = attrs.get('enabled', True)
        if product and product.billing_enabled and enabled and status == 'active':
            if not subscription:
                raise serializers.ValidationError({
                    'subscription': 'Un producto con billing activo requiere suscripcion efectiva para activarse.'
                })
            if not subscription.is_active:
                raise serializers.ValidationError({
                    'subscription': 'La suscripcion efectiva no permite activar este producto.'
                })
        return attrs


class ProductEntitlementAuditLogSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_code = serializers.CharField(source='organization.code', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    actor_name = serializers.CharField(source='actor.full_name', read_only=True, default=None)

    class Meta:
        model = ProductEntitlementAuditLog
        fields = [
            'id', 'entitlement', 'organization', 'organization_name',
            'organization_code', 'product', 'product_code', 'product_name',
            'action', 'previous_state', 'new_state', 'actor', 'actor_name',
            'metadata', 'created_at',
        ]
        read_only_fields = fields


class OrganizationProductEntitlementToggleSerializer(StrictInputMixin, serializers.Serializer):
    action = serializers.ChoiceField(choices=['enable', 'disable', 'trial'])
    reason = serializers.CharField(required=False, allow_blank=True)
    trial_days = serializers.IntegerField(required=False, default=14, min_value=1, max_value=365)


class ISOStandardSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer para estándares ISO"""
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = ISOStandard
        fields = [
            'id', 'code', 'name', 'full_name', 'version', 'description',
            'icon', 'color', 'status', 'is_base', 'monthly_price',
            'annual_price', 'display_order', 'clauses_count', 'metadata',
            'released_at', 'is_available', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ISOStandardListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    
    class Meta:
        model = ISOStandard
        fields = [
            'id', 'code', 'name', 'version', 'status', 
            'is_base', 'monthly_price', 'icon', 'color', 'display_order'
        ]


class OrganizationModuleSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer para módulos asignados a organizaciones"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_code = serializers.CharField(source='organization.code', read_only=True)
    iso_code = serializers.CharField(source='iso_standard.code', read_only=True)
    iso_name = serializers.CharField(source='iso_standard.name', read_only=True)
    is_active = serializers.ReadOnlyField()
    activated_by_name = serializers.CharField(source='activated_by.full_name', read_only=True, default=None)
    
    class Meta:
        model = OrganizationModule
        fields = [
            'id', 'organization', 'organization_name', 'organization_code',
            'iso_standard', 'iso_code', 'iso_name', 'status', 'is_enabled',
            'is_active', 'activated_at', 'expires_at', 'suspended_at',
            'activated_by', 'activated_by_name', 'internal_notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'activated_by', 'activated_at', 'created_at', 'updated_at']

    def validate(self, attrs):
        reject_reparenting(self.instance, attrs, ('organization', 'iso_standard'))
        return attrs


class OrganizationModuleCreateSerializer(StrictInputMixin, serializers.ModelSerializer):
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


class OrganizationModuleToggleSerializer(StrictInputMixin, serializers.Serializer):
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
        fields = [
            'id', 'organization_module', 'organization_name', 'iso_code',
            'action', 'performed_by', 'performed_by_name', 'notes',
            'metadata', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class OrganizationModulesOverviewSerializer(serializers.Serializer):
    """Resumen de módulos de una organización"""
    organization_id = serializers.UUIDField()
    organization_name = serializers.CharField()
    total_modules = serializers.IntegerField()
    active_modules = serializers.IntegerField()
    trial_modules = serializers.IntegerField()
    suspended_modules = serializers.IntegerField()
    modules = OrganizationModuleSerializer(many=True)


class OrganizationModuleBulkSerializer(StrictInputMixin, serializers.Serializer):
    organization_id = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    iso_standards = serializers.PrimaryKeyRelatedField(queryset=ISOStandard.objects.all(), many=True, allow_empty=False)
    status = serializers.ChoiceField(choices=['active', 'trial', 'suspended', 'expired'], default='trial')

    def validate_iso_standards(self, values):
        if len({value.pk for value in values}) != len(values):
            raise serializers.ValidationError('No se permiten módulos duplicados.')
        return values
