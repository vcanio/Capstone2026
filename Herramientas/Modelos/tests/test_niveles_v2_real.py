"""Prueba opcional con YOLO26 real: una época sobre figuras sintéticas.

Habilitar con RUN_NIVELES_REAL=1. Verifica ejecución e integración, no calidad
predictiva. No utiliza ni modifica las fotos, pesos ni ensayos del proyecto.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw
import yaml

import entrenar_niveles as training


@unittest.skipUnless(os.environ.get('RUN_NIVELES_REAL') == '1', 'Integración real opcional: RUN_NIVELES_REAL=1')
class RealYOLOTests(unittest.TestCase):
    def test_yolo26_trains_and_evaluates_all_three_states(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {'train': 'images/train', 'val': 'images/val', 'test': 'images/test',
                      'names': list(training.CLASSES)}
            data = root / 'data.yaml'
            data.write_text(yaml.safe_dump(config))
            for split, offset in [('train', 10), ('val', 50), ('test', 100)]:
                for i in range(2):
                    source = root / 'images' / split / f'figuras_{i}.png'
                    source.parent.mkdir(parents=True, exist_ok=True)
                    label = root / 'labels' / split / f'figuras_{i}.txt'
                    label.parent.mkdir(parents=True, exist_ok=True)
                    image = Image.new('RGB', (96, 96), (offset+i, 20, 30))
                    draw = ImageDraw.Draw(image)
                    rows = []
                    for cls in range(3):
                        y = 5 + cls * 30
                        draw.rectangle((10, y, 85, y+20), fill=(30, 60+cls*60, offset+i))
                        rows.append(f'{cls} {10/96} {y/96} {85/96} {y/96} {85/96} {(y+20)/96} {10/96} {(y+20)/96}')
                    image.save(source)
                    label.write_text('\n'.join(rows) + '\n')
            dataset, report = training.validate_dataset(data)
            args = argparse.Namespace(modelo=str(training.ROOT / 'Modelos/preentrenados/yolo26n-seg.pt'),
                                      nombre='integracion_real', device='cpu', epochs=1, imgsz=64,
                                      batch=2, seed=42, lr=0.001, patience=1, evaluar_test=True,
                                      conf=0.25, iou_mascara=0.5)
            import torch
            threads = torch.get_num_threads()
            try:
                torch.set_num_threads(1)
                with patch.object(training, 'ROOT', root):
                    run = training.train(args, dataset, report)
            finally:
                torch.set_num_threads(threads)
            self.assertTrue((run / 'entrenamiento/weights/best.pt').is_file())
            for split in ('val', 'test'):
                result = json.loads((run / f'alertas_{split}.json').read_text())
                self.assertEqual(result['fotos'], 2)
                self.assertEqual(set(result['por_clase']), {'reponer', 'suficiente', 'no_evaluable'})
            metrics = json.loads((run / 'metricas_validacion.json').read_text())
            self.assertTrue(metrics['cobertura_completa'])
            self.assertEqual(len(metrics['por_clase_yolo']), 3)


if __name__ == '__main__':
    unittest.main()
