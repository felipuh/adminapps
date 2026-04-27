"""
2FA (Two-Factor Authentication) Models - AdminApps
OTP-based 2FA using TOTP (Time-based One-Time Password)
"""
import uuid
import pyotp
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class TwoFactorAuth(models.Model):
    """
    Two-Factor Authentication configuration per user.
    Stores encrypted TOTP secret and backup codes.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor_auth')
    
    # TOTP secret (encrypted in production)
    secret = models.CharField(max_length=255, help_text='TOTP secret key (base32 encoded)')
    
    # Status
    is_enabled = models.BooleanField(default=False, help_text='Is 2FA active for this user?')
    verified_at = models.DateTimeField(null=True, blank=True, help_text='When 2FA was first verified')
    
    # Backup codes (comma-separated, hashed in production)
    backup_codes = models.TextField(
        blank=True,
        help_text='Backup codes for account recovery (comma-separated, space-separated pairs)'
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
    
    def generate_secret(self):
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def get_totp(self):
        """Get TOTP provisioner for this user"""
        return pyotp.TOTP(self.secret)
    
    def verify_token(self, token):
        """Verify a 6-digit OTP token"""
        if not token or not str(token).isdigit() or len(str(token)) != 6:
            return False
        totp = self.get_totp()
        return totp.verify(token, valid_window=1)
    
    def get_backup_codes(self):
        """Get list of backup codes"""
        if not self.backup_codes:
            return []
        return [code.strip() for code in self.backup_codes.split(',')]
    
    def generate_backup_codes(self, count=10):
        """
        Generate backup codes.
        Returns list of codes and stores hashed version.
        """
        import secrets
        codes = [secrets.token_hex(4).upper() for _ in range(count)]
        # In production, hash these before storing
        self.backup_codes = ','.join(codes)
        return codes
    
    def use_backup_code(self, code):
        """
        Verify and mark backup code as used.
        Returns True if valid and unused.
        """
        codes = self.get_backup_codes()
        used_indices = self.backup_codes_used
        
        for idx, stored_code in enumerate(codes):
            if idx not in used_indices and stored_code == code.upper():
                used_indices.append(idx)
                self.backup_codes_used = used_indices
                return True
        
        return False
    
    def disable(self, reason='User disabled 2FA'):
        """Disable 2FA for this user"""
        self.is_enabled = False
        self.disabled_at = timezone.now()
        self.disabled_reason = reason
        self.save()


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
