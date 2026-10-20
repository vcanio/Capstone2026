"""Tarea 19: revisión de tres estados sin inventar una partición para entrenar."""
import copy
import csv
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import datos_modelos as datasets
import panel_modelos as panel
import test_niveles_modelos as fixtures


class LiderExpressPanelTests(unittest.TestCase):
    def setUp(self):
        fixtures.LevelDataTests.setUp(self)
        self.base = self.root / datasets.LIDER_EXPRESS
        (self.base / 'imagenes_ordenadas').mkdir(parents=True)
        datasets.write(self.base / 'manifest.json', {
            'cvat': {'task_id': 19, 'project_id': 7}, 'criterio': datasets.V2_CRITERION,
            'aprobado_entrenamiento': False, 'split': 'sin_asignar'})
        rows = []
        self.snapshot['sources'] = [{'job_id': 45, 'task_id': 19, 'project_id': 7}]
        with (self.root / 'Datos/Registros/inventario.csv').open(encoding='utf-8') as handle:
            originals = list(csv.DictReader(handle))
        for i, row in enumerate(originals):
            stem = f'lider_express_{i + 1:03}_0_original'
            source = self.root / 'Datos' / row['archivo']
            target = self.base / 'imagenes_ordenadas' / (stem + '.jpg')
            shutil.copy2(source, target)
            rows.append({'imagen_id': f'lider_express_{i + 1:03}',
                         'archivo': target.relative_to(self.base).as_posix(),
                         'sha256': row['sha256'], 'grupo_escena': '', 'origen': 'real',
                         'imagen_origen_id': f'lider_express_{i + 1:03}'})
            self.snapshot['frames'][i]['name'] = target.name
        with (self.base / 'inventario.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader(); writer.writerows(rows)
        label = self.snapshot['labels'][0]
        label['attributes'][0]['values'] = list(datasets.V2_STATES)
        self.snapshot['annotations']['shapes'] = [
            {**copy.deepcopy(s), 'attributes': [{'spec_id': 77, 'value': state}]}
            for s, state in zip(self.snapshot['annotations']['shapes'], datasets.V2_STATES * 4)]

    def imported(self):
        with patch.object(datasets, 'fetch_snapshot', return_value=self.snapshot):
            return datasets.import_jobs({'jobs': [45], 'validation': ['28']})

    def test_three_states_are_preserved_but_no_photo_is_assigned_to_training(self):
        value = self.imported()
        report = value['report']
        self.assertEqual(report['criterion']['version'], datasets.V2_CRITERION)
        self.assertEqual(report['clases'], ['Nivel_' + s for s in datasets.V2_STATES])
        self.assertEqual(set(report['estados']), set(datasets.V2_STATES))
        self.assertTrue(report['partition_pending'])
        self.assertTrue(all(i['split'] == 'pending' for i in report['imagenes']))
        self.assertEqual(report['estados_por_split']['train'], {})
        self.assertEqual(report['estados_por_split']['val'], {})
        self.assertEqual(datasets.read(datasets.version_path(value['id']) / 'particion.json')['validation_ids'], [])
        self.assertEqual(value['state'], 'pendiente_revision')
        with self.assertRaises(ValueError):
            datasets.approve({'id': value['id'], 'reviewer': 'Revisor', 'reviewed': True})
        run = self.root / 'ensayo'; run.mkdir()
        with self.assertRaises(ValueError):
            datasets.prepare_version(datasets.version_path(value['id']), run)
        self.assertEqual(list(run.iterdir()), [])

    def test_original_name_alias_resolves_to_registered_photo_and_preview(self):
        inventory = datasets.lider_express_inventory()
        iid = 'lider_express_001_0_original'
        self.assertIn(iid, inventory)
        self.assertEqual(inventory[iid]['familia'], 'lider_express_001')
        value = self.imported()
        preview = datasets.drawing_preview(value['id'], iid, '0', '45')
        with patch.object(panel, 'ROOT', self.root):
            self.assertEqual(panel.allowed_file(preview['image_path']), datasets.safe_image_path(inventory[iid]))
            self.assertIsNone(panel.allowed_file(datasets.LIDER_EXPRESS + '/manifest.json'))

    def test_old_states_and_unregistered_project_tasks_are_rejected(self):
        self.snapshot['labels'][0]['attributes'][0]['values'] = ['vacio', 'suficiente', 'no_evaluable']
        with self.assertRaises(ValueError):
            self.imported()
        for task in ({'id': 20, 'project_id': 7}, {'id': 10, 'project_id': 5}):
            with self.assertRaises(ValueError):
                datasets.project_scope(task)

    def test_unregistered_image_and_escaping_inventory_path_are_rejected(self):
        self.snapshot['frames'][0]['name'] = 'desconocida.jpg'
        with self.assertRaises(ValueError):
            self.imported()
        text = (self.base / 'inventario.csv').read_text()
        (self.base / 'inventario.csv').write_text(text.replace('imagenes_ordenadas/', '../', 1))
        with self.assertRaises(ValueError):
            datasets.lider_express_inventory()


if __name__ == '__main__':
    unittest.main()
