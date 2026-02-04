"""
Serializers para Organizaciones
"""
from rest_framework import serializers
from .models import Organization, OrganizationInvitation


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer completo de organización"""
    
    user_count = serializers.ReadOnlyField()
    enabled_modules = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'uuid', 'name', 'slug', 'legal_name', 'tax_id',
            'email', 'phone', 'website', 'address', 'city', 'country',
            'logo', 'primary_color',
            'plan', 'status', 'max_users', 'user_count',
            'trial_ends_at', 'subscription_ends_at',
            'module_sca_enabled', 'module_sie_enabled', 'module_asb_enabled',
            'module_spm_enabled', 'module_documents_enabled', 'module_risks_enabled',
            'module_objectives_enabled', 'module_audits_enabled',
            'enabled_modules',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'uuid', 'slug', 'user_count', 'created_at', 'updated_at']
    
    def get_enabled_modules(self, obj):
        return obj.get_enabled_modules()


class OrganizationListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listados"""
    
    user_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'uuid', 'name', 'slug', 'logo',
            'plan', 'status', 'user_count',
            'created_at',
        ]


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear organizaciones"""
    
    class Meta:
        model = Organization
        fields = [
            'name', 'legal_name', 'tax_id',
            'email', 'phone', 'website', 'address', 'city', 'country',
            'plan', 'max_users',
        ]
    
    def create(self, validated_data):
        validated_data['status'] = 'trial'
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    """Serializer para invitaciones"""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    
    class Meta:
        model = OrganizationInvitation
        fields = [
            'id', 'organization', 'organization_name',
            'email', 'role', 'status',
            'invited_by', 'invited_by_name',
            'created_at', 'expires_at', 'accepted_at',
        ]
        read_only_fields = ['id', 'status', 'invited_by', 'created_at', 'accepted_at']
