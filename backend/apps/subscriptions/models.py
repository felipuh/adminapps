"""
Subscription Models - Admin Apps
Gestión de planes y suscripciones para organizaciones
"""
import uuid
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Plan(models.Model):
    """
    Planes disponibles para las organizaciones
    """
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Precio
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Precio Base")
    currency = models.CharField(max_length=3, default='MXN', verbose_name="Moneda")
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default='monthly',
        verbose_name="Ciclo de Facturación"
    )
    
    # Límites
    max_users = models.PositiveIntegerField(default=5, verbose_name="Máximo de Usuarios")
    max_documents = models.PositiveIntegerField(default=100, verbose_name="Máximo de Documentos")
    max_storage_mb = models.PositiveIntegerField(default=500, verbose_name="Almacenamiento (MB)")
    max_organizations = models.PositiveIntegerField(default=1, verbose_name="Máximo de Organizaciones")
    
    # Módulos incluidos
    modules_included = models.JSONField(
        default=list,
        verbose_name="Módulos Incluidos",
        help_text="Lista de módulos: sca, sie, asb, spm, documents, risks, objectives, medsupplier"
    )
    
    # Características
    features = models.JSONField(default=list, verbose_name="Características")
    
    # IA
    ai_analysis_enabled = models.BooleanField(default=False, verbose_name="Análisis IA Habilitado")
    ai_monthly_quota = models.PositiveIntegerField(default=0, verbose_name="Cuota Mensual de IA")
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, verbose_name="Plan Destacado")
    is_trial_available = models.BooleanField(default=True, verbose_name="Prueba Disponible")
    trial_days = models.PositiveIntegerField(default=14, verbose_name="Días de Prueba")
    
    # Orden de visualización
    display_order = models.PositiveIntegerField(default=0)
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plans'
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'
        ordering = ['display_order', 'price']
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.get_billing_cycle_display()}"


class Subscription(models.Model):
    """
    Suscripción activa de una organización
    """
    STATUS_CHOICES = [
        ('trial', 'Periodo de Prueba'),
        ('active', 'Activa'),
        ('past_due', 'Pago Vencido'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
        ('suspended', 'Suspendida'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relaciones
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name="Plan"
    )
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Fechas
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Facturación
    next_billing_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Uso actual
    current_users = models.PositiveIntegerField(default=0)
    current_documents = models.PositiveIntegerField(default=0)
    current_storage_mb = models.PositiveIntegerField(default=0)
    ai_usage_this_month = models.PositiveIntegerField(default=0)
    
    # Metadatos
    payment_method = models.CharField(max_length=50, blank=True)
    external_subscription_id = models.CharField(max_length=255, blank=True)  # ID de Stripe, etc.
    notes = models.TextField(blank=True)
    
    # Fechas de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
    
    def __str__(self):
        return f"Suscripción: {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        return self.status in ['active', 'trial']
    
    @property
    def is_trial(self):
        return self.status == 'trial'
    
    @property
    def days_remaining(self):
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0
    
    @property
    def trial_days_remaining(self):
        if self.trial_ends_at and self.is_trial:
            delta = self.trial_ends_at - timezone.now()
            return max(0, delta.days)
        return 0
    
    @property
    def usage_percentage(self):
        """Porcentaje de uso respecto a los límites"""
        return {
            'users': (self.current_users / self.plan.max_users * 100) if self.plan.max_users else 0,
            'documents': (self.current_documents / self.plan.max_documents * 100) if self.plan.max_documents else 0,
            'storage': (self.current_storage_mb / self.plan.max_storage_mb * 100) if self.plan.max_storage_mb else 0,
            'ai': (self.ai_usage_this_month / self.plan.ai_monthly_quota * 100) if self.plan.ai_monthly_quota else 0,
        }
    
    def start_trial(self):
        """Iniciar periodo de prueba"""
        self.status = 'trial'
        self.trial_started_at = timezone.now()
        self.trial_ends_at = timezone.now() + timezone.timedelta(days=self.plan.trial_days)
        self.save()
    
    def activate(self):
        """Activar suscripción después del pago"""
        self.status = 'active'
        self.started_at = timezone.now()
        self.current_period_start = timezone.now()
        
        # Calcular fin del periodo según el ciclo de facturación
        if self.plan.billing_cycle == 'monthly':
            self.current_period_end = timezone.now() + timezone.timedelta(days=30)
        elif self.plan.billing_cycle == 'quarterly':
            self.current_period_end = timezone.now() + timezone.timedelta(days=90)
        else:  # yearly
            self.current_period_end = timezone.now() + timezone.timedelta(days=365)
        
        self.save()
    
    def cancel(self):
        """Cancelar suscripción"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()


class Invoice(models.Model):
    """
    Facturas generadas para las suscripciones
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('paid', 'Pagada'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Cancelada'),
        ('refunded', 'Reembolsada'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=50, unique=True, verbose_name="Número de Factura")
    
    # Relaciones
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name="Suscripción"
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name="Organización"
    )
    
    # Montos
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='MXN')
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Fechas
    issued_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Periodo facturado
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Detalles
    line_items = models.JSONField(default=list, verbose_name="Conceptos")
    notes = models.TextField(blank=True)
    
    # Pago
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=255, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Factura {self.number} - {self.organization.name}"
    
    def save(self, *args, **kwargs):
        if not self.number:
            # Generar número de factura
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                number__startswith=f'INV-{year}'
            ).order_by('-number').first()
            
            if last_invoice:
                try:
                    last_num = int(last_invoice.number.split('-')[-1])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
            
            self.number = f'INV-{year}-{new_num:06d}'
        
        super().save(*args, **kwargs)


class PaymentMethod(models.Model):
    """
    Métodos de pago registrados por las organizaciones
    """
    TYPE_CHOICES = [
        ('card', 'Tarjeta de Crédito/Débito'),
        ('bank_transfer', 'Transferencia Bancaria'),
        ('cash', 'Efectivo'),
        ('check', 'Cheque'),
        ('deposit', 'Deposito Bancario'),
        ('paypal', 'PayPal'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=100, verbose_name="Nombre/Alias")
    
    # Para tarjetas
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)  # visa, mastercard, etc.
    card_exp_month = models.PositiveSmallIntegerField(null=True, blank=True)
    card_exp_year = models.PositiveSmallIntegerField(null=True, blank=True)
    
    # Para bancos
    bank_name = models.CharField(max_length=100, blank=True)
    
    # Estado
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Integración externa
    external_id = models.CharField(max_length=255, blank=True)  # ID de Stripe, etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'
    
    def __str__(self):
        if self.type == 'card':
            return f"{self.card_brand} ****{self.card_last_four}"
        return self.name
