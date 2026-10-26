"""Model visibility persists without deleting weights or experiment evidence."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import panel_modelos as panel


class ModelArchiveTests(unittest.TestCase):
    def setUp(self):
        workspace = Path(__file__).resolve().parents[3]
        test_dir = workspace / '.impeccable/test-tmp'
        test_dir.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=test_dir)
        assert Path(self.temp.name).resolve().is_relative_to(test_dir.resolve())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'Laboratorio/Experimentos/ensayo_fixture'
        self.weights = self.run / 'entrenamiento/weights'
        self.weights.mkdir(parents=True)
        (self.run / 'manifest.json').write_text(json.dumps({'imagenes': []}), encoding='utf-8')
        (self.run / 'snapshot_cvat.json').write_text('{}', encoding='utf-8')
        for kind in ('best', 'last'):
            (self.weights / f'{kind}.pt').write_bytes(f'weights-{kind}'.encode())
        self.general = self.root / 'Modelos/preentrenados/general.pt'
        self.general.parent.mkdir(parents=True)
        self.general.write_bytes(b'general-weights')
        self.best = 'Laboratorio/Experimentos/ensayo_fixture/entrenamiento/weights/best.pt'
        self.last = 'Laboratorio/Experimentos/ensayo_fixture/entrenamiento/weights/last.pt'
        for context in (patch.object(panel, 'ROOT', self.root),
                        patch.object(panel, 'JOBS', self.root / 'Laboratorio/Experimentos/panel_pruebas'),
                        patch.object(panel, 'ACTIVE', None),
                        patch.object(panel, 'inventory', return_value=[]),
                        patch.object(panel.datasets, 'versions', return_value=[])):
            context.start()
            self.addCleanup(context.stop)

    def test_archive_persists_and_restore_keeps_files_and_history(self):
        panel.change_model_visibility({'id': self.best}, archive=True)
        data = panel.catalog()
        self.assertNotIn(self.best, [m['id'] for m in data['models']])
        self.assertIn(self.last, [m['id'] for m in data['models']])
        self.assertEqual(data['archived_models'][0]['id'], self.best)
        self.assertIsNotNone(data['archived_models'][0]['archived_at'])
        self.assertEqual(data['runs'][0]['id'], 'ensayo_fixture')
        self.assertEqual((self.weights / 'best.pt').read_bytes(), b'weights-best')
        saved = json.loads(panel.model_archive_path().read_text(encoding='utf-8'))
        self.assertIn(self.best, saved['models'])
        panel.change_model_visibility({'id': self.best}, archive=False)
        self.assertIn(self.best, [m['id'] for m in panel.catalog()['models']])
        self.assertEqual(panel.catalog()['archived_models'], [])
        self.assertEqual((self.weights / 'last.pt').read_bytes(), b'weights-last')

    def test_archived_weights_cannot_be_selected_for_new_jobs(self):
        panel.change_model_visibility({'id': self.best}, archive=True)
        with self.assertRaisesRegex(ValueError, 'modelo'):
            panel.validate({'model': self.best}, panel.catalog())
        panel.change_model_visibility({'id': self.best}, archive=True)
        self.assertEqual(len(panel.catalog()['archived_models']), 1)

    def test_unknown_paths_and_general_models_are_rejected_without_writes(self):
        for model_id in (None, '', True, [], '../private.pt', self.general.as_posix(),
                         'Modelos/preentrenados/general.pt'):
            with self.subTest(model=model_id), self.assertRaises(ValueError):
                panel.change_model_visibility({'id': model_id}, archive=True)
        self.assertFalse(panel.model_archive_path().exists())
        self.assertEqual(self.general.read_bytes(), b'general-weights')

    def test_running_input_and_output_models_are_protected(self):
        state = panel.JOBS / 'active/estado.json'
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({'config': {'model': self.best}}), encoding='utf-8')
        with patch.object(panel, 'ACTIVE', 'active'):
            with self.assertRaisesRegex(ValueError, 'curso'):
                panel.change_model_visibility({'id': self.best}, archive=True)
            panel.change_model_visibility({'id': self.last}, archive=True)
            panel.change_model_visibility({'id': self.last}, archive=False)
            state.write_text(json.dumps({'config': {'run': 'ensayo_fixture'}}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'curso'):
                panel.change_model_visibility({'id': self.last}, archive=True)
        self.assertEqual(panel.catalog()['archived_models'], [])

    def test_restoring_visible_or_missing_weights_is_rejected(self):
        for model_id in (self.best, 'Laboratorio/Experimentos/missing/best.pt'):
            with self.assertRaises(ValueError):
                panel.change_model_visibility({'id': model_id}, archive=False)
        self.assertFalse(panel.model_archive_path().exists())


if __name__ == '__main__':
    unittest.main()
