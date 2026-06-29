from django.test import override_settings
from rest_framework.test import APITestCase

from apps.organizations.models import Organization
from apps.products.models import OrganizationProductEntitlement, ProductSystem
from apps.subscriptions.models import Plan, Subscription
from apps.users.models import User


@override_settings(INTEGRATION_API_KEYS={'isosmart': 'testhash'})
class ProductSystemEntitlementTests(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            code='MED001',
            name='MedSupplier Customer',
            email='med@example.com',
            status='active',
        )
        self.plan = Plan.objects.create(
            code='MED_PLAN',
            name='MedSupplier Plan',
            modules_included=['medsupplier'],
            price='100.00',
        )
        self.subscription = Subscription.objects.create(
            plan=self.plan,
            status='active',
            amount='100.00',
        )
        self.org.subscription = self.subscription
        self.org.save(update_fields=['subscription'])

        self.med_product, _ = ProductSystem.objects.update_or_create(
            code='MEDSUPPLIER',
            defaults={
                'name': 'ISO Smart MedSupplier',
                'slug': 'iso-smart-medsupplier-test',
                'status': 'active',
            },
        )
        self.iso_product, _ = ProductSystem.objects.update_or_create(
            code='ISO_SMART',
            defaults={
                'name': 'ISO Smart',
                'slug': 'iso-smart-test',
                'status': 'active',
            },
        )
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User',
            role='admin',
            organization=self.org,
        )

    def test_product_entitlement_can_enable_medsupplier_for_organization(self):
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=self.subscription,
            plan=self.plan,
            status='active',
            enabled=True,
            modules_enabled=['document_room', 'rfq', 'quality'],
            scopes=['supplier', 'customer'],
        )

        self.assertTrue(entitlement.is_active)
        self.assertTrue(entitlement.access_allowed)
        self.assertEqual(entitlement.access_denial_reason, 'ok')
        self.assertEqual(entitlement.product.code, 'MEDSUPPLIER')
        self.assertEqual(entitlement.subscription.status, 'active')

    def test_product_entitlement_blocks_access_when_billing_is_past_due(self):
        self.subscription.status = 'past_due'
        self.subscription.save(update_fields=['status'])
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=self.subscription,
            plan=self.plan,
            status='active',
            enabled=True,
        )

        self.assertTrue(entitlement.is_active)
        self.assertFalse(entitlement.access_allowed)
        self.assertEqual(entitlement.access_denial_reason, 'billing_blocked')

    def test_product_entitlement_denies_when_product_not_enabled(self):
        OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            status='active',
            enabled=True,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            '/api/products/entitlements/by_organization/',
            {'organization_id': str(self.org.id)},
        )

        self.assertEqual(response.status_code, 200)
        codes = {item['product_code'] for item in response.data['products']}
        self.assertIn('MEDSUPPLIER', codes)
        self.assertNotIn('ISO_SMART', codes)


@override_settings(INTEGRATION_API_KEYS={
    'isosmart': '20985646232d3504aeddb985345b81ec968ed8d86a6993ab7efcfdd35cd537e7'
})
class ProductIntegrationContractTests(APITestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            code='MEDINT001',
            name='MedSupplier Integration Customer',
            email='medint@example.com',
            status='active',
        )
        self.med_product, _ = ProductSystem.objects.update_or_create(
            code='MEDSUPPLIER',
            defaults={
                'name': 'ISO Smart MedSupplier',
                'slug': 'iso-smart-medsupplier-integration',
                'status': 'active',
            },
        )
        self.iso_product, _ = ProductSystem.objects.update_or_create(
            code='ISO_SMART',
            defaults={
                'name': 'ISO Smart',
                'slug': 'iso-smart-integration',
                'status': 'active',
            },
        )

    def test_integration_validates_enabled_product_access(self):
        plan = Plan.objects.create(
            code='MED_ACTIVE_INTEGRATION',
            name='MedSupplier Active Integration',
            modules_included=['medsupplier'],
            price='100.00',
        )
        subscription = Subscription.objects.create(
            plan=plan,
            status='active',
            amount='100.00',
        )
        self.org.subscription = subscription
        self.org.save(update_fields=['subscription'])
        OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=subscription,
            status='active',
            enabled=True,
            scopes=['supplier', 'customer'],
        )

        response = self.client.get(
            f'/api/integration/organizations/{self.org.id}/products/MEDSUPPLIER/validate/',
            HTTP_X_API_KEY='isosmart-integration-key-2025',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['allowed'])
        self.assertEqual(response.json()['product']['code'], 'MEDSUPPLIER')
        self.assertTrue(response.json()['product']['access_allowed'])
        self.assertEqual(response.json()['reason'], 'ok')

    def test_integration_denies_product_without_entitlement(self):
        response = self.client.get(
            f'/api/integration/organizations/{self.org.id}/products/ISO_SMART/validate/',
            HTTP_X_API_KEY='isosmart-integration-key-2025',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['allowed'])
        self.assertEqual(response.json()['reason'], 'product_not_enabled')

    def test_integration_denies_product_when_subscription_blocks_billing(self):
        plan = Plan.objects.create(
            code='MED_PAST_DUE',
            name='MedSupplier Past Due',
            modules_included=['medsupplier'],
            price='100.00',
        )
        subscription = Subscription.objects.create(
            plan=plan,
            status='past_due',
            amount='100.00',
        )
        self.org.subscription = subscription
        self.org.save(update_fields=['subscription'])
        OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=subscription,
            status='active',
            enabled=True,
        )

        response = self.client.get(
            f'/api/integration/organizations/{self.org.id}/products/MEDSUPPLIER/validate/',
            HTTP_X_API_KEY='isosmart-integration-key-2025',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['allowed'])
        self.assertEqual(response.json()['reason'], 'billing_blocked')
        self.assertFalse(response.json()['product']['access_allowed'])

    def test_legacy_modules_endpoint_includes_product_entitlement(self):
        plan = Plan.objects.create(
            code='MED_ACTIVE_LEGACY',
            name='MedSupplier Active Legacy',
            modules_included=['medsupplier'],
            price='100.00',
        )
        subscription = Subscription.objects.create(
            plan=plan,
            status='active',
            amount='100.00',
        )
        self.org.subscription = subscription
        self.org.save(update_fields=['subscription'])
        OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=subscription,
            status='active',
            enabled=True,
        )

        response = self.client.get(
            f'/api/integration/organizations/{self.org.id}/modules/',
            HTTP_X_API_KEY='isosmart-integration-key-2025',
        )

        self.assertEqual(response.status_code, 200)
        codes = {item['code'] for item in response.json()['modules']}
        self.assertIn('MEDSUPPLIER', codes)

    def test_legacy_modules_endpoint_excludes_billing_blocked_product_entitlement(self):
        plan = Plan.objects.create(
            code='MED_BLOCKED_LEGACY',
            name='MedSupplier Blocked Legacy',
            modules_included=[],
            price='100.00',
        )
        subscription = Subscription.objects.create(
            plan=plan,
            status='past_due',
            amount='100.00',
        )
        self.org.subscription = subscription
        self.org.save(update_fields=['subscription'])
        OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=subscription,
            status='active',
            enabled=True,
        )

        response = self.client.get(
            f'/api/integration/organizations/{self.org.id}/modules/',
            HTTP_X_API_KEY='isosmart-integration-key-2025',
        )

        self.assertEqual(response.status_code, 200)
        codes = {item['code'] for item in response.json()['modules']}
        self.assertNotIn('MEDSUPPLIER', codes)
