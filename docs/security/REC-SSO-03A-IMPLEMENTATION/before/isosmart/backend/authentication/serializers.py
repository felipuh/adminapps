"""
Serializers de Autenticación para ISO Smart
"""

from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import FieldError
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from django.utils import timezone
from .models import PasswordResetToken, User, UserProfile
from core.models import Organization
from integration.client import admin_apps_client


PASSWORD_REUSE_REASON_CODE = 'PASSWORD_REUSE_RECENT'
TEMP_PASSWORD_EXPIRED_REASON_CODE = 'TEMP_PASSWORD_EXPIRED'


def _is_password_reused(user, raw_password):
    if check_password(raw_password, user.password):
        return True

    for previous_hash in (user.password_history or []):
        if previous_hash and check_password(raw_password, previous_hash):
            return True
    return False


class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'must_change_password', 'last_login', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil de usuario en una organización"""
    
    user = UserSerializer(read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'organization', 'organization_name',
            'role', 'role_display', 'job_title', 'department',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoginSerializer(serializers.Serializer):
    """Serializer para el login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    organization_id = serializers.CharField(required=False, allow_null=True)

    _ROLE_MAP = {
        'superadmin': 'org_admin',
        'admin': 'org_admin',
        'org_admin': 'org_admin',
        'iso_manager': 'iso_manager',
        'auditor': 'auditor',
        'user': 'user',
        'viewer': 'viewer',
    }

    def _map_role(self, role):
        return self._ROLE_MAP.get(str(role or '').strip().lower(), 'user')

    def _unique_slug(self, base_slug):
        candidate = (base_slug or '').strip() or 'organization'
        if not Organization.objects.filter(slug=candidate).exists():
            return candidate

        suffix = 2
        while True:
            with_suffix = f"{candidate}-{suffix}"
            if not Organization.objects.filter(slug=with_suffix).exists():
                return with_suffix
            suffix += 1

    def _sync_profiles_from_adminapps(self, user, admin_apps_data):
        organizations = list(admin_apps_data.get('organizations') or [])
        if not organizations:
            return

        default_role = admin_apps_data.get('role')

        for org_item in organizations:
            candidate_external_ids = []
            for key in ('uuid', 'external_id', 'id'):
                value = org_item.get(key)
                if value is not None:
                    candidate_external_ids.append(str(value))

            if not candidate_external_ids:
                continue

            organization = Organization.objects.filter(
                external_id__in=candidate_external_ids
            ).first()

            if not organization:
                org_slug = slugify(org_item.get('slug') or org_item.get('name') or '')
                if org_slug:
                    organization = Organization.objects.filter(slug=org_slug).first()

            if not organization:
                org_name = (org_item.get('name') or '').strip() or f"Org {candidate_external_ids[0]}"
                org_slug = self._unique_slug(slugify(org_item.get('slug') or org_name))
                organization = Organization.objects.create(
                    external_id=candidate_external_ids[0],
                    name=org_name,
                    slug=org_slug,
                    is_active=True,
                )
            elif organization.external_id not in candidate_external_ids:
                # Keep external IDs aligned with AdminApps so tenant filters match.
                organization.external_id = candidate_external_ids[0]
                organization.save(update_fields=['external_id'])

            if not organization.is_active:
                organization.is_active = True
                organization.save(update_fields=['is_active'])

            mapped_role = self._map_role(org_item.get('role') or default_role)
            UserProfile.objects.update_or_create(
                user=user,
                organization=organization,
                defaults={
                    'role': mapped_role,
                    'is_active': True,
                },
            )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        organization_id = attrs.get('organization_id')
        organization = None

        _INVALID_CREDENTIALS_MSG = 'Credenciales inválidas o cuenta temporalmente bloqueada.'
        max_attempts = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
        lockout_minutes = getattr(settings, 'LOGIN_LOCKOUT_MINUTES', 15)

        if email and password:
            # Look up user for lockout check before calling authenticate().
            # Some environments may run with pending auth migrations; fail closed
            # (invalid credentials) instead of bubbling DB field errors as 500.
            try:
                candidate = User.objects.get(email=email)
            except User.DoesNotExist:
                candidate = None
            except FieldError:
                candidate = None
            except Exception:
                candidate = None

            if candidate:
                try:
                    is_locked = candidate.is_locked()
                except Exception:
                    # If schema is outdated (missing lockout fields), avoid 500.
                    is_locked = False

                if is_locked:
                    raise serializers.ValidationError(_INVALID_CREDENTIALS_MSG, code='account_locked')

            if organization_id:
                try:
                    organization = Organization.objects.get(id=int(organization_id))
                except (ValueError, Organization.DoesNotExist):
                    organization = Organization.objects.filter(external_id=organization_id).first()

            external_org_id = organization.external_id if organization else organization_id

            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password,
                organization_id=external_org_id
            )

            if not user:
                if candidate:
                    try:
                        candidate.record_failed_login(
                            max_attempts=max_attempts, lockout_minutes=lockout_minutes
                        )
                    except Exception:
                        # Ignore lockout bookkeeping errors when DB is not fully migrated.
                        pass
                raise serializers.ValidationError(_INVALID_CREDENTIALS_MSG, code='authorization')

            if not user.is_active:
                raise serializers.ValidationError(
                    'Esta cuenta ha sido desactivada.',
                    code='authorization'
                )

            request_obj = self.context.get('request')
            request_host = ''
            if request_obj:
                try:
                    request_host = request_obj.get_host().split(':')[0].strip().lower()
                except Exception:
                    request_host = ''
            local_auth_bypass_hosts = {
                str(host).strip().lower()
                for host in getattr(settings, 'LOCAL_AUTH_BYPASS_HOSTS', set())
                if str(host).strip()
            }
            is_local_request = request_host in local_auth_bypass_hosts
            bypass_header_enabled = bool(
                request_obj
                and str(request_obj.headers.get('X-ISO-LOCAL-AUTH-BYPASS', '')).strip() == '1'
                and getattr(settings, 'DEBUG', False)
            )
            bypass_flag_enabled = bool(
                getattr(settings, 'ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS', False)
                and is_local_request
            )
            allow_local_bypass = bypass_header_enabled or bypass_flag_enabled

            # Reject local-backend-only logins unless controlled local bypass is explicitly enabled.
            request_obj = self.context.get('request')
            admin_apps_data = getattr(request_obj, 'admin_apps_data', None) if request_obj else None
            if not admin_apps_data:
                if not allow_local_bypass:
                    raise serializers.ValidationError(
                        'No fue posible validar tu acceso contra AdminApps. Contacta al administrador.',
                        code='authorization'
                    )

                # Local bypass for testing: synthesize AdminApps-like payload from active local profiles.
                local_profiles = UserProfile.objects.filter(
                    user=user,
                    is_active=True,
                    organization__is_active=True,
                ).select_related('organization')

                local_orgs = []
                for local_profile in local_profiles:
                    local_org = local_profile.organization
                    local_orgs.append({
                        'id': local_org.external_id,
                        'name': local_org.name,
                        'slug': local_org.slug,
                    })

                selected_org = organization.external_id if organization else None
                current_org = next(
                    (org_item for org_item in local_orgs if selected_org and org_item.get('id') == selected_org),
                    local_orgs[0] if local_orgs else {},
                )

                admin_apps_data = {
                    'user': {
                        'id': user.id,
                        'email': user.email,
                    },
                    'organization': current_org,
                    'organizations': local_orgs,
                    'role': None,
                }

                if request_obj is not None:
                    request_obj.admin_apps_data = admin_apps_data

            # Owner policy: only Smart3AI organization can authenticate in ISO Smart.
            if getattr(settings, 'OWNER_ORGANIZATION_ONLY_ACCESS', False) and not allow_local_bypass:
                owner_slug = (getattr(settings, 'OWNER_ORGANIZATION_SLUG', '') or '').strip().lower()
                owner_name = (getattr(settings, 'OWNER_ORGANIZATION_NAME', '') or '').strip().lower()
                owner_external_id = (getattr(settings, 'OWNER_ORGANIZATION_EXTERNAL_ID', '') or '').strip()

                candidate_orgs = list(admin_apps_data.get('organizations') or [])
                current_org = admin_apps_data.get('organization') or {}
                if current_org:
                    candidate_orgs.append(current_org)

                def _is_owner_org(org_item):
                    org_slug = str(org_item.get('slug') or '').strip().lower()
                    org_name = str(org_item.get('name') or '').strip().lower()
                    org_id = str(org_item.get('id') or '').strip()

                    if owner_external_id and org_id == owner_external_id:
                        return True
                    if owner_slug and org_slug == owner_slug:
                        return True
                    if owner_name and org_name == owner_name:
                        return True
                    return False

                if not any(_is_owner_org(org_item) for org_item in candidate_orgs):
                    raise serializers.ValidationError(
                        'Solo la organizacion Smart3AI tiene acceso a esta instancia de ISO Smart.',
                        code='authorization'
                    )

            # Successful authentication — clear any previous failures
            try:
                user.reset_login_attempts()
            except Exception:
                # Ignore bookkeeping errors when lockout columns are missing.
                pass

            try:
                temporary_expiry = user.get_temporary_password_expiry()
            except Exception:
                temporary_expiry = None
            if temporary_expiry and timezone.now() >= temporary_expiry:
                raise serializers.ValidationError(
                    {
                        'detail': 'Tu contraseña temporal ha expirado. Solicita un restablecimiento con un administrador.',
                        'reason_code': TEMP_PASSWORD_EXPIRED_REASON_CODE,
                    },
                    code='authorization',
                )

            temp_password_warning = None
            if temporary_expiry:
                warning_days = max(0, int(getattr(settings, 'TEMP_PASSWORD_WARNING_DAYS', 2)))
                seconds_left = (temporary_expiry - timezone.now()).total_seconds()
                if seconds_left > 0:
                    days_left = int((seconds_left - 1) // 86400) + 1
                    if days_left <= warning_days:
                        temp_password_warning = {
                            'reason_code': 'TEMP_PASSWORD_EXPIRING',
                            'days_left': days_left,
                            'expires_at': temporary_expiry,
                        }
            
            allowed_external_org_ids = set()
            for org in (admin_apps_data.get('organizations') or []):
                for key in ('id', 'uuid', 'external_id'):
                    value = org.get(key)
                    if value is not None:
                        allowed_external_org_ids.add(str(value))

            # Obtener perfiles locales solo para organizaciones vigentes en AdminApps
            profiles = UserProfile.objects.filter(
                user=user,
                is_active=True,
                organization__is_active=True,
            )
            if allowed_external_org_ids:
                profiles = profiles.filter(organization__external_id__in=allowed_external_org_ids)

            if not profiles.exists() and (admin_apps_data.get('organizations') or []):
                self._sync_profiles_from_adminapps(user, admin_apps_data)
                profiles = UserProfile.objects.filter(
                    user=user,
                    is_active=True,
                    organization__is_active=True,
                )
                if allowed_external_org_ids:
                    profiles = profiles.filter(organization__external_id__in=allowed_external_org_ids)
            
            if not profiles.exists():
                raise serializers.ValidationError(
                    'No tienes acceso a ninguna organización.',
                    code='authorization'
                )
            
            # Si se especifica organización, verificar acceso
            if organization_id:
                if not organization:
                    organization = Organization.objects.filter(external_id=organization_id).first()

                if organization:
                    profile = profiles.filter(organization_id=organization.id).first()
                else:
                    profile = None

                if not profile:
                    raise serializers.ValidationError(
                        'No tienes acceso a esta organización.',
                        code='authorization'
                    )
            else:
                # Preferir la organización activa reportada por AdminApps.
                current_org = admin_apps_data.get('organization') or {}
                current_external_id = (
                    current_org.get('uuid')
                    or current_org.get('external_id')
                    or current_org.get('id')
                )
                if current_external_id is not None:
                    profile = profiles.filter(organization__external_id=current_external_id).first()
                else:
                    profile = None

                if not profile:
                    profile = profiles.first()

            product_code = getattr(settings, 'ISO_SMART_PRODUCT_CODE', 'ISO_SMART')
            product_access = admin_apps_client.validate_product_access(
                profile.organization_id,
                product_code,
                use_cache=False,
                allow_local_fallback=allow_local_bypass,
            )
            if request_obj is not None:
                request_obj.admin_apps_product_access = product_access
                admin_apps_data['product_access'] = product_access

            if not product_access.get('allowed'):
                denial_reason = product_access.get('reason') or product_access.get('code') or 'product_access_denied'
                raise serializers.ValidationError(
                    denial_reason,
                    code='authorization'
                )
            
            attrs['user'] = user
            attrs['profile'] = profile
            attrs['temp_password_warning'] = temp_password_warning
            
        else:
            raise serializers.ValidationError(
                'Debes proporcionar email y contraseña.',
                code='authorization'
            )
        
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    """Serializer para la respuesta de login con tokens"""
    
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    profile = UserProfileSerializer()
    organizations = serializers.ListField(child=serializers.DictField())


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer para refresh de token"""
    
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    """Serializer para logout"""
    
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value
    
    def validate_new_password(self, value):
        validate_password(value)
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })
        return attrs


class SwitchOrganizationSerializer(serializers.Serializer):
    """Serializer para cambiar de organización activa"""
    
    organization_id = serializers.IntegerField()
    
    def validate_organization_id(self, value):
        user = self.context['request'].user
        profile = UserProfile.objects.filter(
            user=user,
            organization_id=value,
            is_active=True
        ).first()
        
        if not profile:
            raise serializers.ValidationError(
                'No tienes acceso a esta organización.'
            )
        
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuarios (usado por admins)"""
    
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    organization_id = serializers.IntegerField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'password', 'confirm_password', 'organization_id', 'role'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })

        existing_user = User.objects.filter(email=attrs['email']).first()
        if existing_user:
            if _is_password_reused(existing_user, attrs['password']):
                raise serializers.ValidationError({
                    'detail': 'No puedes reutilizar una contraseña reciente en esta alta/invitación.',
                    'reason_code': PASSWORD_REUSE_REASON_CODE,
                })
            raise serializers.ValidationError({'email': 'Este correo ya está registrado.'})

        return attrs
    
    def create(self, validated_data):
        organization_id = validated_data.pop('organization_id')
        role = validated_data.pop('role')
        phone = validated_data.pop('phone', '')
        validated_data.pop('confirm_password')
        
        user = User.objects.create_user(**validated_data)
        
        # Crear perfil en la organización
        UserProfile.objects.create(
            user=user,
            organization_id=organization_id,
            role=role,
            phone=phone,
        )

        # Enforce first-login password rotation for new tenant users.
        user.mark_temporary_password()
        user.save(update_fields=['must_change_password', 'temporary_password_set_at'])
        
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer para solicitar recuperacion de contrasena."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar nueva contrasena mediante token."""

    selector = serializers.CharField()
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Las contraseñas no coinciden.'
            })

        selector = attrs['selector'].strip()
        raw_token = attrs['token'].strip()
        reset_token = PasswordResetToken.objects.filter(selector=selector).select_related('user').first()

        if not reset_token or not reset_token.is_available() or not reset_token.matches(raw_token):
            raise serializers.ValidationError({
                'token': 'El enlace de recuperación es inválido o ha expirado.'
            })

        attrs['reset_token'] = reset_token
        return attrs
