from decimal import Decimal
from uuid import uuid4

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.integration.models import AIUsageProjection, IntegrationAPIKey
from apps.organizations.models import Organization
from apps.users.models import User


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AIUsageIntegrationTests(APITestCase):
    def setUp(self):
        self.key = 'synthetic-ai-usage-key'
        IntegrationAPIKey.objects.create(name='isosmart-usage', key=self.key, is_active=True)
        self.org = Organization.objects.create(code='AI-USAGE', name='AI Usage Tenant', email='ai-usage@example.test', status='active')

    def payload(self):
        return {
            'usage_event_id': str(uuid4()), 'usage_record_id': str(uuid4()), 'adminapps_tenant_id': str(self.org.id),
            'execution_id': str(uuid4()), 'correlation_id': str(uuid4()), 'product_identifier': 'iso-smart',
            'agent_name': 'value-discovery', 'capability_name': 'organizational_profile',
            'provider': 'openai-compatible-chat-completions', 'model_identifier': 'gpt-4o-mini',
            'attempted_at': timezone.now().isoformat(), 'attempt_status': 'completed', 'usage_status': 'reported',
            'input_tokens': 101, 'output_tokens': 31, 'total_tokens': 132, 'cost_status': 'estimated',
            'estimated_provider_cost': '0.0001230000', 'currency': 'USD',
        }

    def test_ingestion_is_authoritative_tenant_scoped_and_replay_safe(self):
        payload = self.payload()
        first = self.client.post('/api/integration/ai-usage/', payload, format='json', HTTP_X_API_KEY=self.key)
        second = self.client.post('/api/integration/ai-usage/', payload, format='json', HTTP_X_API_KEY=self.key)
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()['replay'])
        record = AIUsageProjection.objects.get()
        self.assertEqual(record.organization_id, self.org.id)
        self.assertEqual(record.estimated_provider_cost, Decimal('0.0001230000'))

    def test_mismatched_token_total_and_unknown_tenant_are_rejected(self):
        payload = self.payload(); payload['total_tokens'] = 1
        self.assertEqual(self.client.post('/api/integration/ai-usage/', payload, format='json', HTTP_X_API_KEY=self.key).status_code, 400)
        payload = self.payload(); payload['adminapps_tenant_id'] = str(uuid4())
        self.assertEqual(self.client.post('/api/integration/ai-usage/', payload, format='json', HTTP_X_API_KEY=self.key).status_code, 404)

    def test_conflicting_replay_and_wrong_producer_are_rejected(self):
        payload = self.payload()
        self.assertEqual(self.client.post('/api/integration/ai-usage/', payload, format='json', HTTP_X_API_KEY=self.key).status_code, 201)
        conflicting = {**payload, 'total_tokens': 133, 'output_tokens': 32}
        self.assertEqual(self.client.post('/api/integration/ai-usage/', conflicting, format='json', HTTP_X_API_KEY=self.key).status_code, 409)
        wrong_key = 'another-service-key'
        IntegrationAPIKey.objects.create(name='unrelated-service', key=wrong_key, is_active=True)
        self.assertEqual(self.client.post('/api/integration/ai-usage/', self.payload(), format='json', HTTP_X_API_KEY=wrong_key).status_code, 403)

    def test_administrative_dashboard_denies_non_admin_and_aggregates_for_admin(self):
        payload = self.payload()
        self.client.post('/api/integration/ai-usage/', payload, format='json', HTTP_X_API_KEY=self.key)
        viewer = User.objects.create_user(email='viewer@example.test', password='test', first_name='View', last_name='Only', organization=self.org, role='viewer')
        self.client.force_authenticate(viewer)
        self.assertEqual(self.client.get('/api/billing/ai-usage/').status_code, 403)
        admin = User.objects.create_user(email='admin@example.test', password='test', first_name='Admin', last_name='User', organization=self.org, role='admin')
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get('/api/billing/ai-usage/').status_code, 403)
        admin = User.objects.create_user(email='superadmin@example.test', password='test', first_name='Super', last_name='Admin', organization=self.org, role='superadmin')
        self.client.force_authenticate(admin)
        response = self.client.get('/api/billing/ai-usage/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['overview']['total_tokens'], 132)
        self.assertEqual(str(response.data['results'][0]['organization_id']), str(self.org.id))

    def test_unpriced_usage_remains_null_and_is_counted_separately(self):
        payload = self.payload()
        payload.update({
            'usage_event_id': str(uuid4()), 'usage_record_id': str(uuid4()),
            'usage_status': 'unknown', 'input_tokens': None, 'output_tokens': None,
            'total_tokens': None, 'cost_status': 'unpriced',
            'estimated_provider_cost': None, 'currency': None,
        })
        self.assertEqual(self.client.post('/api/integration/ai-usage/', payload, format='json', HTTP_X_API_KEY=self.key).status_code, 201)
        admin = User.objects.create_user(email='cost-admin@example.test', password='test', first_name='Cost', last_name='Admin', organization=self.org, role='superadmin')
        self.client.force_authenticate(admin)
        response = self.client.get('/api/billing/ai-usage/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['overview']['unpriced_cost'], 1)
        self.assertEqual(response.data['overview']['unknown_usage'], 1)
        self.assertEqual(AIUsageProjection.objects.get().estimated_provider_cost, None)

    def test_tenant_admin_cannot_read_other_tenant_usage(self):
        other = Organization.objects.create(code='OTHER-AI-USAGE', name='Other Tenant', email='other-ai@example.test', status='active')
        payload = self.payload()
        payload['adminapps_tenant_id'] = str(other.id)
        self.assertEqual(self.client.post('/api/integration/ai-usage/', payload, format='json', HTTP_X_API_KEY=self.key).status_code, 201)
        tenant_admin = User.objects.create_user(email='tenant-admin@example.test', password='test', first_name='Tenant', last_name='Admin', organization=self.org, role='admin')
        self.client.force_authenticate(tenant_admin)
        self.assertEqual(self.client.get('/api/billing/ai-usage/').status_code, 403)
        self.assertEqual(self.client.get(f'/api/billing/ai-usage/?tenant={other.id}').status_code, 403)
