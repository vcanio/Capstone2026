"""El cierre conserva validación, repaso e identidad del padre sin ejecutar ML."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import refuerzo_cierre_v3 as c
import preparacion_v3 as p


def image(name, split, scene, sha):
    return {'name': name, 'path': 'Datos/' + name, 'sha256': sha, 'split': split,
            'origen': 'real', 'familia': scene, 'grupo_escena': scene}


class ClosingTests(unittest.TestCase):
    def setUp(self):
        self.old = [image('a.jpg', 'train', 'a', 'a'), image('b.jpg', 'val', 'b', 'b')]
        self.new = [image('n.jpg', 'train', 'n', 'n')]
        self.rows = self.old + self.new
        self.plan = {'parent_partition': 'old.json', 'parent_manifest': 'parent.json',
                     'initial_model': 'best.pt', 'initial_model_sha256': 'model-hash',
                     'selected_train': ['a.jpg', 'n.jpg'], 'selected_val': ['b.jpg'],
                     'baseline_path': 'baseline.json'}
        self.part = {'schema_version': 5, 'id': 'closure', 'plan_sha256': 'plan-hash',
                     'base_partition_path': 'old.json', 'imagenes': copy.deepcopy(self.rows),
                     'resumen': c.summarize(self.rows)}
        self.selection = {'plan_sha256': 'plan-hash', 'required_initial_model': 'best.pt',
                          'required_initial_model_sha256': 'model-hash', 'baseline_sha256': 'baseline-hash'}

    def validate(self, value):
        with patch.object(c, 'get_plan', return_value=self.plan), \
             patch.object(c, 'incoming_rows', return_value=self.new), \
             patch.object(p, 'partition', return_value={'imagenes': self.old}), \
             patch.object(p, 'read', side_effect=lambda path: {'imagenes': self.old, 'schema_version': 4}), \
             patch.object(p, 'v3_image_path'):
            return c.validate_partition(Path('.'), 'Datos/Registros/Particiones/closure/particion.json', value)

    def test_addition_preserves_old_rows(self):
        self.assertEqual(self.validate(self.part), self.part)

    def test_validation_cannot_be_reassigned_even_if_summary_is_adjusted(self):
        changed = copy.deepcopy(self.part)
        changed['imagenes'][1]['split'] = 'train'
        changed['resumen'] = c.summarize(changed['imagenes'])
        with self.assertRaises(ValueError):
            self.validate(changed)

    def test_replay_cannot_be_removed(self):
        changed = copy.deepcopy(self.part)
        changed['imagenes'].pop(0)
        changed['resumen'] = c.summarize(changed['imagenes'])
        with self.assertRaises(ValueError):
            self.validate(changed)

    def test_duplicate_bytes_are_rejected(self):
        changed = copy.deepcopy(self.rows)
        changed[-1]['sha256'] = changed[0]['sha256']
        with self.assertRaises(ValueError):
            c.validate_rows(changed)

    def test_related_scene_cannot_cross_validation(self):
        changed = copy.deepcopy(self.rows)
        changed[-1]['grupo_escena'] = 'b'
        with self.assertRaises(ValueError):
            c.validate_rows(changed)

    def test_test_is_never_a_development_split(self):
        changed = copy.deepcopy(self.rows)
        changed[-1]['split'] = 'test'
        with self.assertRaises(ValueError):
            c.validate_rows(changed)

    def test_selection_pins_parent_baseline_and_complete_validation(self):
        with patch.object(p, 'partition', return_value=self.part), \
             patch.object(c, 'get_plan', return_value=self.plan), \
             patch.object(p, 'digest', return_value='baseline-hash'):
            args = (Path('.'), {'partition_path': 'p'}, self.rows)
            self.assertEqual(c.choose(*args, self.selection), (['a.jpg', 'n.jpg'], []))
            for key in ('required_initial_model_sha256', 'baseline_sha256'):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    c.choose(*args, {**self.selection, key: 'changed'})
            with self.assertRaises(ValueError):
                c.choose(Path('.'), {'partition_path': 'p'}, [self.rows[0], self.rows[2]], self.selection)


if __name__ == '__main__':
    unittest.main()
