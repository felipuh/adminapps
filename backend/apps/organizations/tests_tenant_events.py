"""Native producer and cross-repository tenant contract tests."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Organization, TenantIntegrationOutbox
from .serializers import OrganizationCreateSerializer, OrganizationUpdateSerializer


class TenantEventProductionTests(TestCase):
    def test_native_create_and_update_commit_versioned_outbox(self):
        organization = OrganizationCreateSerializer().create({
            'name': 'Example Quality', 'email': 'owner@example.test',
        })
        created = TenantIntegrationOutbox.objects.get(organization=organization, source_version=1)
        self.assertEqual(created.status, 'pending')
        self.assertEqual(created.envelope['event_type'], 'tenant.provisioned')
        self.assertEqual(created.envelope['adminapps_tenant_id'], str(organization.id))
        self.assertEqual(created.envelope['aggregate_id'], str(organization.id))
        self.assertEqual(created.envelope['schema_version'], 1)
        self.assertEqual(created.envelope['payload']['adminapps_status'], 'trial')
        self.assertEqual(created.envelope['payload']['lifecycle_status'], 'active')

        OrganizationUpdateSerializer().update(organization, {'name': 'Example Quality 2'})
        updated = TenantIntegrationOutbox.objects.get(organization=organization, source_version=2)
        self.assertEqual(updated.envelope['event_type'], 'tenant.updated')
        self.assertEqual(updated.envelope['payload']['display_name'], 'Example Quality 2')
        self.assertNotEqual(created.id, updated.id)
        OrganizationUpdateSerializer().update(organization, {'name': 'Example Quality 2'})
        self.assertEqual(TenantIntegrationOutbox.objects.filter(organization=organization).count(), 2)

    def test_creation_rollback_removes_event_and_customer(self):
        from django.db import transaction
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                OrganizationCreateSerializer().create({
                    'name': 'Rolled Back', 'email': 'rollback@example.test',
                })
                raise RuntimeError('rollback')
        self.assertFalse(Organization.objects.filter(email='rollback@example.test').exists())
        self.assertFalse(TenantIntegrationOutbox.objects.exists())

    def test_produced_envelope_is_accepted_by_iso_smart_without_translation(self):
        contract_file = (Path(__file__).resolve().parents[4] / 'isosmart' / 'backend' /
                         'foundation' / 'projection_contract.py')
        spec = importlib.util.spec_from_file_location('iso_smart_projection_contract_test', contract_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        organization = OrganizationCreateSerializer().create({
            'name': 'Contract Tenant', 'email': 'contract@example.test',
        })
        event = TenantIntegrationOutbox.objects.get(organization=organization).envelope
        validated = module.validate_projection_event(event)
        self.assertEqual(validated.adminapps_tenant_id, organization.id)
        self.assertEqual(validated.source_version, 1)
        self.assertEqual(validated.payload['adminapps_status'], 'trial')

    @patch('apps.organizations.management.commands.deliver_tenant_events.urlopen')
    @patch.dict('os.environ', {'ISO_SMART_TENANT_EVENT_URL': 'https://iso.example.test/api/integration/adminapps/tenant-events/',
                               'ISO_SMART_TENANT_EVENT_KEY': 'test-key'})
    def test_dispatch_reuses_persisted_event_and_authenticates(self, urlopen):
        from django.core.management import call_command
        from unittest.mock import MagicMock
        response = MagicMock()
        response.status = 201
        urlopen.return_value.__enter__.return_value = response
        organization = OrganizationCreateSerializer().create({
            'name': 'Delivery Tenant', 'email': 'delivery@example.test',
        })
        original = TenantIntegrationOutbox.objects.get(organization=organization)
        call_command('deliver_tenant_events', limit=1)
        delivered = TenantIntegrationOutbox.objects.get(pk=original.pk)
        self.assertEqual(delivered.status, 'delivered')
        self.assertEqual(delivered.envelope, original.envelope)
        self.assertEqual(urlopen.call_args.args[0].get_header('X-api-key'), 'test-key')


class NativeProvisioningAuthorizationTests(APITestCase):
    def test_only_superadmin_can_provision_and_event_records_actor(self):
        user = User.objects.create_user(email='reader@example.test', password='test-password', role='user')
        self.client.force_authenticate(user=user)
        denied = self.client.post('/api/organizations/',
                                  {'name': 'Denied Tenant', 'email': 'denied@example.test'})
        self.assertEqual(denied.status_code, 403)
        self.assertFalse(TenantIntegrationOutbox.objects.exists())
        owner = User.objects.create_superuser(email='owner@example.test', password='test-password')
        self.client.force_authenticate(user=owner)
        accepted = self.client.post('/api/organizations/',
                                    {'name': 'Accepted Tenant', 'email': 'accepted@example.test'})
        self.assertEqual(accepted.status_code, 201)
        organization = Organization.objects.get(email='accepted@example.test')
        self.assertEqual(str(accepted.data['id']), str(organization.id))
        event = TenantIntegrationOutbox.objects.get(organization=organization)
        self.assertEqual(event.envelope['actor_id'], str(owner.id))
