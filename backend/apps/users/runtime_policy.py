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
