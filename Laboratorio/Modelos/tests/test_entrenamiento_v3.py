"""Integridad, reserva y despacho de entrenamiento geométrico sin ejecutar ML."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import preparacion_v3 as preparation
import entrenamiento_v3 as training
import panel_modelos as panel
import panel_worker as worker
from test_preparacion_v3 import fixture


class TrainingV3Tests(unittest.TestCase):
    def test_final_evaluation_callback_does_not_invent_an_extra_epoch(self):
        from types import SimpleNamespace
        progress = Mock()
        start, end = training.epoch_progress_callbacks(progress)
        for epoch in range(26):
            trainer = SimpleNamespace(epoch=epoch)
            start(trainer)
            end(trainer)
        end(SimpleNamespace(epoch=26))
        end(SimpleNamespace(epoch=25))
        completions = [c.kwargs['completed_epochs'] for c in progress.call_args_list if 'completed_epochs' in c.kwargs]
        self.assertEqual(completions, list(range(1, 27)))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.part, snapshot = fixture()
        snapshot['tasks'][0]['annotations']['shapes'][0]['attributes'][0]['value'] = 'parcial'
        snapshot['tasks'][0]['annotations']['shapes'][-1]['attributes'][0]['value'] = 'pendiente'
        file = self.root / preparation.PARTITION
        file.parent.mkdir(parents=True)
        preparation.write(file, self.part)
        for index, row in enumerate(self.part['imagenes']):
            from PIL import Image
            Image.new('RGB', (100, 100), (index * 20, 0, 0)).save(self.root / row['path'])
            row['sha256'] = preparation.digest(self.root / row['path'])
        preparation.write(file, self.part)
        self.report = preparation.analyze(self.part, snapshot)
        self.report.update(id='v3_20261025_000000_12345678', partition_id='fixture',
                           partition_sha256=preparation.digest(file))
        folder = self.root / preparation.OUTPUT / self.report['id']
        folder.mkdir(parents=True)
        for name, value in (('informe.json', self.report), ('snapshot_cvat.json', snapshot), ('particion.json', self.part)):
            preparation.write(folder / name, value)
        self.folder = folder
        out = preparation.export(self.root, dict(id=self.report['id'], reviewed=True, author='Revisor'))
        self.source = out['path']
        weights = self.root / training.DEFAULTS['model']
        weights.parent.mkdir(parents=True)
        weights.write_bytes(b'fixture')
        self.config = {**training.DEFAULTS, 'source': self.source, 'pipeline': training.CRITERION, 'action': 'train'}
        self.partition_patch = patch.object(preparation, 'partition', return_value=self.part)
        self.partition_patch.start()
        self.addCleanup(self.partition_patch.stop)

    def test_reviewed_partial_export_passes_and_test_pixels_are_never_opened(self):
        # Even missing test pixels must not be read for development training.
        for split in ('test_real', 'test_sintetica'):
            for image in (self.root / self.source / 'images' / split).glob('*'):
                image.unlink()
        _, receipt, dev = training.validate_export(self.root, self.source)
        self.assertEqual([i['name'] for i in dev], ['foto_0.png', 'foto_1.png', 'foto_2.png'])
        self.assertEqual(dev[0]['shapes'][0]['delimitacion'], 'parcial')
        self.assertTrue(dev[0]['shapes'][0]['occluded'])
        self.assertEqual(receipt['counts']['test_real'], 1)

    def test_modified_labels_images_inclusions_snapshot_and_lists_are_rejected(self):
        targets = [self.root / self.source / 'labels/train/foto_0.txt',
                   self.root / self.source / 'images/train/foto_0.png',
                   self.root / self.source / 'train.txt',
                   self.root / self.source / 'manifest.json', self.folder / 'snapshot_cvat.json']
        for target in targets:
            original = target.read_bytes()
            with self.subTest(target=target.name):
                if target.name == 'manifest.json':
                    value = preparation.read(target)
                    value['included'][0]['split'] = 'test'
                    preparation.write(target, value)
                elif target.name == 'snapshot_cvat.json':
                    value = preparation.read(target)
                    value['tasks'][0]['annotations']['shapes'][0]['points'][0] = 2
                    preparation.write(target, value)
                else:
                    target.write_bytes(b'changed')
                with self.assertRaises(ValueError):
                    training.validate_export(self.root, self.source)
                target.write_bytes(original)

    def test_unreviewed_previous_policy_and_unsafe_path_are_rejected(self):
        target = self.root / self.source / 'manifest.json'
        original = preparation.read(target)
        for change in ({'reviewed': False}, {'reviewed_visible_regions': False}, {'policy_version': 'old'}):
            preparation.write(target, {**original, **change})
            with self.assertRaises(ValueError):
                training.validate_export(self.root, self.source)
        for path in ('../private', self.source + '/../exportacion_12345678'):
            with self.assertRaises(ValueError):
                training.export_path(self.root, path)

    def test_config_rejects_v2_weights_and_invalid_numbers_and_has_unique_run(self):
        first = training.validate_config(self.root, self.config)
        self.assertNotEqual(first['run'], training.validate_config(self.root, self.config)['run'])
        for change in ({'model': 'Experimentos/v2/best.pt'}, {'lr': float('nan')}, {'batch': True},
                       {'imgsz': 641}, {'patience': 0}, {'name': '../../overwrite'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                training.validate_config(self.root, {**self.config, **change})

    def test_frozen_run_contains_development_only_and_detects_later_change(self):
        config = training.validate_config(self.root, self.config)
        run = self.root / 'Experimentos' / config['run']
        run.parent.mkdir()
        training.freeze_run(self.root, config, run)
        training.verify_run(run)
        self.assertFalse(list((run / 'dataset_niveles').glob('images/test*')))
        manifest = preparation.read(run / 'manifest.json')
        self.assertFalse(manifest['test_used'])
        self.assertEqual(manifest['clases'], ['Nivel'])
        for yaml in (run / 'dataset_niveles').glob('*.yaml'):
            self.assertNotIn('test', yaml.read_text())
        label = next((run / 'dataset_niveles/labels/train').glob('*'))
        label.write_text('changed')
        with self.assertRaises(ValueError):
            training.verify_run(run)

    def test_worker_dispatch_uses_v3_and_never_calls_state_trainer(self):
        job = self.root / 'job'
        job.mkdir()
        preparation.write(job / 'solicitud.json', {**self.config, 'run': 'fixture'})
        with patch.object(training, 'execute') as execute, patch.object(worker.pilot, 'prepare') as legacy:
            worker.execute(job)
        execute.assert_called_once()
        legacy.assert_not_called()

    def test_exif_pixels_are_oriented_losslessly_without_changing_polygon_coordinates(self):
        from PIL import Image, ImageOps, ImageChops
        source, target = self.root / 'portrait.jpg', self.root / 'prepared.jpg'
        exif = Image.Exif()
        exif[274] = 6
        image = Image.new('RGB', (40, 80), 'red')
        image.paste('blue', (0, 0, 40, 40))
        image.save(source, exif=exif)
        row = {'name': source.name, 'width': 80, 'height': 40, 'sha256': preparation.digest(source)}
        before = source.read_bytes()
        saved, record = training.copy_oriented(source, target, row)
        with Image.open(source) as original, Image.open(saved) as prepared:
            self.assertEqual(prepared.size, (80, 40))
            self.assertEqual(prepared.getexif().get(274, 1), 1)
            self.assertIsNone(ImageChops.difference(prepared, ImageOps.exif_transpose(original)).getbbox())
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse(record['polygon_coordinates_changed'])
        self.assertEqual(record['operation'], 'exif_transpose_to_png')

    def test_actual_train_contract_keeps_real_selection_and_synthetic_diagnostic(self):
        config = training.validate_config(self.root, self.config)
        run = self.root / 'Experimentos' / config['run']
        run.parent.mkdir()
        training.register_run(self.root, config, run)
        self.assertTrue(preparation.read(run / 'manifest.json')['preparing'])
        self.assertFalse((run / 'dataset_niveles').exists())
        job = self.root / 'job'
        job.mkdir()
        preparation.write(job / 'solicitud.json', config)
        model = Mock(names={0: 'Nivel'})
        def train(**kwargs):
            best = run / 'entrenamiento/weights/best.pt'
            best.parent.mkdir(parents=True)
            best.write_bytes(b'fake weights')
        model.train.side_effect = train
        model.val.return_value.results_dict = {'metrics/mAP50-95(M)': .5}
        torch = Mock(__version__='fixture')
        torch.cuda.is_available.return_value = False
        runtime = Mock(__version__='fixture')
        with patch('entrenar_niveles.load_runtime', return_value=(torch, runtime)), patch('entrenar_niveles.load_model', return_value=model):
            training.execute(self.root, job, Mock())
        args = model.train.call_args.kwargs
        self.assertTrue(args['data'].endswith('val_real.yaml'))
        self.assertEqual(args['optimizer'], 'AdamW')
        self.assertEqual(args['lr0'], .001)
        self.assertFalse(args['amp'])
        self.assertEqual([Path(c.kwargs['data']).stem for c in model.val.call_args_list], ['val_real', 'val_sintetica'])
        self.assertFalse(preparation.read(job / 'resultado.json')['test_used'])

    def test_panel_dispatch_accepts_only_v3_train_action(self):
        with patch.object(panel, 'ROOT', self.root):
            self.assertEqual(panel.validate(self.config, {})['source_kind'], 'v3_export')
            with self.assertRaises(ValueError):
                panel.validate({**self.config, 'action': 'predict'}, {})


if __name__ == '__main__':
    unittest.main()
