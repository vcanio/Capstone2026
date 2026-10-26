"""Detectar filtracion y referencias invalidas antes de usar la particion fijada."""
import copy
import unittest
from unittest.mock import patch

from particionar_lider_express import PARTITION, annotation_counts, make_records, read, scene_map, validate


class PartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = read(PARTITION / 'grupos_escena.json')
        cls.records, _ = make_records(cls.config, verify_images=False)

    def test_counts_and_real_coverage(self):
        summary = validate(self.records)
        self.assertEqual(sum(s['total'] for s in summary.values()), 296)
        self.assertEqual([summary[s]['base'] for s in ('train', 'val', 'test')], [160, 40, 36])
        self.assertEqual([summary[s]['estados_base_reales']['reponer'] for s in ('train', 'val', 'test')], [2, 1, 1])

    def test_default_verification_still_rejects_missing_image_files(self):
        with patch('pathlib.Path.is_file', return_value=False):
            with self.assertRaisesRegex(ValueError, 'Imagen ausente'):
                make_records(self.config)

    def test_obstacle_variant_cannot_cross_original(self):
        records = copy.deepcopy(self.records)
        row = next(r for r in records if r['task_id'] == 22)
        row['split'] = 'test' if row['split'] == 'train' else 'train'
        with self.assertRaisesRegex(ValueError, 'familia'):
            validate(records)

    def test_whole_family_cannot_cross_scene(self):
        records = copy.deepcopy(self.records)
        family = records[0]['familia']
        for row in records:
            if row['familia'] == family:
                row['split'] = 'test'
        with self.assertRaisesRegex(ValueError, 'escenas'):
            validate(records)

    def test_missing_real_restock_cannot_pass_on_synthetics(self):
        records = copy.deepcopy(self.records)
        for row in records:
            if row['split'] == 'val' and row['origen'] == 'real':
                row['estados'].pop('reponer', None)
        with self.assertRaisesRegex(ValueError, 'cobertura real'):
            validate(records)

    def test_duplicate_group_membership_rejected(self):
        config = copy.deepcopy(self.config)
        config['grupos'][1]['familias'].append(config['grupos'][0]['familias'][0])
        with self.assertRaisesRegex(ValueError, 'dos grupos'):
            scene_map(config)

    def test_unassigned_state_does_not_inherit_default(self):
        snapshot = read(PARTITION / 'fuentes/tarea_19.json')
        snapshot['annotations']['shapes'][0]['attributes'] = []
        with self.assertRaisesRegex(ValueError, 'Estado ausente'):
            annotation_counts(snapshot)

    def test_invalid_geometry_rejected(self):
        snapshot = read(PARTITION / 'fuentes/tarea_19.json')
        snapshot['annotations']['shapes'][0]['points'] = [0, 0, 10, 10, 0, 10, 10, 0]
        with self.assertRaisesRegex(ValueError, 'Geometria invalida'):
            annotation_counts(snapshot)


if __name__ == '__main__':
    unittest.main()
