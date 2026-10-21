"""
Modelos de Usuarios para Admin Apps
Sistema centralizado de usuarios para todo el ecosistema
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
import uuid


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El email es obligatorio'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_platform_admin', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser debe tener is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Modelo de Usuario centralizado para Admin Apps
    Gestiona usuarios de todo el ecosistema (ISO Smart, etc.)
    """
    
    username = None  # Removemos username
    
    # Identificadores
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(_('email'), unique=True)
    
    # Información personal
    first_name = models.CharField(_('nombre'), max_length=150)
    last_name = models.CharField(_('apellido'), max_length=150)
    phone = models.CharField(_('teléfono'), max_length=20, blank=True)
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)
    
    # Roles de plataforma (Admin Apps)
    is_platform_admin = models.BooleanField(
        _('administrador de plataforma'),
        default=False,
        help_text=_('Acceso total a Admin Apps y todas las organizaciones')
    )
    
    # Control
    is_active = models.BooleanField(_('activo'), default=True)
    email_verified = models.BooleanField(_('email verificado'), default=False)
    must_change_password = models.BooleanField(_('debe cambiar contraseña'), default=False)
    
    # Preferencias globales
    language = models.CharField(_('idioma'), max_length=10, default='es')
    timezone = models.CharField(_('zona horaria'), max_length=50, default='America/Mexico_City')
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def get_organizations(self):
        """Retorna las organizaciones a las que pertenece el usuario"""
        return [membership.organization for membership in self.memberships.filter(is_active=True)]
    
    def get_primary_organization(self):
        """Retorna la organización principal del usuario"""
        membership = self.memberships.filter(is_active=True, is_primary=True).first()
        if membership:
            return membership.organization
        # Si no hay primaria, retornar la primera activa
        membership = self.memberships.filter(is_active=True).first()
        return membership.organization if membership else None


class OrganizationMembership(models.Model):
    """
    Membresía de usuario en una organización
    Un usuario puede pertenecer a múltiples organizaciones con diferentes roles
    """
    
    ROLE_CHOICES = [
        ('org_admin', 'Administrador'),
        ('iso_manager', 'Responsable SGC'),
        ('auditor', 'Auditor'),
        ('user', 'Usuario'),
        ('viewer', 'Solo Lectura'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='users'
    )
    role = models.CharField(_('rol'), max_length=20, choices=ROLE_CHOICES, default='user')
    
    # Información adicional por organización
    job_title = models.CharField(_('cargo'), max_length=100, blank=True)
    department = models.CharField(_('departamento'), max_length=100, blank=True)
    
    # Control
    is_primary = models.BooleanField(
        _('organización principal'),
        default=False,
        help_text=_('Organización por defecto al iniciar sesión')
    )
    is_active = models.BooleanField(_('activo en organización'), default=True)
    
    # Metadatos
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invitations'
    )
    
    class Meta:
        db_table = 'organization_memberships'
        unique_together = ['user', 'organization']
        verbose_name = _('membresía')
        verbose_name_plural = _('membresías')
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Si es la primera membresía del usuario, hacerla primaria
        if not self.pk and not OrganizationMembership.objects.filter(user=self.user).exists():
            self.is_primary = True
        super().save(*args, **kwargs)
    
    # Helpers de permisos
    def is_admin(self):
        return self.role == 'org_admin'
    
    def is_manager(self):
        return self.role in ['org_admin', 'iso_manager']
    
    def can_edit(self):
        return self.role in ['org_admin', 'iso_manager', 'user']
    
    def can_audit(self):
        return self.role in ['org_admin', 'iso_manager', 'auditor']


class UserSession(models.Model):
    """Registro de sesiones activas"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True
    )
    token_hash = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sesión de {self.user.email} ({self.created_at})"
