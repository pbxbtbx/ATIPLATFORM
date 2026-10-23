from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Profile, Student, AcademicYear, ClassGroup, Enrollment, Audit, Session, Attendance, Learning, ChallengeProgress, Evidence, Guardian, GuardianLink


class EnrollmentCorrectionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('correction.admin'); Profile.objects.create(user=self.admin, role='admin')
        self.teacher = User.objects.create_user('correction.teacher'); Profile.objects.create(user=self.teacher, role='teacher')
        self.dev = User.objects.create_user('correction.dev'); Profile.objects.create(user=self.dev, role='developer', development_access=True)
        today = timezone.localdate()
        self.student = Student.objects.create(name='Persona ficticia', joined=today)
        self.year = AcademicYear.objects.create(name='Ficticio', starts=today-timedelta(days=30), ends=today+timedelta(days=60))
        self.group = ClassGroup.objects.create(name='Grupo erróneo', year=self.year, kind='initial', starts=self.year.starts, ends=self.year.ends)
        self.correct = ClassGroup.objects.create(name='Grupo correcto', year=self.year, kind='initial', starts=self.year.starts, ends=self.year.ends)
        self.enrollment = Enrollment.objects.create(student=self.student, group=self.group, starts=today)
        self.other = Enrollment.objects.create(student=self.student, group=self.correct, starts=today)
        self.guardian = Guardian.objects.create(name='Responsable ficticio')
        GuardianLink.objects.create(student=self.student, guardian=self.guardian)
        start = timezone.now()
        self.session = Session.objects.create(group=self.group, teacher=self.teacher, title='Ficticia', start=start, end=start+timedelta(hours=1))
        self.correct_session = Session.objects.create(group=self.correct, teacher=self.teacher, title='Ficticia correcta', start=start, end=start+timedelta(hours=1))
        self.url = f'/enrollments/{self.enrollment.pk}/remove-error/'
        self.client.force_login(self.admin)

    def post(self, **values):
        return self.client.post(self.url, {'confirm': 'RETIRAR', 'expected_version': str(self.enrollment.version), **values})

    def test_only_erroneous_enrollment_removed_other_history_preserved(self):
        Learning.objects.create(student=self.student, session=self.correct_session, author=self.teacher, challenge='Conservar')
        before = {m.__name__: list(m.objects.values()) for m in (Student, Guardian, GuardianLink, Learning, Session)}
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertTrue(Enrollment.objects.filter(pk=self.enrollment.pk).exists())
        self.assertEqual(self.post().status_code, 302)
        self.assertFalse(Enrollment.objects.filter(pk=self.enrollment.pk).exists())
        self.assertTrue(Enrollment.objects.filter(pk=self.other.pk).exists())
        self.assertEqual(before, {m.__name__: list(m.objects.values()) for m in (Student, Guardian, GuardianLink, Learning, Session)})
        audit = Audit.objects.get(action='enrollment:remove-error')
        self.assertEqual(audit.object_id, f'{self.student.pk}:{self.group.pk}')
        self.assertNotIn(self.student.name, audit.object_id)
        self.assertEqual(self.post().status_code, 404)

    def test_explicit_confirmation_and_version_required(self):
        for values in ({'confirm': ''}, {'expected_version': '0'}, {'expected_version': ''}):
            self.assertEqual(self.post(**values).status_code, 422)
            self.assertTrue(Enrollment.objects.filter(pk=self.enrollment.pk).exists())
        self.assertFalse(Audit.objects.filter(action='enrollment:remove-error').exists())

    def test_each_educational_record_blocks_correction(self):
        for model, fields in [(Attendance, {}), (Learning, {'author': self.teacher}), (ChallengeProgress, {'author': self.teacher}), (Evidence, {'author': self.teacher, 'title': 'Ficticia'})]:
            obj = model.objects.create(student=self.student, session=self.session, **fields)
            self.assertEqual(self.post().status_code, 422, model.__name__)
            self.assertTrue(Enrollment.objects.filter(pk=self.enrollment.pk).exists())
            obj.delete()

    def test_old_or_finished_enrollment_blocked(self):
        Enrollment.objects.filter(pk=self.enrollment.pk).update(created_at=timezone.now()-timedelta(hours=25))
        self.assertEqual(self.post().status_code, 422)
        Enrollment.objects.filter(pk=self.enrollment.pk).update(created_at=timezone.now(), ends=timezone.localdate())
        self.assertEqual(self.post().status_code, 422)

    def test_permissions_csrf_and_history_link(self):
        self.assertContains(self.client.get(f'/students/{self.student.pk}/'), 'Corregir matrícula errónea')
        for user in (self.teacher, self.dev):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.post().status_code, 403)
        csrf = Client(enforce_csrf_checks=True); csrf.force_login(self.admin)
        self.assertEqual(csrf.post(self.url, {'confirm': 'RETIRAR', 'expected_version': '1'}).status_code, 403)
        self.client.logout(); self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertTrue(Enrollment.objects.filter(pk=self.enrollment.pk).exists())
