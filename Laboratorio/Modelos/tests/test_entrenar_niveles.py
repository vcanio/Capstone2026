"""Validación del criterio v2 y del flujo de entrenamiento sin consumir GPU."""
import argparse
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image
import yaml

import entrenar_niveles as training


class LevelTrainingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / 'data.yaml'
        self.config = {'train': 'images/train', 'val': 'images/val',
                       'names': list(training.CLASSES)}
        self.write_config()
        self.row = '0 0.1 0.1 0.9 0.1 0.9 0.9 0.1 0.9\n'
        for split, color in [('train', 'red'), ('val', 'blue')]:
            image = self.root / 'images' / split / 'foto.png'
            image.parent.mkdir(parents=True)
            Image.new('RGB', (10, 10), color).save(image)
            label = self.root / 'labels' / split / 'foto.txt'
            label.parent.mkdir(parents=True)
            label.write_text(''.join(self.row.replace('0 ', f'{i} ', 1) for i in range(3)))

    def write_config(self):
        self.data.write_text(yaml.safe_dump(self.config), encoding='utf-8')

    def label(self, split='train'):
        return self.root / 'labels' / split / 'foto.txt'

    def test_relative_paths_and_three_class_ids_are_preserved(self):
        dataset, report = training.validate_dataset(self.data)
        self.assertEqual(dataset['path'], str(self.root.resolve()))
        self.assertEqual(report['splits']['train']['niveles_por_clase'], dict.fromkeys(training.CLASSES, 1))
        self.assertFalse(report['advertencias'])

    def test_simple_state_names_are_accepted(self):
        self.config['names'] = {0: 'reponer', 1: 'suficiente', 2: 'no_evaluable'}
        self.write_config()
        dataset, _ = training.validate_dataset(self.data)
        self.assertEqual(dataset['names'], list(training.CLASSES))

    def test_old_classes_and_reordered_classes_are_rejected(self):
        for names in (['Nivel_vacio', 'Nivel_baja_disponibilidad', 'Nivel_suficiente', 'Nivel_no_evaluable'],
                      ['Nivel_suficiente', 'Nivel_reponer', 'Nivel_no_evaluable']):
            with self.subTest(names=names):
                self.config['names'] = names
                self.write_config()
                with self.assertRaisesRegex(ValueError, 'Clases incompatibles'):
                    training.validate_dataset(self.data)

    def test_bad_polygons_and_detection_boxes_are_rejected(self):
        for row in ('3 0 0 1 0 1 1', '0 0.5 0.5 0.2 0.2',
                    '0 nan 0 1 0 1 1', '0 -0.1 0 1 0 1 1',
                    '0 0 0 1 1 1 0 0 1', '0 0 0 0 0 0 0'):
            with self.subTest(row=row):
                self.label().write_text(row)
                with self.assertRaises(ValueError):
                    training.validate_dataset(self.data)

    def test_missing_label_is_rejected(self):
        self.label().unlink()
        with self.assertRaisesRegex(ValueError, 'Falta la etiqueta'):
            training.validate_dataset(self.data)

    def test_missing_classes_block_unless_validation_is_explicitly_exploratory(self):
        original = self.label().read_text()
        self.label().write_text(self.row)
        with self.assertRaisesRegex(ValueError, 'Faltan ejemplos en train'):
            training.validate_dataset(self.data)
        self.label().write_text(original)
        self.label('val').write_text(self.row)
        with self.assertRaisesRegex(ValueError, 'Faltan ejemplos en val'):
            training.validate_dataset(self.data)
        _, report = training.validate_dataset(self.data, allow_incomplete=True)
        self.assertIn('Nivel_suficiente', report['advertencias'][0])

    def test_identical_photos_across_splits_are_rejected(self):
        image = self.root / 'images/train/foto.png'
        (self.root / 'images/val/foto.png').write_bytes(image.read_bytes())
        with self.assertRaisesRegex(ValueError, 'Imagen duplicada'):
            training.validate_dataset(self.data)

    def test_original_and_synthetic_variant_cannot_cross_splits(self):
        for split, name in [('train', 'lider_express_001_0_original'),
                            ('val', 'lider_express_001_A_vacios')]:
            (self.root / 'images' / split / 'foto.png').rename(self.root / 'images' / split / f'{name}.png')
            self.label(split).rename(self.root / 'labels' / split / f'{name}.txt')
        with self.assertRaisesRegex(ValueError, 'Familia repartida'):
            training.validate_dataset(self.data)

    def test_check_only_does_not_train_or_create_experiment(self):
        with patch.object(training, 'train') as train:
            training.main(['--data', str(self.data), '--solo-verificar'])
        train.assert_not_called()
        self.assertFalse((self.root / 'Laboratorio/Experimentos').exists())

    def test_runtime_check_with_dataset_never_starts_training(self):
        with patch.object(training, 'load_model'), patch.object(training, 'train') as train:
            training.main(['--data', str(self.data), '--verificar-entorno'])
        train.assert_not_called()

    def test_training_passes_augmentation_and_evaluates_best_weights(self):
        checkpoint = self.root / 'base.pt'
        checkpoint.write_bytes(b'fixture')
        args = argparse.Namespace(modelo=str(checkpoint), nombre='prueba', device='auto',
                                  epochs=100, imgsz=640, batch=2, seed=42, lr=0.001, patience=20,
                                  evaluar_test=False, conf=0.25, iou_mascara=0.5)
        dataset, report = training.validate_dataset(self.data)
        calls = []

        class FakeYOLO:
            task = 'segment'
            names = dict(enumerate(training.CLASSES))

            def __init__(self, path):
                calls.append(('load', path))

            def train(self, **kwargs):
                calls.append(('train', kwargs))
                best = Path(kwargs['project']) / kwargs['name'] / 'weights/best.pt'
                best.parent.mkdir(parents=True)
                best.write_bytes(b'best')

            def val(self, **kwargs):
                calls.append(('val', kwargs))
                return SimpleNamespace(results_dict={'metrics/mAP50(M)': 0.5}, summary=lambda: [])

        torch = SimpleNamespace(__version__='fixture', version=SimpleNamespace(cuda=None),
                                cuda=SimpleNamespace(is_available=lambda: False))
        ultralytics = SimpleNamespace(__version__='fixture', YOLO=FakeYOLO, settings={})
        with patch.object(training, 'ROOT', self.root), \
             patch.object(training, 'load_runtime', return_value=(torch, ultralytics)), \
             patch('evaluar_niveles_v2.evaluate_split', return_value=({}, [])):
            run = training.train(args, dataset, report)
            with self.assertRaisesRegex(ValueError, 'Ya existe'):
                training.train(args, dataset, report)
        settings = calls[1][1]
        self.assertEqual(settings['degrees'], 3.0)
        self.assertEqual(settings['translate'], 0.05)
        self.assertEqual(settings['scale'], 0.15)
        self.assertEqual(settings['mosaic'], 0.0)
        self.assertEqual(settings['device'], 'cpu')
        self.assertEqual(calls[2], ('load', str(run / 'entrenamiento/weights/best.pt')))
        self.assertEqual(calls[3][1]['split'], 'val')
        self.assertEqual(json.loads((run / 'metricas_validacion.json').read_text())['agregadas'], {'metrics/mAP50(M)': 0.5})

    def test_corrupt_png_is_rejected(self):
        (self.root / 'images/train/foto.png').write_text('texto con extension png')
        with self.assertRaisesRegex(ValueError, 'Imagen inválida'):
            training.validate_dataset(self.data)

    def test_actual_yolo_inventory_includes_mpo(self):
        image = self.root / 'images/train/foto.png'
        Image.new('RGB', (10, 10), 'green').save(image.with_suffix('.mpo'), format='JPEG')
        image.unlink()
        _, report = training.validate_dataset(self.data)
        self.assertTrue(report['splits']['train']['archivos'][0]['imagen'].endswith('.mpo'))

    def test_exif_rotation_is_rejected_before_training(self):
        image = self.root / 'images/train/foto.png'
        exif = Image.Exif()
        exif[274] = 6
        Image.new('RGB', (12, 10), 'green').save(image.with_suffix('.jpg'), exif=exif)
        image.unlink()
        with self.assertRaisesRegex(ValueError, 'EXIF'):
            training.validate_dataset(self.data)

    def test_snapshot_excludes_stale_label_and_image_caches(self):
        (self.root / 'labels/train.cache').write_bytes(b'old cache')
        (self.root / 'images/train/foto.npy').write_bytes(b'old pixels')
        dataset, report = training.validate_dataset(self.data)
        run = self.root / 'ensayo'
        run.mkdir()
        _, frozen = training.snapshot_dataset(run, dataset, report)
        self.assertFalse(list((run / 'dataset').rglob('*.cache')))
        self.assertFalse(list((run / 'dataset').rglob('*.npy')))
        self.label().write_text(self.label().read_text().replace('0.1', '0.2'))
        training.verify_snapshot(frozen)  # Cambiar el original no afecta al ensayo.

    def test_same_size_label_edit_between_review_and_snapshot_is_rejected(self):
        dataset, report = training.validate_dataset(self.data)
        self.label().write_text(self.label().read_text().replace('0.1', '0.2'))
        run = self.root / 'ensayo'
        run.mkdir()
        with self.assertRaisesRegex(ValueError, 'cambió después'):
            training.snapshot_dataset(run, dataset, report)

    def test_incompatible_runtime_has_actionable_error(self):
        with patch.object(training, 'version', return_value='8.3.230'):
            with self.assertRaisesRegex(ValueError, 'igual que Docker'):
                training.check_compatibility()

    def test_incompatible_weights_have_readable_error(self):
        checkpoint = self.root / 'modelo.pt'
        checkpoint.touch()
        def fail(path):
            raise AttributeError("Can't get attribute 'Segment26'")
        runtime = SimpleNamespace(YOLO=fail, __version__=training.ULTRALYTICS_VERSION)
        with self.assertRaisesRegex(ValueError, 'No se pudo cargar modelo.pt'):
            training.load_model(checkpoint, runtime)

    def test_per_class_numpy_numbers_are_serialized(self):
        import numpy as np
        path = self.root / 'metricas.json'
        training.save_json(path, {'referencias': np.int64(3), 'precision': np.float32(0.5)})
        self.assertEqual(json.loads(path.read_text()), {'referencias': 3, 'precision': 0.5})

    def test_test_partition_is_checked_for_leakage(self):
        self.config['test'] = 'images/test'
        self.write_config()
        target = self.root / 'images/test/foto.png'
        target.parent.mkdir(parents=True)
        target.write_bytes((self.root / 'images/train/foto.png').read_bytes())
        label = self.root / 'labels/test/foto.txt'
        label.parent.mkdir(parents=True)
        label.write_text(self.label().read_text())
        with self.assertRaisesRegex(ValueError, 'Imagen duplicada'):
            training.validate_dataset(self.data)

    def test_mutating_snapshot_is_detected(self):
        dataset, report = training.validate_dataset(self.data)
        run = self.root / 'ensayo'
        run.mkdir()
        _, frozen = training.snapshot_dataset(run, dataset, report)
        label = Path(frozen['splits']['train']['archivos'][0]['etiqueta'])
        label.write_text(label.read_text().replace('0.1', '0.2'))
        with self.assertRaisesRegex(ValueError, 'copia del ensayo fue modificada'):
            training.verify_snapshot(frozen)


if __name__ == '__main__':
    unittest.main()
