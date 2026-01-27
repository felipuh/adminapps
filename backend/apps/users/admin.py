from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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


@admin.register(UserOrganization)
class UserOrganizationAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_primary', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'is_primary']
    search_fields = ['user__email', 'organization__name']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'device_type', 'browser', 'is_active', 'created_at']
    list_filter = ['is_active', 'device_type']
    search_fields = ['user__email', 'ip_address']


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'entity_type', 'created_at']
    list_filter = ['action', 'module']
    search_fields = ['user__email', 'description']
    readonly_fields = ['id', 'created_at']
