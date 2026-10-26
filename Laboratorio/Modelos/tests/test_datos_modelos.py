"""Pruebas del importador con CVAT simulado y originales pequeños verificables."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import datos_modelos as datasets
import panel_modelos as panel
import piloto_modulos as pilot


def fixture():
    labels = [{'id': 10, 'name': 'Modulo', 'attributes': [
        {'id': 1, 'name': 'modulo_id', 'default_value': ''},
        {'id': 2, 'name': 'integridad', 'default_value': 'pendiente'},
        {'id': 3, 'name': 'observacion', 'default_value': ''}]}]
    return {'frames': [{'name': f'{i:02}.jpg', 'width': 20, 'height': 20} for i in (1, 2, 3)],
            'labels': labels, 'sources': [{'job_id': 27}], 'annotations': {'shapes': [
                {'id': i + 50, 'frame': i, 'type': 'polygon', 'label_id': 10,
                 'points': [1, 1, 18, 1, 18, 18, 1, 18], 'attributes': [
                     {'spec_id': 1, 'value': 'M01'}, {'spec_id': 2, 'value': 'completo'}]}
                for i in range(3)], 'tracks': [], 'tags': []}}


class DataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.versions = self.root / 'Datos/Registros/Versiones_modelos'
        (self.root / 'Datos/V1/Lider').mkdir(parents=True)
        (self.root / 'Datos/Registros').mkdir(parents=True)
        (self.root / 'Infraestructura/CVAT').mkdir(parents=True)
        datasets.write(self.root / 'Datos/Registros/reserva_evaluacion.json', {'image_ids': [], 'groups': []})
        rows = []
        for i, group in ((1, 'a'), (2, 'a'), (3, 'b')):
            file = self.root / f'Datos/V1/Lider/lider_{i:03}.jpg'
            Image.new('RGB', (20, 20), (i * 40, 100, 100)).save(file)
            rows.append({'imagen_id': f'{i:02}', 'archivo': f'V1/Lider/lider_{i:03}.jpg',
                         'grupo_escena': group, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
        with (self.root / 'Datos/Registros/inventario.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader(); writer.writerows(rows)
        for target, value in (('ROOT', self.root), ('VERSIONS', self.versions)):
            mock = patch.object(datasets, target, value)
            mock.start(); self.addCleanup(mock.stop)
        self.snapshot = fixture()

    def imported(self):
        with patch.object(datasets, 'fetch_snapshot', return_value=self.snapshot):
            return datasets.import_jobs({'jobs': [27], 'validation': ['03']})

    def test_discovery_offers_complete_lots_and_never_individual_jobs(self):
        class Client:
            def listing(self, route):
                if route == '/projects':
                    return [{'id': 4, 'name': 'Módulos Walmart'}]
                if route.startswith('/tasks'):
                    return [{'id': i, 'project_id': 4, 'name': name} for i, name in
                            ((13, 'Piloto'), (14, 'Set completo'), (15, 'Nueva tanda'))]
                return [{'id': job_id, 'task_id': task, 'type': 'annotation',
                         'start_frame': index, 'stop_frame': index,
                         'assignee': {'username': 'persona nueva'}} for job_id, task, index in
                        ((27, 13, 0), (28, 13, 1), (29, 13, 2),
                         (30, 14, 0), (31, 14, 1), (32, 14, 2), (33, 15, 0))]
            def request(self, route):
                job_id = int(route.split('/')[2])
                photo = {30: '01', 31: '02', 32: '03', 33: '03'}.get(job_id, '01')
                return {'frames': [{'name': f'{job_id}/{photo}.jpg'}]}
        sources = datasets.import_sources(Client())
        self.assertNotIn('task:13', [s['id'] for s in sources])
        full = next(s for s in sources if s['id'] == 'task:14')
        self.assertEqual(full['jobs'], [30, 31, 32])
        self.assertEqual(full['image_ids'], ['01', '02', '03'])
        self.assertEqual(next(s for s in sources if s['id'] == 'task:15')['jobs'], [33])
        self.assertTrue(all(s['id'].startswith('task:') for s in sources))
        datasets.write(self.root / 'Datos/Registros/reserva_evaluacion.json',
                       {'image_ids': [], 'groups': ['b']})
        filtered = datasets.import_sources(Client())
        self.assertNotIn('task:14', [s['id'] for s in filtered])
        self.assertNotIn('job:32', [s['id'] for s in filtered])
        self.assertNotIn('task:15', [s['id'] for s in filtered])

    def test_groups_are_kept_together(self):
        report, _ = datasets.inspect(self.snapshot, ['01'])
        self.assertEqual([r['split'] for r in report['imagenes']], ['val', 'val', 'train'])
        self.assertEqual(report['bloqueos_modulos'], 0)

    def add_level(self, parent='M1', level_id='N1', shape_id=150):
        if not any(label['id'] == 11 for label in self.snapshot['labels']):
            self.snapshot['labels'].append({'id': 11, 'name': 'Nivel', 'attributes': [
                {'id': 4, 'name': 'modulo_id'}, {'id': 5, 'name': 'nivel_id'},
                {'id': 6, 'name': 'limite_superior'}, {'id': 7, 'name': 'integridad'}]})
        level = copy.deepcopy(self.snapshot['annotations']['shapes'][0])
        level.update(id=shape_id, label_id=11, attributes=[{'spec_id': 4, 'value': parent},
                     {'spec_id': 5, 'value': level_id}, {'spec_id': 6, 'value': 'cerrado'},
                     {'spec_id': 7, 'value': 'completo'}])
        self.snapshot['annotations']['shapes'].append(level)

    def test_short_ids_and_legacy_parent_ids_are_compatible_without_mutation(self):
        for module_id, parent_id, level_id in [('M1', 'M01', 'N1'), ('M01', 'M1', 'N01'),
                                               ('M10', 'M010', 'N10'), ('M100', 'M100', 'N100')]:
            with self.subTest(module=module_id, parent=parent_id, level=level_id):
                self.snapshot = fixture()
                self.snapshot['annotations']['shapes'][0]['attributes'][0]['value'] = module_id
                self.add_level(parent_id, level_id)
                before = copy.deepcopy(self.snapshot)
                report, _ = datasets.inspect(self.snapshot, ['03'])
                self.assertEqual(report['incidencias'], [])
                self.assertEqual(self.snapshot, before)

    def test_short_and_padded_module_ids_are_duplicates(self):
        duplicate = copy.deepcopy(self.snapshot['annotations']['shapes'][0])
        duplicate.update(id=160, points=[2, 2, 17, 2, 17, 17, 2, 17])
        duplicate['attributes'][0]['value'] = 'M1'
        self.snapshot['annotations']['shapes'].append(duplicate)
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertTrue(any(i['problema'] == 'modulo_id repetido' for i in report['incidencias']))

    def test_short_and_padded_level_ids_are_duplicates_within_parent(self):
        self.add_level('M1', 'N1', 150)
        self.add_level('M01', 'N01', 151)
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertTrue(any(i['problema'] == 'nivel_id inválido o repetido dentro del módulo'
                            for i in report['incidencias']))
        self.assertFalse(any(i['problema'] == 'Nivel sin módulo padre existente' for i in report['incidencias']))

    def test_ids_require_positive_ascii_numbers_and_correct_prefix(self):
        for value in ('M0', 'M00', 'M-1', 'M1.5', 'm1', 'M１', 'M', 'N1', '', None):
            with self.subTest(module=value):
                self.snapshot = fixture()
                self.snapshot['annotations']['shapes'][0]['attributes'][0]['value'] = value
                report, _ = datasets.inspect(self.snapshot, ['03'])
                self.assertTrue(any(i['problema'] == 'modulo_id debe tener formato M1'
                                    for i in report['incidencias']))
        self.snapshot = fixture()
        self.add_level('M01', 'N0')
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertTrue(any(i['problema'] == 'nivel_id inválido o repetido dentro del módulo'
                            for i in report['incidencias']))

    def test_reusing_copy_refreshes_report_without_losing_review(self):
        version = self.imported()
        approved = datasets.approve({'id': version['id'], 'reviewer': 'Vi', 'reviewed': True})
        metadata = datasets.version_path(version['id']) / 'version.json'
        stale = copy.deepcopy(approved)
        stale['report']['incidencias'] = [{'problema': 'modulo_id debe tener formato M01'}]
        datasets.write(metadata, stale)
        reused = self.imported()
        self.assertTrue(reused['import_reused'])
        self.assertEqual(reused['report'], approved['report'])
        self.assertEqual(reused['created_at'], approved['created_at'])
        self.assertEqual(reused['review'], approved['review'])
        self.assertEqual(reused['state'], 'lista_modulos')
        persisted = datasets.read(metadata)
        self.assertEqual({k: v for k, v in persisted.items() if k != 'cvat_status'},
                         {k: v for k, v in approved.items() if k != 'cvat_status'})
        self.assertEqual(persisted['cvat_status'], reused['cvat_status'])

    def test_independent_pilot_versions_must_not_be_combined(self):
        self.snapshot['frames'].append(copy.deepcopy(self.snapshot['frames'][0]))
        with self.assertRaisesRegex(ValueError, 'repetidas'):
            datasets.inspect(self.snapshot, ['03'])

    def test_reserved_scene_is_rejected_even_when_image_not_listed(self):
        datasets.write(self.root / 'Datos/Registros/reserva_evaluacion.json', {'image_ids': [], 'groups': ['a']})
        with self.assertRaisesRegex(ValueError, 'reservada'):
            datasets.inspect(self.snapshot, ['03'])

    def test_exif_orientation_matches_cvat_and_training_copy_preserves_original(self):
        # self.root es el TemporaryDirectory creado por setUp, nunca el proyecto.
        original = self.root / 'Datos/V1/Lider/lider_003.jpg'
        image = Image.new('RGB', (30, 20), (150, 100, 100))
        exif = image.getexif()
        exif[274] = 6
        image.save(original, exif=exif)
        before = original.read_bytes()
        inventory_file = self.root / 'Datos/Registros/inventario.csv'
        with inventory_file.open(encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
        rows[2]['sha256'] = hashlib.sha256(before).hexdigest()
        with inventory_file.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader(); writer.writerows(rows)
        self.snapshot['frames'][2].update(width=20, height=30)
        imported = self.imported()
        datasets.approve({'id': imported['id'], 'reviewer': 'Vi', 'reviewed': True})
        run = self.root / 'Laboratorio/Experimentos/oriented'
        run.mkdir(parents=True)
        datasets.prepare_version(datasets.version_path(imported['id']), run)
        with Image.open(run / 'dataset_modulos/images/val/03.jpg') as result:
            self.assertEqual(result.size, (20, 30))
            self.assertEqual(result.getexif().get(274, 1), 1)
        self.assertEqual(original.read_bytes(), before)
        self.snapshot['frames'][2].update(width=30, height=20)
        with self.assertRaisesRegex(ValueError, 'Dimensiones diferentes'):
            datasets.inspect(self.snapshot, ['03'])

    def test_modified_original_is_rejected(self):
        (self.root / 'Datos/V1/Lider/lider_001.jpg').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'modificado'):
            datasets.inspect(self.snapshot, ['03'])

    def test_identical_images_with_different_ids_are_rejected(self):
        file = self.root / 'Datos/V1/Lider/lider_003.jpg'
        file.write_bytes((self.root / 'Datos/V1/Lider/lider_001.jpg').read_bytes())
        inventory = self.root / 'Datos/Registros/inventario.csv'
        text = inventory.read_text('utf-8')
        rows = list(csv.DictReader(text.splitlines()))
        rows[2]['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
        with inventory.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader(); writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, 'idéntico'):
            datasets.inspect(self.snapshot, ['03'])

    def test_geometry_and_empty_photo_still_block_with_optional_attributes(self):
        self.snapshot['annotations']['shapes'][0]['points'] = [1, 1, 18, 18, 1, 18, 18, 1]
        self.snapshot['annotations']['shapes'][1]['attributes'] = []
        self.snapshot['annotations']['shapes'].pop()
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['bloqueos_modulos'], 2)
        self.assertEqual(report['avisos_atributos'], 2)

    def test_missing_attributes_can_train_after_human_review_without_changing_annotations(self):
        baseline, expected_rows = datasets.inspect(self.snapshot, ['03'])
        for shape in self.snapshot['annotations']['shapes']:
            shape['attributes'] = []
        second = copy.deepcopy(self.snapshot['annotations']['shapes'][0])
        second.update(id=170, points=[2,2,17,2,17,17,2,17])
        self.snapshot['annotations']['shapes'].append(second)
        self.add_level(parent='', level_id='')
        before = copy.deepcopy(self.snapshot)
        report, rows = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['bloqueos_modulos'], 0)
        self.assertGreater(report['avisos_atributos'], 0)
        self.assertEqual(report['avisos_niveles'], 0)
        self.assertFalse(any(i['problema']=='modulo_id repetido' for i in report['incidencias']))
        self.assertEqual(rows['01'][0], expected_rows['01'][0])
        self.assertEqual(len(rows['01']), 2)
        imported = self.imported()
        path = datasets.version_path(imported['id'])
        with self.assertRaisesRegex(ValueError, 'revisión humana'):
            datasets.prepare_version(path, path)
        datasets.approve({'id':imported['id'],'reviewer':'Vi','reviewed':True})
        datasets.prepare_version(path, path)
        self.assertEqual((path/'dataset_modulos/labels/train/01.txt').read_text('utf-8').splitlines(), rows['01'])
        self.assertEqual(self.snapshot, before)
        self.assertEqual(datasets.read(path/'snapshot_cvat.json'), before)

    def test_duplicate_ids_are_optional_but_duplicate_geometry_still_blocks(self):
        duplicate = copy.deepcopy(self.snapshot['annotations']['shapes'][0])
        duplicate.update(id=170, points=[2,2,17,2,17,17,2,17])
        self.snapshot['annotations']['shapes'].append(duplicate)
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['bloqueos_modulos'], 0)
        self.assertTrue(any(i['problema']=='modulo_id repetido' and i['categoria']=='atributos'
                            for i in report['incidencias']))
        duplicate['points']=self.snapshot['annotations']['shapes'][0]['points'][:]
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['bloqueos_modulos'], 1)
        self.assertTrue(any(i['problema']=='Polígono de módulo duplicado' and i['bloquea_modulos']
                            for i in report['incidencias']))

    def test_same_polygon_with_rotated_vertices_is_duplicate(self):
        duplicate = copy.deepcopy(self.snapshot['annotations']['shapes'][0])
        duplicate['points'] = [18, 1, 18, 18, 1, 18, 1, 1]
        duplicate['attributes'][0]['value'] = 'M02'
        self.snapshot['annotations']['shapes'].append(duplicate)
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertTrue(any(i['problema'] == 'Polígono de módulo duplicado' for i in report['incidencias']))

    def test_levels_remain_separate_from_module_approval(self):
        self.snapshot['labels'].append({'id': 11, 'name': 'Nivel', 'attributes': [
            {'id': 4, 'name': 'modulo_id'}, {'id': 5, 'name': 'nivel_id'}, {'id': 6, 'name': 'limite_superior'}]})
        level = copy.deepcopy(self.snapshot['annotations']['shapes'][0])
        level.update(label_id=11, attributes=[{'spec_id': 4, 'value': 'M99'}, {'spec_id': 5, 'value': 'N01'}])
        self.snapshot['annotations']['shapes'].append(level)
        report, rows = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['bloqueos_modulos'], 0)
        self.assertGreater(report['avisos_niveles'], 0)
        self.assertEqual(len(rows['01']), 1)

    def test_draft_cannot_train_and_approval_is_explicit(self):
        v = self.imported(); path = datasets.version_path(v['id'])
        with self.assertRaisesRegex(ValueError, 'revisión humana'):
            datasets.prepare_version(path, path)
        for config in ({'reviewer': 'Vi'}, {'reviewer': '', 'reviewed': True}):
            with self.assertRaises(ValueError):
                datasets.approve({'id': v['id'], **config})
        approved = datasets.approve({'id': v['id'], 'reviewer': 'Vi', 'reviewed': True})
        self.assertEqual(approved['state'], 'lista_modulos')
        datasets.prepare_version(path, path)
        self.assertTrue((path / 'dataset_modulos/labels/val/03.txt').exists())
        self.assertEqual(datasets.read(path / 'manifest.json')['version_datos'], v['id'])

    def test_open_level_without_team_note_keeps_geometry_checks(self):
        self.add_level('M01', 'N1')
        level = self.snapshot['annotations']['shapes'][-1]
        next(a for a in level['attributes'] if a['spec_id'] == 6)['value'] = 'abierto'
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertEqual(report['incidencias'], [])
        level['points'] = [1, 1, 18, 18, 1, 18, 18, 1]
        report, _ = datasets.inspect(self.snapshot, ['03'])
        self.assertTrue(any(i['problema'].startswith('Polígono inválido:') and not i['bloquea_modulos']
                            for i in report['incidencias']))

    def test_partial_without_team_note_can_be_reviewed_and_trained(self):
        for shape in self.snapshot['annotations']['shapes']:
            shape['attributes'][1]['value'] = 'parcial'
        self.add_level('M01', 'N1')
        self.snapshot['annotations']['shapes'][-1]['attributes'][-1]['value'] = 'parcial'
        before = copy.deepcopy(self.snapshot)
        version = self.imported()
        self.assertEqual(version['report']['incidencias'], [])
        self.assertEqual(self.snapshot, before)
        approved = datasets.approve({'id': version['id'], 'reviewer': 'Vi', 'reviewed': True})
        path = datasets.version_path(version['id'])
        datasets.prepare_version(path, path)
        self.assertEqual(approved['state'], 'lista_modulos')
        self.assertEqual(len((path / 'dataset_modulos/labels/val/03.txt').read_text().splitlines()), 1)

    def test_modified_partition_is_rejected(self):
        v = self.imported(); path = datasets.version_path(v['id'])
        datasets.write(path / 'particion.json', {'validation_ids': ['01']})
        with self.assertRaisesRegex(ValueError, 'partición'):
            datasets.approve({'id': v['id'], 'reviewer': 'Vi', 'reviewed': True})

    def test_modified_snapshot_cannot_be_reviewed(self):
        v = self.imported(); path = datasets.version_path(v['id'])
        snapshot_file = path / 'snapshot_cvat.json'
        snapshot_file.write_text(snapshot_file.read_text('utf-8') + ' ', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'modificada'):
            datasets.approve({'id': v['id'], 'reviewer': 'Vi', 'reviewed': True})

    def test_worker_uses_version_partition_for_more_than_pilot(self):
        v = self.imported(); path = datasets.version_path(v['id'])
        approved = datasets.approve({'id': v['id'], 'reviewer': 'Vi', 'reviewed': True})
        run = self.root / 'Laboratorio/Experimentos/new_run'; run.mkdir(parents=True)
        datasets.write(run / 'version_datos.json', approved)
        for name in ('snapshot_cvat.json', 'particion.json'):
            (run / name).write_bytes((path / name).read_bytes())
        with patch.object(pilot, 'RUN', run):
            pilot.prepare()
        self.assertEqual(len(datasets.read(run / 'manifest.json')['imagenes']), 3)
        self.assertTrue((run / 'dataset_modulos/data.yaml').exists())

    def test_panel_selects_approved_version_and_rejects_draft(self):
        v = self.imported()
        config = {'action': 'train', 'model': 'local.pt', 'source': v['id'], 'imgsz': 640,
                  'name': 'new', 'epochs': 1, 'batch': 1, 'lr': 0.001, 'seed': 42}
        data = {'models': [{'id': 'local.pt'}], 'runs': [], 'datasets': [v]}
        with self.assertRaises(ValueError):
            panel.validate(config, data)
        v['state'] = 'lista_modulos'
        self.assertEqual(panel.validate(config, data)['source_kind'], 'dataset')

    def test_archive_and_restore_keep_snapshot_review_and_partition(self):
        value = self.imported()
        path = datasets.version_path(value['id'])
        before = {p.name: p.read_bytes() for p in path.iterdir() if p.is_file()}
        datasets.archive({'id': value['id']})
        self.assertEqual(datasets.versions(), [])
        self.assertEqual(datasets.versions(archived=True)[0]['id'], value['id'])
        with self.assertRaisesRegex(ValueError, 'archivada'):
            datasets.version_path(value['id'])
        with self.assertRaisesRegex(ValueError, 'archivada'):
            datasets.approve({'id': value['id'], 'reviewer': 'Vi', 'reviewed': True})
        restored = datasets.restore({'id': value['id']})
        self.assertEqual(restored, value)
        self.assertEqual(datasets.versions(archived=True), [])
        self.assertEqual(datasets.versions()[0]['id'], value['id'])
        self.assertEqual({p.name: p.read_bytes() for p in path.iterdir() if p.is_file()}, before)

    def test_used_version_is_kept_even_before_training_has_a_manifest(self):
        value = self.imported()
        run = self.root / 'Laboratorio/Experimentos/ensayo_en_preparacion'
        run.mkdir(parents=True)
        datasets.write(run / 'config_interfaz.json', {'source': value['id'], 'source_kind': 'dataset'})
        self.assertEqual(datasets.versions()[0]['archive_uses'], ['ensayo_en_preparacion'])
        with self.assertRaisesRegex(ValueError, 'ensayo_en_preparacion'):
            datasets.archive({'id': value['id']})
        self.assertFalse((datasets.version_path(value['id']) / 'archivo.json').exists())

    def test_archive_restore_reject_unknown_ids_and_paths(self):
        for action in (datasets.archive, datasets.restore):
            for version_id in ('../version.json', None, 'datos_20261007_010000_12345678'):
                with self.subTest(action=action.__name__, id=version_id), self.assertRaises(ValueError):
                    action({'id': version_id})

    def test_unchanged_import_reuses_copy_despite_dates_and_attribute_order(self):
        first = self.imported()
        self.snapshot['exported_at'] = '2030-01-01'
        self.snapshot['sources'][0]['updated_date'] = '2030-01-01'
        self.snapshot['annotations']['shapes'].reverse()
        for shape in self.snapshot['annotations']['shapes']:
            shape['attributes'].reverse()
            shape['cvat_frame'] = shape['frame']
        again = self.imported()
        self.assertEqual(again['id'], first['id'])
        self.assertTrue(again['import_reused'])
        self.assertEqual(len(datasets.versions()), 1)

    def test_annotation_or_partition_change_creates_new_copy(self):
        first = self.imported()
        self.snapshot['annotations']['shapes'][0]['attributes'][0]['value'] = 'M02'
        changed = self.imported()
        self.assertNotEqual(first['id'], changed['id'])
        with patch.object(datasets, 'fetch_snapshot', return_value=self.snapshot):
            partitioned = datasets.import_jobs({'jobs': [27], 'validation': ['01']})
        self.assertNotEqual(changed['id'], partitioned['id'])

    def test_archived_or_modified_copies_are_not_reused(self):
        first = self.imported()
        datasets.archive({'id': first['id']})
        second = self.imported()
        self.assertNotEqual(second['id'], first['id'])
        snapshot_file = datasets.version_path(second['id']) / 'snapshot_cvat.json'
        snapshot_file.write_text(snapshot_file.read_text('utf-8') + ' ', encoding='utf-8')
        third = self.imported()
        self.assertNotEqual(third['id'], second['id'])

    def test_drawing_preview_selects_the_exact_copy_photo_and_object(self):
        value = self.imported()
        preview = datasets.drawing_preview(value['id'], '01', '50', '27')
        self.assertEqual(preview['points'], self.snapshot['annotations']['shapes'][0]['points'])
        self.assertEqual(preview['image_path'], 'Datos/V1/Lider/lider_001.jpg')
        self.assertEqual(preview['attributes']['modulo_id'], 'M01')
        for photo, shape, job in [('02', '50', '27'), ('01', '50', '28'), ('../01', '50', '27')]:
            with self.subTest(photo=photo, shape=shape, job=job), self.assertRaises(ValueError):
                datasets.drawing_preview(value['id'], photo, shape, job)
        datasets.write(self.root / 'Datos/Registros/reserva_evaluacion.json',
                       {'image_ids': ['01'], 'groups': []})
        with self.assertRaisesRegex(ValueError, 'desarrollo'):
            datasets.drawing_preview(value['id'], '01', '50', '27')

    def test_preview_cannot_mix_a_changed_original_with_saved_annotations(self):
        value = self.imported()
        (self.root / 'Datos/V1/Lider/lider_001.jpg').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'original cambió'):
            datasets.drawing_preview(value['id'], '01', '50', '27')


class ImportTests(unittest.TestCase):
    class Client:
        def request(self, route):
            if route == '/jobs/28':
                return {'task_id': 13, 'type': 'annotation', 'start_frame': 5, 'stop_frame': 5}
            if route == '/tasks/13':
                return {'project_id': 4, 'name': 'Piloto'}
            if route.endswith('/data/meta'):
                return {'frames': [{'name': '02_Vilches/03.jpg', 'width': 20, 'height': 20}]}
            if route.endswith('/annotations'):
                shape = fixture()['annotations']['shapes'][0]; shape['frame'] = 5
                return {'shapes': [shape], 'tracks': [], 'tags': []}
            raise AssertionError(route)

        def listing(self, route):
            return fixture()['labels']

    def test_job_global_frame_indexes_are_normalized(self):
        s = datasets.fetch_snapshot([28], self.Client())
        self.assertEqual(s['annotations']['shapes'][0]['frame'], 0)
        self.assertEqual(s['annotations']['shapes'][0]['imported_job_id'], 28)
        self.assertEqual(s['frames'][0]['name'], '02_Vilches/03.jpg')

    def test_three_lots_form_one_snapshot_with_provenance(self):
        class Client(self.Client):
            def request(self, route):
                if route.startswith('/jobs/') and route.count('/') == 2:
                    job_id = int(route.rsplit('/', 1)[1])
                    return {'id': job_id, 'task_id': 14, 'type': 'annotation',
                            'start_frame': job_id - 30, 'stop_frame': job_id - 30}
                if route == '/tasks/14':
                    return {'project_id': 4, 'name': 'Geometría — Set completo'}
                if route.endswith('/data/meta'):
                    index = int(route.split('/')[2]) - 30
                    return {'frames': [fixture()['frames'][index]]}
                if route.endswith('/annotations'):
                    index = int(route.split('/')[2]) - 30
                    return {'shapes': [fixture()['annotations']['shapes'][index]], 'tags': [], 'tracks': []}
                return super().request(route)
        snapshot = datasets.fetch_snapshot([30, 31, 32], Client())
        self.assertEqual([frame['name'] for frame in snapshot['frames']], ['01.jpg', '02.jpg', '03.jpg'])
        self.assertEqual([s['frame'] for s in snapshot['annotations']['shapes']], [0, 1, 2])
        self.assertEqual([s['imported_job_id'] for s in snapshot['annotations']['shapes']], [30, 31, 32])
        self.assertEqual([s['task_id'] for s in snapshot['sources']], [14, 14, 14])

    def test_duplicate_or_invalid_jobs_are_rejected_before_connection(self):
        for ids in ([27, 27], [], [True], ['27'], [-1]):
            with self.assertRaises(ValueError):
                datasets.fetch_snapshot(ids, self.Client())

    def track_client(self, frame=5, keys=None, tags=None):
        class Client(self.Client):
            def request(self, route):
                value = super().request(route)
                if route.endswith('/annotations'):
                    key = {'id': 900, 'frame': frame, 'type': 'polygon', 'outside': False,
                           'points': [1, 1, 18, 1, 18, 18], 'attributes': [
                               {'spec_id': 2, 'value': 'parcial'}]}
                    value['tracks'] = [{'id': 50, 'label_id': 10, 'frame': frame,
                                        'source': 'manual', 'group': 3, 'elements': [],
                                        'attributes': [{'spec_id': 1, 'value': 'M02'},
                                                       {'spec_id': 2, 'value': 'completo'}],
                                        'shapes': copy.deepcopy(keys) if keys is not None else [key]}]
                    value['tags'] = tags or []
                return value
        return Client()

    def test_last_photo_track_preserves_geometry_attributes_and_original(self):
        client = self.track_client()
        original = client.request('/jobs/28/annotations')
        snapshot = datasets.fetch_snapshot([28], client)
        converted = snapshot['annotations']['shapes'][1]
        self.assertEqual(len(snapshot['annotations']['shapes']), 2)
        self.assertEqual(converted['points'], original['tracks'][0]['shapes'][0]['points'])
        self.assertEqual(converted['frame'], 0)
        self.assertEqual(converted['id'], 'track 50')
        self.assertEqual(converted['imported_track_id'], 50)
        self.assertEqual(converted['imported_job_id'], 28)
        self.assertEqual(converted['group'], 3)
        self.assertEqual({a['spec_id']: a['value'] for a in converted['attributes']},
                         {1: 'M02', 2: 'parcial'})
        self.assertEqual(snapshot['sources'][0]['original_tracks'], original['tracks'])
        self.assertFalse(snapshot['sources'][0]['normalization']['cvat_modified'])
        self.assertEqual(snapshot['annotations']['tracks'], [])

    def test_earlier_track_cannot_be_silently_dropped_or_extended(self):
        with self.assertRaisesRegex(ValueError, 'varias fotos'):
            datasets.fetch_snapshot([28], self.track_client(frame=4))

    def test_multi_keyframe_outside_and_non_polygon_tracks_are_rejected(self):
        key = {'id': 900, 'frame': 5, 'type': 'polygon', 'outside': False,
               'points': [1, 1, 18, 1, 18, 18], 'attributes': []}
        for keys in ([key, {**key, 'frame': 6}], [{**key, 'outside': True}],
                     [{**key, 'type': 'rectangle'}]):
            with self.subTest(keys=keys), self.assertRaisesRegex(ValueError, 'varias fotos'):
                datasets.fetch_snapshot([28], self.track_client(keys=keys))

    def test_tags_still_require_a_contour(self):
        with self.assertRaisesRegex(ValueError, 'tags sin contorno'):
            datasets.fetch_snapshot([28], self.track_client(tags=[{'id': 1, 'frame': 5}]))


if __name__ == '__main__':
    unittest.main()
