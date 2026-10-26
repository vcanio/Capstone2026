"""Un lote reúne sus trabajos y respeta las exclusiones sin desplazar contornos."""
import copy
import unittest

import datos_modelos as datasets
import test_datos_modelos as fixtures
from test_datos_modelos import fixture


class LotTests(unittest.TestCase):
    def setUp(self):
        fixtures.DataTests.setUp(self)

    class Client:
        completed = True

        def listing(self, route):
            if route == '/projects':
                return [{'id': 4, 'name': 'Módulos Walmart'}]
            if route == '/tasks':
                return [{'id': 14, 'project_id': 4, 'name': 'Lote completo'}]
            if route.startswith('/labels'):
                return fixture()['labels']
            return [self.request(f'/jobs/{i}') for i in (30, 31, 32)]

        def request(self, route):
            if route == '/tasks/14':
                return {'id': 14, 'project_id': 4, 'name': 'Lote completo'}
            job = int(route.split('/')[2])
            indices = {30: (0, 0), 31: (1, 2), 32: (3, 3)}
            if route.endswith('/data/meta'):
                names = {30: ['01.jpg'], 31: ['02.jpg', '03.jpg'], 32: ['02.jpg']}
                return {'frames': [{'name': name, 'width': 20, 'height': 20} for name in names[job]],
                        'deleted_frames': [1] if job == 31 else []}
            if route.endswith('/annotations'):
                shapes = copy.deepcopy(fixture()['annotations']['shapes'])
                if job == 30:
                    shapes = shapes[:1]
                elif job == 31:
                    shapes = shapes[1:]
                else:
                    shapes = [dict(shapes[1], frame=3)]
                return {'shapes': shapes, 'tracks': [], 'tags': []}
            start, stop = indices[job]
            return {'id': job, 'type': 'annotation', 'task_id': 14,
                    'start_frame': start, 'stop_frame': stop,
                    'state': 'completed' if self.completed else 'new'}

    def test_completed_lot_keeps_all_three_jobs_despite_an_excluded_photo(self):
        sources = datasets.import_sources(self.Client())
        self.assertEqual(len(sources), 1)
        lot = sources[0]
        self.assertEqual(lot['id'], 'task:14')
        self.assertEqual(lot['project_id'], 4)
        self.assertEqual(lot['project_name'], 'Módulos Walmart')
        self.assertEqual(lot['jobs'], [30, 31, 32])
        self.assertEqual(lot['completed_jobs'], 3)
        self.assertEqual(lot['image_ids'], ['01', '03', '02'])
        self.assertEqual(lot['excluded_image_ids'], ['02'])

    def test_excluded_frames_keep_original_cvat_indices_and_correct_images(self):
        snapshot = datasets.fetch_snapshot([30, 31, 32], self.Client())
        self.assertEqual([f['name'] for f in snapshot['frames']], ['01.jpg', '03.jpg', '02.jpg'])
        self.assertEqual([s['frame'] for s in snapshot['annotations']['shapes']], [0, 1, 2])
        self.assertEqual([s['cvat_frame'] for s in snapshot['annotations']['shapes']], [0, 2, 3])
        self.assertEqual([s['imported_job_id'] for s in snapshot['annotations']['shapes']], [30, 31, 32])
        self.assertEqual(snapshot['sources'][1]['excluded_frames'], [{'cvat_frame': 1, 'name': '02.jpg'}])

    def test_import_resolves_the_entire_lot_instead_of_trusting_partial_browser_jobs(self):
        value = datasets.import_lot({'task_id': 14, 'jobs': [30], 'validation': ['03']}, client=self.Client())
        self.assertEqual([s['job_id'] for s in value['sources']], [30, 31, 32])
        self.assertEqual(len(value['report']['imagenes']), 3)
        self.assertEqual(value['cvat_status']['completed_jobs'], 3)
        self.assertEqual(value['state'], 'pendiente_revision')
        preview = datasets.drawing_preview(value['id'], '03', '52', '31')
        self.assertEqual(preview['cvat_frame'], 2)

    def test_rechecking_completion_reuses_immutable_annotations(self):
        client = self.Client()
        value = datasets.import_lot({'task_id': 14, 'validation': ['03']}, client=client)
        client.completed = False
        reused = datasets.import_lot({'task_id': 14, 'validation': ['03']}, client=client)
        self.assertEqual(reused['id'], value['id'])
        self.assertTrue(reused['import_reused'])
        self.assertEqual(reused['snapshot_sha256'], value['snapshot_sha256'])
        self.assertEqual(reused['cvat_status']['completed_jobs'], 0)

    def test_job_only_requests_and_invalid_deleted_indices_are_rejected(self):
        for config in ({'jobs': [30]}, {'task_id': True}, {'task_id': -1}):
            with self.assertRaises(ValueError):
                datasets.import_lot(config, client=self.Client())
        job = self.Client().request('/jobs/31')
        meta = self.Client().request('/jobs/31/data/meta')
        for deleted in ([0], [3], ['1'], [1, 1]):
            with self.subTest(deleted=deleted), self.assertRaises(ValueError):
                datasets.active_job_frames(job, {**meta, 'deleted_frames': deleted})


if __name__ == '__main__':
    unittest.main()
