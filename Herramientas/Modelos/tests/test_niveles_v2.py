"""La etapa base usa su partición real y conserva las clases y reservas."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import datos_modelos as datasets
from comparar_niveles import evaluate_masks, aggregate
from particion_niveles import load_partition, verify_binding
from niveles_modelos import model_states

ROOT = Path(__file__).resolve().parents[3]


class V2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = datasets.read(ROOT / 'Datos/Registros/Particiones/lider_express_v2_20261019/fuentes/tarea_19.json')
        cls.snapshot = {'scope': 'Nivel_estados', 'frames': raw['meta']['frames'], 'labels': raw['labels'],
                        'annotations': raw['annotations'], 'sources': [
                            {'job_id': j['id'], 'task_id': 19, 'project_id': 7, 'state': 'completed',
                             'task_name': raw['task']['name']} for j in raw['jobs']]}
        for shape in cls.snapshot['annotations']['shapes']:
            shape['imported_job_id'] = next(j['id'] for j in raw['jobs']
                if j['start_frame'] <= shape['frame'] <= j['stop_frame'])

    def test_fixed_partition_ignores_custom_validation(self):
        report, _ = datasets.inspect(copy.deepcopy(self.snapshot), ['lider_express_001_0_original'])
        self.assertEqual(report['bloqueos_entrenamiento'], 0)
        self.assertEqual(report['clases'], ['Nivel_reponer', 'Nivel_suficiente'])
        self.assertEqual(report['partition_counts'], {'train': 160, 'val': 10, 'diagnostico': 30, 'reserva': 36})
        self.assertEqual(report['estados_por_split']['val'], {'suficiente': 50, 'reponer': 1})

    def test_missing_family_cannot_silently_change_training(self):
        snapshot = copy.deepcopy(self.snapshot)
        snapshot['frames'].pop()
        with self.assertRaisesRegex(ValueError, '236'):
            datasets.inspect(snapshot, [])

    def test_new_non_evaluable_cannot_be_silently_dropped(self):
        snapshot = copy.deepcopy(self.snapshot)
        snapshot['annotations']['shapes'][0]['attributes'][0]['value'] = 'no_evaluable'
        report, _ = datasets.inspect(snapshot, [])
        self.assertGreater(report['bloqueos_entrenamiento'], 0)

    def test_old_copy_must_be_reimported_and_binding_cannot_change(self):
        binding = load_partition(ROOT)['binding']
        with self.assertRaisesRegex(ValueError, 'Trae nuevamente'):
            verify_binding(ROOT, {}, {'partition_binding': binding})
        with self.assertRaises(ValueError):
            verify_binding(ROOT, {'fixed_partition': {**binding, 'sha256': 'changed'}}, {'partition_binding': binding})

    def test_import_approve_export_excludes_all_diagnostics_and_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            versions = Path(tmp) / 'versions'; versions.mkdir()
            run = Path(tmp) / 'run'; run.mkdir()
            with patch.object(datasets, 'VERSIONS', versions), \
                 patch.object(datasets, 'fetch_snapshot', return_value=copy.deepcopy(self.snapshot)), \
                 patch('conjuntos.consolidate_export'):
                value = datasets.import_jobs({'jobs': [45, 46, 47], 'validation': ['inventada']})
                again = datasets.import_jobs({'jobs': [45, 46, 47]})
                self.assertEqual(again['id'], value['id'])
                datasets.approve({'id': value['id'], 'reviewer': 'Prueba automatizada', 'reviewed': True})
                datasets.prepare_version(versions / value['id'], run)
                manifest = datasets.read(run / 'manifest.json')
                self.assertEqual(manifest['clases'], ['Nivel_reponer', 'Nivel_suficiente'])
                exported = {item['imagen_id'] for item in manifest['imagenes']}
                expected = {name for name, row in load_partition(ROOT)['records'].items()
                            if row['effective_split'] in ('train', 'val')}
                self.assertEqual(exported, expected)
                self.assertEqual(len(exported), 170)
                image_dir = run / 'dataset_niveles/images'
                self.assertEqual(len(list((image_dir / 'train').iterdir())), 160)
                self.assertEqual(len(list((image_dir / 'val').iterdir())), 10)
                self.assertEqual({p.name for p in image_dir.iterdir()}, {'train', 'val'})
                for file in (run / 'dataset_niveles/labels').rglob('*.txt'):
                    self.assertTrue(all(line.split()[0] in ('0', '1') for line in file.read_text().splitlines()))

    def test_binary_sufficient_is_not_a_restock_alert(self):
        mask = np.ones((2, 2), dtype=bool)
        states = ('reponer', 'suficiente')
        sufficient = evaluate_masks([(1, mask)], [(1, mask)], states=states)
        self.assertEqual(sufficient['alertas_predichas'], 0)
        false_alert = evaluate_masks([(1, mask)], [(0, mask)], states=states)
        self.assertEqual(false_alert['falsas_alertas'], 1)
        missed = evaluate_masks([(0, mask)], [(1, mask)], states=states)
        self.assertEqual(missed['alertas_omitidas'], 1)
        summary = aggregate([sufficient, false_alert, missed], states=states)
        self.assertEqual(set(summary['por_estado']), set(states))
        self.assertEqual(model_states({0: 'Nivel_reponer', 1: 'Nivel_suficiente'}), states)


if __name__ == '__main__':
    unittest.main()
