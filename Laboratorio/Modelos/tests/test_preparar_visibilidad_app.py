import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import preparar_visibilidad_app as package


class PrepararVisibilidadAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = 'visibilidad_foto_20261102_150000_abcd'
        self.run_dir = self.root / 'Experimentos' / self.run
        self.run_dir.mkdir(parents=True)
        self.job = self.root / 'Experimentos/panel_pruebas/job'
        self.job.mkdir(parents=True)
        self.models = self.root / 'Aplicacion/modelos'
        self.models.mkdir(parents=True)
        (self.models / 'v3.pt').write_bytes(b'v3 sin cambios')
        self.base = self.root / 'base.pt'
        self.base.write_bytes(b'base')
        self.base_hash = hashlib.sha256(b'base').hexdigest()
        (self.run_dir / 'best.pt').write_bytes(b'candidato')
        self.ckpt_hash = hashlib.sha256(b'candidato').hexdigest()
        rows = [{'name': f'foto_{n}', 'split': 'val', 'etiqueta': 'apta' if n < 60 else 'no_apta'} for n in range(69)]
        snapshot = self.job / 'revision_visibilidad.json'
        snapshot.write_text(json.dumps({'images': rows}), encoding='utf-8')
        (self.job / 'estado.json').write_text(json.dumps({'state': 'done', 'config': {'run': self.run}}), encoding='utf-8')
        self.result = {'schema': 'visibilidad_foto_ensayo_v1', 'test_used': False,
                       'snapshot_sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                       'checkpoint_sha256': self.ckpt_hash, 'threshold': .8,
                       'validation': [{**r, 'score_apta': .9 if r['etiqueta'] == 'apta' else .1,
                                       'decision': r['etiqueta']} for r in rows]}

    def run_prepare(self):
        (self.run_dir / 'resultado.json').write_text(json.dumps(self.result), encoding='utf-8')
        with patch.object(package, 'ROOT', self.root), patch.object(package, 'WEIGHT', self.base), \
             patch.object(package, 'WEIGHT_SHA256', self.base_hash):
            return package.prepare(self.run)

    def test_prepara_solo_modo_experimental_y_conserva_v3(self):
        result = self.run_prepare()
        self.assertTrue(result['experimental'])
        self.assertEqual((self.models / 'v3.pt').read_bytes(), b'v3 sin cambios')
        self.assertTrue((self.models / 'visibilidad_experimental.json').is_file())

    def test_rechaza_candidato_que_acepta_obstruccion(self):
        self.result['validation'][-1]['score_apta'] = .9
        self.result['validation'][-1]['decision'] = 'apta'
        with self.assertRaisesRegex(ValueError, 'criterios'):
            self.run_prepare()
        self.assertFalse((self.models / 'visibilidad_experimental.json').exists())
