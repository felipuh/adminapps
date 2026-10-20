"""Live functional grants resolved inside the Decision B authority fence."""
from django.utils import timezone
from .authorization_contract import CONTRACT, role_scopes


def entitlement_eligible(entitlement):
    """Conservative authorization hold, not an adjudication of trial rights.

    Organization.subscription is the existing tenant billing link. An override
    cannot establish ownership; ambiguous billing associations grant nothing.
    """
    now = timezone.now()
    if (not entitlement.access_allowed or entitlement.starts_at is None
            or entitlement.starts_at > now
            or (entitlement.ends_at is not None and entitlement.ends_at <= now)):
        return False
    if entitlement.status == 'trial':
        return False
    subscription = entitlement.effective_subscription
    if entitlement.subscription_id and entitlement.subscription_id != entitlement.organization.subscription_id:
        return False
    if entitlement.product.billing_enabled:
        if entitlement.status != 'active' or subscription is None or not subscription.is_active:
            return False
        if subscription.pk != entitlement.organization.subscription_id or subscription.status != 'active':
            return False
        if subscription.current_period_start and subscription.current_period_start > now:
            return False
        if subscription.current_period_end and subscription.current_period_end <= now:
            return False
    return True


def resolve(session, user, membership, products, client):
    """No user/request scopes and no service credential can mint user grants."""
    evidence = dict(contract=CONTRACT, state='denied', principal_type='user',
                    sub=str(user.pk), tenant_id=str(membership.organization_id),
                    client_id=client.client_id, product=client.product, role=membership.role,
                    sid=str(session.id), sg=session.generation, av=session.authority_version,
                    scopes=[])
    if (not user.is_active or not membership.is_active
            or str(session.user_id) != evidence['sub']
            or str(session.tenant_id) != evidence['tenant_id']
            or session.role != membership.role or session.state != 'active'
            or session.revoked_at is not None or session.product != client.product
            or session.client.client_id != client.client_id):
        return evidence
    matches = [p for p in products if p.get('code') == client.product]
    if len(matches) != 1:
        return evidence
    product = matches[0]
    if product.get('access_allowed') is not True or product.get('authorization_eligible') is not True:
        return evidence
    # Legacy module labels have no versioned mapping to this resource catalog.
    # Do not silently ignore such restrictions. An explicit empty list means
    # capabilities are declared exclusively by exact v1 scopes; other states
    # stay held pending the module-to-resource contract.
    if product.get('modules_enabled') != []:
        return evidence
    scopes = role_scopes(product.get('scopes'), client.product, membership.role)
    if scopes:
        evidence.update(state='active', scopes=scopes)
    return evidence
