from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.integration.models import IntegrationAPIKey
from apps.organizations.models import Organization
from apps.products.models import OrganizationProductEntitlement, ProductSystem
from apps.subscriptions.models import Plan, Subscription
from apps.users.models import User, UserOrganization


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class IntegrationAPIKeyUsageTests(APITestCase):
    def test_integration_health_rejects_missing_api_key(self):
        response = self.client.get('/api/integration/health/')

        self.assertEqual(response.status_code, 401)

    def test_persisted_api_key_tracks_last_usage(self):
        api_key = IntegrationAPIKey.objects.create(
            name='medsupplier-service',
            key='integration-key-for-usage-test',
            is_active=True,
        )

        response = self.client.get(
            '/api/integration/health/',
            HTTP_X_API_KEY='integration-key-for-usage-test',
        )

        self.assertEqual(response.status_code, 200)
        api_key.refresh_from_db()
        self.assertIsNotNone(api_key.last_used_at)
        self.assertEqual(api_key.last_used_service, 'medsupplier-service')


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SSOProductClaimsTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            code='SSO001',
            name='SSO Customer',
            email='sso@example.com',
            status='active',
        )
        self.plan = Plan.objects.create(
            code='SSO_PLAN',
            name='SSO Plan',
            price='100.00',
            currency='CRC',
        )
        self.subscription = Subscription.objects.create(
            plan=self.plan,
            status='active',
            amount='100.00',
        )
        self.organization.subscription = self.subscription
        self.organization.save(update_fields=['subscription'])

        self.user = User.objects.create_user(
            email='sso-user@example.com',
            password='SsoPass123!',
            first_name='SSO',
            last_name='User',
            organization=self.organization,
            role='org_admin',
            is_active=True,
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.organization,
            role='org_admin',
            is_primary=True,
            is_active=True,
        )

        self.iso_product, _ = ProductSystem.objects.update_or_create(
            code='ISO_SMART',
            defaults={
                'name': 'ISO Smart',
                'slug': 'iso-smart-sso',
                'status': 'active',
                'billing_enabled': True,
            },
        )
        self.med_product, _ = ProductSystem.objects.update_or_create(
            code='MEDSUPPLIER',
            defaults={
                'name': 'ISO Smart MedSupplier',
                'slug': 'iso-smart-medsupplier-sso',
                'status': 'active',
                'billing_enabled': True,
            },
        )
        OrganizationProductEntitlement.objects.create(
            organization=self.organization,
            product=self.iso_product,
            subscription=self.subscription,
            plan=self.plan,
            status='active',
            enabled=True,
            scopes=['qms'],
        )
        OrganizationProductEntitlement.objects.create(
            organization=self.organization,
            product=self.med_product,
            subscription=self.subscription,
            plan=self.plan,
            status='suspended',
            enabled=True,
            scopes=['supplier'],
        )

    def test_sso_login_includes_product_claims_in_response_and_access_token(self):
        response = self.client.post(
            '/api/integration/sso/login/',
            {
                'email': 'sso-user@example.com',
                'password': 'SsoPass123!',
                'organization_id': str(self.organization.id),
                'client_id': 'isosmart',
                'audience': ['isosmart'],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        tokens = response.json()['tokens']
        self.assertEqual(tokens['allowed_products'], ['ISO_SMART'])

        product_claims = {item['code']: item for item in tokens['product_entitlements']}
        self.assertTrue(product_claims['ISO_SMART']['access_allowed'])
        self.assertFalse(product_claims['MEDSUPPLIER']['access_allowed'])
        self.assertEqual(product_claims['MEDSUPPLIER']['access_denial_reason'], 'entitlement_inactive')

        access = AccessToken(tokens['access_token'])
        self.assertEqual(access['allowed_products'], ['ISO_SMART'])
        jwt_claims = {item['code']: item for item in access['product_entitlements']}
        self.assertIn('ISO_SMART', jwt_claims)
        self.assertIn('MEDSUPPLIER', jwt_claims)
        self.assertFalse(jwt_claims['MEDSUPPLIER']['access_allowed'])
