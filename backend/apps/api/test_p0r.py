"""P0R: real dispatch, serializers, signed tokens and adapters; simulated ORM only."""
from contextlib import ExitStack, nullcontext
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as NS, ModuleType
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch
import uuid

from django.contrib.auth.hashers import make_password
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.api import test_control_plane as previous
from apps.users.models import User, UserOrganization
from apps.users.serializers import RegisterSerializer
from apps.users.views import UserViewSet, LogoutView, RegisterView
from apps.organizations.models import Organization, OrganizationInvitation
from apps.organizations.views import OrganizationInvitationViewSet
from apps.integration.models import IntegrationAPIKey, SSOSecurityFence
from apps.integration import views as integration_views


class SessionAPITests(TestCase):
    setUp = previous.ControlPlaneTests.setUp
    members = previous.ControlPlaneTests.members
    user = previous.ControlPlaneTests.user
    call = previous.ControlPlaneTests.call

    def test_local_registry_revocation_reports_its_limit_and_keeps_owner_filter(self):
        from apps.users.models import UserSession
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.authentication import JWTAuthentication
        actor = self.user()
        access = AccessToken(); access['user_id'] = str(actor.pk)
        request = self.factory.post('/offline/', {}, format='json')
        force_authenticate(request, user=actor, token=access)
        with patch.object(UserSession.objects, 'filter') as records, \
             patch('apps.integration.session_lifecycle.revoke_for_user') as central:
            response = UserViewSet.as_view({'post': 'revoke_sessions'})(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['scope'], 'local_registry')
        self.assertFalse(response.data['access_tokens_revoked']); self.assertFalse(response.data['central_sessions_revoked'])
        records.assert_called_once_with(user=actor, is_active=True)
        records.return_value.exclude.assert_called_once_with(token_jti=access['jti'])
        records.return_value.exclude.return_value.update.assert_called_once_with(is_active=False)
        central.assert_not_called()
        # Characterize the remaining gap: a different signed local access token
        # still authenticates because JWTAuthentication does not read UserSession.
        other_access = AccessToken(); other_access['user_id'] = str(actor.pk)
        incoming = self.factory.get('/offline/', HTTP_AUTHORIZATION='Bearer ' + str(other_access))
        with patch.object(User.objects, 'get', return_value=actor):
            authenticated, _ = JWTAuthentication().authenticate(incoming)
        self.assertEqual(authenticated.pk, actor.pk)

    def test_central_revocation_dispatch_real_uuid_serializer_and_scope(self):
        actor = self.user(); sid = uuid.uuid4()
        with patch('apps.integration.session_lifecycle.revoke_for_user', return_value=1) as revoke:
            response = self.call(UserViewSet, 'revoke_sso_sessions', actor, {'session_id': str(sid)})
        self.assertEqual(response.status_code, 200)
        revoke.assert_called_once_with(actor=actor, session_id=sid)
        self.assertEqual(response.data, {'scope': 'central_sso', 'revoked': 1, 'local_sessions_revoked': False})

    def test_central_revoke_all_does_not_preserve_request_ids(self):
        with patch('apps.integration.session_lifecycle.revoke_for_user', return_value=2) as revoke:
            actor = self.user()
            response = self.call(UserViewSet, 'revoke_sso_sessions', actor)
        self.assertEqual(response.status_code, 200)
        revoke.assert_called_once_with(actor=actor)

    def test_central_revocation_invalid_fields_denied_before_service(self):
        for payload in ({'session_id': 'bad'}, {'session_id': None}, {'user_id': str(uuid.uuid4())},
                        {'current_token_jti': 'other'}, {'tenant_id': str(self.other.pk)}):
            with self.subTest(payload=payload), patch('apps.integration.session_lifecycle.revoke_for_user') as revoke:
                response = self.call(UserViewSet, 'revoke_sso_sessions', self.user(), payload)
            self.assertEqual(response.status_code, 400)
            revoke.assert_not_called()

    def test_central_revocation_nonhuman_inactive_anonymous_denied(self):
        inactive = self.user(); inactive.is_active = False
        for actor in (None, inactive, IntegrationAPIKey(id=1)):
            with self.subTest(actor=type(actor).__name__), patch('apps.integration.session_lifecycle.revoke_for_user') as revoke:
                self.assertIn(self.call(UserViewSet, 'revoke_sso_sessions', actor).status_code, (401, 403))
                revoke.assert_not_called()
        request = self.factory.post('/offline/', {}, format='json')
        force_authenticate(request, user=self.user(), token={'token_family': 'CENTRAL'})
        self.assertEqual(UserViewSet.as_view({'post': 'revoke_sso_sessions'})(request).status_code, 403)

    def test_central_revocation_persistence_failure_returns_no_success(self):
        from django.db import DatabaseError
        with patch('apps.integration.session_lifecycle.revoke_for_user', side_effect=DatabaseError('private')):
            response = self.call(UserViewSet, 'revoke_sso_sessions', self.user())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private', str(response.data))

    def test_logout_real_signed_refresh_idempotent_and_foreign_denied(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        actor = self.user(); token = RefreshToken(); token['user_id'] = str(actor.pk)
        raw = str(token); revoked = set()
        def blacklisted(**kw):
            return NS(exists=lambda: kw['token__jti'] in revoked)
        def blacklist(**kw):
            revoked.add(kw['token'].jti); return NS(), True
        with patch.object(BlacklistedToken.objects, 'filter', side_effect=blacklisted), \
             patch.object(OutstandingToken.objects, 'get_or_create', return_value=(NS(jti=token['jti']), True)), \
             patch.object(BlacklistedToken.objects, 'get_or_create', side_effect=blacklist), \
             patch('apps.users.views.log_logout_activity') as audit:
            for _ in range(2):
                request = self.factory.post('/offline/', {'refresh': raw}, format='json')
                force_authenticate(request, user=actor)
                self.assertEqual(LogoutView.as_view()(request).status_code, 200)
            request = self.factory.post('/offline/', {'refresh': raw}, format='json')
            force_authenticate(request, user=self.user())
            self.assertEqual(LogoutView.as_view()(request).status_code, 400)
            self.assertEqual(audit.call_count, 2)
        self.assertEqual(revoked, {token['jti']})

    def test_logout_rejects_signed_access_and_tampered_refresh(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        actor = self.user(); token = RefreshToken(); token['user_id'] = str(actor.pk)
        for raw in (str(token.access_token), str(token)[:-8] + 'tampered'):
            request = self.factory.post('/offline/', {'refresh': raw}, format='json')
            force_authenticate(request, user=actor)
            with patch.object(BlacklistedToken.objects, 'filter') as check, patch('apps.users.views.log_logout_activity') as audit:
                check.return_value.exists.return_value = False
                self.assertEqual(LogoutView.as_view()(request).status_code, 400)
                audit.assert_not_called()

    def test_logout_audit_failure_does_not_restore_blacklisted_refresh(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        actor = self.user(); token = RefreshToken(); token['user_id'] = str(actor.pk)
        request = self.factory.post('/offline/', {'refresh': str(token)}, format='json')
        force_authenticate(request, user=actor)
        with patch.object(RefreshToken, 'check_blacklist'), patch.object(RefreshToken, 'blacklist') as revoked, \
             patch('apps.users.views.log_logout_activity', side_effect=RuntimeError('audit unavailable')):
            with self.assertRaises(RuntimeError):
                LogoutView.as_view()(request)
            revoked.assert_called_once()


class InvitationLifecycleTests(TestCase):
    setUp = previous.ControlPlaneTests.setUp

    def members(self, **kw):
        query = previous.ControlPlaneTests.members(self, **kw)
        if kw.get('role') != self.member_role:
            query.exists.return_value = False
        return query
    user = previous.ControlPlaneTests.user
    call = previous.ControlPlaneTests.call

    def fixture(self):
        self.inviter = self.user('org_admin')
        self.invitation = OrganizationInvitation(organization=self.org, invited_by=self.inviter,
            email='invited@example.invalid', role='user', status='pending', token='synthetic-invitation',
            expires_at=timezone.now() + timezone.timedelta(days=1))
        self.payload = {'email': self.invitation.email, 'first_name': 'Invited', 'last_name': 'User',
            'password': 'Synthetic-invite-123!', 'password_confirm': 'Synthetic-invite-123!',
            'invitation_token': str(self.invitation.token)}
        stack = ExitStack(); self.addCleanup(stack.close)
        self.fence = stack.enter_context(patch.object(SSOSecurityFence.objects, 'select_for_update'))
        self.fence.return_value.get.return_value = NS(enabled=True)
        stack.enter_context(patch('apps.users.serializers.transaction.atomic', return_value=nullcontext()))
        self.lookup = stack.enter_context(patch.object(OrganizationInvitation.objects, 'get', return_value=self.invitation))
        locked = stack.enter_context(patch.object(OrganizationInvitation.objects, 'select_for_update'))
        locked.return_value.get.side_effect = lambda **kw: self.current_invitation(**kw)
        self.actor_lookup = stack.enter_context(patch.object(User.objects, 'get', side_effect=lambda **kw: self.current_inviter(**kw)))
        self.org_lookup = stack.enter_context(patch.object(Organization.objects, 'get', side_effect=lambda **kw: self.current_org(**kw)))
        existing = stack.enter_context(patch.object(User.objects, 'filter'))
        existing.return_value.first.return_value = None
        self.saved = stack.enter_context(patch.object(User, 'save'))
        self.created = stack.enter_context(patch.object(UserOrganization.objects, 'create'))
        self.invite_save = stack.enter_context(patch.object(self.invitation, 'save'))
        return stack

    def current_invitation(self, **kw):
        if self.invitation.status != kw['status']:
            raise OrganizationInvitation.DoesNotExist
        return self.invitation

    def current_inviter(self, **kw):
        self.assertEqual(kw, {'pk': self.inviter.pk, 'is_active': True})
        if not self.inviter.is_active:
            raise User.DoesNotExist
        return self.inviter

    def current_org(self, **kw):
        self.assertEqual(kw, {'pk': self.org.pk, 'status': 'active'})
        if self.org.status != 'active':
            raise Organization.DoesNotExist
        return self.org

    def consume(self):
        serializer = RegisterSerializer(data=copy.deepcopy(self.payload))
        serializer.is_valid(raise_exception=True)
        return serializer, serializer.save()

    def test_registration_consumes_live_invitation_with_real_serializer(self):
        self.fixture()
        _, user = self.consume()
        self.assertEqual((user.organization_id, user.role), (self.org.pk, 'user'))
        self.assertTrue(user.check_password(self.payload['password']))
        self.assertEqual(self.invitation.status, 'accepted')
        self.saved.assert_called_once()
        self.created.assert_called_once_with(user=user, organization=self.org, role='user', is_primary=True)
        self.invite_save.assert_called_once_with(update_fields=['status', 'accepted_at'])
        self.fence.return_value.get.assert_called_once_with(pk=1)

    def test_registration_dispatch_emits_signed_tokens_after_live_consumption(self):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        self.fixture()
        with patch.object(OutstandingToken.objects, 'create'):
            response = RegisterView.as_view()(self.factory.post('/offline/', self.payload, format='json'))
        self.assertEqual(response.status_code, 201, response.data)
        token = AccessToken(response.data['tokens']['access'])
        self.assertEqual(str(token['user_id']), response.data['user']['id'])
        self.assertEqual(self.created.call_args.kwargs['role'], 'user')
        self.assertEqual(self.invitation.status, 'accepted')

    def test_authority_removed_after_validation_is_denied_at_consumption(self):
        for mutation in ('inactive', 'membership', 'role', 'tenant', 'revoked', 'expired', 'missing', 'email', 'global_role', 'member_role', 'inviter_tenant'):
            with self.subTest(mutation=mutation), self.fixture():
                serializer = RegisterSerializer(data=copy.deepcopy(self.payload)); serializer.is_valid(raise_exception=True)
                if mutation == 'inactive': self.inviter.is_active = False
                elif mutation == 'membership': self.membership_active = False
                elif mutation == 'role': self.inviter.role = 'user'
                elif mutation == 'tenant': self.org.status = 'suspended'
                elif mutation == 'revoked': self.invitation.status = 'cancelled'
                elif mutation == 'expired': self.invitation.expires_at = timezone.now() - timezone.timedelta(seconds=1)
                elif mutation == 'missing': self.invitation.invited_by = None
                elif mutation == 'email': self.invitation.email = 'different@example.invalid'
                elif mutation == 'global_role': self.invitation.role = 'superadmin'
                elif mutation == 'member_role': self.member_role = 'viewer'
                elif mutation == 'inviter_tenant': self.inviter.organization = self.other
                with self.assertRaises(ValidationError): serializer.save()
                self.saved.assert_not_called(); self.created.assert_not_called(); self.invite_save.assert_not_called()
                self.membership_active = True; self.org.status = 'active'; self.member_role = 'org_admin'

    def test_platform_inviter_lost_permission_or_staff_denied_on_consume(self):
        for missing in ('staff', 'permission'):
            with self.subTest(missing=missing), self.fixture():
                self.inviter.role = 'admin'; self.inviter.is_staff = True
                serializer = RegisterSerializer(data=copy.deepcopy(self.payload)); serializer.is_valid(raise_exception=True)
                if missing == 'staff': self.inviter.is_staff = False
                else: self.inviter.has_perm.return_value = False
                with self.assertRaises(ValidationError): serializer.save()
                self.saved.assert_not_called()

    def test_invitee_cannot_supply_role_or_tenant(self):
        self.fixture()
        for extra in ({'role': 'superadmin'}, {'organization': str(self.other.pk)}, {'is_staff': True}):
            serializer = RegisterSerializer(data={**self.payload, **extra})
            self.assertFalse(serializer.is_valid())
        self.saved.assert_not_called()

    def test_disabled_fence_and_replay_cannot_consume(self):
        self.fixture()
        serializer = RegisterSerializer(data=copy.deepcopy(self.payload)); serializer.is_valid(raise_exception=True)
        self.fence.return_value.get.return_value.enabled = False
        with self.assertRaises(ValidationError): serializer.save()
        self.saved.assert_not_called()
        self.fence.return_value.get.return_value.enabled = True
        self.consume()
        with self.assertRaises(ValidationError): self.consume()
        self.saved.assert_called_once()

    def test_preview_revalidates_authority_without_consuming(self):
        self.fixture()
        response = OrganizationInvitationViewSet.as_view({'post': 'accept'}, permission_classes=[])(
            self.factory.post('/offline/', {'token': str(self.invitation.token)}, format='json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['role'], 'user')
        self.inviter.is_active = False
        response = OrganizationInvitationViewSet.as_view({'post': 'accept'}, permission_classes=[])(
            self.factory.post('/offline/', {'token': str(self.invitation.token)}, format='json'))
        self.assertEqual(response.status_code, 400)
        self.created.assert_not_called(); self.invite_save.assert_not_called()


class ServiceGrantTests(TestCase):
    setUp = previous.ServiceDataTests.setUp
    call = previous.ServiceDataTests.call

    def test_unknown_or_incomplete_grant_denies_all_operations(self):
        original = copy.deepcopy(self.grant)
        mutations = [{'operations': ['get_organization', 'unknown']}, {'operations': ['*', 'get_organization']},
                     {'operations': ['get_organization']*2}, {'product_codes': []}, {'product_codes': ['UNKNOWN']},
                     {'tenant_ids': []}, {'tenant_ids': ['*']}, {'tenant_ids': [True]}, {'extra': True}]
        for mutation in mutations:
            self.grant = {**original, **mutation}
            with self.subTest(mutation=mutation), patch.object(Organization.objects, 'get', return_value=self.org) as lookup:
                self.assertIn(self.call(integration_views.get_organization, org_id=self.org.pk).status_code, (400, 403))
                lookup.assert_not_called()

    def test_revoked_timestamp_unsaved_or_wrong_format_principal_denied(self):
        for field, value in (('revoked_at', timezone.now()), ('id', None), ('credential_format', 'legacy_plaintext'), ('status', 'rotated')):
            with self.subTest(field=field), patch.object(self.principal, field, value), patch.object(Organization.objects, 'get', return_value=self.org) as lookup:
                self.assertEqual(self.call(integration_views.get_organization, org_id=self.org.pk).status_code, 403)
                lookup.assert_not_called()

    def test_modules_exclude_foreign_products_and_unmapped_owner_exemptions(self):
        self.grant['operations'].append('get_organization_modules')
        self.org.metadata = {'owner_organization': True}
        with patch.object(Organization.objects, 'get', return_value=self.org), \
             patch.object(integration_views, '_active_product_entitlements') as entitlements, \
             patch.object(integration_views, '_product_system_aliases', return_value=set()):
            entitlements.return_value.filter.return_value = [NS(product=NS(code='ISO_SMART', name='ISO'),
                access_allowed=True, enabled=True, status='active', subscription=None)]
            response = self.call(integration_views.get_organization_modules, org_id=self.org.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m['code'] for m in json.loads(response.content)['modules']], ['ISO_SMART'])
        entitlements.return_value.filter.assert_called_once_with(product__code__in=['ISO_SMART'])

    def test_users_and_lookup_return_only_granted_tenant_memberships(self):
        self.grant['operations'].append('get_organization_users')
        user = User(email='member@example.invalid')
        member = UserOrganization(user=user, organization=self.org, role='viewer')
        with patch.object(Organization.objects, 'get', return_value=self.org), \
             patch.object(UserOrganization.objects, 'filter') as members:
            members.return_value.select_related.return_value = [member]
            response = self.call(integration_views.get_organization_users, org_id=self.org.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['users'][0]['role'], 'viewer')
        with patch.object(User.objects, 'get', return_value=user), patch.object(UserOrganization.objects, 'filter') as members:
            scoped = members.return_value.select_related.return_value.filter.return_value
            scoped.exists.return_value = True; scoped.__iter__.return_value = iter([member])
            response = self.call(integration_views.get_user_by_id, {'user_id': str(user.pk), 'organization_id': str(self.org.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m['id'] for m in json.loads(response.content)['organizations']], [str(self.org.pk)])
        members.return_value.select_related.return_value.filter.assert_called_once_with(organization_id=str(self.org.pk))


class ConsumerGrantCompatibilityTests(TestCase):
    """Execute both actual clients through their real HTTP adapter into central handlers."""
    def setUp(self):
        from django.urls import resolve
        resolve('/api/integration/organizations/')
        self.factory = APIRequestFactory()
        self.org = Organization(name='Tenant', code='TENANT', status='active', created_at=timezone.now())
        self.user = User(email='member@example.invalid', organization=self.org)
        self.member = UserOrganization(user=self.user, organization=self.org, role='viewer')
        self.principal = IntegrationAPIKey(id=87, name='offline-only', credential_id='c'*32,
            credential_format='hashed_v1', status='active', is_active=True)
        self.raw = 'iak_' + self.principal.credential_id + '.' + 'S'*43
        self.principal.credential_hash = make_password(self.raw)
        operations = ['list_organizations', 'get_organization', 'get_organization_users',
                      'get_organization_modules', 'get_organization_products',
                      'validate_organization_product_access', 'get_user_by_id']
        self.grant = {'operations': operations, 'tenant_ids': [str(self.org.pk)], 'product_codes': ['ISO_SMART']}
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        def p(target, name, **kw): return self.stack.enter_context(patch.object(target, name, **kw))
        p(self.principal, 'save')
        self.key_lookup = p(IntegrationAPIKey.objects, 'filter', side_effect=self.keys)
        p(Organization.objects, 'get', side_effect=self.tenant)
        p(Organization.objects, 'filter', return_value=[self.org])
        p(User.objects, 'get', return_value=self.user)
        p(UserOrganization.objects, 'filter', side_effect=self.members)
        from apps.products.models import ProductSystem, OrganizationProductEntitlement
        self.product = ProductSystem(code='ISO_SMART', name='ISO Smart', slug='iso-smart', status='active', billing_enabled=False)
        self.entitlement = OrganizationProductEntitlement(organization=self.org, product=self.product, status='active', enabled=True)
        p(ProductSystem.objects, 'filter').return_value.first.return_value = self.product
        p(OrganizationProductEntitlement.objects, 'filter').return_value.select_related.return_value.first.return_value = self.entitlement
        p(integration_views, '_active_product_entitlements').return_value.filter.return_value = [self.entitlement]
        p(integration_views, '_product_system_aliases', return_value={'iso_smart'})
        p(integration_views, '_audit_product_access_validation')
        self.stack.enter_context(override_settings(INTEGRATION_API_KEYS={},
            INTEGRATION_API_GRANTS={self.principal.credential_id: self.grant},
            ADMIN_APPS_INTEGRATION={'BASE_URL': 'https://offline.invalid/api/integration', 'API_KEY': self.raw, 'ALLOW_LOCAL_FALLBACK': True},
            ALLOW_LOCAL_AUTH_FALLBACK=True, IS_PRODUCTION=False))

    def keys(self, **kw):
        query = MagicMock()
        query.first.return_value = self.principal if kw == {'credential_id': self.principal.credential_id} else None
        query.iterator.return_value = iter([]); query.values_list.return_value = []
        return query

    def tenant(self, **kw):
        if str(kw['id']) != str(self.org.pk) or self.org.status != kw['status']:
            raise Organization.DoesNotExist
        return self.org

    def members(self, **kw):
        query = MagicMock()
        query.select_related.return_value = query; query.filter.return_value = query
        query.exists.return_value = True; query.__iter__.side_effect = lambda: iter([self.member])
        return query

    def bridge(self, method, url, **kw):
        from urllib.parse import urlsplit
        from django.urls import resolve
        import requests
        path = urlsplit(url).path
        request = getattr(self.factory, method)(path, kw.get('json', {}), format='json', HTTP_X_API_KEY=kw['headers']['X-API-Key'])
        match = resolve(path)
        central = match.func(request, **match.kwargs)
        response = requests.Response(); response.status_code = central.status_code
        response.url = url; response._content = central.content
        return response

    def adapters(self):
        root = Path(__file__).resolve().parents[4]
        for repo in ('isosmart', 'ISO_Smart_MedSupplier'):
            spec = importlib.util.spec_from_file_location('offline_client_' + repo, root / repo / 'backend/integration/client.py')
            module = importlib.util.module_from_spec(spec)
            core = ModuleType('core.models'); core.Organization = None
            with patch.dict('sys.modules', {'core.models': core}): spec.loader.exec_module(module)
            client = module.AdminAppsClient()
            self.product.code = 'ISO_SMART' if repo == 'isosmart' else 'MEDSUPPLIER'
            self.grant['product_codes'] = [self.product.code]
            yield repo, module, client

    def test_both_adapters_all_seven_legacy_handlers_with_authenticated_credential(self):
        from apps.integration.api_authorization import OPERATIONS
        seen = set()
        for repo, module, client in self.adapters():
            with self.subTest(repo=repo), patch.object(module.requests, 'get', side_effect=lambda url, **kw: self.bridge('get', url, **kw)), \
                 patch.object(module.requests, 'post', side_effect=lambda url, **kw: self.bridge('post', url, **kw)), \
                 patch.object(module.cache, 'get', side_effect=AssertionError('Stale authority cache consulted')), \
                 patch.object(client, '_resolve_adminapps_org_id', return_value=str(self.org.pk)):
                outputs = {
                    'list_organizations': client.get_organizations(),
                    'get_organization': client.get_organization(str(self.org.pk)),
                    'get_organization_users': client.get_organization_users(str(self.org.pk)),
                    'get_organization_modules': client.get_organization_modules(str(self.org.pk)),
                    'get_organization_products': client._make_request('GET', f'/organizations/{self.org.pk}/products/'),
                    'validate_organization_product_access': client.validate_product_access(str(self.org.pk), self.product.code),
                    'get_user_by_id': client.get_user(str(self.user.pk), str(self.org.pk)),
                }
                for operation, output in outputs.items():
                    self.assertNotIn('error', output, (repo, operation, output)); seen.add(operation)
                self.assertTrue(outputs['validate_organization_product_access']['allowed'])
                self.assertEqual(outputs['get_user_by_id']['organizations'][0]['id'], str(self.org.pk))
                self.assertEqual(outputs['get_organization_modules']['modules'][0]['code'], self.product.code)
                self.assertEqual(outputs['get_organization_products']['products'][0]['code'], self.product.code)
        self.assertEqual(seen, OPERATIONS)
        self.assertGreater(self.key_lookup.call_count, 0)

    def test_both_adapters_reject_revocation_grant_removal_and_product_tenant_escape(self):
        for repo, module, client in self.adapters():
            with self.subTest(repo=repo), patch.object(module.requests, 'get', side_effect=lambda url, **kw: self.bridge('get', url, **kw)), \
                 patch.object(module.cache, 'get', side_effect=AssertionError('Stale authority cache consulted')), \
                 patch.object(client, '_resolve_adminapps_org_id', side_effect=lambda value: value), \
                 patch.object(module, 'Organization', Mock()), \
                 patch.object(client, '_get_organization_local', side_effect=AssertionError('Authorization fallback')), \
                 patch.object(client, '_validate_product_access_local', side_effect=AssertionError('Authorization fallback')), \
                 patch.object(client, '_get_organization_users_local', side_effect=AssertionError('Authorization fallback')), \
                 patch.object(client, '_get_organization_modules_local', side_effect=AssertionError('Authorization fallback')):
                self.assertTrue(client._local_fallback_allowed())
                self.assertNotIn('error', client.get_organization(str(self.org.pk)))
                self.principal.status = 'revoked'
                result = client.get_organization(str(self.org.pk))
                self.assertTrue(result['authorization_denied']); self.assertFalse(result['allowed'])
                self.principal.status = 'active'
                operations = self.grant['operations']; self.grant['operations'] = ['get_user_by_id']
                self.assertTrue(client.get_organization(str(self.org.pk))['authorization_denied'])
                self.assertTrue(client.get_organization_users(str(self.org.pk))['authorization_denied'])
                self.assertTrue(client.get_organization_modules(str(self.org.pk))['authorization_denied'])
                self.grant['operations'] = operations
                self.assertTrue(client.get_organization(str(uuid.uuid4()))['authorization_denied'])
                foreign_product = 'MEDSUPPLIER' if self.product.code == 'ISO_SMART' else 'ISO_SMART'
                result = client.validate_product_access(str(self.org.pk), foreign_product, allow_local_fallback=True)
                self.assertFalse(result['allowed']); self.assertTrue(result['authorization_denied'])
                with override_settings(IS_PRODUCTION=True), patch.object(module.requests, 'get', side_effect=module.requests.exceptions.Timeout):
                    self.assertFalse(client._local_fallback_allowed())
                    result = client.get_organization(str(self.org.pk))
                    self.assertEqual(result['fallback'], 'disabled')

    def test_both_module_helpers_reject_authorization_denial_even_with_module_payload(self):
        for repo, module, client in self.adapters():
            with self.subTest(repo=repo), patch.object(client, 'get_organization_modules', return_value={
                    'authorization_denied': True, 'allowed': False,
                    'modules': [{'code': self.product.code, 'enabled': True}]}):
                self.assertFalse(client.is_module_enabled(str(self.org.pk), self.product.code))

    def test_authenticated_credential_cannot_borrow_grant_or_ssoclient(self):
        from apps.integration.models import SSOClient
        self.grant['operations'] = ['get_organization']
        request = self.factory.get('/offline/', HTTP_X_API_KEY=self.raw.replace('.S', '.X', 1))
        with patch.object(SSOClient.objects, 'select_related', side_effect=AssertionError('SSO grant inference')):
            response = integration_views.get_organization(request, org_id=self.org.pk)
            self.assertEqual(response.status_code, 401)
            request = self.factory.get('/offline/', HTTP_X_API_KEY=self.raw)
            with override_settings(INTEGRATION_API_GRANTS={'different-credential': self.grant}):
                response = integration_views.get_organization(request, org_id=self.org.pk)
            self.assertEqual(response.status_code, 403)


class FunctionalP0Tests(TestCase):
    setUp = previous.ControlPlaneTests.setUp
    members = previous.ControlPlaneTests.members
    user = previous.ControlPlaneTests.user
    call = previous.ControlPlaneTests.call
    resolved = previous.ControlPlaneTests.resolved

    def test_subscription_change_plan_effect_and_missing_plan_deny(self):
        from apps.subscriptions.models import Plan, Subscription
        from apps.subscriptions.views import SubscriptionViewSet
        old = Plan(code='old', price='10.00'); new = Plan(code='new', name='New', price='25.00')
        subscription = Subscription(plan=old, amount='10.00', status='active')
        other = Subscription(plan=old, amount='10.00', status='active')
        actor = self.user('admin', is_staff=True)
        with self.resolved(SubscriptionViewSet, subscription), patch.object(subscription, 'save') as save, \
             patch.object(Plan.objects, 'get', return_value=new) as lookup:
            response = self.call(SubscriptionViewSet, 'change_plan', actor, {'plan_id': str(new.pk)}, pk=subscription.pk)
        self.assertEqual(response.status_code, 200)
        lookup.assert_called_once_with(pk=new.pk, is_active=True)
        self.assertEqual((subscription.plan, subscription.amount), (new, new.price)); save.assert_called_once()
        self.assertEqual((other.plan, other.amount), (old, '10.00'))
        with self.resolved(SubscriptionViewSet, subscription), patch.object(subscription, 'save') as save, \
             patch.object(Plan.objects, 'get', side_effect=Plan.DoesNotExist):
            response = self.call(SubscriptionViewSet, 'change_plan', actor, {'plan_id': str(uuid.uuid4())}, pk=subscription.pk)
        self.assertEqual(response.status_code, 404); save.assert_not_called()

    def test_subscription_activation_and_cancellation_execute_model_effects(self):
        from apps.subscriptions.models import Plan, Subscription
        from apps.subscriptions.views import SubscriptionViewSet
        subscription = Subscription(plan=Plan(code='existing', billing_cycle='monthly'), status='past_due')
        actor = self.user('admin', is_staff=True)
        with self.resolved(SubscriptionViewSet, subscription), patch.object(subscription, 'save') as save:
            response = self.call(SubscriptionViewSet, 'activate', actor, pk=subscription.pk)
            self.assertEqual(response.status_code, 200); self.assertEqual(subscription.status, 'active')
            self.assertGreater(subscription.current_period_end, subscription.current_period_start)
            response = self.call(SubscriptionViewSet, 'cancel', actor, pk=subscription.pk)
            self.assertEqual(response.status_code, 200); self.assertEqual(subscription.status, 'cancelled')
            self.assertIsNotNone(subscription.cancelled_at); self.assertEqual(save.call_count, 2)

    def test_invoice_payment_executes_subscription_activation(self):
        from apps.subscriptions.models import Plan, Subscription, Invoice
        from apps.subscriptions.views import InvoiceViewSet
        subscription = Subscription(plan=Plan(code='existing', billing_cycle='monthly'), status='past_due')
        invoice = Invoice(organization=self.org, subscription=subscription, status='pending')
        with self.resolved(InvoiceViewSet, invoice), patch.object(invoice, 'save') as save, patch.object(subscription, 'save') as activated:
            response = self.call(InvoiceViewSet, 'mark_paid', self.user('admin', is_staff=True), {'payment_reference': 'offline-reference'}, pk=invoice.pk)
        self.assertEqual(response.status_code, 200); self.assertEqual(invoice.status, 'paid')
        self.assertEqual(invoice.payment_reference, 'offline-reference'); self.assertIsNotNone(invoice.paid_at)
        self.assertEqual(subscription.status, 'active'); save.assert_called_once(); activated.assert_called_once()

    def test_entitlement_restrictive_patch_real_serializer_and_audit(self):
        from apps.products.models import ProductSystem, OrganizationProductEntitlement, ProductEntitlementAuditLog
        from apps.products.views import OrganizationProductEntitlementViewSet
        from apps.integration.authorization_contract import CATALOG
        product = ProductSystem(code='ISO_SMART', billing_enabled=False)
        entitlement = OrganizationProductEntitlement(organization=self.org, product=product, enabled=True, status='active', scopes=[next(iter(CATALOG['ISO_SMART']))])
        with self.resolved(OrganizationProductEntitlementViewSet, entitlement), patch.object(entitlement, 'save') as save, \
             patch.object(ProductEntitlementAuditLog.objects, 'create') as audit:
            response = self.call(OrganizationProductEntitlementViewSet, 'partial_update', self.user('admin', is_staff=True),
                                 {'enabled': False, 'scopes': []}, method='patch', pk=entitlement.pk)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(entitlement.enabled); self.assertEqual(entitlement.scopes, [])
        self.assertEqual(entitlement.organization_id, self.org.pk); save.assert_called_once()
        self.assertEqual(audit.call_args.kwargs['action'], 'disabled')
        self.assertEqual(audit.call_args.kwargs['previous_state']['enabled'], True)
        self.assertEqual(audit.call_args.kwargs['new_state']['enabled'], False)

    def test_entitlement_billing_activation_and_unknown_scope_denied(self):
        from apps.products.models import ProductSystem, OrganizationProductEntitlement, ProductEntitlementAuditLog
        from apps.products.views import OrganizationProductEntitlementViewSet
        entitlement = OrganizationProductEntitlement(organization=self.org, product=ProductSystem(code='ISO_SMART', billing_enabled=True), enabled=False, status='suspended')
        with self.resolved(OrganizationProductEntitlementViewSet, entitlement), patch.object(entitlement, 'save') as save, \
             patch.object(ProductEntitlementAuditLog.objects, 'create') as audit:
            actor = self.user('admin', is_staff=True)
            response = self.call(OrganizationProductEntitlementViewSet, 'toggle', actor, {'action': 'enable'}, pk=entitlement.pk)
            self.assertEqual(response.status_code, 400)
            for payload in ({'scopes': ['*']}, {'scopes': ['MEDSUPPLIER:resources.resource:read']}, {'status': 'invented'}):
                response = self.call(OrganizationProductEntitlementViewSet, 'partial_update', actor, payload, method='patch', pk=entitlement.pk)
                self.assertEqual(response.status_code, 400)
        save.assert_not_called(); audit.assert_not_called()

    def test_membership_deactivation_then_foreign_reference_denied(self):
        from apps.users.views import UserOrganizationViewSet
        target = self.user(); member = UserOrganization(organization=self.org, user=target, role='viewer', is_active=True)
        actor = self.user('org_admin')
        with self.resolved(UserOrganizationViewSet, member), patch.object(member, 'save') as save:
            response = self.call(UserOrganizationViewSet, 'partial_update', actor, {'is_active': False}, method='patch', pk=member.pk)
        self.assertEqual(response.status_code, 200, response.data); self.assertFalse(member.is_active); save.assert_called_once()
        with self.resolved(UserOrganizationViewSet, member), patch.object(member, 'save') as save, \
             patch('django.db.models.query.QuerySet.get', return_value=self.other):
            response = self.call(UserOrganizationViewSet, 'partial_update', actor, {'organization': str(self.other.pk)}, method='patch', pk=member.pk)
        self.assertEqual(response.status_code, 400); save.assert_not_called(); self.assertEqual(member.organization_id, self.org.pk)

    def test_user_disable_effect_and_self_disable_denied(self):
        target = self.user(); actor = self.user('org_admin')
        with self.resolved(UserViewSet, target), patch.object(target, 'save') as save:
            response = self.call(UserViewSet, 'deactivate', actor, pk=target.pk)
        self.assertEqual(response.status_code, 200); self.assertFalse(target.is_active); save.assert_called_once()
        with self.resolved(UserViewSet, actor), patch.object(actor, 'save') as save:
            response = self.call(UserViewSet, 'deactivate', actor, pk=actor.pk)
        self.assertEqual(response.status_code, 400); save.assert_not_called()

    def test_user_password_change_real_serializer_hash_and_audit(self):
        from apps.users.models import UserActivityLog
        actor = self.user(); actor.set_password('Synthetic-old-123!')
        payload = {'current_password': 'Synthetic-old-123!', 'new_password': 'Synthetic-new-456!', 'new_password_confirm': 'Synthetic-new-456!'}
        with patch.object(actor, 'save') as save, patch.object(UserActivityLog.objects, 'create') as audit:
            response = self.call(UserViewSet, 'change_password', actor, payload)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(actor.check_password(payload['new_password'])); self.assertFalse(actor.must_change_password)
        save.assert_called_once(); audit.assert_called_once()
        with patch.object(actor, 'save') as save:
            response = self.call(UserViewSet, 'change_password', actor, payload)
        self.assertEqual(response.status_code, 400); save.assert_not_called()

    def test_tenant_suspend_is_idempotent_and_emits_one_event(self):
        from apps.organizations.views import OrganizationViewSet
        with self.resolved(OrganizationViewSet, self.org), patch.object(self.org, 'save') as save, \
             patch('apps.organizations.views.transaction.atomic', return_value=nullcontext()), \
             patch.object(Organization.objects, 'select_for_update') as locked, \
             patch('apps.organizations.tenant_events.record_tenant_event') as event:
            locked.return_value.get.return_value = self.org
            for _ in range(2):
                response = self.call(OrganizationViewSet, 'suspend', self.user('superadmin', is_staff=True), pk=self.org.pk)
                self.assertEqual(response.status_code, 200)
        self.assertEqual(self.org.status, 'suspended'); self.assertEqual(self.other.status, 'active')
        save.assert_called_once(); event.assert_called_once()

    def test_tenant_readiness_and_backoffice_denial_preserve_missing_permissions(self):
        from apps.api.views import FeatureFlagsView
        from apps.organizations.models import OrganizationFeatureFlag
        actor = self.user('admin', is_staff=True); actor.has_perm.return_value = False
        request = self.factory.get('/offline/'); force_authenticate(request, user=actor)
        with patch.object(OrganizationFeatureFlag.objects, 'resolve_for_organization') as service:
            response = FeatureFlagsView.as_view()(request)
        self.assertEqual(response.status_code, 403); service.assert_not_called()
