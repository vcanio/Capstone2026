import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
import numpy as np

from PIL import Image
from inferencia import ModelRunner


class FiltroExperimentalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'modelos').mkdir()
        payload = b'fixture'
        (self.root / 'modelos/fixture.pt').write_bytes(payload)
        (self.root / 'modelos.json').write_text(json.dumps({'default_model': 'fixture', 'models': [
            {'id': 'fixture', 'file': 'modelos/fixture.pt', 'sha256': hashlib.sha256(payload).hexdigest(),
             'classes': ['Nivel']}]}), encoding='utf-8')
        self.runner = ModelRunner(self.root)
        buffer = BytesIO()
        Image.new('RGB', (120, 80), 'white').save(buffer, 'PNG')
        self.photo = buffer.getvalue()

    def test_filtro_rechaza_antes_de_yolo_y_no_devuelve_mediciones(self):
        with patch('visibilidad_experimental.assess', return_value={'estado': 'no_apta', 'politica': 'test'}), \
             patch.object(self.runner, '_load_model') as load:
            result = self.runner.analyze(self.photo, 'fixture', .6, 'yolo_paulo_v2', visibility_mode='experimental')
        load.assert_not_called()
        self.assertEqual(result['photo_status'], 'no_evaluable')
        self.assertEqual(result['detections'], [])
        self.assertNotIn('occupancy', result)

    def test_falta_candidato_falla_cerrado_sin_ejecutar_yolo(self):
        with patch.object(self.runner, '_load_model') as load:
            with self.assertRaisesRegex(ValueError, 'candidato'):
                self.runner.analyze(self.photo, 'fixture', .6, visibility_mode='experimental')
        load.assert_not_called()

    def test_sin_mascaras_validas_se_bloquea_antes_de_ocupacion(self):
        model = MagicMock()
        model.predict.return_value = [MagicMock(masks=None)]
        with patch('visibilidad_experimental.assess', return_value={'estado': 'apta', 'politica': 'test'}), \
             patch.object(self.runner, '_load_model', return_value=(model, 'cpu')), \
             patch('inferencia.draw_result', return_value=(Image.new('RGB', (120, 80)), [])), \
             patch('inferencia.analyze_edges') as edges:
            result = self.runner.analyze(self.photo, 'fixture', .6, 'yolo_paulo_v2', visibility_mode='experimental')
        edges.assert_not_called()
        self.assertEqual(result['photo_status'], 'no_evaluable')
        self.assertEqual(result['evaluabilidad']['estado'], 'dudosa')

    def test_contorno_al_borde_bloquea_toda_la_foto(self):
        model = MagicMock()
        model.predict.return_value[0].masks.data.cpu.return_value.numpy.return_value = np.ones((1, 80, 120))
        detected = [{'state': 'detectado', 'near_frame': True}]
        with patch('visibilidad_experimental.assess', return_value={'estado': 'apta', 'politica': 'test'}), \
             patch.object(self.runner, '_load_model', return_value=(model, 'cpu')), \
             patch('inferencia.draw_result', return_value=(Image.new('RGB', (120, 80)), detected)), \
             patch('inferencia.analyze_edges') as edges:
            result = self.runner.analyze(self.photo, 'fixture', .6, 'yolo_paulo_v2', visibility_mode='experimental')
        edges.assert_not_called()
        self.assertEqual(result['detections'], [])
        self.assertEqual(result['photo_status'], 'no_evaluable')

    def test_mascara_completa_puede_continuar(self):
        model = MagicMock()
        model.predict.return_value[0].masks.data.cpu.return_value.numpy.return_value = np.ones((1, 80, 120))
        detected = [{'state': 'detectado', 'near_frame': False, 'display_polygon': [(10, 10), (20, 20)]}]
        with patch('visibilidad_experimental.assess', return_value={'estado': 'apta', 'politica': 'test'}), \
             patch.object(self.runner, '_load_model', return_value=(model, 'cpu')), \
             patch('inferencia.draw_result', return_value=(Image.new('RGB', (120, 80)), detected)):
            result = self.runner.analyze(self.photo, 'fixture', .6, visibility_mode='experimental')
        self.assertEqual(result['evaluabilidad']['estado'], 'apta')
        self.assertEqual(len(result['detections']), 1)

    def test_region_que_no_se_puede_medir_suspende_toda_la_foto(self):
        model = MagicMock()
        model.predict.return_value[0].masks.data.cpu.return_value.numpy.return_value = np.ones((1, 80, 120))
        detected = [{'state': 'detectado', 'near_frame': False, 'display_polygon': [(10, 10), (20, 20)]}]
        def cannot_measure(original, prediction, detections, version):
            detections[0]['occupancy'] = {'status': 'sin_medicion'}
            return {'occupancy': {}}
        with patch('visibilidad_experimental.assess', return_value={'estado': 'apta', 'politica': 'test'}), \
             patch.object(self.runner, '_load_model', return_value=(model, 'cpu')), \
             patch('inferencia.draw_result', return_value=(Image.new('RGB', (120, 80)), detected)), \
             patch('inferencia.analyze_edges', side_effect=cannot_measure):
            result = self.runner.analyze(self.photo, 'fixture', .6, 'yolo_paulo_v2', visibility_mode='experimental')
        self.assertEqual(result['photo_status'], 'no_evaluable')
        self.assertEqual(result['detections'], [])
        self.assertNotIn('occupancy', result)


if __name__ == '__main__':
    unittest.main()
