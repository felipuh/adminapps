from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.integration.services import rotate_integration_api_key


class Command(BaseCommand):
    help = 'Rotate an Integration API key; the replacement is shown only once.'

    def add_arguments(self, parser):
        parser.add_argument('--id', required=True, help='Integration API key database ID.')
        parser.add_argument('--actor-id', required=True, help='Active staff operator ID.')

    def handle(self, *args, **options):
        user_model = get_user_model()
        try:
            operator = user_model.objects.get(pk=options['actor_id'])
        except user_model.DoesNotExist as exc:
            raise CommandError('Active staff operator not found.') from exc

        try:
            credential, raw_key = rotate_integration_api_key(
                credential_id=options['id'],
                operator=operator,
            )
        except (PermissionDenied, ValidationError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.WARNING(
            'Save this replacement key now; it cannot be recovered later.'
        ))
        self.stdout.write(f'Credential ID: {credential.pk}')
        self.stdout.write(f'Fingerprint: {credential.fingerprint}')
        self.stdout.write(f'API key (one-time): {raw_key}')
