"""
2FA API Endpoints - AdminApps
Setup, verification, and management of two-factor authentication
"""
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError, PermissionDenied
from django.db import transaction
import pyotp
import qrcode
from io import BytesIO
import base64

from apps.users.models_2fa import TwoFactorAuth
from apps.users.serializers import CustomTokenObtainPairSerializer
from . import two_factor_service as two_factor


def _verification_challenge(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.lower().startswith('bearer '):
        raise PermissionDenied('2FA verification token required')
    return auth_header.split(' ', 1)[1].strip()


def _issue_verified_2fa_tokens(user):
    """Use the standard login issuer and claims, only after factor verification."""
    try:
        two_factor.require_commit_boundary()
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        return {'access': str(refresh.access_token), 'refresh': str(refresh)}
    except Exception:
        # Never expose issuer/persistence errors or return a partial token pair.
        raise APIException('Unable to complete 2FA authentication') from None


@transaction.non_atomic_requests
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_2fa_setup(request):
    """
    POST /api/auth/2fa/setup/initiate/
    
    Initiates 2FA setup for the current user.
    Returns a TOTP secret and QR code.
    """
    user = request.user
    
    secret = two_factor.initiate_configuration(user.pk)

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
    
    return Response({
        'secret': secret,
        'qr_code': f'data:image/png;base64,{qr_code_base64}',
        'manual_entry_key': secret,
        'message': 'Scan the QR code with your authenticator app or enter the manual entry key'
    })


@transaction.non_atomic_requests
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
    
    two_fa, backup_codes = two_factor.verify_configuration(user.pk, token)

    return Response({
        'status': 'enabled',
        'verified_at': two_fa.verified_at.isoformat(),
        'backup_codes': backup_codes,
        'message': 'Save these backup codes in a safe place. You can use them to access your account if you lose access to your authenticator app.'
    }, status=status.HTTP_201_CREATED)


@transaction.non_atomic_requests
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@two_factor.sanitize_database_errors
def verify_2fa_token(request):
    """
    POST /api/auth/2fa/verify/
    Body: { "token": "123456" }
    
    Verifies an OTP token during login or for sensitive operations.
    Used by login flow to complete authentication.
    Returns user data and the standard JWT pair on successful verification.
    
    Rate limited: Max 5 failed attempts in 15 minutes.
    """
    token = request.data.get('token')
    if not token:
        raise ValidationError({'token': 'OTP token is required'})
    user, event = two_factor.consume_challenge(
        _verification_challenge(request), token, request=request,
    )
    # The service has returned only after its durable transaction committed.
    tokens = _issue_verified_2fa_tokens(user)
    user.record_login()
    message = ('Backup code used successfully. Consider regenerating your backup codes.'
               if event == 'backup_code_used' else 'OTP token verified successfully')
    return Response({
        'status': 'verified', **tokens, 'message': message,
        'user': {
            'id': str(user.id), 'email': user.email, 'full_name': user.full_name,
            'role': user.role,
            'organization_id': str(user.organization.id) if user.organization else None,
            'organization_name': user.organization.name if user.organization else None,
            'theme': user.theme, 'avatar': user.avatar.url if user.avatar else None,
        },
        'remaining_attempts': two_factor.MAX_ATTEMPTS,
    })


@transaction.non_atomic_requests
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
    
    two_factor.disable_configuration(user.pk, password=password, reason='User requested')

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
