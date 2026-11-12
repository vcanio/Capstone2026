"""Seguimiento sin GPU: etapas reales del trabajador y vistas guardadas del ensayo."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import panel_modelos as panel
import panel_worker as worker


class TrainingProgressTests(unittest.TestCase):
    def test_worker_tracks_stages_without_changing_training_parameters(self):
        with TemporaryDirectory() as directory:
            job = Path(directory)
            config = {'action':'train', 'run':'fixture', 'epochs':100, 'model':'general.pt',
                      'imgsz':640, 'batch':2, 'lr':0.001, 'seed':42}
            (job/'solicitud.json').write_text(json.dumps(config), encoding='utf-8')
            stages=[]
            original=panel.write_json

            def write(path, value):
                stages.append(dict(value))
                original(path, value)

            def train(*args, progress):
                self.assertEqual(args, (100, worker.pilot.ROOT/'general.pt', 640, 2, 0.001, 42))
                progress('training',current_epoch=1)
                progress('training',completed_epochs=1)

            with patch.object(panel,'write_json',side_effect=write), \
                 patch.object(worker.pilot,'RUN',worker.pilot.RUN), \
                 patch.object(worker.pilot,'SEED',42), \
                 patch.object(worker.pilot,'prepare'), \
                 patch.object(worker.pilot,'train',side_effect=train), \
                 patch.object(worker.pilot,'evaluate',side_effect=lambda progress:progress('comparing')):
                worker.execute(job)
            self.assertEqual([s['stage'] for s in stages],
                             ['preparing','training','training','training','evaluating','comparing','done'])
            result=panel.read_json(job/'progreso.json')
            self.assertEqual(result['completed_epochs'],1)
            self.assertEqual(result['total_epochs'],100)
            self.assertEqual(panel.read_json(job/'resultado.json'),{'run':'fixture'})

    def test_job_preview_comes_from_its_run_and_prefers_validation(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            job=root/'job';job.mkdir()
            training=root/'Experimentos/fixture/entrenamiento';training.mkdir(parents=True)
            panel.write_json(job/'estado.json',{'state':'running','config':{'action':'train','run':'fixture'}})
            panel.write_json(job/'progreso.json',{'stage':'training','completed_epochs':3})
            (training/'train_batch0.jpg').write_bytes(b'fixture')
            (training/'val_batch0_pred.jpg').write_bytes(b'fixture')
            panel.write_json(training.parent/'entorno.json',{'gpu':'GPU fixture'})
            with patch.object(panel,'ROOT',root):
                status=panel.job_status(job)
            self.assertEqual(status['progress']['stage'],'training')
            self.assertEqual(status['progress']['device'],'GPU fixture')
            self.assertEqual(status['progress']['preview_kind'],'validation')
            self.assertIn('val_batch0_pred.jpg',status['progress']['preview_url'])

    def test_old_jobs_without_progress_remain_readable(self):
        with TemporaryDirectory() as directory:
            job=Path(directory)
            panel.write_json(job/'estado.json',{'state':'done','config':{'action':'train','run':'fixture'}})
            self.assertEqual(panel.job_status(job)['state'],'done')
            self.assertIsNone(panel.job_status(job)['progress']['device'])


if __name__=='__main__':
    unittest.main()
