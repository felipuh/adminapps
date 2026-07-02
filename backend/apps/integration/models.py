"""
Models for Integration module
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class IntegrationAPIKey(models.Model):
    """
    API Keys para integración con servicios externos
    """
    name = models.CharField(max_length=100, help_text="Nombre del servicio")
    key = models.CharField(max_length=255, unique=True, help_text="API Key")
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_service = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_api_keys'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
    
    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"


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
