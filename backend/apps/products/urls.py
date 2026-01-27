"""
URLs for Products - Admin Apps
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ISOStandardViewSet, OrganizationModuleViewSet, ModuleActivityLogViewSet

router = DefaultRouter()
router.register(r'iso-standards', ISOStandardViewSet, basename='iso-standard')
router.register(r'modules', OrganizationModuleViewSet, basename='organization-module')
router.register(r'module-logs', ModuleActivityLogViewSet, basename='module-log')

urlpatterns = [
    path('', include(router.urls)),
]
