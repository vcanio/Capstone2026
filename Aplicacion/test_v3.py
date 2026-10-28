"""Comportamiento de alcance e inferencia de V3."""
from copy import deepcopy
import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from vision_v3 import apply_scope
from test_lite import LiteTests, photo
from inferencia import ModelRunner
from ocupacion_paulo import lower_band_is_low_signal

class LowerBandTests(unittest.TestCase):
    def test_weak_lower_band_and_evidence_of_products(self):
        self.assertTrue(lower_band_is_low_signal(True, 1, 11.27, 0, 0, .015))
        self.assertFalse(lower_band_is_low_signal(True, 1, 11.27, 0, 0, .3))
        self.assertFalse(lower_band_is_low_signal(True, 1, 11.27, 20, 0, 0))
        self.assertFalse(lower_band_is_low_signal(True, .1, 11.27, 0, 0, 0))

class ScopeTests(unittest.TestCase):
    def test_ambiguous_signal_keeps_explanation(self):
        level = {'display_polygon': [(10, 10), (90, 10)],
                 'occupancy': {'review_reason': 'Posible cartel; revisar.'},
                 'occupancy_estimate': {'pct': None, 'state': 'revisar', 'label': 'Revisar · señal ambigua'}}
        apply_scope([level], 100, 100)
        self.assertEqual(level['notice'], 'Posible cartel; revisar.')
        self.assertEqual(level['occupancy_estimate']['label'], 'Revisar · señal ambigua')
        self.assertIsNone(level['occupancy_estimate']['pct'])

    def test_frame_contact_requires_review_without_changing_geometry(self):
        level = {'display_polygon': [(0, 10), (90, 90)],
                 'occupancy_estimate': {'pct': 80, 'state': 'suficiente', 'label': 'Suficiente'}}
        points = deepcopy(level['display_polygon'])
        apply_scope([level], 100, 100)
        self.assertEqual(level['occupancy_estimate']['state'], 'revisar')
        self.assertEqual(level['scope'], 'Solo zona visible')
        self.assertEqual(level['display_polygon'], points)

    def test_scope_uses_original_mask_contact_after_visual_adjustment(self):
        level = {'display_polygon': [(10, 10), (90, 90)], 'near_frame': True}
        apply_scope([level], 100, 100)
        self.assertEqual(level['scope'], 'Solo zona visible')

class RunnerV3Tests(unittest.TestCase):
    def setUp(self):
        LiteTests.setUp(self)
        path = self.root / 'modelos.json'
        value = json.loads(path.read_text())
        value['default_model'] = 'fixture'
        value['models'][0]['classes'] = ['Nivel']
        path.write_text(json.dumps(value))

    def test_inference_runs_without_visibility_and_with_legacy_person_value(self):
        runner = ModelRunner(self.root)
        with self.assertRaisesRegex(ValueError, '0,40'):
            runner.analyze(photo(), 'fixture', .39)
        model = MagicMock()
        model.predict.return_value = [object()]
        runner.models['fixture'] = model
        torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
        ultralytics = SimpleNamespace(YOLO=MagicMock(), settings=SimpleNamespace(update=lambda value: None))
        with patch.dict('sys.modules', {'torch': torch, 'ultralytics': ultralytics}), \
             patch('inferencia.draw_result', side_effect=lambda image, result: (image, [])):
            for visibility in (None, 'person', 'occluded'):
                result = runner.analyze(photo(), 'fixture', .6, visibility=visibility)
                self.assertNotIn('visibility', result)
        self.assertEqual(model.predict.call_count, 3)
