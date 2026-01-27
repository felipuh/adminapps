"""
Serializers for Organizations - Admin Apps
"""
from rest_framework import serializers
from .models import Organization, OrganizationSettings, OrganizationInvitation


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSettings
        exclude = ['organization']


class OrganizationListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    users_count = serializers.ReadOnlyField()
    subscription_name = serializers.CharField(source='subscription.plan.name', read_only=True, default=None)
    
    class Meta:
        model = Organization
        fields = [
            'id', 'code', 'name', 'email', 'industry', 'size',
            'status', 'users_count', 'max_users', 'subscription_name',
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
    
    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ['id', 'code', 'created_at', 'updated_at']


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear organizaciones"""
    
    class Meta:
        model = Organization
        fields = [
            'name', 'legal_name', 'tax_id', 'email', 'phone', 'website',
            'address', 'city', 'state', 'country', 'postal_code',
            'industry', 'size', 'employees_count', 'iso_standards', 'notes'
        ]
    
    def create(self, validated_data):
        organization = Organization.objects.create(**validated_data)
        # Crear settings por defecto
        OrganizationSettings.objects.create(organization=organization)
        return organization


class OrganizationUpdateSerializer(serializers.ModelSerializer):
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


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.full_name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = OrganizationInvitation
        fields = '__all__'
        read_only_fields = ['id', 'token', 'status', 'invited_by', 'created_at', 'accepted_at']


class OrganizationInvitationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation
        fields = ['organization', 'email', 'role', 'message']
    
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
