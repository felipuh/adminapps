"""
ISO Modules - Admin Apps
Control maestro de módulos ISO disponibles y asignación a clientes
"""
import uuid
from django.db import models
from django.utils import timezone


class ProductSystem(models.Model):
    """Producto o sistema administrable por AdminApps."""

    PRODUCT_TYPE_CHOICES = [
        ('saas', 'SaaS'),
        ('module', 'Module'),
        ('service', 'Service'),
        ('bundle', 'Bundle'),
    ]
    STATUS_CHOICES = [
        ('development', 'En Desarrollo'),
        ('beta', 'Beta'),
        ('active', 'Activo'),
        ('deprecated', 'Descontinuado'),
        ('retired', 'Retirado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, verbose_name='Codigo')
    name = models.CharField(max_length=120, verbose_name='Nombre')
    slug = models.SlugField(max_length=80, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Descripcion')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='saas')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='development')
    billing_enabled = models.BooleanField(default=True)
    default_plan = models.ForeignKey(
        'subscriptions.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_products',
    )
    launch_url = models.URLField(blank=True)
    api_base_url = models.URLField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_systems'
        verbose_name = 'Producto/Sistema'
        verbose_name_plural = 'Productos/Sistemas'
        ordering = ['name']

    def __str__(self):
        return f'{self.code} - {self.name}'

    @property
    def is_available(self):
        return self.status in {'active', 'beta'}


class OrganizationProductEntitlement(models.Model):
    """Habilitacion producto-neutral de una organizacion."""

    STATUS_CHOICES = [
        ('trial', 'Prueba'),
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('expired', 'Expirado'),
        ('cancelled', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='product_entitlements',
    )
    product = models.ForeignKey(
        ProductSystem,
        on_delete=models.PROTECT,
        related_name='organization_entitlements',
    )
    enabled = models.BooleanField(default=True)
    plan = models.ForeignKey(
        'subscriptions.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_entitlements',
    )
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_entitlements',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True)
    modules_enabled = models.JSONField(default=list, blank=True)
    scopes = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    activated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_entitlements_activated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_product_entitlements'
        verbose_name = 'Entitlement de Producto'
        verbose_name_plural = 'Entitlements de Producto'
        unique_together = ['organization', 'product']
        ordering = ['organization__name', 'product__name']

    def __str__(self):
        return f'{self.organization.name} - {self.product.code}'

    @property
    def is_active(self):
        if not self.enabled:
            return False
        if self.status not in {'active', 'trial'}:
            return False
        if self.ends_at and timezone.now() > self.ends_at:
            return False
        return True

    def enable(self, user=None):
        self.enabled = True
        self.status = 'active'
        self.suspended_at = None
        self.suspension_reason = ''
        if user:
            self.activated_by = user
        self.save()

    def disable(self, reason=''):
        self.enabled = False
        self.status = 'suspended'
        self.suspended_at = timezone.now()
        self.suspension_reason = reason
        self.save()


class ISOStandard(models.Model):
    """
    Estándares ISO disponibles en la plataforma
    Controlados exclusivamente por Comtech
    """
    STATUS_CHOICES = [
        ('development', 'En Desarrollo'),
        ('beta', 'Beta'),
        ('active', 'Activo'),
        ('deprecated', 'Descontinuado'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")  # ISO9001, ISO14001, etc.
    name = models.CharField(max_length=100, verbose_name="Nombre")
    full_name = models.CharField(max_length=255, verbose_name="Nombre Completo")
    version = models.CharField(max_length=20, default='2015', verbose_name="Versión")
    
    # Descripción
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=50, default='shield-check', verbose_name="Icono")
    color = models.CharField(max_length=7, default='#3B82F6', verbose_name="Color")
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='development')
    is_base = models.BooleanField(default=False, verbose_name="Es Módulo Base")  # ISO 9001 sería base
    
    # Pricing
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio Mensual")
    annual_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio Anual")
    
    # Orden de visualización
    display_order = models.PositiveIntegerField(default=0)
    
    # Metadatos
    clauses_count = models.PositiveIntegerField(default=0, verbose_name="Número de Cláusulas")
    metadata = models.JSONField(default=dict, blank=True)
    
    # Fechas
    released_at = models.DateField(null=True, blank=True, verbose_name="Fecha de Lanzamiento")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'iso_standards'
        verbose_name = 'Estándar ISO'
        verbose_name_plural = 'Estándares ISO'
        ordering = ['display_order', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_available(self):
        return self.status in ['active', 'beta']


class OrganizationModule(models.Model):
    """
    Módulos ISO asignados a cada organización
    Esta es la "llave" que Comtech controla
    """
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('trial', 'Prueba'),
        ('expired', 'Expirado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='iso_modules'
    )
    iso_standard = models.ForeignKey(
        ISOStandard,
        on_delete=models.PROTECT,
        related_name='organization_assignments'
    )
    
    # Estado del módulo para esta organización
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Control de acceso
    is_enabled = models.BooleanField(default=True, verbose_name="Habilitado")
    
    # Fechas de vigencia
    activated_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Activación")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Expiración")
    suspended_at = models.DateTimeField(null=True, blank=True)
    
    # Quién lo activó
    activated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='modules_activated'
    )
    
    # Notas internas (solo Comtech ve esto)
    internal_notes = models.TextField(blank=True, verbose_name="Notas Internas")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organization_modules'
        verbose_name = 'Módulo de Organización'
        verbose_name_plural = 'Módulos de Organizaciones'
        unique_together = ['organization', 'iso_standard']
    
    def __str__(self):
        return f"{self.organization.name} - {self.iso_standard.code}"
    
    @property
    def is_active(self):
        if not self.is_enabled:
            return False
        if self.status not in ['active', 'trial']:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True
    
    def enable(self, user=None):
        """Activar módulo (abrir la llave)"""
        self.is_enabled = True
        self.status = 'active'
        self.suspended_at = None
        if user:
            self.activated_by = user
        self.save()
    
    def disable(self, reason=''):
        """Desactivar módulo (cerrar la llave)"""
        self.is_enabled = False
        self.status = 'suspended'
        self.suspended_at = timezone.now()
        if reason:
            self.internal_notes += f"\n[{timezone.now()}] Suspendido: {reason}"
        self.save()
    
    def set_trial(self, days=14):
        """Establecer periodo de prueba"""
        self.status = 'trial'
        self.is_enabled = True
        self.expires_at = timezone.now() + timezone.timedelta(days=days)
        self.save()


class ModuleActivityLog(models.Model):
    """
    Log de actividad de módulos (auditoría interna de Comtech)
    """
    ACTION_CHOICES = [
        ('enabled', 'Habilitado'),
        ('disabled', 'Deshabilitado'),
        ('trial_started', 'Prueba Iniciada'),
        ('trial_ended', 'Prueba Terminada'),
        ('expired', 'Expirado'),
        ('renewed', 'Renovado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    organization_module = models.ForeignKey(
        OrganizationModule,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'module_activity_logs'
        verbose_name = 'Log de Módulo'
        verbose_name_plural = 'Logs de Módulos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.organization_module} - {self.action}"
