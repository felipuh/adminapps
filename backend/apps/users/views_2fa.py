"""
2FA API Endpoints - AdminApps
Setup, verification, and management of two-factor authentication
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
import pyotp
import qrcode
from io import BytesIO
import base64

from apps.users.models import User
from apps.users.models_2fa import TwoFactorAuth, TwoFactorAuthLog


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_2fa_setup(request):
    """
    POST /api/auth/2fa/setup/initiate/
    
    Initiates 2FA setup for the current user.
    Returns a TOTP secret and QR code.
    """
    user = request.user
    
    # Get or create 2FA config
    try:
        two_fa = user.two_factor_auth
        if two_fa.is_enabled:
            raise ValidationError('2FA is already enabled for this user')
    except TwoFactorAuth.DoesNotExist:
        two_fa = TwoFactorAuth.objects.create(user=user)
    
    # Generate new secret
    secret = two_fa.generate_secret()
    two_fa.secret = secret
    two_fa.save()
    
    # Generate QR code
    totp = pyotp.TOTP(secret)
    provision_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name='AdminApps 2FA'
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provision_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    
    # Convert to base64
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    qr_code_base64 = base64.b64encode(img_bytes.getvalue()).decode()
    
    # Log event
    TwoFactorAuthLog.objects.create(
        user=user,
        event_type='setup_initiated',
        status='success',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    return Response({
        'secret': secret,
        'qr_code': f'data:image/png;base64,{qr_code_base64}',
        'manual_entry_key': secret,
        'message': 'Scan the QR code with your authenticator app or enter the manual entry key'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa_setup(request):
    """
    POST /api/auth/2fa/setup/verify/
    Body: { "token": "123456" }
    
    Verifies the OTP token to complete 2FA setup.
    Generates and returns backup codes.
    """
    user = request.user
    token = request.data.get('token')
    
    if not token:
        raise ValidationError({'token': 'OTP token is required'})
    
    try:
        two_fa = user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        raise ValidationError('2FA setup was not initiated')
    
    # Verify token
    if not two_fa.verify_token(token):
        TwoFactorAuthLog.objects.create(
            user=user,
            event_type='setup_cancelled',
            status='failure',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            details={'reason': 'Invalid OTP token'}
        )
        raise ValidationError({'token': 'Invalid OTP token. Please try again.'})
    
    # Generate backup codes
    backup_codes = two_fa.generate_backup_codes(count=10)
    two_fa.is_enabled = True
    two_fa.verified_at = timezone.now()
    two_fa.save()
    
    # Log event
    TwoFactorAuthLog.objects.create(
        user=user,
        event_type='setup_verified',
        status='success',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        details={'backup_codes_count': len(backup_codes)}
    )
    
    return Response({
        'status': 'enabled',
        'verified_at': two_fa.verified_at.isoformat(),
        'backup_codes': backup_codes,
        'message': 'Save these backup codes in a safe place. You can use them to access your account if you lose access to your authenticator app.'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa_token(request):
    """
    POST /api/auth/2fa/verify/
    Body: { "token": "123456" }
    
    Verifies an OTP token during login or for sensitive operations.
    Used by login flow to complete authentication.
    Returns user data on successful verification.
    
    Rate limited: Max 5 failed attempts in 15 minutes.
    """
    from apps.users.rate_limit import (
        check_two_fa_rate_limit,
        increment_two_fa_attempts,
        reset_two_fa_attempts,
        MAX_TWO_FA_ATTEMPTS
    )
    
    user = request.user
    token = request.data.get('token')
    
    # Check rate limit before processing
    try:
        check_two_fa_rate_limit(user)
    except PermissionDenied as e:
        raise e
    
    if not token:
        raise ValidationError({'token': 'OTP token is required'})
    
    try:
        two_fa = user.two_factor_auth
        if not two_fa.is_enabled:
            raise PermissionDenied('2FA is not enabled for this user')
    except TwoFactorAuth.DoesNotExist:
        raise PermissionDenied('2FA is not configured')
    
    # Try OTP token
    if two_fa.verify_token(token):
        # Record login if it wasn't already recorded
        if hasattr(user, 'record_login'):
            user.record_login()
        
        # Reset rate limit on successful verification
        reset_two_fa_attempts(user)
        
        TwoFactorAuthLog.objects.create(
            user=user,
            event_type='token_verified',
            status='success',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        # Return user data for login completion
        return Response({
            'status': 'verified',
            'message': 'OTP token verified successfully',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'organization_id': str(user.organization.id) if user.organization else None,
                'organization_name': user.organization.name if user.organization else None,
                'theme': user.theme,
                'avatar': user.avatar.url if user.avatar else None,
            },
            'remaining_attempts': MAX_TWO_FA_ATTEMPTS
        })
    
    # Try backup code
    if two_fa.use_backup_code(token):
        two_fa.save()
        
        # Record login if it wasn't already recorded
        if hasattr(user, 'record_login'):
            user.record_login()
        
        # Reset rate limit on successful verification
        reset_two_fa_attempts(user)
        
        TwoFactorAuthLog.objects.create(
            user=user,
            event_type='backup_code_used',
            status='success',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        return Response({
            'status': 'verified',
            'message': 'Backup code used successfully. Consider regenerating your backup codes.',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'organization_id': str(user.organization.id) if user.organization else None,
                'organization_name': user.organization.name if user.organization else None,
                'theme': user.theme,
                'avatar': user.avatar.url if user.avatar else None,
            },
            'remaining_attempts': MAX_TWO_FA_ATTEMPTS
        })
    
    # Token invalid - increment rate limit
    attempts = increment_two_fa_attempts(user)
    remaining = MAX_TWO_FA_ATTEMPTS - attempts
    
    TwoFactorAuthLog.objects.create(
        user=user,
        event_type='token_failed',
        status='failure',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    error_data = {'token': 'Invalid OTP token or backup code'}
    error_data['remaining_attempts'] = max(0, remaining)
    
    if remaining <= 2 and remaining > 0:
        error_data['warning'] = f'Only {remaining} attempt(s) remaining before lockout'
    
    raise ValidationError(error_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_2fa(request):
    """
    POST /api/auth/2fa/disable/
    
    Disables 2FA for the current user.
    Requires re-authentication.
    """
    user = request.user
    password = request.data.get('password')
    
    if not password:
        raise ValidationError({'password': 'Password is required to disable 2FA'})
    
    # Verify password
    if not user.check_password(password):
        raise PermissionDenied('Invalid password')
    
    try:
        two_fa = user.two_factor_auth
        two_fa.disable(reason='User requested')
        two_fa.save()
    except TwoFactorAuth.DoesNotExist:
        raise ValidationError('2FA is not configured')
    
    # Log event
    TwoFactorAuthLog.objects.create(
        user=user,
        event_type='disabled',
        status='success',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    return Response({'status': 'disabled', 'message': '2FA has been disabled'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_2fa_status(request):
    """
    GET /api/auth/2fa/status/
    
    Returns the current 2FA status for the user.
    """
    user = request.user
    
    try:
        two_fa = user.two_factor_auth
        return Response({
            'is_enabled': two_fa.is_enabled,
            'verified_at': two_fa.verified_at.isoformat() if two_fa.verified_at else None,
            'backup_codes_available': len([i for i in range(10) if i not in two_fa.backup_codes_used])
        })
    except TwoFactorAuth.DoesNotExist:
        return Response({
            'is_enabled': False,
            'verified_at': None,
            'backup_codes_available': 0
        })


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
