"""
2FA (Two-Factor Authentication) Models - AdminApps
OTP-based 2FA using TOTP (Time-based One-Time Password)

SECURITY: Secretos TOTP y backup codes están cifrados en reposo.
"""
import uuid
import pyotp
import logging
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import hashlib

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_encryption_key():
    """Derive encryption key from Django SECRET_KEY"""
    secret = settings.SECRET_KEY.encode()
    # Derive a 32-byte key from SECRET_KEY
    key_material = hashlib.sha256(secret).digest()
    # Fernet requires base64-encoded 32-byte key
    return base64.urlsafe_b64encode(key_material)


def _encrypt_value(value):
    """Encrypt a string value"""
    if not value:
        return None
    try:
        f = Fernet(_get_encryption_key())
        return f.encrypt(value.encode()).decode()
    except Exception:
        logger.error("Encryption failed")
        raise ValueError("Failed to encrypt sensitive data")


def _decrypt_value(encrypted_value):
    """Decrypt an encrypted string value"""
    if not encrypted_value:
        return None
    try:
        f = Fernet(_get_encryption_key())
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception:
        logger.error("Decryption failed")
        # Si falla la desencriptación, retornar None en lugar de fallar
        # (puede haber claves antiguas)
        return None


class TwoFactorAuth(models.Model):
    """
    Two-Factor Authentication configuration per user.
    Almacena secreto TOTP y backup codes CIFRADOS en reposo.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor_auth')
    
    # SECURITY FIX C4: TOTP secret cifrado
    _secret_encrypted = models.TextField(
        db_column='secret_encrypted',
        blank=True,
        help_text='TOTP secret encriptado (DO NOT ACCESS DIRECTLY - use .secret property)'
    )
    
    # Shared anti-replay state, serialized by the user/configuration row locks.
    generation = models.UUIDField(default=uuid.uuid4, editable=False)
    last_totp_counter = models.BigIntegerField(null=True, blank=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    attempts_expires_at = models.DateTimeField(null=True, blank=True)

    # Status
    is_enabled = models.BooleanField(default=False, help_text='Is 2FA active for this user?')
    verified_at = models.DateTimeField(null=True, blank=True, help_text='When 2FA was first verified')
    
    # SECURITY FIX C4: Backup codes cifrados
    _backup_codes_encrypted = models.TextField(
        db_column='backup_codes_encrypted',
        blank=True,
        help_text='Backup codes encriptados (DO NOT ACCESS DIRECTLY - use .backup_codes property)'
    )
    backup_codes_used = models.JSONField(default=list, help_text='List of used backup code indices')
    
    # Recovery
    disabled_at = models.DateTimeField(null=True, blank=True, help_text='When 2FA was disabled')
    disabled_reason = models.CharField(max_length=255, blank=True, help_text='Why 2FA was disabled')
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'two_factor_auth'
        verbose_name = '2FA Configuration'
        verbose_name_plural = '2FA Configurations'
    
    def __str__(self):
        return f"2FA for {self.user.email} - {'Enabled' if self.is_enabled else 'Disabled'}"
    
    @property
    def secret(self):
        """Obtener secreto descifrado"""
        if not self._secret_encrypted:
            return None
        return _decrypt_value(self._secret_encrypted)
    
    @secret.setter
    def secret(self, value):
        """Rotate the generation whenever a secret is assigned."""
        self.generation = uuid.uuid4()
        self.last_totp_counter = None
        if value:
            self._secret_encrypted = _encrypt_value(value)
        else:
            self._secret_encrypted = None
    
    @property
    def backup_codes(self):
        """Obtener backup codes descifrados"""
        if not self._backup_codes_encrypted:
            return ""
        decrypted = _decrypt_value(self._backup_codes_encrypted)
        return decrypted or ""
    
    @backup_codes.setter
    def backup_codes(self, value):
        """Cifrar y almacenar backup codes"""
        if value:
            self._backup_codes_encrypted = _encrypt_value(value)
        else:
            self._backup_codes_encrypted = None
    
    def generate_secret(self):
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def get_totp(self):
        """Get TOTP provisioner for this user"""
        secret = self.secret
        if not secret:
            return None
        return pyotp.TOTP(secret)
    
    def verify_token(self, token):
        """Consume a factor through the same persistent ledger as login/SSO."""
        from .two_factor_service import consume_factor
        accepted = consume_factor(self.user_id, token, allow_backup=False)
        self.refresh_from_db()
        return accepted

    def get_backup_codes(self):
        """Get list of backup codes (decrypted)"""
        codes_str = self.backup_codes
        if not codes_str:
            return []
        return [code.strip() for code in codes_str.split(',')]
    
    def generate_backup_codes(self, count=10):
        """
        Generate backup codes.
        Returns list of codes y stores encrypted version.
        """
        import secrets
        codes = [secrets.token_hex(4).upper() for _ in range(count)]
        # SECURITY FIX C4: Backup codes encriptados antes de almacenar
        self.backup_codes = ','.join(codes)
        return codes
    
    def use_backup_code(self, code):
        """Consume under shared locks; callers must not save a stale instance."""
        from .two_factor_service import consume_factor
        accepted = consume_factor(self.user_id, code, backup_only=True)
        self.refresh_from_db()
        return accepted

    def disable(self, reason='User disabled 2FA'):
        from .two_factor_service import disable_configuration
        disable_configuration(self.user_id, reason=reason)
        self.refresh_from_db()


class TwoFactorChallenge(models.Model):
    """Only a nonce digest and bound metadata are persisted, never the token."""

    nonce_digest = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.PositiveSmallIntegerField(default=1)
    purpose = models.CharField(max_length=40)
    scope = models.CharField(max_length=40)
    generation = models.UUIDField()
    context_digest = models.CharField(max_length=64)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'two_factor_challenges'


class TwoFactorAuthLog(models.Model):
    """
    Audit log for 2FA events (verification, enable/disable, backup code use, etc.)
    """
    
    EVENT_TYPES = [
        ('setup_initiated', 'Setup Initiated'),
        ('setup_verified', '2FA Setup Verified'),
        ('setup_cancelled', 'Setup Cancelled'),
        ('enabled', '2FA Enabled'),
        ('disabled', '2FA Disabled'),
        ('token_verified', 'OTP Token Verified'),
        ('token_failed', 'OTP Token Failed'),
        ('backup_code_used', 'Backup Code Used'),
        ('backup_code_invalid', 'Backup Code Invalid'),
        ('recovery_attempted', 'Recovery Attempted'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='two_factor_logs')
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Event details
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('failure', 'Failure'), ('pending', 'Pending')],
        default='pending'
    )
    details = models.JSONField(default=dict, help_text='Event-specific data')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'two_factor_auth_logs'
        verbose_name = '2FA Audit Log'
        verbose_name_plural = '2FA Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_event_type_display()} ({self.created_at.date()})"
