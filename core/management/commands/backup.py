import hashlib, sqlite3, shutil, os
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.utils import timezone
from core.models import BackupCheck

class Command(BaseCommand):
    help='Copia coherente de SQLite y archivos privados; restaura la BD en una copia temporal y comprueba integridad.'
    def handle(self,*args,**options):
        root=settings.BASE_DIR/'var'/'backups'/settings.ENVIRONMENT/datetime.now().strftime('%Y%m%d-%H%M%S-%f'); root.mkdir(parents=True,mode=0o700)
        target=root/'database.sqlite3'
        with sqlite3.connect(str(settings.DATABASES['default']['NAME'])) as source,sqlite3.connect(target) as output: source.backup(output)
        os.chmod(target,0o600)
        if Path(settings.MEDIA_ROOT).exists(): shutil.copytree(settings.MEDIA_ROOT,root/'private')
        restored=root/'restore-check.sqlite3'; shutil.copy2(target,restored)
        with sqlite3.connect(restored) as check:
            if check.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or check.execute('PRAGMA foreign_key_check').fetchall(): raise CommandError('Copia inválida.')
            check.execute('SELECT COUNT(*) FROM core_learning').fetchone()
        restored.unlink()
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        BackupCheck.objects.create(filename=str(root.relative_to(settings.BASE_DIR/'var')),digest=digest,verified_at=timezone.now())
        self.stdout.write('Copia y restauración de comprobación correctas: '+str(root))
