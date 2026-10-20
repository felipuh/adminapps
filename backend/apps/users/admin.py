from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import PermissionDenied
from .admin_authorization import ReadOnlyAdminMixin, RoleRestrictedAdminMixin
from .models import User, UserOrganization, UserSession, UserActivityLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'organization', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'organization']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Organización', {'fields': ('organization', 'role', 'job_title', 'department')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')}),
        ('Preferencias', {'fields': ('language', 'timezone', 'theme', 'email_notifications', 'push_notifications')}),
        ('Seguridad', {'fields': ('failed_login_attempts', 'locked_until', 'must_change_password')}),
        ('Fechas', {'fields': ('last_login_at', 'last_activity_at', 'created_at', 'updated_at')}),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login_at', 'last_activity_at']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'organization', 'role'),
        }),
    )

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            and request.user.is_org_admin
            and (
                request.user.is_admin
                or request.user.organization_id is not None
            )
        )

    def has_change_permission(self, request, obj=None):
        if not super().has_change_permission(request, obj):
            return False
        if not request.user.is_org_admin:
            return False
        if not request.user.is_admin and not request.user.organization_id:
            return False
        return (
            obj is None
            or request.user.is_admin
            or obj.organization_id == request.user.organization_id
        )

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        if not request.user.is_admin:
            return False
        return obj is not None and obj.pk != request.user.pk

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_admin:
            return queryset
        if not request.user.organization_id:
            return queryset.none()
        return queryset.filter(organization_id=request.user.organization_id)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly_fields.extend(['is_staff', 'is_superuser'])
        if obj:
            readonly_fields.append('organization')
            if obj.pk == request.user.pk:
                readonly_fields.append('role')
            elif (
                obj.role == 'superadmin'
                and not request.user.is_superadmin
            ) or (
                obj.role == 'admin'
                and not request.user.is_admin
            ):
                readonly_fields.append('role')
        return tuple(dict.fromkeys(readonly_fields))

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        role_field = form.base_fields.get('role')
        if role_field:
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
        if not request.user.is_superuser and {
            'is_staff',
            'is_superuser',
        }.intersection(form.changed_data):
            raise PermissionDenied
        if not request.user.is_admin:
            if not request.user.organization_id:
                raise PermissionDenied
            obj.organization_id = request.user.organization_id
        super().save_model(request, obj, form, change)


@admin.register(UserOrganization)
class UserOrganizationAdmin(RoleRestrictedAdminMixin, admin.ModelAdmin):
    required_role = 'is_org_admin'

    list_display = ['user', 'organization', 'role', 'is_primary', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'is_primary']
    search_fields = ['user__email', 'organization__name']

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
        if obj is None:
            return request.user.is_admin or request.user.organization_id is not None
        if obj.user_id == request.user.pk:
            return False
        return (
            request.user.is_admin
            or obj.organization_id == request.user.organization_id
        )

    def has_delete_permission(self, request, obj=None):
        if not super().has_delete_permission(request, obj):
            return False
        if obj is None:
            return False
        if obj.user_id == request.user.pk:
            return False
        return (
            request.user.is_admin
            or obj.organization_id == request.user.organization_id
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_admin:
            return queryset
        if not request.user.organization_id:
            return queryset.none()
        return queryset.filter(organization_id=request.user.organization_id)

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == 'organization'
            and not request.user.is_admin
        ):
            from apps.organizations.models import Organization
            kwargs['queryset'] = Organization.objects.filter(
                pk=request.user.organization_id
            )
        elif db_field.name == 'user' and request.user.pk:
            kwargs['queryset'] = User.objects.exclude(pk=request.user.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.user_id == request.user.pk:
            raise PermissionDenied
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


@admin.register(UserSession)
class UserSessionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'device_type', 'browser', 'is_active', 'created_at']
    list_filter = ['is_active', 'device_type']
    search_fields = ['user__email', 'ip_address']


@admin.register(UserActivityLog)
class UserActivityLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'entity_type', 'created_at']
    list_filter = ['action', 'module']
    search_fields = ['user__email', 'description']
    readonly_fields = ['id', 'created_at']
