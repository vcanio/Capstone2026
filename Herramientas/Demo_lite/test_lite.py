from io import BytesIO
import hashlib
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image
import app
import preparar
from inferencia import BusyError, ModelRunner, analyze_edges, draw_result, read_photo


def photo(format='PNG', size=(120, 80), exif=None):
    output = BytesIO()
    Image.new('RGB', size, 'white').save(output, format=format, **({'exif': exif} if exif else {}))
    return output.getvalue()


class LiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'modelos').mkdir()
        body = b'weights fixture'
        (self.root / 'modelos/fixture.pt').write_bytes(body)
        manifest = {'models': [{'id': 'fixture', 'name': 'Modelo de prueba', 'file': 'modelos/fixture.pt',
                                'sha256': hashlib.sha256(body).hexdigest()}]}
        (self.root / 'modelos.json').write_text(json.dumps(manifest))

    def test_package_is_self_contained_and_tampered_weights_fail(self):
        runner = ModelRunner(self.root)
        self.assertEqual(runner.available(), [{'id': 'fixture', 'name': 'Modelo de prueba'}])
        (self.root / 'modelos/fixture.pt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'modificado'):
            ModelRunner(self.root)

    def test_preparation_accepts_cpu_wheels_and_detects_partial_environments(self):
        versions = dict(preparar.REQUIRED)
        versions['torch'] += '+cpu'
        versions['torchvision'] += '+cpu'
        self.assertTrue(preparar.dependencies_match(versions))
        self.assertFalse(preparar.dependencies_match({**versions, 'torch': None}))
        self.assertFalse(preparar.dependencies_match({**versions, 'numpy': '2.0.0'}))

    def test_ready_marker_requires_matching_package_and_environment(self):
        marker = self.root / 'listo.json'
        state = {'folder': str(self.root), 'fingerprint': 'version-a', 'packages': dict(preparar.REQUIRED)}
        with patch.object(preparar, 'READY', marker):
            self.assertFalse(preparar.is_ready(state))
            marker.write_text(json.dumps(state))
            self.assertTrue(preparar.is_ready(state))
            self.assertFalse(preparar.is_ready({**state, 'fingerprint': 'version-b'}))
            marker.write_text('{incomplete')
            self.assertFalse(preparar.is_ready(state))

    def test_unknown_models_nonfinite_confidence_and_concurrent_work_are_rejected(self):
        runner = ModelRunner(self.root)
        for model, confidence in (('../secret', .25), ('fixture', float('nan')), ('fixture', True), ('fixture', 2)):
            with self.subTest(model=model, confidence=confidence), self.assertRaises(ValueError):
                runner.analyze(photo(), model, confidence)
        runner.lock.acquire()
        with self.assertRaises(BusyError):
            runner.analyze(photo(), 'fixture')
        runner.lock.release()

    def test_bad_photos_and_pixel_limits_are_rejected(self):
        for body in (b'', b'not an image', photo('GIF')):
            with self.assertRaises(ValueError):
                read_photo(body)
        with patch('inferencia.MAX_PIXELS', 100), self.assertRaises(ValueError):
            read_photo(photo())

    def test_invalid_analysis_method_is_rejected_before_model_loading(self):
        with self.assertRaisesRegex(ValueError, 'bordes'):
            ModelRunner(self.root).analyze(photo(), 'fixture', method='invalid')

    def test_portable_edge_sources_are_checked_at_startup(self):
        manifest = json.loads((self.root / 'modelos.json').read_text())
        manifest['edge_sources'] = {}
        for name in ('ocupacion_paulo.py', 'gondola_bordes.py'):
            body = b'fixture source'
            (self.root / name).write_bytes(body)
            manifest['edge_sources'][name] = hashlib.sha256(body).hexdigest()
        (self.root / 'modelos.json').write_text(json.dumps(manifest))
        ModelRunner(self.root)
        (self.root / 'gondola_bordes.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'bordes.*modificado'):
            ModelRunner(self.root)

    def test_edges_use_original_pixels_and_keep_yolo_states(self):
        import numpy as np
        original = np.full((240, 720, 3), 255, dtype=np.uint8)
        mask = np.zeros((2, 240, 720), dtype=np.uint8)
        mask[:, 20:220, 30:690] = 1
        masks = SimpleNamespace(data=SimpleNamespace(cpu=lambda: SimpleNamespace(numpy=lambda: mask)))
        detections = [{'id': 1, 'state': 'reponer'}, {'id': 2, 'state': 'no_evaluable'}]
        output = analyze_edges(original.copy(), SimpleNamespace(masks=masks), detections)
        self.assertEqual([d['state'] for d in detections], ['reponer', 'no_evaluable'])
        self.assertEqual(detections[0]['occupancy']['area_signal_pct'], 0)
        self.assertIsNone(detections[1]['occupancy']['area_signal_pct'])
        self.assertFalse(output['occupancy']['changes_yolo_state'])
        self.assertFalse(np.asarray(output['edges_image']).any())
        self.assertTrue(np.array_equal(np.asarray(output['occupancy_image']), original))
        # Una caja sin máscara debe conservarse como sin medición.
        detections = [{'id': 1, 'state': 'suficiente'}]
        analyze_edges(original, SimpleNamespace(masks=None), detections)
        self.assertEqual(detections[0]['occupancy']['status'], 'sin_medicion')
        self.assertIsNone(detections[0]['occupancy']['area_signal_pct'])
        with patch('inferencia.MAX_BYTES', 1), self.assertRaises(ValueError):
            read_photo(photo())

    def test_exif_is_applied_and_alpha_is_composited(self):
        exif = Image.Exif()
        exif[274] = 6
        image = read_photo(photo('JPEG', exif=exif))
        self.assertEqual(image.size, (80, 120))
        self.assertFalse(image.getexif())
        output = BytesIO()
        Image.new('RGBA', (20, 20), (0, 0, 0, 0)).save(output, 'PNG')
        self.assertEqual(read_photo(output.getvalue()).getpixel((0, 0)), (255, 255, 255))

    def test_rendering_handles_no_detections_and_preserves_class_labels(self):
        image = Image.new('RGB', (400, 300), 'white')
        output, detections = draw_result(image, SimpleNamespace(boxes=None))
        self.assertEqual(detections, [])
        self.assertEqual(output.getpixel((10, 10)), (255, 255, 255))
        def tensor(values):
            return SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: values))
        result = SimpleNamespace(names={0: 'Nivel_vacio'}, masks=None,
                                 boxes=SimpleNamespace(xyxy=tensor([[10, 10, 350, 100]]), conf=tensor([.8]), cls=tensor([0])))
        output, detections = draw_result(image, result)
        self.assertEqual(detections[0]['state'], 'vacio')
        self.assertEqual(detections[0]['id'], 1)
        self.assertNotEqual(output.getpixel((10, 50)), (255, 255, 255))

    def test_v2_base_exposes_only_its_two_states_and_renders_reponer(self):
        manifest = json.loads((self.root / 'modelos.json').read_text())
        manifest['models'][0].update(classes=['Nivel_reponer', 'Nivel_suficiente'], guide='v2 base')
        (self.root / 'modelos.json').write_text(json.dumps(manifest))
        available = ModelRunner(self.root).available()[0]
        self.assertEqual([s['key'] for s in available['states']], ['reponer', 'suficiente'])
        self.assertIn('no reconoce', available['note'])
        def tensor(values):
            return SimpleNamespace(cpu=lambda: SimpleNamespace(tolist=lambda: values))
        result = SimpleNamespace(names={0: 'Nivel_reponer'}, masks=None,
            boxes=SimpleNamespace(xyxy=tensor([[5, 5, 200, 100]]), conf=tensor([.9]), cls=tensor([0])))
        _, detections = draw_result(Image.new('RGB', (300, 200)), result)
        self.assertEqual(detections[0]['state'], 'reponer')


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        self.server.runner = SimpleNamespace(available=lambda: [{'id': 'fixture', 'name': 'Prueba'}],
            analyze=lambda *args: {'image': Image.new('RGB', (20, 20), 'white'), 'detections': [], 'counts': {}, 'model': 'fixture'})
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def test_ui_and_models_are_available_without_cvat(self):
        with urlopen(self.url + '/') as response:
            self.assertIn(b'Walmart Lite', response.read())
        with urlopen(self.url + '/api/models') as response:
            self.assertEqual(json.load(response)['models'][0]['id'], 'fixture')

    def test_prediction_response_contains_an_image_and_uploads_are_not_saved(self):
        request = Request(self.url + '/api/predict?model=fixture&confidence=0.25', data=photo(), headers={'Content-Type': 'image/png'})
        with urlopen(request) as response:
            data = json.load(response)
            self.assertTrue(data['image_url'].startswith('data:image/jpeg;base64,'))

    def test_edge_method_and_three_images_travel_through_http_without_files(self):
        from unittest.mock import Mock
        predict = Mock(return_value={'image': Image.new('RGB', (20, 20)),
            'occupancy_image': Image.new('RGB', (20, 20)), 'edges_image': Image.new('L', (20, 20)),
            'filtered_edges_image': Image.new('L', (20, 20)), 'occupancy': {'calibrated': False},
            'detections': [], 'counts': {}, 'model': 'fixture'})
        self.server.runner.analyze = predict
        request = Request(self.url + '/api/predict?model=fixture&method=yolo_paulo', data=photo(),
                          headers={'Content-Type': 'image/png'})
        with urlopen(request) as response:
            data = json.load(response)
        self.assertEqual(predict.call_args.args[3], 'yolo_paulo')
        for field in ('occupancy_image_url', 'edges_image_url', 'filtered_edges_image_url'):
            self.assertTrue(data[field].startswith('data:image/png;base64,'))

    def test_private_paths_foreign_origin_and_large_uploads_are_rejected(self):
        for path in ('/modelos.json', '/../app.py'):
            with self.assertRaises(HTTPError) as error:
                urlopen(self.url + path)
            self.assertEqual(error.exception.code, 404)
        request = Request(self.url + '/api/predict', data=photo(), headers={'Origin': 'https://example.com'})
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 403)
        with patch.object(app, 'MAX_BYTES', 1), self.assertRaises(HTTPError) as error:
            urlopen(Request(self.url + '/api/predict', data=photo()))
        self.assertEqual(error.exception.code, 413)


if __name__ == '__main__':
    unittest.main()
