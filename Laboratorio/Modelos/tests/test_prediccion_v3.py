"""Pruebas V3: modelos terminados, validación íntegra y reserva fuera del ajuste."""
from pathlib import Path
import unittest
from unittest.mock import patch

import preparacion_v3 as preparation
import entrenamiento_v3 as training
import prediccion_v3 as prediction
import panel_modelos as panel
import test_entrenamiento_v3 as training_tests


class PredictionV3Tests(unittest.TestCase):
    def test_archived_v3_weights_are_hidden_and_rejected_but_preserved(self):
        last = self.model.replace('best.pt', 'last.pt')
        (self.root / '.config-modelo').mkdir()
        preparation.write(self.root / '.config-modelo/modelos_archivados.json',
                          {'schema_version': 1, 'models': {last: {'archived_at': 'test'}}})
        catalog = prediction.catalog(self.root)
        self.assertEqual([m['id'] for m in catalog['models']], [self.model])
        self.assertEqual([m['id'] for m in catalog['archived_models']], [last])
        with self.assertRaisesRegex(ValueError, 'archivado'):
            prediction.validate(self.root, {**self.request, 'model': last}, lambda _: None)
        self.assertEqual((self.root / last).read_bytes(), b'fixture')

    def setUp(self):
        training_tests.TrainingV3Tests.setUp(self)
        config = training.validate_config(self.root, self.config)
        self.run = self.root / 'Experimentos' / config['run']
        self.run.parent.mkdir()
        training.freeze_run(self.root, config, self.run)
        weights = self.run / 'entrenamiento/weights'
        weights.mkdir(parents=True)
        for checkpoint in ('best', 'last'):
            (weights / (checkpoint + '.pt')).write_bytes(b'fixture')
        preparation.write(self.run / 'metricas_geometria_v3.json', {'sets': {}, 'test_used': False})
        self.model = (weights / 'best.pt').relative_to(self.root).as_posix()
        self.request = dict(action='predict', pipeline=training.CRITERION, model=self.model,
                            source_mode='validation', photo='foto_1.png', conf=.6, nms=.7, imgsz=640)

    def test_catalog_exposes_best_last_and_only_real_synthetic_validation(self):
        value = prediction.catalog(self.root)
        self.assertEqual([m['checkpoint'] for m in value['models']], ['best', 'last'])
        self.assertEqual([p['name'] for p in value['runs'][0]['photos']], ['foto_1.png', 'foto_2.png'])
        self.assertFalse(value['occupancy_enabled'])
        self.assertFalse(value['final_test_enabled'])
        self.assertEqual(value['minimum_confidence'], .6)

    def test_user_minimum_confidence_is_enforced_without_clamping_or_changing_history(self):
        for value in [.25, .599999, 1, True, float('nan')]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'mínimo aceptado es 0,60'):
                prediction.validate(self.root, {**self.request, 'conf': value}, lambda _: None)
        for value in [.6, .75, .99]:
            clean = prediction.validate(self.root, {**self.request, 'conf': value}, lambda _: None)
            self.assertEqual(clean['conf'], value)

    def test_validation_passes_server_truth_and_rejects_train_test_or_unknown(self):
        clean = prediction.validate(self.root, {**self.request, 'truth_rows': ['spoof']}, lambda _: None)
        self.assertEqual(clean['scope'], 'Nivel_geometria')
        self.assertEqual(clean['project_version'], 'v3')
        self.assertEqual(clean['origin'], 'real')
        self.assertTrue(clean['image'].endswith('/images/val_real/foto_1.png'))
        self.assertNotEqual(clean['truth_rows'], ['spoof'])
        for name in ('foto_0.png', 'foto_3.png', '../../private', 'missing.png'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                prediction.validate(self.root, {**self.request, 'photo': name}, lambda _: None)

    def test_validation_checks_image_and_label_hashes(self):
        image, label, _ = prediction.validation_image(self.root, self.model, 'foto_1.png')
        for file in (image, label):
            original = file.read_bytes()
            file.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'integridad'):
                prediction.validation_image(self.root, self.model, 'foto_1.png')
            file.write_bytes(original)

    def test_upload_has_no_truth_and_known_training_or_test_images_are_rejected(self):
        photo = {'id': 'Experimentos/panel_pruebas/Subidas_panel/id/imagen.jpg',
                 'name': 'nueva.jpg', 'sha256_original': 'new_photo'}
        config = {**self.request, 'source_mode': 'upload', 'image': photo['id'], 'truth_rows': ['spoof']}
        clean = prediction.validate(self.root, config, lambda _: photo)
        self.assertEqual(clean['image_source'], 'upload')
        self.assertNotIn('truth_rows', clean)
        self.assertNotIn('split', clean)
        for idx in (0, 3):
            photo['sha256_original'] = self.part['imagenes'][idx]['sha256']
            with self.assertRaises(ValueError):
                prediction.validate(self.root, config, lambda _: photo)

    def test_invalid_models_parameters_and_occupancy_are_rejected(self):
        for change in ({'model': '../private.pt'}, {'model': training.DEFAULTS['model']},
                       {'imgsz': 641}, {'conf': float('nan')}, {'nms': True},
                       {'occupancy': True}, {'source_mode': 'test'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                prediction.validate(self.root, {**self.request, **change}, lambda _: None)
        metrics = self.run / 'metricas_geometria_v3.json'
        metrics.unlink()
        with self.assertRaises(ValueError):
            prediction.run_path(self.root, self.model)

    def test_panel_dispatches_v3_predictions_without_a_legacy_run(self):
        with patch.object(panel, 'ROOT', self.root):
            clean = panel.validate(self.request, {'runs': [], 'models': []})
        self.assertEqual(clean['scope'], 'Nivel_geometria')
        self.assertEqual(clean['split'], 'val')


if __name__ == '__main__':
    unittest.main()
