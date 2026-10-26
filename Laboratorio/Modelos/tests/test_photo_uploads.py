"""Own-photo inference: upload boundaries, orientation and dataset isolation."""
import csv
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image
import panel_modelos as panel


class PhotoUploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'Datos/Registros').mkdir(parents=True)
        reserve = self.root / 'Datos/Registros/reserva_evaluacion.json'
        reserve.parent.mkdir(parents=True, exist_ok=True)
        reserve.write_text(json.dumps({'image_ids': ['holdout'], 'groups': ['reserved']}))
        self.inventory_path = self.root / 'Datos/Registros/inventario.csv'
        self.inventory_path.write_text('imagen_id,archivo,sha256,grupo_escena\n')
        self.inventory_before = self.inventory_path.read_bytes()
        for context in (patch.object(panel, 'ROOT', self.root),
                        patch.object(panel, 'JOBS', self.root / 'Laboratorio/Experimentos/panel_pruebas')):
            context.start()
            self.addCleanup(context.stop)
        self.server = panel.ThreadingHTTPServer(('127.0.0.1', 0), panel.Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def photo(self, format='PNG', size=(80, 40), exif=None):
        buffer = BytesIO()
        Image.new('RGB', size, '#0053e2').save(buffer, format=format, **({'exif': exif} if exif else {}))
        return buffer.getvalue()

    def upload(self, body=None, **headers):
        request = Request(self.url + '/api/photos', data=body if body is not None else self.photo(),
                          headers={'Content-Type': 'image/png', 'X-Filename': 'mi%20foto.png', **headers})
        return urlopen(request)

    def test_uploaded_photo_is_served_and_kept_outside_inventory_and_training(self):
        with self.upload() as response:
            self.assertEqual(response.status, 201)
            photo = json.load(response)
        self.assertEqual(photo['name'], 'mi foto.png')
        self.assertEqual((photo['width'], photo['height']), (80, 40))
        self.assertTrue(photo['id'].startswith('Laboratorio/Experimentos/panel_pruebas/Subidas_panel/'))
        self.assertEqual(self.inventory_path.read_bytes(), self.inventory_before)
        self.assertFalse((self.root / 'Datos/Registros/Versiones_modelos').exists())
        with urlopen(self.url + photo['url']) as response:
            with Image.open(BytesIO(response.read())) as image:
                self.assertEqual(image.size, (80, 40))
        folder = (self.root / photo['id']).parent
        self.assertIsNone(panel.allowed_file(str((folder / 'foto.json').relative_to(self.root)).replace('\\', '/')))

    def test_own_photo_never_borrows_truth_from_matching_filename(self):
        photo = panel.save_uploaded_photo(self.photo(), 'REAL_01.jpg')
        model = 'Laboratorio/Experimentos/run/entrenamiento/weights/best.pt'
        catalog = {'models': [{'id': model, 'run': 'run'}], 'images': [], 'runs': [
            {'id': 'run', 'manifest': {'scope': 'Nivel_estados', 'dataset_dir': 'dataset_niveles',
                                      'imagenes': [{'imagen': 'imagen.jpg', 'split': 'val'}]}}]}
        config = panel.validate({'action': 'predict', 'image': photo['id'], 'model': model,
                                 'conf': .25, 'nms': .7, 'imgsz': 640, 'truth': 'spoof.txt'}, catalog)
        self.assertEqual(config['image_source'], 'upload')
        self.assertEqual(config['scope'], 'Nivel_estados')
        self.assertNotIn('truth', config)
        self.assertNotIn('split', config)

    def test_exif_rotation_is_applied_and_metadata_is_removed(self):
        exif = Image.Exif()
        exif[274] = 6
        photo = panel.save_uploaded_photo(self.photo('JPEG', exif=exif), 'turned.jpg')
        with Image.open(self.root / photo['id']) as image:
            self.assertEqual(image.size, (40, 80))
            self.assertNotIn(274, image.getexif())

    def test_corrupt_and_unsupported_files_are_rejected_without_creating_upload(self):
        for body in (b'not an image', self.photo('GIF')):
            with self.subTest(body=body[:6]), self.assertRaises(HTTPError) as error:
                self.upload(body)
            self.assertEqual(error.exception.code, 400)
        self.assertFalse((self.root / 'Laboratorio/Experimentos/panel_pruebas/Subidas_panel').exists())

    def test_byte_and_pixel_limits_are_enforced_before_storage(self):
        with patch.object(panel, 'MAX_UPLOAD_BYTES', 10), self.assertRaises(HTTPError) as error:
            self.upload()
        self.assertEqual(error.exception.code, 413)
        with patch.object(panel, 'MAX_UPLOAD_PIXELS', 100), self.assertRaises(HTTPError) as error:
            self.upload()
        self.assertEqual(error.exception.code, 400)
        self.assertFalse((self.root / 'Laboratorio/Experimentos/panel_pruebas/Subidas_panel').exists())

    def test_reserved_photo_can_be_tested_without_entering_training_or_validation(self):
        body = self.photo()
        with self.inventory_path.open('a', newline='') as handle:
            csv.writer(handle).writerow(['holdout', 'Imagenes/holdout.jpg', hashlib.sha256(body).hexdigest(), 'reserved'])
        inventory_before = self.inventory_path.read_bytes()
        reserve_path = self.root / 'Datos/Registros/reserva_evaluacion.json'
        reserve_before = reserve_path.read_bytes()
        with self.upload(body) as response:
            self.assertEqual(response.status, 201)
            photo = json.load(response)
        with urlopen(self.url + photo['url']) as response:
            self.assertEqual(response.status, 200)
        model = 'Laboratorio/Experimentos/run/entrenamiento/weights/best.pt'
        catalog = {'models': [{'id': model, 'run': 'run'}], 'images': [], 'runs': []}
        config = panel.validate({'action': 'predict', 'image': photo['id'], 'model': model,
                                 'conf': .25, 'nms': .7, 'imgsz': 640}, catalog)
        self.assertEqual(config['image_source'], 'upload')
        self.assertNotIn('truth', config)
        self.assertNotIn('split', config)
        self.assertEqual(panel.inventory(), [])
        self.assertEqual(self.inventory_path.read_bytes(), inventory_before)
        self.assertEqual(reserve_path.read_bytes(), reserve_before)
        self.assertFalse((self.root / 'Datos/Registros/Versiones_modelos').exists())

    def test_untrusted_origin_and_wrong_content_type_are_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.upload(Origin='https://other.example')
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            self.upload(**{'Content-Type': 'text/html'})
        self.assertEqual(error.exception.code, 415)

    def test_missing_metadata_and_path_traversal_do_not_authorize_files(self):
        photo = panel.save_uploaded_photo(self.photo(), '../../REAL_01.jpg')
        self.assertEqual(photo['name'], 'REAL_01.jpg')
        self.assertIsNone(panel.uploaded_photo(photo['id'].replace('/imagen.jpg', '/../imagen.jpg')))
        (self.root / photo['id']).with_name('foto.json').unlink()
        self.assertIsNone(panel.uploaded_photo(photo['id']))


if __name__ == '__main__':
    unittest.main()
