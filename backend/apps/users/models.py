"""
User Models - Admin Apps
Sistema de usuarios con roles y permisos multi-organización
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'superadmin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado
    Soporta múltiples organizaciones y roles
    """
    
    ROLE_CHOICES = [
        ('superadmin', 'Super Administrador'),     # Acceso total a Admin Apps
        ('admin', 'Administrador'),                # Administrador de Admin Apps
        ('org_admin', 'Administrador de Org'),     # Administrador de una organización
        ('iso_manager', 'Gestor ISO'),             # Responsable del SGC
        ('auditor', 'Auditor'),                    # Solo lectura + auditorías
        ('user', 'Usuario'),                       # Usuario estándar
        ('viewer', 'Visualizador'),                # Solo lectura
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Email")
    
    # Información personal
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)
    
    # Organización y rol
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="Organización Principal"
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='user', verbose_name="Rol")
    job_title = models.CharField(max_length=100, blank=True, verbose_name="Cargo")
    department = models.CharField(max_length=100, blank=True, verbose_name="Departamento")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_staff = models.BooleanField(default=False, verbose_name="Es Staff")
    is_verified = models.BooleanField(default=False, verbose_name="Email Verificado")
    
    # Seguridad
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)
    
    # Preferencias
    language = models.CharField(max_length=10, default='es', verbose_name="Idioma")
    timezone = models.CharField(max_length=50, default='America/Mexico_City', verbose_name="Zona Horaria")
    theme = models.CharField(
        max_length=20,
        choices=[('light', 'Claro'), ('dark', 'Oscuro'), ('system', 'Sistema')],
        default='dark'
    )
    
    # Notificaciones
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Fechas
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadatos
    metadata = models.JSONField(default=dict, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_locked(self):
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
    
    @property
    def is_superadmin(self):
        return self.role == 'superadmin' or self.is_superuser
    
    @property
    def is_admin(self):
        return self.role in ['superadmin', 'admin'] or self.is_superuser
    
    @property
    def is_org_admin(self):
        return self.role in ['superadmin', 'admin', 'org_admin']
    
    @property
    def is_iso_manager(self):
        return self.role in ['superadmin', 'admin', 'org_admin', 'iso_manager']
    
    @property
    def can_edit(self):
        return self.role not in ['viewer', 'auditor']
    
    def lock_account(self, minutes=30):
        """Bloquear cuenta temporalmente"""
        self.locked_until = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save(update_fields=['locked_until'])
    
    def unlock_account(self):
        """Desbloquear cuenta"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['locked_until', 'failed_login_attempts'])
    
    def record_login(self):
        """Registrar inicio de sesión exitoso"""
        self.last_login_at = timezone.now()
        self.last_activity_at = timezone.now()
        self.failed_login_attempts = 0
        self.save(update_fields=['last_login_at', 'last_activity_at', 'failed_login_attempts'])
    
    def record_failed_login(self):
        """Registrar intento de inicio de sesión fallido"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account(30)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])


class UserOrganization(models.Model):
    """
    Relación muchos a muchos entre usuarios y organizaciones
    Permite que un usuario pertenezca a múltiples organizaciones con diferentes roles
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organization_memberships'
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='user_memberships'
    )
    role = models.CharField(
        max_length=30,
        choices=User.ROLE_CHOICES,
        default='user',
        verbose_name="Rol en Organización"
    )
    
    is_primary = models.BooleanField(default=False, verbose_name="Organización Principal")
    is_active = models.BooleanField(default=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_organizations'
        verbose_name = 'Membresía de Usuario'
        verbose_name_plural = 'Membresías de Usuarios'
        unique_together = ['user', 'organization']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.organization.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        # Si es la primera organización del usuario, marcarla como principal
        if not UserOrganization.objects.filter(user=self.user).exists():
            self.is_primary = True
        super().save(*args, **kwargs)


class UserSession(models.Model):
    """
    Registro de sesiones activas del usuario
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    # Información de sesión
    token_jti = models.CharField(max_length=255, unique=True)  # JWT ID
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # desktop, mobile, tablet
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Estado
    is_active = models.BooleanField(default=True)
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuarios'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sesión: {self.user.email} - {self.created_at}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class UserActivityLog(models.Model):
    """
    Log de actividad del usuario para auditoría
    """
    ACTION_CHOICES = [
        ('login', 'Inicio de Sesión'),
        ('logout', 'Cierre de Sesión'),
        ('password_change', 'Cambio de Contraseña'),
        ('profile_update', 'Actualización de Perfil'),
        ('create', 'Creación'),
        ('update', 'Actualización'),
        ('delete', 'Eliminación'),
        ('view', 'Visualización'),
        ('export', 'Exportación'),
        ('import', 'Importación'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs'
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    module = models.CharField(max_length=100, blank=True)  # Ej: 'documents', 'risks', etc.
    entity_type = models.CharField(max_length=100, blank=True)  # Modelo afectado
    entity_id = models.CharField(max_length=100, blank=True)
    
    description = models.TextField(blank=True)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activity_logs'
        verbose_name = 'Log de Actividad'
        verbose_name_plural = 'Logs de Actividad'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email if self.user else 'Sistema'} - {self.action} - {self.created_at}"
