"""Errores de estado, niveles omitidos, duplicados y falsas alertas del criterio v2."""
import unittest
from pathlib import Path
import tempfile
from types import SimpleNamespace

import numpy as np
from PIL import Image

from evaluar_niveles_v2 import aggregate, evaluate_masks, evaluate_split


class ThreeStateMetricTests(unittest.TestCase):
    def test_wrong_state_and_abstention_are_not_correct_alerts(self):
        a, b, c = (np.eye(3, dtype=bool)[i:i+1].repeat(3, axis=0) for i in range(3))
        detail = evaluate_masks([(0, a), (1, b), (2, c)], [(2, a), (0, b), (2, c)])
        summary = aggregate([detail])
        self.assertEqual(summary['reposicion']['omitidas'], 1)
        self.assertEqual(summary['reposicion']['falsas_alertas'], 1)
        self.assertEqual(summary['reposicion']['acertadas'], 0)
        self.assertEqual(summary['por_clase']['no_evaluable']['tp'], 1)
        self.assertEqual(summary['matriz_confusion']['reponer']['no_evaluable'], 1)

    def test_unmatched_levels_and_duplicate_predictions_count(self):
        mask = np.ones((2, 2), dtype=bool)
        missing = evaluate_masks([(0, mask)], [])
        duplicate = evaluate_masks([(0, mask)], [(0, mask), (0, mask)])
        summary = aggregate([missing, duplicate])
        self.assertEqual(summary['reposicion']['acertadas'], 1)
        self.assertEqual(summary['reposicion']['omitidas'], 1)
        self.assertEqual(summary['reposicion']['falsas_alertas'], 1)
        self.assertEqual(summary['reposicion']['recall'], 0.5)
        self.assertEqual(summary['reposicion']['precision'], 0.5)
        self.assertEqual(summary['matriz_confusion']['reponer']['no_detectado'], 1)

    def test_empty_metrics_are_unavailable_instead_of_perfect(self):
        result = aggregate([evaluate_masks([], [])])
        self.assertIsNone(result['reposicion']['recall'])
        self.assertIsNone(result['reposicion']['precision'])

    def test_iou_threshold_is_respected(self):
        a = np.array([[1, 1], [0, 0]], dtype=bool)
        b = np.array([[1, 0], [0, 1]], dtype=bool)
        summary = aggregate([evaluate_masks([(0, a)], [(0, b)], minimum_iou=0.5)])
        self.assertEqual(summary['reposicion']['acertadas'], 0)

    def test_predicted_masks_are_evaluated_at_original_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / 'foto.png'
            Image.new('RGB', (12, 10), 'red').save(image)
            label = root / 'foto.txt'
            label.write_text('0 0 0 1 0 1 1 0 1\n')
            class Tensor:
                def __init__(self, value):
                    self.value = value
                def cpu(self):
                    return self
                def numpy(self):
                    return np.asarray(self.value)
                def tolist(self):
                    return self.value
            result = SimpleNamespace(boxes=SimpleNamespace(cls=Tensor([0])),
                                     masks=SimpleNamespace(data=Tensor(np.ones((1, 10, 12)))))
            calls = []
            def predict(source, **kwargs):
                calls.append(kwargs)
                return [result]
            summary, details = evaluate_split(SimpleNamespace(predict=predict),
                                               [{'imagen': str(image), 'etiqueta': str(label)}], 'cpu', 64)
            self.assertEqual(summary['reposicion']['acertadas'], 1)
            self.assertEqual(summary['reposicion']['precision'], 1)
            self.assertEqual(details[0]['parejas'][0]['iou_mascara'], 1)
            self.assertEqual(calls[0]['conf'], 0.25)
            self.assertTrue(calls[0]['retina_masks'])


if __name__ == '__main__':
    unittest.main()
