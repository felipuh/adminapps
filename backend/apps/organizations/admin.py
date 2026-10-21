from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from apps.users.admin_authorization import RoleRestrictedAdminMixin
from .models import Organization, OrganizationSettings, OrganizationInvitation, OrganizationFeatureFlag


@admin.register(Organization)
class OrganizationAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):
    required_role = 'is_admin'

    list_display = ['code', 'name', 'email', 'industry', 'status', 'users_count', 'created_at']
    list_filter = ['status', 'industry', 'size']
    search_fields = ['code', 'name', 'email', 'legal_name']
    readonly_fields = ['id', 'code', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            and request.user.is_superadmin
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_admin:
            return queryset
        if not request.user.organization_id:
            return queryset.none()
        return queryset.filter(pk=request.user.organization_id)
    
    def users_count(self, obj):
        return obj.users.count()
    users_count.short_description = 'Usuarios'


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):
    required_role = 'is_org_admin'

    list_display = ['organization', 'theme', 'ai_auto_analysis', 'auto_backup_enabled']

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        return (
            obj is None
            or request.user.is_admin
            or obj.organization_id == request.user.organization_id
        )

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            and (
                request.user.is_admin
                or request.user.organization_id is not None
            )
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_admin:
            return queryset
        if not request.user.organization_id:
            return queryset.none()
        return queryset.filter(organization_id=request.user.organization_id)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'organization'
            and not request.user.is_admin
        ):
            kwargs['queryset'] = Organization.objects.filter(
                pk=request.user.organization_id
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not request.user.is_admin:
            if not request.user.organization_id:
                raise PermissionDenied
            obj.organization_id = request.user.organization_id
        super().save_model(request, obj, form, change)


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):
    required_role = 'is_org_admin'

    list_display = ['email', 'organization', 'role', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'role']
    search_fields = ['email', 'organization__name']
    readonly_fields = [
        'token', 'status', 'invited_by', 'expires_at', 'created_at',
        'accepted_at',
    ]

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            and (
                request.user.is_admin
                or request.user.organization_id is not None
            )
        )

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        return (
            obj is None
            or request.user.is_admin
            or obj.organization_id == request.user.organization_id
        )

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        return (
            obj is None
            or request.user.is_admin
            or obj.organization_id == request.user.organization_id
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_admin:
            return queryset
        if not request.user.organization_id:
            return queryset.none()
        return queryset.filter(organization_id=request.user.organization_id)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'organization'
            and not request.user.is_admin
        ):
            kwargs['queryset'] = Organization.objects.filter(
                pk=request.user.organization_id
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and (
            (obj.role == 'superadmin' and not request.user.is_superadmin)
            or (obj.role == 'admin' and not request.user.is_admin)
        ):
            readonly_fields.append('role')
        return tuple(dict.fromkeys(readonly_fields))

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        role_field = form.base_fields.get('role')
        if role_field:
            from apps.users.models import User
            allowed_roles = User.ROLE_CHOICES
            if not request.user.is_superadmin:
                allowed_roles = [
                    choice for choice in allowed_roles
                    if choice[0] != 'superadmin'
                ]
            if not request.user.is_admin:
                allowed_roles = [
                    choice for choice in allowed_roles
                    if choice[0] not in {'admin', 'superadmin'}
                ]
            role_field.choices = allowed_roles
        return form

    def save_model(self, request, obj, form, change):
        if not change:
            obj.invited_by = request.user
            obj.expires_at = timezone.now() + timezone.timedelta(days=7)
        role_changed = not change or 'role' in form.changed_data
        if (
            role_changed
            and obj.role == 'superadmin'
            and not request.user.is_superadmin
        ):
            raise PermissionDenied
        if (
            role_changed
            and obj.role == 'admin'
            and not request.user.is_admin
        ):
            raise PermissionDenied
        if not request.user.is_admin:
            if not request.user.organization_id:
                raise PermissionDenied
            obj.organization_id = request.user.organization_id
        super().save_model(request, obj, form, change)


@admin.register(OrganizationFeatureFlag)
class OrganizationFeatureFlagAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):
    required_role = 'is_superadmin'

    list_display = ['key', 'enabled', 'organization', 'updated_at']
    list_filter = ['enabled', 'organization']
    search_fields = ['key', 'description', 'organization__name', 'organization__code']
