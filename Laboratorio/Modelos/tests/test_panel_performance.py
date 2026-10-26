"""HTTP regressions for caching, previews and the reserved-image boundary."""
import gzip
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


class PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / 'Datos/V1/Lider/lider_001.jpg'
        self.image.parent.mkdir(parents=True)
        Image.new('RGB', (1600, 1200), '#0053e2').save(self.image)
        self.original = self.image.read_bytes()
        self.inventory = [{'archivo': 'V1/Lider/lider_001.jpg'}]
        for context in (patch.object(panel, 'ROOT', self.root),
                        patch.object(panel, 'JOBS', self.root / 'Laboratorio/Experimentos/panel_pruebas'),
                        patch.object(panel, 'inventory', side_effect=lambda: self.inventory),
                        patch.object(panel.datasets, 'package_inventory', return_value={})):
            context.start()
            self.addCleanup(context.stop)
        panel.invalidate_catalog()
        self.addCleanup(panel.invalidate_catalog)
        panel.JOB_CACHE.clear()
        self.addCleanup(panel.JOB_CACHE.clear)
        self.server = panel.ThreadingHTTPServer(('127.0.0.1', 0), panel.Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def test_photo_bypasses_catalog_and_preview_preserves_original(self):
        with patch.object(panel, 'catalog', side_effect=AssertionError('Catalog must not run')):
            with urlopen(self.url + '/file?path=Datos/V1/Lider/lider_001.jpg&preview=thumb') as response:
                body = response.read()
                self.assertEqual(response.headers['Content-Type'], 'image/jpeg')
            with Image.open(BytesIO(body)) as image:
                self.assertEqual(image.size, (280, 210))
            self.assertLess(len(body), len(self.original))
            with urlopen(self.url + '/file?path=Datos/V1/Lider/lider_001.jpg') as response:
                self.assertEqual(response.read(), self.original)
        self.assertEqual(self.image.read_bytes(), self.original)

    def test_revalidation_checks_permission_even_for_previously_cached_photo(self):
        url = self.url + '/file?path=Datos/V1/Lider/lider_001.jpg&preview=thumb'
        with urlopen(url) as response:
            etag = response.headers['ETag']
            self.assertEqual(response.headers['Cache-Control'], 'private, no-cache')
        request = Request(url, headers={'If-None-Match': etag})
        with self.assertRaises(HTTPError) as context:
            urlopen(request)
        self.assertEqual(context.exception.code, 304)
        self.inventory = []  # The photo is now reserved or removed from the inventory.
        with self.assertRaises(HTTPError) as context:
            urlopen(request)
        self.assertEqual(context.exception.code, 404)

    def test_thumbnail_updates_when_original_changes(self):
        url = self.url + '/file?path=Datos/V1/Lider/lider_001.jpg&preview=thumb'
        with urlopen(url) as response:
            before, etag = response.read(), response.headers['ETag']
        Image.new('RGB', (800, 400), 'red').save(self.image)
        with urlopen(Request(url, headers={'If-None-Match': etag})) as response:
            self.assertEqual(response.status, 200)
            self.assertNotEqual(response.read(), before)
            self.assertNotEqual(response.headers['ETag'], etag)

    def test_catalog_cache_invalidates_and_compression_round_trips(self):
        data = {'runs': [], 'description': 'fixture' * 1000}
        with patch.object(panel, 'catalog', return_value=data) as build:
            for _ in range(2):
                with urlopen(Request(self.url + '/api/catalog', headers={'Accept-Encoding': 'gzip'})) as response:
                    self.assertEqual(response.headers['Content-Encoding'], 'gzip')
                    self.assertEqual(json.loads(gzip.decompress(response.read())), data)
            self.assertEqual(build.call_count, 1)
            panel.invalidate_catalog()
            with urlopen(self.url + '/api/catalog') as response:
                self.assertEqual(json.load(response), data)
            self.assertEqual(build.call_count, 2)

    def test_catalog_revalidation_survives_expiry_and_detects_changes(self):
        data = {'runs': [], 'description': 'fixture' * 1000}
        with patch.object(panel, 'catalog', return_value=data) as build, \
             patch.object(panel.time, 'monotonic', return_value=100) as clock:
            with urlopen(self.url + '/api/catalog') as response:
                etag = response.headers['ETag']
                self.assertEqual(response.headers['Cache-Control'], 'private, no-cache')
            request = Request(self.url + '/api/catalog', headers={'If-None-Match': etag,
                                                                  'Accept-Encoding': 'gzip'})
            for now in (101, 200):
                clock.return_value = now
                with self.assertRaises(HTTPError) as context:
                    urlopen(request)
                self.assertEqual(context.exception.code, 304)
                self.assertEqual(context.exception.read(), b'')
                self.assertEqual(context.exception.headers['ETag'], etag)
            self.assertEqual(build.call_count, 2)
            build.return_value = {**data, 'runs': [{'id': 'new'}]}
            panel.invalidate_catalog()
            with urlopen(request) as response:
                self.assertNotEqual(response.headers['ETag'], etag)
                self.assertEqual(json.loads(gzip.decompress(response.read())), build.return_value)

    def test_polling_only_rereads_active_jobs_and_invalidates_finished_files(self):
        for n in range(30):
            job = panel.JOBS / str(n)
            job.mkdir(parents=True)
            panel.write_json(job / 'estado.json', {'id': str(n), 'state': 'running' if n == 0 else 'done',
                                                  'config': {'action': 'predict', 'image': '01.jpg'}})
            (job / 'salida.log').write_text('initial', encoding='utf-8')
        with patch.object(panel, 'job_status', wraps=panel.job_status) as read, \
             patch.object(panel.time, 'monotonic', return_value=100) as clock:
            for _ in range(3):
                with urlopen(self.url + '/api/jobs') as response:
                    self.assertEqual(len(json.load(response)), 30)
            self.assertEqual(read.call_count, 32)  # 30 cold reads, then only the active job.
            (panel.JOBS / '1/salida.log').write_text('updated log', encoding='utf-8')
            panel.write_json(panel.JOBS / '2/resultado.json', {'metric': 42})
            panel.write_json(panel.JOBS / '0/estado.json', {'id': '0', 'state': 'done', 'config': {'action': 'predict'}})
            statuses = {item['id']: item for item in panel.recent_jobs()}
            self.assertEqual(statuses['0']['state'], 'done')  # Active completion is immediate.
            self.assertEqual(statuses['1']['log'], 'initial')
            self.assertEqual(read.call_count, 33)
            clock.return_value += panel.FINISHED_JOB_RECHECK_SECONDS
            statuses = {item['id']: item for item in panel.recent_jobs()}
            self.assertEqual(read.call_count, 35)
            self.assertEqual(statuses['1']['log'], 'updated log')
            self.assertEqual(statuses['2']['result']['metric'], 42)
            panel.recent_jobs()
            self.assertEqual(read.call_count, 35)

    def test_finished_training_cache_detects_progress_environment_and_previews(self):
        clock_patch = patch.object(panel.time, 'monotonic', return_value=100)
        clock = clock_patch.start()
        self.addCleanup(clock_patch.stop)
        job = panel.JOBS / 'train'
        job.mkdir(parents=True)
        run = self.root / 'Laboratorio/Experimentos/run'
        training = run / 'entrenamiento'
        training.mkdir(parents=True)
        panel.write_json(job / 'estado.json', {'state': 'done', 'config': {'action': 'train', 'run': 'run'}})
        first = panel.recent_jobs()[0]
        self.assertNotIn('preview_url', first['progress'])
        panel.write_json(job / 'progreso.json', {'stage': 'done', 'completed_epochs': 3})
        panel.write_json(run / 'entorno.json', {'gpu': 'fixture GPU'})
        (training / 'val_batch0_pred.jpg').write_bytes(b'preview')
        clock.return_value += panel.FINISHED_JOB_RECHECK_SECONDS
        updated = panel.recent_jobs()[0]
        self.assertEqual(updated['progress']['device'], 'fixture GPU')
        self.assertEqual(updated['progress']['completed_epochs'], 3)
        self.assertIn('val_batch0_pred.jpg', updated['progress']['preview_url'])
        (training / 'val_batch0_pred.jpg').write_bytes(b'updated preview')
        clock.return_value += panel.FINISHED_JOB_RECHECK_SECONDS
        self.assertNotEqual(panel.recent_jobs()[0]['progress']['preview_url'], updated['progress']['preview_url'])

    def test_only_recorded_comparisons_and_run_previews_are_served(self):
        run = self.root / 'Laboratorio/Experimentos/fixture'
        run.mkdir(parents=True)
        panel.write_json(run / 'manifest.json', {'imagenes': []})
        panel.write_json(run / 'evaluacion_por_imagen.json', [{'imagen': '01.jpg', 'split': 'val'}])
        for name in ('comparaciones/01_val.jpg', 'comparaciones/unlisted.jpg',
                     'entrenamiento/val_batch0_pred.jpg', 'entrenamiento/private.jpg'):
            file = run / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(self.original)
        for name in ('comparaciones/01_val.jpg', 'entrenamiento/val_batch0_pred.jpg'):
            with urlopen(self.url + '/file?path=Laboratorio/Experimentos/fixture/' + name) as response:
                self.assertEqual(response.status, 200)
        for name in ('comparaciones/unlisted.jpg', 'entrenamiento/private.jpg', '../../README.md'):
            with self.assertRaises(HTTPError) as context:
                urlopen(self.url + '/file?path=Laboratorio/Experimentos/fixture/' + name)
            self.assertEqual(context.exception.code, 404)


if __name__ == '__main__':
    unittest.main()
