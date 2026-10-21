from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management.base import BaseCommand, CommandError

from apps.integration.services import create_integration_api_key


class Command(BaseCommand):
    help = 'Generate a new Integration API key; the raw value is shown only once.'

    def add_arguments(self, parser):
        parser.add_argument('--name', default='isosmart')
        parser.add_argument('--actor-id', required=True)

    def handle(self, *args, **options):
        user_model = get_user_model()
        try:
            operator = user_model.objects.get(pk=options['actor_id'])
        except user_model.DoesNotExist as exc:
            raise CommandError('Active staff operator not found.') from exc

        try:
            credential, raw_key = create_integration_api_key(
                name=options['name'],
                operator=operator,
            )
        except PermissionDenied as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.WARNING(
            'Save this replacement key now; it cannot be recovered later.'
        ))
        self.stdout.write(f'Credential ID: {credential.pk}')
        self.stdout.write(f'Fingerprint: {credential.fingerprint}')
        self.stdout.write(f'API key (one-time): {raw_key}')
