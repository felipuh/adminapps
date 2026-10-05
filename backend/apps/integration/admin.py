"""
Admin configuration for Integration module
"""
from django.contrib import admin
from .models import DemoRequest, IntegrationAPIKey, LandingAnalyticsEvent


@admin.register(IntegrationAPIKey)
class IntegrationAPIKeyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'credential_id',
        'credential_format',
        'fingerprint',
        'status',
        'last_used_at',
        'created_at',
    )
    list_filter = ('credential_format', 'status', 'is_active', 'created_at')
    search_fields = ('name', 'credential_id', 'fingerprint')
    fields = (
        'name',
        'credential_id',
        'credential_format',
        'fingerprint',
        'status',
        'is_active',
        'replaced_by',
        'last_used_at',
        'last_used_service',
        'created_at',
        'revoked_at',
        'rotated_at',
        'updated_at',
    )
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LandingAnalyticsEvent)
class LandingAnalyticsEventAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'event_name',
        'campaign',
        'variant',
        'intent',
        'event_date',
        'occurred_at',
    )
    list_filter = ('event_name', 'campaign', 'variant', 'intent', 'event_date')
    search_fields = ('campaign', 'session_id', 'persona', 'page_path')
    ordering = ('-occurred_at',)


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = (
        'organization_name',
        'full_name',
        'work_email',
        'product_code',
        'priority',
        'status',
        'owner',
        'created_at',
    )
    list_filter = ('status', 'product_code', 'priority', 'source', 'created_at')
    search_fields = ('organization_name', 'full_name', 'work_email', 'campaign')
    readonly_fields = (
        'id',
        'external_id',
        'source_service',
        'consent_given',
        'consented_at',
        'created_at',
        'updated_at',
    )
    ordering = ('-created_at',)
    list_select_related = ('owner',)
