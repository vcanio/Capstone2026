"""La visibilidad de V3 limita las recomendaciones y no altera la geometría."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch
from PIL import Image
from vision_v3 import apply_scope, person_result, visibility_check
from test_lite import LiteTests, photo
from inferencia import ModelRunner


class ScopeTests(unittest.TestCase):
    def test_ambiguous_signal_keeps_its_explanation_without_replenishment_claim(self):
        level = self.level()
        level['occupancy'] = {'review_required': True, 'review_reason': 'Posible cartel; revisar.'}
        level['occupancy_estimate'] = {'pct': None, 'state': 'revisar',
                                       'label': 'Revisar · señal ambigua', 'color': '#a16207'}
        apply_scope([level], 'clear', 100, 100)
        self.assertEqual(level['notice'], 'Posible cartel; revisar.')
        self.assertEqual(level['occupancy_estimate']['label'], 'Revisar · señal ambigua')
        self.assertIsNone(level['occupancy_estimate']['pct'])

    def level(self, pct=80):
        return {'display_polygon': [(10, 10), (90, 10), (90, 90), (10, 90)],
                'occupancy_estimate': {'pct': pct, 'state': 'suficiente', 'label': 'Suficiente', 'color': '#16a34a'}}

    def test_partial_never_claims_whole_level_sufficient_or_changes_points(self):
        level = self.level()
        points = deepcopy(level['display_polygon'])
        apply_scope([level], 'partial', 100, 100)
        self.assertEqual(level['occupancy_estimate']['pct'], 80)
        self.assertEqual(level['occupancy_estimate']['state'], 'revisar')
        self.assertEqual(level['scope'], 'Solo zona visible')
        self.assertEqual(level['display_polygon'], points)

    def test_crop_indication_overrides_clear_and_object_blocks_measurement(self):
        level = self.level()
        level['display_polygon'][0] = (0, 10)
        apply_scope([level], 'clear', 100, 100)
        self.assertEqual(level['occupancy_estimate']['state'], 'revisar')
        level = self.level()
        apply_scope([level], 'occluded', 100, 100)
        self.assertIsNone(level['occupancy_estimate']['pct'])
        self.assertEqual(level['occupancy_estimate']['state'], 'revisar')

    def test_clear_keeps_reading_person_has_no_contours_or_replenishment(self):
        level = self.level()
        apply_scope([level], 'clear', 100, 100)
        self.assertEqual(level['occupancy_estimate']['state'], 'suficiente')
        result = person_result(Image.new('RGB', (100, 100)), 'v3', 'yolo_paulo_v2')
        self.assertEqual(result['detections'], [])
        self.assertEqual(result['photo_status'], 'gondola_tapada')
        self.assertNotIn('occupancy', result)
        for value in (None, '', 'automatic'):
            with self.assertRaises(ValueError): visibility_check(value)


class RunnerV3Tests(unittest.TestCase):
    def setUp(self):
        LiteTests.setUp(self)
        path = self.root / 'modelos.json'
        value = json.loads(path.read_text())
        value['default_model'] = 'fixture'
        value['models'][0]['classes'] = ['Nivel']
        path.write_text(json.dumps(value))

    # Solo pruebas V3 propias; los contratos V1/V2 se ejecutan con LiteTests.
    def test_minimum_and_visibility_are_checked_before_inference(self):
        runner = ModelRunner(self.root)
        with self.assertRaisesRegex(ValueError, 'visibilidad|Indica'):
            runner.analyze(photo(), 'fixture', .6)
        with self.assertRaisesRegex(ValueError, '0,60'):
            runner.analyze(photo(), 'fixture', .59, visibility='clear')
        with patch.dict('sys.modules', {'torch': None, 'ultralytics': None}):
            result = runner.analyze(photo(), 'fixture', .6, visibility='person')
        self.assertEqual(result['photo_status'], 'gondola_tapada')
        self.assertTrue(runner.available()[0]['geometry_only'])
