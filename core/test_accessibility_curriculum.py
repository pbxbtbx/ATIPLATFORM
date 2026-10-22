import json,re,tempfile,sqlite3
from pathlib import Path
from datetime import timedelta
from django.test import TestCase,Client,override_settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import Profile,AcademicYear,ClassGroup,Student,Enrollment,Session,Learning,ChallengeProgress,Resource
from core import practice
from core.accessibility import preferences
from core.curriculum import board


class AccessibilityCurriculumTests(TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.override=override_settings(PRACTICE_DATABASE_PATH=Path(self.tmp.name)/'practice.sqlite3');self.override.enable();self.addCleanup(self.override.disable)
        self.admin=User.objects.create_user('a11y.admin');Profile.objects.create(user=self.admin,role='admin')
        self.teacher=User.objects.create_user('a11y.teacher');Profile.objects.create(user=self.teacher)
        self.other=User.objects.create_user('a11y.other');Profile.objects.create(user=self.other)
        self.dev=User.objects.create_user('a11y.dev');Profile.objects.create(user=self.dev,role='developer',development_access=True)
        today=timezone.localdate();year=AcademicYear.objects.create(name='Ficticio',starts=today-timedelta(days=30),ends=today+timedelta(days=100))
        self.group=ClassGroup.objects.create(name='Grupo ficticio',year=year,kind='initial',starts=year.starts,ends=year.ends);self.group.teachers.add(self.teacher)
        self.foreign=ClassGroup.objects.create(name='Otro grupo ficticio',year=year,kind='initial',starts=year.starts,ends=year.ends);self.foreign.teachers.add(self.other)
        self.student=Student.objects.create(name='NO_LEER_DATOS_PERSONALES',joined=today)
        Enrollment.objects.create(student=self.student,group=self.group,starts=today)
        start=timezone.now().replace(hour=16,minute=30,second=0,microsecond=0)
        self.session=Session.objects.create(group=self.group,teacher=self.teacher,title='Sesión ficticia',content_area='games',start=start,end=start+timedelta(minutes=90))
        self.client.force_login(self.admin)
    def accessibility_data(self,**extra):
        data={'text_size':'extra','contrast':'high','spacing':'on','large_targets':'on','reduce_motion':'on','simple':'on','audio':'on','speech_rate':'0.85'};data.update(extra);return data
    def test_preferences_personal_persistent_and_no_learning_changes(self):
        self.assertEqual(self.client.post('/accessibility/',self.accessibility_data()).status_code,302)
        self.admin.profile.refresh_from_db();self.teacher.profile.refresh_from_db()
        self.assertEqual(self.admin.profile.accessibility['text_size'],'extra');self.assertEqual(self.teacher.profile.accessibility,{})
        self.assertContains(self.client.get('/'),'a11y-contrast-high')
        self.client.logout();self.client.force_login(self.admin);self.assertContains(self.client.get('/accessibility/'),'a11y-large_targets')
        self.assertFalse(Learning.objects.exists());self.assertFalse(ChallengeProgress.objects.exists())
    def test_invalid_preferences_and_safe_classes(self):
        self.client.post('/accessibility/',self.accessibility_data(text_size='"><script>'))
        self.admin.profile.refresh_from_db();self.assertEqual(self.admin.profile.accessibility,{})
        self.assertEqual(preferences({'audio':'false','text_size':'bad','contrast':'high','unknown':'x'})['audio'],False)
        self.assertEqual(preferences([])['text_size'],'normal')
    def test_accessibility_auth_csrf_and_audio_only_static_text(self):
        self.client.logout();self.assertEqual(self.client.get('/accessibility/').status_code,302)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin);self.assertEqual(csrf.post('/accessibility/',self.accessibility_data()).status_code,403)
        self.client.force_login(self.admin);self.client.post('/accessibility/',self.accessibility_data())
        content=self.client.get(f'/students/{self.student.pk}/?tab=learning').content.decode()
        raw=re.search(r'<script id="audio-messages" type="application/json">(.*?)</script>',content).group(1)
        self.assertNotIn(self.student.name,json.dumps(json.loads(raw)))
    def practice_data(self,version=0,**extra):
        data={'version':version,'area':'games','reached_alpha':['R1','R2'],'reached_beta':[f'R{n}' for n in range(1,9)]};data.update(extra);return data
    def test_practice_separate_sqlite_and_no_educational_writes(self):
        before={m.__name__:list(m.objects.values()) for m in (Student,Session,Enrollment,Learning,ChallengeProgress,Resource)}
        self.assertContains(self.client.get('/practice/'),'Aprendiz ficticio A')
        self.assertEqual(self.client.post('/practice/',self.practice_data()).status_code,302)
        version,state=practice.read(self.admin.pk);self.assertEqual(version,1)
        self.assertEqual(len(state['students']['alpha']['games']),2);self.assertEqual(len(state['students']['beta']['games']),8)
        self.assertEqual(before,{m.__name__:list(m.objects.values()) for m in (Student,Session,Enrollment,Learning,ChallengeProgress,Resource)})
        with sqlite3.connect(Path(self.tmp.name)/'practice.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),[('practice_runs',)])
    def test_practice_ownership_and_no_real_student_identifiers(self):
        self.client.post('/practice/',self.practice_data(owner=self.teacher.pk,student=str(self.student.pk)))
        self.client.force_login(self.teacher)
        version,state=practice.read(self.teacher.pk);self.assertEqual(version,0);self.assertEqual(state['students']['alpha']['games'],[])
        self.client.post('/practice/',self.practice_data(reached_alpha=['R3'],reached_beta=[]))
        self.assertEqual(practice.read(self.admin.pk)[1]['students']['alpha']['games'],['R1','R2'])
        self.assertEqual(practice.read(self.teacher.pk)[1]['students']['alpha']['games'],['R3'])
    def test_practice_stale_version_and_invalid_choices(self):
        self.client.post('/practice/',self.practice_data())
        response=self.client.post('/practice/',self.practice_data(reached_alpha=['R8']))
        self.assertEqual(response.status_code,422);self.assertEqual(practice.read(self.admin.pk)[0],1)
        self.assertEqual(self.client.post('/practice/',self.practice_data(version=1,reached_alpha=['REAL-ID'])).status_code,422)
        self.assertEqual(practice.read(self.admin.pk)[0],1)
    def test_reset_confirmed_only_practice_and_other_user_unchanged(self):
        self.client.post('/practice/',self.practice_data())
        self.assertEqual(self.client.post('/practice/',{'action':'reset','version':1,'confirm':'NO'}).status_code,422)
        self.assertEqual(practice.read(self.admin.pk)[0],1)
        self.client.post('/practice/',{'action':'reset','version':1,'confirm':'REINICIAR'})
        self.assertEqual(practice.read(self.admin.pk)[1]['students']['alpha']['games'],[])
        self.assertTrue(Student.objects.filter(pk=self.student.pk).exists());self.assertTrue(Session.objects.filter(pk=self.session.pk).exists())
    def test_practice_rejects_primary_path_and_permissions(self):
        from django.conf import settings
        with override_settings(PRACTICE_DATABASE_PATH=settings.DATABASES['default']['NAME']):
            with self.assertRaises(ValidationError):practice.read(self.admin.pk)
        foreign_path=Path(self.tmp.name)/'foreign.sqlite3'
        with sqlite3.connect(foreign_path) as db:db.execute('CREATE TABLE core_student(id TEXT)')
        with override_settings(PRACTICE_DATABASE_PATH=foreign_path):
            with self.assertRaises(ValidationError):practice.read(self.admin.pk)
        self.client.force_login(self.dev);self.assertEqual(self.client.get('/practice/').status_code,403)
        self.client.logout();self.assertEqual(self.client.get('/practice/').status_code,302)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin);self.assertEqual(csrf.post('/practice/',self.practice_data()).status_code,403)
    def test_three_main_two_extra_blocks_and_snapshot_revision_counts(self):
        first=Learning.objects.create(student=self.student,session=self.session,author=self.teacher,challenge='Reto',learning_status='supported')
        revised=Learning.objects.create(student=self.student,session=self.session,author=self.teacher,challenge='Reto revisado',supersedes=first,learning_status='autonomous')
        specs=[{'id':f'R{n}','title':'Reto ficticio'} for n in range(1,9)]
        previous=ChallengeProgress.objects.create(student=self.student,session=self.session,author=self.teacher,content_area='games',reached=['R1'],specs=specs)
        latest=ChallengeProgress.objects.create(student=self.student,session=self.session,author=self.teacher,content_area='games',reached=['R1','R2'],specs=specs,supersedes=previous)
        items=board([first,revised],[previous,latest]);games=next(b for b in items if b['key']=='games')
        self.assertEqual(sum(not b['extra'] for b in items),3);self.assertEqual(sum(b['extra'] for b in items),2)
        self.assertEqual(games['count'],2);self.assertEqual(games['total'],8);self.assertEqual(games['observations'],1)
        self.assertEqual(first.content_area,'games');self.session.content_area='robotics';self.session.save()
        first.refresh_from_db();latest.refresh_from_db();self.assertEqual(first.content_area,'games');self.assertEqual(latest.content_area,'games')
    def test_board_scoped_and_unassigned_legacy_not_reclassified(self):
        self.session.content_area='';self.session.save()
        legacy=Learning.objects.create(student=self.student,session=self.session,author=self.teacher,challenge='Antiguo')
        self.session.content_area='robotics';self.session.save();legacy.refresh_from_db();self.assertEqual(legacy.content_area,'')
        stranger=Session.objects.create(group=self.foreign,teacher=self.other,title='NO_MOSTRAR_OTRO_GRUPO',content_area='games',start=self.session.start,end=self.session.end)
        Learning.objects.create(student=self.student,session=stranger,author=self.other,challenge='NO_MOSTRAR_OTRO_RETO')
        self.client.force_login(self.teacher)
        response=self.client.get(f'/students/{self.student.pk}/?tab=learning')
        self.assertContains(response,'Diseño e impresión 3D');self.assertContains(response,'Sin bloque asignado')
        self.assertNotContains(response,'NO_MOSTRAR_OTRO_RETO')
        response=self.client.get(f'/students/{self.student.pk}/?tab=learning&area=games');self.assertNotContains(response,'Antiguo')
        self.assertEqual(self.client.get(f'/students/{self.student.pk}/?tab=learning&area=invalid').status_code,200)

    def test_class_save_freezes_content_area_for_each_revision(self):
        self.session.challenge_specs=[{'id':f'R{n}','title':f'Reto ficticio {n}','hint':'','criteria':''} for n in range(1,9)];self.session.save()
        key=str(self.student.pk)
        data={'version':1,'track_'+key:'1','reached_'+key:['R1'],'record_'+key:'1','challenge_'+key:'Reto ficticio','learning_'+key:'progress','state_'+key:'progress'}
        self.assertEqual(self.client.post(f'/sessions/{self.session.pk}/save/',data).status_code,302)
        first=ChallengeProgress.objects.get();learning=Learning.objects.get();self.assertEqual(first.content_area,'games');self.assertEqual(learning.content_area,'games')
        self.session.refresh_from_db();self.session.content_area='robotics';self.session.save()
        data.update(version=self.session.version,**{'progress_version_'+key:str(first.pk),'reached_'+key:['R1','R2']})
        self.assertEqual(self.client.post(f'/sessions/{self.session.pk}/save/',data).status_code,302)
        first.refresh_from_db();learning.refresh_from_db();self.assertEqual(first.content_area,'games');self.assertEqual(learning.content_area,'games')
        self.assertEqual(ChallengeProgress.objects.exclude(pk=first.pk).get().content_area,'robotics')

    def test_word_import_explicit_content_area(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from core.test_importing import document
        response=self.client.post('/imports/',{'kind':'word','file':SimpleUploadedFile('ficticio.docx',document())})
        url=response.url;tomorrow=(timezone.localdate()+timedelta(days=1)).isoformat()
        options={'action':'review','group':str(self.group.pk),'teacher':self.teacher.pk,'content_area':'games','title':'Word ficticio por bloque','number':3,'start':tomorrow+'T10:00','duration':90}
        self.assertContains(self.client.post(url,options),'value="confirm"')
        self.client.post(url,{'action':'confirm'})
        self.assertEqual(Session.objects.get(title='Word ficticio por bloque').content_area,'games')
