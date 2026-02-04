"""
Models for Integration module
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class IntegrationAPIKey(models.Model):
    """
    API Keys para integración con servicios externos
    """
    name = models.CharField(max_length=100, help_text="Nombre del servicio")
    key = models.CharField(max_length=255, unique=True, help_text="API Key")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'integration_api_keys'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
    
    def __str__(self):
        return f"{self.name} - {'Active' if self.is_active else 'Inactive'}"
