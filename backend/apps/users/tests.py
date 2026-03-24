from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization
from apps.users.models import User


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    TEMP_PASSWORD_MAX_AGE_DAYS=7,
    TEMP_PASSWORD_WARNING_DAYS=2,
)
class AuthSecurityRegressionTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            code='ORG00001',
            name='Acme Org',
            email='org@example.com',
        )

        self.user = self._create_user(
            email='user@example.com',
            password='InitialPass123!',
            first_name='Regular',
            last_name='User',
            role='user',
        )

        self.org_admin = self._create_user(
            email='org-admin@example.com',
            password='AdminPass123!',
            first_name='Org',
            last_name='Admin',
            role='org_admin',
        )

    def _create_user(self, email, password, first_name, last_name, role):
        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization=self.organization,
            role=role,
            is_active=True,
        )
        user.set_password(password)
        user.save(update_fields=['password'])
        return user

    def _reason_code(self, response):
        reason_code = response.data.get('reason_code') if isinstance(response.data, dict) else None
        if isinstance(reason_code, list):
            return str(reason_code[0]) if reason_code else None
        return str(reason_code) if reason_code is not None else None

    def test_login_rejects_expired_temporary_password(self):
        self.user.mark_temporary_password(when=timezone.now() - timedelta(days=8))
        self.user.save(update_fields=['metadata', 'must_change_password'])

        response = self.client.post(
            '/api/auth/login/',
            {'email': self.user.email, 'password': 'InitialPass123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._reason_code(response), 'TEMP_PASSWORD_EXPIRED')

    def test_login_adds_security_alert_when_temporary_password_near_expiry(self):
        # Remaining time is less than one day, so alert should be emitted.
        self.user.mark_temporary_password(when=timezone.now() - timedelta(days=6, hours=12))
        self.user.save(update_fields=['metadata', 'must_change_password'])

        response = self.client.post(
            '/api/auth/login/',
            {'email': self.user.email, 'password': 'InitialPass123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('security_alert', response.data)
        self.assertEqual(response.data['security_alert']['reason_code'], 'TEMP_PASSWORD_EXPIRING')
        self.assertLessEqual(response.data['security_alert']['days_left'], 2)

    def test_register_rejects_recent_password_reuse_for_existing_email(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': self.user.email,
                'password': 'InitialPass123!',
                'password_confirm': 'InitialPass123!',
                'first_name': 'Retry',
                'last_name': 'User',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._reason_code(response), 'PASSWORD_REUSE_RECENT')

    def test_change_password_rejects_reuse_of_recent_password(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            '/api/auth/users/change_password/',
            {
                'current_password': 'InitialPass123!',
                'new_password': 'InitialPass123!',
                'new_password_confirm': 'InitialPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._reason_code(response), 'PASSWORD_REUSE_RECENT')

    def test_change_password_clears_temporary_password_flags(self):
        self.user.mark_temporary_password(when=timezone.now() - timedelta(days=1))
        self.user.save(update_fields=['metadata', 'must_change_password'])

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/auth/users/change_password/',
            {
                'current_password': 'InitialPass123!',
                'new_password': 'BrandNewPass456!',
                'new_password_confirm': 'BrandNewPass456!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        self.assertNotIn('temporary_password_set_at', self.user.metadata)
        self.assertTrue(self.user.check_password('BrandNewPass456!'))

    def test_admin_reset_password_rejects_reuse_of_recent_password(self):
        self.client.force_authenticate(user=self.org_admin)

        response = self.client.post(
            f'/api/auth/users/{self.user.id}/reset_password/',
            {'new_password': 'InitialPass123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._reason_code(response), 'PASSWORD_REUSE_RECENT')


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class UserRolePermissionTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            code='ORG00002',
            name='Permissions Org',
            email='permissions@example.com',
        )

        self.regular_user = self._create_user(
            email='regular@example.com',
            password='RegularPass123!',
            first_name='Regular',
            last_name='Member',
            role='user',
        )
        self.org_admin = self._create_user(
            email='orgadmin@example.com',
            password='OrgAdminPass123!',
            first_name='Org',
            last_name='Admin',
            role='org_admin',
        )
        self.admin_user = self._create_user(
            email='admin@example.com',
            password='GlobalAdmin123!',
            first_name='Global',
            last_name='Admin',
            role='admin',
        )

    def _create_user(self, email, password, first_name, last_name, role):
        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization=self.organization,
            role=role,
            is_active=True,
        )
        user.set_password(password)
        user.save(update_fields=['password'])
        return user

    def test_regular_user_cannot_create_user(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(
            '/api/auth/users/',
            {
                'email': 'new.user@example.com',
                'password': 'NewStrongPass123!',
                'password_confirm': 'NewStrongPass123!',
                'first_name': 'New',
                'last_name': 'User',
                'organization': str(self.organization.id),
                'role': 'user',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_org_admin_can_create_user(self):
        self.client.force_authenticate(user=self.org_admin)

        response = self.client.post(
            '/api/auth/users/',
            {
                'email': 'created.by.orgadmin@example.com',
                'password': 'NewStrongPass123!',
                'password_confirm': 'NewStrongPass123!',
                'first_name': 'Created',
                'last_name': 'ByOrgAdmin',
                'organization': str(self.organization.id),
                'role': 'user',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='created.by.orgadmin@example.com').exists())

    def test_org_admin_cannot_destroy_user(self):
        self.client.force_authenticate(user=self.org_admin)

        response = self.client.delete(f'/api/auth/users/{self.regular_user.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_destroy_other_user(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(f'/api/auth/users/{self.regular_user.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.regular_user.id).exists())

    def test_admin_cannot_destroy_self(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.delete(f'/api/auth/users/{self.admin_user.id}/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data[0]), 'No puedes eliminarte a ti mismo')

    def test_org_admin_cannot_deactivate_self(self):
        self.client.force_authenticate(user=self.org_admin)

        response = self.client.post(f'/api/auth/users/{self.org_admin.id}/deactivate/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('error'), 'No puedes desactivarte a ti mismo')

    def test_regular_user_cannot_unlock_user(self):
        self.regular_user.failed_login_attempts = 5
        self.regular_user.lock_account(30)

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(f'/api/auth/users/{self.org_admin.id}/unlock/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_unlock_user(self):
        self.regular_user.failed_login_attempts = 5
        self.regular_user.lock_account(30)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/auth/users/{self.regular_user.id}/unlock/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.failed_login_attempts, 0)
        self.assertIsNone(self.regular_user.locked_until)


@override_settings(
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
)
class OrganizationIsolationTests(APITestCase):
    """
    Verify that non-admin users only see data from their own organization
    and that global admins can see across all organizations.
    """

    def setUp(self):
        self.org_a = Organization.objects.create(
            code='ORG00010', name='Org A', email='orga@example.com',
        )
        self.org_b = Organization.objects.create(
            code='ORG00020', name='Org B', email='orgb@example.com',
        )

        self.user_a = self._create_user(
            email='user-a@example.com', org=self.org_a, role='user',
        )
        self.user_a2 = self._create_user(
            email='user-a2@example.com', org=self.org_a, role='user',
        )
        self.user_b = self._create_user(
            email='user-b@example.com', org=self.org_b, role='user',
        )
        self.org_admin_a = self._create_user(
            email='admin-a@example.com', org=self.org_a, role='org_admin',
        )
        self.global_admin = self._create_user(
            email='global@example.com', org=self.org_a, role='admin',
        )

    def _create_user(self, email, org, role):
        user = User.objects.create(
            email=email,
            first_name='Test',
            last_name='User',
            organization=org,
            role=role,
            is_active=True,
        )
        user.set_password('Pass123!Pass!')
        user.save(update_fields=['password'])
        return user

    # ------------------------------------------------------------------ #
    # User list filtering                                                  #
    # ------------------------------------------------------------------ #

    def test_non_admin_user_list_excludes_other_orgs(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get('/api/auth/users/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_emails = {u['email'] for u in response.data.get('results', response.data)}
        self.assertIn(self.user_a.email, result_emails)
        self.assertNotIn(self.user_b.email, result_emails)

    def test_global_admin_user_list_includes_all_orgs(self):
        self.client.force_authenticate(user=self.global_admin)

        response = self.client.get('/api/auth/users/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_emails = {u['email'] for u in response.data.get('results', response.data)}
        self.assertIn(self.user_a.email, result_emails)
        self.assertIn(self.user_b.email, result_emails)

    # ------------------------------------------------------------------ #
    # User detail access                                                   #
    # ------------------------------------------------------------------ #

    def test_non_admin_cannot_retrieve_user_from_other_org(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/auth/users/{self.user_b.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_global_admin_can_retrieve_user_from_any_org(self):
        self.client.force_authenticate(user=self.global_admin)

        response = self.client.get(f'/api/auth/users/{self.user_b.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_b.email)

    # ------------------------------------------------------------------ #
    # Organization list filtering                                          #
    # ------------------------------------------------------------------ #

    def test_non_admin_organization_list_shows_only_own_org(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get('/api/organizations/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {
            str(o['id']) for o in response.data.get('results', response.data)
        }
        self.assertIn(str(self.org_a.id), result_ids)
        self.assertNotIn(str(self.org_b.id), result_ids)

    def test_global_admin_organization_list_includes_all_orgs(self):
        self.client.force_authenticate(user=self.global_admin)

        response = self.client.get('/api/organizations/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {
            str(o['id']) for o in response.data.get('results', response.data)
        }
        self.assertIn(str(self.org_a.id), result_ids)
        self.assertIn(str(self.org_b.id), result_ids)

    # ------------------------------------------------------------------ #
    # Organization detail access                                           #
    # ------------------------------------------------------------------ #

    def test_non_admin_cannot_retrieve_other_org_detail(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(f'/api/organizations/{self.org_b.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_global_admin_can_retrieve_any_org_detail(self):
        self.client.force_authenticate(user=self.global_admin)

        response = self.client.get(f'/api/organizations/{self.org_b.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Org B')

    # ------------------------------------------------------------------ #
    # Cross-org admin action blocked for org_admin                        #
    # ------------------------------------------------------------------ #

    def test_org_admin_cannot_reset_password_of_user_in_other_org(self):
        self.client.force_authenticate(user=self.org_admin_a)

        response = self.client.post(
            f'/api/auth/users/{self.user_b.id}/reset_password/',
            {'new_password': 'NewPass987!OK'},
            format='json',
        )

        # user_b belongs to org_b, invisible to org_admin_a → 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
