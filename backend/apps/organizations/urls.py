"""
URLs for Organizations - Admin Apps
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, OrganizationInvitationViewSet

router = DefaultRouter()
router.register(r'', OrganizationViewSet, basename='organization')
router.register(r'invitations', OrganizationInvitationViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),
]
