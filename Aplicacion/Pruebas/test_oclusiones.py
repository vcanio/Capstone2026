"""Pruebas de oclusiones frontales (Sección 5.6) y respaldo geométrico de nivel superior abierto."""
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import cv2
import numpy as np
from PIL import Image

from geometria_niveles import check_open_top_shelf, project_open_top_level
from inferencia import ModelRunner, analyze_edges
from oclusiones import (
    COCO_OCCLUSION_CLASSES,
    COCO_OCCLUSION_CONF,
    detect_coco_occlusions,
    detect_intrusions_from_rgb,
    draw_subtle_person_overlay,
    evaluate_level_occlusion,
    extract_person_polygons,
    photo_blocked_by_person,
)
from ocupacion_linea_a import analyze_gondola_rgb
from presentacion_niveles import occupancy_estimate
from vision_v3 import apply_scope


def _tensor(values):
    return SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: values, numpy=lambda: values))


class OcclusionTests(unittest.TestCase):
    def test_partial_occlusion_under_25_pct_masks_columns_without_forcing_review(self):
        rgb = np.full((300, 600, 3), 210, dtype=np.uint8)
        for x in range(40, 560, 70):
            cv2.rectangle(rgb, (x, 70), (x + 52, 230), (210, 45, 45), -1)
            cv2.rectangle(rgb, (x + 8, 100), (x + 44, 155), (245, 245, 245), -1)
        level_mask = np.zeros((300, 600), dtype=np.uint8)
        level_mask[40:260, 20:580] = 1
        occ_mask = np.zeros((300, 600), dtype=np.uint8)
        # Franja estrecha del 12% del ancho (~67 px) pintada lisa como intruso oscuro.
        occ_mask[40:260, 250:318] = 1
        rgb[40:260, 250:318] = (20, 20, 20)

        info = evaluate_level_occlusion(level_mask, occ_mask)
        self.assertFalse(info['requires_review'])
        self.assertTrue(info['should_mask_columns'])
        self.assertLess(info['occluded_area_frac'], 0.25)

        out = analyze_gondola_rgb(rgb, [level_mask], occlusion_masks=[occ_mask])[0]
        self.assertEqual(out['state'], 'suficiente')
        self.assertTrue(out['occlusion_masked'])
        self.assertGreater(out['occlusion_pct'], 5.0)

    def test_heavy_occlusion_25_pct_or_more_routes_to_review(self):
        rgb = np.full((300, 600, 3), 210, dtype=np.uint8)
        for x in range(40, 560, 70):
            cv2.rectangle(rgb, (x, 70), (x + 52, 230), (210, 45, 45), -1)
        level_mask = np.zeros((300, 600), dtype=np.uint8)
        level_mask[40:260, 20:580] = 1
        occ_mask = np.zeros((300, 600), dtype=np.uint8)
        occ_mask[40:260, 180:380] = 1  # > 35% del nivel obstruido.

        info = evaluate_level_occlusion(level_mask, occ_mask)
        self.assertTrue(info['requires_review'])
        self.assertFalse(info['should_mask_columns'])

        masks = np.expand_dims(level_mask, axis=0)
        result = SimpleNamespace(
            names={0: 'Nivel'},
            masks=SimpleNamespace(data=_tensor(masks)),
            boxes=SimpleNamespace(xyxy=_tensor([[20, 40, 580, 260]])),
        )
        detections = [{'id': 1, 'state': 'detectado'}]
        analyze_edges(rgb, result, detections, version='v2', occlusion_masks=[occ_mask])
        occ = detections[0]['occupancy']
        est = detections[0]['occupancy_estimate']
        self.assertEqual(occ['state'], 'revisar')
        self.assertEqual(occ['label'], 'Revisar · zona obstruida')
        self.assertEqual(occ['signal_pattern'], 'foreground_occlusion')
        self.assertEqual(est['state'], 'revisar')
        self.assertEqual(est['label'], 'Revisar · zona obstruida')
        self.assertIsNone(occupancy_estimate(occ, 'v2')['pct'])

    def test_rgb_intrusion_detector_ignores_clean_shelves_and_catches_vertical_blocker(self):
        clean_rgb = np.full((420, 600, 3), 220, dtype=np.uint8)
        # Riel continuo fuerte entre niveles 185..215.
        clean_rgb[190:202, 20:580] = (40, 40, 40)
        clean_rgb[202:212, 20:580] = (235, 235, 235)
        for y0, y1 in ((40, 175), (240, 385)):
            for x in range(40, 540, 65):
                cv2.rectangle(clean_rgb, (x, y0 + 20), (x + 48, y1 - 10), (35, 110, 205), -1)
                cv2.rectangle(clean_rgb, (x + 8, y0 + 40), (x + 40, y0 + 80), (245, 245, 245), -1)

        m_top = np.zeros((420, 600), dtype=np.uint8)
        m_top[30:182, 20:580] = 1
        m_bot = np.zeros((420, 600), dtype=np.uint8)
        m_bot[218:390, 20:580] = 1

        clean_occ = detect_intrusions_from_rgb(clean_rgb, [m_top, m_bot])
        self.assertEqual(clean_occ, [None, None])

        # Bloque vertical intruso de color vivo que tapa ambos niveles y el riel en ~30% del ancho.
        blocked_rgb = clean_rgb.copy()
        blocked_rgb[20:400, 210:390] = (25, 165, 95)
        blocked_occ = detect_intrusions_from_rgb(blocked_rgb, [m_top, m_bot])
        self.assertIsNotNone(blocked_occ[0])
        self.assertIsNotNone(blocked_occ[1])

        res = analyze_gondola_rgb(blocked_rgb, [m_top, m_bot])
        self.assertEqual(res[0]['signal_pattern'], 'foreground_occlusion')
        self.assertEqual(res[1]['signal_pattern'], 'foreground_occlusion')

    def test_coco_occlusion_detector_masks_partial_and_routes_heavy_to_review(self):
        rgb = np.full((300, 600, 3), 210, dtype=np.uint8)
        for y0, y1 in ((30, 130), (160, 260)):
            for x in range(40, 540, 70):
                cv2.rectangle(rgb, (x, y0 + 15), (x + 50, y1 - 10), (210, 45, 45), -1)
                cv2.rectangle(rgb, (x + 8, y0 + 30), (x + 42, y0 + 65), (245, 245, 245), -1)
        m1 = np.zeros((300, 600), dtype=np.uint8)
        m1[30:130, 20:580] = 1
        m2 = np.zeros((300, 600), dtype=np.uint8)
        m2[160:260, 20:580] = 1

        # Persona COCO simulada cubre 15% del nivel 1 (<25%) y 40% del nivel 2 (>=25%).
        coco_mask = np.zeros((300, 600), dtype=np.float32)
        coco_mask[30:130, 220:304] = 1.0
        coco_mask[160:260, 180:404] = 1.0
        calls = []

        class FakeCocoModel:
            def predict(self, img, **kwargs):
                calls.append(kwargs)
                return [SimpleNamespace(masks=SimpleNamespace(data=_tensor(np.expand_dims(coco_mask, 0))))]

        occ_masks = detect_coco_occlusions(rgb, [m1, m2], model=FakeCocoModel(), device='cpu')
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['classes'], list(COCO_OCCLUSION_CLASSES))
        self.assertAlmostEqual(calls[0]['conf'], COCO_OCCLUSION_CONF)

        out = analyze_gondola_rgb(rgb, [m1, m2], occlusion_masks=occ_masks)
        self.assertEqual(out[0]['state'], 'suficiente')
        self.assertTrue(out[0]['occlusion_masked'])
        self.assertEqual(out[1]['state'], 'revisar')
        self.assertEqual(out[1]['signal_pattern'], 'foreground_occlusion')
        self.assertEqual(out[1]['label'], 'Revisar · zona obstruida')

    def test_runner_validates_declared_coco_occlusion_model_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'modelos').mkdir()
            w1 = b'official weights'
            w2 = b'coco weights'
            (root / 'modelos/official.pt').write_bytes(w1)
            (root / 'modelos/yolo26n-seg.pt').write_bytes(w2)
            manifest = {
                'default_model': 'official',
                'models': [{
                    'id': 'official',
                    'name': 'Oficial',
                    'file': 'modelos/official.pt',
                    'sha256': hashlib.sha256(w1).hexdigest(),
                    'classes': ['Nivel'],
                }],
                'occlusion_model': {
                    'id': 'yolo26n-seg-coco',
                    'file': 'modelos/yolo26n-seg.pt',
                    'sha256': hashlib.sha256(w2).hexdigest(),
                    'bytes': len(w2),
                    'classes': [0],
                    'confidence': 0.35,
                },
            }
            (root / 'modelos.json').write_text(json.dumps(manifest), encoding='utf-8')
            runner = ModelRunner(root)
            self.assertEqual(len(runner.available()), 1)
            (root / 'modelos/yolo26n-seg.pt').write_bytes(b'corrupted')
            with self.assertRaisesRegex(ValueError, 'oclusiones.*modificado'):
                ModelRunner(root)

    def test_photo_blocked_by_person_only_when_obstructing_shelf_or_frame(self):
        lvl = np.zeros((200, 400), dtype=np.uint8)
        lvl[40:160, 40:360] = 1
        distant = np.zeros((200, 400), dtype=np.uint8)
        distant[40:160, 350:362] = 1  # ~3.7% del nivel en un borde.
        res_ok = photo_blocked_by_person([lvl], distant, (200, 400))
        self.assertFalse(res_ok['blocked'])

        blocking = np.zeros((200, 400), dtype=np.uint8)
        blocking[40:160, 140:260] = 1  # ~37% del nivel obstruido.
        res_blk = photo_blocked_by_person([lvl], blocking, (200, 400))
        self.assertTrue(res_blk['blocked'])
        self.assertIn('Persona obstruyendo', res_blk['reason'])

        res_no_lvls = photo_blocked_by_person([], blocking, (200, 400))
        self.assertTrue(res_no_lvls['blocked'])

        polys = extract_person_polygons(blocking)
        self.assertTrue(len(polys) >= 1 and len(polys[0]) >= 4)
        base_img = Image.new('RGB', (400, 200), (220, 220, 220))
        annotated = draw_subtle_person_overlay(base_img, polys)
        self.assertEqual(annotated.size, (400, 200))
        self.assertNotEqual(annotated.getpixel((200, 100)), (220, 220, 220))
        self.assertEqual(annotated.getpixel((10, 10)), (220, 220, 220))


class OpenTopGeometryTests(unittest.TestCase):
    def test_normal_height_top_shelf_is_unchanged(self):
        detections = [
            {
                'id': 1,
                'display_polygon': [[50.0, 540.0], [550.0, 540.0], [550.0, 720.0], [50.0, 720.0]],
                'occupancy_estimate': {'pct': 82.0, 'state': 'suficiente', 'label': 'Suficiente', 'color': '#16a34a'},
            },
            {
                'id': 2,
                'display_polygon': [[50.0, 340.0], [550.0, 340.0], [550.0, 520.0], [50.0, 520.0]],
                'occupancy_estimate': {'pct': 78.0, 'state': 'suficiente', 'label': 'Suficiente', 'color': '#16a34a'},
            },
            {
                'id': 3,
                'display_polygon': [[50.0, 140.0], [550.0, 140.0], [550.0, 320.0], [50.0, 320.0]],
                'occupancy_estimate': {'pct': 76.0, 'state': 'suficiente', 'label': 'Suficiente', 'color': '#16a34a'},
            },
        ]
        diag = check_open_top_shelf(detections, 600, 800)
        self.assertIsNone(diag)
        apply_scope(detections, 600, 800)
        self.assertEqual(detections[2]['occupancy_estimate']['state'], 'suficiente')

    def test_truncated_open_top_shelf_projects_median_and_routes_sufficient_to_review(self):
        detections = [
            {
                'id': 1,
                'display_polygon': [[50.0, 540.0], [550.0, 540.0], [550.0, 720.0], [50.0, 720.0]],  # h=180
                'occupancy_estimate': {'pct': 85.0, 'state': 'suficiente', 'label': 'Suficiente', 'color': '#16a34a'},
            },
            {
                'id': 2,
                'display_polygon': [[50.0, 340.0], [550.0, 340.0], [550.0, 520.0], [50.0, 520.0]],  # h=180
                'occupancy_estimate': {'pct': 80.0, 'state': 'suficiente', 'label': 'Suficiente', 'color': '#16a34a'},
            },
            {
                'id': 3,
                'display_polygon': [[50.0, 265.0], [550.0, 265.0], [550.0, 320.0], [50.0, 320.0]],  # h=55 (< 90)
                'occupancy_estimate': {'pct': 65.0, 'state': 'suficiente', 'label': 'Suficiente', 'color': '#16a34a'},
            },
        ]
        proj = project_open_top_level(detections, 600, 800)
        self.assertIsNotNone(proj)
        self.assertEqual(proj['median_height'], 180.0)
        self.assertEqual(proj['polygon'][0], [50.0, 140.0])

        apply_scope(detections, 600, 800)
        top = detections[2]
        self.assertTrue(top['open_top_truncated'])
        self.assertEqual(top['open_top_projected_polygon'][0], [50.0, 140.0])
        self.assertEqual(top['occupancy_estimate']['state'], 'revisar')
        self.assertEqual(top['occupancy_estimate']['label'], 'Revisar · nivel superior abierto')

        # Si ya estaba en Reponer, conserva la alerta sin ocultarla.
        top_reponer = {
            'id': 3,
            'display_polygon': [[50.0, 265.0], [550.0, 265.0], [550.0, 320.0], [50.0, 320.0]],
            'occupancy_estimate': {'pct': 18.0, 'state': 'reponer', 'label': 'Reponer', 'color': '#dc2626'},
        }
        apply_scope([detections[0], detections[1], top_reponer], 600, 800)
        self.assertEqual(top_reponer['occupancy_estimate']['state'], 'reponer')
        self.assertIn('nivel superior abierto', top_reponer['notice'])


if __name__ == '__main__':
    unittest.main()
