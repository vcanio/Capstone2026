"""La distribución usa el modelo adoptado y rechaza un peso alterado."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import empaquetar_demo_lite as package


class OfficialPackageTests(unittest.TestCase):
    def test_current_model_is_packaged_and_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in package.LEGAL_FILES:
                (root / name).write_text('License fixture for ' + name, encoding='utf-8')
            source = root / 'Aplicacion'
            (source / 'modelos').mkdir(parents=True)
            (source / 'herramientas').mkdir()
            (source / 'herramientas/fuente_uv.json').write_text('{"files": []}', encoding='utf-8')
            (source / 'app.py').write_text('# portable app\n', encoding='utf-8')
            body = b'new official checkpoint'
            weight = source / 'modelos/current.pt'
            weight.write_bytes(body)
            model = dict(id='current', file='modelos/current.pt', bytes=len(body),
                         sha256=hashlib.sha256(body).hexdigest(), classes=['Nivel'], source_run='new_run')
            manifest = dict(default_model='current', models=[model], edge_sources={})
            (source / 'modelos.json').write_text(json.dumps(manifest), encoding='utf-8')
            with patch.multiple(package, ROOT=root, SOURCE=source, FILES=('app.py',),
                                EDGE_FILES={}, SUPPORT_FILES={}):
                output = root / 'official.zip'
                package.build(output, v3=True)
                with zipfile.ZipFile(output) as archive:
                    self.assertEqual(archive.read('Walmart_Vision/modelos/current.pt'), body)
                    self.assertEqual(json.loads(archive.read('Walmart_Vision/modelos.json')), manifest)
                    self.assertEqual(len([p for p in archive.namelist() if p.endswith('.pt')]), 1)
                    for name in package.LEGAL_FILES:
                        self.assertEqual(archive.read('Walmart_Vision/' + name), (root / name).read_bytes())
                weight.write_bytes(b'wrong checkpoint')
                with self.assertRaisesRegex(ValueError, 'modelo oficial'):
                    package.build(root / 'invalid.zip', v3=True)


if __name__ == '__main__':
    unittest.main()
