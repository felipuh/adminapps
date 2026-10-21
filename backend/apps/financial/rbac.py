"""Explicit and auditable financial-permission operations."""

from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import FinancialPermissionAuditEvent


FINANCIAL_PERMISSION_CODES = frozenset({
    'financial_policy_admin',
    'financial_budget_admin',
    'financial_tariff_approve',
    'financial_evidence_review',
    'financial_reconcile',
    'financial_manual_resolution',
    'financial_audit_read',
    'financial_admin',
})


def _reference(subject):
    return str(getattr(subject, 'pk', subject))


def _permission(permission_code):
    if permission_code not in FINANCIAL_PERMISSION_CODES:
        raise ValidationError('Unknown financial permission.')
    return Permission.objects.get(
        content_type__app_label='financial',
        codename=permission_code,
    )


def has_financial_permission(user, permission_code):
    # Do not delegate to ``User.has_perm``: Django deliberately lets every
    # superuser pass that method, while the S2 contract requires an explicit
    # financial assignment even for superusers and platform administrators.
    return bool(
        user
        and getattr(user, 'is_authenticated', False)
        and getattr(user, 'is_active', False)
        and permission_code in FINANCIAL_PERMISSION_CODES
        and user.user_permissions.filter(
            content_type__app_label='financial',
            codename=permission_code,
        ).exists()
    )


def require_financial_permission(*, actor, permission_code, correlation_id=None):
    """Enforce a dedicated permission and record a secret-free denial."""
    if has_financial_permission(actor, permission_code):
        return
    FinancialPermissionAuditEvent.objects.create(
        action='denied',
        permission_code=permission_code,
        actor_reference=_reference(actor),
        reason_code='financial_permission_denied',
        correlation_id=correlation_id,
    )
    raise PermissionDenied('Financial permission required.')


def grant_financial_permission(*, actor, subject, permission_code, correlation_id=None):
    """Grant a single dedicated financial permission; no broad role implies it."""
    require_financial_permission(
        actor=actor,
        permission_code='financial_admin',
        correlation_id=correlation_id,
    )
    permission = _permission(permission_code)
    with transaction.atomic():
        subject.user_permissions.add(permission)
        FinancialPermissionAuditEvent.objects.create(
            action='granted',
            permission_code=permission_code,
            actor_reference=_reference(actor),
            subject_reference=_reference(subject),
            correlation_id=correlation_id,
        )


def revoke_financial_permission(*, actor, subject, permission_code, correlation_id=None):
    require_financial_permission(
        actor=actor,
        permission_code='financial_admin',
        correlation_id=correlation_id,
    )
    permission = _permission(permission_code)
    with transaction.atomic():
        subject.user_permissions.remove(permission)
        FinancialPermissionAuditEvent.objects.create(
            action='revoked',
            permission_code=permission_code,
            actor_reference=_reference(actor),
            subject_reference=_reference(subject),
            correlation_id=correlation_id,
        )
