"""Real DRF dispatch and serializer tests with explicitly simulated persistence."""
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock
import uuid

from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.users.models import User, UserOrganization
from apps.organizations.models import Organization, OrganizationInvitation
from apps.organizations.views import OrganizationInvitationViewSet
from apps.subscriptions.views import SubscriptionViewSet, InvoiceViewSet
from apps.users.views import UserViewSet


class ControlPlaneTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.org = Organization(id=uuid.uuid4(), name='Tenant A', status='active')
        self.other = Organization(id=uuid.uuid4(), name='Tenant B', status='active')
        self.membership_active = True
        self.member_role = 'org_admin'
        self.member_filter = patch.object(UserOrganization.objects, 'filter', side_effect=self.members)
        self.member_filter.start()
        self.addCleanup(self.member_filter.stop)

    def members(self, **kw):
        query = MagicMock()
        valid = (self.membership_active and kw.get('is_active') is True
                 and kw.get('organization__status') == 'active'
                 and kw.get('organization_id') == self.org.pk)
        query.exists.return_value = valid
        query.filter.return_value.exists.side_effect = lambda: valid and self.member_role == 'org_admin'
        return query

    def user(self, role='user', **kwargs):
        user = User(id=uuid.uuid4(), email='synthetic@example.invalid', role=role,
                    organization=self.org, is_active=True, **kwargs)
        user.has_perm = Mock(return_value=True)
        return user

    def call(self, cls, action, user, data=None, method='post', pk=None):
        request = getattr(self.factory, method)('/offline/', data or {}, format='json')
        if user is not None:
            force_authenticate(request, user=user)
        return cls.as_view({method: action})(request, **({'pk': str(pk)} if pk else {}))

    def test_member_cannot_activate_subscription_handler(self):
        obj = NS(activate=Mock())
        with patch.object(SubscriptionViewSet, 'get_object', return_value=obj):
            response = self.call(SubscriptionViewSet, 'activate', self.user())
        self.assertEqual(response.status_code, 403)
        obj.activate.assert_not_called()

    def test_member_cannot_mark_invoice_paid_handler(self):
        obj = NS(status='pending', subscription=None, save=Mock())
        with patch.object(InvoiceViewSet, 'get_object', return_value=obj):
            response = self.call(InvoiceViewSet, 'mark_paid', self.user())
        self.assertEqual(response.status_code, 403)
        obj.save.assert_not_called()

    def test_org_admin_cannot_reset_platform_admin_password(self):
        obj = self.user('superadmin', is_staff=True)
        with patch.object(UserViewSet, 'get_queryset') as qs, patch.object(obj, 'save') as save:
            qs.return_value = User.objects.all()
            with patch('rest_framework.generics.get_object_or_404', return_value=obj):
                response = self.call(UserViewSet, 'reset_password', self.user('org_admin'),
                                     {'new_password': 'Synthetic-New-Password-123!'}, pk=obj.pk)
        self.assertEqual(response.status_code, 403)
        save.assert_not_called()

    def test_invitation_patch_cannot_promote_global_role(self):
        obj = OrganizationInvitation(id=uuid.uuid4(), organization=self.org,
                                     email='invited@example.invalid', role='user',
                                     expires_at=timezone.now() + timezone.timedelta(days=1))
        with patch.object(OrganizationInvitationViewSet, 'get_object', return_value=obj), \
             patch.object(obj, 'save') as save:
            response = self.call(OrganizationInvitationViewSet, 'partial_update', self.user('org_admin'),
                                 {'role': 'superadmin'}, method='patch', pk=obj.pk)
        self.assertIn(response.status_code, (400, 403))
        save.assert_not_called()

    def test_plan_mutations_anonymous_and_non_superadmin_denied(self):
        from apps.subscriptions.views import PlanViewSet
        for actor in (None, self.user(), self.user('admin', is_staff=True)):
            for method, action in [('post', 'create'), ('put', 'update'), ('patch', 'partial_update'), ('delete', 'destroy')]:
                with self.subTest(action=action, actor=getattr(actor, 'role', None)), \
                     patch.object(PlanViewSet, 'perform_create') as create, \
                     patch.object(PlanViewSet, 'get_object') as lookup:
                    response = self.call(PlanViewSet, action, actor, {'name': 'Probe'}, method=method)
                    self.assertIn(response.status_code, (401, 403))
                    create.assert_not_called()
                    lookup.assert_not_called()

    def test_platform_role_alone_and_missing_operation_grant_denied(self):
        from apps.subscriptions.views import PlanViewSet
        for staff, grant in [(False, True), (True, False)]:
            actor = self.user('superadmin', is_staff=staff)
            actor.has_perm.return_value = grant
            with patch.object(PlanViewSet, 'perform_create') as save:
                response = self.call(PlanViewSet, 'create', actor, {'name': 'Probe'})
            self.assertEqual(response.status_code, 403)
            save.assert_not_called()

    def test_inactive_human_and_service_claims_denied(self):
        from apps.subscriptions.views import PlanViewSet
        from apps.integration.models import IntegrationAPIKey
        actors = [self.user('superadmin', is_staff=True), IntegrationAPIKey(name='service')]
        actors[0].is_active = False
        for actor in actors:
            response = self.call(PlanViewSet, 'list', actor, method='get')
            self.assertIn(response.status_code, (401, 403))
        actor = self.user('superadmin', is_staff=True)
        for auth in ({'principal_type': 'service'}, {'client_id': 'iso-client'}, {'token_family': 'CENTRAL'}):
            request = self.factory.post('/offline/', {}, format='json')
            force_authenticate(request, user=actor, token=auth)
            response = PlanViewSet.as_view({'post': 'create'})(request)
            self.assertEqual(response.status_code, 403)

    def test_service_key_header_not_human_session(self):
        from apps.subscriptions.views import PlanViewSet
        request = self.factory.post('/offline/', {}, format='json', HTTP_X_API_KEY='synthetic')
        force_authenticate(request, user=self.user('superadmin', is_staff=True))
        self.assertEqual(PlanViewSet.as_view({'post': 'create'})(request).status_code, 403)

    def test_platform_subscription_actions_allow_and_preserve_effect(self):
        actor = self.user('admin', is_staff=True)
        for action in ('activate', 'cancel'):
            obj = NS(activate=Mock(), cancel=Mock())
            with patch.object(SubscriptionViewSet, 'get_object', return_value=obj):
                response = self.call(SubscriptionViewSet, action, actor)
            self.assertEqual(response.status_code, 200)
            getattr(obj, action).assert_called_once_with()
            actor.has_perm.assert_called_with('subscriptions.change_subscription')

    def test_platform_invoice_mark_paid_allow_activates_subscription(self):
        obj = NS(status='pending', subscription=NS(status='past_due', activate=Mock()), save=Mock())
        with patch.object(InvoiceViewSet, 'get_object', return_value=obj):
            response = self.call(InvoiceViewSet, 'mark_paid', self.user('admin', is_staff=True), {'payment_reference': 'offline'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(obj.status, 'paid')
        self.assertEqual(obj.payment_reference, 'offline')
        obj.save.assert_called_once_with()
        obj.subscription.activate.assert_called_once_with()

    def test_action_payload_cannot_assign_tenant_or_privileges(self):
        with patch.object(SubscriptionViewSet, 'get_object') as obj:
            response = self.call(SubscriptionViewSet, 'activate', self.user('admin', is_staff=True), {'organization': str(self.other.pk)})
        self.assertEqual(response.status_code, 400)
        obj.assert_not_called()

    def test_no_tenant_and_revoked_or_nonadmin_membership_denied(self):
        from apps.subscriptions.views import PaymentMethodViewSet
        for case in ('absent', 'revoked', 'viewer'):
            actor = self.user('org_admin')
            if case == 'absent':
                actor.organization = None
            self.membership_active = case != 'revoked'
            self.member_role = 'viewer' if case == 'viewer' else 'org_admin'
            with patch.object(PaymentMethodViewSet, 'perform_create') as create:
                response = self.call(PaymentMethodViewSet, 'create', actor, {'type': 'card'})
            self.assertEqual(response.status_code, 403)
            create.assert_not_called()

    def resolved(self, cls, obj):
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(patch.object(cls, 'filter_queryset', side_effect=lambda qs: qs))
        stack.enter_context(patch('rest_framework.generics.get_object_or_404', return_value=obj))
        return stack

    def test_user_update_cross_tenant_and_privileged_target_denied(self):
        for target in (self.user(), self.user('superadmin'), self.user('user', is_staff=True)):
            if target.role == 'user' and not target.is_staff:
                target.organization = self.other
            with self.resolved(UserViewSet, target), patch.object(target, 'save') as save:
                response = self.call(UserViewSet, 'partial_update', self.user('org_admin'), {'first_name': 'Probe'}, method='patch', pk=target.pk)
            self.assertEqual(response.status_code, 403)
            save.assert_not_called()

    def test_user_update_allow_and_privilege_mass_assignment_denied(self):
        target = self.user()
        actor = self.user('org_admin')
        with self.resolved(UserViewSet, target), patch.object(target, 'save') as save:
            response = self.call(UserViewSet, 'partial_update', actor, {'first_name': 'Updated'}, method='patch', pk=target.pk)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(target.first_name, 'Updated')
            save.assert_called_once()
            save.reset_mock()
            for data in ({'is_superuser': True}, {'is_staff': True}, {'organization': str(self.other.pk)}, {'role': 'admin'}, {'groups': [1]}, {'user_permissions': [1]}):
                response = self.call(UserViewSet, 'partial_update', actor, data, method='patch', pk=target.pk)
                self.assertEqual(response.status_code, 400)
            save.assert_not_called()

    def test_reset_password_allow_ordinary_same_tenant_target(self):
        target = self.user()
        with self.resolved(UserViewSet, target), patch.object(target, 'save') as save:
            response = self.call(UserViewSet, 'reset_password', self.user('org_admin'), {'new_password': 'Synthetic-Only-123!'}, pk=target.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(target.check_password('Synthetic-Only-123!'))
        self.assertTrue(target.must_change_password)
        save.assert_called_once()

    def test_invitation_update_allow_and_cross_tenant_denied(self):
        for org, expected in ((self.org, 200), (self.other, 403)):
            obj = OrganizationInvitation(id=uuid.uuid4(), organization=org, role='user',
                                         email='invited@example.invalid', expires_at=timezone.now()+timezone.timedelta(days=1))
            with self.resolved(OrganizationInvitationViewSet, obj), patch.object(obj, 'save') as save:
                response = self.call(OrganizationInvitationViewSet, 'partial_update', self.user('org_admin'), {'message': 'Welcome'}, method='patch', pk=obj.pk)
            self.assertEqual(response.status_code, expected)
            self.assertEqual(save.call_count, int(expected == 200))

    def test_membership_foreign_user_and_reparenting_rejected(self):
        from apps.users.serializers import UserOrganizationSerializer
        target = self.user()
        actor = self.user('org_admin')
        other_user = self.user()
        other_user.organization = self.other
        instance = UserOrganization(user=target, organization=self.org, role='user')
        from rest_framework.exceptions import ValidationError
        for data in ({'user': other_user}, {'organization': self.other}):
            with self.assertRaises(ValidationError):
                UserOrganizationSerializer(instance, context={'request': NS(user=actor)}).validate(data)
        with self.assertRaises(ValidationError):
            UserOrganizationSerializer(context={'request': NS(user=actor)}).validate({'user': other_user, 'organization': self.org, 'role': 'user'})
        with self.assertRaises(ValidationError):
            UserOrganizationSerializer(context={'request': NS(user=actor)}).validate({'user': self.user(is_staff=True), 'organization': self.org, 'role': 'user'})

    def test_payment_method_create_allow_and_foreign_organization_denied(self):
        from apps.subscriptions.views import PaymentMethodViewSet
        from apps.subscriptions.models import PaymentMethod
        actor = self.user('org_admin')
        def create(**kwargs):
            return PaymentMethod(**kwargs)
        with patch.object(PaymentMethod.objects, 'create', side_effect=create) as saved:
            response = self.call(PaymentMethodViewSet, 'create', actor, {'type': 'card', 'name': 'Offline'})
            self.assertEqual(response.status_code, 201)
            self.assertEqual(saved.call_args.kwargs['organization'], self.org)
            saved.reset_mock()
            with patch('django.db.models.query.QuerySet.get', return_value=self.other):
                response = self.call(PaymentMethodViewSet, 'create', actor, {'type': 'card', 'organization': str(self.other.pk)})
            self.assertEqual(response.status_code, 400)
            saved.assert_not_called()

    def test_payment_default_allow_and_cross_tenant_deny(self):
        from apps.subscriptions.views import PaymentMethodViewSet
        from apps.subscriptions.models import PaymentMethod
        for org, expected in ((self.org, 200), (self.other, 403)):
            obj = PaymentMethod(organization=org, type='card')
            with self.resolved(PaymentMethodViewSet, obj), patch.object(obj, 'save') as save, \
                 patch.object(PaymentMethod.objects, 'filter') as filtered:
                response = self.call(PaymentMethodViewSet, 'set_default', self.user('org_admin'), pk=obj.pk)
            self.assertEqual(response.status_code, expected)
            self.assertEqual(save.call_count, int(expected == 200))
            if expected == 200:
                filtered.assert_called_with(organization=self.org, is_default=True)
                filtered.return_value.update.assert_called_once_with(is_default=False)
            else:
                filtered.return_value.update.assert_not_called()

    def test_session_revoke_uses_authenticated_jti_and_owner(self):
        from apps.users.models import UserSession
        actor = self.user()
        request = self.factory.post('/offline/', {'current_token_jti': 'trusted'}, format='json')
        force_authenticate(request, user=actor, token={'jti': 'trusted'})
        with patch.object(UserSession.objects, 'filter') as sessions:
            response = UserViewSet.as_view({'post': 'revoke_sessions'})(request)
        self.assertEqual(response.status_code, 200)
        sessions.assert_called_once_with(user=actor, is_active=True)
        sessions.return_value.exclude.assert_called_once_with(token_jti='trusted')
        sessions.return_value.exclude.return_value.update.assert_called_once_with(is_active=False)
        with patch.object(UserSession.objects, 'filter') as sessions:
            response = self.call(UserViewSet, 'revoke_sessions', actor, {'current_token_jti': 'foreign'})
        self.assertEqual(response.status_code, 400)
        sessions.assert_not_called()

    def test_organization_settings_effect_allow_and_module_escalation_denied(self):
        from apps.organizations.views import OrganizationViewSet
        from apps.organizations.models import OrganizationSettings
        actor = self.user('org_admin')
        obj = OrganizationSettings(organization=self.org)
        with self.resolved(OrganizationViewSet, self.org), \
             patch.object(OrganizationSettings.objects, 'get_or_create', return_value=(obj, False)), \
             patch.object(obj, 'save') as save:
            response = self.call(OrganizationViewSet, 'organization_settings', actor, {'theme': 'light'}, method='patch', pk=self.org.pk)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(obj.theme, 'light')
            save.assert_called_once()
            save.reset_mock()
            response = self.call(OrganizationViewSet, 'organization_settings', actor, {'module_sca_enabled': True}, method='patch', pk=self.org.pk)
            self.assertEqual(response.status_code, 400)
            save.assert_not_called()

    def test_entitlement_relations_and_exact_product_scopes(self):
        from apps.products.serializers import OrganizationProductEntitlementSerializer
        from apps.products.models import OrganizationProductEntitlement, ProductSystem
        from apps.subscriptions.models import Subscription
        from rest_framework.exceptions import ValidationError
        product = ProductSystem(code='ISO_SMART', billing_enabled=False)
        obj = OrganizationProductEntitlement(organization=self.org, product=product, status='active')
        for data in ({'organization': self.other}, {'product': ProductSystem(code='MEDSUPPLIER')},
                     {'subscription': Subscription()}, {'scopes': ['*']},
                     {'scopes': ['MEDSUPPLIER:medsupplier.suppliercontact:read']}):
            with self.subTest(data=data), self.assertRaises(ValidationError):
                OrganizationProductEntitlementSerializer(obj).validate(data)
        data = {'scopes': ['ISO_SMART:resources.resource:read']}
        self.assertEqual(OrganizationProductEntitlementSerializer(obj).validate(data), data)

    def test_invoice_subscription_cross_tenant_relation_rejected(self):
        from apps.subscriptions.serializers import InvoiceDetailSerializer
        from apps.subscriptions.models import Subscription
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            InvoiceDetailSerializer().validate({'organization': self.org, 'subscription': Subscription()})

    def test_catalog_crud_allow_real_serializers_and_effects(self):
        from apps.subscriptions.models import Plan
        from apps.subscriptions.views import PlanViewSet
        from apps.products.models import ProductSystem, ISOStandard
        from apps.products.views import ProductSystemViewSet, ISOStandardViewSet
        actor = self.user('superadmin', is_staff=True)
        for cls, model, payload in (
            (PlanViewSet, Plan, {'code': 'offline', 'name': 'Offline', 'price': '15.00'}),
            (ProductSystemViewSet, ProductSystem, {'code': 'OFFLINE', 'name': 'Offline', 'slug': 'offline'}),
            (ISOStandardViewSet, ISOStandard, {'code': 'ISO-OFFLINE', 'name': 'Offline', 'full_name': 'Offline', 'version': '1'}),
        ):
            with self.subTest(model=model.__name__), \
                 patch('django.db.models.query.QuerySet.exists', return_value=False), \
                 patch.object(model.objects, 'create', side_effect=lambda **kw: model(**kw)) as create:
                response = self.call(cls, 'create', actor, payload)
                self.assertEqual(response.status_code, 201, response.data)
                create.assert_called_once()
            obj = model(**payload)
            for method, action in [('patch', 'partial_update'), ('put', 'update')]:
                data = {'name': 'Changed'} if method == 'patch' else dict(payload, name='Changed')
                with self.resolved(cls, obj), patch.object(obj, 'save') as save, \
                     patch('django.db.models.query.QuerySet.exists', return_value=False):
                    response = self.call(cls, action, actor, data, method=method, pk=obj.pk)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(obj.name, 'Changed')
                save.assert_called_once()
            with self.resolved(cls, obj), patch.object(obj, 'delete') as delete:
                response = self.call(cls, 'destroy', actor, method='delete', pk=obj.pk)
            self.assertEqual(response.status_code, 204)
            delete.assert_called_once()

    def test_module_toggle_allow_audit_and_org_admin_denied(self):
        from apps.products.models import OrganizationModule, ISOStandard, ModuleActivityLog
        from apps.products.views import OrganizationModuleViewSet
        obj = OrganizationModule(organization=self.org, iso_standard=ISOStandard(code='ISO-OFFLINE'))
        for actor, expected in ((self.user('admin', is_staff=True), 200), (self.user('org_admin'), 403)):
            with self.resolved(OrganizationModuleViewSet, obj), patch.object(obj, 'disable') as disable, \
                 patch.object(ModuleActivityLog.objects, 'create') as audit:
                response = self.call(OrganizationModuleViewSet, 'toggle', actor, {'action': 'disable', 'reason': 'offline'}, pk=obj.pk)
            self.assertEqual(response.status_code, expected, response.data)
            self.assertEqual(disable.call_count, int(expected == 200))
            self.assertEqual(audit.call_count, int(expected == 200))

    def test_entitlement_toggle_allow_audit_and_org_admin_denied(self):
        from apps.products.models import OrganizationProductEntitlement, ProductSystem, ProductEntitlementAuditLog
        from apps.products.views import OrganizationProductEntitlementViewSet
        obj = OrganizationProductEntitlement(organization=self.org, product=ProductSystem(code='ISO_SMART', billing_enabled=False))
        for actor, expected in ((self.user('admin', is_staff=True), 200), (self.user('org_admin'), 403)):
            with self.resolved(OrganizationProductEntitlementViewSet, obj), patch.object(obj, 'disable') as disable, \
                 patch.object(ProductEntitlementAuditLog.objects, 'create') as audit:
                response = self.call(OrganizationProductEntitlementViewSet, 'toggle', actor, {'action': 'disable', 'reason': 'offline'}, pk=obj.pk)
            self.assertEqual(response.status_code, expected, response.data)
            self.assertEqual(disable.call_count, int(expected == 200))
            self.assertEqual(audit.call_count, int(expected == 200))

    def test_membership_update_allow_preserves_identity(self):
        from apps.users.views import UserOrganizationViewSet
        target = self.user()
        obj = UserOrganization(user=target, organization=self.org, role='viewer')
        # Stop the fixture membership lookup mock while exercising the target queryset.
        with self.resolved(UserOrganizationViewSet, obj), patch.object(obj, 'save') as save:
            response = self.call(UserOrganizationViewSet, 'partial_update', self.user('org_admin'), {'role': 'user'}, method='patch', pk=obj.pk)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(obj.user_id, target.pk)
        self.assertEqual(obj.role, 'user')
        save.assert_called_once()

    def test_organization_activate_allow_records_tenant_event(self):
        from contextlib import nullcontext
        from apps.organizations.views import OrganizationViewSet
        self.org.status = 'suspended'
        with self.resolved(OrganizationViewSet, self.org), patch.object(self.org, 'save') as save, \
             patch('apps.organizations.views.transaction.atomic', return_value=nullcontext()), \
             patch.object(Organization.objects, 'select_for_update') as locked, \
             patch('apps.organizations.tenant_events.record_tenant_event') as event:
            locked.return_value.get.return_value = self.org
            actor = self.user('superadmin', is_staff=True)
            response = self.call(OrganizationViewSet, 'activate', actor, pk=self.org.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.org.status, 'active')
        save.assert_called_once()
        event.assert_called_once_with(self.org, actor_id=actor.pk)

    def test_module_bulk_validates_all_ids_before_effects_and_allows_valid(self):
        from contextlib import nullcontext
        from apps.products.models import ISOStandard, OrganizationModule, ModuleActivityLog
        from apps.products.views import OrganizationModuleViewSet
        iso = ISOStandard(code='ISO-OFFLINE')
        def lookup(query, **kw):
            if query.model is Organization and str(kw['pk']) == str(self.org.pk):
                return self.org
            if query.model is ISOStandard and str(kw['pk']) == str(iso.pk):
                return iso
            raise query.model.DoesNotExist
        actor = self.user('admin', is_staff=True)
        for ids, expected in (([str(iso.pk), str(uuid.uuid4())], 400), ([str(iso.pk)], 200)):
            module = OrganizationModule(organization=self.org, iso_standard=iso)
            with patch('django.db.models.query.QuerySet.get', autospec=True, side_effect=lookup), \
                 patch('apps.products.views.transaction.atomic', return_value=nullcontext()), \
                 patch.object(OrganizationModule.objects, 'filter') as existing, \
                 patch.object(OrganizationModule.objects, 'create', return_value=module) as create, \
                 patch.object(module, 'set_trial') as trial, \
                 patch.object(ModuleActivityLog.objects, 'create') as audit:
                existing.return_value.exists.return_value = False
                response = self.call(OrganizationModuleViewSet, 'bulk_assign', actor, {'organization_id': str(self.org.pk), 'iso_standards': ids})
            self.assertEqual(response.status_code, expected, response.data)
            self.assertEqual(create.call_count, int(expected == 200))
            self.assertEqual(trial.call_count, int(expected == 200))
            self.assertEqual(audit.call_count, int(expected == 200))

    def test_subscription_queryset_uses_canonical_not_invoice_ownership(self):
        view = SubscriptionViewSet()
        view.request = NS(user=self.user())
        with patch('apps.subscriptions.views.Subscription.objects.all') as all_subs:
            query = view.get_queryset()
        all_subs.return_value.filter.assert_called_once_with(organizations=self.org)
        exclusions = all_subs.return_value.filter.return_value.exclude.call_args.kwargs
        self.assertIn('organizations__in', exclusions)

    def test_subscription_invoices_do_not_leak_other_tenant(self):
        from apps.subscriptions.models import Subscription, Invoice
        obj = Subscription()
        with self.resolved(SubscriptionViewSet, obj), patch.object(Invoice.objects, 'filter') as invoices:
            invoices.return_value.select_related.return_value.order_by.return_value.filter.return_value = []
            response = self.call(SubscriptionViewSet, 'invoices', self.user(), method='get', pk=obj.pk)
        self.assertEqual(response.status_code, 200)
        invoices.return_value.select_related.return_value.order_by.return_value.filter.assert_called_once_with(organization_id=self.org.pk)


class ServiceDataTests(TestCase):
    def setUp(self):
        from apps.integration.models import IntegrationAPIKey
        self.factory = APIRequestFactory()
        self.org = Organization(id=uuid.uuid4(), name='Tenant', code='TENANT', status='active', created_at=timezone.now())
        self.principal = IntegrationAPIKey(id=1, credential_id='a'*32, name='offline', status='active', credential_format='hashed_v1')
        self.grant = {'operations': ['get_organization', 'get_user_by_id', 'list_organizations', 'get_organization_products', 'validate_organization_product_access'],
                      'tenant_ids': [str(self.org.pk)], 'product_codes': ['ISO_SMART']}

    def call(self, handler, data=None, **kwargs):
        from django.test import override_settings
        from apps.integration import views
        request = (self.factory.post('/offline/', data, format='json', HTTP_X_API_KEY='synthetic') if data is not None
                   else self.factory.get('/offline/', HTTP_X_API_KEY='synthetic'))
        with override_settings(INTEGRATION_API_GRANTS={self.principal.credential_id: self.grant}), \
             patch.object(views, 'authenticate_integration_api_key', return_value=self.principal), \
             patch.object(self.principal, 'save'):
            return handler(request, **kwargs)

    def test_explicit_service_tenant_read_allow(self):
        from apps.integration import views
        with patch.object(Organization.objects, 'get', return_value=self.org) as get:
            response = self.call(views.get_organization, org_id=self.org.pk)
        self.assertEqual(response.status_code, 200)
        get.assert_called_once_with(id=self.org.pk, status='active')

    def test_foreign_tenant_and_missing_grants_deny_before_business_query(self):
        from apps.integration import views
        for case in ('foreign', 'missing', 'revoked', 'ungranted_operation', 'malformed'):
            self.principal.is_active = case != 'revoked'
            self.grant['operations'] = ['get_organization'] if case != 'ungranted_operation' else []
            self.grant['tenant_ids'] = [] if case == 'missing' else [str(self.org.pk)]
            if case == 'malformed':
                self.grant['tenant_ids'] = ['*']
            tenant = uuid.uuid4() if case == 'foreign' else self.org.pk
            with patch.object(Organization.objects, 'get') as get:
                response = self.call(views.get_organization, org_id=tenant)
            self.assertIn(response.status_code, (400, 403))
            get.assert_not_called()

    def test_service_list_filters_tenants(self):
        from apps.integration import views
        with patch.object(Organization.objects, 'filter', return_value=[self.org]) as filtered:
            response = self.call(views.list_organizations)
        self.assertEqual(response.status_code, 200)
        filtered.assert_called_once_with(status='active', pk__in={str(self.org.pk)})

    def test_service_product_isolation(self):
        from apps.integration import views
        with patch.object(Organization.objects, 'get') as get:
            response = self.call(views.validate_organization_product_access, org_id=self.org.pk, product_code='MEDSUPPLIER')
        self.assertEqual(response.status_code, 403)
        get.assert_not_called()
        with patch.object(Organization.objects, 'get', return_value=self.org), \
             patch.object(views, '_active_product_entitlements') as entitlements:
            entitlements.return_value.filter.return_value = []
            response = self.call(views.get_organization_products, org_id=self.org.pk)
        self.assertEqual(response.status_code, 200)
        entitlements.return_value.filter.assert_called_once_with(product__code__in=['ISO_SMART'])

    def test_service_user_lookup_requires_tenant_and_membership(self):
        from apps.integration import views
        with patch.object(User.objects, 'get') as get:
            response = self.call(views.get_user_by_id, {'user_id': str(uuid.uuid4())})
        self.assertEqual(response.status_code, 400)
        get.assert_not_called()
        user = User(email='offline@example.invalid')
        with patch.object(User.objects, 'get', return_value=user), patch.object(UserOrganization.objects, 'filter') as members:
            scoped = members.return_value.select_related.return_value.filter.return_value
            scoped.exists.return_value = False
            response = self.call(views.get_user_by_id, {'user_id': str(user.pk), 'organization_id': str(self.org.pk)})
        self.assertEqual(response.status_code, 404)


class PlatformBillingTests(TestCase):
    setUp = ControlPlaneTests.setUp
    members = ControlPlaneTests.members
    user = ControlPlaneTests.user
    call = ControlPlaneTests.call
    resolved = ControlPlaneTests.resolved

    def test_all_billing_actions_deny_role_only_before_handler(self):
        from apps.billing import views
        from apps.users.platform_api_authorization import POLICIES
        for name, actions in POLICIES.items():
            cls = getattr(views, name, None)
            if cls is None:
                continue
            for action in actions:
                with self.subTest(view=name, action=action):
                    if hasattr(cls, 'get_extra_actions'):
                        method = ('get' if action in {'list', 'retrieve', 'export_csv', 'compliance_preview', 'mapping_audit'}
                                  else 'patch' if action == 'partial_update' else 'put' if action == 'update'
                                  else 'delete' if action == 'destroy' else 'post')
                        with patch.object(cls, action) as handler:
                            response = self.call(cls, action, self.user('admin'), method=method)
                    else:
                        with patch.object(cls, action) as handler:
                            request = getattr(self.factory, action)('/offline/', {}, format='json')
                            force_authenticate(request, user=self.user('admin'))
                            response = cls.as_view()(request)
                    self.assertEqual(response.status_code, 403)
                    handler.assert_not_called()

    def test_billing_catalog_mapping_allow_and_missing_permission_deny(self):
        from apps.billing.views import ProductCatalogViewSet
        actor = self.user('admin', is_staff=True)
        with patch('apps.billing.views.auto_map_product_catalog_candidates', return_value={'items': []}) as service:
            response = self.call(ProductCatalogViewSet, 'auto_map', actor, {'dry_run': True})
            self.assertEqual(response.status_code, 200)
            service.assert_called_once_with(dry_run=True)
            service.reset_mock()
            actor.has_perm.side_effect = lambda perm: perm != 'billing.change_productcatalog'
            response = self.call(ProductCatalogViewSet, 'auto_map', actor, {'dry_run': False})
            self.assertEqual(response.status_code, 403)
            service.assert_not_called()

    def test_billing_foreign_subscription_and_price_denied(self):
        from apps.billing.serializers import IssueInvoiceSerializer
        from apps.billing.models import ProductCatalog, ProductPrice
        from apps.subscriptions.models import Subscription
        from rest_framework.exceptions import ValidationError
        product = ProductCatalog()
        price = ProductPrice(product=product)
        with self.assertRaises(ValidationError):
            IssueInvoiceSerializer().validate({'organization': self.org, 'product': product, 'product_price': price, 'subscription': Subscription()})
        price.product = ProductCatalog()
        with self.assertRaises(ValidationError):
            IssueInvoiceSerializer().validate({'organization': self.org, 'product': product, 'product_price': price})

    def test_billing_payment_reject_allow_service_effect_and_org_admin_deny(self):
        from apps.billing.models import PaymentRecord, ElectronicInvoice, ProductCatalog, FiscalProfile
        from apps.billing.views import PaymentRecordViewSet
        invoice = ElectronicInvoice(organization=self.org, product=ProductCatalog(), fiscal_profile=FiscalProfile(), invoice_number='OFFLINE')
        obj = PaymentRecord(organization=self.org, invoice=invoice)
        for actor, expected in ((self.user('admin', is_staff=True), 200), (self.user('org_admin'), 403)):
            with self.resolved(PaymentRecordViewSet, obj), \
                 patch('apps.billing.views.reject_payment_record', return_value=obj) as reject, \
                 patch('apps.billing.views._create_notification_event') as notify:
                response = self.call(PaymentRecordViewSet, 'reject', actor, {'notes': 'offline'}, pk=obj.pk)
            self.assertEqual(response.status_code, expected, response.data)
            self.assertEqual(reject.call_count, int(expected == 200))
            self.assertEqual(notify.call_count, int(expected == 200))

    def test_backoffice_readiness_allow_service_and_role_only_deny(self):
        from apps.api.views import ProductReadinessView
        for staff, expected in ((True, 200), (False, 403)):
            request = self.factory.get('/offline/')
            force_authenticate(request, user=self.user('admin', is_staff=staff))
            with patch('apps.api.views.build_product_access_readiness_report', return_value={'ok': True}) as service:
                response = ProductReadinessView.as_view()(request)
            self.assertEqual(response.status_code, expected)
            self.assertEqual(service.call_count, int(expected == 200))

    def test_logout_owner_binding_allow_and_foreign_refresh_denied(self):
        from apps.users.views import LogoutView
        actor = self.user()
        for owner, expected in ((str(actor.pk), 200), (str(uuid.uuid4()), 400)):
            token = MagicMock()
            token.get.return_value = owner
            request = self.factory.post('/offline/', {'refresh': 'synthetic'}, format='json')
            force_authenticate(request, user=actor)
            with patch('apps.users.services.RefreshToken', return_value=token), \
                 patch('apps.users.views.log_logout_activity') as log:
                response = LogoutView.as_view()(request)
            self.assertEqual(response.status_code, expected)
            self.assertEqual(token.blacklist.call_count, int(expected == 200))
            self.assertEqual(log.call_count, int(expected == 200))

    def test_core_mutations_reject_regular_user_before_handler(self):
        from importlib import import_module
        from apps.users.api_authorization import POLICIES
        modules = [import_module('apps.'+name+'.views') for name in ('users', 'organizations', 'products', 'subscriptions')]
        operations = {'create', 'update', 'partial_update', 'destroy', 'activate', 'deactivate', 'suspend', 'unlock',
                      'reset_password', 'organization_settings', 'cancel', 'resend', 'toggle', 'bulk_assign', 'set_default', 'mark_paid', 'change_plan'}
        for name, (_, _, actions) in POLICIES.items():
            cls = next((getattr(m, name) for m in modules if hasattr(m, name)), None)
            if cls is None:
                continue
            for action in actions & operations:
                method = 'patch' if action in {'partial_update', 'organization_settings'} else 'put' if action == 'update' else 'delete' if action == 'destroy' else 'post'
                with self.subTest(view=name, action=action), patch.object(cls, action) as handler:
                    response = self.call(cls, action, self.user(), method=method)
                    self.assertEqual(response.status_code, 403)
                    handler.assert_not_called()

    def test_feature_flags_live_member_allow_and_foreign_id_deny(self):
        from apps.api.views import FeatureFlagsView
        from apps.organizations.models import OrganizationFeatureFlag
        for query, expected in (('', 200), ('?organization_id='+str(self.other.pk), 403)):
            request = self.factory.get('/offline/'+query)
            force_authenticate(request, user=self.user())
            with patch.object(OrganizationFeatureFlag.objects, 'resolve_for_organization', return_value={'test': False}) as flags:
                response = FeatureFlagsView.as_view()(request)
            self.assertEqual(response.status_code, expected)
            self.assertEqual(flags.call_count, int(expected == 200))

    def test_user_create_allow_and_global_role_denied_with_real_serializer(self):
        actor = self.user('org_admin')
        data = {'email': 'new@example.invalid', 'first_name': 'New', 'last_name': 'User',
                'password': 'Synthetic-New-123!', 'password_confirm': 'Synthetic-New-123!', 'role': 'user'}
        with patch.object(User.objects, 'filter') as existing, patch.object(User, 'save') as save, \
             patch.object(UserOrganization.objects, 'create') as membership:
            existing.return_value.first.return_value = None
            response = self.call(UserViewSet, 'create', actor, data)
            self.assertEqual(response.status_code, 201, response.data)
            save.assert_called_once()
            self.assertEqual(membership.call_args.kwargs['organization'], self.org)
            self.assertEqual(membership.call_args.kwargs['role'], 'user')
            save.reset_mock()
            membership.reset_mock()
            response = self.call(UserViewSet, 'create', actor, dict(data, role='admin'))
            self.assertEqual(response.status_code, 400)
            save.assert_not_called()
            membership.assert_not_called()

    def test_invitation_create_allow_and_foreign_tenant_deny(self):
        data = {'email': 'new@example.invalid', 'organization': str(self.org.pk), 'role': 'user'}
        for org, expected in ((self.org, 201), (self.other, 400)):
            with patch('django.db.models.query.QuerySet.get', return_value=org), \
                 patch('django.db.models.query.QuerySet.exists', return_value=False), \
                 patch.object(OrganizationInvitation.objects, 'create', side_effect=lambda **kw: OrganizationInvitation(**kw)) as create:
                response = self.call(OrganizationInvitationViewSet, 'create', self.user('org_admin'), dict(data, organization=str(org.pk)))
            self.assertEqual(response.status_code, expected, response.data)
            self.assertEqual(create.call_count, int(expected == 201))
            if expected == 201:
                self.assertEqual(create.call_args.kwargs['organization'], self.org)
                self.assertEqual(create.call_args.kwargs['role'], 'user')

    def test_subscription_patch_privileged_fields_only_platform(self):
        from apps.subscriptions.models import Subscription, Plan
        obj = Subscription(plan=Plan(), status='active')
        for actor, expected in ((self.user(), 403), (self.user('admin', is_staff=True), 200)):
            with self.resolved(SubscriptionViewSet, obj), patch.object(obj, 'save') as save, \
                 patch('apps.subscriptions.serializers.SubscriptionDetailSerializer._get_organization', return_value=self.org):
                response = self.call(SubscriptionViewSet, 'partial_update', actor, {'discount_percent': '10.00'}, method='patch', pk=obj.pk)
            self.assertEqual(response.status_code, expected, response.data)
            self.assertEqual(save.call_count, int(expected == 200))

    def test_malformed_plan_id_does_not_reach_save(self):
        obj = NS(save=Mock())
        with patch.object(SubscriptionViewSet, 'get_object', return_value=obj):
            response = self.call(SubscriptionViewSet, 'change_plan', self.user('admin', is_staff=True), {'plan_id': 'invalid'})
        self.assertEqual(response.status_code, 400)
        obj.save.assert_not_called()

    def test_plan_detail_read_allows_human_without_tenant(self):
        from apps.subscriptions.models import Plan
        from apps.subscriptions.views import PlanViewSet
        plan = Plan(code='read-only', name='Readable', price='15.00', is_active=True)
        actor = self.user()
        actor.organization = None
        with self.resolved(PlanViewSet, plan):
            response = self.call(PlanViewSet, 'retrieve', actor, method='get', pk=plan.pk)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['code'], 'read-only')

    def test_plan_read_queryset_keeps_inactive_catalog_hidden(self):
        from apps.subscriptions.models import Plan
        from apps.subscriptions.views import PlanViewSet
        view = PlanViewSet()
        view.request = NS(user=self.user())
        with patch.object(Plan.objects, 'all') as plans:
            view.get_queryset()
        plans.return_value.filter.assert_called_once_with(is_active=True)
