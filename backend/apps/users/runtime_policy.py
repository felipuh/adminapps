"""Governance and transactional audit for the opt-in restricted processes."""
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS


def restricted_runtime():
    return getattr(settings, 'ADMINAPPS_RUNTIME_PROFILE', None) in {'control_plane', 'admin'}


def check_held_fields(data, fields):
    if restricted_runtime() and set(data).intersection(fields):
        raise PermissionDenied('Operación retenida por gobernanza comercial.')


def validate_catalog_payload(serializer, attrs):
    """Restrict writes before granting SQL compatibility to legacy serializers."""
    if not restricted_runtime():
        return attrs
    model = getattr(getattr(serializer, 'Meta', None), 'model', None)
    label = model._meta.label_lower if model else ''
    creating = getattr(serializer, 'instance', None) is None
    if label == 'products.productsystem':
        check_held_fields(attrs, {'billing_enabled', 'default_plan'})
        if not creating and 'code' in attrs and attrs['code'] != serializer.instance.code:
            raise PermissionDenied('La identidad de producto no puede reasignarse.')
        if creating:
            attrs['billing_enabled'] = False
    elif label == 'subscriptions.plan':
        check_held_fields(attrs, {'price', 'currency', 'billing_cycle', 'max_users',
                                 'max_documents', 'max_storage_mb', 'max_organizations',
                                 'modules_included', 'ai_analysis_enabled', 'ai_monthly_quota',
                                 'is_trial_available', 'trial_days'})
        if attrs.get('is_active') is True:
            raise PermissionDenied('Activación comercial de planes retenida.')
        if creating:
            attrs.update(is_active=False, is_trial_available=False)
    elif label in {'products.organizationproductentitlement', 'products.organizationmodule'}:
        check_held_fields(attrs, {'plan', 'subscription'})
        if attrs.get('status') == 'trial' or (creating and 'status' not in attrs):
            raise PermissionDenied('Trials retenidos; indique un estado no comercial autorizado.')
    elif label == 'products.isostandard':
        check_held_fields(attrs, {'monthly_price', 'annual_price'})
    if type(serializer).__name__ in {
        'OrganizationProductEntitlementToggleSerializer', 'OrganizationModuleToggleSerializer',
        'OrganizationModuleBulkSerializer',
    }:
        if attrs.get('action') == 'trial' or attrs.get('status') == 'trial':
            raise PermissionDenied('Trials retenidos por gobernanza.')
        check_held_fields(getattr(serializer, 'initial_data', {}), {'trial_days'})
    return attrs


class AuditedMutationMixin:
    """Keep business mutations and audit atomic, excluding durable IAM lifecycle.

    Apply only to business viewsets. Never wrap login/refresh/revocation: their
    durable transaction boundary intentionally rejects ambient transactions.
    """
    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        self._audit_serializer = serializer
        return serializer

    def dispatch(self, request, *args, **kwargs):
        if not restricted_runtime() or request.method in SAFE_METHODS:
            return super().dispatch(request, *args, **kwargs)
        with transaction.atomic():
            response = super().dispatch(request, *args, **kwargs)
            if response.status_code >= 400:
                transaction.set_rollback(True)
                return response
            actor = self.request.user
            # Public invitation preview does not mutate authorized business state.
            if getattr(self, 'action', None) == 'accept':
                return response
            from .models import UserActivityLog
            instance = getattr(getattr(self, '_audit_serializer', None), 'instance', None)
            if instance is None and kwargs.get('pk'):
                instance = self.get_object()
            model = self.queryset.model
            organization_id = (getattr(instance, 'pk', None)
                               if model._meta.label_lower == 'organizations.organization'
                               else getattr(instance, 'organization_id', None))
            UserActivityLog.objects.create(
                user=actor, organization_id=organization_id,
                action='create' if self.action == 'create' else 'update',
                module='control_plane', entity_type=model._meta.label_lower,
                entity_id=str(getattr(instance, 'pk', '') or ''),
                description=self.action,
            )
            return response
