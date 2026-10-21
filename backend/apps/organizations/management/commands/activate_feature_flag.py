"""
Management command to activate (or deactivate) a feature flag for a specific organization.

Usage:
  python manage.py activate_feature_flag --flag billing_revenue_dashboard --org TEST_ORG --enable
  python manage.py activate_feature_flag --flag billing_revenue_dashboard --org TEST_ORG --disable
"""
from django.core.management.base import BaseCommand, CommandError
from apps.organizations.models import Organization, OrganizationFeatureFlag


class Command(BaseCommand):
    help = 'Activate or deactivate a feature flag for a specific organization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flag',
            type=str,
            required=True,
            help='Feature flag key (e.g., billing_revenue_dashboard)'
        )
        parser.add_argument(
            '--org',
            type=str,
            required=True,
            help='Organization code (e.g., TEST_ORG)'
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Enable the flag for this organization'
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            help='Disable the flag for this organization'
        )

    def handle(self, *args, **options):
        flag_key = options['flag']
        org_code = options['org']
        
        if not options['enable'] and not options['disable']:
            raise CommandError('Specify either --enable or --disable')
        
        if options['enable'] and options['disable']:
            raise CommandError('Cannot specify both --enable and --disable')
        
        # Find organization
        try:
            org = Organization.objects.get(code=org_code)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization with code "{org_code}" not found')
        
        # Create or update org-specific flag override
        enabled = options['enable']
        flag, created = OrganizationFeatureFlag.objects.get_or_create(
            key=flag_key,
            organization=org,
            defaults={'enabled': enabled}
        )
        
        if not created:
            flag.enabled = enabled
            flag.save()
            action = 'Updated'
        else:
            action = 'Created'
        
        status = 'ENABLED' if enabled else 'DISABLED'
        self.stdout.write(
            self.style.SUCCESS(
                f'{action} org-specific flag: {org.name} → {flag_key}={status}'
            )
        )
        
        # Show current resolution
        resolved = OrganizationFeatureFlag.objects.resolve_for_organization(org)
        self.stdout.write(
            f'\nFlag resolution for {org.name}:'
        )
        self.stdout.write(f'  {flag_key}: {resolved.get(flag_key, "NOT SET")}')
