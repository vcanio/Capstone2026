"""Reutilizacion y proteccion de una exportacion compartida entre ensayos."""
import json
from pathlib import Path
import tempfile
import unittest

from conjuntos import consolidate_export, dataset_directory, experiment_file, verify_export


class SharedDatasetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.version = 'datos_20261015_012453_4ba1d339'

    def make_run(self, name, label='0 0.1 0.1 0.9 0.1 0.9 0.9'):
        run = self.root / 'Experimentos' / name
        (run / 'dataset_niveles/images/train').mkdir(parents=True)
        (run / 'dataset_niveles/labels/train').mkdir(parents=True)
        (run / 'dataset_niveles/images/train/REAL_01.jpg').write_bytes(b'immutable-image')
        (run / 'dataset_niveles/labels/train/REAL_01.txt').write_text(label)
        (run / 'manifest.json').write_text(json.dumps(dict(
            dataset_dir='dataset_niveles', version_datos=self.version, clases=['Nivel_vacio'])))
        return run

    def test_two_runs_share_one_verified_export_and_keep_historical_label_paths(self):
        first, second = self.make_run('primero'), self.make_run('segundo')
        shared = consolidate_export(self.root, first)
        self.assertEqual(consolidate_export(self.root, second), shared)
        self.assertFalse((first / 'dataset_niveles').exists())
        self.assertFalse((second / 'dataset_niveles').exists())
        self.assertEqual(dataset_directory(self.root, first), dataset_directory(self.root, second))
        self.assertEqual(experiment_file(self.root, 'Experimentos/primero/dataset_niveles/labels/train/REAL_01.txt'),
                         shared / 'labels/train/REAL_01.txt')
        self.assertEqual(len(verify_export(shared)['archivos']), 3)

    def test_changed_labels_cannot_replace_an_export_with_the_same_version(self):
        first = self.make_run('primero')
        shared = consolidate_export(self.root, first)
        original = (shared / 'labels/train/REAL_01.txt').read_bytes()
        second = self.make_run('segundo', label='1 0.1 0.1 0.9 0.1 0.9 0.9')
        with self.assertRaisesRegex(ValueError, 'exportacion distinta'):
            consolidate_export(self.root, second)
        self.assertEqual((shared / 'labels/train/REAL_01.txt').read_bytes(), original)
        self.assertTrue((second / 'dataset_niveles').is_dir())

    def test_modified_shared_content_is_detected_before_reuse(self):
        shared = consolidate_export(self.root, self.make_run('primero'))
        (shared / 'images/train/REAL_01.jpg').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'fue modificada'):
            consolidate_export(self.root, self.make_run('segundo'))

    def test_unrelated_version_and_unsafe_directory_are_rejected(self):
        run = self.make_run('primero')
        consolidate_export(self.root, run)
        metadata = json.loads((run / 'manifest.json').read_text())
        metadata['dataset_ref']['version'] = '../other'
        with self.assertRaisesRegex(ValueError, 'no corresponde'):
            dataset_directory(self.root, run, metadata)

    def test_comparison_signature_ignores_relocation_of_registered_sources(self):
        import panel_modelos as panel
        old = dict(imagenes=[dict(archivo='Equilibrado_v1_20261013/reales/entrenamiento/REAL_01.jpg', sha256='abc')])
        current = dict(imagenes=[dict(archivo='V1/Lider/lider_001.jpg', sha256='abc')])
        self.assertEqual(panel.dataset_signature(old, b'snapshot'), panel.dataset_signature(current, b'snapshot'))
