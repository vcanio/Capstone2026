from conjuntos import dataset_directory
"""La tarea 16 se observa con su partición fija y no se aprueba por sincronizar."""
import copy
import hashlib
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import datos_modelos as datasets
import panel_modelos as panel
import test_niveles_modelos as fixtures


class PackageTests(unittest.TestCase):
    def setUp(self):
        fixtures.LevelDataTests.setUp(self)
        directory = self.root / 'Datos/V1/Equilibrado_v1_20261013'
        directory.mkdir()
        entries = []
        for index, iid in enumerate(('REAL_01', 'EQ_01_V1', 'REAL_03')):
            source = self.root / f'Datos/V1/Lider/lider_{index+1:03}.jpg'
            destination = directory / (iid + '.jpg')
            shutil.copy2(source, destination)
            entries.append({'id': iid, 'archivo': destination.name, 'imagen_fuente': '01.jpg' if index < 2 else '03.jpg',
                            'escena': 'a' if index < 2 else 'b', 'split': 'train' if index < 2 else 'val',
                            'origen': 'sintetica' if index == 1 else 'real', 'ancho': 20, 'alto': 20,
                            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})
            self.snapshot['frames'][index]['name'] = destination.name
        self.snapshot['sources'] = [{'job_id': 36, 'task_id': 16, 'project_id': 6}]
        datasets.write(directory / 'manifest.json', {'imagenes': entries})
        self.manifest = directory / 'manifest.json'

    def imported(self):
        with patch.object(datasets, 'fetch_snapshot', return_value=self.snapshot):
            return datasets.import_jobs({'jobs': [36], 'validation': ['invalid-user-selection']})

    def test_fixed_split_supports_review_and_full_image_export(self):
        value = self.imported()
        self.assertEqual([i['split'] for i in value['report']['imagenes']], ['train', 'train', 'val'])
        self.assertEqual(datasets.read(datasets.version_path(value['id']) / 'particion.json')['validation_ids'], ['REAL_03'])
        self.assertEqual(value['report']['package'], 'Equilibrado_v1_20261013')
        self.assertEqual(value['report']['bloqueos_entrenamiento'], 0)
        self.assertEqual(value['report']['criterion']['export_mode'], 'full_image')
        self.assertNotIn('analysis_region_export_pending', value['report']['criterion'])
        approved = datasets.approve({'id': value['id'], 'reviewer': 'Revisor', 'reviewed': True})
        self.assertEqual(approved['state'], 'lista_niveles')
        run = self.root / 'package_run'; run.mkdir()
        datasets.prepare_version(datasets.version_path(value['id']), run)
        from PIL import Image
        with Image.open(dataset_directory(datasets.ROOT, run) / 'images/train/REAL_01.jpg') as image:
            self.assertEqual(image.size, (20, 20))
        rows = (dataset_directory(datasets.ROOT, run) / 'labels/train/REAL_01.txt').read_text().splitlines()
        self.assertEqual([row.split()[0] for row in rows], ['0', '1', '2', '3'])
        self.assertTrue(all(0 <= float(x) <= 1 for row in rows for x in row.split()[1:]))
        self.assertTrue((dataset_directory(datasets.ROOT, run) / 'labels/val/REAL_03.txt').exists())

    def test_jobs_with_only_training_or_only_validation_can_be_observed(self):
        for indices in ([0, 1], [2]):
            snapshot = copy.deepcopy(self.snapshot)
            snapshot['frames'] = [self.snapshot['frames'][i] for i in indices]
            snapshot['annotations']['shapes'] = [dict(s, frame=indices.index(s['frame']))
                                                for s in self.snapshot['annotations']['shapes'] if s['frame'] in indices]
            validation = ['REAL_03'] if indices == [2] else []
            report, _ = datasets.inspect(snapshot, validation)
            self.assertEqual(len(report['imagenes']), len(indices))
            self.assertGreater(report['bloqueos_entrenamiento'], 0)
            missing = 'validación' if indices == [0, 1] else 'entrenamiento'
            self.assertTrue(any(f'fotos de {missing}' in issue['problema'] for issue in report['incidencias']))

    def test_shared_manifest_exports_cvat_ids_using_single_real_sources(self):
        value = datasets.read(self.manifest)
        metadata = self.root / 'Datos/Registros/Lotes/Equilibrado_v1_20261013'
        metadata.mkdir(parents=True)
        synthetic = self.root / 'Datos/V1/Sinteticas'
        synthetic.mkdir()
        for entry in value['imagenes']:
            previous = self.manifest.parent / entry['archivo']
            if entry['origen'] == 'real':
                source_id = int(Path(entry['imagen_fuente']).stem)
                source = self.root / f'Datos/V1/Lider/lider_{source_id:03}.jpg'
                previous.unlink()
            else:
                source = synthetic / previous.name
                shutil.move(previous, source)
            entry['archivo'] = source.relative_to(self.root / 'Datos').as_posix()
        value['base_archivos'] = 'Datos'
        datasets.write(metadata / 'manifest.json', value)
        imported = self.imported()
        datasets.approve({'id': imported['id'], 'reviewer': 'Revisor', 'reviewed': True})
        run = self.root / 'shared_run'
        run.mkdir()
        datasets.prepare_version(datasets.version_path(imported['id']), run)
        self.assertTrue((dataset_directory(datasets.ROOT, run) / 'images/train/REAL_01.jpg').is_file())
        self.assertTrue((dataset_directory(datasets.ROOT, run) / 'labels/train/REAL_01.txt').is_file())
        self.assertEqual(datasets.package_inventory()['REAL_01']['archivo'],
                         'V1/Lider/lider_001.jpg')

    def test_package_still_rejects_pending_states_and_invalid_polygons(self):
        for change in ('pending', 'polygon'):
            snapshot = copy.deepcopy(self.snapshot)
            shape = snapshot['annotations']['shapes'][0]
            if change == 'pending':
                shape['attributes'][0]['value'] = 'pendiente'
            else:
                shape['points'] = [1, 1, 18, 18, 18, 1, 1, 18]
            with self.subTest(change=change), patch.object(datasets, 'fetch_snapshot', return_value=snapshot):
                value = datasets.import_jobs({'jobs': [36]})
                self.assertGreater(value['report']['bloqueos_entrenamiento'], 0)
                with self.assertRaisesRegex(ValueError, 'bloqueos'):
                    datasets.approve({'id': value['id'], 'reviewer': 'Revisor', 'reviewed': True})

    def test_preview_and_file_route_admit_only_registered_package_images(self):
        value = self.imported()
        preview = datasets.drawing_preview(value['id'], 'REAL_01', 0, 36)
        self.assertEqual(preview['image_path'], 'Datos/V1/Equilibrado_v1_20261013/REAL_01.jpg')
        with patch.object(panel, 'ROOT', self.root), patch.object(panel, 'inventory', return_value=[]):
            self.assertIsNotNone(panel.allowed_file(preview['image_path']))
            self.assertIsNone(panel.allowed_file('Datos/V1/Equilibrado_v1_20261013/manifest.json'))
            self.assertIsNone(panel.allowed_file('Datos/V1/Equilibrado_v1_20261013/unknown.jpg'))

    def test_reserved_source_and_scene_leakage_and_unsafe_path_are_rejected(self):
        original = datasets.read(self.manifest)
        for change in ('reserve', 'leak', 'path'):
            value = copy.deepcopy(original)
            if change == 'reserve':
                datasets.write(self.root / 'Datos/Registros/reserva_evaluacion.json', {'image_ids': ['01'], 'groups': []})
            elif change == 'leak':
                value['imagenes'][2]['escena'] = 'a'
            else:
                value['imagenes'][0]['archivo'] = '../Imagenes/01.jpg'
            datasets.write(self.manifest, value)
            with self.assertRaises(ValueError):
                datasets.package_inventory()
            datasets.write(self.root / 'Datos/Registros/reserva_evaluacion.json', {'image_ids': [], 'groups': []})


if __name__ == '__main__':
    unittest.main()
