"""Regresiones de sincronización: versiones, revisión, pausa y desconexión."""
import copy
import threading
import unittest
from unittest.mock import Mock, patch

import datos_modelos as datasets
from sync_cvat import CvatSync
import test_datos_modelos as fixtures


class SyncTests(unittest.TestCase):
    def setUp(self):
        fixtures.DataTests.setUp(self)
        self.client = Mock()
        self.invalidated = Mock()
        self.sync = CvatSync(threading.Lock(), self.invalidated, reader=lambda: self.client)
        self.signature = 'initial'
        self.signature_patch = patch.object(self.sync, 'remote_signature', side_effect=lambda *_: self.signature)
        self.signature_patch.start(); self.addCleanup(self.signature_patch.stop)
        self.snapshot_patch = patch.object(datasets, 'fetch_snapshot', side_effect=lambda *_a, **_k: copy.deepcopy(self.snapshot))
        self.fetch = self.snapshot_patch.start(); self.addCleanup(self.snapshot_patch.stop)
        self.sync.configure({'jobs': [27], 'validation': ['03'], 'enabled': True})

    def tick(self):
        self.sync.due['27'] = 0
        self.sync.tick()
        return self.sync.status()['sources'][0]

    def test_changed_drawings_create_pending_copy_and_preserve_reviewed_training_source(self):
        first = self.tick()['version_id']
        datasets.approve({'id': first, 'reviewed': True, 'reviewer': 'Revisor'})
        original = (datasets.version_path(first) / 'snapshot_cvat.json').read_bytes()
        self.snapshot['annotations']['shapes'][0]['points'][0] = 2
        self.signature = 'changed'
        second = self.tick()['version_id']
        self.assertNotEqual(second, first)
        self.assertEqual(datasets.read(datasets.version_path(second) / 'version.json')['state'], 'pendiente_revision')
        self.assertEqual(datasets.read(datasets.version_path(first) / 'version.json')['state'], 'lista_modulos')
        self.assertEqual((datasets.version_path(first) / 'snapshot_cvat.json').read_bytes(), original)
        self.assertEqual(self.invalidated.call_count, 2)

    def test_unchanged_and_metadata_only_changes_do_not_create_duplicates(self):
        first = self.tick()['version_id']
        self.tick()
        self.assertEqual(self.fetch.call_count, 1)
        self.signature = 'metadata-changed'
        self.snapshot['exported_at'] = 'later'
        self.assertEqual(self.tick()['version_id'], first)
        self.assertEqual(len(list(self.versions.glob('*/version.json'))), 1)

    def test_network_failure_keeps_copy_and_retries_with_backoff_then_recovers(self):
        first = self.tick()['version_id']
        with patch.object(self.sync, 'remote_signature', side_effect=ValueError('CVAT no disponible')):
            failure = self.tick()
            self.assertEqual(failure['state'], 'error')
            self.assertEqual(failure['version_id'], first)
            self.assertEqual(failure['retry_seconds'], 20)
        recovered = self.tick()
        self.assertEqual(recovered['state'], 'synced')
        self.assertNotIn('error', recovered)

    def test_pause_and_restart_preserve_configuration_without_reading_cvat(self):
        first = self.tick()['version_id']
        self.sync.configure({'jobs': [27], 'validation': ['03'], 'enabled': False})
        new = CvatSync(threading.Lock(), Mock(), reader=self.client)
        new.initialize(); new.tick()
        self.assertFalse(new.status()['sources'][0]['enabled'])
        self.assertEqual(new.status()['sources'][0]['version_id'], first)
        self.client.assert_not_called()

    def test_manual_mode_clears_enabled_sources_without_starting_reader_or_worker(self):
        self.tick()
        reader = Mock(side_effect=AssertionError('No debe consultar CVAT en modo manual'))
        new = CvatSync(threading.Lock(), Mock(), reader=reader)
        new.pause_all()
        self.assertIsNone(new.thread)
        self.assertTrue(all(not s['enabled'] for s in new.status()['sources']))
        saved = datasets.read(new.path)
        self.assertTrue(all(not s['enabled'] for s in saved['sources'].values()))
        reader.assert_not_called()

    def test_archive_latest_pauses_without_recreating_hidden_version(self):
        first = self.tick()['version_id']
        datasets.archive({'id': first})
        source = self.tick()
        self.assertFalse(source['enabled'])
        self.assertEqual(source['state'], 'paused')
        self.assertEqual(len(list(self.versions.glob('*/version.json'))), 1)

    def test_pause_during_remote_read_prevents_inflight_import(self):
        def pause(*_):
            self.sync.configure({'jobs': [27], 'validation': ['03'], 'enabled': False})
            return 'change'
        with patch.object(self.sync, 'remote_signature', side_effect=pause):
            source = self.tick()
        self.assertFalse(source['enabled'])
        self.assertEqual(len(list(self.versions.glob('*/version.json'))), 0)

    def test_status_and_pause_remain_available_during_long_import(self):
        started, release = threading.Event(), threading.Event()
        original = datasets.import_jobs
        def delayed(*args, **kwargs):
            started.set()
            release.wait(3)
            return original(*args, **kwargs)
        with patch.object(datasets, 'import_jobs', side_effect=delayed):
            thread = threading.Thread(target=self.sync.tick)
            thread.start()
            self.assertTrue(started.wait(1))
            try:
                self.assertEqual(self.sync.status()['sources'][0]['state'], 'syncing')
                self.sync.configure({'jobs': [27], 'validation': ['03'], 'enabled': False})
                self.assertFalse(self.sync.status()['sources'][0]['enabled'])
            finally:
                release.set(); thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(self.sync.status()['sources'][0]['state'], 'paused')

    def test_remote_save_version_detected_even_when_job_timestamp_unchanged(self):
        # Execute the actual remote fingerprint rather than the test override.
        client = Mock()
        annotations = {'version': 1, 'shapes': [], 'tracks': [], 'tags': []}
        def request(route):
            if route == '/jobs/27':
                return {'id': 27, 'type': 'annotation', 'task_id': 13, 'updated_date': 'same'}
            if route == '/tasks/13':
                return {'id': 13, 'project_id': 4, 'updated_date': 'same'}
            return annotations
        client.request.side_effect = request
        before = CvatSync.remote_signature(self.sync, client, [27])
        annotations['version'] += 1
        self.assertNotEqual(before, CvatSync.remote_signature(self.sync, client, [27]))
        before = CvatSync.remote_signature(self.sync, client, [27])
        annotations['shapes'].append({'points': [1, 2, 3, 4, 5, 6]})
        self.assertNotEqual(before, CvatSync.remote_signature(self.sync, client, [27]))

    def test_bootstrap_follows_latest_partition_for_each_active_lot(self):
        datasets.import_jobs({'jobs': [27], 'validation': ['03']})
        datasets.import_jobs({'jobs': [27], 'validation': ['01']})
        self.sync.path.unlink()
        self.sync.initialize()
        self.assertEqual(self.sync.status()['sources'][0]['validation'], ['01'])

    def test_first_bootstrap_does_not_recreate_a_lot_whose_latest_copy_was_archived(self):
        datasets.import_jobs({'jobs': [27], 'validation': ['03']})
        self.snapshot['annotations']['shapes'][0]['points'][0] = 2
        latest = datasets.import_jobs({'jobs': [27], 'validation': ['03']})
        datasets.archive({'id': latest['id']})
        self.sync.path.unlink()
        self.sync.initialize()
        self.assertEqual(self.sync.status()['sources'], [])


if __name__ == '__main__':
    unittest.main()
