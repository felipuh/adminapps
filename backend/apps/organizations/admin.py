from django.contrib import admin
from .models import Organization, OrganizationSettings, OrganizationInvitation, OrganizationFeatureFlag


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'email', 'industry', 'status', 'users_count', 'created_at']
    list_filter = ['status', 'industry', 'size']
    search_fields = ['code', 'name', 'email', 'legal_name']
    readonly_fields = ['id', 'code', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def users_count(self, obj):
        return obj.users.count()
    users_count.short_description = 'Usuarios'


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    list_display = ['organization', 'theme', 'ai_auto_analysis', 'auto_backup_enabled']


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'organization', 'role', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'role']
    search_fields = ['email', 'organization__name']


@admin.register(OrganizationFeatureFlag)
class OrganizationFeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['key', 'enabled', 'organization', 'updated_at']
    list_filter = ['enabled', 'organization']
    search_fields = ['key', 'description', 'organization__name', 'organization__code']
