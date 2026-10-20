"""Behavioral checks for the combination: mask isolation, missing data and semantics."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from ocupacion_paulo import Analyzer, Parameters, provenance, paulo
from experimentar_paulo import development_entries
import panel_modelos as panel


class SignalTests(unittest.TestCase):
    def test_worker_passes_original_pixels_even_while_rendering_red_yolo_mask(self):
        import panel_worker as worker
        from PIL import Image

        class Tensor:
            def __init__(self, value): self.value = np.asarray(value)
            def cpu(self): return self
            def tolist(self): return self.value.tolist()
            def numpy(self): return self.value

        class Boxes:
            xyxy = Tensor([[20, 20, 700, 460]])
            conf = Tensor([.95])
            cls = Tensor([0])
            def __len__(self): return 1

        mask = np.zeros((480, 720), np.uint8); mask[20:460, 20:700] = 1
        result = SimpleNamespace(boxes=Boxes(), names={0:'Nivel_reponer', 1:'Nivel_suficiente'},
            masks=SimpleNamespace(xy=[np.array([[20,20],[700,460],[700,20],[20,460]])], data=Tensor([mask])))
        class Result:
            def __getattr__(self, name): return getattr(result, name)
            def __getitem__(self, order): return self
        class Model:
            names = result.names
            def predict(self, image, **kwargs): return [Result()]

        directory = panel.ROOT / '.tmp/pruebas_modelos'; directory.mkdir(parents=True, exist_ok=True)
        font = worker.pilot.font_path()
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            root = Path(temporary); job = root / 'job'; job.mkdir()
            original = np.full((480, 720, 3), 255, np.uint8)
            Image.fromarray(original).save(root / 'original.png')
            (job / 'solicitud.json').write_text(json.dumps({'action':'predict','model':'fake.pt',
                'image':'original.png','occupancy':True,'imgsz':640,'conf':.25,'nms':.7}))
            with patch.object(worker.pilot, 'ROOT', root), patch.object(worker.pilot, 'font_path', return_value=font), \
                 patch.dict('sys.modules', {'torch':SimpleNamespace(cuda=SimpleNamespace(is_available=lambda:False)),
                                           'ultralytics':SimpleNamespace(YOLO=lambda path:Model())}):
                worker.execute(job)
            output = json.loads((job / 'resultado.json').read_text(encoding='utf-8'))
            self.assertEqual(output['occupancy']['input_kind'], 'original_rgb_before_inference')
            self.assertEqual(output['occupancy']['input_rgb_sha256'], hashlib.sha256(original.tobytes()).hexdigest())
            self.assertEqual(output['detecciones'][0]['occupancy']['area_signal_pct'], 0)
            self.assertEqual(output['detecciones'][0]['occupancy']['width_signal_pct'], 0)
            self.assertFalse(output['detecciones'][0]['contorno_valido'])
            self.assertEqual(output['detecciones'][0]['occupancy']['status'], 'medido')
            self.assertEqual(output['detecciones'][0]['occupancy']['mask_source'], 'yolo_raster')
            self.assertTrue(output['detecciones'][0]['occupancy']['contour_warning'])
            self.assertTrue(output['detecciones'][0]['alerta'])
            displayed = np.asarray(Image.open(job / 'prediccion.jpg').convert('RGB'))
            self.assertLess(int(displayed[240, 360, 1]), 250)  # The display really has the red tint.
            self.assertTrue(np.all(np.asarray(Image.open(root / 'original.png')) == original))
            for field, filename in (('occupancy_edges_image', 'paulo_bordes.png'),
                                    ('occupancy_filtered_edges_image', 'paulo_bordes_niveles.png')):
                self.assertEqual(output[field], filename)
                with Image.open(job / filename) as edges:
                    self.assertEqual(edges.mode, 'L')
                    self.assertEqual(edges.size, (720, 480))
                    self.assertFalse(np.asarray(edges).any())  # No red masks or numbered badges.

    def test_saved_filtered_edges_exclude_outside_and_skipped_levels(self):
        import cv2
        image = np.full((240, 720, 3), 255, np.uint8)
        for x, y in np.random.default_rng(42).integers([10, 10], [710, 230], size=(40, 2)):
            cv2.circle(image, (int(x), int(y)), 6, (0, 0, 0), -1)
        analyzer = Analyzer(image)
        mask = np.zeros(image.shape[:2], bool); mask[20:220, 30:340] = True
        analyzer.analyze(mask, state='no_evaluable', valid_contour=False)
        self.assertFalse(analyzer.filtered_edges.any())
        result = analyzer.analyze(mask, valid_contour=False)
        self.assertEqual(result['status'], 'medido')
        self.assertTrue(analyzer.edges.any())
        self.assertTrue(analyzer.filtered_edges.any())
        self.assertFalse(analyzer.filtered_edges[~mask].any())

    def test_unmeasurable_is_not_zero_or_a_stock_alert(self):
        image = np.full((240, 720, 3), 255, dtype=np.uint8)
        analyzer = Analyzer(image)
        tiny = np.zeros(image.shape[:2], bool); tiny[2:12, 2:12] = True
        for result in (analyzer.analyze(tiny), analyzer.analyze(None),
                       analyzer.analyze(np.ones(image.shape[:2], bool), 'no_evaluable'),
                       analyzer.analyze(np.zeros(image.shape[:2], bool), valid_contour=False),
                       analyzer.analyze(np.ones((10, 10)), valid_contour=False),
                       analyzer.analyze(np.full(image.shape[:2], np.nan), valid_contour=False),
                       analyzer.analyze(np.full(image.shape[:2], .5), valid_contour=False)):
            self.assertEqual(result['status'], 'sin_medicion')
            self.assertIsNone(result['area_signal_pct'])
            self.assertIsNone(result['width_signal_pct'])

    def test_mask_excludes_dark_background_from_signal_and_denominator(self):
        image = np.zeros((300, 900, 3), np.uint8)
        image[60:240, 100:800] = 255
        mask = np.zeros(image.shape[:2], bool); mask[90:210, 130:770] = True
        result = Analyzer(image).analyze(mask)
        self.assertEqual(result['status'], 'medido')
        self.assertEqual(result['area_signal_pct'], 0)
        self.assertEqual(result['width_signal_pct'], 0)

    def test_full_width_low_product_differs_from_grid_area(self):
        image = np.full((480, 960, 3), 255, dtype=np.uint8)
        image[360:] = (220, 20, 20)
        result = Analyzer(image, replace(Parameters(), opening=1)).analyze(np.ones(image.shape[:2], bool))
        self.assertLess(result['area_signal_pct'], 40)
        self.assertGreater(result['width_signal_pct'], 90)

    def test_flat_dark_background_does_not_count_as_product(self):
        for color in ((0, 0, 0), (40, 40, 40), (35, 4, 4)):
            image = np.full((240, 720, 3), color, dtype=np.uint8)
            result = Analyzer(image).analyze(np.ones(image.shape[:2], bool))
            self.assertEqual(result['area_signal_pct'], 0)
            self.assertEqual(result['width_signal_pct'], 0)
        self.assertFalse(result['calibrated'])
        self.assertFalse(provenance()['changes_yolo_state'])

    def test_dark_textured_regions_can_still_generate_signal(self):
        yy, xx = np.indices((240, 720))
        pattern = (30 + 35*((xx//8 + yy//8) % 2)).astype(np.uint8)
        image = np.repeat(pattern[..., None], 3, axis=2)
        result = Analyzer(image).analyze(np.ones(image.shape[:2], bool))
        self.assertGreater(result['area_signal_pct'], 20)

    def test_masked_texture_does_not_count_an_outside_color_boundary(self):
        image = np.zeros((300, 900, 3), np.uint8)
        image[:, :] = (240, 20, 20)
        image[60:240, 100:800] = 30
        mask = np.zeros(image.shape[:2], bool); mask[90:210, 130:770] = True
        result = Analyzer(image).analyze(mask)
        self.assertEqual(result['area_signal_pct'], 0)

    def test_standalone_handles_clipped_tiny_and_off_image_boxes(self):
        args = SimpleNamespace(canny=[40, 120], cell=24, thr=.04, margin=.03,
            open=3, line=.04, color_frac=.35, sat=70, vmin=50, tex=4., tex_vmax=90)
        image = np.full((240, 720, 3), 40, dtype=np.uint8)
        results, _ = paulo().analizar(image, [[-50, 0, 300, 240], [800, 0, 120, 120], [0, 0, 20, 20], [0, 0, -2, 40]], args)
        self.assertEqual(results[0]['pct'], 0)
        for result in results[1:]:
            self.assertIsNone(result['pct'])
            self.assertEqual(result['status'], 'sin_medicion')
        paulo().dibujar(image, results)  # Missing measurements remain drawable.
        with self.assertRaises(ValueError): paulo().analizar(image, [[0, 0, 720, 240]], SimpleNamespace(**{**vars(args), 'cell':0}))
        with self.assertRaises(ValueError): paulo().analizar(image, [[0, 0, 720, 240]], SimpleNamespace(**{**vars(args), 'tex':float('nan')}))
        with self.assertRaises(ValueError): paulo().analizar(image, [[0, 0, 'bad', 40]], args)

    def test_standalone_rejects_empty_image_file(self):
        directory = panel.ROOT / '.tmp/pruebas_modelos'
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            file = Path(temporary) / 'empty.png'; file.write_bytes(b'')
            self.assertIsNone(paulo().leer_imagen(str(file)))

    def test_standalone_cli_writes_reproducible_json_without_opening_editor(self):
        from PIL import Image
        directory = panel.ROOT / '.tmp/pruebas_modelos'
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            root = Path(temporary)
            Image.fromarray(np.full((240, 720, 3), 40, np.uint8)).save(root/'frame.png')
            (root/'rois.json').write_text(json.dumps([[0, 0, 720, 240], [800, 0, 120, 120]]))
            result = subprocess.run([sys.executable, str(panel.ROOT/'Experimentos/Bordes/gondola_bordes.py'),
                str(root/'frame.png'), '--rois', str(root/'rois.json'), '--out', str(root/'output'),
                '--stress', '2'], capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((root/'output/frame_mediciones.json').read_text(encoding='utf-8'))
            self.assertEqual(data['resultados'][0]['pct'], 0)
            self.assertIsNone(data['resultados'][1]['pct'])
            self.assertFalse(data['calibrado'])

    def test_both_new_models_share_registered_validation_and_reject_other_splits(self):
        from particion_niveles import load_partition
        import json
        partition = load_partition(panel.ROOT)
        run = panel.ROOT / 'Experimentos/v2_base_yolo26n_01_20261020_004933_b105'
        manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(len(development_entries(manifest, partition)), 10)
        changed = {**manifest, 'imagenes': [{**manifest['imagenes'][0], 'split': 'val'}]}
        with self.assertRaises(ValueError): development_entries(changed, partition)

    def test_backend_only_accepts_explicit_experiment_with_v2_model(self):
        data = {'models': [{'id': 'model.pt', 'run': 'v2'}], 'images': [{'id': 'photo.jpg'}],
                'runs': [{'id': 'v2', 'manifest': {'scope': 'Nivel_estados', 'imagenes': [],
                'criterion': {'version': 'disponibilidad_visual_nivel_v2_reponer'}}}]}
        config = {'action': 'predict', 'model': 'model.pt', 'image': 'photo.jpg', 'conf': .25, 'nms': .7, 'imgsz': 640}
        self.assertNotIn('occupancy', panel.validate(config, data))
        self.assertTrue(panel.validate({**config, 'occupancy': True}, data)['occupancy'])
        with self.assertRaises(ValueError): panel.validate({**config, 'occupancy': 'true'}, data)
        data['runs'][0]['manifest']['criterion']['version'] = 'disponibilidad_visual_nivel_v1'
        with self.assertRaises(ValueError): panel.validate({**config, 'occupancy': True}, data)


if __name__ == '__main__':
    unittest.main()
