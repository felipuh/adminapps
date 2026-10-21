import json

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError, ProgrammingError

from apps.products.services import build_product_access_readiness_report


class Command(BaseCommand):
    help = 'Generate a read-only SaaS product access readiness report for AdminApps.'

    def handle(self, *args, **options):
        try:
            report = build_product_access_readiness_report()
        except (OperationalError, ProgrammingError) as exc:
            raise CommandError(
                'No se pudo generar el readiness de productos porque el schema no esta actualizado. '
                'Ejecuta las migraciones de AdminApps antes de usar este comando.'
            ) from exc

        self.stdout.write(json.dumps(report, indent=2, ensure_ascii=True))
