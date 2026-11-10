"""La entrega conjunta mantiene un solo modelo y funciona sin el laboratorio."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import empaquetar_apps_prueba as package


class CombinedPackageTests(unittest.TestCase):
    def test_shared_engine_client_and_launchers_survive_relocation(self):
        def fake_team(output, *, v3):
            self.assertTrue(v3)
            with zipfile.ZipFile(output, 'w') as archive:
                archive.writestr('Walmart_Vision/modelos/current.pt', b'official weight')
                archive.writestr('Walmart_Vision/app.py', b'# shared engine')

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'apps.zip'
            with patch.object(package, 'build_team', fake_team):
                result = package.build(output)
                with self.assertRaisesRegex(ValueError, 'ya existe'):
                    package.build(output)
            with zipfile.ZipFile(output) as archive:
                prefix = package.PACKAGE_ROOT + '/'
                names = archive.namelist()
                self.assertEqual(len([n for n in names if n.endswith('.pt')]), 1)
                self.assertIn(prefix + 'Aplicacion_Cliente/app_cliente.py', names)
                self.assertIn(prefix + 'Aplicacion/modelos/current.pt', names)
                self.assertFalse(any('/Laboratorio/' in n or '/Datos/' in n for n in names))
                manifest = json.loads(archive.read(prefix + 'MANIFIESTO_SHA256.json'))
                for name, digest in manifest.items():
                    self.assertEqual(hashlib.sha256(archive.read(prefix + name)).hexdigest(), digest)
                for app in ('cliente', 'equipo'):
                    launcher = archive.read(prefix + 'iniciar_' + app + '.cmd')
                    self.assertIn(b'%~dp0', launcher)
                    self.assertIn(b'\r\n', launcher)
            self.assertEqual(output.with_suffix('.sha256').read_text().split()[0], result['sha256'])


if __name__ == '__main__':
    unittest.main()
