"""
Serializers for Users - Admin Apps
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, UserOrganization, UserSession, UserActivityLog


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para JWT con datos adicionales"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar claims personalizados
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['role'] = user.role
        if user.organization:
            token['organization_id'] = str(user.organization.id)
            token['organization_name'] = user.organization.name
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Verificar si la cuenta está bloqueada
        if self.user.is_locked:
            raise serializers.ValidationError(
                'Cuenta bloqueada temporalmente. Intente más tarde.'
            )
        
        # Registrar login
        self.user.record_login()
        
        # Agregar datos adicionales a la respuesta
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'full_name': self.user.full_name,
            'role': self.user.role,
            'organization_id': str(self.user.organization.id) if self.user.organization else None,
            'organization_name': self.user.organization.name if self.user.organization else None,
            'theme': self.user.theme,
            'must_change_password': self.user.must_change_password,
        }
        
        return data


class UserListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listados"""
    organization_name = serializers.CharField(source='organization.name', read_only=True, default=None)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'organization_name', 'is_active', 'last_login_at', 'created_at'
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle"""
    organization_name = serializers.CharField(source='organization.name', read_only=True, default=None)
    full_name = serializers.ReadOnlyField()
    is_locked = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'avatar', 'organization', 'organization_name',
            'role', 'job_title', 'department',
            'is_active', 'is_staff', 'is_verified', 'is_locked', 'must_change_password',
            'language', 'timezone', 'theme',
            'email_notifications', 'push_notifications',
            'last_login_at', 'last_activity_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_staff', 'is_verified', 'is_locked',
            'last_login_at', 'last_activity_at', 'created_at', 'updated_at'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
            'organization', 'role', 'job_title', 'department'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.must_change_password = True
        user.set_password(password)
        user.save()
        
        # Si tiene organización, crear membresía
        if user.organization:
            UserOrganization.objects.create(
                user=user,
                organization=user.organization,
                role=user.role,
                is_primary=True
            )
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar usuarios"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone',
            'role', 'job_title', 'department',
            'is_active', 'language', 'timezone', 'theme',
            'email_notifications', 'push_notifications'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para que el usuario actualice su propio perfil"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'avatar',
            'job_title', 'department',
            'language', 'timezone', 'theme',
            'email_notifications', 'push_notifications'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Contraseña actual incorrecta')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer para solicitar reset de contraseña"""
    email = serializers.EmailField(required=True)


class ResetPasswordConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar reset de contraseña"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs


class UserOrganizationSerializer(serializers.ModelSerializer):
    """Serializer para membresías de organización"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserOrganization
        fields = '__all__'
        read_only_fields = ['id', 'joined_at', 'updated_at']


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer para sesiones de usuario"""
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'ip_address', 'device_type', 'browser', 'os',
            'is_active', 'created_at', 'last_activity_at', 'expires_at'
        ]


class UserActivityLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de actividad"""
    user_email = serializers.CharField(source='user.email', read_only=True, default='Sistema')
    organization_name = serializers.CharField(source='organization.name', read_only=True, default=None)
    
    class Meta:
        model = UserActivityLog
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro público"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    invitation_token = serializers.CharField(required=False, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
            'invitation_token'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email ya está registrado')
        return value
    
    def create(self, validated_data):
        invitation_token = validated_data.pop('invitation_token', None)
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.must_change_password = True
        user.set_password(password)
        
        # Procesar invitación si existe
        if invitation_token:
            from apps.organizations.models import OrganizationInvitation
            try:
                invitation = OrganizationInvitation.objects.get(
                    token=invitation_token,
                    status='pending'
                )
                user.organization = invitation.organization
                user.role = invitation.role
                user.is_verified = True
                
                # Marcar invitación como aceptada
                from django.utils import timezone
                invitation.status = 'accepted'
                invitation.accepted_at = timezone.now()
                invitation.save()
            except OrganizationInvitation.DoesNotExist:
                pass
        
        user.save()
        
        # Crear membresía si tiene organización
        if user.organization:
            UserOrganization.objects.create(
                user=user,
                organization=user.organization,
                role=user.role,
                is_primary=True
            )
        
        return user
