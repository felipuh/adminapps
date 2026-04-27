from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization, OrganizationFeatureFlag
from apps.users.models import User


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FeatureFlagsApiTests(APITestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(code='ORGA001', name='Org A', email='orga@example.com')
        self.org_b = Organization.objects.create(code='ORGB001', name='Org B', email='orgb@example.com')

        self.user = User.objects.create(
            email='user@orga.local',
            first_name='Regular',
            last_name='User',
            organization=self.org_a,
            role='user',
            is_active=True,
        )
        self.user.set_password('UserPass123!')
        self.user.save(update_fields=['password'])

        self.admin = User.objects.create(
            email='admin@adminapps.local',
            first_name='Admin',
            last_name='User',
            organization=self.org_b,
            role='admin',
            is_active=True,
            is_staff=True,
        )
        self.admin.set_password('AdminPass123!')
        self.admin.save(update_fields=['password'])

        OrganizationFeatureFlag.objects.create(key='billing_dashboard_v2', enabled=False)
        OrganizationFeatureFlag.objects.create(key='new_reports', enabled=True)
        OrganizationFeatureFlag.objects.create(key='billing_dashboard_v2', enabled=True, organization=self.org_a)
        OrganizationFeatureFlag.objects.create(key='new_reports', enabled=False, organization=self.org_b)

    def test_non_admin_gets_org_resolved_flags(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/api/feature-flags/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['organization_id'], str(self.org_a.id))
        self.assertEqual(response.data['flags']['billing_dashboard_v2'], True)
        self.assertEqual(response.data['flags']['new_reports'], True)

    def test_non_admin_cannot_request_another_organization(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f'/api/feature-flags/?organization_id={self.org_b.id}')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_request_specific_organization_flags(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f'/api/feature-flags/?organization_id={self.org_b.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['organization_id'], str(self.org_b.id))
        self.assertEqual(response.data['flags']['billing_dashboard_v2'], False)
        self.assertEqual(response.data['flags']['new_reports'], False)

    def test_non_admin_without_organization_gets_400(self):
        no_org_user = User.objects.create(
            email='no-org@adminapps.local',
            first_name='No',
            last_name='Org',
            role='user',
            is_active=True,
        )
        no_org_user.set_password('NoOrgPass123!')
        no_org_user.save(update_fields=['password'])

        self.client.force_authenticate(user=no_org_user)
        response = self.client.get('/api/feature-flags/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FeatureFlagsRolloutTest(APITestCase):
    """
    End-to-end test for feature flag rollout:
    - Global flag disabled
    - Org-specific override enabled for pilot organization
    - Verify users in pilot org see flag=True
    - Verify users in other orgs see flag=False
    """
    def setUp(self):
        # Create organizations
        self.pilot_org = Organization.objects.create(
            code='PILOT_ORG',
            name='Pilot Organization',
            email='pilot@example.com'
        )
        self.regular_org = Organization.objects.create(
            code='REG_ORG',
            name='Regular Organization',
            email='regular@example.com'
        )
        
        # Create global flag (disabled)
        OrganizationFeatureFlag.objects.create(
            key='billing_revenue_dashboard',
            enabled=False
        )
        
        # Create org-specific override for pilot org (enabled)
        OrganizationFeatureFlag.objects.create(
            key='billing_revenue_dashboard',
            enabled=True,
            organization=self.pilot_org
        )
        
        # Create users
        self.pilot_user = User.objects.create(
            email='pilot_user@example.com',
            first_name='Pilot',
            last_name='User',
            organization=self.pilot_org,
            role='user',
            is_active=True,
        )
        self.pilot_user.set_password('PilotPass123!')
        self.pilot_user.save(update_fields=['password'])
        
        self.regular_user = User.objects.create(
            email='regular_user@example.com',
            first_name='Regular',
            last_name='User',
            organization=self.regular_org,
            role='user',
            is_active=True,
        )
        self.regular_user.set_password('RegularPass123!')
        self.regular_user.save(update_fields=['password'])
    
    def test_pilot_user_sees_enabled_flag(self):
        """Pilot org user should see billing_revenue_dashboard=True"""
        self.client.force_authenticate(user=self.pilot_user)
        
        response = self.client.get('/api/feature-flags/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['flags']['billing_revenue_dashboard'],
            True,
            'Pilot user should see billing_revenue_dashboard=True'
        )
    
    def test_regular_user_sees_disabled_flag(self):
        """Regular org user should see billing_revenue_dashboard=False"""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get('/api/feature-flags/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['flags']['billing_revenue_dashboard'],
            False,
            'Regular user should see billing_revenue_dashboard=False (global default)'
        )
    
    def test_different_orgs_see_different_flags(self):
        """Verify flag resolution is org-specific"""
        # Pilot org request
        self.client.force_authenticate(user=self.pilot_user)
        pilot_response = self.client.get('/api/feature-flags/')
        pilot_flag = pilot_response.data['flags']['billing_revenue_dashboard']
        
        # Regular org request
        self.client.force_authenticate(user=self.regular_user)
        regular_response = self.client.get('/api/feature-flags/')
        regular_flag = regular_response.data['flags']['billing_revenue_dashboard']
        
        self.assertNotEqual(
            pilot_flag,
            regular_flag,
            'Pilot and regular orgs should have different flag values'
        )
        self.assertTrue(pilot_flag)
        self.assertFalse(regular_flag)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class RequestIDMiddlewareApiTests(APITestCase):
    def test_generates_request_id_when_missing(self):
        response = self.client.get('/api/feature-flags/')

        self.assertIn('X-Request-ID', response)
        self.assertTrue(response['X-Request-ID'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_echoes_incoming_request_id_header(self):
        response = self.client.get('/api/feature-flags/', HTTP_X_REQUEST_ID='req-adminapps-001')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['X-Request-ID'], 'req-adminapps-001')
