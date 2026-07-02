"""
Admin configuration for Integration module
"""
from django.contrib import admin
from .models import IntegrationAPIKey, LandingAnalyticsEvent


@admin.register(IntegrationAPIKey)
class IntegrationAPIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'last_used_at', 'last_used_service', 'created_at')
    list_filter = ('is_active', 'last_used_at', 'created_at')
    search_fields = ('name', 'key')
    readonly_fields = ('last_used_at', 'last_used_service', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'key', 'is_active')
        }),
        ('Uso', {
            'fields': ('last_used_at', 'last_used_service'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


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
