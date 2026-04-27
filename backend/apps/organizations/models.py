"""
Organization Models - Admin Apps
Gestión de organizaciones/clientes que usan ISO Smart
"""
import uuid
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class OrganizationFeatureFlagQuerySet(models.QuerySet):
    def resolve_for_organization(self, organization=None):
        """Resolve global flags plus optional organization overrides."""
        resolved = {
            item['key']: item['enabled']
            for item in self.filter(organization__isnull=True).values('key', 'enabled')
        }
        if organization is not None:
            org_items = self.filter(organization=organization).values('key', 'enabled')
            resolved.update({item['key']: item['enabled'] for item in org_items})
        return resolved


class OrganizationFeatureFlag(models.Model):
    """Feature flags with optional per-organization override."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=80, verbose_name='Clave')
    description = models.CharField(max_length=255, blank=True, verbose_name='Descripción')
    enabled = models.BooleanField(default=False, verbose_name='Habilitada')
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='feature_flags',
        verbose_name='Organización',
        help_text='Si está vacío, aplica como valor global por defecto.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrganizationFeatureFlagQuerySet.as_manager()

    class Meta:
        db_table = 'organization_feature_flags'
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'
        ordering = ['key']
        constraints = [
            models.UniqueConstraint(fields=['key', 'organization'], name='uniq_feature_flag_scope')
        ]

    def __str__(self):
        scope = self.organization.code if self.organization_id else 'GLOBAL'
        return f"{scope}:{self.key}={self.enabled}"

    def save(self, *args, **kwargs):
        normalized_key = slugify(str(self.key or '').strip()).replace('-', '_')
        if not normalized_key:
            raise ValueError('Feature flag key cannot be empty')
        self.key = normalized_key
        super().save(*args, **kwargs)


class Organization(models.Model):
    """
    Modelo principal de Organización/Cliente
    Cada organización representa una empresa que usa ISO Smart
    """
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('inactive', 'Inactiva'),
        ('suspended', 'Suspendida'),
        ('trial', 'Periodo de Prueba'),
    ]
    
    INDUSTRY_CHOICES = [
        ('manufacturing', 'Manufactura'),
        ('technology', 'Tecnología'),
        ('healthcare', 'Salud'),
        ('finance', 'Finanzas'),
        ('education', 'Educación'),
        ('construction', 'Construcción'),
        ('retail', 'Comercio'),
        ('services', 'Servicios'),
        ('government', 'Gobierno'),
        ('other', 'Otro'),
    ]
    
    SIZE_CHOICES = [
        ('micro', 'Micro (1-10 empleados)'),
        ('small', 'Pequeña (11-50 empleados)'),
        ('medium', 'Mediana (51-250 empleados)'),
        ('large', 'Grande (251-1000 empleados)'),
        ('enterprise', 'Corporativo (1000+ empleados)'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    name = models.CharField(max_length=255, verbose_name="Nombre")
    legal_name = models.CharField(max_length=255, blank=True, verbose_name="Razón Social")
    tax_id = models.CharField(max_length=50, blank=True, verbose_name="RFC/NIT")
    
    # Información de contacto
    email = models.EmailField(verbose_name="Email Principal")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    website = models.URLField(blank=True, verbose_name="Sitio Web")
    
    # Dirección
    address = models.TextField(blank=True, verbose_name="Dirección")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    state = models.CharField(max_length=100, blank=True, verbose_name="Estado/Provincia")
    country = models.CharField(max_length=100, default='México', verbose_name="País")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Código Postal")
    
    # Clasificación
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, default='services', verbose_name="Industria")
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='small', verbose_name="Tamaño")
    employees_count = models.PositiveIntegerField(default=1, verbose_name="Número de Empleados")
    
    # Branding
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True, verbose_name="Logo")
    primary_color = models.CharField(max_length=7, default='#3B82F6', verbose_name="Color Primario")
    secondary_color = models.CharField(max_length=7, default='#1E40AF', verbose_name="Color Secundario")
    
    # Estado y suscripción
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial', verbose_name="Estado")
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organizations',
        verbose_name="Suscripción"
    )
    
    # Límites
    max_users = models.PositiveIntegerField(default=5, verbose_name="Máximo de Usuarios")
    max_documents = models.PositiveIntegerField(default=100, verbose_name="Máximo de Documentos")
    max_storage_mb = models.PositiveIntegerField(default=500, verbose_name="Almacenamiento Máximo (MB)")
    
    # Fechas
    trial_ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Fin de Periodo de Prueba")
    subscription_ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Fin de Suscripción")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    # Configuración ISO
    iso_standards = models.JSONField(default=list, verbose_name="Estándares ISO")  # ['ISO 9001', 'ISO 14001', etc.]
    
    # Metadatos
    notes = models.TextField(blank=True, verbose_name="Notas")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadatos")
    
    class Meta:
        db_table = 'organizations'
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Generar código automático
            last_org = Organization.objects.order_by('-created_at').first()
            if last_org and last_org.code.startswith('ORG'):
                try:
                    num = int(last_org.code[3:]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.code = f'ORG{num:05d}'
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_trial(self):
        return self.status == 'trial'
    
    @property
    def trial_expired(self):
        if self.trial_ends_at:
            return timezone.now() > self.trial_ends_at
        return False
    
    @property
    def subscription_expired(self):
        if self.subscription_ends_at:
            return timezone.now() > self.subscription_ends_at
        return False
    
    @property
    def users_count(self):
        return self.users.count()
    
    @property
    def can_add_users(self):
        return self.users_count < self.max_users


class OrganizationSettings(models.Model):
    """
    Configuración específica de cada organización
    """
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='settings',
        primary_key=True
    )
    
    # Módulos habilitados
    module_sca_enabled = models.BooleanField(default=True, verbose_name="SCA Habilitado")
    module_sie_enabled = models.BooleanField(default=True, verbose_name="SIE Habilitado")
    module_asb_enabled = models.BooleanField(default=True, verbose_name="ASB Habilitado")
    module_spm_enabled = models.BooleanField(default=True, verbose_name="SPM Habilitado")
    module_documents_enabled = models.BooleanField(default=True, verbose_name="Documentos Habilitado")
    module_risks_enabled = models.BooleanField(default=True, verbose_name="Riesgos Habilitado")
    module_objectives_enabled = models.BooleanField(default=True, verbose_name="Objetivos Habilitado")
    
    # Configuración de IA
    ai_auto_analysis = models.BooleanField(default=False, verbose_name="Análisis Automático")
    ai_analysis_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Diario'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensual'),
        ],
        default='weekly',
        verbose_name="Frecuencia de Análisis"
    )
    
    # Notificaciones
    notify_risk_critical = models.BooleanField(default=True)
    notify_risk_high = models.BooleanField(default=True)
    notify_objective_deadline = models.BooleanField(default=True)
    notify_document_expiry = models.BooleanField(default=True)
    notify_audit_reminder = models.BooleanField(default=True)
    
    # Apariencia
    theme = models.CharField(
        max_length=20,
        choices=[('light', 'Claro'), ('dark', 'Oscuro'), ('system', 'Sistema')],
        default='dark',
        verbose_name="Tema"
    )
    language = models.CharField(max_length=10, default='es', verbose_name="Idioma")
    date_format = models.CharField(max_length=20, default='DD/MM/YYYY', verbose_name="Formato de Fecha")
    
    # Backup
    auto_backup_enabled = models.BooleanField(default=False, verbose_name="Backup Automático")
    backup_frequency = models.CharField(max_length=20, default='weekly', verbose_name="Frecuencia de Backup")
    last_backup_at = models.DateTimeField(null=True, blank=True, verbose_name="Último Backup")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organization_settings'
        verbose_name = 'Configuración de Organización'
        verbose_name_plural = 'Configuraciones de Organizaciones'
    
    def __str__(self):
        return f"Settings: {self.organization.name}"


class OrganizationInvitation(models.Model):
    """
    Invitaciones para unirse a una organización
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    email = models.EmailField(verbose_name="Email Invitado")
    role = models.CharField(max_length=30, default='user', verbose_name="Rol Asignado")
    token = models.CharField(max_length=100, unique=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invited_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations'
    )
    
    message = models.TextField(blank=True, verbose_name="Mensaje Personal")
    
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'organization_invitations'
        verbose_name = 'Invitación'
        verbose_name_plural = 'Invitaciones'
        unique_together = ['organization', 'email']
    
    def __str__(self):
        return f"Invitación: {self.email} -> {self.organization.name}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
