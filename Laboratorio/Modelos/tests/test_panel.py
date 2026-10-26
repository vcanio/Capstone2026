"""Regresiones del panel: partición, parámetros y acceso a archivos privados."""
import copy
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import panel_modelos as panel


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = panel.catalog()
        # El historial real puede estar vacío o archivado. La validación usa
        # un ensayo sintético para no depender de entrenamientos anteriores.
        cls.data['runs'] = [{'id': 'ensayo_fixture', 'ready': True,
                             'manifest': {'imagenes': [{'imagen': '03.jpg', 'split': 'train'},
                                                      {'imagen': '28.jpg', 'split': 'val'}]}}]
        cls.data['models'] = [{'id': 'Laboratorio/Experimentos/ensayo_fixture/entrenamiento/weights/best.pt',
                               'run': 'ensayo_fixture'}]
        cls.config = {'action': 'predict', 'model': cls.data['models'][0]['id'],
                      'image': 'Datos/V1/Lider/lider_028.jpg', 'conf': 0.25, 'nms': 0.7, 'imgsz': 640}

    def test_reserve_is_absent_and_rejected(self):
        reserve = panel.read_json(panel.ROOT / 'Datos/Registros/reserva_evaluacion.json')
        self.assertTrue(all(image['scene'] not in reserve['groups'] for image in self.data['images']))
        for image_id in reserve['image_ids']:
            config = {**self.config, 'image': f'Datos/V1/Lider/{image_id}.jpg'}
            with self.assertRaises(ValueError):
                panel.validate(config, self.data)

    def test_validation_truth_is_attached(self):
        config = panel.validate(self.config, self.data)
        self.assertEqual(config['split'], 'val')
        self.assertTrue(config['truth'].endswith('/val/28.txt'))

    def test_training_photo_is_rejected_even_with_a_historical_path(self):
        for path in ('Datos/V1/Lider/lider_003.jpg', 'Datos/Imagenes/03.jpg'):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'se usó para entrenar'):
                panel.validate({**self.config, 'image': path}, self.data)

    def test_training_history_includes_parent_runs_but_keeps_validation(self):
        parent = {'id': 'parent', 'manifest': {'imagenes': [
            {'imagen': 'REAL_03.jpg', 'archivo': 'Equilibrado_v1_20261013/reales/entrenamiento/REAL_03.jpg', 'split': 'train'},
            {'imagen': '28.jpg', 'split': 'val'}]}}
        child = {'id': 'child', 'config': {'model': 'Laboratorio/Experimentos/parent/entrenamiento/weights/best.pt'},
                 'manifest': {'imagenes': [{'imagen': '04.jpg', 'split': 'train'}]}}
        self.assertEqual(panel.training_image_ids({'run': 'child'}, [parent, child]),
                         ['Datos/V1/Lider/lider_003.jpg', 'Datos/V1/Lider/lider_004.jpg'])
        self.assertEqual(panel.training_image_ids({'run': None}, [parent, child]), [])

    def test_same_filename_in_another_folder_is_not_mistaken_for_training(self):
        data = copy.deepcopy(self.data)
        data['runs'][0]['manifest']['imagenes'] = [
            {'imagen': 'lider_028.jpg', 'archivo': 'V1/otra/lider_028.jpg', 'split': 'train'}]
        clean = panel.validate(self.config, data)
        self.assertNotIn('truth', clean)
        self.assertNotIn('split', clean)

    def test_unsafe_paths_and_invalid_numbers(self):
        for change in ({'model': '../private.pt'}, {'conf': float('nan')}, {'imgsz': 641},
                       {'conf': True}, {'nms': 2}, {'imgsz': 640.5}):
            with self.assertRaises(ValueError):
                panel.validate({**self.config, **change}, self.data)

    def test_new_runs_are_unique_and_keep_source(self):
        config = {'action': 'train', 'model': self.config['model'], 'source': self.data['runs'][0]['id'],
                  'name': 'verificacion', 'epochs': 1, 'batch': 1, 'lr': 0.001, 'seed': 42, 'imgsz': 320}
        first = panel.validate(config, self.data)
        second = panel.validate(config, self.data)
        self.assertNotEqual(first['run'], second['run'])
        self.assertEqual(first['source'], config['source'])
        self.assertNotEqual(first['run'], config['source'])
        with self.assertRaises(ValueError):
            panel.validate({**config, 'name': '../../overwrite'}, self.data)

    def test_signature_changes_with_labels(self):
        manifest = self.data['runs'][0]['manifest']
        signature = panel.dataset_signature(manifest, b'original labels')
        self.assertNotEqual(signature, panel.dataset_signature(manifest, b'edited labels'))
        edited = copy.deepcopy(manifest)
        edited['imagenes'][0]['split'] = 'val'
        self.assertNotEqual(signature, panel.dataset_signature(edited, b'original labels'))


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading
        cls.server = panel.ThreadingHTTPServer(('127.0.0.1', 0), panel.Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_catalog_and_frontend(self):
        with urlopen(self.url + '/api/catalog') as response:
            self.assertEqual(response.status, 200)
        with urlopen(self.url + '/') as response:
            self.assertIn(b'Laboratorio de modelos', response.read())

    def test_health_does_not_depend_on_cvat(self):
        import json
        with urlopen(self.url + '/api/health') as response:
            self.assertEqual(json.load(response), {'status': 'ok'})

    def test_frontend_resources_are_served_and_support_revalidation(self):
        import re
        with urlopen(self.url + '/') as response:
            html = response.read().decode('utf-8')
        resources = re.findall(r'(?:src|href)="(/static/[^\"]+)"', html)
        self.assertTrue(any(path.endswith('.css') for path in resources))
        self.assertTrue(any(path.endswith('.js') for path in resources))
        for path in resources:
            with self.subTest(resource=path), urlopen(self.url + path) as response:
                self.assertEqual(response.status, 200)
                self.assertTrue(response.read().strip())
                expected = 'css' if path.endswith('.css') else 'javascript'
                self.assertIn(expected, response.headers['Content-Type'])
                etag = response.headers['ETag']
            request = Request(self.url + path, headers={'If-None-Match': etag})
            with self.assertRaises(HTTPError) as context:
                urlopen(request)
            self.assertEqual(context.exception.code, 304)

    def test_static_route_rejects_missing_files_and_paths_outside_assets(self):
        for path in ('/static/missing.js', '/static/../panel_modelos.py', '/static/../../README.md'):
            with self.subTest(path=path), self.assertRaises(HTTPError) as context:
                urlopen(self.url + path)
            self.assertEqual(context.exception.code, 404)

    def test_foreign_host_is_denied(self):
        request = Request(self.url + '/api/health', headers={'Host': 'example.com:8090'})
        with self.assertRaises(HTTPError) as context:
            urlopen(request)
        self.assertEqual(context.exception.code, 403)

    def test_private_and_reserved_files_are_denied(self):
        for path in ('Infraestructura/CVAT/acceso_local.json', 'Datos/V1/Lider/lider_014.jpg', '../README.md'):
            with self.assertRaises(HTTPError) as context:
                urlopen(self.url + '/file?path=' + path)
            self.assertEqual(context.exception.code, 404)

    def test_foreign_origin_cannot_start_job(self):
        for route in ('/api/jobs', '/api/datasets/import', '/api/datasets/approve',
                      '/api/datasets/archive', '/api/datasets/restore',
                      '/api/datasets/sync',
                      '/api/models/archive', '/api/models/restore'):
            request = Request(self.url + route, data=b'{}', headers={'Origin': 'https://example.com'})
            with self.assertRaises(HTTPError) as context:
                urlopen(request)
            self.assertEqual(context.exception.code, 403)

    def test_dataset_routes_reject_non_object_requests(self):
        for route in ('/api/datasets/import', '/api/datasets/approve',
                      '/api/datasets/archive', '/api/datasets/restore',
                      '/api/datasets/sync',
                      '/api/models/archive', '/api/models/restore'):
            request = Request(self.url + route, data=b'[]', headers={'Content-Type': 'application/json'})
            with self.assertRaises(HTTPError) as context:
                urlopen(request)
            self.assertEqual(context.exception.code, 400)


if __name__ == '__main__':
    unittest.main()
