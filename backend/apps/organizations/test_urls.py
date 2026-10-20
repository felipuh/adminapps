"""The invitation routes must resolve before the organization detail route."""

from django.test import SimpleTestCase
from django.urls import resolve

from apps.organizations.views import OrganizationInvitationViewSet


class OrganizationInvitationRouteTests(SimpleTestCase):
    def test_invitation_list_reaches_invitation_viewset(self):
        match = resolve('/api/organizations/invitations/')
        self.assertIs(match.func.cls, OrganizationInvitationViewSet)
        self.assertEqual(match.func.actions['post'], 'create')
