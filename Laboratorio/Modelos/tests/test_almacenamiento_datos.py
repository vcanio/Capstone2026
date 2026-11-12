"""Exact catalog authorization, integrity and portable/disconnected storage."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import almacenamiento_datos as storage


class ExternalStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        self.data = Path(self.temp.name) / 'external'
        self.root.mkdir()
        self.data.mkdir()
        self.ref = 'Datos/Preparados/a/images/train/same.png'
        self.add_file(self.ref, 'Exportaciones/a/same.png', b'one')
        self.env = patch.dict('os.environ', {'WALMART_DATA_ROOT': str(self.data)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def add_file(self, ref, target, content):
        path = self.data / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        file = self.root / storage.CATALOG
        value = json.loads(file.read_text()) if file.is_file() else {'schema_version': 1, 'archivos': {}}
        value['archivos'][ref] = dict(externa=target, bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(value))

    def test_reads_without_original_and_verifies_bytes(self):
        self.assertEqual(storage.read_path(self.root, self.ref, verify=True).read_bytes(), b'one')
        (self.data / 'Exportaciones/a/same.png').write_bytes(b'two')
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            storage.read_path(self.root, self.ref, verify=True)

    def test_colliding_names_remain_independent(self):
        other = 'Datos/Preparados/b/images/train/same.png'
        self.add_file(other, 'Exportaciones/b/same.png', b'two')
        self.assertEqual(storage.read_path(self.root, self.ref).read_bytes(), b'one')
        self.assertEqual(storage.read_path(self.root, other).read_bytes(), b'two')

    def test_rejects_traversal_and_absolute_paths(self):
        for ref in ('../secret', '/secret', 'E:/secret', 'Datos/../secret', 'Datos\\secret'):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                storage.read_path(self.root, ref)
        self.assertFalse(storage.authorized(self.root, self.root / self.ref, self.root / 'Experimentos'))
        self.assertFalse(storage.authorized(self.root, self.data / 'secret', self.data))

    def test_disk_unavailable_explains_missing_dataset(self):
        with patch.dict('os.environ', {'WALMART_DATA_ROOT': str(self.data / 'unplugged')}):
            with self.assertRaisesRegex(FileNotFoundError, 'Dataset no disponible'):
                storage.read_path(self.root, self.ref)

    def test_external_reparse_escape_and_invalid_catalog_are_rejected(self):
        real = Path.resolve
        with patch.object(Path, 'resolve', lambda p, *a, **kw: self.data.parent / 'secret' if p.name == 'same.png' else real(p, *a, **kw)):
            with self.assertRaisesRegex(ValueError, 'sale de la raíz'):
                storage.read_path(self.root, self.ref)
        file = self.root / storage.CATALOG
        value = json.loads(file.read_text())
        value['archivos'][self.ref]['externa'] = '../secret'
        file.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            storage.read_path(self.root, self.ref)

    def test_local_data_works_without_external_drive(self):
        path = self.root / self.ref
        path.parent.mkdir(parents=True)
        path.write_bytes(b'one')
        with patch.dict('os.environ', {'WALMART_DATA_ROOT': str(self.data / 'unplugged')}):
            self.assertEqual(storage.read_path(self.root, self.ref, verify=True).read_bytes(), b'one')

    def test_panel_only_exposes_explicitly_authorized_catalog_files(self):
        import panel_modelos as panel
        with patch.object(panel,'ROOT',self.root), patch.object(panel,'inventory',return_value=[]), patch.object(panel.datasets,'package_inventory',return_value={}):
            self.assertIsNone(panel.allowed_file(self.ref))
            file=self.root/storage.CATALOG
            value=json.loads(file.read_text())
            value['archivos'][self.ref]['panel']=True
            file.write_text(json.dumps(value))
            self.assertEqual(panel.allowed_file(self.ref),self.data/'Exportaciones/a/same.png')
            for ref in ('E:/secret.png',str(self.data/'Exportaciones/a/same.png'),'../secret.png',self.ref+'x'):
                self.assertIsNone(panel.allowed_file(ref))


if __name__ == '__main__':
    unittest.main()
