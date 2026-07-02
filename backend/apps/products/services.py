from django.db.models import Q

from apps.organizations.models import Organization
from apps.products.models import OrganizationProductEntitlement, ProductSystem


PRODUCT_ACCESS_READINESS_CODES = ('ISO_SMART', 'MEDSUPPLIER')
PRODUCT_ACCESS_LEGACY_ALIASES = {
    'ISO_SMART': {'iso_smart', 'iso-smart', 'isosmart', 'smartiso'},
    'MEDSUPPLIER': {'medsupplier', 'iso-smart-medsupplier', 'iso_smart_medsupplier', 'isosmartmedsupplier'},
}


def _normalize_legacy_module(value):
    return str(value or '').strip().lower()


def _plan_mentions_product(plan, aliases):
    modules = plan.modules_included or []
    if not isinstance(modules, list):
        return False
    for module in modules:
        if isinstance(module, str) and _normalize_legacy_module(module) in aliases:
            return True
        if isinstance(module, dict) and _normalize_legacy_module(module.get('code')) in aliases:
            return True
    return False


def build_product_access_readiness_report():
    products = ProductSystem.objects.filter(code__in=PRODUCT_ACCESS_READINESS_CODES).order_by('code')
    entitlements = OrganizationProductEntitlement.objects.filter(
        product__code__in=PRODUCT_ACCESS_READINESS_CODES
    )

    product_report = []
    for code in PRODUCT_ACCESS_READINESS_CODES:
        product = next((item for item in products if item.code == code), None)
        product_entitlements = entitlements.filter(product__code=code)
        product_report.append({
            'code': code,
            'exists': product is not None,
            'status': product.status if product else None,
            'billing_enabled': product.billing_enabled if product else None,
            'is_available': product.is_available if product else False,
            'entitlements': {
                'total': product_entitlements.count(),
                'active': product_entitlements.filter(enabled=True, status='active').count(),
                'trial': product_entitlements.filter(enabled=True, status='trial').count(),
                'suspended': product_entitlements.filter(status='suspended').count(),
                'cancelled': product_entitlements.filter(status='cancelled').count(),
                'access_allowed': sum(1 for entitlement in product_entitlements.select_related(
                    'organization', 'product', 'product__default_plan', 'plan', 'subscription', 'subscription__plan'
                ) if entitlement.access_allowed),
            },
        })

    active_orgs = Organization.objects.filter(status='active')
    iso_orgs = active_orgs.filter(
        product_entitlements__product__code='ISO_SMART',
        product_entitlements__enabled=True,
        product_entitlements__status__in=['active', 'trial'],
    )
    med_orgs = active_orgs.filter(
        product_entitlements__product__code='MEDSUPPLIER',
        product_entitlements__enabled=True,
        product_entitlements__status__in=['active', 'trial'],
    )
    both_orgs = iso_orgs.filter(
        product_entitlements__product__code='MEDSUPPLIER',
        product_entitlements__enabled=True,
        product_entitlements__status__in=['active', 'trial'],
    )

    legacy_mentions = []
    organizations_with_subscription = Organization.objects.select_related('subscription__plan').filter(
        status='active',
        subscription__isnull=False,
        subscription__plan__modules_included__isnull=False,
    )
    for organization in organizations_with_subscription:
        subscription = organization.subscription
        mentioned_codes = [
            code for code, aliases in PRODUCT_ACCESS_LEGACY_ALIASES.items()
            if _plan_mentions_product(subscription.plan, aliases)
        ]
        if not mentioned_codes:
            continue
        entitled_codes = set(
            OrganizationProductEntitlement.objects.filter(
                organization=organization,
                product__code__in=mentioned_codes,
            ).values_list('product__code', flat=True)
        )
        missing_codes = sorted(set(mentioned_codes) - entitled_codes)
        if missing_codes:
            legacy_mentions.append({
                'organization_id': str(organization.id),
                'organization_code': organization.code,
                'plan_code': subscription.plan.code,
                'missing_entitlements': missing_codes,
            })

    missing_products = [item['code'] for item in product_report if not item['exists']]
    unavailable_products = [
        item['code'] for item in product_report
        if item['exists'] and not item['is_available']
    ]

    return {
        'status': 'ready' if not missing_products and not unavailable_products else 'attention_required',
        'products': product_report,
        'commercial_scenarios': {
            'active_organizations': active_orgs.count(),
            'iso_smart_only': iso_orgs.exclude(id__in=med_orgs.values('id')).distinct().count(),
            'medsupplier_only': med_orgs.exclude(id__in=iso_orgs.values('id')).distinct().count(),
            'both_products': both_orgs.distinct().count(),
            'no_active_product': active_orgs.exclude(
                Q(id__in=iso_orgs.values('id')) | Q(id__in=med_orgs.values('id'))
            ).distinct().count(),
        },
        'legacy_bypass_watchlist': {
            'plan_product_mentions_without_entitlement': len(legacy_mentions),
            'items': legacy_mentions,
        },
        'checks': {
            'required_products_exist': not missing_products,
            'required_products_available': not unavailable_products,
            'legacy_plan_mentions_do_not_grant_access': True,
            'billing_active_requires_entitlement': True,
        },
    }
