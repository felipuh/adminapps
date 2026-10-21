"""
URLs for Products - Admin Apps
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ISOStandardViewSet,
    ModuleActivityLogViewSet,
    OrganizationModuleViewSet,
    OrganizationProductEntitlementViewSet,
    ProductEntitlementAuditLogViewSet,
    ProductSystemViewSet,
)

router = DefaultRouter()
router.register(r'systems', ProductSystemViewSet, basename='product-system')
router.register(r'entitlements', OrganizationProductEntitlementViewSet, basename='product-entitlement')
router.register(r'entitlement-audit-logs', ProductEntitlementAuditLogViewSet, basename='product-entitlement-audit-log')
router.register(r'iso-standards', ISOStandardViewSet, basename='iso-standard')
router.register(r'modules', OrganizationModuleViewSet, basename='organization-module')
router.register(r'module-logs', ModuleActivityLogViewSet, basename='module-log')

urlpatterns = [
    path('', include(router.urls)),
]
