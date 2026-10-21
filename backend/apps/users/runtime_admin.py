"""Restricted AdminSite for the explicit admin process; legacy site unchanged."""
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from .api_authorization import may_manage_user
from .models import User, UserOrganization


WRITABLE = {
    'users.user': {'first_name', 'last_name', 'phone', 'job_title', 'department',
                   'language', 'timezone', 'theme', 'email_notifications',
                   'push_notifications', 'is_active'},
    'users.userorganization': {'is_active'},
    'organizations.organizationsettings': {'theme'},
}
REVIEWED = {
    'users.user', 'users.userorganization', 'users.usersession', 'users.useractivitylog',
    'organizations.organization', 'organizations.organizationsettings',
    'organizations.organizationinvitation', 'organizations.organizationfeatureflag',
    'products.productsystem', 'products.organizationproductentitlement',
    'products.productentitlementauditlog', 'products.isostandard',
    'products.organizationmodule', 'products.moduleactivitylog',
    'subscriptions.plan', 'subscriptions.subscription', 'subscriptions.invoice',
    'subscriptions.paymentmethod',
}


class RuntimeAdminSite(admin.AdminSite):
    def has_permission(self, request):
        user = request.user
        if not super().has_permission(request) or not isinstance(user, User) or not user.is_org_admin:
            return False
        if user.is_admin:
            return True
        return UserOrganization.objects.filter(
            user=user, organization_id=user.organization_id, is_active=True,
            role='org_admin', organization__status='active',
        ).exists()


class RuntimeModelAdminMixin:
    def _admitted(self, request, obj=None):
        if not self.admin_site.has_permission(request):
            return False
        if obj is None:
            return True
        target = obj if isinstance(obj, User) else getattr(obj, 'user', None)
        if target is not None and not may_manage_user(request.user, target):
            return False
        if getattr(obj, 'role', None) == 'superadmin' and not request.user.is_superadmin:
            return False
        if getattr(obj, 'role', None) == 'admin' and not request.user.is_admin:
            return False
        if not request.user.is_admin:
            org_id = getattr(obj, 'organization_id', None)
            if org_id is None and target is not None:
                org_id = target.organization_id
            if self.model._meta.label_lower == 'organizations.organization':
                org_id = obj.pk
            if str(org_id) != str(request.user.organization_id):
                return False
        return True

    def has_module_permission(self, request):
        return self._admitted(request) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return self._admitted(request, obj) and super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return (self.model._meta.label_lower in WRITABLE and self._admitted(request, obj)
                and super().has_change_permission(request, obj))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        return {}

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        if request.user.is_admin:
            return filters
        # RelatedFieldListFilter otherwise enumerates tenants outside the queryset.
        return tuple(name for name in filters if isinstance(name, str)
                     and not self.model._meta.get_field(name).is_relation)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not self._admitted(request):
            return queryset.none()
        fields = {field.name for field in self.model._meta.fields}
        if not request.user.is_admin:
            if 'organization' in fields:
                queryset = queryset.filter(organization_id=request.user.organization_id)
            elif 'user' in fields:
                queryset = queryset.filter(user__organization_id=request.user.organization_id)
            elif self.model._meta.label_lower == 'organizations.organization':
                queryset = queryset.filter(pk=request.user.organization_id)
            else:
                return queryset.none()
        if self.model is User and not request.user.is_superuser:
            queryset = queryset.exclude(Q(is_staff=True) | Q(is_superuser=True))
            if not request.user.is_superadmin:
                queryset = queryset.exclude(role='superadmin')
            if not request.user.is_admin:
                queryset = queryset.exclude(role='admin')
        return queryset

    def get_fieldsets(self, request, obj=None):
        label = self.model._meta.label_lower
        if label == 'users.user':
            return [(None, {'fields': ('email', 'organization', 'role', *sorted(WRITABLE[label]))})]
        if label == 'users.userorganization':
            return [(None, {'fields': ('user', 'organization', 'role', 'is_active')})]
        if label == 'organizations.organizationsettings':
            return [(None, {'fields': ('organization', 'theme')})]
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        allowed = WRITABLE.get(self.model._meta.label_lower, set())
        return tuple(dict.fromkeys([
            *super().get_readonly_fields(request, obj),
            *(field.name for field in self.model._meta.fields if field.name not in allowed),
        ]))

    def save_model(self, request, obj, form, change):
        allowed = WRITABLE.get(self.model._meta.label_lower, set())
        submitted = set(request.POST) - {'csrfmiddlewaretoken', '_save', '_continue', '_addanother'}
        if (not change or not self.has_change_permission(request, obj)
                or set(form.changed_data) - allowed or submitted - allowed):
            raise PermissionDenied('Campos o autoridad fuera del perfil administrativo.')
        if isinstance(obj, User) and obj.pk == request.user.pk and 'is_active' in form.changed_data:
            raise PermissionDenied('No puede desactivar su propio principal.')
        super().save_model(request, obj, form, change)

    def user_change_password(self, request, id, form_url=''):
        raise PermissionDenied('Use el flujo IAM de contraseña autorizado.')


site = RuntimeAdminSite(name='admin')
for model, model_admin in admin.site._registry.items():
    if model._meta.label_lower in REVIEWED:
        bounded = type('Runtime' + type(model_admin).__name__, (RuntimeModelAdminMixin, type(model_admin)), {})
        site.register(model, bounded)
