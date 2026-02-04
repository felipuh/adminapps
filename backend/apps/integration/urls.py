"""
URLs de Integración para Admin Apps
"""
from django.urls import path
from . import views

app_name = 'integration'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health-check'),
    
    # Organizaciones
    path('organizations/', views.list_organizations, name='list-organizations'),
    path('organizations/<uuid:org_id>/', views.get_organization, name='get-organization'),
    path('organizations/<uuid:org_id>/users/', views.get_organization_users, name='get-organization-users'),
    path('organizations/<uuid:org_id>/modules/', views.get_organization_modules, name='get-organization-modules'),
    
    # Validación de credenciales
    path('validate-credentials/', views.validate_credentials, name='validate-credentials'),
    
    # Usuarios
    path('user/', views.get_user_by_id, name='get-user'),
]
