"""
Serializers de Usuarios
"""
from rest_framework import serializers
from .models import User, OrganizationMembership


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    organization_id = serializers.IntegerField(required=False, allow_null=True)


class UserSerializer(serializers.ModelSerializer):
    """Serializer de usuario"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'uuid', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'avatar', 'is_platform_admin',
            'language', 'timezone',
            'email_verified', 'must_change_password',
            'created_at', 'last_login_at',
        ]
        read_only_fields = ['id', 'uuid', 'email_verified', 'created_at', 'last_login_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    organization_id = serializers.IntegerField(write_only=True, required=False)
    role = serializers.CharField(write_only=True, required=False, default='user')
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name',
            'phone', 'organization_id', 'role',
        ]
    
    def create(self, validated_data):
        organization_id = validated_data.pop('organization_id', None)
        role = validated_data.pop('role', 'user')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Crear membresía si se especificó organización
        if organization_id:
            from organizations.models import Organization
            try:
                org = Organization.objects.get(pk=organization_id)
                OrganizationMembership.objects.create(
                    user=user,
                    organization=org,
                    role=role,
                    is_primary=True,
                    invited_by=self.context['request'].user
                )
            except Organization.DoesNotExist:
                pass
        
        return user


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer de membresía"""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = OrganizationMembership
        fields = [
            'id', 'user', 'user_email', 'organization', 'organization_name',
            'role', 'job_title', 'department',
            'is_primary', 'is_active',
            'joined_at', 'updated_at',
        ]
        read_only_fields = ['id', 'joined_at', 'updated_at']
