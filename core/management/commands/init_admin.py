import getpass,os
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from core.models import Profile
class Command(BaseCommand):
    help='Crea la primera cuenta de administración. No sobrescribe usuarios ni imprime contraseñas.'
    def add_arguments(self,parser): parser.add_argument('--username',required=True); parser.add_argument('--development',action='store_true'); parser.add_argument('--sensitive',action='store_true')
    def handle(self,*args,**opts):
        if User.objects.exists(): raise CommandError('Ya existen usuarios. Crea o modifica cuentas desde Configuración.')
        password=os.getenv('INITIAL_ADMIN_PASSWORD') or getpass.getpass('Contraseña inicial: ')
        try: validate_password(password)
        except ValidationError as e: raise CommandError(' '.join(e.messages))
        with transaction.atomic():
            u=User.objects.create_user(username=opts['username'],password=password,first_name='Administración')
            Profile.objects.create(user=u,role='admin',development_access=opts['development'],sensitive_access=opts['sensitive'])
        self.stdout.write('Cuenta creada. Los permisos adicionales corresponden a los indicadores elegidos.')
