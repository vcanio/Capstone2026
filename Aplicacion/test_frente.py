"""Cobertura del frente: altura libre, huecos, carteles y estructura."""
import unittest
import cv2
import numpy as np
from ocupacion_paulo import Analyzer, front_coverage
from presentacion_niveles import occupancy_estimate


class FrontTests(unittest.TestCase):
    def test_same_front_with_different_product_heights_and_gaps(self):
        usable = np.ones((20, 20), bool)
        for top in (8, 14, 17):
            active = np.zeros_like(usable)
            active[top:19, 2:18] = True
            self.assertEqual(front_coverage(active, active, usable), 80)
        active[:, 8:12] = False
        self.assertEqual(front_coverage(active, active, usable), 60)

    def test_upper_sign_and_isolated_lower_line_do_not_cover_front(self):
        usable = np.ones((20, 20), bool)
        active = np.zeros_like(usable)
        active[:6] = True
        active[18] = True
        self.assertEqual(front_coverage(active, active, usable), 0)
        # La señal normalizada sin respaldo absoluto tampoco cuenta.
        self.assertEqual(front_coverage(usable, np.zeros_like(usable), usable), 0)

    def test_mask_gaps_are_never_joined_and_small_mask_has_no_measurement(self):
        active = np.ones((20, 20), bool)
        usable = np.zeros_like(active)
        usable[8] = True
        usable[10] = True
        self.assertEqual(front_coverage(active, active, usable), 0)
        self.assertIsNone(front_coverage(active, active, np.zeros_like(usable)))

    def test_empty_rails_and_short_products_through_analyzer(self):
        image = np.full((480, 960, 3), 70, np.uint8)
        for y in (410, 420):
            cv2.line(image, (20, y), (940, y), (90, 90, 90), 3)
        mask = np.ones(image.shape[:2], np.uint8)
        empty = Analyzer(image, version='v2', front_mode=True).analyze(mask)
        self.assertLess(empty['front_signal_pct'], 30)
        for x in range(80, 850, 100):
            cv2.rectangle(image, (x, 310), (x+70, 400), (240, 240, 240), -1)
            cv2.circle(image, (x+35, 350), 18, (20, 30, 120), 4)
        occupied = Analyzer(image, version='v2', front_mode=True).analyze(mask)
        self.assertEqual(occupancy_estimate(occupied, 'v2')['state'], 'suficiente')
        legacy = Analyzer(image, version='v2').analyze(mask)
        self.assertNotIn('front_signal_pct', legacy)

    def test_front_estimate_is_not_fallback_area_and_respects_review(self):
        measurement = dict(status='medido', interpretation_policy='front_coverage_v1',
                           front_signal_pct=80, combined_signal_pct=20)
        self.assertEqual(occupancy_estimate(measurement, 'v2')['pct'], 80)
        measurement['review_required'] = True
        self.assertEqual(occupancy_estimate(measurement, 'v2')['state'], 'revisar')
        measurement.update(review_required=False, front_signal_pct=None)
        self.assertIsNone(occupancy_estimate(measurement, 'v2')['pct'])


if __name__ == '__main__':
    unittest.main()
