"""Línea A en el flujo portable: máscaras, orden, presentación y procedencia."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

import cv2
import numpy as np

from inferencia import analyze_edges
from ocupacion_linea_a import analyze_gondola_rgb, METHOD_LINEA_A, INTERPRETATION_POLICY
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
