from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.organizations.views import OrganizationViewSet


class OrganizationSettingsAuthorizationTests(SimpleTestCase):
    def permissions_allow(self, method, user):
        request = SimpleNamespace(method=method, user=user)
        view = OrganizationViewSet()
        view.action = 'organization_settings'
        view.request = request
        return all(
            permission.has_permission(request, view)
            for permission in view.get_permissions()
        )

    def user(self, *, authenticated=True, org_admin=False):
        return SimpleNamespace(
            is_authenticated=authenticated,
            is_org_admin=org_admin,
        )

    def test_organization_member_cannot_change_settings(self):
        self.assertFalse(
            self.permissions_allow('PATCH', self.user())
        )

    def test_organization_admin_can_read_settings(self):
        self.assertTrue(
            self.permissions_allow('GET', self.user(org_admin=True))
        )

    def test_organization_member_can_read_settings(self):
        self.assertTrue(
            self.permissions_allow('GET', self.user())
        )

    def test_organization_admin_can_change_settings(self):
        self.assertTrue(
            self.permissions_allow('PATCH', self.user(org_admin=True))
        )

    def test_unauthenticated_user_cannot_read_settings(self):
        self.assertFalse(
            self.permissions_allow('GET', self.user(authenticated=False))
        )
