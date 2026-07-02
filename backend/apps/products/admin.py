from django.contrib import admin
from .models import (
    ISOStandard,
    ModuleActivityLog,
    OrganizationModule,
    OrganizationProductEntitlement,
    ProductEntitlementAuditLog,
    ProductSystem,
)


@admin.register(ProductSystem)
class ProductSystemAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'slug', 'product_type', 'status', 'billing_enabled']
    list_filter = ['product_type', 'status', 'billing_enabled']
    search_fields = ['code', 'name', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(OrganizationProductEntitlement)
class OrganizationProductEntitlementAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 'product', 'status', 'enabled', 'access_allowed',
        'starts_at', 'ends_at',
    ]
    list_filter = ['status', 'enabled', 'product']
    search_fields = ['organization__name', 'organization__code', 'product__code', 'product__name']
    raw_id_fields = ['organization', 'product', 'plan', 'subscription', 'activated_by']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ProductEntitlementAuditLog)
class ProductEntitlementAuditLogAdmin(admin.ModelAdmin):
    list_display = ['organization', 'product', 'action', 'actor', 'created_at']
    list_filter = ['action', 'product', 'created_at']
    search_fields = ['organization__name', 'organization__code', 'product__code', 'product__name']
    readonly_fields = [
        'id', 'entitlement', 'organization', 'product', 'action',
        'previous_state', 'new_state', 'actor', 'metadata', 'created_at',
    ]
    raw_id_fields = ['entitlement', 'organization', 'product', 'actor']


@admin.register(ISOStandard)
class ISOStandardAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'version', 'status', 'is_base', 'monthly_price', 'display_order']
    list_filter = ['status', 'is_base']
    search_fields = ['code', 'name', 'full_name']
    ordering = ['display_order', 'code']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('code', 'name', 'full_name', 'version')
        }),
        ('Visualización', {
            'fields': ('description', 'icon', 'color', 'display_order')
        }),
        ('Estado', {
            'fields': ('status', 'is_base', 'released_at')
        }),
        ('Precios', {
            'fields': ('monthly_price', 'annual_price')
        }),
        ('Metadatos', {
            'fields': ('clauses_count', 'metadata'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrganizationModule)
class OrganizationModuleAdmin(admin.ModelAdmin):
    list_display = ['organization', 'iso_standard', 'status', 'is_enabled', 'activated_at', 'expires_at']
    list_filter = ['status', 'is_enabled', 'iso_standard']
    search_fields = ['organization__name', 'organization__code', 'iso_standard__code']
    raw_id_fields = ['organization', 'activated_by']
    readonly_fields = ['activated_at', 'created_at', 'updated_at']
    
    actions = ['enable_modules', 'disable_modules']
    
    def enable_modules(self, request, queryset):
        count = 0
        for module in queryset:
            module.enable(user=request.user)
            count += 1
        self.message_user(request, f'{count} módulos activados.')
    enable_modules.short_description = "Activar módulos seleccionados"
    
    def disable_modules(self, request, queryset):
        count = 0
        for module in queryset:
            module.disable(reason='Desactivación masiva desde admin')
            count += 1
        self.message_user(request, f'{count} módulos desactivados.')
    disable_modules.short_description = "Desactivar módulos seleccionados"


@admin.register(ModuleActivityLog)
class ModuleActivityLogAdmin(admin.ModelAdmin):
    list_display = ['organization_module', 'action', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['organization_module__organization__name', 'notes']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['organization_module', 'performed_by']
