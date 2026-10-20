"""Development photos follow the registered base split, including inference access."""
import unittest

import panel_modelos as panel
from particion_niveles import load_partition


class VersionHistoryTests(unittest.TestCase):
    def test_historical_real_photo_follows_renamed_inventory_path(self):
        images = {image['id']: image for image in panel.catalog()['images']}
        path = panel.current_image_path('Datos/Equilibrado_v1_20261013/reales/entrenamiento/REAL_06.jpg')
        self.assertEqual(images[path]['project_version'], 'v1')
        self.assertEqual(images[path]['name'], '06')

    def test_base_gallery_contains_learning_and_real_validation_only(self):
        images = panel.base_development_images()
        self.assertEqual(len(images), 170)
        records = load_partition(panel.ROOT)['records']
        selected = [records[image['name']] for image in images]
        self.assertEqual(sum(row['effective_split'] == 'train' for row in selected), 160)
        self.assertEqual(sum(row['effective_split'] == 'val' for row in selected), 10)
        self.assertTrue(all(row['origen'] == 'real' for row in selected
                            if row['effective_split'] == 'val'))
        self.assertTrue(all(image['project_version'] == 'v2' for image in images))

    def test_final_and_diagnostic_base_photos_cannot_be_selected_for_prediction(self):
        images = panel.base_development_images()
        data = {'images': images, 'models': [{'id': 'general.pt', 'run': None}], 'runs': []}
        config = {'action': 'predict', 'model': 'general.pt', 'conf': .25, 'nms': .7, 'imgsz': 640}
        self.assertEqual(panel.validate({**config, 'image': images[0]['id']}, data)['image'], images[0]['id'])
        inventory = panel.datasets.lider_express_inventory()
        for name, row in load_partition(panel.ROOT)['records'].items():
            if row['effective_split'] in ('reserva', 'diagnostico'):
                with self.subTest(photo=name), self.assertRaisesRegex(ValueError, 'reservada'):
                    panel.validate({**config, 'image': 'Datos/' + inventory[name]['archivo']}, data)
