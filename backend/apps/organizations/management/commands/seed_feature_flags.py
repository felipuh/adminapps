from django.core.management.base import BaseCommand, CommandError

from apps.organizations.models import Organization, OrganizationFeatureFlag


DEFAULT_FLAGS = {
    'billing_revenue_dashboard': False,
    'reports_email_scheduler': True,
    'landing_analytics_dashboard': True,
}


class Command(BaseCommand):
    help = 'Seed default feature flags and optional org override for AdminApps.'

    def add_arguments(self, parser):
        parser.add_argument('--org-code', type=str, help='Organization code for override (e.g. ORG00001).')
        parser.add_argument('--enable-revenue-dashboard', action='store_true', help='Enable billing_revenue_dashboard for org override.')

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for key, enabled in DEFAULT_FLAGS.items():
            obj, was_created = OrganizationFeatureFlag.objects.get_or_create(
                key=key,
                organization=None,
                defaults={
                    'enabled': enabled,
                    'description': f'Default global flag for {key}',
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created global flag: {obj.key}={obj.enabled}'))
            elif obj.enabled != enabled:
                obj.enabled = enabled
                obj.save(update_fields=['enabled', 'updated_at'])
                updated += 1
                self.stdout.write(self.style.WARNING(f'Updated global flag: {obj.key}={obj.enabled}'))

        org_code = options.get('org_code')
        if org_code:
            try:
                organization = Organization.objects.get(code=org_code)
            except Organization.DoesNotExist as exc:
                raise CommandError(f'Organization not found for code={org_code}') from exc

            org_enabled = bool(options.get('enable_revenue_dashboard'))
            org_flag, was_created = OrganizationFeatureFlag.objects.get_or_create(
                key='billing_revenue_dashboard',
                organization=organization,
                defaults={
                    'enabled': org_enabled,
                    'description': 'Organization override for revenue dashboard rollout',
                },
            )
            if not was_created and org_flag.enabled != org_enabled:
                org_flag.enabled = org_enabled
                org_flag.save(update_fields=['enabled', 'updated_at'])
                updated += 1
            elif was_created:
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Org override set: {organization.code} billing_revenue_dashboard={org_flag.enabled}'
                )
            )

        self.stdout.write(self.style.SUCCESS(f'Done. created={created} updated={updated}'))
