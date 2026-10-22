from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import ImportDraft


class Command(BaseCommand):
    help='Elimina borradores de importación de más de 24 horas, incluidos sus datos personales temporales.'
    def handle(self,*args,**options):
        count,_=ImportDraft.objects.filter(created_at__lt=timezone.now()-timedelta(days=1)).delete()
        self.stdout.write(f'Borradores eliminados: {count}')
