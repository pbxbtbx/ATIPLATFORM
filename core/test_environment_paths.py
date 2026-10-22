"""Load settings in isolation; never open a database or copy educational data."""
import os
import runpy
from pathlib import Path
from unittest.mock import patch
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parent.parent


class EnvironmentPathTests(SimpleTestCase):
    def load(self, **values):
        with patch.dict(os.environ, values, clear=True):
            return runpy.run_path(str(ROOT / 'config' / 'settings.py'))

    def test_production_keeps_explicit_database_media_and_practice(self):
        values = self.load(APP_ENV='production', DJANGO_SECRET_KEY='synthetic-test-only-' * 4,
                           DATABASE_PATH='/private/demo.sqlite3', PRIVATE_MEDIA_ROOT='/private/files/demo',
                           PRACTICE_DATABASE_PATH='/private/practice/demo.sqlite3')
        self.assertEqual(values['DATABASES']['default']['NAME'], '/private/demo.sqlite3')
        self.assertEqual(values['MEDIA_ROOT'], Path('/private/files/demo'))
        self.assertEqual(values['PRACTICE_DATABASE_PATH'], Path('/private/practice/demo.sqlite3'))
        self.assertFalse(values['DEBUG'])
        self.assertTrue(values['SESSION_COOKIE_SECURE'])
        self.assertTrue(values['CSRF_COOKIE_SECURE'])
        self.assertTrue(values['SECURE_SSL_REDIRECT'])

    def test_existing_defaults_unchanged_without_overrides(self):
        for environment in ('demo', 'testing', 'staging'):
            values = self.load(APP_ENV=environment)
            self.assertEqual(values['MEDIA_ROOT'], ROOT / 'var' / 'private' / environment)
            self.assertEqual(values['PRACTICE_DATABASE_PATH'], ROOT / 'var' / 'practice' / (environment + '.sqlite3'))

    def test_production_still_rejects_placeholder_secret(self):
        with self.assertRaises(RuntimeError):
            self.load(APP_ENV='production')
