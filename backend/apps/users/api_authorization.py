"""Local control-plane boundary, additional to each endpoint's existing policy.

Platform authority requires a live human User, staff admission, the existing role,
and a Django permission for the precise model operation. Organization authority
requires a live primary-tenant membership. Neither grants consumer-product scopes.
"""
from collections.abc import Mapping

from rest_framework.exceptions import MethodNotAllowed, PermissionDenied, ValidationError
from rest_framework.permissions import SAFE_METHODS
from .models import User, UserOrganization


# Explicit action catalog: new handlers do not inherit administrative authority.
POLICIES = {
    'FeatureFlagsView': ('organizations.organizationfeatureflag', 'tenant_read', {'get'}),
    'PlanViewSet': ('subscriptions.plan', 'catalog', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'featured', 'compare'}),
    'ProductSystemViewSet': ('products.productsystem', 'platform', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'active'}),
    'ISOStandardViewSet': ('products.isostandard', 'platform', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'active', 'organizations'}),
    'OrganizationProductEntitlementViewSet': ('products.organizationproductentitlement', 'platform', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'toggle', 'by_organization', 'audit_logs'}),
    'OrganizationModuleViewSet': ('products.organizationmodule', 'platform', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'toggle', 'by_organization', 'bulk_assign'}),
    'ProductEntitlementAuditLogViewSet': ('products.productentitlementauditlog', 'platform', {'list', 'retrieve'}),
    'ModuleActivityLogViewSet': ('products.moduleactivitylog', 'platform', {'list', 'retrieve'}),
    'SubscriptionViewSet': ('subscriptions.subscription', 'tenant_read', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'activate', 'cancel', 'change_plan', 'stats', 'invoices'}),
    'InvoiceViewSet': ('subscriptions.invoice', 'tenant_read', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'mark_paid', 'download'}),
    'PaymentMethodViewSet': ('subscriptions.paymentmethod', 'tenant_admin', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'set_default'}),
    'OrganizationViewSet': ('organizations.organization', 'tenant_read', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'organization_settings', 'stats', 'users', 'activate', 'suspend'}),
    'OrganizationInvitationViewSet': ('organizations.organizationinvitation', 'tenant_admin', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'resend', 'cancel', 'accept'}),
    'UserViewSet': ('users.user', 'tenant_users', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'activate', 'deactivate', 'unlock', 'reset_password', 'me', 'change_password', 'sessions', 'revoke_sessions', 'revoke_session', 'revoke_sso_sessions', 'activity'}),
    'UserOrganizationViewSet': ('users.userorganization', 'tenant_admin', {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'}),
    'UserActivityLogViewSet': ('users.useractivitylog', 'tenant_admin', {'list', 'retrieve'}),
    'UserNotificationViewSet': ('users.useractivitylog', 'tenant_read', {'list', 'unread_count', 'mark_read', 'mark_all_read'}),
}
SELF_ACTIONS = {'me', 'change_password', 'sessions', 'revoke_sessions', 'revoke_session', 'revoke_sso_sessions', 'activity'}

ACTION_INPUTS = {
    'activate': set(), 'deactivate': set(), 'unlock': set(), 'suspend': set(),
    'cancel': set(), 'resend': set(), 'set_default': set(),
    'change_plan': {'plan_id'}, 'mark_paid': {'payment_reference'},
    'reset_password': {'new_password'}, 'revoke_sessions': {'current_token_jti'},
    'revoke_sso_sessions': {'session_id'},
    'revoke_session': {'session_id', 'all'},
    'toggle': {'action', 'reason', 'trial_days'},
    'bulk_assign': {'organization_id', 'iso_standards', 'status'},
    'mark_read': {'notification_id'}, 'mark_all_read': set(),
}


def require_human(request):
    user = request.user
    # Check the authenticated principal, never a role/tenant supplied in a payload.
    auth = getattr(request, 'auth', None)
    claims = getattr(auth, 'payload', auth)
    if (not isinstance(user, User) or not user.is_active or not user.is_authenticated
            or getattr(request, 'integration_service', None)
            or request.headers.get('X-API-Key')):
        raise PermissionDenied('Se requiere una sesión humana local activa.')
    if isinstance(claims, Mapping) and (
        claims.get('principal_type', 'human') != 'human'
        or claims.get('token_family') == 'CENTRAL'
        or claims.get('client_id') or claims.get('product')
    ):
        raise PermissionDenied('La credencial no autoriza el control plane humano.')
    return user


def platform_actor(user):
    return bool(user.is_active and user.is_staff and user.is_admin)


def may_manage_user(actor, target):
    if getattr(target, 'is_superuser', False) and not actor.is_superuser:
        return False
    if getattr(target, 'is_staff', False) and not actor.is_superuser:
        return False
    if getattr(target, 'role', None) == 'superadmin' and not actor.is_superadmin:
        return False
    if getattr(target, 'role', None) == 'admin' and not actor.is_admin:
        return False
    return True


def reject_reparenting(instance, attrs, fields):
    if instance is None:
        return
    for field in fields:
        if field in attrs:
            value = attrs[field]
            new_id = getattr(value, 'pk', value)
            old_id = getattr(instance, field + '_id', None)
            if str(new_id) != str(old_id):
                raise ValidationError({field: 'No se puede reasignar esta relación.'})


class StrictInputMixin:
    """Reject ignored inputs explicitly instead of silently accepting privilege probes."""
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            writable = {name for name, field in self.fields.items() if not field.read_only}
            invalid = set(data) - writable
            if invalid:
                raise ValidationError({name: 'Campo no modificable.' for name in sorted(invalid)})
        from .runtime_policy import validate_catalog_payload
        return validate_catalog_payload(self, super().to_internal_value(data))


class ControlPlaneMixin:
    def check_permissions(self, request):
        name = type(self).__name__
        policy = POLICIES.get(name)
        action = getattr(self, 'action', request.method.lower())
        if not policy or action not in policy[2]:
            raise PermissionDenied('Operación sin política de autorización.')
        # Token preview retains its existing public contract; it grants no session.
        if name == 'OrganizationInvitationViewSet' and action == 'accept':
            super().check_permissions(request)
            return
        user = require_human(request)
        super().check_permissions(request)
        from .runtime_policy import restricted_runtime
        if restricted_runtime() and action == 'destroy':
            raise MethodNotAllowed(request.method, 'Borrado físico retenido; use desactivación o cancelación autorizada.')
        if (restricted_runtime() and request.method not in SAFE_METHODS
                and name in {'SubscriptionViewSet', 'InvoiceViewSet', 'PaymentMethodViewSet'}):
            raise PermissionDenied('Mutación comercial o financiera retenida por gobernanza.')
        if request.method not in SAFE_METHODS and action in ACTION_INPUTS:
            if not isinstance(request.data, Mapping) or set(request.data) - ACTION_INPUTS[action]:
                raise ValidationError('Campos no admitidos para esta operación.')
        write = request.method not in SAFE_METHODS
        if name == 'UserViewSet' and action in SELF_ACTIONS:
            return
        if name == 'UserNotificationViewSet':
            write = False  # only the caller's read markers are changed
        if user.is_admin:
            if not platform_actor(user):
                raise PermissionDenied('El rol global requiere admisión de plataforma.')
            model = policy[0]
            if name == 'OrganizationViewSet' and action == 'organization_settings':
                model = 'organizations.organizationsettings'
            app, resource = model.split('.')
            operation = ('view' if not write else 'add' if action in {'create', 'bulk_assign'}
                         else 'delete' if action == 'destroy' else 'change')
            if not user.has_perm(f'{app}.{operation}_{resource}'):
                raise PermissionDenied('Falta permiso para esta operación de plataforma.')
            return
        if policy[1] == 'platform' or (policy[1] == 'catalog' and write):
            raise PermissionDenied('Se requiere administración de plataforma.')
        if policy[1] == 'catalog':
            return
        if policy[1] == 'tenant_read' and write and not (
            name == 'OrganizationViewSet' and action == 'organization_settings'
        ):
            raise PermissionDenied('Esta mutación requiere administración de plataforma.')
        if name == 'SubscriptionViewSet' and action == 'stats':
            raise PermissionDenied('Las estadísticas globales requieren plataforma.')
        if not user.organization_id:
            raise PermissionDenied('Se requiere una organización vigente.')
        members = UserOrganization.objects.filter(
            user=user, organization_id=user.organization_id, is_active=True,
            organization__status='active',
        )
        if write or policy[1] == 'tenant_admin':
            members = members.filter(role='org_admin')
        if not members.exists():
            raise PermissionDenied('Membresía o autoridad de organización insuficiente.')

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        user = request.user
        # Plans are a global catalog, not tenant-owned objects. Their read
        # visibility is still constrained by PlanViewSet.get_queryset().
        catalog_read = (
            type(self).__name__ == 'PlanViewSet'
            and request.method in SAFE_METHODS
            and obj._meta.label_lower == 'subscriptions.plan'
        )
        if not platform_actor(user) and not catalog_read:
            org_id = obj.pk if obj._meta.label_lower == 'organizations.organization' else getattr(obj, 'organization_id', None)
            # Subscription has no tenant owner; its queryset uses the canonical link
            # and rejects ambiguous shared subscriptions.
            if obj._meta.label_lower != 'subscriptions.subscription' and (
                not org_id or str(org_id) != str(user.organization_id)
            ):
                raise PermissionDenied('Objeto fuera de la organización autorizada.')
        if request.method not in SAFE_METHODS:
            target = obj if isinstance(obj, User) else getattr(obj, 'user', None)
            if target is not None and not may_manage_user(user, target):
                raise PermissionDenied('No puedes administrar un principal de mayor autoridad.')
            role = getattr(obj, 'role', None)
            if role == 'superadmin' and not user.is_superadmin:
                raise PermissionDenied('Objeto reservado a superadministradores.')
            if role == 'admin' and not user.is_admin:
                raise PermissionDenied('Objeto reservado a administradores de plataforma.')
