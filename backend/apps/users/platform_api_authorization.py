"""Additional platform admission for billing/backoffice APIs.

Existing financial services and governance decisions are not replaced by these
HTTP authorization checks. Each custom action is explicitly mapped to its model
operations. Unknown actions fail closed.
"""
from rest_framework.exceptions import PermissionDenied
from .api_authorization import platform_actor, require_human


def crud(model, *, readonly=False):
    app, name = model.split('.')
    result = {action: (f'{app}.view_{name}',) for action in ('list', 'retrieve')}
    if not readonly:
        result.update({action: (f'{app}.{verb}_{name}',) for action, verb in (
            ('create', 'add'), ('update', 'change'), ('partial_update', 'change'), ('destroy', 'delete'))})
    return result


ISSUE = ('billing.add_electronicinvoice', 'billing.add_paymentrecord', 'billing.add_revenuesnapshot')
PAY = ('billing.change_electronicinvoice', 'billing.add_paymentrecord', 'billing.change_paymentrecord', 'billing.add_revenuesnapshot')
BILLING_READ = ('billing.view_electronicinvoice', 'billing.view_paymentrecord',
                'billing.view_revenuesnapshot', 'billing.view_productcatalog', 'subscriptions.view_subscription')
POLICIES = {
    'FiscalProfileViewSet': crud('billing.fiscalprofile'),
    'ProductCatalogViewSet': dict(crud('billing.productcatalog'), mapping_audit=('billing.view_productcatalog',), auto_map=('billing.change_productcatalog', 'products.view_productsystem')),
    'ProductPriceViewSet': crud('billing.productprice'),
    'ElectronicInvoiceViewSet': dict(crud('billing.electronicinvoice', readonly=True),
        export_csv=('billing.view_electronicinvoice',), compliance_preview=('billing.view_electronicinvoice',),
        recalculate=('billing.change_electronicinvoice',), issue=ISSUE, issue_from_subscription=ISSUE,
        run_cycle=ISSUE, run_batch=ISSUE, mark_paid=PAY,
        prepare_hacienda=('billing.change_electronicinvoice',), update_hacienda_status=('billing.change_electronicinvoice',),
        generate_xml=('billing.change_electronicinvoice',), credit_note=ISSUE),
    'PaymentRecordViewSet': dict(crud('billing.paymentrecord', readonly=True),
        register_pending=('billing.add_paymentrecord', 'billing.view_electronicinvoice'), confirm=PAY,
        reject=('billing.change_paymentrecord',)),
    'RevenueSnapshotViewSet': crud('billing.revenuesnapshot', readonly=True),
    'RecurringReportScheduleViewSet': dict(crud('billing.recurringreportschedule'),
        run_now=('billing.change_recurringreportschedule',) + BILLING_READ,
        run_due=('billing.change_recurringreportschedule',) + BILLING_READ),
    'BillingSummaryView': {'get': BILLING_READ},
    'AIUsageDashboardView': {'get': ('integration.view_aiusageprojection',)},
    'RevenueByProductView': {'get': BILLING_READ},
    'RevenueByOrganizationView': {'get': BILLING_READ},
    'RevenueTimelineView': {'get': BILLING_READ},
    'AccountsReceivableView': {'get': BILLING_READ},
    'SchedulerStatusView': {'get': ('billing.view_schedulerjoblog',), 'post': ISSUE + ('billing.add_schedulerjoblog',)},
    'BillingChurnAnalyticsView': {'get': BILLING_READ},
    'BillingReconciliationView': {'get': BILLING_READ, 'post': PAY},
    'ProductDashboardView': {'get': BILLING_READ + ('products.view_productsystem',)},
    'BillingAlertsView': {'get': BILLING_READ},
    'DashboardView': {'get': BILLING_READ + ('organizations.view_organization', 'users.view_user', 'users.view_useractivitylog', 'products.view_organizationmodule', 'products.view_organizationproductentitlement')},
    'SystemStatsView': {'get': ('organizations.view_organization', 'users.view_user', 'products.view_isostandard', 'products.view_organizationmodule')},
    'ProductReadinessView': {'get': ('organizations.view_organization', 'products.view_productsystem', 'products.view_organizationproductentitlement')},
    'QuickActionsView': {'get': ('organizations.view_organization', 'products.view_organizationmodule')},
    'LandingAnalyticsSummaryView': {'get': ('integration.view_landinganalyticsevent',)},
}


class PlatformOperationMixin:
    def check_permissions(self, request):
        user = require_human(request)
        super().check_permissions(request)
        action = getattr(self, 'action', request.method.lower())
        required = POLICIES.get(type(self).__name__, {}).get(action)
        if not platform_actor(user) or not required or not all(user.has_perm(p) for p in required):
            raise PermissionDenied('Autoridad de plataforma insuficiente para esta operación.')
