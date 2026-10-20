from conjuntos import dataset_directory
"""Regresiones: estados exportados, escenas y errores de alertas de stock."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import datos_modelos as datasets
from comparar_niveles import evaluate_masks, aggregate
from niveles_modelos import STATES, CLASS_NAMES
import test_datos_modelos as fixtures


class LevelDataTests(unittest.TestCase):
    def setUp(self):
        fixtures.DataTests.setUp(self)
        self.snapshot = fixtures.fixture()
        self.snapshot['scope'] = 'Nivel_estados'
        self.snapshot['sources'] = [{'job_id': 33, 'project_id': 6, 'task_id': 15}]
        self.snapshot['labels'] = [{'id': 20, 'name': 'Nivel', 'attributes': [
            {'id': 77, 'name': 'estado', 'default_value': 'pendiente', 'values': ['pendiente', *STATES]}]}]
        self.snapshot['annotations']['shapes'] = [
            {'id': i*10+j, 'frame': i, 'type': 'polygon', 'label_id': 20,
             'points': [1, 1+j*4, 18, 1+j*4, 18, 3+j*4, 1, 3+j*4],
             'attributes': [{'spec_id': 77, 'value': state}]}
            for i in range(3) for j, state in enumerate(STATES)]

    def test_states_exported_and_optional_attributes_not_required(self):
        before = copy.deepcopy(self.snapshot)
        report, rows = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['bloqueos_entrenamiento'], 0)
        self.assertEqual(report['incidencias'], [])
        self.assertEqual([row.split()[0] for row in rows['01']], ['0', '1', '2', '3'])
        self.assertEqual(self.snapshot, before)
        self.assertEqual(report['estados_por_split']['train']['no_evaluable'], 2)

    def test_pending_blocks_whole_image_not_silent_background(self):
        self.snapshot['annotations']['shapes'][0]['attributes'][0]['value'] = 'pendiente'
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['bloqueos_entrenamiento'], 1)

    def test_non_evaluable_geometry_still_blocks(self):
        self.snapshot['annotations']['shapes'][3]['points'] = [1, 1, 18, 18, 18, 1, 1, 18]
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['bloqueos_entrenamiento'], 1)

    def test_scene_split_keeps_views_together_and_preserves_reserve(self):
        report, _ = datasets.inspect(self.snapshot, ['01'])
        self.assertEqual([i['split'] for i in report['imagenes']], ['val', 'val', 'train'])
        datasets.write(self.root / 'Datos/Registros/reserva_evaluacion.json',
                       {'image_ids': [], 'groups': ['a']})
        with self.assertRaises(ValueError):
            datasets.inspect(self.snapshot, ['03'])

    def test_missing_training_state_blocks_even_if_present_in_validation(self):
        for s in self.snapshot['annotations']['shapes']:
            if s['frame'] < 2 and s['attributes'][0]['value'] == 'vacio':
                s['attributes'][0]['value'] = 'suficiente'
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertTrue(any('Sin ejemplos de vacio' in i['problema'] for i in report['incidencias']))

    def test_review_prepare_and_reuse_keep_state_classes(self):
        with patch.object(datasets, 'fetch_snapshot', return_value=self.snapshot):
            version = datasets.import_jobs({'jobs': [33], 'validation': ['03']})
            self.assertEqual(version['scope'], 'Nivel_estados')
            approved = datasets.approve({'id': version['id'], 'reviewer': 'Revisor', 'reviewed': True})
            self.assertEqual(approved['state'], 'lista_niveles')
            self.assertEqual(datasets.import_jobs({'jobs': [33], 'validation': ['03']})['id'], version['id'])
        run = self.root / 'run'; run.mkdir()
        datasets.prepare_version(datasets.version_path(version['id']), run)
        manifest = datasets.read(run / 'manifest.json')
        self.assertEqual(manifest['clases'], CLASS_NAMES)
        self.assertFalse((run / 'dataset_modulos').exists())
        lines = (dataset_directory(datasets.ROOT, run) / 'labels/train/01.txt').read_text().splitlines()
        self.assertEqual([line.split()[0] for line in lines], ['0', '1', '2', '3'])


class AlertMetricTests(unittest.TestCase):
    def test_localization_is_not_state_accuracy_and_abstention_does_not_hide_miss(self):
        a = np.array([[True, False], [False, False]])
        b = np.array([[False, True], [False, False]])
        c = np.array([[False, False], [True, False]])
        truth = [(0, a), (1, b), (2, c)]
        predictions = [(3, a), (0, b), (1, c)]
        detail = evaluate_masks(truth, predictions)
        self.assertEqual(detail['aciertos'], 3)
        self.assertEqual(detail['estados_acertados'], 0)
        self.assertEqual(detail['alertas_acertadas'], 1)
        self.assertEqual(detail['alertas_omitidas'], 1)
        self.assertEqual(detail['falsas_alertas'], 1)
        summary = aggregate([detail])
        self.assertEqual(summary['alertas']['recall'], .5)
        self.assertEqual(summary['alertas']['precision'], .5)

    def test_omitted_critical_and_extra_alert_are_included(self):
        mask = np.ones((2, 2), dtype=bool)
        missing = evaluate_masks([(0, mask)], [])
        extra = evaluate_masks([], [(1, mask)])
        metrics = aggregate([missing, extra])
        self.assertEqual(metrics['alertas']['omitidas'], 1)
        self.assertEqual(metrics['alertas']['falsas'], 1)
        self.assertEqual(metrics['por_estado']['vacio']['recall'], 0)
        self.assertIsNone(metrics['por_estado']['no_evaluable']['recall'])


if __name__ == '__main__':
    unittest.main()
