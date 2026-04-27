"""
URLs for API - Admin Apps
"""
from django.urls import path
from .views import HealthCheckView, DashboardView, SystemStatsView, QuickActionsView, LandingAnalyticsSummaryView, FeatureFlagsView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('stats/', SystemStatsView.as_view(), name='system_stats'),
    path('quick-actions/', QuickActionsView.as_view(), name='quick_actions'),
    path('analytics/landing/', LandingAnalyticsSummaryView.as_view(), name='landing_analytics_summary'),
    path('feature-flags/', FeatureFlagsView.as_view(), name='feature_flags'),
]
