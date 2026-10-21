import json

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError, ProgrammingError

from apps.billing.services import (
    auto_map_product_catalog_candidates,
    build_product_catalog_mapping_audit,
)


class Command(BaseCommand):
    help = 'Audit and optionally auto-map ProductCatalog items to ProductSystem entries.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Apply exact candidate mappings. Without this flag the command is read-only.',
        )

    def handle(self, *args, **options):
        try:
            if options['apply']:
                report = auto_map_product_catalog_candidates(dry_run=False)
            else:
                report = build_product_catalog_mapping_audit()
        except (OperationalError, ProgrammingError) as exc:
            raise CommandError(
                'No se pudo auditar ProductCatalog porque el schema no esta actualizado. '
                'Ejecuta las migraciones de AdminApps antes de usar este comando.'
            ) from exc

        self.stdout.write(json.dumps(report, indent=2, ensure_ascii=True))
