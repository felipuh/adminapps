"""Decision B state. These tables are central, cross-tenant IAM authority tables.

No token or credential material is persisted. Runtime requires PostgreSQL and
migration 0009/0010, which must be activated separately.
"""
import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, F


class SSOSecurityFence(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    enabled = models.BooleanField(default=False)
    generation = models.PositiveBigIntegerField(default=0)
    authority_epoch = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = 'sso_security_fence'
        constraints = [models.CheckConstraint(check=Q(id=1), name='sso_single_fence')]


class SSOSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    client = models.ForeignKey('integration.SSOClient', on_delete=models.PROTECT)
    tenant = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)
    product = models.CharField(max_length=50)
    generation = models.PositiveBigIntegerField(unique=True)
    authority_version = models.PositiveBigIntegerField()
    authenticated_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    state = models.CharField(max_length=16, default='active')
    revoked_at = models.DateTimeField(null=True)
    revocation_reason = models.CharField(max_length=64, blank=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)
    access_jti = models.UUIDField(default=uuid.uuid4)
    refresh_jti = models.UUIDField(default=uuid.uuid4)
    mfa_generation = models.UUIDField(null=True)
    mfa_challenge_digest = models.CharField(max_length=64, blank=True)
    role = models.CharField(max_length=30)
    authentication_methods = models.JSONField(default=list)

    class Meta:
        db_table = 'sso_sessions'
        indexes = [models.Index(fields=['user', 'client', 'tenant', 'state'], name='sso_authority_scope')]
        constraints = [
            models.UniqueConstraint(fields=['mfa_challenge_digest'], condition=~Q(mfa_challenge_digest=''), name='sso_one_session_per_mfa'),
            models.CheckConstraint(check=Q(generation__gt=0, authority_version__gt=0), name='sso_positive_versions'),
            models.CheckConstraint(check=Q(expires_at__gt=F('authenticated_at')), name='sso_positive_lifetime'),
            models.CheckConstraint(check=(Q(state='active', revoked_at__isnull=True, revocation_reason='') |
                (Q(state='revoked', revoked_at__isnull=False) & ~Q(revocation_reason=''))), name='sso_revocation_state'),
        ]


class SSORevocationOutbox(models.Model):
    # UUID event identity, deterministic (session, generation) idempotency key.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(SSOSession, on_delete=models.PROTECT)
    generation = models.PositiveBigIntegerField()
    client_id_snapshot = models.CharField(max_length=100)
    product = models.CharField(max_length=50)
    tenant_id_snapshot = models.UUIDField()
    reason = models.CharField(max_length=64)
    correlation_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'sso_revocation_outbox'
        constraints = [models.UniqueConstraint(fields=['session', 'generation'], name='sso_event_idempotency')]
