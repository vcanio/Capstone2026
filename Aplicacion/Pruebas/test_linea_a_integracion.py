"""Línea A en el flujo portable: máscaras, orden, presentación y procedencia."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

import cv2
import numpy as np

from inferencia import analyze_edges
from ocupacion_linea_a import analyze_gondola_rgb, compute_cell_maps, METHOD_LINEA_A, INTERPRETATION_POLICY
from presentacion_niveles import occupancy_estimate
from vision_v3 import apply_scope


def tensor(values):
    return SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: values, numpy=lambda: values))


class LineaAIntegrationTests(unittest.TestCase):
    def test_shared_gondola_anchorage_uses_original_masks_in_spatial_order(self):
        rgb = np.full((600, 900, 3), 70, np.uint8)
        for x in range(80, 800, 90):
            cv2.rectangle(rgb, (x, 370), (x + 65, 540), (220, 50, 50), -1)
            cv2.rectangle(rgb, (x + 10, 410), (x + 55, 470), (240, 240, 240), -1)
        masks = np.zeros((2, 600, 900), np.uint8)
        masks[0, 30:260, 30:870] = 1  # YOLO entrega primero el superior.
        masks[1, 330:570, 30:870] = 1
        saved = masks.copy()
        result = SimpleNamespace(names={0: 'Nivel'}, masks=SimpleNamespace(data=tensor(masks)),
                                 boxes=SimpleNamespace(xyxy=tensor([[30, 30, 870, 260], [30, 330, 870, 570]])))
        detections = [{'id': 1, 'state': 'detectado'}, {'id': 2, 'state': 'detectado'}]
        expected = analyze_gondola_rgb(rgb, [masks[1], masks[0]])
        output = analyze_edges(rgb, result, detections, version='v2')
        self.assertEqual(output['occupancy']['method'], METHOD_LINEA_A)
        self.assertEqual(output['occupancy']['interpretation_policy']['threshold_pct'], 52)
        self.assertEqual([d['occupancy'] for d in detections], expected)
        self.assertEqual(detections[1]['occupancy_estimate']['state'], 'reponer')
        self.assertTrue(np.any(np.asarray(output['occupancy_image']) != rgb))
        np.testing.assert_array_equal(masks, saved)
        self.assertEqual([d['state'] for d in detections], ['detectado', 'detectado'])

    def test_missing_mask_and_ambiguous_readings_do_not_become_sufficient(self):
        detections = [{'state': 'detectado'}]
        output = analyze_edges(np.zeros((120, 240, 3), np.uint8),
                               SimpleNamespace(names={0: 'Nivel'}, masks=None), detections, 'v2')
        self.assertEqual(output['occupancy']['method'], METHOD_LINEA_A)
        self.assertIsNone(detections[0]['occupancy_estimate']['pct'])
        self.assertEqual(detections[0]['occupancy_estimate']['state'], 'sin_medicion')
        measurement = dict(status='medido', interpretation_policy=INTERPRETATION_POLICY,
                           pct=70, state='revisar', review_required=True)
        self.assertEqual(occupancy_estimate(measurement, 'v2')['state'], 'revisar')
        self.assertIsNone(occupancy_estimate(measurement, 'v2')['pct'])

    def test_linea_a_boundary_and_scope_keep_their_own_decisions(self):
        for value, state in ((51.99, 'reponer'), (52, 'suficiente')):
            reading = occupancy_estimate(dict(status='medido', interpretation_policy=INTERPRETATION_POLICY,
                                             pct=value, state=state), 'v2')
            self.assertEqual(reading['state'], state)
        level = dict(display_polygon=[(0, 20), (90, 90)], occupancy_estimate=reading,
                     occupancy={'interpretation_policy': INTERPRETATION_POLICY})
        saved = deepcopy(level['display_polygon'])
        apply_scope([level], 100, 100)
        self.assertEqual(level['occupancy_estimate']['state'], 'revisar')
        self.assertEqual(level['display_polygon'], saved)

    def test_flat_saturated_backboard_without_texture_is_reponer(self):
        rgb = np.full((600, 900, 3), 215, np.uint8)
        # Tablero azul completamente liso sin bordes ni envases dentro del nivel superior.
        rgb[50:220, 120:780] = (35, 105, 195)
        for x in range(80, 800, 90):
            cv2.rectangle(rgb, (x, 370), (x + 65, 540), (220, 50, 50), -1)
            cv2.rectangle(rgb, (x + 10, 410), (x + 55, 470), (245, 245, 245), -1)
        masks = np.zeros((2, 600, 900), np.uint8)
        masks[0, 30:260, 30:870] = 1
        masks[1, 330:570, 30:870] = 1
        out = analyze_gondola_rgb(rgb, [masks[1], masks[0]])
        self.assertEqual(out[0]['state'], 'suficiente')
        self.assertEqual(out[1]['state'], 'reponer')

    def test_open_ceiling_horizontal_trusses_are_reponer(self):
        rgb = np.full((600, 900, 3), 205, np.uint8)
        # Franjas horizontales tipo cielo raso y luminarias en el nivel superior vacío.
        for y in range(45, 235, 24):
            cv2.line(rgb, (35, y), (865, y), (110, 110, 110), 2)
        for x in range(80, 800, 90):
            cv2.rectangle(rgb, (x, 370), (x + 65, 540), (200, 60, 50), -1)
            cv2.rectangle(rgb, (x + 12, 405), (x + 54, 480), (245, 245, 245), -1)
        masks = np.zeros((2, 600, 900), np.uint8)
        masks[0, 30:250, 30:870] = 1
        masks[1, 330:570, 30:870] = 1
        out = analyze_gondola_rgb(rgb, [masks[1], masks[0]])
        self.assertEqual(out[0]['state'], 'suficiente')
        self.assertEqual(out[1]['state'], 'reponer')

    def test_tilted_shelf_preserves_empty_right_columns_in_valid_cols(self):
        usable = np.ones((4, 20), dtype=bool)
        # El extremo derecho cae parcialmente del estante y deja solo 1 fila usable en soporte.
        usable[0:2, 12:] = False
        usable[3, 12:] = False
        stocked_cols = np.broadcast_to(np.arange(20)[None, :] < 12, (4, 20))
        feat = {
            'valid': True,
            'valid_cells': int(usable.sum()),
            'usable': usable,
            'observed_coverage': np.ones((4, 20), dtype=np.float32),
            'density': np.where(stocked_cols, 0.08, 0.0).astype(np.float32),
            'gradient': np.where(stocked_cols, 48.0, 4.0).astype(np.float32),
            'color_density': np.where(stocked_cols, 0.5, 0.0).astype(np.float32),
            'deviation': np.where(stocked_cols, 24.0, 2.0).astype(np.float32),
        }
        maps = compute_cell_maps(feat)
        self.assertTrue(bool(maps['valid_cols'].all()))
        self.assertFalse(bool(maps['col_covered_full'][12:].any()))

    def test_exposed_floor_mask_suppresses_horizontal_tray_edges(self):
        from ocupacion_linea_a import score_level_from_features

        h, w = 10, 20
        usable = np.ones((h, w), dtype=bool)
        density = np.full((h, w), 0.04, dtype=np.float32)
        density[:5, :] = 0.01  # Zonas superiores sin detalle de envases.
        feat = {
            'valid': True,
            'valid_cells': int(usable.sum()),
            'usable': usable,
            'observed_coverage': np.ones((h, w), dtype=np.float32),
            'density': density,
            'gradient': np.full((h, w), 45.0, dtype=np.float32),
            'color_density': np.full((h, w), 0.05, dtype=np.float32),
            'deviation': np.full((h, w), 20.0, dtype=np.float32),
            'gx': np.full((h, w), 8.0, dtype=np.float32),
            'gy': np.full((h, w), 40.0, dtype=np.float32),
            'vx': np.full((h, w), 0.08, dtype=np.float32),
            'bu': np.full((h, w), 0.25, dtype=np.float32),
        }
        res = score_level_from_features(feat, None)
        self.assertTrue(res['floor_mask_active'])
        self.assertEqual(res['state'], 'reponer')
        self.assertEqual(res['operational_severity'], 'critica')

    def test_facing_gap_alert_triggers_reponer_above_52_pct(self):
        from ocupacion_linea_a import score_level_from_features

        h, w = 10, 20
        usable = np.ones((h, w), dtype=bool)
        stocked = np.broadcast_to(np.arange(w)[None, :] < 12, (h, w))  # 60 % cubierto, 40 % hueco.
        feat = {
            'valid': True,
            'valid_cells': int(usable.sum()),
            'usable': usable,
            'observed_coverage': np.ones((h, w), dtype=np.float32),
            'density': np.where(stocked, 0.10, 0.005).astype(np.float32),
            'gradient': np.where(stocked, 60.0, 5.0).astype(np.float32),
            'color_density': np.where(stocked, 0.50, 0.02).astype(np.float32),
            'deviation': np.where(stocked, 25.0, 2.0).astype(np.float32),
            'gx': np.where(stocked, 35.0, 5.0).astype(np.float32),
            'gy': np.full((h, w), 20.0, dtype=np.float32),
            'vx': np.where(stocked, 0.45, 0.05).astype(np.float32),
            'bu': np.full((h, w), 0.35, dtype=np.float32),
        }
        bounds = ((0.0, 0.10), (4.0, 60.0), (0.0, 0.50), (2.0, 25.0))
        res = score_level_from_features(feat, bounds)
        self.assertGreaterEqual(res['raw_pct'], 52.0)
        self.assertGreaterEqual(res['max_gap_pct'], 35.0)
        self.assertLess(res['front_hyb_pct'], 68.0)
        self.assertEqual(res['state'], 'reponer')
        self.assertEqual(res['operational_severity'], 'alta')

    def test_weak_two_column_island_is_bridged_by_gap_analyzer(self):
        from ocupacion_linea_a import analyze_column_gaps

        covered = np.zeros(20, dtype=bool)
        covered[:5] = True
        covered[9:11] = True  # Isla aislada de 2 columnas entre tramos vacíos.
        weak_frac = np.where(covered, 0.80, 0.05).astype(np.float32)
        weak_frac[9:11] = 0.25
        weak_gap = analyze_column_gaps(covered, col_frac=weak_frac, bridge_single=True)
        self.assertAlmostEqual(weak_gap['max_gap_pct'], 75.0, places=2)
        self.assertFalse(bool(weak_gap['filtered_covered'][9:11].any()))

        strong_frac = weak_frac.copy()
        strong_frac[9:11] = 0.70
        strong_gap = analyze_column_gaps(covered, col_frac=strong_frac, bridge_single=True)
        self.assertAlmostEqual(strong_gap['max_gap_pct'], 45.0, places=2)
        self.assertAlmostEqual(strong_gap['significant_gaps_pct'], 65.0, places=2)
        self.assertAlmostEqual(strong_gap['effective_gap_pct'], 0.85 * 65.0, places=2)

    def test_low_contrast_dark_front_triggers_review_and_requires_bu(self):
        from ocupacion_linea_a import score_level_from_features

        h, w = 10, 20
        usable = np.ones((h, w), dtype=bool)
        active = np.zeros((h, w), dtype=bool)
        active[4:7, :] = True  # 3/7 filas de body cubiertas en todo el frente (sin hueco horizontal).
        feat = {
            'valid': True,
            'valid_cells': int(usable.sum()),
            'usable': usable,
            'observed_coverage': np.ones((h, w), dtype=np.float32),
            'density': np.where(active, 0.04, 0.005).astype(np.float32),
            'gradient': np.where(active, 30.0, 10.0).astype(np.float32),
            'color_density': np.where(active, 0.25, 0.05).astype(np.float32),
            'deviation': np.where(active, 15.0, 4.0).astype(np.float32),
            'bu': np.full((h, w), 0.05, dtype=np.float32),
        }
        bounds = ((0.0, 0.12), (5.0, 80.0), (0.0, 0.50), (2.0, 35.0))
        res_dark = score_level_from_features(feat, bounds)
        self.assertEqual(res_dark['state'], 'revisar')
        self.assertEqual(res_dark['signal_pattern'], 'low_contrast_continuous_front')
        self.assertTrue(res_dark['review_required'])
        self.assertEqual(res_dark['operational_severity'], 'verificar')
        self.assertGreaterEqual(res_dark['raw_pct'], 36.0)
        self.assertLess(res_dark['raw_pct'], 52.0)

        feat_no_bu = {k: v for k, v in feat.items() if k != 'bu'}
        res_no_bu = score_level_from_features(feat_no_bu, bounds)
        self.assertEqual(res_no_bu['state'], 'reponer')

    def test_white_stocked_packages_protected_on_top_level(self):
        from ocupacion_linea_a import score_level_from_features

        h, w = 10, 20
        usable = np.ones((h, w), dtype=bool)
        bu = np.full((h, w), 0.25, dtype=np.float32)
        bu[5:, :] = 0.85  # Base blanca brillante con logos coloridos arriba.
        color_density = np.full((h, w), 0.08, dtype=np.float32)
        color_density[:5, :] = 0.40
        feat = {
            'valid': True,
            'valid_cells': int(usable.sum()),
            'usable': usable,
            'observed_coverage': np.ones((h, w), dtype=np.float32),
            'density': np.full((h, w), 0.08, dtype=np.float32),
            'gradient': np.full((h, w), 45.0, dtype=np.float32),
            'color_density': color_density,
            'deviation': np.full((h, w), 22.0, dtype=np.float32),
            'gx': np.full((h, w), 22.0, dtype=np.float32),
            'gy': np.full((h, w), 35.0, dtype=np.float32),
            'vx': np.full((h, w), 0.30, dtype=np.float32),
            'bu': bu,
        }
        res = score_level_from_features(feat, None, is_top_level=True)
        self.assertFalse(res['ceil_mask_active'])
        self.assertFalse(res['floor_mask_active'])
        self.assertEqual(res['state'], 'suficiente')

    def test_stacked_white_sacks_without_top_color_not_suppressed_as_ceiling(self):
        from ocupacion_linea_a import score_level_from_features

        h, w = 12, 20
        usable = np.ones((h, w), dtype=bool)
        bu = np.full((h, w), 0.20, dtype=np.float32)
        bu[6:, :] = 0.78  # Sacos blancos en mitad inferior bajo sombra del estante superior.
        vx = np.full((h, w), 0.14, dtype=np.float32)
        vx[6:, :] = 0.18
        feat = {
            'valid': True,
            'valid_cells': int(usable.sum()),
            'usable': usable,
            'observed_coverage': np.ones((h, w), dtype=np.float32),
            'density': np.full((h, w), 0.04, dtype=np.float32),
            'gradient': np.full((h, w), 32.0, dtype=np.float32),
            'color_density': np.full((h, w), 0.06, dtype=np.float32),
            'deviation': np.full((h, w), 16.0, dtype=np.float32),
            'gx': np.full((h, w), 17.0, dtype=np.float32),
            'gy': np.full((h, w), 29.0, dtype=np.float32),
            'vx': vx,
            'bu': bu,
        }
        res = score_level_from_features(feat, None, is_top_level=False)
        self.assertFalse(res['ceil_mask_active'])
        self.assertFalse(res['floor_mask_active'])
        self.assertEqual(res['state'], 'suficiente')

    def test_bicolor_printed_boxes_credit_solid_color_band(self):
        from ocupacion_linea_a import score_level_from_features

        h, w = 11, 20
        usable = np.ones((h, w), dtype=bool)
        bu = np.full((h, w), 0.05, dtype=np.float32)
        bu[:5, :] = 0.45
        color_density = np.full((h, w), 0.08, dtype=np.float32)
        color_density[6:, :] = 0.85  # Franja inferior de cartón azul/celeste liso.
        vx = np.full((h, w), 0.10, dtype=np.float32)
        vx[5, :] = 0.34  # Línea de logos centrales con bordes verticales.
        density = np.full((h, w), 0.01, dtype=np.float32)
        density[5, :] = 0.05
        gradient = np.full((h, w), 12.0, dtype=np.float32)
        gradient[5, :] = 40.0
        deviation = np.full((h, w), 5.0, dtype=np.float32)
        deviation[5, :] = 22.0
        feat = {
            'valid': True,
            'valid_cells': int(usable.sum()),
            'usable': usable,
            'observed_coverage': np.ones((h, w), dtype=np.float32),
            'density': density,
            'gradient': gradient,
            'color_density': color_density,
            'deviation': deviation,
            'gx': np.full((h, w), 20.0, dtype=np.float32),
            'gy': np.full((h, w), 20.0, dtype=np.float32),
            'vx': vx,
            'bu': bu,
        }
        bounds = ((0.0, 0.12), (2.0, 84.0), (0.0, 1.0), (1.0, 50.0))
        res = score_level_from_features(feat, bounds)
        self.assertEqual(res['state'], 'suficiente')
        self.assertGreaterEqual(res['pct'], 52.0)

    def test_recessed_upper_product_over_dark_tray_avoids_upper_band_review(self):
        from ocupacion_linea_a import compute_cell_maps, score_level_from_features

        h, w = 10, 20
        usable = np.ones((h, w), dtype=bool)
        density = np.full((h, w), 0.005, dtype=np.float32)
        density[:5, :] = 0.09  # Producto retraído al fondo visible en mitad superior.
        gradient = np.full((h, w), 8.0, dtype=np.float32)
        gradient[:5, :] = 55.0
        deviation = np.full((h, w), 3.0, dtype=np.float32)
        deviation[:5, :] = 28.0
        vx = np.full((h, w), 0.06, dtype=np.float32)
        vx[:5, :] = 0.30
        feat = {
            'valid': True,
            'valid_cells': int(usable.sum()),
            'usable': usable,
            'observed_coverage': np.ones((h, w), dtype=np.float32),
            'density': density,
            'gradient': gradient,
            'color_density': np.where(density > 0.02, 0.45, 0.01).astype(np.float32),
            'deviation': deviation,
            'gx': np.full((h, w), 24.0, dtype=np.float32),
            'gy': np.full((h, w), 20.0, dtype=np.float32),
            'vx': vx,
            'bu': np.full((h, w), 0.02, dtype=np.float32),
        }
        bounds = ((0.0, 0.13), (5.0, 90.0), (0.0, 0.80), (2.0, 50.0))
        maps = compute_cell_maps(feat, bounds)
        self.assertTrue(maps['recessed_upper_product'])
        res = score_level_from_features(feat, bounds)
        self.assertEqual(res['state'], 'suficiente')
        self.assertFalse(res['review_required'])
