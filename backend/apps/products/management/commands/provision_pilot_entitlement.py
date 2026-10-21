import json
import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import Organization
from apps.products.models import (
    OrganizationProductEntitlement,
    ProductEntitlementAuditLog,
    ProductSystem,
)
from apps.subscriptions.models import Plan, Subscription


class Command(BaseCommand):
    help = 'Idempotently provision a pilot product entitlement for one organization.'

    def add_arguments(self, parser):
        parser.add_argument('--organization', required=True, help='Organization UUID, code, or exact name.')
        parser.add_argument('--product', required=True, help='ProductSystem code, for example ISO_SMART.')
        parser.add_argument('--plan', default='pilot', help='Plan code or "pilot" to use <PRODUCT>_PILOT.')
        parser.add_argument('--amount', default='0.00', help='Subscription amount for a created pilot plan.')
        parser.add_argument('--currency', default='USD', help='Plan currency for a created pilot plan.')
        parser.add_argument('--billing-cycle', default='monthly', choices=['monthly', 'quarterly', 'yearly'])
        parser.add_argument('--scopes', default='', help='Comma-separated entitlement scopes.')
        parser.add_argument('--dry-run', action='store_true', help='Show intended changes without writing.')

    def handle(self, *args, **options):
        product_code = str(options['product']).strip().upper()
        organization = self._get_organization(options['organization'])
        product = ProductSystem.objects.filter(code=product_code).first()
        if product is None:
            raise CommandError(f'ProductSystem {product_code} does not exist.')
        if not product.is_available:
            raise CommandError(f'ProductSystem {product_code} is not active or beta.')

        plan_code = self._plan_code(options['plan'], product_code)
        scopes = [item.strip() for item in options['scopes'].split(',') if item.strip()]
        amount = Decimal(str(options['amount']))
        dry_run = options['dry_run']

        before = self._state(organization, product)
        changes = self._planned_changes(organization, product, plan_code)

        result = {
            'dry_run': dry_run,
            'organization': {
                'id': str(organization.id),
                'code': organization.code,
                'name': organization.name,
                'status': organization.status,
            },
            'product': product_code,
            'plan': plan_code,
            'before': before,
            'planned_changes': changes,
        }

        if dry_run:
            result['after'] = before
            self.stdout.write(json.dumps(result, indent=2, ensure_ascii=True))
            return

        with transaction.atomic():
            plan, plan_created = Plan.objects.get_or_create(
                code=plan_code,
                defaults={
                    'name': f'{product.name} Pilot',
                    'price': amount,
                    'currency': options['currency'],
                    'billing_cycle': options['billing_cycle'],
                    'modules_included': [],
                    'features': [product_code],
                    'is_active': True,
                    'is_trial_available': False,
                },
            )
            subscription, subscription_created = self._ensure_subscription(organization, plan, amount)
            entitlement, entitlement_created = OrganizationProductEntitlement.objects.get_or_create(
                organization=organization,
                product=product,
                defaults={
                    'enabled': True,
                    'status': 'active',
                    'plan': plan,
                    'subscription': subscription,
                    'scopes': scopes,
                    'metadata': {'provisioned_by': 'provision_pilot_entitlement'},
                },
            )

            previous_state = before.get('entitlement') or {}
            updated_fields = []
            if not entitlement.enabled:
                entitlement.enabled = True
                updated_fields.append('enabled')
            if entitlement.status != 'active':
                entitlement.status = 'active'
                updated_fields.append('status')
            if entitlement.plan_id != plan.id:
                entitlement.plan = plan
                updated_fields.append('plan')
            if entitlement.subscription_id != subscription.id:
                entitlement.subscription = subscription
                updated_fields.append('subscription')
            if scopes and entitlement.scopes != scopes:
                entitlement.scopes = scopes
                updated_fields.append('scopes')
            metadata = dict(entitlement.metadata or {})
            if metadata.get('provisioned_by') != 'provision_pilot_entitlement':
                metadata['provisioned_by'] = 'provision_pilot_entitlement'
                entitlement.metadata = metadata
                updated_fields.append('metadata')
            if updated_fields:
                updated_fields.append('updated_at')
                entitlement.save(update_fields=updated_fields)

            if organization.subscription_id != subscription.id:
                organization.subscription = subscription
                organization.save(update_fields=['subscription', 'updated_at'])

            entitlement.refresh_from_db()
            ProductEntitlementAuditLog.objects.create(
                entitlement=entitlement,
                organization=organization,
                product=product,
                action='created' if entitlement_created else 'updated',
                previous_state=previous_state,
                new_state={
                    'enabled': entitlement.enabled,
                    'status': entitlement.status,
                    'subscription_id': str(entitlement.subscription_id),
                    'plan_id': str(entitlement.plan_id),
                    'access_allowed': entitlement.access_allowed,
                    'access_denial_reason': entitlement.access_denial_reason,
                },
                metadata={
                    'source': 'provision_pilot_entitlement',
                    'plan_created': plan_created,
                    'subscription_created': subscription_created,
                    'updated_fields': updated_fields,
                },
            )

        result['after'] = self._state(organization, product)
        result['access_allowed'] = result['after']['entitlement']['access_allowed']
        result['source'] = 'adminapps'
        result['fallback'] = False
        self.stdout.write(json.dumps(result, indent=2, ensure_ascii=True))

    def _get_organization(self, value):
        lookup = str(value).strip()
        candidates = Organization.objects.none()
        try:
            candidates = Organization.objects.filter(id=uuid.UUID(lookup))
        except ValueError:
            pass
        if not candidates.exists():
            candidates = Organization.objects.filter(code__iexact=lookup)
        if not candidates.exists():
            candidates = Organization.objects.filter(name__iexact=lookup)
        try:
            return candidates.get()
        except Organization.DoesNotExist as exc:
            raise CommandError(f'Organization {lookup} does not exist.') from exc
        except Organization.MultipleObjectsReturned as exc:
            raise CommandError(f'Organization {lookup} matched multiple rows.') from exc

    def _plan_code(self, plan, product_code):
        plan = str(plan).strip()
        if plan.lower() == 'pilot':
            return f'{product_code}_PILOT'
        return plan.upper()

    def _ensure_subscription(self, organization, plan, amount):
        existing = organization.subscription
        if existing and existing.is_active:
            return existing, False
        subscription = Subscription.objects.create(
            plan=plan,
            status='active',
            started_at=timezone.now(),
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30),
            amount=amount,
            notes='Provisioned by provision_pilot_entitlement.',
        )
        return subscription, True

    def _planned_changes(self, organization, product, plan_code):
        entitlement = OrganizationProductEntitlement.objects.filter(
            organization=organization,
            product=product,
        ).first()
        return {
            'create_plan': not Plan.objects.filter(code=plan_code).exists(),
            'create_subscription': not (organization.subscription and organization.subscription.is_active),
            'create_entitlement': entitlement is None,
            'activate_entitlement': bool(entitlement and (not entitlement.enabled or entitlement.status != 'active')),
            'attach_subscription': bool(entitlement and not entitlement.effective_subscription),
        }

    def _state(self, organization, product):
        organization.refresh_from_db()
        entitlement = OrganizationProductEntitlement.objects.filter(
            organization=organization,
            product=product,
        ).select_related('subscription', 'subscription__plan', 'plan', 'product').first()
        org_subscription = organization.subscription
        return {
            'organization_subscription': {
                'id': str(org_subscription.id),
                'plan': org_subscription.plan.code,
                'status': org_subscription.status,
                'is_active': org_subscription.is_active,
            } if org_subscription else None,
            'entitlement': {
                'id': str(entitlement.id),
                'enabled': entitlement.enabled,
                'status': entitlement.status,
                'subscription_id': str(entitlement.subscription_id) if entitlement.subscription_id else None,
                'effective_subscription_id': str(entitlement.effective_subscription.id) if entitlement.effective_subscription else None,
                'plan_id': str(entitlement.plan_id) if entitlement.plan_id else None,
                'access_allowed': entitlement.access_allowed,
                'access_denial_reason': entitlement.access_denial_reason,
                'scopes': entitlement.scopes,
            } if entitlement else None,
        }
