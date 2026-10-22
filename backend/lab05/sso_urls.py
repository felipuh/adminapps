"""Opt-in LAB05 SSO surface; never mounted by operational URLConfs."""
from django.urls import path
from apps.integration import sso_views

urlpatterns = [
    path('api/integration/sso/login/', sso_views.sso_login),
    path('api/integration/sso/login/verify-2fa/', sso_views.sso_login_verify_2fa),
    path('api/integration/sso/introspect/', sso_views.sso_introspect),
    path('api/integration/sso/logout/', sso_views.sso_logout),
    path('api/integration/sso/rotate/', sso_views.sso_rotate),
]
