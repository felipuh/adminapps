"""
Modelos de Organizaciones para Admin Apps
"""
from django.db import models
from django.utils.text import slugify
import uuid


class Organization(models.Model):
    """Organización/Cliente del sistema"""
    
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('basic', 'Básico'),
        ('professional', 'Profesional'),
        ('enterprise', 'Empresarial'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('trial', 'Prueba'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Información básica
    name = models.CharField('Nombre', max_length=255)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    legal_name = models.CharField('Razón Social', max_length=255, blank=True)
    tax_id = models.CharField('NIT/RUC/RFC', max_length=50, blank=True)
    
    # Contacto
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Teléfono', max_length=50, blank=True)
    website = models.URLField('Sitio Web', blank=True)
    address = models.TextField('Dirección', blank=True)
    city = models.CharField('Ciudad', max_length=100, blank=True)
    country = models.CharField('País', max_length=100, blank=True)
    
    # Branding
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#3B82F6')
    
    # Plan y suscripción
    plan = models.CharField('Plan', max_length=20, choices=PLAN_CHOICES, default='trial')
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='trial')
    max_users = models.IntegerField('Máximo de usuarios', default=5)
    trial_ends_at = models.DateTimeField('Fin de prueba', null=True, blank=True)
    subscription_ends_at = models.DateTimeField('Fin de suscripción', null=True, blank=True)
    
    # Módulos habilitados
    module_sca_enabled = models.BooleanField('SCA - Context Analyzer', default=True)
    module_sie_enabled = models.BooleanField('SIE - Stakeholder Intelligence', default=True)
    module_asb_enabled = models.BooleanField('ASB - Scope Builder', default=True)
    module_spm_enabled = models.BooleanField('SPM - Process Mapper', default=True)
    module_documents_enabled = models.BooleanField('Gestión Documental', default=True)
    module_risks_enabled = models.BooleanField('Gestión de Riesgos', default=True)
    module_objectives_enabled = models.BooleanField('Objetivos de Calidad', default=True)
    module_audits_enabled = models.BooleanField('Auditorías', default=False)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_organizations'
    )
    
    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Asegurar unicidad
            original_slug = self.slug
            counter = 1
            while Organization.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    @property
    def user_count(self):
        return self.users.filter(is_active=True).count()
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    def get_enabled_modules(self):
        """Retorna lista de módulos habilitados"""
        modules = []
        if self.module_sca_enabled:
            modules.append({'code': 'SCA', 'name': 'Context Analyzer', 'clause': '4.1'})
        if self.module_sie_enabled:
            modules.append({'code': 'SIE', 'name': 'Stakeholder Intelligence', 'clause': '4.2'})
        if self.module_asb_enabled:
            modules.append({'code': 'ASB', 'name': 'Scope Builder', 'clause': '4.3'})
        if self.module_spm_enabled:
            modules.append({'code': 'SPM', 'name': 'Process Mapper', 'clause': '4.4'})
        if self.module_documents_enabled:
            modules.append({'code': 'DOC', 'name': 'Gestión Documental', 'clause': '7.5'})
        if self.module_risks_enabled:
            modules.append({'code': 'RISK', 'name': 'Gestión de Riesgos', 'clause': '6.1'})
        if self.module_objectives_enabled:
            modules.append({'code': 'OBJ', 'name': 'Objetivos de Calidad', 'clause': '6.2'})
        if self.module_audits_enabled:
            modules.append({'code': 'AUDIT', 'name': 'Auditorías Internas', 'clause': '9.2'})
        return modules


class OrganizationInvitation(models.Model):
    """Invitaciones pendientes a una organización"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, default='user')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invited_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'organization_invitations'
        unique_together = ['organization', 'email', 'status']
    
    def __str__(self):
        return f"Invitación a {self.email} para {self.organization.name}"
