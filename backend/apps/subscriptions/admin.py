from django.contrib import admin
from .models import Plan, Subscription, Invoice, PaymentMethod


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'price', 'billing_cycle', 'max_users', 'is_active', 'is_featured']
    list_filter = ['is_active', 'is_featured', 'billing_cycle']
    search_fields = ['code', 'name']
    ordering = ['display_order', 'price']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'plan', 'status', 'current_period_start', 'current_period_end', 'created_at']
    list_filter = ['status', 'plan']
    ordering = ['-created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'organization', 'total', 'status', 'issued_at', 'due_date']
    list_filter = ['status']
    search_fields = ['number', 'organization__name']
    ordering = ['-issued_at']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['organization', 'type', 'name', 'is_default', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['organization__name', 'name']
