from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase

from apps.products.admin import (
    ISOStandardAdmin,
    ModuleActivityLogAdmin,
    OrganizationModuleAdmin,
    OrganizationProductEntitlementAdmin,
    ProductEntitlementAuditLogAdmin,
    ProductSystemAdmin,
)
from apps.products.models import (
    ISOStandard,
    ModuleActivityLog,
    OrganizationModule,
    OrganizationProductEntitlement,
    ProductEntitlementAuditLog,
    ProductSystem,
)
from apps.organizations.admin import (
    OrganizationAdmin,
    OrganizationFeatureFlagAdmin,
    OrganizationInvitationAdmin,
    OrganizationSettingsAdmin,
)
from apps.organizations.models import (
    Organization,
    OrganizationFeatureFlag,
    OrganizationInvitation,
    OrganizationSettings,
)
from apps.subscriptions.admin import InvoiceAdmin, PaymentMethodAdmin, PlanAdmin, SubscriptionAdmin
from apps.subscriptions.models import Invoice, PaymentMethod, Plan, Subscription
from apps.users.admin import UserAdmin, UserOrganizationAdmin, UserSessionAdmin
from apps.users.models import User, UserOrganization, UserSession


class DjangoAdminRoleAuthorizationTests(SimpleTestCase):
    def setUp(self):
        self.site = AdminSite()

    def request_for(self, *, is_admin=False, is_superadmin=False, is_org_admin=False,
                    is_superuser=False, pk='actor',
                    organization_id='actor-org'):
        user = SimpleNamespace(
            pk=pk,
            is_authenticated=True,
            is_admin=is_admin,
            is_superadmin=is_superadmin,
            is_org_admin=is_org_admin,
            is_superuser=is_superuser,
            organization_id=organization_id,
            has_perm=lambda permission: True,
        )
        return SimpleNamespace(user=user)

    def assert_admin_write_role(self, admin_class, model, *, allowed, role):
        model_admin = admin_class(model, self.site)
        request = self.request_for(**{role: allowed})
        for permission in (
            model_admin.has_add_permission,
            model_admin.has_change_permission,
            model_admin.has_delete_permission,
            model_admin.has_view_permission,
        ):
            self.assertEqual(permission(request), allowed)

    def test_sensitive_product_and_plan_writes_match_api_roles(self):
        for admin_class, model in (
            (ProductSystemAdmin, ProductSystem),
            (ISOStandardAdmin, ISOStandard),
            (PlanAdmin, Plan),
        ):
            with self.subTest(admin=admin_class.__name__):
                self.assert_admin_write_role(
                    admin_class, model, allowed=False, role='is_superadmin',
                )
                self.assert_admin_write_role(
                    admin_class, model, allowed=True, role='is_superadmin',
                )

        for admin_class, model in (
            (OrganizationProductEntitlementAdmin, OrganizationProductEntitlement),
            (OrganizationModuleAdmin, OrganizationModule),
            (SubscriptionAdmin, Subscription),
            (InvoiceAdmin, Invoice),
            (PaymentMethodAdmin, PaymentMethod),
        ):
            with self.subTest(admin=admin_class.__name__):
                self.assert_admin_write_role(
                    admin_class, model, allowed=False, role='is_admin',
                )
                self.assert_admin_write_role(
                    admin_class, model, allowed=True, role='is_admin',
                )

    def test_user_admin_requires_org_admin_for_create_and_change(self):
        model_admin = UserAdmin(User, self.site)
        request = self.request_for(is_org_admin=False)
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))

        request = self.request_for(is_org_admin=True)
        self.assertTrue(model_admin.has_add_permission(request))
        self.assertTrue(model_admin.has_change_permission(request))

    def test_user_and_membership_admin_disable_bulk_delete(self):
        request = self.request_for(is_admin=True, is_org_admin=True)
        user_admin = UserAdmin(User, self.site)
        membership_admin = UserOrganizationAdmin(UserOrganization, self.site)
        self.assertFalse(user_admin.has_delete_permission(request))
        self.assertFalse(membership_admin.has_delete_permission(request))

        own_user = SimpleNamespace(pk=request.user.pk)
        self.assertFalse(user_admin.has_delete_permission(request, own_user))

    def test_user_admin_protects_global_privilege_fields(self):
        model_admin = UserAdmin(User, self.site)
        request = self.request_for(is_org_admin=True, is_admin=True)
        readonly_fields = model_admin.get_readonly_fields(request)
        self.assertIn('is_staff', readonly_fields)
        self.assertIn('is_superuser', readonly_fields)

        request = self.request_for(is_org_admin=True, is_admin=True, pk='user-1')
        target = SimpleNamespace(pk='user-1', role='user')
        self.assertIn('role', model_admin.get_readonly_fields(request, target))

        other_user = SimpleNamespace(pk='user-2', role='user')
        self.assertIn(
            'organization',
            model_admin.get_readonly_fields(request, other_user),
        )

    def test_organization_admin_mutations_match_platform_roles(self):
        organization_admin = OrganizationAdmin(Organization, self.site)
        org_admin_request = self.request_for(is_admin=True)
        self.assertFalse(organization_admin.has_add_permission(org_admin_request))
        self.assertFalse(organization_admin.has_delete_permission(org_admin_request))
        self.assertTrue(
            organization_admin.has_add_permission(
                self.request_for(is_superadmin=True, is_admin=True)
            )
        )

        settings_admin = OrganizationSettingsAdmin(
            OrganizationSettings, self.site,
        )
        org_request = self.request_for(
            is_org_admin=True,
            pk='actor',
        )
        own_settings = SimpleNamespace(organization_id='actor-org')
        other_settings = SimpleNamespace(organization_id='other-org')
        self.assertTrue(settings_admin.has_change_permission(org_request, own_settings))
        self.assertFalse(settings_admin.has_change_permission(org_request, other_settings))

    def test_membership_admin_blocks_self_and_cross_organization_edits(self):
        model_admin = UserOrganizationAdmin(UserOrganization, self.site)
        request = self.request_for(is_org_admin=True, pk='actor')
        own_membership = SimpleNamespace(
            user_id='actor',
            organization_id='actor-org',
        )
        other_membership = SimpleNamespace(
            user_id='other-user',
            organization_id='other-org',
        )
        self.assertFalse(model_admin.has_change_permission(request, own_membership))
        self.assertFalse(model_admin.has_delete_permission(request, own_membership))
        self.assertFalse(model_admin.has_change_permission(request, other_membership))
        self.assertFalse(model_admin.has_delete_permission(request, other_membership))

    def test_security_audit_and_session_admins_are_immutable(self):
        for admin_class, model in (
            (ProductEntitlementAuditLogAdmin, ProductEntitlementAuditLog),
            (ModuleActivityLogAdmin, ModuleActivityLog),
            (UserSessionAdmin, UserSession),
        ):
            with self.subTest(admin=admin_class.__name__):
                model_admin = admin_class(model, self.site)
                request = self.request_for(is_admin=True)
                self.assertFalse(model_admin.has_add_permission(request))
                self.assertFalse(model_admin.has_change_permission(request))
                self.assertFalse(model_admin.has_delete_permission(request))

        feature_admin = OrganizationFeatureFlagAdmin(
            OrganizationFeatureFlag, self.site,
        )
        self.assertFalse(
            feature_admin.has_change_permission(
                self.request_for(is_admin=True),
            )
        )
        self.assertTrue(
            feature_admin.has_change_permission(
                self.request_for(is_superadmin=True),
            )
        )

    def test_non_superadmin_cannot_assign_superadmin_role_in_admin(self):
        model_admin = UserAdmin(User, self.site)
        request = self.request_for(is_org_admin=True, is_admin=True)
        target = SimpleNamespace(
            role='superadmin',
            is_staff=False,
            is_superuser=False,
        )
        form = SimpleNamespace(changed_data=['role'])

        with self.assertRaises(PermissionDenied):
            model_admin.save_model(request, target, form, change=False)

    def test_non_superuser_cannot_grant_django_staff_privileges(self):
        model_admin = UserAdmin(User, self.site)
        request = self.request_for(is_org_admin=True, is_admin=True)
        target = SimpleNamespace(
            role='user',
            is_staff=True,
            is_superuser=False,
        )
        form = SimpleNamespace(changed_data=['is_staff'])

        with self.assertRaises(PermissionDenied):
            model_admin.save_model(request, target, form, change=False)

    def test_org_admin_forms_do_not_offer_global_roles(self):
        request = self.request_for(
            is_org_admin=True,
            organization_id='00000000-0000-0000-0000-000000000001',
        )

        user_form = UserAdmin(User, self.site).get_form(request)
        user_roles = {role for role, _label in user_form.base_fields['role'].choices}
        self.assertNotIn('admin', user_roles)
        self.assertNotIn('superadmin', user_roles)

        invitation_form = OrganizationInvitationAdmin(
            OrganizationInvitation, self.site,
        ).get_form(request)
        invitation_roles = {
            role for role, _label in invitation_form.base_fields['role'].choices
        }
        self.assertNotIn('admin', invitation_roles)
        self.assertNotIn('superadmin', invitation_roles)
