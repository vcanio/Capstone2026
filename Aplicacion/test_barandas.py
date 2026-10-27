"""Regresiones de señal interior; no usan pesos ni imágenes de test."""
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from ocupacion_paulo import Analyzer, fragmented_lower_rails


class FragmentedRailTests(unittest.TestCase):
    def scene(self):
        image = np.full((300, 900, 3), 50, np.uint8)
        for y in (235, 250):
            for x in range(30, 820, 130):
                cv2.line(image, (x, y), (x+118, y), (110, 110, 110), 5)
        return image

    def measure(self, image, fragments=True):
        analyzer = Analyzer(image, version='v2')
        mask = np.ones(image.shape[:2], np.uint8)
        if fragments:
            result = analyzer.analyze(mask)
        else:
            with patch('ocupacion_paulo.fragmented_lower_rails',
                       side_effect=lambda edges, cell: np.zeros_like(edges)):
                result = analyzer.analyze(mask)
        return analyzer, result

    def test_fragmented_empty_rail_does_not_return_as_texture(self):
        before, old = self.measure(self.scene(), fragments=False)
        after, new = self.measure(self.scene())
        self.assertTrue(after.structures.any())
        self.assertLess(new['combined_signal_pct'], 1)
        self.assertFalse(after.signal.any())
        self.assertLessEqual(new['combined_signal_pct'], old['combined_signal_pct'])

    def test_exclusion_does_not_amplify_background_or_remove_products_above_rail(self):
        image = self.scene()
        # Contrasting white and colored products; the dark background has
        # a weak lighting gradient which must not be promoted after removal.
        image[:220] += np.linspace(0, 8, 220).astype(np.uint8)[:, None, None]
        cv2.rectangle(image, (120, 115), (230, 230), (240, 240, 240), -1)
        cv2.rectangle(image, (420, 115), (530, 230), (220, 30, 50), -1)
        for x in (175, 475):
            cv2.circle(image, (x, 170), 20, (30, 30, 30), 4)
        before, old = self.measure(image, fragments=False)
        after, new = self.measure(image)
        self.assertLessEqual(new['combined_signal_pct'], old['combined_signal_pct'])
        self.assertFalse((after.signal & ~before.signal).any())
        # Inspect cells clear of the rail; mixed product/rail cells may lose
        # the rail contribution while retaining the product above it.
        for left, right in ((130, 220), (430, 520)):
            previous = before.signal[130:195, left:right].sum()
            self.assertGreater(previous, 0)
            self.assertGreaterEqual(after.signal[130:195, left:right].sum(), .95*previous)

    def test_local_product_edges_and_vertical_posts_are_not_extended_into_rails(self):
        edges = np.zeros((300, 900), np.uint8)
        cv2.rectangle(edges, (380, 210), (490, 270), 255, 2)
        cv2.line(edges, (100, 40), (100, 280), 255, 2)
        self.assertFalse(fragmented_lower_rails(edges, 24).any())

    def test_large_missing_spans_are_not_painted_as_structure(self):
        edges = np.zeros((300, 900), np.uint8)
        cv2.line(edges, (10, 240), (300, 240), 255, 2)
        cv2.line(edges, (600, 240), (890, 240), 255, 2)
        blocked = fragmented_lower_rails(edges, 24)
        self.assertTrue(blocked.any())
        self.assertFalse(blocked[:, 350:550].any())


if __name__ == '__main__':
    unittest.main()
