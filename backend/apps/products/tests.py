import json
from io import StringIO

from django.core.management import call_command
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization
from apps.products.models import (
    OrganizationProductEntitlement,
    ProductEntitlementAuditLog,
    ProductSystem,
)
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

    def test_can_enable_iso_smart_for_organization(self):
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.iso_product,
            subscription=self.subscription,
            plan=self.plan,
            status='active',
            enabled=True,
        )

        self.assertTrue(entitlement.access_allowed)
        self.assertEqual(entitlement.product.code, 'ISO_SMART')

    def test_provision_pilot_entitlement_dry_run_does_not_write(self):
        self.org.subscription = None
        self.org.save(update_fields=['subscription'])
        out = StringIO()

        call_command(
            'provision_pilot_entitlement',
            organization=self.org.code,
            product='ISO_SMART',
            dry_run=True,
            stdout=out,
        )

        payload = json.loads(out.getvalue())
        self.assertTrue(payload['dry_run'])
        self.assertTrue(payload['planned_changes']['create_plan'])
        self.assertTrue(payload['planned_changes']['create_subscription'])
        self.assertIsNone(payload['after']['entitlement'])
        self.assertFalse(Plan.objects.filter(code='ISO_SMART_PILOT').exists())
        self.assertFalse(
            OrganizationProductEntitlement.objects.filter(
                organization=self.org,
                product=self.iso_product,
            ).exists()
        )

    def test_provision_pilot_entitlement_allows_iso_smart_access(self):
        self.org.subscription = None
        self.org.save(update_fields=['subscription'])
        out = StringIO()

        call_command(
            'provision_pilot_entitlement',
            organization=self.org.code,
            product='ISO_SMART',
            scopes='pilot,qms',
            stdout=out,
        )

        payload = json.loads(out.getvalue())
        entitlement = OrganizationProductEntitlement.objects.get(
            organization=self.org,
            product=self.iso_product,
        )
        self.assertTrue(payload['access_allowed'])
        self.assertEqual(payload['source'], 'adminapps')
        self.assertFalse(payload['fallback'])
        self.assertTrue(entitlement.access_allowed)
        self.assertEqual(entitlement.access_denial_reason, 'ok')
        self.assertEqual(entitlement.scopes, ['pilot', 'qms'])
        self.org.refresh_from_db()
        self.assertEqual(self.org.subscription.status, 'active')
        self.assertTrue(
            ProductEntitlementAuditLog.objects.filter(
                entitlement=entitlement,
                metadata__source='provision_pilot_entitlement',
            ).exists()
        )

    def test_provision_pilot_entitlement_is_idempotent(self):
        self.org.subscription = None
        self.org.save(update_fields=['subscription'])
        out = StringIO()

        call_command('provision_pilot_entitlement', organization=self.org.code, product='ISO_SMART', stdout=out)
        call_command('provision_pilot_entitlement', organization=self.org.code, product='ISO_SMART', stdout=out)

        self.assertEqual(Plan.objects.filter(code='ISO_SMART_PILOT').count(), 1)
        self.assertEqual(
            OrganizationProductEntitlement.objects.filter(
                organization=self.org,
                product=self.iso_product,
            ).count(),
            1,
        )
        self.assertEqual(Subscription.objects.filter(plan__code='ISO_SMART_PILOT').count(), 1)

    def test_entitlement_api_exposes_subscription_plan_as_effective_plan(self):
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=self.subscription,
            status='active',
            enabled=True,
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f'/api/products/entitlements/{entitlement.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['plan'])
        self.assertEqual(response.data['effective_plan'], str(self.plan.id))
        self.assertEqual(response.data['effective_plan_code'], self.plan.code)
        self.assertEqual(response.data['effective_plan_name'], self.plan.name)

    def test_default_plan_is_reported_but_does_not_bypass_billing_requirement(self):
        self.org.subscription = None
        self.org.save(update_fields=['subscription'])
        self.med_product.default_plan = self.plan
        self.med_product.save(update_fields=['default_plan'])
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            status='active',
            enabled=True,
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f'/api/products/entitlements/{entitlement.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['effective_plan'], str(self.plan.id))
        self.assertFalse(response.data['access_allowed'])
        self.assertEqual(response.data['access_denial_reason'], 'billing_not_configured')

    def test_customer_can_have_both_iso_smart_and_medsupplier(self):
        OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.iso_product,
            subscription=self.subscription,
            status='active',
            enabled=True,
        )
        OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=self.subscription,
            status='active',
            enabled=True,
        )

        codes = set(
            OrganizationProductEntitlement.objects
            .filter(organization=self.org)
            .values_list('product__code', flat=True)
        )
        self.assertEqual(codes, {'ISO_SMART', 'MEDSUPPLIER'})

    def test_admin_can_toggle_entitlement_states_and_audit_is_recorded(self):
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=self.subscription,
            status='active',
            enabled=True,
        )
        self.client.force_authenticate(user=self.admin)

        disable_response = self.client.post(
            f'/api/products/entitlements/{entitlement.id}/toggle/',
            {'action': 'disable', 'reason': 'contract ended'},
            format='json',
        )
        self.assertEqual(disable_response.status_code, status.HTTP_200_OK)
        entitlement.refresh_from_db()
        self.assertFalse(entitlement.access_allowed)
        self.assertEqual(entitlement.status, 'suspended')

        trial_response = self.client.post(
            f'/api/products/entitlements/{entitlement.id}/toggle/',
            {'action': 'trial', 'trial_days': 7},
            format='json',
        )
        self.assertEqual(trial_response.status_code, status.HTTP_200_OK)
        entitlement.refresh_from_db()
        self.assertEqual(entitlement.status, 'trial')
        self.assertTrue(entitlement.enabled)

        actions = set(ProductEntitlementAuditLog.objects.values_list('action', flat=True))
        self.assertIn('disabled', actions)
        self.assertIn('trial_started', actions)

    def test_patch_revocation_records_disabled_audit_event(self):
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=self.subscription,
            status='active',
            enabled=True,
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f'/api/products/entitlements/{entitlement.id}/',
            {'enabled': False, 'status': 'cancelled'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entitlement.refresh_from_db()
        self.assertFalse(entitlement.enabled)
        self.assertEqual(entitlement.status, 'cancelled')
        self.assertTrue(
            ProductEntitlementAuditLog.objects.filter(
                entitlement=entitlement,
                action='disabled',
                previous_state__enabled=True,
                new_state__enabled=False,
                new_state__status='cancelled',
            ).exists()
        )

    def test_cannot_create_active_billing_entitlement_without_subscription(self):
        self.org.subscription = None
        self.org.save(update_fields=['subscription'])
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            '/api/products/entitlements/',
            {
                'organization': str(self.org.id),
                'product': str(self.med_product.id),
                'status': 'active',
                'enabled': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('subscription', response.data)

    def test_can_create_trial_billing_entitlement_without_subscription(self):
        self.org.subscription = None
        self.org.save(update_fields=['subscription'])
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            '/api/products/entitlements/',
            {
                'organization': str(self.org.id),
                'product': str(self.med_product.id),
                'status': 'trial',
                'enabled': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entitlement = OrganizationProductEntitlement.objects.get(
            organization=self.org,
            product=self.med_product,
        )
        self.assertTrue(entitlement.access_allowed)

    def test_cannot_toggle_enable_billing_entitlement_without_subscription(self):
        self.org.subscription = None
        self.org.save(update_fields=['subscription'])
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            status='suspended',
            enabled=False,
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            f'/api/products/entitlements/{entitlement.id}/toggle/',
            {'action': 'enable'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        entitlement.refresh_from_db()
        self.assertFalse(entitlement.enabled)
        self.assertEqual(entitlement.status, 'suspended')

    def test_non_admin_cannot_manage_entitlements(self):
        org_admin = User.objects.create_user(
            email='org-admin@example.com',
            password='OrgAdmin123!',
            first_name='Org',
            last_name='Admin',
            role='org_admin',
            organization=self.org,
        )
        self.client.force_authenticate(user=org_admin)

        response = self.client.post(
            '/api/products/entitlements/',
            {
                'organization': str(self.org.id),
                'product': str(self.med_product.id),
                'status': 'active',
                'enabled': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_access_readiness_command_reports_required_products(self):
        out = StringIO()

        call_command('check_product_access_readiness', stdout=out)

        report = json.loads(out.getvalue())
        self.assertEqual(report['status'], 'ready')
        product_codes = {item['code'] for item in report['products']}
        self.assertEqual(product_codes, {'ISO_SMART', 'MEDSUPPLIER'})
        self.assertTrue(report['checks']['required_products_exist'])
        self.assertTrue(report['checks']['legacy_plan_mentions_do_not_grant_access'])

    def test_product_access_readiness_command_flags_legacy_plan_mentions_without_entitlement(self):
        OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=self.subscription,
            status='active',
            enabled=True,
        )
        legacy_plan = Plan.objects.create(
            code='LEGACY_MED_ONLY',
            name='Legacy Med Plan',
            modules_included=['medsupplier'],
            price='50.00',
        )
        legacy_subscription = Subscription.objects.create(
            plan=legacy_plan,
            status='active',
            amount='50.00',
        )
        legacy_org = Organization.objects.create(
            code='LEGACY001',
            name='Legacy Mention Customer',
            email='legacy@example.com',
            status='active',
            subscription=legacy_subscription,
        )
        out = StringIO()

        call_command('check_product_access_readiness', stdout=out)

        report = json.loads(out.getvalue())
        self.assertEqual(
            report['legacy_bypass_watchlist']['plan_product_mentions_without_entitlement'],
            1,
        )
        item = report['legacy_bypass_watchlist']['items'][0]
        self.assertEqual(item['organization_id'], str(legacy_org.id))
        self.assertEqual(item['missing_entitlements'], ['MEDSUPPLIER'])


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
        entitlement = OrganizationProductEntitlement.objects.create(
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
        self.assertFalse(
            ProductEntitlementAuditLog.objects.filter(
                entitlement=entitlement,
                action='validated',
            ).exists()
        )

    def test_integration_can_audit_successful_validation_when_requested(self):
        plan = Plan.objects.create(
            code='MED_ACTIVE_AUDIT',
            name='MedSupplier Active Audit',
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
        entitlement = OrganizationProductEntitlement.objects.create(
            organization=self.org,
            product=self.med_product,
            subscription=subscription,
            status='active',
            enabled=True,
        )

        response = self.client.get(
            f'/api/integration/organizations/{self.org.id}/products/MEDSUPPLIER/validate/?audit=true',
            HTTP_X_API_KEY='isosmart-integration-key-2025',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ProductEntitlementAuditLog.objects.filter(
                entitlement=entitlement,
                action='validated',
                new_state__allowed=True,
                new_state__reason='ok',
                metadata__integration_service='isosmart',
            ).exists()
        )

    def test_integration_denies_product_without_entitlement(self):
        response = self.client.get(
            f'/api/integration/organizations/{self.org.id}/products/ISO_SMART/validate/',
            HTTP_X_API_KEY='isosmart-integration-key-2025',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['allowed'])
        self.assertEqual(response.json()['reason'], 'product_not_enabled')
        self.assertTrue(
            ProductEntitlementAuditLog.objects.filter(
                entitlement__isnull=True,
                organization=self.org,
                product=self.iso_product,
                action='validated',
                new_state__allowed=False,
                new_state__reason='product_not_enabled',
            ).exists()
        )

    def test_legacy_modules_endpoint_does_not_grant_saas_product_from_plan_only(self):
        plan = Plan.objects.create(
            code='MED_PLAN_ONLY',
            name='Plan Mentions MedSupplier',
            modules_included=['medsupplier', 'iso_smart'],
            price='100.00',
        )
        subscription = Subscription.objects.create(
            plan=plan,
            status='active',
            amount='100.00',
        )
        self.org.subscription = subscription
        self.org.save(update_fields=['subscription'])

        response = self.client.get(
            f'/api/integration/organizations/{self.org.id}/modules/',
            HTTP_X_API_KEY='isosmart-integration-key-2025',
        )

        self.assertEqual(response.status_code, 200)
        codes = {item['code'] for item in response.json()['modules']}
        self.assertNotIn('MEDSUPPLIER', codes)
        self.assertNotIn('ISO_SMART', codes)

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
        entitlement = OrganizationProductEntitlement.objects.create(
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
        self.assertTrue(
            ProductEntitlementAuditLog.objects.filter(
                entitlement=entitlement,
                action='validated',
                new_state__allowed=False,
                new_state__reason='billing_blocked',
            ).exists()
        )

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
