from types import SimpleNamespace
from contextlib import nullcontext
import uuid
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.organizations.models import Organization, OrganizationInvitation
from apps.organizations.serializers import OrganizationInvitationCreateSerializer
from apps.users.serializers import (
    RegisterSerializer,
    UserCreateSerializer,
    UserOrganizationSerializer,
    UserUpdateSerializer,
)
from apps.users.views import UserOrganizationViewSet


class UserOrganizationAuthorizationTests(SimpleTestCase):
    def setUp(self):
        self.organization = SimpleNamespace(id='org-a', pk='org-a')
        self.foreign_organization = SimpleNamespace(id='org-b', pk='org-b')
        self.actor = SimpleNamespace(
            id='user-a',
            pk='user-a',
            is_authenticated=True,
            is_admin=False,
            is_superadmin=False,
            organization=self.organization,
            organization_id='org-a',
        )
        self.target = SimpleNamespace(
            id='user-b',
            pk='user-b',
            organization_id='org-a',
        )

    def serializer(self, *, actor=None, instance=None):
        request = SimpleNamespace(user=actor or self.actor)
        return UserOrganizationSerializer(
            instance=instance,
            context={'request': request},
        )

    def test_org_admin_cannot_create_membership_in_another_tenant(self):
        with self.assertRaises(ValidationError):
            self.serializer().validate({
                'organization': self.foreign_organization,
                'user': self.target,
                'role': 'user',
            })

    def test_org_admin_cannot_grant_global_admin_role(self):
        with self.assertRaises(ValidationError):
            self.serializer().validate({
                'organization': self.organization,
                'user': self.target,
                'role': 'superadmin',
            })

    def test_actor_cannot_create_or_update_own_membership(self):
        with self.assertRaises(ValidationError):
            self.serializer().validate({
                'organization': self.organization,
                'user': self.actor,
                'role': 'superadmin',
            })

        instance = SimpleNamespace(user=self.actor, organization=self.organization)
        with self.assertRaises(ValidationError):
            self.serializer(instance=instance).validate({'role': 'user'})

    def test_org_admin_can_manage_member_in_own_tenant_with_non_global_role(self):
        attrs = {
            'organization': self.organization,
            'user': self.target,
            'role': 'user',
        }
        self.assertEqual(self.serializer().validate(attrs), attrs)

    def test_org_admin_cannot_delete_own_membership(self):
        view = UserOrganizationViewSet()
        view.request = SimpleNamespace(user=self.actor)
        with self.assertRaises(PermissionDenied):
            view.perform_destroy(SimpleNamespace(user=self.actor))

    def test_global_admin_cannot_grant_superadmin_on_user_create(self):
        actor = SimpleNamespace(
            is_authenticated=True,
            is_admin=True,
            is_superadmin=False,
        )
        serializer = UserCreateSerializer(
            context={'request': SimpleNamespace(user=actor)}
        )
        with self.assertRaises(ValidationError):
            serializer.validate({
                'email': 'target@example.test',
                'password': 'temporary-password',
                'password_confirm': 'temporary-password',
                'role': 'superadmin',
            })

    def test_admin_cannot_promote_self_or_other_user_to_superadmin(self):
        actor = SimpleNamespace(
            id='user-a',
            pk='user-a',
            is_authenticated=True,
            is_admin=True,
            is_superadmin=False,
            organization_id='org-a',
        )
        own_user = SimpleNamespace(
            id='user-a',
            pk='user-a',
            role='admin',
            organization_id='org-a',
        )
        own_serializer = UserUpdateSerializer(
            instance=own_user,
            context={'request': SimpleNamespace(user=actor)},
        )
        with self.assertRaises(ValidationError):
            own_serializer.validate({'role': 'superadmin'})

        target = SimpleNamespace(
            id='user-b',
            pk='user-b',
            role='user',
            organization_id='org-a',
        )
        target_serializer = UserUpdateSerializer(
            instance=target,
            context={'request': SimpleNamespace(user=actor)},
        )
        with self.assertRaises(ValidationError):
            target_serializer.validate({'role': 'superadmin'})

    def test_admin_cannot_invite_superadmin_or_other_tenant(self):
        org_admin = SimpleNamespace(
            is_authenticated=True,
            is_admin=False,
            is_superadmin=False,
            organization_id='org-a',
        )
        serializer = OrganizationInvitationCreateSerializer(
            context={'request': SimpleNamespace(user=org_admin)}
        )
        with self.assertRaises(ValidationError):
            serializer.validate({
                'organization': self.organization,
                'role': 'superadmin',
            })
        with self.assertRaises(ValidationError):
            serializer.validate({
                'organization': self.foreign_organization,
                'role': 'user',
            })

        admin = SimpleNamespace(
            is_authenticated=True,
            is_admin=True,
            is_superadmin=False,
            organization_id='org-a',
        )
        admin_serializer = OrganizationInvitationCreateSerializer(
            context={'request': SimpleNamespace(user=admin)}
        )
        with self.assertRaises(ValidationError):
            admin_serializer.validate({
                'organization': self.organization,
                'role': 'superadmin',
            })

    def test_registration_invitation_must_match_the_invited_email(self):
        invitation = SimpleNamespace(
            email='invited@example.test',
            is_expired=False,
            status='pending',
            role='user',
        )
        with patch('apps.users.serializers.User.objects.filter') as user_filter:
            with patch(
                'apps.organizations.models.OrganizationInvitation.objects.get',
                return_value=invitation,
            ):
                user_filter.return_value.first.return_value = None
                serializer = RegisterSerializer()
                with self.assertRaises(ValidationError):
                    serializer.validate({
                        'email': 'attacker@example.test',
                        'password': 'Temporary-Password-1!',
                        'password_confirm': 'Temporary-Password-1!',
                        'invitation_token': 'bearer-token',
                    })

    def test_registration_rejects_invalid_or_expired_invitations(self):
        serializer = RegisterSerializer()
        with patch('apps.users.serializers.User.objects.filter') as user_filter:
            user_filter.return_value.first.return_value = None
            with patch(
                'apps.organizations.models.OrganizationInvitation.objects.get',
                side_effect=OrganizationInvitation.DoesNotExist,
            ):
                with self.assertRaises(ValidationError):
                    serializer.validate({
                        'email': 'invited@example.test',
                        'password': 'Temporary-Password-1!',
                        'password_confirm': 'Temporary-Password-1!',
                        'invitation_token': 'invalid-token',
                    })

            expired = SimpleNamespace(
                email='invited@example.test',
                is_expired=True,
                status='pending',
                role='user',
            )
            with patch(
                'apps.organizations.models.OrganizationInvitation.objects.get',
                return_value=expired,
            ):
                with self.assertRaises(ValidationError):
                    serializer.validate({
                        'email': 'invited@example.test',
                        'password': 'Temporary-Password-1!',
                        'password_confirm': 'Temporary-Password-1!',
                        'invitation_token': 'expired-token',
                    })

    def test_registration_rejects_invitation_with_unauthorized_global_role(self):
        invitation = SimpleNamespace(
            email='invited@example.test',
            is_expired=False,
            status='pending',
            role='superadmin',
            invited_by=SimpleNamespace(is_superadmin=False, is_admin=True),
        )
        with patch('apps.users.serializers.User.objects.filter') as user_filter:
            user_filter.return_value.first.return_value = None
            with patch(
                'apps.organizations.models.OrganizationInvitation.objects.get',
                return_value=invitation,
            ):
                serializer = RegisterSerializer()
                with self.assertRaises(ValidationError):
                    serializer.validate({
                        'email': 'invited@example.test',
                        'password': 'Temporary-Password-1!',
                        'password_confirm': 'Temporary-Password-1!',
                        'invitation_token': 'bearer-token',
                    })

    def test_registration_consumes_valid_invitation_with_expected_effects_offline(self):
        organization = Organization(id=uuid.uuid4(), name='Tenant')
        invitation = SimpleNamespace(
            email='invited@example.test',
            is_expired=False,
            status='pending',
            role='user',
            invited_by=None,
            organization=organization,
            accepted_at=None,
            save=Mock(),
        )

        with patch(
            'apps.organizations.models.OrganizationInvitation.objects.select_for_update'
        ) as select_for_update:
            select_for_update.return_value.get.return_value = invitation
            with patch(
                'apps.integration.models.SSOSecurityFence.objects.select_for_update'
            ) as fence_select_for_update:
                fence_select_for_update.return_value.get.return_value.enabled = True
                with patch(
                    'apps.users.serializers.transaction.atomic',
                    return_value=nullcontext(),
                ):
                    with patch(
                        'apps.organizations.invitation_authority.validate_invitation_authority'
                    ):
                        with patch('apps.users.serializers.User.save') as user_save:
                            with patch(
                                'apps.users.serializers.UserOrganization.objects.create'
                            ) as membership_create:
                                user = RegisterSerializer().create({
                                    'email': 'invited@example.test',
                                    'first_name': 'Invited',
                                    'last_name': 'User',
                                    'invitation_token': 'bearer-token',
                                    'password': 'Temporary-Password-1!',
                                })

        self.assertEqual(user.organization, organization)
        self.assertEqual(user.role, 'user')
        self.assertTrue(user.is_verified)
        user_save.assert_called_once()
        membership_create.assert_called_once_with(
            user=user,
            organization=organization,
            role='user',
            is_primary=True,
        )
        self.assertEqual(invitation.status, 'accepted')
        invitation.save.assert_called_once_with(
            update_fields=['status', 'accepted_at']
        )
