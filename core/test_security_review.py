import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from django.test import TestCase, override_settings, Client
from django.contrib.auth.models import User
from django.core.management import call_command
from core.models import Profile, Audit, Student, Learning
from core.security_review import integrity, scan_evidence, runtime_checks, report_path
from core.management.commands.security_scan import run_scan, bandit_count, dependency_count


class SecurityReviewTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); (self.root / 'core').mkdir()
        (self.root / 'core' / 'example.py').write_text('x = 1\n')
        self.override = override_settings(BASE_DIR=self.root, ENVIRONMENT='testing')
        self.override.enable(); self.addCleanup(self.override.disable)
        self.dev = User.objects.create_user('security.dev')
        Profile.objects.create(user=self.dev, role='developer', development_access=True)
        self.admin = User.objects.create_user('security.admin', is_superuser=True)
        Profile.objects.create(user=self.admin, role='admin')
        self.client.force_login(self.dev)

    def manifest(self):
        call_command('security_manifest', verbosity=0)
        return integrity()

    def evidence(self, **kwargs):
        check = self.manifest()
        data = {'schema': 1, 'environment': 'testing', 'manifest_digest': check['digest'],
                'created_at': datetime.now(timezone.utc).isoformat(),
                'bandit': {'status': 'ok', 'count': 0}, 'dependencies': {'status': 'ok', 'count': 0}}
        data.update(kwargs)
        path = report_path(); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return check

    def test_permission_is_explicit_not_admin_or_superuser(self):
        self.client.logout(); self.assertEqual(self.client.get('/developer/security/').status_code, 302)
        self.client.force_login(self.admin); self.assertEqual(self.client.get('/developer/security/').status_code, 403)
        self.client.force_login(self.dev)
        response = self.client.get('/developer/security/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertTrue(Audit.objects.filter(actor=self.dev, action='security:view').exists())
        from core.access import students
        self.assertFalse(students(self.dev).exists())
        self.assertEqual(self.client.get('/reports/').status_code, 403)

    def test_dashboard_read_only_no_post_no_subprocess(self):
        before = (Student.objects.count(), Learning.objects.count())
        with patch('subprocess.run', side_effect=AssertionError('web execution forbidden')):
            self.assertEqual(self.client.get('/developer/security/').status_code, 200)
            csrf = Client(enforce_csrf_checks=True); csrf.force_login(self.dev)
            self.assertEqual(csrf.post('/developer/security/', {'command': 'whoami'}).status_code, 403)
            self.assertEqual(self.client.post('/developer/security/').status_code, 405)
        self.assertEqual(before, (Student.objects.count(), Learning.objects.count()))

    def test_integrity_modified_added_missing_symlink(self):
        self.assertEqual(integrity()['status'], 'unknown')
        self.assertEqual(self.manifest()['status'], 'ok')
        call_command('security_manifest', check=True)
        path = self.root / 'core' / 'example.py'; path.write_text('x = 2')
        self.assertEqual(integrity()['count'], 1)
        path.unlink(); self.assertEqual(integrity()['count'], 1)
        (self.root / 'core' / 'new.py').write_text('')
        self.assertEqual(integrity()['count'], 2)
        path.symlink_to('/etc/passwd'); self.assertEqual(integrity()['status'], 'unknown')

    def test_reports_fail_closed_stale_changed_env_corrupt(self):
        check = self.evidence(); self.assertTrue(scan_evidence(check)['available'])
        for extra in [
            {'created_at': (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()},
            {'created_at': datetime.now().isoformat()}, {'environment': 'production'},
            {'manifest_digest': 'wrong'}, {'bandit': {'status': '<script>', 'count': 0}},
            {'dependencies': {'status': 'ok', 'count': 'SECRET'}},
        ]:
            check = self.evidence(**extra); self.assertFalse(scan_evidence(check)['available'])
        self.evidence(); (self.root / 'core' / 'example.py').write_text('changed')
        self.assertFalse(scan_evidence(integrity())['available'])
        report_path().write_text('{broken'); self.assertFalse(scan_evidence(check)['available'])

    def test_report_unknown_status_not_clean_and_raw_secrets_never_rendered(self):
        self.evidence(bandit={'status': 'unknown', 'count': 0}, debug='SECRET_MARKER')
        response = self.client.get('/developer/security/')
        self.assertContains(response, 'No comprobado')
        self.assertNotContains(response, 'SECRET_MARKER')

    def test_runtime_flags_without_secret_disclosure(self):
        with override_settings(DEBUG=True, SECRET_KEY='NEVER_RENDER_SECRET', ALLOWED_HOSTS=['*'], SESSION_COOKIE_SECURE=False):
            self.assertGreaterEqual(sum(c['status'] == 'warning' for c in runtime_checks()), 4)
            self.client.force_login(self.dev)
            self.assertNotContains(self.client.get('/developer/security/'), 'NEVER_RENDER_SECRET')

    def test_scanner_errors_are_unknown_not_success(self):
        with patch('subprocess.run', side_effect=OSError('SECRET')):
            self.assertEqual(run_scan('bandit', [], bandit_count)['status'], 'unknown')
        with patch('subprocess.run') as run:
            run.return_value.stdout = b'{"results": [], "errors": []}'; run.return_value.returncode = 0
            self.assertEqual(run_scan('bandit', [], bandit_count)['status'], 'ok')
            run.return_value.returncode = 1
            self.assertEqual(run_scan('bandit', [], bandit_count)['status'], 'unknown')
        with self.assertRaises(ValueError): dependency_count({'dependencies': [{'skip_reason': 'missing'}]})

    def test_scan_command_aggregates_only_and_fails_on_findings(self):
        from django.core.management.base import CommandError
        self.manifest()
        with patch('core.management.commands.security_scan.run_scan', return_value={'status': 'warning', 'count': 2}):
            with self.assertRaises(CommandError): call_command('security_scan')
        data = json.loads(report_path().read_text())
        self.assertEqual(data['bandit']['count'], 2)
        self.assertNotIn('results', data)
        self.assertEqual(report_path().stat().st_mode & 0o777, 0o600)
