"""Las fotos adicionales usan anotaciones revisadas y nunca entrenamiento/reserva."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import panel_modelos as panel
from evaluar_desarrollo import development_records, verified_image
from particion_niveles import load_partition
import test_niveles_v2 as fixtures


class DevelopmentEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.V2Tests.setUpClass()
        cls.snapshot = copy.deepcopy(fixtures.V2Tests.snapshot)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.write('snapshot_cvat.json', self.snapshot)
        binding = load_partition(panel.ROOT)['binding']
        self.write('particion.json', {'validation_ids': [], 'fixed_partition': binding})
        self.write('manifest.json', {'version_datos': 'fixture', 'criterion': {'stage': 'base'},
                                    'clases': ['Nivel_reponer', 'Nivel_suficiente'],
                                    'partition_binding': binding})
        self.write('version_datos.json', {'id': 'fixture', 'state': 'lista_niveles',
            'review': {'reviewer': 'Prueba'}, 'snapshot_sha256': self.hash('snapshot_cvat.json'),
            'partition_sha256': self.hash('particion.json')})

    def write(self, name, value):
        (self.run / name).write_text(json.dumps(value), encoding='utf-8')

    def hash(self, name):
        return hashlib.sha256((self.run / name).read_bytes()).hexdigest()

    def test_all_forty_photos_are_reviewed_and_outside_training_and_reserve(self):
        records = development_records(self.run)
        self.assertEqual(len(records), 40)
        self.assertEqual(sum(p['split'] == 'diagnostico' for p in records), 30)
        self.assertTrue(all(p['truth_rows'] for p in records))
        expected = {p['archivo'] for p in load_partition(panel.ROOT)['records'].values()
                    if p['effective_split'] in ('val', 'diagnostico')}
        self.assertEqual({'Datos/' + p['archivo'] for p in records}, expected)

    def test_changed_snapshot_and_unreviewed_copy_are_rejected(self):
        value = copy.deepcopy(self.snapshot)
        value['annotations']['shapes'][0]['points'][0] += 1
        self.write('snapshot_cvat.json', value)
        with self.assertRaisesRegex(ValueError, 'anotaciones revisadas'):
            development_records(self.run)
        self.write('snapshot_cvat.json', self.snapshot)
        metadata = json.loads((self.run / 'version_datos.json').read_text())
        metadata['state'] = 'pendiente_revision'
        self.write('version_datos.json', metadata)
        with self.assertRaises(ValueError):
            development_records(self.run)

    def test_image_hash_is_checked_even_after_the_reference_was_cached(self):
        photo = development_records(self.run)[0]
        with patch('evaluar_desarrollo.digest', return_value='modified'):
            with self.assertRaisesRegex(ValueError, 'imagen revisada cambió'):
                verified_image(photo)

    def test_selector_adds_variants_without_exposing_final_reserve(self):
        photos = panel.base_development_images()
        self.assertEqual(len(photos), 200)
        self.assertTrue(all(p['project_version'] == 'v2' for p in photos))
        reserved = {p['archivo'] for p in load_partition(panel.ROOT)['records'].values()
                    if p['effective_split'] == 'reserva'}
        self.assertTrue(reserved.isdisjoint(p['id'] for p in photos))

    def test_prediction_uses_server_reference_rows_and_ignores_client_rows(self):
        record = development_records(self.run)[1]
        model_id = 'Laboratorio/Experimentos/fixture/entrenamiento/weights/best.pt'
        image_id = panel.manifest_image_path(record)
        catalog = {'models': [{'id': model_id, 'run': 'fixture'}], 'images': [{'id': image_id}],
            'runs': [{'id': 'fixture', 'manifest': {'scope': 'Nivel_estados',
                'criterion': {'stage': 'base'}, 'imagenes': []}}]}
        with patch('evaluar_desarrollo.development_records', return_value=[record]), \
             patch('evaluar_desarrollo.verified_image'):
            clean = panel.validate({'action': 'predict', 'model': model_id, 'image': image_id,
                'conf': .25, 'nms': .7, 'imgsz': 640, 'truth_rows': ['spoof']}, catalog)
        self.assertEqual(clean['truth_rows'], record['truth_rows'])
        self.assertEqual(clean['split'], 'val')


if __name__ == '__main__':
    unittest.main()
