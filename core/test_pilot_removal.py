import tempfile
from pathlib import Path
from django.test import SimpleTestCase
from scripts.remove_pilot_data import inventory, remove, RemovalBlocked, CONFIRMATION


class PilotRemovalTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'app'; self.root.mkdir()
        self.data = self.root / 'var'; self.data.mkdir()
        self.code = self.root / 'manage.py'; self.code.write_text('preserve code')
        self.secret = Path(self.tmp.name) / 'secret'; self.secret.write_text('preserve secret')
        for name in ('demo.sqlite3', 'demo.sqlite3-wal', 'production.sqlite3', 'private/demo/test.pdf', 'backups/demo/database.sqlite3', 'practice/demo.sqlite3', 'security/production.json'):
            path = self.data / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'synthetic fixture only')

    def test_inventory_reads_no_contents_and_changes_nothing(self):
        before = {p: p.read_bytes() for p in self.data.rglob('*') if p.is_file()}
        self.assertEqual(inventory(self.root, {})[1], 7)
        self.assertEqual(before, {p: p.read_bytes() for p in self.data.rglob('*') if p.is_file()})

    def test_removes_all_runtime_files_but_preserves_code_and_external_secret(self):
        self.assertEqual(remove(self.root, {}, confirm=CONFIRMATION, site_disabled=True), 7)
        self.assertEqual(list(self.data.iterdir()), [])
        self.assertEqual(self.code.read_text(), 'preserve code')
        self.assertEqual(self.secret.read_text(), 'preserve secret')
        self.assertEqual(self.data.stat().st_mode & 0o777, 0o700)
        self.assertEqual(remove(self.root, {}, confirm=CONFIRMATION, site_disabled=True), 0)

    def test_no_confirmation_or_stopped_site_declaration_never_deletes(self):
        for values in ({}, {'confirm': 'wrong', 'site_disabled': True}, {'confirm': CONFIRMATION}):
            with self.assertRaises(RemovalBlocked): remove(self.root, {}, **values)
            self.assertEqual(inventory(self.root, {})[1], 7)

    def test_external_paths_block_before_any_deletion(self):
        for key in ('DATABASE_PATH', 'PRIVATE_MEDIA_ROOT', 'PRACTICE_DATABASE_PATH'):
            with self.assertRaises(RemovalBlocked): remove(self.root, {key: str(self.secret)}, confirm=CONFIRMATION, site_disabled=True)
        self.assertEqual(inventory(self.root, {})[1], 7)

    def test_symlink_within_var_and_var_itself_never_followed(self):
        link = self.data / 'link'; link.symlink_to(self.secret)
        with self.assertRaises(RemovalBlocked): remove(self.root, {}, confirm=CONFIRMATION, site_disabled=True)
        self.assertTrue((self.data / 'demo.sqlite3').exists())
        self.assertEqual(self.secret.read_text(), 'preserve secret')
        link.unlink()
        root = Path(self.tmp.name) / 'other'; root.mkdir(); (root / 'var').symlink_to(self.data, target_is_directory=True)
        with self.assertRaises(RemovalBlocked): remove(root, {}, confirm=CONFIRMATION, site_disabled=True)

    def test_missing_var_is_safe_noop_without_creating_database(self):
        root = Path(self.tmp.name) / 'empty'; root.mkdir()
        self.assertEqual(remove(root, {}, confirm=CONFIRMATION, site_disabled=True), 0)
        self.assertFalse((root / 'var').exists())
