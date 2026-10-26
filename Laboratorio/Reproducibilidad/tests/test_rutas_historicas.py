"""Instalar paquetes históricos con sus hashes sin recrear las carpetas retiradas."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preparar import install_archive, validate_archive


class HistoricalArchiveTests(unittest.TestCase):
    def test_verified_legacy_source_is_installed_in_current_application_folder(self):
        body = b'published source fixture'
        name = 'Herramientas/Demo_lite/fixture.txt'
        package = {'files': [{'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as stream:
                stream.writestr(name, body)
            self.assertEqual(install_archive(archive, package, root), 1)
            self.assertEqual((root / 'Aplicacion/fixture.txt').read_bytes(), body)
            self.assertFalse((root / 'Herramientas').exists())

    def test_distinct_archive_names_cannot_overwrite_the_same_mapped_destination(self):
        body = b'same fixture'
        names = ['Herramientas/Demo_lite/fixture.txt', 'Aplicacion/fixture.txt']
        package = {'files': [{'path': n, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()} for n in names]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as stream:
                for name in names:
                    stream.writestr(name, body)
            with self.assertRaisesRegex(ValueError, 'coinciden'):
                validate_archive(archive, package, root)
            self.assertFalse((root / 'Aplicacion').exists())
