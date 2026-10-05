"""
Models for Integration module
"""
import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .credentials import integration_api_key_fingerprint

User = get_user_model()


class IntegrationAPIKey(models.Model):
    """
    API Keys para integración con servicios externos
    """
    CREDENTIAL_FORMATS = [
        ('legacy_plaintext', 'Legacy plaintext'),
        ('hashed_v1', 'Hashed v1'),
    ]
    LIFECYCLE_STATES = [
        ('created', 'Created'),
        ('active', 'Active'),
        ('revoked', 'Revoked'),
        ('rotated', 'Rotated'),
    ]

    name = models.CharField(max_length=100, help_text="Nombre del servicio")
    key = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Legacy plaintext key only; secure keys are never stored here.",
    )
    credential_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    credential_hash = models.CharField(max_length=255, blank=True)
    credential_format = models.CharField(
        max_length=24,
        choices=CREDENTIAL_FORMATS,
        default='hashed_v1',
    )
    fingerprint = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=16, choices=LIFECYCLE_STATES, default='active')
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_service = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    rotated_at = models.DateTimeField(null=True, blank=True)
    replaced_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replaces',
    )
    
    class Meta:
        db_table = 'integration_api_keys'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
    
    def __str__(self):
        return f"{self.name} - {self.status}"

    def save(self, *args, **kwargs):
        converted_raw_key = bool(self.key)
        if converted_raw_key:
            raw_key = self.key
            self.credential_hash = make_password(raw_key)
            self.fingerprint = integration_api_key_fingerprint(raw_key)
            self.credential_format = 'hashed_v1'
            self.key = None
            update_fields = kwargs.get('update_fields')
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {
                    'key',
                    'credential_hash',
                    'credential_format',
                    'fingerprint',
                }
        if self.status in {'revoked', 'rotated'}:
            self.is_active = False
        elif not self.is_active:
            self.status = 'revoked'
            self.revoked_at = self.revoked_at or timezone.now()
            update_fields = kwargs.get('update_fields')
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {
                    'status',
                    'revoked_at',
                }
        if self._state.adding and self.credential_format == 'legacy_plaintext':
            raise ValidationError(
                'New Integration API keys cannot use legacy plaintext storage.'
            )
        if self.credential_format == 'hashed_v1':
            if not self.credential_hash or not self.fingerprint:
                raise ValidationError(
                    'Hashed Integration API keys require a verifier and fingerprint.'
                )
        super().save(*args, **kwargs)


class IntegrationAPIKeyAuditEvent(models.Model):
    """Durable, secret-free audit evidence for API-key lifecycle operations."""

    ACTION_CHOICES = [
        ('created', 'Created'),
        ('rotated', 'Rotated'),
    ]

    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    old_credential = models.ForeignKey(
        IntegrationAPIKey,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_events_as_old',
    )
    new_credential = models.ForeignKey(
        IntegrationAPIKey,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_events_as_new',
    )
    old_fingerprint = models.CharField(max_length=80, blank=True)
    new_fingerprint = models.CharField(max_length=80)
    service_name = models.CharField(max_length=100)
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='integration_api_key_audit_events',
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'integration_api_key_audit_events'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} - {self.service_name} - {self.event_id}'


class LandingAnalyticsEvent(models.Model):
    """Centralized storage for Smart3AI landing events."""

    event_name = models.CharField(max_length=80, db_index=True)
    event_date = models.DateField(default=timezone.localdate, db_index=True)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    received_at = models.DateTimeField(auto_now_add=True)

    campaign = models.CharField(max_length=120, blank=True, db_index=True)
    variant = models.CharField(max_length=8, blank=True, db_index=True)
    persona = models.CharField(max_length=32, blank=True)
    intent = models.CharField(max_length=24, blank=True, db_index=True)
    location = models.CharField(max_length=80, blank=True)

    session_id = models.CharField(max_length=120, blank=True, db_index=True)
    page_path = models.CharField(max_length=255, blank=True)
    page_url = models.TextField(blank=True)
    href = models.TextField(blank=True)
    referrer = models.TextField(blank=True)

    source_service = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'landing_analytics_events'
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['event_date', 'campaign', 'variant']),
            models.Index(fields=['event_name', 'campaign']),
        ]

    def save(self, *args, **kwargs):
        if self.occurred_at:
            self.event_date = timezone.localtime(self.occurred_at).date()
        super().save(*args, **kwargs)


class DemoRequest(models.Model):
    """Pre-tenant commercial request received from an approved landing service."""

    STATUS_CHOICES = [
        ('new', 'Nueva'),
        ('contacted', 'Contactada'),
        ('qualified', 'Calificada'),
        ('scheduled', 'Agendada'),
        ('closed', 'Cerrada'),
    ]
    PRIORITY_CHOICES = [
        ('document_control', 'Control documental'),
        ('audit_readiness', 'Preparación de auditorías'),
        ('findings_actions', 'Hallazgos y acciones'),
        ('indicators_followup', 'Indicadores y seguimiento'),
        ('general_evaluation', 'Evaluación general'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.UUIDField(unique=True, db_index=True)
    full_name = models.CharField(max_length=160)
    work_email = models.EmailField(db_index=True)
    organization_name = models.CharField(max_length=200, db_index=True)
    product_code = models.CharField(max_length=40, db_index=True)
    priority = models.CharField(max_length=32, choices=PRIORITY_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    source = models.CharField(max_length=80, default='landing', db_index=True)
    campaign = models.CharField(max_length=120, blank=True, db_index=True)
    page_url = models.URLField(max_length=500, blank=True)
    consent_given = models.BooleanField(default=False)
    consented_at = models.DateTimeField()
    source_service = models.CharField(max_length=100)
    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_demo_requests',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'integration_demo_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='demo_req_status_created_idx'),
            models.Index(fields=['product_code', 'priority'], name='demo_req_product_priority_idx'),
        ]

    def __str__(self):
        return f'{self.organization_name} — {self.work_email}'
