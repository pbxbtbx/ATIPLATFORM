import io
import zipfile
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Profile, AcademicYear, ClassGroup, Student, Session, Enrollment, ImportDraft
from .importing import parse_docx, parse_csv


def document():
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+''.join('<w:p><w:r><w:t>'+t+'</w:t></w:r></w:p>' for t in ['Ficha Docente 03','Videojuego de prueba','Duración','90 min','Ladrillos que trabajamos','Eventos','Preparar antes de la clase','Abrir entorno','Retos desbloqueables','R1','Crear personaje'])+'</w:body></w:document>')
    return out.getvalue()


class ImportTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('admin'); Profile.objects.create(user=self.user,role='admin')
        self.teacher=User.objects.create_user('docente'); Profile.objects.create(user=self.teacher)
        self.today=timezone.localdate()
        year=AcademicYear.objects.create(name='Ficticio',starts=self.today-timedelta(days=10),ends=self.today+timedelta(days=100))
        self.group=ClassGroup.objects.create(name='Prueba',year=year,kind='initial',starts=year.starts,ends=year.ends,capacity=3)
        self.group.teachers.add(self.teacher)
        self.client.force_login(self.user)
    def upload(self,kind,data,filename):
        response=self.client.post('/imports/',{'kind':kind,'file':SimpleUploadedFile(filename,data)})
        self.assertEqual(response.status_code,302)
        return response.url
    def options(self,**extra):
        data={'group':str(self.group.pk),'teacher':str(self.teacher.pk),'action':'review'};data.update(extra);return data
    def test_bulk_preview_confirm_idempotent(self):
        response=self.client.post('/imports/',{'kind':'students','names':'Ficticio A\nFicticio B'})
        url=response.url
        self.assertEqual(Student.objects.count(),0)
        preview=self.client.post(url,self.options(joined=self.today.isoformat()))
        self.assertContains(preview,'Confirmar y crear registros')
        self.assertEqual(Student.objects.count(),0)
        self.client.post(url,{'action':'confirm'})
        self.client.post(url,{'action':'confirm'})
        self.assertEqual(Student.objects.count(),2);self.assertEqual(Enrollment.objects.count(),2)
        self.assertEqual(ImportDraft.objects.get().payload,{})
    def test_capacity_duplicate_and_recheck_at_commit(self):
        url=self.upload('students',b'nombre\nFicticio A\nFicticio B\n','a.csv')
        self.client.post(url,self.options(joined=self.today.isoformat()))
        self.group.capacity=1;self.group.save()
        self.assertContains(self.client.post(url,{'action':'confirm'}),'No hay plazas')
        self.assertFalse(Student.objects.exists())
        self.group.capacity=3;self.group.save()
        Student.objects.create(name='FICTICIO A',joined=self.today)
        self.assertContains(self.client.post(url,{'action':'confirm'}),'repetidos')
        self.assertEqual(Student.objects.count(),1)
    def test_word_extraction_then_create_planned_only(self):
        parsed=parse_docx(document());self.assertEqual(parsed['duration'],90);self.assertIn('R1',parsed['planned'])
        url=self.upload('word',document(),'sesion.docx')
        data=self.options(title=parsed['title'],number=3,start=self.today.isoformat()+'T10:00',duration=90,goals=parsed['goals'],materials=parsed['materials'],planned=parsed['planned'])
        self.assertContains(self.client.post(url,data),'Confirmar y crear registros')
        self.client.post(url,{'action':'confirm','title':'NO DEBE USARSE'})
        session=Session.objects.get();self.assertEqual(session.title,'Videojuego de prueba');self.assertEqual(session.status,'planned')
        self.assertEqual(session.end-session.start,timedelta(minutes=90));self.assertEqual(session.actual,'')
        self.assertIn('R1',session.planned);self.assertEqual(session.attendance_set.count(),0)
    def test_conflicts_atomic_csv_and_missing_fields(self):
        day=self.today.isoformat()
        url=self.upload('sessions',f'titulo;inicio;duracion_minutos\nUno;{day}T10:00;90\nDos;{day}T11:00;60\n'.encode(),'s.csv')
        self.assertContains(self.client.post(url,self.options()),'solapan')
        self.client.post(url,{'action':'confirm'});self.assertEqual(Session.objects.count(),0)
        url=self.upload('word',document(),'s.docx')
        self.assertNotContains(self.client.post(url,self.options()),'value="confirm"')
    def test_scope_owner_expiration_and_developer(self):
        url=self.upload('word',document(),'s.docx')
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.post('/imports/',{'kind':'students','names':'Persona'}).status_code,200)
        self.assertEqual(Student.objects.count(),0)
        foreign=ClassGroup.objects.create(name='Otro',year=self.group.year,kind='initial',starts=self.group.starts,ends=self.group.ends)
        own=self.upload('word',document(),'s.docx')
        self.assertNotContains(self.client.post(own,self.options(group=str(foreign.pk))),'value="confirm"')
        self.teacher.profile.role='developer';self.teacher.profile.save()
        self.assertEqual(self.client.get('/imports/').status_code,403)
        self.client.force_login(self.user)
        ImportDraft.objects.filter(author=self.user).update(created_at=timezone.now()-timedelta(days=2))
        self.assertEqual(self.client.get(url).status_code,302)
    def test_bad_inputs_and_archives(self):
        for data in (b'not a zip',b''):
            with self.assertRaises(ValidationError): parse_docx(data)
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:z.writestr('word/document.xml','<!DOCTYPE foo><foo/>')
        with self.assertRaises(ValidationError):parse_docx(out.getvalue())
        for data in (b'nombre;secreto\nA;x',b'nombre\n',b'nombre,nombre_preferido\nA,B,C',b'nombre,nombre\nA,B'):
            with self.assertRaises(ValidationError):parse_csv(data,'students')
    def test_palette_persistent_independent(self):
        self.client.post('/appearance/',{'theme':'night','learning_palette':'basic'})
        self.user.profile.refresh_from_db();self.assertEqual(self.user.profile.learning_palette,'basic')
        self.assertContains(self.client.get('/appearance/'),'learning-palette-basic')
        self.client.post('/appearance/',{'theme':'classic','learning_palette':'invalid'})
        self.user.profile.refresh_from_db();self.assertEqual(self.user.profile.theme,'night')

    def test_csv_student_optional_fields_and_existing_session_conflict(self):
        url=self.upload('students','nombre;nombre_preferido;nacimiento\nPersona CSV ficticia;Alias;2018-01-02\n'.encode(),'alumnado.csv')
        self.client.post(url,self.options(joined=self.today.isoformat()))
        self.client.post(url,{'action':'confirm'})
        student=Student.objects.get();self.assertEqual(student.preferred_name,'Alias');self.assertEqual(student.birth_date.isoformat(),'2018-01-02')
        url=self.upload('sessions',f'titulo;inicio;duracion_minutos\nSesión CSV;{self.today.isoformat()}T10:00;90\n'.encode(),'sesiones.csv')
        self.assertContains(self.client.post(url,self.options()),'value="confirm"')
        start=timezone.make_aware(timezone.datetime.combine(self.today,timezone.datetime.min.time()).replace(hour=10))
        existing=Session.objects.create(group=self.group,teacher=self.teacher,title='Existente',start=start,end=start+timedelta(hours=1))
        self.assertContains(self.client.post(url,{'action':'confirm'}),'Conflicto')
        self.assertEqual(Session.objects.count(),1);existing.refresh_from_db();self.assertEqual(existing.title,'Existente')

    def test_confirm_without_review_and_csrf(self):
        from django.test import Client
        url=self.upload('word',document(),'sesion.docx')
        self.client.post(url,dict(self.options(title='Intento',number=1,start=self.today.isoformat()+'T10:00',duration=90),action='confirm'))
        self.assertFalse(Session.objects.exists())
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user)
        self.assertEqual(csrf.post('/imports/',{'kind':'students','names':'Prueba'}).status_code,403)
