import io,json
from datetime import timedelta
from django.test import TestCase,Client,override_settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import *
from .forms import ResourceForm,DynamicStudentForm
from .services import move_student,snapshot,save_versioned
from .configuration import DEFAULT

class PlatformTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user('admin',password='Example-password-948!'); Profile.objects.create(user=self.admin,role='admin',development_access=True,sensitive_access=True)
        self.teacher=User.objects.create_user('teacher',password='Example-password-948!'); Profile.objects.create(user=self.teacher,role='teacher')
        self.other=User.objects.create_user('other',password='Example-password-948!'); Profile.objects.create(user=self.other,role='teacher')
        self.dev=User.objects.create_user('dev',password='Example-password-948!'); Profile.objects.create(user=self.dev,role='developer',development_access=True)
        self.today=timezone.localdate()
        self.year=AcademicYear.objects.create(name='Curso ficticio',starts=self.today-timedelta(days=100),ends=self.today+timedelta(days=300))
        self.group=ClassGroup.objects.create(name='Grupo ficticio',year=self.year,kind='initial',starts=self.year.starts,ends=self.year.ends,capacity=10)
        self.group.teachers.add(self.teacher)
        self.group2=ClassGroup.objects.create(name='Otro grupo ficticio',year=self.year,kind='durcal',starts=self.year.starts,ends=self.year.ends,capacity=10)
        self.group2.teachers.add(self.other)
        self.student=Student.objects.create(name='Persona ficticia',joined=self.today-timedelta(days=30))
        self.second=Student.objects.create(name='Hermano ficticio',joined=self.student.joined)
        self.enrollment=Enrollment.objects.create(student=self.student,group=self.group,starts=self.student.joined)
        Enrollment.objects.create(student=self.second,group=self.group,starts=self.second.joined)
        self.resource=Resource.objects.create(title='Recurso original',kind='initial',domain='Robótica',description='Contenido original')
        self.start=timezone.now().replace(hour=10,minute=0,second=0,microsecond=0)
        self.session=Session.objects.create(group=self.group,teacher=self.teacher,title='Sesión ficticia',start=self.start,end=self.start+timedelta(hours=1),resource=self.resource,resource_snapshot=snapshot(self.resource))
        self.client.force_login(self.admin)
    def session_data(self,session=None,**extra):
        s=session or self.session
        data={'group':str(s.group_id),'teacher':s.teacher_id,'title':s.title,'number':s.number,'start':timezone.localtime(s.start).strftime('%Y-%m-%dT%H:%M'),'end':timezone.localtime(s.end).strftime('%Y-%m-%dT%H:%M'),'resource':str(s.resource_id) if s.resource_id else '', 'status':s.status,'expected_version':s.version,'repeat':'1'}
        data.update(extra); return data
    def test_pages_render(self):
        pages=['/','/groups/','/students/','/calendar/','/calendar/?view=month','/calendar/?view=day','/library/','/reports/','/settings/','/developer/','/sessions/new/','/groups/new/','/students/new/','/settings/year/new/','/settings/users/new/']
        pages += [reverse('group',args=[self.group.pk]),reverse('session',args=[self.session.pk])]
        for tab in ['summary','learning','attendance','guardians','evidence','restricted']: pages.append(reverse('student',args=[self.student.pk])+'?tab='+tab)
        for url in pages:
            with self.subTest(url=url): self.assertEqual(self.client.get(url).status_code,200)
    def test_auth_required_and_csrf(self):
        self.client.logout(); self.assertEqual(self.client.get('/students/').status_code,302)
        protected=Client(enforce_csrf_checks=True); protected.force_login(self.admin)
        self.assertEqual(protected.post('/groups/new/',{}).status_code,403)
    def test_teacher_scope_and_sensitive_denied(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('group',args=[self.group.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('session',args=[self.session.pk])).status_code,404)
        self.assertEqual(self.client.get(reverse('student',args=[self.student.pk])).status_code,404)
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse('student',args=[self.student.pk])+'?tab=restricted').status_code,403)
        self.assertEqual(self.client.post(reverse('restricted_new',args=[self.student.pk]),{}).status_code,403)
    def test_developer_not_educational_access(self):
        self.client.force_login(self.dev)
        self.assertEqual(self.client.get('/developer/').status_code,200)
        self.assertEqual(self.client.get(reverse('student',args=[self.student.pk])).status_code,404)
        self.assertNotContains(self.client.get('/students/'),'Persona ficticia')
        self.assertEqual(self.client.get('/settings/').status_code,403)
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get('/developer/').status_code,403)
        self.assertNotContains(self.client.get('/'),'href="/developer/"')
    def test_individual_paces_and_no_automatic_completion(self):
        self.client.force_login(self.teacher)
        data={'version':1,'actual':'Probamos dos prototipos','common_activity':'Sensor','record_'+str(self.student.pk):'on','record_'+str(self.second.pk):'on','state_'+str(self.student.pk):'supported','learning_'+str(self.student.pk):'progress','state_'+str(self.second.pk):'autonomous','learning_'+str(self.second.pk):'autonomous','private_'+str(self.student.pk):'Privada de uno','close':'1'}
        self.assertEqual(self.client.post(reverse('class_save',args=[self.session.pk]),data).status_code,302)
        one=Learning.objects.get(student=self.student); two=Learning.objects.get(student=self.second)
        self.assertEqual(one.learning_status,'progress'); self.assertEqual(two.learning_status,'autonomous'); self.assertEqual(two.internal_notes,'')
        self.session.refresh_from_db(); self.assertEqual(self.session.status,'done')
    def test_learning_revisions_append(self):
        data={'version':1,'record_'+str(self.student.pk):'on','common_activity':'Primer reto'}
        self.client.post(reverse('class_save',args=[self.session.pk]),data)
        first=Learning.objects.get(student=self.student)
        data.update(version=2,common_activity='Revisión del reto')
        self.client.post(reverse('class_save',args=[self.session.pk]),data)
        self.assertEqual(Learning.objects.count(),2); self.assertEqual(Learning.objects.exclude(pk=first.pk).get().supersedes,first)
    def test_cancel_and_recovery_keep_original(self):
        response=self.client.post(reverse('session_edit',args=[self.session.pk]),self.session_data(status='recover'))
        self.assertEqual(response.status_code,302)
        self.session.refresh_from_db(); self.assertEqual(self.session.status,'recover')
        data=self.session_data(start=timezone.localtime(self.start+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),end=timezone.localtime(self.start+timedelta(days=2,hours=1)).strftime('%Y-%m-%dT%H:%M'),status='planned')
        response=self.client.post(reverse('session_recover',args=[self.session.pk]),data)
        self.assertEqual(response.status_code,302); recovered=Session.objects.get(recovery_of=self.session); self.assertEqual(recovered.status,'planned')
        self.assertEqual(Session.objects.get(pk=self.session.pk).status,'recover')
    def test_single_occurrence_edit(self):
        series=uuid.uuid4(); self.session.series=series; self.session.save()
        later=Session.objects.create(group=self.group,teacher=self.teacher,title='Segunda',start=self.start+timedelta(days=7),end=self.start+timedelta(days=7,hours=1),series=series)
        data=self.session_data(start=timezone.localtime(self.start+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),end=timezone.localtime(self.start+timedelta(days=1,hours=1)).strftime('%Y-%m-%dT%H:%M'),scope='one')
        self.assertEqual(self.client.post(reverse('session_edit',args=[self.session.pk]),data).status_code,302)
        later.refresh_from_db(); self.assertEqual(later.start,self.start+timedelta(days=7))
    def test_recurrence_atomic_and_conflicts(self):
        data=self.session_data(title='Serie',start=timezone.localtime(self.start+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),end=timezone.localtime(self.start+timedelta(days=1,hours=1)).strftime('%Y-%m-%dT%H:%M'),repeat='3')
        response=self.client.post('/sessions/new/',data); self.assertEqual(response.status_code,302)
        created=Session.objects.filter(title='Serie'); self.assertEqual(created.count(),3); self.assertEqual(created.values('series').distinct().count(),1)
        response=self.client.post('/sessions/new/',data); self.assertContains(response,'Conflicto'); self.assertEqual(created.count(),3)
    def test_holidays_block_whole_series(self):
        Holiday.objects.create(title='Festivo ficticio',start=self.today+timedelta(days=8),end=self.today+timedelta(days=8))
        data=self.session_data(title='Serie fallida',start=timezone.localtime(self.start+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),end=timezone.localtime(self.start+timedelta(days=1,hours=1)).strftime('%Y-%m-%dT%H:%M'),repeat='3')
        self.assertContains(self.client.post('/sessions/new/',data),'periodo sin clase')
        self.assertFalse(Session.objects.filter(title='Serie fallida').exists())
    def test_transfer_keeps_history(self):
        learning=Learning.objects.create(student=self.student,session=self.session,author=self.teacher,challenge='Anterior')
        move_student(self.student,self.group2,self.today,self.admin,self.enrollment.pk)
        self.enrollment.refresh_from_db(); self.assertEqual(self.enrollment.ends,self.today-timedelta(days=1))
        self.assertTrue(Learning.objects.filter(pk=learning.pk).exists()); self.assertEqual(self.student.enrollments.count(),2)
    def test_siblings_share_responsible(self):
        g=Guardian.objects.create(name='Responsable ficticio')
        GuardianLink.objects.create(student=self.student,guardian=g,relationship='Responsable',legal=True)
        GuardianLink.objects.create(student=self.second,guardian=g,relationship='Recogida',pickup='Viernes')
        self.assertEqual(Guardian.objects.count(),1); self.assertEqual(GuardianLink.objects.count(),2)
        self.assertFalse(self.second.guardians.get().legal)
    def test_report_excludes_sensitive_and_other_students(self):
        Learning.objects.create(student=self.student,session=self.session,author=self.teacher,challenge='Mi proyecto',achievement='Logro compartible',internal_notes='SECRETO_INTERNO')
        Learning.objects.create(student=self.second,session=self.session,author=self.teacher,challenge='OTRO_ALUMNO')
        RestrictedNote.objects.create(student=self.student,kind='health',content='SECRETO_SALUD',source='Familia',relevance='Operativa',review=self.today,author=self.admin)
        response=self.client.get('/reports/',{'student':self.student.pk,'section':['achievement','internal_notes']})
        self.assertContains(response,'Logro compartible'); self.assertNotContains(response,'SECRETO_INTERNO'); self.assertNotContains(response,'SECRETO_SALUD'); self.assertNotContains(response,'OTRO_ALUMNO')
        response=self.client.get('/reports/',{'student':self.student.pk,'format':'csv','section':['achievement','internal_notes']})
        self.assertIn(b'Logro compartible',response.content); self.assertNotIn(b'SECRETO',response.content)
        response=self.client.get('/reports/',{'student':self.student.pk,'format':'pdf'})
        self.assertEqual(response.status_code,200); self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF'))
    def test_library_snapshot_is_immutable(self):
        self.resource.description='Contenido nuevo'; self.resource.save()
        self.session.refresh_from_db(); self.assertEqual(self.session.resource_snapshot['description'],'Contenido original')
        data=self.session_data(title='Nombre nuevo')
        self.assertEqual(self.client.post(reverse('session_edit',args=[self.session.pk]),data).status_code,302)
        self.session.refresh_from_db(); self.assertEqual(self.session.resource_snapshot['description'],'Contenido original')
    def test_concurrent_class_write_rejected_and_rolled_back(self):
        data={'version':1,'actual':'Primera edición','attendance_'+str(self.student.pk):'present'}
        self.client.post(reverse('class_save',args=[self.session.pk]),data)
        data.update(actual='Sobrescritura',**{'attendance_'+str(self.student.pk):'absent'})
        self.client.post(reverse('class_save',args=[self.session.pk]),data)
        self.session.refresh_from_db(); self.assertEqual(self.session.actual,'Primera edición')
        self.assertEqual(Attendance.objects.get().status,'present')
    def test_concurrent_resource_write_rejected(self):
        data={k:getattr(self.resource,k) for k in ['title','kind','domain','description','duration']}; data['expected_version']=1
        one=ResourceForm(data,instance=Resource.objects.get(pk=self.resource.pk)); two=ResourceForm(data,instance=Resource.objects.get(pk=self.resource.pk))
        self.assertTrue(one.is_valid()); self.assertTrue(two.is_valid()); save_versioned(one,self.admin)
        with self.assertRaises(ValidationError): save_versioned(two,self.admin)
    def test_config_flow_restore_does_not_touch_history(self):
        l=Learning.objects.create(student=self.student,session=self.session,author=self.teacher,challenge='Conservar')
        response=self.client.post('/developer/',{'payload':json.dumps(DEFAULT),'description':'Cambiar presentación'})
        self.assertEqual(response.status_code,302); version=ConfigVersion.objects.get(); url=reverse('config_preview',args=[version.pk])
        self.assertEqual(self.client.post(url,{'action':'publish','confirm':'PUBLICAR'}).status_code,400)
        self.assertEqual(self.client.post(url,{'action':'validate'}).status_code,200)
        self.assertEqual(self.client.post(url,{'action':'publish','confirm':'PUBLICAR'}).status_code,302)
        self.assertEqual(self.client.post(reverse('config_restore',args=[version.pk]),{'confirm':'RESTAURAR'}).status_code,302)
        self.assertEqual(ConfigVersion.objects.count(),2); self.assertEqual(Learning.objects.get(pk=l.pk).challenge,'Conservar')
    def test_config_rejects_code_and_invalid_data(self):
        response=self.client.post('/developer/',{'payload':json.dumps({'script':'alert(1)'}),'description':'No permitido'})
        self.assertContains(response,'claves no admitidas'); self.assertEqual(ConfigVersion.objects.count(),0)
    def test_restricted_audit_has_no_sensitive_content(self):
        RestrictedNote.objects.create(student=self.student,kind='reported',content='CONTENIDO PRIVADO',source='Familia',relevance='Operativa',review=self.today,author=self.admin)
        self.client.get(reverse('student',args=[self.student.pk])+'?tab=restricted')
        self.assertTrue(Audit.objects.filter(action='restricted:read').exists())
        self.assertNotIn('CONTENIDO PRIVADO',str(list(Audit.objects.values())))
    def test_evidence_rejects_executable_disguised(self):
        file=SimpleUploadedFile('danger.png',b'<script>alert(1)</script>',content_type='image/png')
        response=self.client.post(reverse('evidence_new',args=[self.student.pk]),{'session':self.session.pk,'title':'Prueba','visibility':'staff','file':file})
        self.assertContains(response,'Solo PDF'); self.assertEqual(Evidence.objects.count(),0)
    def test_archive_preserves_records(self):
        self.year.archived=True; self.year.save(); self.group.status='archived'; self.group.save()
        self.assertTrue(Session.objects.filter(pk=self.session.pk).exists()); self.assertEqual(self.student.enrollments.count(),1)
    def test_custom_fields_retain_retired_data(self):
        payload={**DEFAULT,'custom_fields':[{'key':'tool','label':'Herramienta preferida','type':'choice','required':True,'options':['Robótica','3D']}]}
        ConfigVersion.objects.create(environment='development',author=self.admin,description='Campos',payload=payload,state='published',published_at=timezone.now())
        self.student.custom_values={'old_field':'Conservar'}; self.student.save()
        data={'name':self.student.name,'joined':str(self.student.joined),'status':'active','expected_version':1,'custom_tool':'Robótica'}
        form=DynamicStudentForm(data,instance=self.student); self.assertTrue(form.is_valid(),form.errors)
        save_versioned(form,self.admin); self.student.refresh_from_db()
        self.assertEqual(self.student.custom_values,{'old_field':'Conservar','tool':'Robótica'})
    def test_group_reporting_scope(self):
        Learning.objects.create(student=self.student,session=self.session,author=self.teacher,challenge='Reto compartible',internal_notes='PRIVADO')
        self.client.force_login(self.teacher)
        response=self.client.get('/reports/group/',{'group':str(self.group.pk)})
        self.assertContains(response,'Reto compartible'); self.assertNotContains(response,'PRIVADO')
        self.assertEqual(self.client.get('/reports/group/',{'group':str(self.group2.pk)}).status_code,404)
        self.client.force_login(self.dev); self.assertEqual(self.client.get('/reports/group/').status_code,403)
    def test_administrative_export_requires_explicit_sensitive_permission(self):
        RestrictedNote.objects.create(student=self.student,kind='reported',content='RESTRINGIDO',source='Familia',relevance='Operativa',review=self.today,author=self.admin)
        url=reverse('student_export',args=[self.student.pk])
        self.assertEqual(self.client.post(url,{'confirm':'wrong'}).status_code,400)
        self.assertNotIn('restricted',self.client.post(url,{'confirm':'EXPORTAR'}).json())
        data=self.client.post(url,{'confirm':'EXPORTAR','sensitive':'1'}).json()
        self.assertEqual(data['restricted'][0]['content'],'RESTRINGIDO')
        self.admin.profile.sensitive_access=False; self.admin.profile.save()
        self.assertEqual(self.client.post(url,{'confirm':'EXPORTAR','sensitive':'1'}).status_code,403)
        self.client.force_login(self.teacher); self.assertEqual(self.client.get(url).status_code,403)
    def test_configurable_states_keep_historical_labels(self):
        payload={**DEFAULT,'progress_states':[{'key':'investigate','label':'Investigando'}]}
        conf=ConfigVersion.objects.create(environment='development',author=self.admin,description='Estados',payload=payload,state='published',published_at=timezone.now())
        data={'version':1,'common_activity':'Explorar','record_'+str(self.student.pk):'on','state_'+str(self.student.pk):'investigate','learning_'+str(self.student.pk):'investigate'}
        self.client.post(reverse('class_save',args=[self.session.pk]),data)
        learning=Learning.objects.get();self.assertEqual(learning.get_learning_status_display(),'Investigando')
        conf.payload=DEFAULT;conf.save();learning.refresh_from_db();self.assertEqual(learning.get_learning_status_display(),'Investigando')
    def test_feature_modules_enforced_server_side(self):
        ConfigVersion.objects.create(environment='development',author=self.admin,description='Módulos',payload={**DEFAULT,'modules':{'library':False,'reports':False}},state='published',published_at=timezone.now())
        self.assertEqual(self.client.get('/library/').status_code,403);self.assertEqual(self.client.get('/reports/').status_code,403)
        self.assertEqual(self.client.get('/library/new/').status_code,403)
    def test_dst_recurrence_preserves_madrid_wall_time(self):
        from zoneinfo import ZoneInfo
        from datetime import datetime,date
        self.group.starts=date(2026,1,1);self.group.ends=date(2027,1,1);self.group.save()
        data=self.session_data(start='2026-10-20T17:00',end='2026-10-20T18:00',repeat='3',title='Serie cambio de hora')
        self.assertEqual(self.client.post('/sessions/new/',data).status_code,302)
        sessions=Session.objects.filter(title='Serie cambio de hora').order_by('start')
        self.assertEqual([timezone.localtime(s.start).hour for s in sessions],[17,17,17])
        self.assertEqual([s.start.hour for s in sessions],[15,16,16])
    def test_following_series_shift(self):
        series=uuid.uuid4();self.session.series=series;self.session.save()
        later=Session.objects.create(group=self.group,teacher=self.teacher,title='Siguiente',start=self.start+timedelta(days=7),end=self.start+timedelta(days=7,hours=1),series=series)
        data=self.session_data(start=timezone.localtime(self.start+timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),end=timezone.localtime(self.start+timedelta(days=1,hours=1)).strftime('%Y-%m-%dT%H:%M'),scope='following')
        self.assertEqual(self.client.post(reverse('session_edit',args=[self.session.pk]),data).status_code,302)
        later.refresh_from_db();self.assertEqual(later.start,self.start+timedelta(days=8))
    def test_failed_close_retains_submitted_draft(self):
        data={'version':1,'record_'+str(self.student.pk):'on','common_activity':'Conservar esta actividad','close':'1'}
        response=self.client.post(reverse('class_save',args=[self.session.pk]),data)
        self.assertEqual(response.status_code,422); self.assertContains(response,'Conservar esta actividad',status_code=422)
        self.assertFalse(Learning.objects.exists()); self.session.refresh_from_db();self.assertEqual(self.session.version,1)
    def test_safe_diagnostic_contains_no_exception_message(self):
        from .middleware import SafeErrorMiddleware
        from django.test import RequestFactory
        middleware=SafeErrorMiddleware(lambda r:None)
        middleware.process_exception(RequestFactory().get('/'),RuntimeError('Contraseña privada: NUNCA_REGISTRAR'))
        self.assertEqual(TechnicalEvent.objects.count(),1)
        self.assertNotIn('NUNCA_REGISTRAR',str(list(TechnicalEvent.objects.values())))
    def test_login_verifies_credentials(self):
        self.client.logout()
        response=self.client.post('/login/',{'username':'teacher','password':'incorrecta'})
        self.assertEqual(response.status_code,200);self.assertNotIn('_auth_user_id',self.client.session)
        response=self.client.post('/login/',{'username':'teacher','password':'Example-password-948!'})
        self.assertEqual(response.status_code,302);self.assertEqual(int(self.client.session['_auth_user_id']),self.teacher.pk)

    def test_valid_private_file_download_scope(self):
        import tempfile
        from reportlab.pdfgen import canvas
        stream=io.BytesIO(); pdf=canvas.Canvas(stream);pdf.drawString(20,20,'Creación ficticia');pdf.save();content=stream.getvalue()
        with tempfile.TemporaryDirectory() as directory,override_settings(MEDIA_ROOT=directory):
            upload=SimpleUploadedFile('proyecto.pdf',content,content_type='application/pdf')
            response=self.client.post(reverse('evidence_new',args=[self.student.pk]),{'session':self.session.pk,'title':'Prototipo ficticio','visibility':'staff','file':upload})
            self.assertEqual(response.status_code,302); evidence=Evidence.objects.get()
            self.client.force_login(self.teacher);response=self.client.get(reverse('evidence_download',args=[evidence.pk]))
            self.assertEqual(b''.join(response.streaming_content),content);self.assertIn('attachment',response['Content-Disposition']);self.assertEqual(response['Cache-Control'],'no-store')
            self.client.force_login(self.other);self.assertEqual(self.client.get(reverse('evidence_download',args=[evidence.pk])).status_code,404)
            self.client.force_login(self.dev);self.assertEqual(self.client.get(reverse('evidence_download',args=[evidence.pk])).status_code,404)


class BootstrapTests(TestCase):
    def test_first_admin_explicit_permissions_and_no_password_output(self):
        from unittest.mock import patch
        from django.core.management import call_command,CommandError
        output=io.StringIO()
        with patch.dict('os.environ',{'INITIAL_ADMIN_PASSWORD':'Example-bootstrap-948!'}):
            call_command('init_admin',username='first.admin',development=True,sensitive=False,stdout=output)
        user=User.objects.get(username='first.admin')
        self.assertTrue(user.profile.development_access);self.assertFalse(user.profile.sensitive_access)
        self.assertNotIn('Example-bootstrap',output.getvalue())
        with self.assertRaises(CommandError): call_command('init_admin',username='duplicate')
