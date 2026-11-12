"""V3: no perder niveles al excluir fotos, ni mezclar reservas al exportar."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import preparacion_v3 as v3
import panel_modelos as panel


def fixture():
    rows = []
    for idx, (split, origin) in enumerate((('train', 'real'), ('val', 'real'),
                                          ('val', 'sintetica'), ('test', 'real'),
                                          ('test', 'sintetica'), ('train', 'sintetica'))):
        rows.append({'name': f'foto_{idx}.png', 'path': f'Datos/foto_{idx}.png',
                     'width': 100, 'height': 100, 'task_id': 24, 'split': split,
                     'origen': origin, 'familia': f'familia_{idx}', 'grupo_escena': f'escena_{idx}',
                     'sha256': hashlib.sha256(str(idx).encode()).hexdigest()})
    shapes = [{'id': 10 + idx, 'frame': idx, 'type': 'polygon', 'label_id': 22,
               'points': [1, 1, 99, 1, 99, 99, 1, 99], 'occluded': idx == 0,
               'attributes': [{'spec_id': 83, 'value': 'completa'}]} for idx in range(len(rows))]
    part = {'id': 'fixture', 'resumen': {}, 'imagenes': rows}
    snapshot = {'labels': [{'id': 22, 'name': 'Nivel', 'attributes': [{'id': 83, 'name': 'delimitacion'}]}],
                'tasks': [{'task': {'id': 24}, 'frames_by_name': {r['name']: i for i, r in enumerate(rows)},
                           'annotations': {'shapes': shapes, 'tracks': [], 'tags': []},
                           'jobs': [{'id': 1, 'start_frame': 0, 'stop_frame': 5}]}]}
    return part, snapshot


class PreparationV3Tests(unittest.TestCase):
    def test_rutas_historicas_v3_se_resuelven_en_su_ubicacion_actual(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for folder in ('lider_express_20261016', 'visibilidad_limitada_20261019'):
                old = f'Datos/V2/{folder}/imagenes/foto.png'
                expected = (root / f'Datos/V3/{folder}/imagenes/foto.png').resolve()
                self.assertEqual(v3.v3_image_path(root, old), expected)
            with self.assertRaisesRegex(ValueError, 'inválida'):
                v3.v3_image_path(root, '../fuera.png')

    def test_final_catalog_contains_only_test_and_keeps_origins_separate(self):
        part, _ = fixture()
        original = copy.deepcopy(part)
        result = v3.final_test_catalog(part)
        self.assertEqual([p['name'] for p in result['images']], ['foto_3.png', 'foto_4.png'])
        self.assertEqual(result['counts'], {'real': 1, 'sintetica': 1})
        self.assertFalse(result['analysis_enabled'])
        self.assertEqual(part, original)
        actual = v3.final_test_catalog(v3.partition(Path(__file__).resolve().parents[3], v3.PARTITION))
        self.assertEqual(len(actual['images']), 63)
        self.assertEqual(actual['counts'], {'real': 27, 'sintetica': 36})

    def test_active_partition_moves_old_test_by_scene_and_keeps_existing_development(self):
        root = Path(__file__).resolve().parents[3]
        reference = 'Datos/Registros/Particiones/v3_469_desarrollo_20261102/particion.json'
        if not (root / reference).is_file():
            self.skipTest('Requiere la partición histórica local de desarrollo.')
        part = v3.partition(root, reference)
        base = v3.partition(root, part['base_partition_path'])
        changes = [(a, b) for a, b in zip(base['imagenes'], part['imagenes']) if a['split'] != b['split']]
        self.assertEqual(len(changes), 63)
        self.assertTrue(all(a['split'] == 'test' and b['split'] in ('train', 'val') for a, b in changes))
        self.assertEqual(sum(b['split'] == 'train' for _, b in changes), 52)
        self.assertEqual(sum(b['split'] == 'val' for _, b in changes), 11)
        self.assertEqual(v3.final_test_catalog(part)['images'], [])

    def test_final_preview_rejects_development_unknown_paths_and_changed_bytes(self):
        part, _ = fixture()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'Datos').mkdir()
            for index, row in enumerate(part['imagenes']):
                (root / row['path']).write_bytes(str(index).encode())
            with patch.object(v3, 'partition', return_value=part):
                self.assertEqual(v3.final_image_path(root, 'foto_3.png'), root / 'Datos/foto_3.png')
                for name in ('foto_0.png', 'foto_1.png', '../../private', 'unknown.png'):
                    with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'prueba final'):
                        v3.final_image_path(root, name)
                (root / 'Datos/foto_3.png').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'ausente o cambió'):
                    v3.final_image_path(root, 'foto_3.png')

    def test_fixed_partition_matches_registered_scenes_without_training_approval(self):
        root = Path(__file__).resolve().parents[3]
        part = v3.partition(root, v3.PARTITION)
        self.assertEqual(len(part['imagenes']), 458)
        self.assertFalse(part['training_enabled'])
        damaged = copy.deepcopy(part)
        damaged['imagenes'][0]['split'] = 'val'
        with patch.object(v3, 'read', return_value=damaged):
            with self.assertRaises(ValueError):
                v3.partition(root)

    def test_v3_record_error_does_not_break_historical_catalog(self):
        root = Path(__file__).resolve().parents[3]
        with patch.object(v3, 'status', side_effect=ValueError('fixture')):
            result = v3.catalog_status(root)
        self.assertFalse(result['preparation_enabled'])
        self.assertIn('fixture', result['error'])

    def test_pending_level_blocks_whole_image_and_preserves_other_shapes(self):
        part, snap = fixture()
        pending = copy.deepcopy(snap['tasks'][0]['annotations']['shapes'][0])
        pending['id'] = 99
        pending['attributes'][0]['value'] = 'pendiente'
        snap['tasks'][0]['annotations']['shapes'].append(pending)
        original = copy.deepcopy(snap)
        result = v3.analyze(part, snap)
        self.assertFalse(result['images'][0]['eligible'])
        self.assertEqual(len(result['images'][0]['shapes']), 2)
        self.assertEqual(result['blocked_images'], 1)
        self.assertEqual(snap, original)
        self.assertFalse(result['training_enabled'])

    def test_partial_is_a_warning_but_review_tag_blocks_whole_photo(self):
        part, snap = fixture()
        snap['tasks'][0]['annotations']['shapes'][1]['attributes'][0]['value'] = 'parcial'
        snap['tasks'][0]['annotations']['tags'] = [{'frame': 2, 'label_id': 50}]
        result = v3.analyze(part, snap)
        self.assertTrue(result['images'][1]['eligible'])
        self.assertEqual(result['images'][1]['issues'], [])
        self.assertEqual(result['images'][1]['warnings'][0]['code'], 'delimitacion_parcial')
        self.assertEqual(result['images'][1]['shapes'][0]['delimitacion'], 'parcial')
        self.assertEqual(result['partial_polygons'], 1)
        self.assertFalse(result['images'][2]['eligible'])
        self.assertEqual(result['issues']['revision_foto'], 1)

    def test_partial_warning_never_overrides_invalid_geometry_pending_or_disabled_photo(self):
        for block in ('geometry', 'pending', 'disabled'):
            part, snap = fixture()
            shapes = snap['tasks'][0]['annotations']['shapes']
            shapes[0]['attributes'][0]['value'] = 'parcial'
            if block == 'geometry':
                shapes[0]['points'] = [1, 1, 101, 1, 99, 99]
            elif block == 'pending':
                pending = copy.deepcopy(shapes[0])
                pending.update(id=99, attributes=[{'spec_id': 83, 'value': 'pendiente'}])
                shapes.append(pending)
            else:
                snap['tasks'][0]['meta'] = {'deleted_frames': [0]}
            original = copy.deepcopy(snap)
            image = v3.analyze(part, snap)['images'][0]
            self.assertFalse(image['eligible'], block)
            self.assertTrue(image['issues'])
            self.assertTrue(any(w['code'] == 'delimitacion_parcial' for w in image['warnings']))
            self.assertEqual(snap, original)

    def test_disabled_cvat_photo_keeps_partition_but_cannot_be_exported(self):
        part, snap = fixture()
        snap['tasks'][0]['meta'] = {'deleted_frames': [1]}
        result = v3.analyze(part, snap)
        image = result['images'][1]
        self.assertFalse(image['eligible'])
        self.assertEqual(image['split'], 'val')
        self.assertEqual(image['issues'][0]['code'], 'excluida_cvat')
        self.assertEqual(result['image_count'], 6)

    def test_occlusion_keeps_complete_geometry_and_missing_photo_is_not_negative(self):
        part, snap = fixture()
        snap['tasks'][0]['annotations']['shapes'].pop()
        result = v3.analyze(part, snap)
        self.assertTrue(result['images'][0]['eligible'])
        self.assertEqual(result['images'][0]['warnings'][0]['code'], 'oclusion')
        self.assertEqual(result['occluded_polygons'], 1)
        self.assertFalse(result['images'][-1]['eligible'])
        self.assertEqual(result['issues']['sin_niveles'], 1)

    def test_invalid_points_unknown_classes_and_tracks_are_blocked(self):
        for change in ({'points': [1, 1, 99, 99, 1, 99, 99, 1]},
                       {'points': [1, 1, 101, 1, 99, 99]},
                       {'points': [float('nan'), 1, 99, 1, 99, 99]},
                       {'label_id': 999}, {'type': 'rectangle'}):
            part, snap = fixture()
            snap['tasks'][0]['annotations']['shapes'][0].update(change)
            self.assertFalse(v3.analyze(part, snap)['images'][0]['eligible'])
        snap['tasks'][0]['annotations']['tracks'] = [{'id': 12}]
        self.assertEqual(v3.analyze(part, snap)['blocked_images'], 6)

    def save_copy(self, root, partial_frames=()):
        part, snap = fixture()
        for frame in partial_frames:
            snap['tasks'][0]['annotations']['shapes'][frame]['attributes'][0]['value'] = 'parcial'
        snap['tasks'][0]['annotations']['shapes'][-1]['attributes'][0]['value'] = 'pendiente'
        p = root / v3.PARTITION
        p.parent.mkdir(parents=True)
        v3.write(p, part)
        for idx, row in enumerate(part['imagenes']):
            (root / row['path']).write_bytes(str(idx).encode())
        report = v3.analyze(part, snap)
        report.update(id='v3_20261023_000000_12345678', partition_id='fixture',
                      partition_sha256=v3.digest(p))
        folder = root / v3.OUTPUT / report['id']
        folder.mkdir(parents=True)
        v3.write(folder / 'informe.json', report)
        return report

    def test_export_separates_real_synthetic_and_test_and_records_exclusions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = self.save_copy(root)
            result = v3.export(root, {'id': report['id'], 'reviewed': True, 'author': 'Revisor'})
            out = root / result['path']
            self.assertFalse(result['training_enabled'])
            self.assertEqual(result['excluded'], 1)
            self.assertEqual(result['counts'], {'train': 1, 'val_real': 1, 'val_sintetica': 1,
                                                'test_real': 1, 'test_sintetica': 1})
            yaml = (out / 'desarrollo.yaml').read_text()
            self.assertIn('val: val_real.txt', yaml)
            self.assertNotIn('test', yaml)
            self.assertIn('0: Nivel', yaml)
            labels = list((out / 'labels').rglob('*.txt'))
            self.assertEqual(len(labels), 5)
            self.assertTrue(all(p.read_text().startswith('0 ') for p in labels))
            self.assertTrue(all(0 <= float(v) <= 1 for p in labels for v in p.read_text().split()[1:]))
            manifest = v3.read(out / 'manifest.json')
            self.assertEqual(manifest['excluded'][0]['name'], 'foto_5.png')
            self.assertEqual(len(manifest['included']), 5)

    def test_export_includes_reviewed_partial_regions_and_preserves_attributes_outside_yolo_class(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = self.save_copy(root, partial_frames=(0, 1, 3))
            result = v3.export(root, {'id': report['id'], 'reviewed': True, 'author': 'Revisor'})
            out = root / result['path']
            manifest = v3.read(out / 'manifest.json')
            self.assertEqual(manifest['policy_version'], v3.PREPARATION_POLICY)
            self.assertTrue(manifest['reviewed_visible_regions'])
            self.assertEqual(result['excluded'], 1)
            for frame in (0, 1, 3):
                entry = next(i for i in manifest['included'] if i['name'] == f'foto_{frame}.png')
                self.assertEqual(entry['shapes'][0]['delimitacion'], 'parcial')
                self.assertEqual(entry['shapes'][0]['occluded'], frame == 0)
                self.assertTrue(any(w['code'] == 'delimitacion_parcial' for w in entry['warnings']))
            for label in (out / 'labels').rglob('*.txt'):
                fields = label.read_text().split()
                self.assertEqual(fields[0], '0')
                self.assertEqual(len(fields), 9)
            self.assertNotIn('test', (out / 'desarrollo.yaml').read_text())

    def test_previous_policy_requires_new_copy_instead_of_changing_old_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = self.save_copy(root)
            report.pop('policy_version')
            path = root / v3.OUTPUT / report['id'] / 'informe.json'
            v3.write(path, report)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'política anterior'):
                v3.export(root, {'id': report['id'], 'reviewed': True, 'author': 'Revisor'})
            self.assertEqual(path.read_bytes(), before)

    def test_export_requires_human_review_and_detects_changed_partition_and_images(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = self.save_copy(root)
            config = {'id': report['id'], 'reviewed': True, 'author': 'Revisor'}
            with self.assertRaisesRegex(ValueError, 'revisión visual'):
                v3.export(root, {**config, 'reviewed': False})
            image = root / 'Datos/foto_0.png'
            image.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Cambió la imagen'):
                v3.export(root, config)
            image.write_bytes(b'0')
            (root / v3.PARTITION).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'partición cambió'):
                v3.export(root, config)

    def test_export_cannot_fall_back_to_synthetic_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = self.save_copy(root)
            report['images'][1]['eligible'] = False
            v3.write(root / v3.OUTPUT / report['id'] / 'informe.json', report)
            with self.assertRaisesRegex(ValueError, 'validación real'):
                v3.export(root, {'id': report['id'], 'reviewed': True, 'author': 'Revisor'})

    def test_prepare_reads_three_tasks_and_saves_immutable_snapshot(self):
        part, snap = fixture()
        part['imagenes'] = [part['imagenes'][0]]
        annotations = copy.deepcopy(snap['tasks'][0]['annotations'])
        annotations['shapes'] = annotations['shapes'][:1]
        class Reader:
            def listing(self, route):
                if route.startswith('/labels'):
                    return snap['labels']
                task_id = int(route.split('task_id=')[1].split('&')[0])
                return [{'id': task_id, 'task_id': task_id, 'type': 'annotation', 'start_frame': 0, 'stop_frame': 0}]
            def request(self, route):
                task_id = int(route.split('/')[2])
                rows = [r for r in part['imagenes'] if r['task_id'] == task_id]
                if route.endswith('/annotations'):
                    return annotations
                if route.endswith('/data/meta'):
                    return {'frames': [{'name': r['name'], 'width': 100, 'height': 100} for r in rows]}
                return {'id': task_id, 'project_id': 8, 'size': len(rows)}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root / v3.PARTITION
            p.parent.mkdir(parents=True)
            v3.write(p, part)
            for idx, task_id in enumerate((27, 28), 1):
                part['imagenes'].append({**part['imagenes'][0], 'name': f'task{task_id}.png',
                                         'path': f'Datos/task{task_id}.png', 'task_id': task_id})
            for row in part['imagenes']:
                (root / row['path']).write_bytes(b'0')
            with patch.object(v3, 'partition', return_value=part):
                result = v3.prepare(root, Reader())
                first = root / v3.OUTPUT / result['id'] / 'snapshot_cvat.json'
                raw = first.read_bytes()
                second = v3.prepare(root, Reader())
            self.assertNotEqual(result['id'], second['id'])
            self.assertEqual(first.read_bytes(), raw)
            self.assertEqual(result['image_count'], 3)
            self.assertEqual(len(v3.read(first)['tasks']), 3)

    def test_unsafe_version_is_rejected(self):
        with self.assertRaises(ValueError):
            v3.version_path(Path('.'), '../../private')

    def test_prepare_maps_renamed_cvat_frames_without_changing_partition_identity(self):
        part, snap = fixture()
        part['imagenes'] = [part['imagenes'][0]]
        shape = copy.deepcopy(snap['tasks'][0]['annotations']['shapes'][0])
        class Reader:
            def listing(self, route):
                if route.startswith('/labels'):
                    self_test.assertIn('project_id=11', route)
                    return snap['labels']
                self_test.assertIn('task_id=33', route)
                return [{'id': 74, 'task_id': 33, 'type': 'annotation', 'start_frame': 0, 'stop_frame': 0}]
            def request(self, route):
                self_test.assertTrue(route.startswith('/tasks/33'))
                if route.endswith('/annotations'):
                    return {'shapes': [shape], 'tracks': [], 'tags': []}
                if route.endswith('/data/meta'):
                    return {'frames': [{'name': 'origen__foto_0.png', 'width': 100, 'height': 100}]}
                return {'id': 33, 'project_id': 11, 'size': 1}
        self_test = self
        source = {'project_id': 11, 'tasks': {24: 33},
                  'entries': {(24, 'foto_0.png'): {'nombre_propuesto': 'origen__foto_0.png'}}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root / v3.PARTITION
            p.parent.mkdir(parents=True)
            v3.write(p, part)
            (root / 'Datos/foto_0.png').write_bytes(b'0')
            with patch.object(v3, 'partition', return_value=part), patch.object(v3, 'cvat_source', return_value=source):
                result = v3.prepare(root, Reader())
            image = result['images'][0]
            self.assertEqual((image['task_id'], image['name']), (24, 'foto_0.png'))
            self.assertEqual((image['cvat_task_id'], image['cvat_name'], image['job_id']),
                             (33, 'origen__foto_0.png', 74))
            self.assertEqual(image['shapes'][0]['points'], shape['points'])

    def test_cvat_source_requires_verified_receipt_and_unchanged_mapping(self):
        part, _ = fixture()
        part['imagenes'] = [part['imagenes'][0]]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reference = v3.PARTITION
            partition_path = root / reference
            partition_path.parent.mkdir(parents=True)
            v3.write(partition_path, part)
            directory = root / 'Datos/Registros/Organizacion_nombres_20261030'
            directory.mkdir(parents=True)
            plan_path = directory / 'plan_nombres_v3.csv'
            row = {'tarea_actual': 24, 'nombre_actual': 'foto_0.png',
                   'nombre_propuesto': 'origen__foto_0.png', 'sha256': part['imagenes'][0]['sha256']}
            with plan_path.open('w', encoding='utf-8-sig', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=row.keys())
                writer.writeheader(); writer.writerow(row)
            receipt = {'status': 'verified', 'project_id': 11,
                       'tasks': [{'status': 'verified', 'source_task': 24, 'task_id': 33}]}
            v3.write(directory / 'migracion_cvat.json', receipt)
            config_path = root / v3.CVAT_ACTIVE_SOURCE
            config_path.parent.mkdir(parents=True)
            config = {'partition_path': reference, 'partition_sha256': v3.digest(partition_path),
                      'plan_sha256': v3.digest(plan_path), 'project_id': 11, 'tasks': {'24': 33}}
            v3.write(config_path, config)
            self.assertEqual(v3.cvat_source(root, reference, part)['tasks'], {24: 33})
            receipt['status'] = 'in_progress'
            v3.write(directory / 'migracion_cvat.json', receipt)
            with self.assertRaisesRegex(ValueError, 'no está verificada'):
                v3.cvat_source(root, reference, part)
            receipt['status'] = 'verified'
            v3.write(directory / 'migracion_cvat.json', receipt)
            plan_path.write_text('alterado', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'mapa de nombres'):
                v3.cvat_source(root, reference, part)


class PreparationV3HttpTests(unittest.TestCase):
    def test_http_preparation_uses_server_root_and_rejects_external_origins(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), panel.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            with patch.object(panel.v3, 'prepare', return_value={'image_count': 458}) as prepare:
                req = Request(url + '/api/v3/prepare', data=b'{"tasks":[25]}', headers={'Content-Type': 'application/json'})
                with urlopen(req) as response:
                    self.assertEqual(response.status, 201)
                    self.assertEqual(json.load(response)['image_count'], 458)
                prepare.assert_called_once_with(panel.ROOT)
                req = Request(url + '/api/v3/prepare', data=b'{}', headers={'Origin': 'https://untrusted.example'})
                with self.assertRaises(HTTPError) as error:
                    urlopen(req)
                self.assertEqual(error.exception.code, 403)
                self.assertEqual(prepare.call_count, 1)
            with patch.object(panel.v3, 'report', return_value={'images': []}):
                with self.assertRaises(HTTPError) as error:
                    urlopen(url + '/api/v3/image?id=fixture&photo=../../private')
                self.assertEqual(error.exception.code, 404)
            with tempfile.TemporaryDirectory() as temp:
                image = Path(temp) / 'photo.jpg'
                image.write_bytes(b'private-photo-fixture')
                with patch.object(panel.v3, 'final_image_path', return_value=image) as resolve:
                    with urlopen(url + '/api/v3/final-image?photo=safe.jpg') as response:
                        self.assertEqual(response.read(), b'private-photo-fixture')
                    resolve.assert_called_once_with(panel.ROOT, 'safe.jpg')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
