"""Integridad, fuente del paquete y conservación de los documentos académicos."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import empaquetar
import verificar


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name) / 'producto'
        cls.root.mkdir()
        for name in verificar.git_files():
            destination = cls.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(verificar.ROOT / name, destination)
        def git(*args):
            return subprocess.check_output(['git', '-C', str(cls.root), *args], stderr=subprocess.STDOUT)
        git('init', '-q')
        git('config', 'core.autocrlf', 'false')
        git('config', 'user.name', 'Prueba local de distribución')
        git('config', 'user.email', 'test@example.invalid')
        git('add', '--all')
        git('-c', 'core.hooksPath=', 'commit', '-qm', 'Fixture del producto')
        cls.commit = git('rev-parse', 'HEAD').decode().strip()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_package_has_one_verified_model_and_relocatable_guides(self):
        output = Path(self.temporary.name) / 'apps.zip'
        result = empaquetar.build(output, self.root)
        with self.assertRaisesRegex(ValueError, 'ya existe'):
            empaquetar.build(output, self.root)
        self.assertEqual(result['source_commit'], self.commit)
        prefix = empaquetar.PACKAGE_ROOT + '/'
        with zipfile.ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            self.assertEqual(len([n for n in names if n.endswith('.pt')]), 1)
            self.assertFalse(any('/Laboratorio/' in n or '/Datos/' in n or '/Fase ' in n for n in names))
            for app in ('cliente', 'equipo'):
                self.assertIn(b'%~dp0', archive.read(prefix + 'iniciar_' + app + '.cmd'))
            source = json.loads(archive.read(prefix + 'FUENTE.json'))
            self.assertEqual(source['commit'], self.commit)
            self.assertTrue(source['working_tree_clean'])
            manifest = json.loads(archive.read(prefix + 'MANIFIESTO_SHA256.json'))
            for name, expected in manifest.items():
                self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), expected, name)
            extraction = Path(self.temporary.name) / 'extraido'
            archive.extractall(extraction)
        product = extraction / empaquetar.PACKAGE_ROOT
        names = [p.relative_to(product).as_posix() for p in product.rglob('*') if p.is_file()]
        self.assertGreater(verificar.verify_links(product, names), 0)
        self.assertEqual(verificar.verify_model(product)['id'], 'V3-cierre-revisado-20261110')
        for name in ('Aplicacion/inferencia.py', 'Aplicacion/modelos.json', 'Aplicacion_Cliente/app_cliente.py'):
            self.assertEqual((product / name).read_bytes(), (self.root / name).read_bytes())
        self.assertEqual(output.with_suffix('.sha256').read_text().split()[0], result['sha256'])

    def test_changed_engine_is_rejected(self):
        path = self.root / 'Aplicacion/ocupacion_linea_a.py'
        before = path.read_bytes()
        try:
            path.write_bytes(before + b'\n# altered\n')
            with self.assertRaisesRegex(ValueError, 'edge_sources'):
                verificar.verify_model(self.root)
        finally:
            path.write_bytes(before)

    def test_changed_weight_is_rejected(self):
        manifest = json.loads((self.root / 'Aplicacion/modelos.json').read_text())
        path = self.root / 'Aplicacion' / manifest['models'][0]['file']
        before = path.read_bytes()
        try:
            path.write_bytes(b'invalid weight')
            with self.assertRaisesRegex(ValueError, 'peso oficial'):
                verificar.verify_model(self.root)
        finally:
            path.write_bytes(before)

    def test_changed_academic_file_is_rejected(self):
        names = json.loads((self.root / 'Documentacion/Evidencias/integridad_academica.json').read_text())['files']
        path = self.root / next(iter(names))
        before = path.read_bytes()
        try:
            path.write_bytes(before + b'changed')
            with self.assertRaisesRegex(ValueError, 'académico protegido'):
                verificar.verify(self.root)
        finally:
            path.write_bytes(before)

    def test_dirty_checkout_cannot_claim_a_source_commit(self):
        path = self.root / 'Aplicacion/app.py'
        before = path.read_bytes()
        output = Path(self.temporary.name) / 'dirty.zip'
        try:
            path.write_bytes(before + b'\n# changed\n')
            with self.assertRaisesRegex(ValueError, 'clon limpio'):
                empaquetar.build(output, self.root)
            self.assertFalse(output.exists())
        finally:
            path.write_bytes(before)

    def test_escaping_path_and_broken_link_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Ruta inválida'):
            verificar.safe_file(self.root, '../outside')
        path = self.root / 'Documentacion/broken.md'
        try:
            path.write_text('[ausente](missing.md)\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Enlace sin archivo'):
                verificar.verify_links(self.root, ['Documentacion/broken.md'])
        finally:
            path.unlink(missing_ok=True)

    def test_secret_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'secreto'):
            verificar.secret_fields({'nested': {'access_token': 'test_value_not_a_credential'}})


if __name__ == '__main__':
    unittest.main()
