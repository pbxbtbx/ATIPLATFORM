import os, secrets
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import *
from core.services import snapshot

class Command(BaseCommand):
    help='Carga registros ficticios únicamente con APP_ENV=demo y base de datos demo separada.'
    def handle(self,*args,**opts):
        if settings.ENVIRONMENT!='demo' or 'demo' not in str(settings.DATABASES['default']['NAME']): raise CommandError('Usa APP_ENV=demo con una base de datos cuyo nombre contenga demo.')
        if ClassGroup.objects.exists(): self.stdout.write('Demostración ya creada. No se sobrescribe.'); return
        password=os.getenv('DEMO_PASSWORD')
        if not password or len(password)<12: raise CommandError('Define DEMO_PASSWORD (mínimo 12 caracteres) en el proceso; no se imprime ni se guarda en archivos.')
        today=timezone.localdate(); year=AcademicYear.objects.create(name='Curso ficticio de demostración',starts=today-timedelta(days=90),ends=today+timedelta(days=270))
        admin=User.objects.create_user('demo.admin',password=password,first_name='Equipo demo'); Profile.objects.create(user=admin,role='admin',development_access=True,sensitive_access=True)
        teacher=User.objects.create_user('demo.docente',password=password,first_name='Docente ficticio'); Profile.objects.create(user=teacher,role='teacher')
        dev=User.objects.create_user('demo.desarrollo',password=password,first_name='Desarrollo ficticio'); Profile.objects.create(user=dev,role='developer',development_access=True)
        names=['Exploradores · DEMO','Laboratorio creativo · DEMO','Dúrcal multinivel · DEMO']
        resources=[]
        descriptions=[('Un jardín que responde','Robótica y domótica','Construir un prototipo que detecte luz y active una señal.'),('Historias que se juegan','Videojuegos','Crear una escena interactiva y explicar sus reglas.'),('Diseñar para resolver','Diseño e impresión 3D','Prototipar una solución y mejorarla tras una prueba.')]
        for index,(kind,label) in enumerate(ClassGroup.TYPES):
            group=ClassGroup.objects.create(name=names[index],kind=kind,year=year,location='Aula ficticia '+str(index+1),starts=year.starts,ends=year.ends,capacity=12,schedule='Horario ficticio: solo demostración',plan='Explorar → prototipar → probar → compartir')
            group.teachers.add(teacher,admin)
            title,domain,description=descriptions[index]
            resource=Resource.objects.create(title=title+' · DEMO',kind=kind,domain=domain,description=description,goals='Descomponer un reto, probar una idea y explicar las decisiones.',materials='Kit de prototipado y ordenador (ejemplo ficticio).',challenges='Inicio: activar una salida. Ampliación: usar condiciones. Avanzado: depurar y justificar la solución.',supports='Instrucciones visuales y trabajo por parejas.',criteria='Explica una decisión y utiliza pruebas para mejorar el prototipo.')
            start=timezone.now().replace(hour=9+index*2,minute=0,second=0,microsecond=0)
            session=Session.objects.create(group=group,teacher=teacher,title=resource.title,start=start,end=start+timedelta(hours=1),resource=resource,resource_snapshot=snapshot(resource),goals=resource.goals,materials=resource.materials,planned=description)
            future=Session.objects.create(group=group,teacher=teacher,title='Iterar y compartir · DEMO',start=start+timedelta(days=7),end=start+timedelta(days=7,hours=1),number=2,goals='Revisar el prototipo y comunicar el proceso.',materials=resource.materials)
            for n in range(3):
                student=Student.objects.create(name=f'Persona ficticia {index*3+n+1:02d}',joined=today-timedelta(days=30),interests='Crear proyectos de tecnología (ejemplo ficticio)',strengths='Curiosidad y ganas de experimentar.')
                Enrollment.objects.create(student=student,group=group,starts=student.joined)
                if index==0 and n<2:
                    guardian,_=Guardian.objects.get_or_create(name='Responsable ficticio compartido',defaults={'email':'ejemplo@example.invalid'})
                    GuardianLink.objects.create(student=student,guardian=guardian,relationship='Responsable de demostración',legal=True)
                Attendance.objects.create(session=session,student=student,status='present')
                Learning.objects.create(student=student,session=session,author=teacher,challenge='Primer prototipo ficticio',evidence='Prueba una entrada y describe el resultado.',achievement='Identifica una relación causa-efecto.',next_step='Añadir otra condición.' if n else 'Repasar entradas y salidas con apoyo.',activity_status='autonomous' if n else 'supported',learning_status='progress' if n==0 else 'autonomous')
        Task.objects.create(author=admin,title='Preparar kits para la próxima clase · DEMO',due=today)
        Task.objects.create(author=admin,title='Revisar la secuencia de retos · DEMO',due=today+timedelta(days=1))
        self.stdout.write(self.style.SUCCESS('Demostración creada. Usuarios: demo.admin, demo.docente, demo.desarrollo. Contraseña: la indicada en DEMO_PASSWORD. Todos los datos son ficticios.'))
