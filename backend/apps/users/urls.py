"""
URLs for Users - Admin Apps
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    LogoutView,
    UserViewSet,
    UserNotificationViewSet,
    UserOrganizationViewSet,
    UserActivityLogViewSet,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)
from .views_2fa import (
    initiate_2fa_setup,
    verify_2fa_setup,
    verify_2fa_token,
    disable_2fa,
    get_2fa_status,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'notifications', UserNotificationViewSet, basename='notification')
router.register(r'memberships', UserOrganizationViewSet, basename='membership')
router.register(r'activity-logs', UserActivityLogViewSet, basename='activity-log')

urlpatterns = [
    # Autenticación
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # 2FA endpoints
    path('2fa/setup/initiate/', initiate_2fa_setup, name='2fa_setup_initiate'),
    path('2fa/setup/verify/', verify_2fa_setup, name='2fa_setup_verify'),
    path('2fa/verify/', verify_2fa_token, name='2fa_verify'),
    path('2fa/disable/', disable_2fa, name='2fa_disable'),
    path('2fa/status/', get_2fa_status, name='2fa_status'),
    
    # Router URLs
    path('', include(router.urls)),
]
