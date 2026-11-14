import hashlib
import json
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
from PIL import Image

APP_DIR = Path(__file__).resolve().parents[1]
CLIENT_DIR = APP_DIR.parent / 'Aplicacion_Cliente'
for p in (str(APP_DIR), str(CLIENT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app_cliente import enrich_for_store
from calidad_foto import assess_photo_quality
from inferencia import ModelRunner


def _textured_rgb(size=(360, 280), seed=42) -> Image.Image:
    rng = np.random.default_rng(seed)
    base = rng.integers(80, 190, (size[1], size[0], 3), dtype=np.uint8)
    for y in range(20, size[1], 40):
        cv2.rectangle(base, (15, y), (size[0] - 15, y + 18), (35, 110, 210), -1)
        cv2.line(base, (10, y + 22), (size[0] - 10, y + 22), (240, 240, 240), 2)
    return Image.fromarray(base, 'RGB')


def _png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()


class CalidadFotoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'modelos').mkdir()
        payload = b'fixture'
        (self.root / 'modelos/fixture.pt').write_bytes(payload)
        (self.root / 'modelos.json').write_text(
            json.dumps({
                'default_model': 'fixture',
                'models': [{
                    'id': 'fixture',
                    'file': 'modelos/fixture.pt',
                    'sha256': hashlib.sha256(payload).hexdigest(),
                    'classes': ['Nivel'],
                }],
            }),
            encoding='utf-8',
        )
        self.runner = ModelRunner(self.root)

    def test_imagen_nitida_pasa_calidad(self):
        img = _textured_rgb()
        res = assess_photo_quality(img)
        self.assertTrue(res['usable'])
        self.assertEqual(res['status'], 'ok')

    def test_imagen_borrosa_es_no_evaluable(self):
        sharp = np.asarray(_textured_rgb())
        blur = Image.fromarray(cv2.GaussianBlur(sharp, (35, 35), 11.0))
        res = assess_photo_quality(blur)
        self.assertFalse(res['usable'])
        self.assertEqual(res['status'], 'desenfoque')

    def test_imagen_oscura_es_subexpuesta(self):
        dark = Image.new('RGB', (360, 280), (15, 15, 18))
        res = assess_photo_quality(dark)
        self.assertFalse(res['usable'])
        self.assertEqual(res['status'], 'subexpuesta')

    def test_imagen_quemada_es_sobreexpuesta(self):
        bright = Image.new('RGB', (360, 280), (252, 252, 252))
        res = assess_photo_quality(bright)
        self.assertFalse(res['usable'])
        self.assertEqual(res['status'], 'sobreexpuesta')

    def test_runner_bloquea_antes_de_yolo_en_mala_captura_real(self):
        dark_bytes = _png_bytes(Image.new('RGB', (360, 280), (12, 12, 12)))
        with patch.object(self.runner, '_load_model') as load:
            result = self.runner.analyze(dark_bytes, 'fixture', 0.6, 'yolo_paulo_v2')
        load.assert_not_called()
        self.assertEqual(result['photo_status'], 'no_evaluable')
        self.assertEqual(result['detections'], [])
        self.assertEqual(result['calidad']['status'], 'subexpuesta')

    def test_runner_continua_si_calidad_es_valida_y_adjunta_calidad(self):
        sharp_bytes = _png_bytes(_textured_rgb())
        model = MagicMock()
        model.predict.return_value = [MagicMock(masks=None)]
        with patch.object(self.runner, '_load_model', return_value=(model, 'cpu')), \
             patch('inferencia.draw_result', return_value=(Image.new('RGB', (360, 280)), [])):
            result = self.runner.analyze(sharp_bytes, 'fixture', 0.6, 'yolo_paulo_v2')
        model.predict.assert_called_once()
        self.assertTrue(result['calidad']['usable'])
        self.assertEqual(result['calidad']['status'], 'ok')

    def test_cliente_clasifica_foto_no_evaluable_en_verificar(self):
        enriched = enrich_for_store({
            'photo_status': 'no_evaluable',
            'message': 'Foto demasiado borrosa o movida para evaluar la góndola.',
            'detections': [],
        })
        self.assertEqual(enriched['store_summary']['aisle_state'], 'verificar')
        self.assertEqual(enriched['store_summary']['aisle_label'], 'Foto no evaluable')


if __name__ == '__main__':
    unittest.main()
