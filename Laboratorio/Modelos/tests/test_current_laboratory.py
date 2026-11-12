"""El catálogo operativo mantiene la base estable y evita cargar inventarios antiguos."""
import copy
import gzip
import json
import unittest
from unittest.mock import patch

import panel_modelos as panel


class CurrentLaboratoryTests(unittest.TestCase):
    def fixture(self):
        stable = 'Experimentos/stable/entrenamiento/weights/best.pt'
        training = {
            'supported': True, 'vision_release': {'run': 'stable', 'model': stable},
            'initial_models': [{'id': stable}, {'id': 'general.pt'}],
            'defaults': {'model': stable, 'epochs': 40, 'lr': .0001, 'patience': 10},
            'runs': [dict(id=name, ready=ready, best=best) for name, ready, best in
                     [('stable', True, True), ('retired', True, False),
                      ('candidate', True, True), ('running', False, False)]],
            'exports': [{'id': 'old', 'partition_id': 'old'}, {'id': 'new', 'partition_id': 'active'}],
            'selections': [{'id': 'old', 'source': 'old'}, {'id': 'new', 'source': 'new'}],
            'module_pilot': {'tasks': {'train': {}}}}
        prediction = {'models': [{'id': 'candidate.pt', 'run': 'candidate'},
                                 {'id': stable, 'run': 'stable'}],
                      'runs': [{'id': name} for name in ('retired', 'candidate', 'stable')]}
        return training, prediction

    def get_catalog(self, training, prediction):
        with patch.object(panel.training_v3, 'catalog', return_value=copy.deepcopy(training)), \
             patch.object(panel.prediction_v3, 'catalog', return_value=copy.deepcopy(prediction)), \
             patch.object(panel.v3, 'catalog_status', return_value={'partition_id': 'active'}), \
             patch.object(panel, 'inventory', side_effect=AssertionError('Legacy inventory read')), \
             patch.object(panel, 'catalog', side_effect=AssertionError('Legacy catalog read')):
            return panel.current_catalog()

    def test_stable_first_active_partition_and_candidates_without_legacy_reads(self):
        training, prediction = self.fixture()
        result = self.get_catalog(training, prediction)
        current = result['v3_training']
        self.assertEqual(current['initial_models'], training['initial_models'][:1])
        self.assertEqual([r['id'] for r in current['runs']], ['stable', 'candidate', 'running'])
        self.assertEqual([e['id'] for e in current['exports']], ['new'])
        self.assertEqual([s['id'] for s in current['selections']], ['new'])
        self.assertIsNone(current['module_pilot'])
        self.assertEqual(current['defaults']['name'], 'v3_refuerzo_actual')
        self.assertEqual(result['v3_prediction']['models'][0]['id'], training['vision_release']['model'])
        self.assertEqual([r['id'] for r in result['v3_prediction']['runs']], ['candidate', 'stable'])
        self.assertTrue(all(result[key] == [] for key in ('runs', 'models', 'images', 'datasets')))

    def test_missing_stable_weights_or_register_does_not_fall_back_to_general(self):
        training, prediction = self.fixture()
        for change in ({'initial_models': [{'id': 'general.pt'}]}, {'vision_release': None}):
            with self.subTest(change=change):
                result = self.get_catalog({**training, **change}, prediction)['v3_training']
                self.assertFalse(result['supported'])
                self.assertEqual(result['initial_models'], [])
                self.assertIn('best.pt', result['error'])

    def test_prepared_refuerzo_is_visible_without_changing_official_partition(self):
        training, prediction = self.fixture()
        stable = training['vision_release']['model']
        training['exports'].append({'id': 'closing', 'partition_id': 'closing_partition'})
        training['selections'].append({'id': 'closing', 'source': 'closing', 'required_initial_model': stable})
        result = self.get_catalog(training, prediction)['v3_training']
        self.assertEqual([e['id'] for e in result['exports']], ['new', 'closing'])
        self.assertEqual([s['id'] for s in result['selections']], ['new', 'closing'])

    def test_current_and_legacy_caches_are_separate_and_both_invalidate(self):
        panel.invalidate_catalog()
        self.addCleanup(panel.invalidate_catalog)
        with patch.object(panel, 'catalog', return_value={'scope': 'legacy'}) as legacy, \
             patch.object(panel, 'current_catalog', return_value={'scope': 'current'}) as current:
            old = panel.cached_catalog()
            active = panel.cached_catalog(current=True)
            self.assertEqual(json.loads(gzip.decompress(active[2])), {'scope': 'current'})
            self.assertNotEqual(old[3], active[3])
            self.assertIs(active, panel.cached_catalog(current=True))
            self.assertEqual(current.call_count, 1)
            self.assertEqual(legacy.call_count, 1)
            panel.invalidate_catalog()
            panel.cached_catalog(current=True)
            panel.cached_catalog()
            self.assertEqual(current.call_count, 2)
            self.assertEqual(legacy.call_count, 2)
