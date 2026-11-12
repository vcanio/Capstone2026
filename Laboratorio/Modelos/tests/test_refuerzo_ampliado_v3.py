"""Migración explícita de escenas revisadas sin usar la reserva para seleccionar."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import preparacion_v3 as p
import refuerzo_ampliado_v3 as a


def image(name, split, scene, family=None):
    return {'name': name, 'path': 'Datos/' + name, 'sha256': name, 'split': split,
            'origen': 'real', 'familia': family or scene, 'grupo_escena': scene}


class ExpandedClosingTests(unittest.TestCase):
    def setUp(self):
        self.original = [image('old.jpg', 'train', 'old'), image('marked.jpg', 'val', 'new', 'f1'),
                         image('view.jpg', 'val', 'new', 'f2'), image('variant.jpg', 'val', 'bridge', 'f2'),
                         image('val.jpg', 'val', 'reserved-dev')]
        self.rows = a.promoted_rows(self.original, {'marked.jpg'})
        self.plan = {'selected_train': ['old.jpg', 'marked.jpg', 'view.jpg', 'variant.jpg'],
                     'selected_val': ['val.jpg'], 'moved_val_to_train': ['marked.jpg', 'view.jpg', 'variant.jpg'],
                     'reserved_inventory': 'reserved.json', 'initial_model': 'official/best.pt',
                     'initial_model_sha256': '7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a',
                     'baseline_path': 'baseline.json'}
        self.part = {'schema_version': 6, 'id': 'expanded', 'base_partition_path': a.PARENT,
                     'imagenes': self.rows, 'resumen': a.summarize(self.rows), 'plan_sha256': 'plan'}
        self.reserve = {'files': [{'sha256': 'unseen'}], 'exact_duplicates_known_sources': []}

    def validate(self, part):
        with patch.object(a, 'get_plan', return_value=self.plan), \
             patch.object(a, 'reviewed_hashes', return_value={'marked.jpg'}), \
             patch.object(p, 'partition', return_value={'imagenes': self.original}), \
             patch.object(p, 'read', return_value=self.reserve):
            return a.validate_partition(Path('.'), 'Datos/Registros/Particiones/expanded/particion.json', part)

    def test_related_views_and_families_move_transitively(self):
        self.assertEqual([x['name'] for x in self.rows if x['split'] == 'val'], ['val.jpg'])
        self.assertEqual(self.original[1]['split'], 'val')
        self.assertEqual(self.validate(self.part), self.part)

    def test_previously_trained_sources_cannot_return_to_validation(self):
        changed = copy.deepcopy(self.part)
        changed['imagenes'][0]['split'] = 'val'
        changed['resumen'] = a.summarize(changed['imagenes'])
        with self.assertRaises(ValueError):
            self.validate(changed)

    def test_partial_scene_migration_is_rejected(self):
        changed = copy.deepcopy(self.part)
        changed['imagenes'][2]['split'] = 'val'
        changed['resumen'] = a.summarize(changed['imagenes'])
        with self.assertRaises(ValueError):
            self.validate(changed)

    def test_unrelated_validation_cannot_be_promoted(self):
        changed = copy.deepcopy(self.part)
        changed['imagenes'][-1]['split'] = 'train'
        changed['resumen'] = a.summarize(changed['imagenes'])
        with self.assertRaises(ValueError):
            self.validate(changed)

    def test_reserved_exact_duplicate_blocks_preparation(self):
        self.reserve['files'][0]['sha256'] = 'marked.jpg'
        with self.assertRaises(ValueError):
            self.validate(self.part)

    def test_migration_receipt_cannot_omit_related_sources(self):
        self.plan['moved_val_to_train'].pop()
        with self.assertRaises(ValueError):
            self.validate(self.part)

    def test_rejected_candidate_cannot_be_initial_model(self):
        self.plan['initial_model_sha256'] = 'candidate'
        with self.assertRaises(ValueError):
            self.validate(self.part)

    def test_selection_rejects_changed_baseline_or_missing_levels_image(self):
        selection = {'plan_sha256': 'plan', 'required_initial_model': self.plan['initial_model'],
                     'required_initial_model_sha256': self.plan['initial_model_sha256'], 'baseline_sha256': 'baseline'}
        with patch.object(p, 'partition', return_value=self.part), \
             patch.object(a, 'get_plan', return_value=self.plan), patch.object(p, 'digest', return_value='baseline'):
            args = (Path('.'), {'partition_path': 'p'}, self.rows)
            self.assertEqual(a.choose(*args, selection), (self.plan['selected_train'], []))
            with self.assertRaises(ValueError):
                a.choose(*args, {**selection, 'baseline_sha256': 'changed'})
            with self.assertRaises(ValueError):
                a.choose(Path('.'), {'partition_path': 'p'}, self.rows[:-1], selection)


class HumanRevisionPlanTests(unittest.TestCase):
    def setUp(self):
        self.folder = a.BASE + '/revisiones/humana_1'
        self.reference = self.folder + '/plan_particion.json'
        self.plan = {'approved_by': 'Vicente', 'authorization': 'Revisado y ajustado en CVAT.',
                     'revision_of_plan': a.PLAN, 'revision_of_plan_sha256': 'sha',
                     'source_snapshot': self.folder + '/snapshot_cvat.json',
                     'human_review_receipt': self.folder + '/cambios.json',
                     'evidence_sha256': {ref: 'sha' for ref in [a.PLAN, self.folder + '/snapshot_cvat.json', self.folder + '/cambios.json']}}

    def get(self, reference=None):
        with patch.object(p, 'digest', return_value='sha'), patch.object(p, 'read', return_value=self.plan):
            return a.get_plan(Path('.'), {'plan_path': reference or self.reference, 'plan_sha256': 'sha'})

    def test_human_revision_can_pin_new_snapshot_without_replacing_original(self):
        self.assertEqual(self.get(), self.plan)

    def test_revision_cannot_lose_original_plan_provenance(self):
        self.plan['revision_of_plan_sha256'] = 'other'
        with self.assertRaises(ValueError):
            self.get()

    def test_revision_cannot_reuse_old_snapshot_or_escape_review_directory(self):
        self.plan['source_snapshot'] = a.BASE + '/source_snapshot.json'
        with self.assertRaises(ValueError):
            self.get()
        with self.assertRaises(ValueError):
            self.get(a.BASE + '/revisiones/../plan_particion.json')


if __name__ == '__main__':
    unittest.main()
