"""P0R continuation: actual adapters/dispatch/serializers, simulated persistence."""
from contextlib import ExitStack
from unittest import TestCase
from unittest.mock import Mock, patch
import json

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import force_authenticate
from apps.api import test_p0r as prior
from apps.api import test_control_plane as base
from apps.organizations.models import Organization
from apps.subscriptions.models import Invoice, Subscription, Plan
from apps.subscriptions.views import InvoiceViewSet
from apps.users.models import User, UserSession
from apps.users.views import UserViewSet


class ConsumerDenialContinuationTests(TestCase):
    setUp = prior.ConsumerGrantCompatibilityTests.setUp
    keys = prior.ConsumerGrantCompatibilityTests.keys
    tenant = prior.ConsumerGrantCompatibilityTests.tenant
    members = prior.ConsumerGrantCompatibilityTests.members
    bridge = prior.ConsumerGrantCompatibilityTests.bridge
    adapters = prior.ConsumerGrantCompatibilityTests.adapters

    def test_disabled_tenant_404_never_restores_local_authority_in_either_adapter(self):
        for repo, module, client in self.adapters():
            with self.subTest(repo=repo), ExitStack() as stack:
                stack.enter_context(patch.object(module.requests, 'get', side_effect=lambda url, **kw: self.bridge('get', url, **kw)))
                stack.enter_context(patch.object(module, 'Organization', Mock()))
                stack.enter_context(patch.object(client, '_resolve_adminapps_org_id', return_value=str(self.org.pk)))
                fallbacks = [stack.enter_context(patch.object(client, name, return_value={
                    'allowed': True, 'source': 'local_database', 'modules': [{'code': self.product.code}]}))
                    for name in ('_get_organization_local', '_get_organization_users_local', '_get_organization_modules_local')]
                self.org.status = 'active'
                self.assertNotIn('error', client.get_organization(str(self.org.pk)))
                self.org.status = 'suspended'
                for operation in (client.get_organization, client.get_organization_users, client.get_organization_modules):
                    result = operation(str(self.org.pk))
                    self.assertTrue(result.get('authorization_denied'), (repo, operation.__name__, result))
                    self.assertIs(result.get('allowed'), False)
                for fallback in fallbacks:
                    fallback.assert_not_called()
                self.org.status = 'active'

    def test_all_client_errors_deny_even_with_positive_or_nonobject_payload(self):
        for repo, module, client in self.adapters():
            for status in (400, 401, 403, 404, 405, 409, 410, 422, 429):
                for payload in ({'allowed': True, 'modules': [{'code': self.product.code}]}, [], None):
                    with self.subTest(repo=repo, status=status, payload=payload):
                        response = module.requests.Response(); response.status_code = status
                        response._content = json.dumps(payload).encode()
                        with patch.object(module.requests, 'get', return_value=response):
                            result = client._make_request('GET', '/organizations/missing/')
                        self.assertIsInstance(result, dict)
                        self.assertIs(result.get('allowed'), False)
                        self.assertTrue(result.get('authorization_denied'))


    def test_server_errors_with_allow_payload_never_grant_production_access(self):
        for repo, module, client in self.adapters():
            for status in (500, 502, 503):
                response = module.requests.Response(); response.status_code = status
                response._content = json.dumps({'allowed': True, 'valid': True,
                    'modules': [{'code': self.product.code}]}).encode()
                with self.subTest(repo=repo, status=status), override_settings(IS_PRODUCTION=True), \
                        patch.object(module.requests, 'get', return_value=response), \
                        patch.object(client, '_resolve_adminapps_org_id', return_value=str(self.org.pk)), \
                        patch.object(client, '_validate_product_access_local') as fallback:
                    result = client.validate_product_access(str(self.org.pk), self.product.code, allow_local_fallback=True)
                    self.assertIs(result.get('allowed'), False)
                    fallback.assert_not_called()


class InvoiceFunctionalContinuationTests(TestCase):
    setUp = base.ControlPlaneTests.setUp
    members = base.ControlPlaneTests.members
    user = base.ControlPlaneTests.user
    call = base.ControlPlaneTests.call
    resolved = base.ControlPlaneTests.resolved

    def fixture(self, status='pending'):
        plan = Plan(name='Offline', code='OFFLINE', billing_cycle='monthly')
        subscription = Subscription(plan=plan, status='past_due')
        invoice = Invoice(organization=self.org, subscription=subscription, status=status,
                          number='OFFLINE-ONLY', payment_reference='')
        return invoice, subscription

    def test_pending_and_overdue_payments_execute_real_effects_and_preserve_other_tenant(self):
        for status in ('pending', 'overdue'):
            invoice, subscription = self.fixture(status)
            other, _ = self.fixture(); other.organization = self.other
            with self.subTest(status=status), self.resolved(InvoiceViewSet, invoice), \
                    patch.object(invoice, 'save') as saved, patch.object(subscription, 'save') as activated:
                response = self.call(InvoiceViewSet, 'mark_paid', self.user('admin', is_staff=True),
                                     {'payment_reference': 'offline-reference'}, pk=invoice.pk)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(invoice.status, 'paid'); self.assertEqual(invoice.payment_reference, 'offline-reference')
            self.assertIsNotNone(invoice.paid_at); self.assertEqual(subscription.status, 'active')
            self.assertIsNotNone(subscription.current_period_end)
            saved.assert_called_once(); activated.assert_called_once()
            self.assertEqual(other.status, 'pending'); self.assertEqual(other.payment_reference, '')

    def test_reference_payload_validation_prevents_any_business_effect(self):
        for reference in ({'forged': 'reference'}, ['forged'], True, None, 'X' * 256):
            invoice, subscription = self.fixture()
            with self.subTest(reference=reference), self.resolved(InvoiceViewSet, invoice), \
                    patch.object(invoice, 'save') as saved, patch.object(subscription, 'activate') as activated:
                response = self.call(InvoiceViewSet, 'mark_paid', self.user('admin', is_staff=True),
                                     {'payment_reference': reference}, pk=invoice.pk)
            self.assertEqual(response.status_code, 400, response.data)
            saved.assert_not_called(); activated.assert_not_called()
            self.assertEqual(invoice.status, 'pending'); self.assertEqual(invoice.payment_reference, '')

    def test_cancelled_refunded_draft_and_unknown_invoices_cannot_be_paid(self):
        for status in ('cancelled', 'refunded', 'draft', 'unknown'):
            invoice, subscription = self.fixture(status)
            with self.subTest(status=status), self.resolved(InvoiceViewSet, invoice), \
                    patch.object(invoice, 'save') as saved, patch.object(subscription, 'activate') as activated:
                response = self.call(InvoiceViewSet, 'mark_paid', self.user('admin', is_staff=True), pk=invoice.pk)
            self.assertEqual(response.status_code, 400, response.data)
            saved.assert_not_called(); activated.assert_not_called(); self.assertEqual(invoice.status, status)

    def test_paid_replay_preserves_reference_timestamp_and_revoked_subscription(self):
        invoice, subscription = self.fixture('paid')
        invoice.payment_reference = 'original'; invoice.paid_at = timezone.now() - timezone.timedelta(days=1)
        original_time = invoice.paid_at
        # A replay must not reactivate even a past-due subscription.
        for payload in ({}, {'payment_reference': 'original'}):
            with self.subTest(payload=payload), self.resolved(InvoiceViewSet, invoice), \
                    patch.object(invoice, 'save') as saved, patch.object(subscription, 'activate') as activated:
                response = self.call(InvoiceViewSet, 'mark_paid', self.user('admin', is_staff=True), payload, pk=invoice.pk)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(invoice.paid_at, original_time); self.assertEqual(invoice.payment_reference, 'original')
            saved.assert_not_called(); activated.assert_not_called(); self.assertEqual(subscription.status, 'past_due')

    def test_paid_conflicting_reference_denied_without_overwriting_payment(self):
        invoice, subscription = self.fixture('paid'); invoice.payment_reference = 'original'
        with self.resolved(InvoiceViewSet, invoice), patch.object(invoice, 'save') as saved, \
                patch.object(subscription, 'activate') as activated:
            response = self.call(InvoiceViewSet, 'mark_paid', self.user('admin', is_staff=True),
                                 {'payment_reference': 'replacement'}, pk=invoice.pk)
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(invoice.payment_reference, 'original'); saved.assert_not_called(); activated.assert_not_called()

    def test_payment_denies_unprivileged_inactive_and_technical_principals_before_handler(self):
        from apps.integration.models import IntegrationAPIKey
        inactive = self.user('admin', is_staff=True); inactive.is_active = False
        missing_permission = self.user('admin', is_staff=True); missing_permission.has_perm.return_value = False
        for actor in (None, self.user(), self.user('org_admin'), inactive, missing_permission, IntegrationAPIKey(id=1)):
            with self.subTest(actor=type(actor).__name__), patch.object(InvoiceViewSet, 'get_object') as lookup:
                response = self.call(InvoiceViewSet, 'mark_paid', actor)
            self.assertIn(response.status_code, (401, 403)); lookup.assert_not_called()

    def test_payment_rejects_elevation_and_foreign_relation_fields(self):
        for payload in ({'organization': str(self.other.pk)}, {'subscription': 'forged'}, {'status': 'paid'}, {'is_staff': True}):
            with self.subTest(payload=payload), patch.object(InvoiceViewSet, 'get_object') as lookup:
                response = self.call(InvoiceViewSet, 'mark_paid', self.user('admin', is_staff=True), payload)
            self.assertEqual(response.status_code, 400); lookup.assert_not_called()


class LocalRegistryTokenContinuationTests(TestCase):
    setUp = base.ControlPlaneTests.setUp
    members = base.ControlPlaneTests.members
    user = base.ControlPlaneTests.user

    def test_real_bearer_uses_authenticated_jti_and_owns_registry_filter(self):
        from rest_framework_simplejwt.tokens import AccessToken
        actor = self.user(); access = AccessToken(); access['user_id'] = str(actor.pk)
        request = self.factory.post('/offline/', {}, format='json', HTTP_AUTHORIZATION='Bearer ' + str(access))
        with patch.object(User.objects, 'get', return_value=actor), patch.object(UserSession.objects, 'filter') as records:
            response = UserViewSet.as_view({'post': 'revoke_sessions'})(request)
        self.assertEqual(response.status_code, 200)
        records.assert_called_once_with(user=actor, is_active=True)
        records.return_value.exclude.assert_called_once_with(token_jti=access['jti'])
        self.assertFalse(response.data['access_tokens_revoked'])

    def test_signed_bearer_cannot_keep_arbitrary_other_jti(self):
        from rest_framework_simplejwt.tokens import AccessToken
        actor = self.user(); access = AccessToken(); access['user_id'] = str(actor.pk)
        request = self.factory.post('/offline/', {'current_token_jti': 'foreign'}, format='json',
                                    HTTP_AUTHORIZATION='Bearer ' + str(access))
        with patch.object(User.objects, 'get', return_value=actor), patch.object(UserSession.objects, 'filter') as records:
            response = UserViewSet.as_view({'post': 'revoke_sessions'})(request)
        self.assertEqual(response.status_code, 400); records.assert_not_called()
