import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('repro_preparar', Path(__file__).parents[1] / 'preparar.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / 'checkout'
        self.target.mkdir()
        self.zip = self.root / 'datos.zip'
        self.body = b'immutable dataset'
        self.package = {'files': [{'path': 'Datos/foto.jpg', 'bytes': len(self.body),
                                  'sha256': hashlib.sha256(self.body).hexdigest()}]}

    def archive(self, entries=None):
        with zipfile.ZipFile(self.zip, 'w') as z:
            for name, body in entries or [('Datos/foto.jpg', self.body)]:
                z.writestr(name, body)

    def test_install_is_idempotent_and_detects_changed_local_data(self):
        self.archive()
        self.assertEqual(prepare.install_archive(self.zip, self.package, self.target), 1)
        self.assertEqual(prepare.install_archive(self.zip, self.package, self.target), 0)
        (self.target / 'Datos/foto.jpg').write_bytes(b'my work')
        with self.assertRaisesRegex(ValueError, 'local diferente'):
            prepare.install_archive(self.zip, self.package, self.target)
        self.assertEqual((self.target / 'Datos/foto.jpg').read_bytes(), b'my work')

    def test_modified_archive_is_rejected_before_any_write(self):
        self.archive([('Datos/foto.jpg', b'x' * len(self.body))])
        with self.assertRaisesRegex(ValueError, 'modificado'):
            prepare.install_archive(self.zip, self.package, self.target)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_unlisted_files_and_duplicate_entries_are_rejected(self):
        self.archive([('Datos/foto.jpg', self.body), ('extra.py', b'code')])
        with self.assertRaises(ValueError):
            prepare.install_archive(self.zip, self.package, self.target)
        self.archive([('Datos/foto.jpg', self.body), ('Datos/foto.jpg', self.body)])
        with self.assertRaises(ValueError):
            prepare.install_archive(self.zip, self.package, self.target)

    def test_traversal_windows_paths_and_symlink_parents_are_rejected(self):
        for name in ('../outside', '/absolute', 'C:/private', 'Datos/../code', 'Datos\\file', './file'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                prepare.safe_path(self.target, name)

    def test_archive_digest_is_checked_even_when_using_local_assets(self):
        self.archive()
        item = {'file': self.zip.name, 'bytes': self.zip.stat().st_size, 'sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'modificado'):
            prepare.get_archive(item, self.root, self.target)

    def test_standalone_package_can_install_in_an_explicit_subdirectory(self):
        self.archive()
        package = {**self.package, 'destination': 'Entregables'}
        prepare.install_archive(self.zip, package, self.target)
        self.assertEqual((self.target / 'Entregables/Datos/foto.jpg').read_bytes(), self.body)
        prepare.verify_files(package, self.target)

    def test_development_package_without_remote_url_requests_local_assets(self):
        item = {'file': 'datos.zip', 'bytes': 1, 'sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'Release pública contiene solo Walmart Visión'):
            prepare.get_archive(item, None, self.target)


if __name__ == '__main__':
    unittest.main()
