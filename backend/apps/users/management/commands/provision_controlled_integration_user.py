import json
import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.organizations.models import Organization
from apps.users.models import UserOrganization


class Command(BaseCommand):
    help = 'Idempotently provision a local controlled integration user for an existing organization.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Controlled QA user email.')
        parser.add_argument('--organization', required=True, help='Organization UUID, code, or exact name.')
        parser.add_argument('--password', help='Password to set. Required unless --dry-run is used.')
        parser.add_argument('--role', default='org_admin', help='Organization role for the controlled user.')
        parser.add_argument('--first-name', default='Controlled', help='First name for created users.')
        parser.add_argument('--last-name', default='Integration', help='Last name for created users.')
        parser.add_argument('--dry-run', action='store_true', help='Show intended changes without writing.')

    def handle(self, *args, **options):
        email = str(options['email']).strip().lower()
        if not email:
            raise CommandError('Email cannot be empty.')

        organization = self._get_organization(options['organization'])
        dry_run = bool(options['dry_run'])
        password = options.get('password')
        role = str(options['role']).strip() or 'org_admin'

        if not dry_run and not password:
            raise CommandError('Use --password for real execution. The password is never printed.')

        user_model = get_user_model()
        user = user_model.objects.filter(email=email).first()
        membership = (
            UserOrganization.objects.filter(user=user, organization=organization).first()
            if user else None
        )

        planned_changes = {
            'create_user': user is None,
            'set_password': not dry_run,
            'activate_user': bool(user and not user.is_active),
            'attach_primary_organization': bool(user and user.organization_id != organization.id),
            'create_membership': membership is None,
            'activate_membership': bool(membership and not membership.is_active),
            'update_membership_role': bool(membership and membership.role != role),
        }

        before = self._state(user, membership)
        result = {
            'dry_run': dry_run,
            'email': email,
            'organization': {
                'id': str(organization.id),
                'code': organization.code,
                'name': organization.name,
                'status': organization.status,
            },
            'role': role,
            'before': before,
            'planned_changes': planned_changes,
        }

        if dry_run:
            result['after'] = before
            self.stdout.write(json.dumps(result, indent=2, ensure_ascii=True))
            return

        with transaction.atomic():
            if user is None:
                user = user_model(
                    email=email,
                    first_name=options['first_name'],
                    last_name=options['last_name'],
                    organization=organization,
                    role=role,
                    is_active=True,
                    is_verified=True,
                )
            else:
                user.organization = organization
                user.role = role
                user.is_active = True
                user.is_verified = True
                if not user.first_name:
                    user.first_name = options['first_name']
                if not user.last_name:
                    user.last_name = options['last_name']
                if hasattr(user, 'clear_temporary_password'):
                    user.clear_temporary_password()

            user.set_password(password)
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save()

            membership, _ = UserOrganization.objects.update_or_create(
                user=user,
                organization=organization,
                defaults={
                    'role': role,
                    'is_primary': True,
                    'is_active': True,
                },
            )

        result['after'] = self._state(user, membership)
        result['password_printed'] = False
        self.stdout.write(json.dumps(result, indent=2, ensure_ascii=True))

    def _get_organization(self, value):
        lookup = str(value).strip()
        candidates = Organization.objects.none()
        try:
            candidates = Organization.objects.filter(id=uuid.UUID(lookup))
        except (TypeError, ValueError):
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

    def _state(self, user, membership):
        return {
            'user': {
                'id': str(user.id),
                'email': user.email,
                'organization_id': str(user.organization_id) if user.organization_id else None,
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'is_locked': user.is_locked,
            } if user else None,
            'membership': {
                'id': str(membership.id),
                'organization_id': str(membership.organization_id),
                'role': membership.role,
                'is_primary': membership.is_primary,
                'is_active': membership.is_active,
            } if membership else None,
        }
