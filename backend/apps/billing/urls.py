from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountsReceivableView,
    BillingAlertsView,
    BillingChurnAnalyticsView,
    BillingReconciliationView,
    BillingSummaryView,
    ProductDashboardView,
    ElectronicInvoiceViewSet,
    FiscalProfileViewSet,
    PaymentRecordViewSet,
    ProductCatalogViewSet,
    ProductPriceViewSet,
    RevenueByOrganizationView,
    RevenueByProductView,
    RevenueTimelineView,
    RevenueSnapshotViewSet,
    SchedulerStatusView,
)

router = DefaultRouter()
router.register(r'fiscal-profiles', FiscalProfileViewSet, basename='billing-fiscal-profile')
router.register(r'products', ProductCatalogViewSet, basename='billing-product')
router.register(r'prices', ProductPriceViewSet, basename='billing-price')
router.register(r'invoices', ElectronicInvoiceViewSet, basename='billing-invoice')
router.register(r'payments', PaymentRecordViewSet, basename='billing-payment')
router.register(r'revenue-snapshots', RevenueSnapshotViewSet, basename='billing-revenue-snapshot')

urlpatterns = [
    path('summary/', BillingSummaryView.as_view(), name='billing-summary'),
    path('revenue/by-product/', RevenueByProductView.as_view(), name='billing-revenue-by-product'),
    path('revenue/by-organization/', RevenueByOrganizationView.as_view(), name='billing-revenue-by-organization'),
    path('revenue/timeline/', RevenueTimelineView.as_view(), name='billing-revenue-timeline'),
    path('accounts-receivable/', AccountsReceivableView.as_view(), name='billing-accounts-receivable'),
    path('scheduler/', SchedulerStatusView.as_view(), name='billing-scheduler'),
    path('reconciliation/', BillingReconciliationView.as_view(), name='billing-reconciliation'),
    path('churn/', BillingChurnAnalyticsView.as_view(), name='billing-churn'),
    path('products/dashboard/', ProductDashboardView.as_view(), name='billing-product-dashboard'),
    path('alerts/', BillingAlertsView.as_view(), name='billing-alerts'),
    path('', include(router.urls)),
]
