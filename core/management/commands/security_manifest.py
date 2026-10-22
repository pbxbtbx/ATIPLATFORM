"""Maintainer-only release step. Never exposed by a web route."""
import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from core.security_review import fingerprint, MANIFEST, integrity


class Command(BaseCommand):
    help = 'Genera la referencia SHA-256 para revisar y versionar antes del despliegue.'
    def add_arguments(self, parser):
        parser.add_argument('--check', action='store_true', help='Verifica sin modificar el manifiesto.')

    def handle(self, *args, **options):
        if options['check']:
            if integrity()['status'] != 'ok':
                raise CommandError('Integridad no verificada; revisa el manifiesto y los archivos.')
            self.stdout.write('Integridad comprobada; manifiesto sin modificar.')
            return
        files = fingerprint(settings.BASE_DIR)
        (settings.BASE_DIR / MANIFEST).write_text(json.dumps({'schema': 1, 'files': files}, sort_keys=True, indent=2) + '\n')
        self.stdout.write(f'Manifiesto generado: {len(files)} archivos. Revisa el diff antes de publicarlo.')
