from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import Profile,AcademicYear,ClassGroup,Student,Enrollment,Session,ChallengeProgress,Learning,SupportPlan,Audit,Attendance
from core.challenges import tier_for,specs_for,extract_challenges


def eight_specs():
    return [{'id':f'R{n}','title':f'Consigna ficticia {n}','hint':'Pista ficticia','criteria':'Observar la acción'} for n in range(1,9)]


class ChallengeAndSupportTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user('admin');Profile.objects.create(user=self.admin,role='admin',sensitive_access=True)
        self.teacher=User.objects.create_user('docente');Profile.objects.create(user=self.teacher)
        self.other=User.objects.create_user('otro');Profile.objects.create(user=self.other,sensitive_access=True)
        self.dev=User.objects.create_user('desarrollo');Profile.objects.create(user=self.dev,role='developer',development_access=True,sensitive_access=True)
        self.today=timezone.localdate()
        year=AcademicYear.objects.create(name='Ficticio',starts=self.today-timedelta(days=10),ends=self.today+timedelta(days=100))
        self.group=ClassGroup.objects.create(name='Grupo ficticio',year=year,kind='initial',starts=year.starts,ends=year.ends)
        self.group.teachers.add(self.teacher)
        self.a=Student.objects.create(name='Ficticio A',joined=self.today)
        self.b=Student.objects.create(name='Ficticio B',joined=self.today)
        for student in (self.a,self.b):Enrollment.objects.create(student=student,group=self.group,starts=self.today)
        start=timezone.now().replace(hour=16,minute=30,second=0,microsecond=0)
        self.session=Session.objects.create(group=self.group,teacher=self.teacher,title='Sesión ficticia',start=start,end=start+timedelta(minutes=90),challenge_specs=eight_specs())
        self.url=f'/sessions/{self.session.pk}/'
        self.client.force_login(self.admin)
    def post_data(self,**extra):
        self.session.refresh_from_db()
        data={'version':self.session.version,'draft':'1'};data.update(extra);return data
    def test_thresholds_and_different_individual_paces(self):
        self.assertEqual([tier_for(i,8) for i in range(9)],['common','common','uncommon','uncommon','rare','rare','epic','epic','legendary'])
        data=self.post_data(**{f'track_{self.a.pk}':'1',f'reached_{self.a.pk}':['R1','R2'],f'track_{self.b.pk}':'1',f'reached_{self.b.pk}':[f'R{n}' for n in range(1,9)]})
        self.assertEqual(self.client.post(self.url+'save/',data).status_code,302)
        self.assertEqual(len(ChallengeProgress.objects.get(student=self.a).reached),2)
        self.assertEqual(len(ChallengeProgress.objects.get(student=self.b).reached),8)
        self.assertEqual(Learning.objects.count(),0)
        page=self.client.get(self.url);self.assertContains(page,'data-challenge-count>2</span>/8');self.assertContains(page,'data-challenge-count>8</span>/8')
    def test_append_revision_history_and_stale_version(self):
        key=str(self.a.pk)
        self.client.post(self.url+'save/',self.post_data(**{'track_'+key:'1','reached_'+key:['R1','R2']}))
        first=ChallengeProgress.objects.get()
        data=self.post_data(**{'track_'+key:'1','reached_'+key:['R1'],'progress_version_'+key:str(first.pk)})
        self.assertEqual(self.client.post(self.url+'save/',data).status_code,302)
        self.assertEqual(ChallengeProgress.objects.count(),2)
        latest=ChallengeProgress.objects.exclude(pk=first.pk).get();self.assertEqual(latest.supersedes,first)
        first.refresh_from_db();self.assertEqual(first.reached,['R1','R2'])
        response=self.client.post(self.url+'save/',self.post_data(**{'track_'+key:'1','reached_'+key:['R8'],'progress_version_'+key:str(first.pk)}))
        self.assertEqual(response.status_code,422);self.assertEqual(ChallengeProgress.objects.count(),2)
        failed=self.client.post(self.url+'save/',self.post_data(**{'track_'+key:'1','progress_version_'+key:str(latest.pk),'close':'1'}))
        self.assertEqual(failed.status_code,422)
        self.assertEqual(failed.context['draft_values']['reached_'+key],[])
        self.assertEqual(ChallengeProgress.objects.count(),2)
        self.assertContains(self.client.get(f'/students/{self.a.pk}/?tab=learning'),'Historial de retos alcanzados')
    def test_invalid_ids_atomic_and_csrf_scope(self):
        data=self.post_data(**{f'track_{self.a.pk}':'1',f'reached_{self.a.pk}':['R1'],f'track_{self.b.pk}':'1',f'reached_{self.b.pk}':['R99']})
        self.assertEqual(self.client.post(self.url+'save/',data).status_code,422)
        self.assertFalse(ChallengeProgress.objects.exists())
        self.client.force_login(self.other);self.assertEqual(self.client.post(self.url+'save/',data).status_code,404)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin)
        self.assertEqual(csrf.post(self.url+'save/',data).status_code,403)
    def test_legacy_extraction_and_editor_preserves_history(self):
        text='Retos desbloqueables\nR1\nConsigna uno\nPista uno\nCriterio uno\nR2\nConsigna dos\nPista dos\nCriterio dos\nAtención a la diversidad\nApoyo general'
        self.session.challenge_specs=[];self.session.resource_snapshot={'source_text':text};self.session.save()
        self.assertEqual(len(specs_for(self.session)),2)
        self.client.post(self.url+'save/',self.post_data(**{f'track_{self.a.pk}':'1',f'reached_{self.a.pk}':['R1']}))
        self.session.refresh_from_db();self.assertEqual(len(self.session.challenge_specs),2)
        data={'version':self.session.version,'form-TOTAL_FORMS':'1','form-INITIAL_FORMS':'0','form-0-title':'Cambiar'}
        self.assertContains(self.client.post(self.url+'challenges/',data),'Los retos ya tienen seguimiento')
        self.session.refresh_from_db();self.assertEqual(self.session.challenge_specs[0]['title'],'Consigna uno')
    def test_edit_challenges_without_progress_and_optimistic_lock(self):
        data={'version':self.session.version,'form-TOTAL_FORMS':'1','form-INITIAL_FORMS':'0','form-0-title':'Reto editado','form-0-hint':'Pista','form-0-criteria':'Criterio'}
        self.assertEqual(self.client.post(self.url+'challenges/',data).status_code,302)
        self.session.refresh_from_db();self.assertEqual(self.session.challenge_specs[0]['title'],'Reto editado')
        self.assertContains(self.client.post(self.url+'challenges/',data),'La sesión ha cambiado')
        data.update(version=self.session.version,**{'form-0-title':'','form-0-hint':'','form-0-criteria':''})
        self.assertEqual(self.client.post(self.url+'challenges/',data).status_code,302)
        self.session.refresh_from_db();self.assertEqual(specs_for(self.session),[])
    def support_data(self,**extra):
        data={'active':'on','adaptation_kind':'curricular','neae_reported':'on','nature':'reported','source':'Fuente ficticia','relevance':'Finalidad ficticia','support':'APOYO_RESTRINGIDO_FICTICIO','review':(self.today+timedelta(days=30)).isoformat(),'previous':''};data.update(extra);return data
    def test_support_permissions_no_leak_and_revision(self):
        url=f'/students/{self.a.pk}/support/'
        self.assertEqual(self.client.post(url,self.support_data()).status_code,302)
        first=SupportPlan.objects.get()
        self.assertContains(self.client.get(self.url),'APOYO_RESTRINGIDO_FICTICIO')
        self.assertNotContains(self.client.get('/reports/',{'student':str(self.a.pk),'format':'csv','section':'support'}),'APOYO_RESTRINGIDO_FICTICIO')
        exported=self.client.post(f'/students/{self.a.pk}/export/',{'confirm':'EXPORTAR'}).json()
        self.assertNotIn('support_plans',exported)
        exported=self.client.post(f'/students/{self.a.pk}/export/',{'confirm':'EXPORTAR','sensitive':'1'}).json()
        self.assertEqual(len(exported['support_plans']),1)
        self.assertTrue(Audit.objects.filter(action='support:read',object_id=str(self.a.pk)).exists())
        self.client.force_login(self.teacher)
        self.assertNotContains(self.client.get(self.url),'APOYO_RESTRINGIDO_FICTICIO')
        self.assertNotContains(self.client.get(self.url),'Adaptación educativa acordada')
        self.assertEqual(self.client.get(url).status_code,403)
        self.assertEqual(self.client.post(url,self.support_data()).status_code,403)
        self.client.force_login(self.other);self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.dev);self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(url,self.support_data(active='',previous=str(first.pk))).status_code,302)
        self.assertEqual(SupportPlan.objects.count(),2)
        self.assertNotContains(self.client.get(self.url),'APOYO_RESTRINGIDO_FICTICIO')
        self.assertEqual(self.client.post(url,self.support_data(previous=str(first.pk))).status_code,200)
        self.assertEqual(SupportPlan.objects.count(),2)
    def test_neae_not_inferred_from_observation(self):
        response=self.client.post(f'/students/{self.a.pk}/support/',self.support_data(nature='unverified'))
        self.assertEqual(response.status_code,200);self.assertFalse(SupportPlan.objects.exists())
    def test_delete_only_single_empty_session_admin_confirmation(self):
        other=Session.objects.create(group=self.group,teacher=self.teacher,title='Conservar',start=self.session.start+timedelta(days=7),end=self.session.end+timedelta(days=7),series=self.session.series)
        self.assertEqual(self.client.post(self.url+'delete/',{'confirm':'no','version':1}).status_code,200)
        self.assertTrue(Session.objects.filter(pk=self.session.pk).exists())
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.post(self.url+'delete/',{'confirm':'ELIMINAR','version':1}).status_code,403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.url+'delete/',{'confirm':'ELIMINAR','version':1}).status_code,302)
        self.assertTrue(Session.objects.filter(pk=other.pk).exists());self.assertEqual(Student.objects.count(),2)
        self.assertTrue(Audit.objects.filter(action='session:delete',object_id=str(self.session.pk)).exists())
    def test_deletion_blocked_by_attendance_progress_and_concurrent_edit(self):
        Attendance.objects.create(session=self.session,student=self.a,status='present')
        self.client.post(self.url+'delete/',{'confirm':'ELIMINAR','version':1});self.assertTrue(Session.objects.filter(pk=self.session.pk).exists())
        Attendance.objects.all().delete()
        self.session.version=2;self.session.save()
        self.client.post(self.url+'delete/',{'confirm':'ELIMINAR','version':1});self.assertTrue(Session.objects.filter(pk=self.session.pk).exists())
        ChallengeProgress.objects.create(session=self.session,student=self.a,author=self.admin,reached=['R1'],specs=eight_specs())
        self.client.post(self.url+'delete/',{'confirm':'ELIMINAR','version':2});self.assertTrue(Session.objects.filter(pk=self.session.pk).exists())
