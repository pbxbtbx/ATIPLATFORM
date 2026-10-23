import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.core.files.base import ContentFile
from core.models import *
from core.data_erasure import make_preview, erase_records, verify_files


class DataErasureTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.override = override_settings(BASE_DIR=root, MEDIA_ROOT=root/'var'/'private', ERASURE_ONLY=False)
        self.override.enable(); self.addCleanup(self.override.disable)
        self.password = 'Fictitious-test-password-325!'
        self.admin = User.objects.create_user('erasure.admin', password=self.password)
        Profile.objects.create(user=self.admin, role='admin', sensitive_access=True)
        self.other = User.objects.create_user('erasure.other', password=self.password)
        Profile.objects.create(user=self.other, role='admin', sensitive_access=True)
        self.teacher = User.objects.create_user('erasure.teacher'); Profile.objects.create(user=self.teacher)
        self.dev = User.objects.create_user('erasure.dev'); Profile.objects.create(user=self.dev, role='developer', development_access=True, sensitive_access=True)
        today = timezone.localdate()
        self.one = Student.objects.create(name='Ficticia para retirar', joined=today)
        self.keep = Student.objects.create(name='Ficticia conservada', joined=today)
        year = AcademicYear.objects.create(name='Ficticio', starts=today-timedelta(days=10), ends=today+timedelta(days=50))
        self.group = ClassGroup.objects.create(name='Ficticio', kind='initial', year=year, starts=year.starts, ends=year.ends)
        self.session = Session.objects.create(group=self.group, teacher=self.teacher, title='Ficticia', start=timezone.now(), end=timezone.now()+timedelta(hours=1))
        for person in (self.one, self.keep):
            Enrollment.objects.create(student=person, group=self.group, starts=today)
        self.exclusive = Guardian.objects.create(name='Contacto exclusivo ficticio')
        self.shared = Guardian.objects.create(name='Contacto compartido ficticio')
        GuardianLink.objects.create(student=self.one, guardian=self.exclusive)
        GuardianLink.objects.create(student=self.one, guardian=self.shared)
        GuardianLink.objects.create(student=self.keep, guardian=self.shared)
        first = Learning.objects.create(student=self.one, session=self.session, author=self.teacher, challenge='Primera')
        Learning.objects.create(student=self.one, session=self.session, author=self.teacher, supersedes=first, challenge='Segunda')
        Learning.objects.create(student=self.keep, session=self.session, author=self.teacher, challenge='Conservar')
        first = ChallengeProgress.objects.create(student=self.one, session=self.session, author=self.teacher)
        ChallengeProgress.objects.create(student=self.one, session=self.session, author=self.teacher, supersedes=first)
        first = SupportPlan.objects.create(student=self.one, author=self.teacher, review=today)
        SupportPlan.objects.create(student=self.one, author=self.teacher, review=today, supersedes=first)
        Attendance.objects.create(student=self.one, session=self.session, status='present')
        RestrictedNote.objects.create(student=self.one, author=self.teacher, kind='health', content='FICTICIO', review=today)
        Consent.objects.create(student=self.one, granted_at=today)
        self.evidence = Evidence.objects.create(student=self.one, session=self.session, author=self.teacher, title='Ficticia')
        self.evidence.file.save('synthetic.pdf', ContentFile(b'%PDF synthetic only'))
        self.file = Path(self.evidence.file.path)
        ImportDraft.objects.create(author=self.other, kind='ods', payload={'synthetic': 'draft only'})
        self.client.force_login(self.admin)

    def plan(self):
        return make_preview(self.admin, [str(self.one.pk)])[0]

    def erase(self, token=None):
        return erase_records(self.admin, token or self.plan(), self.password, 'ELIMINAR 1 ALUMNOS', True)

    def test_selected_graph_revisions_and_exclusive_contacts_removed_keep_unchanged(self):
        before = {m.__name__: list(m.objects.filter(student=self.keep).values()) for m in (Enrollment, Learning, GuardianLink)}
        token, counts, _ = make_preview(self.admin, [str(self.one.pk)])
        self.assertEqual(counts['guardians'], 1); self.assertEqual(counts['shared_guardians'], 1)
        receipt = verify_files(self.erase(token))
        self.assertFalse(Student.objects.filter(pk=self.one.pk).exists())
        self.assertFalse(Guardian.objects.filter(pk=self.exclusive.pk).exists())
        self.assertTrue(Guardian.objects.filter(pk=self.shared.pk).exists())
        self.assertFalse(ImportDraft.objects.exists())
        self.assertFalse(self.file.exists())
        self.assertEqual(receipt.checks, {'database': True, 'files': True})
        self.assertEqual(before, {m.__name__: list(m.objects.filter(student=self.keep).values()) for m in (Enrollment, Learning, GuardianLink)})
        self.assertTrue(Session.objects.filter(pk=self.session.pk).exists())
        self.assertNotIn(self.one.name, str(receipt.counts)+str(receipt.checks)+str(receipt.pending_files))
        self.assertTrue(Audit.objects.filter(action='privacy:erasure', object_id=str(receipt.pk)).exists())

    def test_wrong_password_confirmation_scope_and_stale_snapshot_no_deletion(self):
        token = self.plan()
        for password, phrase, accepted in [('wrong', 'ELIMINAR 1 ALUMNOS', True), (self.password, 'wrong', True), (self.password, 'ELIMINAR 1 ALUMNOS', False)]:
            with self.assertRaises(ValidationError): erase_records(self.admin, token, password, phrase, accepted)
            self.assertTrue(self.file.exists()); self.assertTrue(Student.objects.filter(pk=self.one.pk).exists())
        Learning.objects.create(student=self.one, session=self.session, author=self.teacher, challenge='Cambio')
        with self.assertRaises(ValidationError): self.erase(token)
        self.assertFalse(DataErasure.objects.exists())

    def test_cross_scope_revision_reference_rolls_back(self):
        selected = Learning.objects.filter(student=self.one).last()
        retained = Learning.objects.get(student=self.keep); retained.supersedes=selected; retained.save()
        with self.assertRaises(ProtectedError): self.erase()
        self.assertTrue(Student.objects.filter(pk=self.one.pk).exists())
        self.assertTrue(Guardian.objects.filter(pk=self.exclusive.pk).exists())
        self.assertTrue(self.file.exists()); self.assertFalse(DataErasure.objects.exists())

    def test_file_failure_is_pending_and_retry_verified(self):
        receipt = self.erase()
        with patch('core.data_erasure.default_storage.delete', side_effect=OSError('private details')):
            receipt = verify_files(receipt)
        self.assertFalse(receipt.checks['files']); self.assertTrue(receipt.pending_files)
        receipt = verify_files(receipt)
        self.assertTrue(receipt.checks['files']); self.assertEqual(receipt.pending_files, [])

    def test_shared_file_not_erased_and_symlink_outside_never_followed(self):
        Evidence.objects.create(student=self.keep, session=self.session, author=self.teacher, title='Ficticia compartida', file=self.evidence.file.name)
        receipt = verify_files(self.erase())
        self.assertFalse(receipt.checks['files']); self.assertTrue(self.file.exists())
        outside = Path(self.tmp.name)/'outside'; outside.write_text('preserve')
        self.file.unlink(); self.file.symlink_to(outside)
        Evidence.objects.filter(student=self.keep).delete()
        receipt = verify_files(receipt)
        self.assertFalse(receipt.checks['files']); self.assertEqual(outside.read_text(), 'preserve')

    def test_views_preview_get_no_mutation_receipt_owner_only_and_copies_pending(self):
        response = self.client.post('/privacy/erasure/', {'student': str(self.one.pk), 'action': 'preview'})
        self.assertContains(response, self.one.name)
        self.assertTrue(Student.objects.filter(pk=self.one.pk).exists())
        token = response.context['token']
        response = self.client.post('/privacy/erasure/', {'action':'erase', 'token':token, 'password':self.password, 'confirmation':'ELIMINAR 1 ALUMNOS', 'accept':'on'})
        self.assertEqual(response.status_code, 302)
        receipt = self.client.get(response['Location'])
        self.assertContains(receipt, 'pendiente de revisión externa')
        self.assertNotContains(receipt, self.one.name)
        self.assertIn('no-store', receipt['Cache-Control'])
        self.client.force_login(self.other); self.assertEqual(self.client.get(response['Location']).status_code, 404)
        with self.assertRaises(ValidationError): self.erase(token)

    def test_admin_sensitive_permission_login_and_csrf_required(self):
        for user in (self.teacher, self.dev):
            self.client.force_login(user); self.assertEqual(self.client.get('/privacy/erasure/').status_code, 403)
        self.admin.profile.sensitive_access=False; self.admin.profile.save()
        self.client.force_login(self.admin); self.assertEqual(self.client.get('/privacy/erasure/').status_code, 403)
        self.admin.profile.sensitive_access=True; self.admin.profile.save()
        csrf=Client(enforce_csrf_checks=True); csrf.force_login(self.admin)
        self.assertEqual(csrf.post('/privacy/erasure/', {'student':str(self.one.pk)}).status_code, 403)
        self.client.logout(); self.assertEqual(self.client.get('/privacy/erasure/').status_code, 302)

    @override_settings(ERASURE_ONLY=True)
    def test_restricted_mode_denies_other_users_and_routes(self):
        self.assertRedirects(self.client.get('/students/'), '/privacy/erasure/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/privacy/erasure/').status_code, 200)
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get('/students/').status_code, 403)
        self.assertEqual(self.client.get('/privacy/erasure/').status_code, 403)
        self.client.logout(); self.assertRedirects(self.client.get('/students/'), '/login/', fetch_redirect_response=False)

    def test_expired_tampered_and_other_actor_tokens_do_not_delete(self):
        from core.data_erasure import load_preview
        token = self.plan()
        with self.assertRaises(ValidationError): load_preview(self.other, token)
        with self.assertRaises(ValidationError): load_preview(self.admin, token+'x')
        with patch('django.core.signing.time.time', return_value=timezone.now().timestamp()+1000):
            with self.assertRaises(ValidationError): load_preview(self.admin, token)
        self.assertTrue(Student.objects.filter(pk=self.one.pk).exists())
        self.assertTrue(self.file.exists())

    def test_select_everyone_erases_shared_contacts_when_no_unselected_links_remain(self):
        token, counts, _ = make_preview(self.admin, [str(self.one.pk), str(self.keep.pk)])
        self.assertEqual(counts['guardians'], 2); self.assertEqual(counts['shared_guardians'], 0)
        receipt = erase_records(self.admin, token, self.password, 'ELIMINAR 2 ALUMNOS', True)
        receipt = verify_files(receipt)
        self.assertFalse(Student.objects.exists()); self.assertFalse(Guardian.objects.exists())
        self.assertTrue(receipt.checks['database']); self.assertTrue(receipt.checks['files'])
        backup = Path(self.tmp.name)/'var'/'backups'/'demo'/'database.sqlite3'
        backup.parent.mkdir(parents=True); backup.write_bytes(b'synthetic backup remains')
        response = self.client.get(f'/privacy/erasure/{receipt.pk}/')
        self.assertContains(response, 'pendiente de revisión externa')
        self.assertEqual(response.context['copies']['backup_files'], 1)
        self.assertTrue(backup.exists())
