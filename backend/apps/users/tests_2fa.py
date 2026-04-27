"""
2FA Tests - AdminApps
Tests for two-factor authentication setup, verification, and management
"""
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
import pyotp

from apps.organizations.models import Organization
from apps.users.models import User
from apps.users.models_2fa import TwoFactorAuth, TwoFactorAuthLog


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TwoFactorAuthSetupTests(APITestCase):
    """Tests for 2FA setup flow"""
    
    def setUp(self):
        self.org = Organization.objects.create(
            code='TEST_ORG_2FA',
            name='Test Org 2FA',
            email='test@example.com'
        )
        self.user = User.objects.create(
            email='user_2fa@example.com',
            first_name='Test',
            last_name='User',
            organization=self.org,
            is_active=True,
        )
        self.user.set_password('TestPass123!')
        self.user.save()
    
    def test_unauthenticated_cannot_initiate_2fa(self):
        """Unauthenticated users cannot initiate 2FA"""
        response = self.client.post('/api/auth/2fa/setup/initiate/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_initiate_2fa_setup_returns_secret_and_qr(self):
        """Initiating 2FA setup returns secret and QR code"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/2fa/setup/initiate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('secret', response.data)
        self.assertIn('qr_code', response.data)
        self.assertIn('manual_entry_key', response.data)
        self.assertTrue(response.data['qr_code'].startswith('data:image/png;base64,'))
    
    def test_2fa_config_created_on_initiate(self):
        """2FA config is created when setup is initiated"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/2fa/setup/initiate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(TwoFactorAuth.objects.filter(user=self.user).exists())
    
    def test_verify_2fa_with_invalid_token(self):
        """Verifying 2FA with invalid token fails"""
        self.client.force_authenticate(user=self.user)
        
        # Initiate setup
        self.client.post('/api/auth/2fa/setup/initiate/')
        
        # Try invalid token
        response = self.client.post('/api/auth/2fa/setup/verify/', {'token': '000000'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid OTP token', str(response.data))
    
    def test_verify_2fa_with_valid_token(self):
        """Verifying 2FA with valid token enables it"""
        self.client.force_authenticate(user=self.user)
        
        # Initiate setup and get secret
        init_response = self.client.post('/api/auth/2fa/setup/initiate/')
        secret = init_response.data['secret']
        
        # Generate valid token
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        # Verify with valid token
        response = self.client.post('/api/auth/2fa/setup/verify/', {'token': token})
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'enabled')
        self.assertIn('backup_codes', response.data)
        self.assertEqual(len(response.data['backup_codes']), 10)
        
        # Verify 2FA is now enabled
        two_fa = TwoFactorAuth.objects.get(user=self.user)
        self.assertTrue(two_fa.is_enabled)
        self.assertIsNotNone(two_fa.verified_at)
    
    def test_cannot_setup_2fa_twice_simultaneously(self):
        """Cannot initiate 2FA setup if already enabled"""
        self.client.force_authenticate(user=self.user)
        
        # First setup
        init_response = self.client.post('/api/auth/2fa/setup/initiate/')
        secret1 = init_response.data['secret']
        totp = pyotp.TOTP(secret1)
        self.client.post('/api/auth/2fa/setup/verify/', {'token': totp.now()})
        
        # Try second setup while already enabled
        response = self.client.post('/api/auth/2fa/setup/initiate/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already enabled', str(response.data))


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TwoFactorAuthVerificationTests(APITestCase):
    """Tests for 2FA token verification during login/operations"""
    
    def setUp(self):
        self.org = Organization.objects.create(
            code='TEST_ORG_VERIFY',
            name='Test Org Verify',
            email='test@example.com'
        )
        self.user = User.objects.create(
            email='verify_2fa@example.com',
            first_name='Verify',
            last_name='User',
            organization=self.org,
            is_active=True,
        )
        self.user.set_password('VerifyPass123!')
        self.user.save()
        
        # Setup 2FA for this user
        self.client.force_authenticate(user=self.user)
        init_response = self.client.post('/api/auth/2fa/setup/initiate/')
        self.secret = init_response.data['secret']
        totp = pyotp.TOTP(self.secret)
        setup_response = self.client.post('/api/auth/2fa/setup/verify/', {'token': totp.now()})
        self.backup_codes = setup_response.data['backup_codes']
    
    def test_verify_2fa_token(self):
        """Verifying valid OTP token succeeds"""
        self.client.force_authenticate(user=self.user)
        
        totp = pyotp.TOTP(self.secret)
        response = self.client.post('/api/auth/2fa/verify/', {'token': totp.now()})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'verified')
    
    def test_verify_with_invalid_token(self):
        """Verifying with invalid token fails"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/auth/2fa/verify/', {'token': '000000'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verify_with_backup_code(self):
        """Verifying with backup code succeeds and marks it as used"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/auth/2fa/verify/', {'token': self.backup_codes[0]})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'verified')
        self.assertIn('backup code used', response.data['message'].lower())
    
    def test_cannot_reuse_backup_code(self):
        """Backup codes can only be used once"""
        self.client.force_authenticate(user=self.user)
        
        code = self.backup_codes[0]
        
        # Use backup code once
        self.client.post('/api/auth/2fa/verify/', {'token': code})
        
        # Try to use same backup code again
        response = self.client.post('/api/auth/2fa/verify/', {'token': code})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TwoFactorAuthDisableTests(APITestCase):
    """Tests for disabling 2FA"""
    
    def setUp(self):
        self.org = Organization.objects.create(
            code='TEST_ORG_DISABLE',
            name='Test Org Disable',
            email='test@example.com'
        )
        self.user = User.objects.create(
            email='disable_2fa@example.com',
            first_name='Disable',
            last_name='User',
            organization=self.org,
            is_active=True,
        )
        self.user.set_password('DisablePass123!')
        self.user.save()
        
        # Setup 2FA for this user
        self.client.force_authenticate(user=self.user)
        init_response = self.client.post('/api/auth/2fa/setup/initiate/')
        secret = init_response.data['secret']
        totp = pyotp.TOTP(secret)
        self.client.post('/api/auth/2fa/setup/verify/', {'token': totp.now()})
    
    def test_disable_2fa_requires_password(self):
        """Disabling 2FA requires password verification"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/auth/2fa/disable/', {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_disable_2fa_with_wrong_password(self):
        """Disabling 2FA with wrong password fails"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/auth/2fa/disable/', {'password': 'WrongPass123!'})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_disable_2fa_with_correct_password(self):
        """Disabling 2FA with correct password succeeds"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/auth/2fa/disable/', {'password': 'DisablePass123!'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'disabled')
        
        # Verify 2FA is disabled
        two_fa = TwoFactorAuth.objects.get(user=self.user)
        self.assertFalse(two_fa.is_enabled)
        self.assertIsNotNone(two_fa.disabled_at)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TwoFactorAuthStatusTests(APITestCase):
    """Tests for checking 2FA status"""
    
    def setUp(self):
        self.org = Organization.objects.create(
            code='TEST_ORG_STATUS',
            name='Test Org Status',
            email='test@example.com'
        )
        self.user = User.objects.create(
            email='status_2fa@example.com',
            first_name='Status',
            last_name='User',
            organization=self.org,
            is_active=True,
        )
        self.user.set_password('StatusPass123!')
        self.user.save()
    
    def test_get_2fa_status_not_enabled(self):
        """Getting 2FA status when not enabled"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/2fa/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_enabled'])
        self.assertIsNone(response.data['verified_at'])
        self.assertEqual(response.data['backup_codes_available'], 0)
    
    def test_get_2fa_status_enabled(self):
        """Getting 2FA status when enabled"""
        self.client.force_authenticate(user=self.user)
        
        # Setup 2FA
        init_response = self.client.post('/api/auth/2fa/setup/initiate/')
        secret = init_response.data['secret']
        totp = pyotp.TOTP(secret)
        self.client.post('/api/auth/2fa/setup/verify/', {'token': totp.now()})
        
        # Check status
        response = self.client.get('/api/auth/2fa/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_enabled'])
        self.assertIsNotNone(response.data['verified_at'])
        self.assertEqual(response.data['backup_codes_available'], 10)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TwoFactorAuthLoggingTests(APITestCase):
    """Tests for 2FA audit logging"""
    
    def setUp(self):
        self.org = Organization.objects.create(
            code='TEST_ORG_LOG',
            name='Test Org Log',
            email='test@example.com'
        )
        self.user = User.objects.create(
            email='log_2fa@example.com',
            first_name='Log',
            last_name='User',
            organization=self.org,
            is_active=True,
        )
        self.user.set_password('LogPass123!')
        self.user.save()
    
    def test_2fa_events_logged(self):
        """2FA events are logged to audit trail"""
        self.client.force_authenticate(user=self.user)
        
        # Initiate setup
        self.client.post('/api/auth/2fa/setup/initiate/')
        self.assertTrue(TwoFactorAuthLog.objects.filter(
            user=self.user,
            event_type='setup_initiated'
        ).exists())
        
        # Verify setup with valid token
        init_response = self.client.post('/api/auth/2fa/setup/initiate/')
        secret = init_response.data['secret']
        totp = pyotp.TOTP(secret)
        self.client.post('/api/auth/2fa/setup/verify/', {'token': totp.now()})
        
        self.assertTrue(TwoFactorAuthLog.objects.filter(
            user=self.user,
            event_type='setup_verified',
            status='success'
        ).exists())


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class LoginWith2FATests(APITestCase):
    """Tests for login flow with 2FA enabled"""
    
    def setUp(self):
        self.org = Organization.objects.create(
            code='TEST_ORG_LOGIN_2FA',
            name='Test Org Login 2FA',
            email='test@example.com'
        )
        self.user = User.objects.create(
            email='login_2fa@example.com',
            first_name='Login',
            last_name='User2FA',
            organization=self.org,
            is_active=True,
        )
        self.user.set_password('LoginPass123!')
        self.user.save()
        
        # Setup 2FA for this user
        two_fa = TwoFactorAuth.objects.create(user=self.user)
        secret = two_fa.generate_secret()
        two_fa.secret = secret
        two_fa.is_enabled = True
        two_fa.verified_at = timezone.now()
        backup_codes = two_fa.generate_backup_codes()
        two_fa.save()
        self.secret = secret
        self.backup_codes = backup_codes
    
    def test_login_with_2fa_enabled_requires_token(self):
        """Login with 2FA enabled returns requires_2fa flag"""
        response = self.client.post('/api/auth/login/', {
            'email': 'login_2fa@example.com',
            'password': 'LoginPass123!',
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('requires_2fa'))
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'login_2fa@example.com')
        # Should have access token to verify 2FA
        self.assertIn('access', response.data)
    
    def test_login_without_2fa_enabled_works_normally(self):
        """Login without 2FA enabled works as before"""
        # Create user without 2FA
        user_no_2fa = User.objects.create(
            email='no_2fa@example.com',
            first_name='No',
            last_name='2FA',
            organization=self.org,
            is_active=True,
        )
        user_no_2fa.set_password('NoPass123!')
        user_no_2fa.save()
        
        response = self.client.post('/api/auth/login/', {
            'email': 'no_2fa@example.com',
            'password': 'NoPass123!',
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('requires_2fa', False))
        self.assertIn('user', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_verify_2fa_token_after_login(self):
        """Verifying 2FA token after login returns complete user data"""
        # First, login with email/password
        login_response = self.client.post('/api/auth/login/', {
            'email': 'login_2fa@example.com',
            'password': 'LoginPass123!',
        })
        
        access_token = login_response.data['access']
        
        # Now verify 2FA with the access token
        totp = pyotp.TOTP(self.secret)
        response = self.client.post(
            '/api/auth/2fa/verify/',
            {'token': totp.now()},
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'verified')
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'login_2fa@example.com')
        self.assertEqual(response.data['user']['role'], 'user')
        self.assertIsNotNone(response.data['user']['organization_id'])
    
    def test_verify_2fa_with_backup_code_after_login(self):
        """Verifying 2FA with backup code after login"""
        # First, login with email/password
        login_response = self.client.post('/api/auth/login/', {
            'email': 'login_2fa@example.com',
            'password': 'LoginPass123!',
        })
        
        access_token = login_response.data['access']
        
        # Now verify 2FA with backup code
        response = self.client.post(
            '/api/auth/2fa/verify/',
            {'token': self.backup_codes[0]},
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'verified')
        self.assertIn('backup code used', response.data['message'].lower())
    
    def test_invalid_password_login_fails(self):
        """Login with invalid password fails"""
        response = self.client.post('/api/auth/login/', {
            'email': 'login_2fa@example.com',
            'password': 'WrongPass!',
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_2fa_required_is_false_for_user_without_2fa(self):
        """2FA required is false for users without 2FA setup"""
        user_no_2fa = User.objects.create(
            email='no_2fa_test@example.com',
            first_name='NoTest',
            last_name='User',
            organization=self.org,
            is_active=True,
        )
        user_no_2fa.set_password('NoPass123!')
        user_no_2fa.save()
        
        response = self.client.post('/api/auth/login/', {
            'email': 'no_2fa_test@example.com',
            'password': 'NoPass123!',
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('requires_2fa', False))
        # Should have refresh token for normal login
        self.assertIn('refresh', response.data)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TwoFactorAuthRateLimitTests(APITestCase):
    """Tests for 2FA rate limiting to prevent brute force attacks"""
    
    def setUp(self):
        self.org = Organization.objects.create(
            code='TEST_ORG_RATE_LIMIT',
            name='Test Org Rate Limit',
            email='test@example.com'
        )
        self.user = User.objects.create(
            email='ratelimit@example.com',
            first_name='Rate',
            last_name='Limit',
            organization=self.org,
            is_active=True,
        )
        self.user.set_password('LimitPass123!')
        self.user.save()
        
        # Setup 2FA for this user
        two_fa = TwoFactorAuth.objects.create(user=self.user)
        secret = two_fa.generate_secret()
        two_fa.secret = secret
        two_fa.is_enabled = True
        two_fa.verified_at = timezone.now()
        two_fa.save()
        self.secret = secret
        
        # Login to get access token
        login_response = self.client.post('/api/auth/login/', {
            'email': 'ratelimit@example.com',
            'password': 'LimitPass123!',
        })
        self.access_token = login_response.data['access']
    
    def test_rate_limit_increments_on_failed_attempts(self):
        """Rate limit should increment on failed OTP attempts"""
        # First failed attempt
        response = self.client.post(
            '/api/auth/2fa/verify/',
            {'token': '000000'},
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(int(response.data['remaining_attempts']), 4)
    
    def test_rate_limit_resets_on_successful_verification(self):
        """Rate limit should reset on successful OTP verification"""
        # Add some failed attempts
        for i in range(2):
            self.client.post(
                '/api/auth/2fa/verify/',
                {'token': '000000'},
                HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
            )
        
        # Verify with correct OTP
        totp = pyotp.TOTP(self.secret)
        response = self.client.post(
            '/api/auth/2fa/verify/',
            {'token': totp.now()},
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['remaining_attempts'], 5)
    
    def test_rate_limit_blocks_after_max_attempts(self):
        """Should block after MAX_TWO_FA_ATTEMPTS (5) failed attempts"""
        # Make 5 failed attempts
        for i in range(5):
            response = self.client.post(
                '/api/auth/2fa/verify/',
                {'token': '000000'},
                HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 6th attempt should be blocked (403 Forbidden - rate limited)
        response = self.client.post(
            '/api/auth/2fa/verify/',
            {'token': '123456'},
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
    
    def test_rate_limit_shows_warning_when_near_limit(self):
        """Should show warning when user is near rate limit"""
        # Make 3 failed attempts (2 left)
        for i in range(3):
            self.client.post(
                '/api/auth/2fa/verify/',
                {'token': '000000'},
                HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
            )
        
        # 4th attempt should show warning
        response = self.client.post(
            '/api/auth/2fa/verify/',
            {'token': '000000'},
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(int(response.data['remaining_attempts']), 1)
        self.assertIn('warning', response.data)
        self.assertIn('1 attempt', response.data['warning'].lower())
    
    def test_rate_limit_returns_403_with_details(self):
        """Rate limited response (403) should include helpful details"""
        # Make 5 failed attempts to trigger lockout
        for i in range(5):
            self.client.post(
                '/api/auth/2fa/verify/',
                {'token': '000000'},
                HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
            )
        
        # Try again - should get 403
        response = self.client.post(
            '/api/auth/2fa/verify/',
            {'token': '123456'},
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
