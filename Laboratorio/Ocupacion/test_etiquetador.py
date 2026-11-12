"""Pruebas rápidas de integridad para el etiquetador y evaluador de ocupación."""
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Ocupacion'))

from etiquetador_ocupacion import LabelingStore, render_preview_jpeg
from evaluar_linea_base import compute_binary_metrics


class TestOcupacionCalibracion(unittest.TestCase):
    def test_markdown_links_resolve(self):
        docs = [
            ROOT / 'Laboratorio/Ocupacion/README.md',
            ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107/README.md',
        ]
        for md in docs:
            if not md.is_file():
                continue  # La guía de calibración acompaña los datos privados.
            for target in re.findall(r'\]\(([^)]+)\)', md.read_text(encoding='utf-8')):
                dest = (md.parent / target).resolve()
                self.assertTrue(dest.exists(), f'Enlace roto en {md}: {target}')

    def test_manifest_integrity_and_zero_scene_leak(self):
        if not (ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107/muestra_desarrollo.json').is_file():
            self.skipTest('Integración: requiere la muestra privada de ocupación.')
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            store = LabelingStore(labels_path=tp / 'lbl.json', csv_path=tp / 'lbl.csv')
            imgs = store.manifest['images']
            self.assertEqual(len(imgs), 163)
            val_scenes = {x['grupo_escena'] for x in imgs if x['split'] == 'val'}
            train_scenes = {x['grupo_escena'] for x in imgs if x['split'] == 'train'}
            self.assertEqual(len(val_scenes & train_scenes), 0)
            self.assertEqual(sum(1 for x in imgs if x['split'] == 'val'), 93)
            self.assertEqual(sum(1 for x in imgs if x['split'] == 'train'), 70)

            # Verificar guardado atómico y exportación CSV
            first = imgs[0]
            lv_map = {str(lv['level_id']): 'suficiente' for lv in first['levels']}
            lv_map['1'] = 'vacio'
            store.save_item({'item_key': first['item_key'], 'levels': lv_map, 'note': 'ok', 'annotator': 'Test'})

            reloaded = LabelingStore(labels_path=tp / 'lbl.json', csv_path=tp / 'lbl.csv')
            summary = reloaded.summary_payload()
            self.assertEqual(summary['progress']['photos_done']['total'], 1)
            self.assertEqual(summary['progress']['gondola_distribution']['alerta'], 1)
            self.assertTrue((tp / 'lbl.csv').is_file())

            # Verificar previsualización JPEG con orientación EXIF aplicada
            from io import BytesIO
            from PIL import Image
            jpeg = render_preview_jpeg(first['serve_path'])
            self.assertGreater(len(jpeg), 10_000)
            with Image.open(BytesIO(jpeg)) as preview_img:
                self.assertEqual(
                    preview_img.width < preview_img.height,
                    first['width'] < first['height'],
                )

    def test_binary_metrics_accounting(self):
        metrics = compute_binary_metrics([
            (True, 'reponer'),     # TP
            (True, 'revisar'),     # Abstención en alerta (cuenta contra recall automático)
            (False, 'suficiente'), # TN
            (False, 'reponer'),    # FP
        ])
        self.assertEqual(metrics['precision_pct'], 50.0)
        self.assertEqual(metrics['recall_automatico_pct'], 50.0)
        self.assertEqual(metrics['recall_sobre_decididos_pct'], 100.0)
        self.assertEqual(metrics['tasa_revision_pct'], 25.0)


if __name__ == '__main__':
    unittest.main()
