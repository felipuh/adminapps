from django.core.management.base import BaseCommand
from django.utils import timezone
import os

from apps.integration.models import IntegrationAPIKey


class Command(BaseCommand):
    help = "Create or update an Integration API key in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="isosmart",
            help="Service name for the API key (default: isosmart)",
        )
        parser.add_argument(
            "--key",
            default=None,
            help="API key value. If omitted, uses ISOSMART_INTEGRATION_KEY env var.",
        )
        parser.add_argument(
            "--active",
            action="store_true",
            help="Mark the key as active.",
        )
        parser.add_argument(
            "--inactive",
            action="store_true",
            help="Mark the key as inactive.",
        )

    def handle(self, *args, **options):
        name = options["name"]
        key = options["key"] or os.environ.get("ISOSMART_INTEGRATION_KEY")

        if not key:
            key = "isosmart-integration-key-2025"
            self.stdout.write(
                self.style.WARNING(
                    "No key provided. Using default dev key: isosmart-integration-key-2025"
                )
            )

        if options["active"] and options["inactive"]:
            self.stdout.write(
                self.style.ERROR("Use only one of --active or --inactive.")
            )
            return

        is_active = True
        if options["inactive"]:
            is_active = False

        key_obj, created = IntegrationAPIKey.objects.update_or_create(
            name=name,
            defaults={
                "key": key,
                "is_active": is_active,
                "updated_at": timezone.now(),
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Created API key for {name} (active={is_active}).")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Updated API key for {name} (active={is_active}).")
            )
