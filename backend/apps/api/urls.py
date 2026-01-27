"""
URLs for API - Admin Apps
"""
from django.urls import path
from .views import HealthCheckView, DashboardView, SystemStatsView, QuickActionsView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('stats/', SystemStatsView.as_view(), name='system_stats'),
    path('quick-actions/', QuickActionsView.as_view(), name='quick_actions'),
]
