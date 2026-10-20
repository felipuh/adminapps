from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.permissions import IsAuthenticated

from apps.subscriptions.views import PlanViewSet
from apps.users.permissions import IsSuperAdmin


class PlanViewSetAuthorizationTests(SimpleTestCase):
    def permissions_for(self, action, *, authenticated=True, superadmin=False):
        view = PlanViewSet()
        view.action = action
        view.request = SimpleNamespace(
            user=SimpleNamespace(
                is_authenticated=authenticated,
                is_superadmin=superadmin,
            )
        )
        return view.get_permissions()

    def test_read_actions_require_an_authenticated_user(self):
        for action in ('list', 'retrieve'):
            with self.subTest(action=action):
                permissions = self.permissions_for(action)
                self.assertEqual(len(permissions), 1)
                self.assertIsInstance(permissions[0], IsAuthenticated)

                anonymous_permissions = self.permissions_for(
                    action,
                    authenticated=False,
                )
                self.assertFalse(
                    all(
                        permission.has_permission(
                            SimpleNamespace(
                                user=SimpleNamespace(is_authenticated=False)
                            ),
                            None,
                        )
                        for permission in anonymous_permissions
                    )
                )

    def test_every_model_mutation_requires_superadmin(self):
        for action in ('create', 'update', 'partial_update', 'destroy'):
            with self.subTest(action=action):
                permissions = self.permissions_for(action)
                self.assertEqual(len(permissions), 1)
                self.assertIsInstance(permissions[0], IsSuperAdmin)

                regular_user = SimpleNamespace(
                    is_authenticated=True,
                    is_superadmin=False,
                )
                self.assertFalse(
                    permissions[0].has_permission(
                        SimpleNamespace(user=regular_user),
                        None,
                    )
                )

                superadmin = SimpleNamespace(
                    is_authenticated=True,
                    is_superadmin=True,
                )
                self.assertTrue(
                    permissions[0].has_permission(
                        SimpleNamespace(user=superadmin),
                        None,
                    )
                )
