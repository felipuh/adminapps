"""
URLs de Integración para Admin Apps
"""
from django.urls import path
from . import views
from . import sso_views

app_name = 'integration'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health-check'),
    
    # Organizaciones
    path('organizations/', views.list_organizations, name='list-organizations'),
    path('organizations/<uuid:org_id>/', views.get_organization, name='get-organization'),
    path('organizations/<uuid:org_id>/users/', views.get_organization_users, name='get-organization-users'),
    path('organizations/<uuid:org_id>/modules/', views.get_organization_modules, name='get-organization-modules'),
    path('organizations/<uuid:org_id>/products/', views.get_organization_products, name='get-organization-products'),
    path(
        'organizations/<uuid:org_id>/products/<str:product_code>/validate/',
        views.validate_organization_product_access,
        name='validate-organization-product-access',
    ),
    
    # Validación de credenciales
    path('validate-credentials/', views.validate_credentials, name='validate-credentials'),

    # Smart3AI centralized SSO
    path('sso/login/', sso_views.sso_login, name='sso-login'),
    path('sso/login/verify-2fa/', sso_views.sso_login_verify_2fa, name='sso-login-verify-2fa'),
    path('sso/introspect/', sso_views.sso_introspect, name='sso-introspect'),
    
    # Usuarios
    path('user/', views.get_user_by_id, name='get-user'),

    # Analítica de landing Smart3AI
    path('landing-analytics/events/', views.ingest_landing_analytics, name='landing-analytics-events'),
    path('landing-analytics/summary/', views.landing_analytics_summary, name='landing-analytics-summary'),
]
