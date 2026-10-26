"""Comprobar perspectiva, salientes, límites y datos degenerados."""
import unittest
import cv2
import numpy as np
from geometria_niveles import level_quadrilateral


class GeometryTests(unittest.TestCase):
    def test_straight_quad_preserves_perspective_and_input(self):
        points = np.array([[40, 30], [660, 65], [610, 240], [55, 225]], np.float32)
        original = points.copy()
        quad = np.asarray(level_quadrilateral(points, (720, 300)))
        self.assertEqual(quad.shape, (4, 2))
        distances = np.linalg.norm(quad[:, None] - points[None, :], axis=2)
        self.assertLess(distances.min(axis=1).max(), 1)
        np.testing.assert_array_equal(points, original)

    def test_irregular_sides_and_local_protrusion_fit_four_straight_edges(self):
        expected = np.array([[40, 30], [660, 65], [610, 240], [55, 225]], np.int32)
        mask = np.zeros((300, 720), np.uint8)
        cv2.fillPoly(mask, [expected], 1)
        cv2.rectangle(mask, (20, 100), (55, 125), 1, -1)
        cv2.rectangle(mask, (350, 228), (380, 244), 0, -1)
        contour = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0][0]
        quad = np.asarray(level_quadrilateral(contour, (720, 300)), dtype=np.float32)
        self.assertEqual(quad.shape, (4, 2))
        self.assertTrue(cv2.isContourConvex(quad))
        distances = np.linalg.norm(quad[:, None] - expected[None, :], axis=2)
        self.assertLess(distances.min(axis=1).max(), 6)

    def test_degenerate_inputs_do_not_fabricate_a_level(self):
        for points in ([], [[1, 2]], [[1, 1], [2, 2], [3, 3]],
                       [[1, 1], [float('nan'), 2], [3, 1]]):
            with self.subTest(points=points):
                self.assertIsNone(level_quadrilateral(points, (720, 300)))

    def test_quad_at_image_border_stays_inside(self):
        points = [[-2, 0], [720, 15], [718, 299], [0, 290]]
        quad = np.asarray(level_quadrilateral(points, (720, 300)))
        self.assertEqual(quad.shape, (4, 2))
        self.assertTrue((quad >= 0).all())
        self.assertTrue((quad <= [719, 299]).all())


if __name__ == '__main__':
    unittest.main()
