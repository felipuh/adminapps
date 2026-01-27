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
    UserOrganizationViewSet,
    UserActivityLogViewSet,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
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
    
    # Router URLs
    path('', include(router.urls)),
]
