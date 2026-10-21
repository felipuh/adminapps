"""
Serializers for Organizations - Admin Apps
"""
from apps.users.api_authorization import StrictInputMixin, reject_reparenting
from apps.users.runtime_policy import restricted_runtime, check_held_fields

from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from .models import Organization, OrganizationSettings, OrganizationInvitation


def _is_billing_exempt_owner_org(organization):
    if not getattr(settings, 'BILLING_OWNER_ORG_EXEMPT_ENABLED', True):
        return False

    organization_id = str(organization.id)
    configured_id = getattr(settings, 'BILLING_OWNER_ORG_ID', '').strip()
    if configured_id and organization_id == configured_id:
        return True

    configured_code = getattr(settings, 'BILLING_OWNER_ORG_CODE', '').strip().lower()
    if configured_code and (organization.code or '').strip().lower() == configured_code:
        return True

    configured_name = getattr(settings, 'BILLING_OWNER_ORG_NAME', '').strip().lower()
    if configured_name and (organization.name or '').strip().lower() == configured_name:
        return True

    return False


class OrganizationSettingsSerializer(StrictInputMixin, serializers.ModelSerializer):
    class Meta:
        model = OrganizationSettings
        exclude = ['organization']

    def validate(self, attrs):
        actor = getattr(self.context.get('request'), 'user', None)
        privileged = {key for key in attrs if key.startswith('module_') or key == 'last_backup_at'}
        if privileged and not (actor and actor.is_staff and actor.is_admin):
            raise serializers.ValidationError({key: 'Campo reservado a plataforma.' for key in privileged})
        return attrs


class OrganizationListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    users_count = serializers.ReadOnlyField()
    subscription_name = serializers.CharField(source='subscription.plan.name', read_only=True, default=None)
    billing_exempt = serializers.SerializerMethodField()

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(obj)
    
    class Meta:
        model = Organization
        fields = [
            'id', 'code', 'name', 'email', 'industry', 'size',
            'status', 'users_count', 'max_users', 'subscription_name', 'billing_exempt',
            'created_at'
        ]


class OrganizationDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle"""
    settings = OrganizationSettingsSerializer(read_only=True)
    users_count = serializers.ReadOnlyField()
    can_add_users = serializers.ReadOnlyField()
    trial_expired = serializers.ReadOnlyField()
    subscription_expired = serializers.ReadOnlyField()
    subscription_name = serializers.CharField(source='subscription.plan.name', read_only=True, default=None)
    billing_exempt = serializers.SerializerMethodField()

    def get_billing_exempt(self, obj):
        return _is_billing_exempt_owner_org(obj)
    
    class Meta:
        model = Organization
        fields = [
            'id', 'code', 'name', 'legal_name', 'tax_id', 'email', 'phone',
            'website', 'address', 'city', 'state', 'country', 'postal_code',
            'industry', 'size', 'employees_count', 'logo', 'primary_color',
            'secondary_color', 'status', 'subscription', 'max_users',
            'max_documents', 'max_storage_mb', 'trial_ends_at',
            'subscription_ends_at', 'iso_standards', 'notes', 'metadata',
            'settings', 'users_count', 'can_add_users', 'trial_expired',
            'subscription_expired', 'subscription_name', 'billing_exempt',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']


class OrganizationCreateSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer para crear organizaciones"""
    
    class Meta:
        model = Organization
        fields = [
            'id',
            'name', 'legal_name', 'tax_id', 'email', 'phone', 'website',
            'address', 'city', 'state', 'country', 'postal_code',
            'industry', 'size', 'employees_count', 'iso_standards', 'notes'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        from .tenant_events import record_tenant_event
        request = self.context.get('request')
        actor_id = getattr(getattr(request, 'user', None), 'id', None)
        if restricted_runtime():
            # Creating tenant identity does not adjudicate a commercial trial.
            validated_data['status'] = 'inactive'
        with transaction.atomic():
            organization = Organization.objects.create(**validated_data)
            OrganizationSettings.objects.create(organization=organization)
            record_tenant_event(organization, actor_id=actor_id)
            return organization


class OrganizationUpdateSerializer(StrictInputMixin, serializers.ModelSerializer):
    """Serializer para actualizar organizaciones"""
    
    class Meta:
        model = Organization
        fields = [
            'name', 'legal_name', 'tax_id', 'email', 'phone', 'website',
            'address', 'city', 'state', 'country', 'postal_code',
            'industry', 'size', 'employees_count', 'status',
            'max_users', 'max_documents', 'max_storage_mb',
            'iso_standards', 'notes', 'metadata',
            'primary_color', 'secondary_color'
        ]

    def validate(self, attrs):
        check_held_fields(attrs, {'max_users', 'max_documents', 'max_storage_mb'})
        if restricted_runtime() and attrs.get('status') == 'trial':
            raise serializers.ValidationError({'status': 'Trials retenidos por gobernanza.'})
        return attrs

    def update(self, instance, validated_data):
        from .tenant_events import record_tenant_event
        request = self.context.get('request')
        actor_id = getattr(getattr(request, 'user', None), 'id', None)
        with transaction.atomic():
            instance = Organization.objects.select_for_update().get(pk=instance.pk)
            changed = any(getattr(instance, key) != validated_data[key]
                          for key in ('name', 'status') if key in validated_data)
            instance = super().update(instance, validated_data)
            if changed:
                record_tenant_event(instance, actor_id=actor_id)
            return instance


class OrganizationInvitationSerializer(StrictInputMixin, serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.full_name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = OrganizationInvitation
        fields = [
            'id', 'organization', 'organization_name', 'email', 'role', 'token',
            'status', 'invited_by', 'invited_by_name', 'message', 'expires_at',
            'accepted_at', 'is_expired', 'created_at',
        ]
        read_only_fields = ['id', 'token', 'status', 'invited_by', 'created_at', 'accepted_at']

    def validate(self, attrs):
        reject_reparenting(self.instance, attrs, ('organization',))
        if self.instance and self.instance.status != 'pending':
            raise serializers.ValidationError('Solo se pueden modificar invitaciones pendientes.')
        return OrganizationInvitationCreateSerializer.validate(self, attrs)


class OrganizationInvitationCreateSerializer(StrictInputMixin, serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation
        fields = ['organization', 'email', 'role', 'message']

    def validate(self, attrs):
        request = self.context.get('request')
        actor = getattr(request, 'user', None)
        if not actor or not actor.is_authenticated:
            raise serializers.ValidationError('Se requiere una sesión autenticada.')

        role = attrs.get('role', getattr(self.instance, 'role', None))
        if role == 'superadmin' and not actor.is_superadmin:
            raise serializers.ValidationError({
                'role': 'Solo un superadministrador puede asignar ese rol.'
            })
        if role == 'admin' and not actor.is_admin:
            raise serializers.ValidationError({
                'role': 'No puedes asignar roles administrativos globales.'
            })

        organization = attrs.get('organization', getattr(self.instance, 'organization', None))
        organization_id = getattr(
            organization,
            'pk',
            getattr(organization, 'id', organization),
        )
        if not actor.is_admin and str(organization_id) != str(actor.organization_id):
            raise serializers.ValidationError({
                'organization': 'No puedes crear invitaciones para otra organización.'
            })

        return attrs

    def validate_email(self, value):
        from apps.users.models import User
        # Verificar si ya existe un usuario con este email en la organización
        org = self.initial_data.get('organization')
        if User.objects.filter(email=value, organization_id=org).exists():
            raise serializers.ValidationError("Este usuario ya pertenece a la organización")
        return value


class OrganizationStatsSerializer(serializers.Serializer):
    """Estadísticas de una organización"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_documents = serializers.IntegerField()
    storage_used_mb = serializers.FloatField()
    storage_percentage = serializers.FloatField()
    risks_count = serializers.IntegerField()
    critical_risks = serializers.IntegerField()
    objectives_count = serializers.IntegerField()
    completed_objectives = serializers.IntegerField()
    last_activity = serializers.DateTimeField()
