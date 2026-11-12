import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import revision_visibilidad_cvat as review


class ProposalTests(unittest.TestCase):
    def test_lotes_tienen_confirmacion_independiente(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first, second = folder / 'p1.json', folder / 'p2.json'
            approval1, approval2 = folder / 'a1.json', folder / 'a2.json'
            images = [{'name': f'f{n}', 'cvat_name': f'f{n}', 'split': 'train' if n < 336 else 'val',
                       'origen': 'real', 'etiqueta': 'pendiente'} for n in range(405)]
            train = {f'f{n}': n for n in range(336)}
            val = {f'f{n}': n-336 for n in range(336, 405)}
            receipt = {'status': 'lista_para_revision', 'inventory_sha256': 'hash', 'project_id': 12,
                       'tasks': [{'split': 'train', 'task_id': 37, 'status': 'verificada', 'frames': train},
                                 {'split': 'val', 'task_id': 38, 'status': 'verificada', 'frames': val}]}
            for path, frame in ((first, 0), (second, 1)):
                path.write_text(json.dumps({'project_id': 12, 'inventory_sha256': 'hash', 'status': 'verificadas',
                                            'targets': [{'task_id': 37, 'frame': frame}]}), encoding='utf-8')
            tags = [{'id': 4, 'label_id': 1, 'frame': 0, 'attributes': [{'spec_id': 10, 'value': 'no_apta'}, {'spec_id': 11, 'value': 'persona'}]},
                    {'id': 5, 'label_id': 1, 'frame': 1, 'attributes': [{'spec_id': 10, 'value': 'apta'}, {'spec_id': 11, 'value': 'sin_definir'}]}]
            class Reader:
                def listing(self, route):
                    return [{'name': 'Evaluabilidad', 'type': 'tag', 'id': 1, 'attributes': [{'id': 10, 'name': 'decision'}, {'id': 11, 'name': 'motivo'}]}]
                def request(self, route):
                    frames = train if '/37/' in route else val
                    if route.endswith('/data/meta'):
                        return {'frames': [{'name': name} for name in frames], 'deleted_frames': []}
                    return {'tags': tags if '/37/' in route else [], 'shapes': [], 'tracks': []}
            reader = Reader()
            with patch.object(review, 'PROPOSALS', first), patch.object(review, 'APPROVAL', approval1), \
                 patch.object(review, 'SECOND_PROPOSALS', second), patch.object(review, 'SECOND_APPROVAL', approval2), \
                 patch.object(review, 'digest', return_value='hash'):
                review.confirm_proposals(reader, {'images': images}, receipt, True, 'tarea33')
                state = review.collect(reader, {'images': images}, receipt)
                self.assertEqual([r['etiqueta'] for r in state['images'][:2]], ['no_apta', 'pendiente'])
                review.confirm_proposals(reader, {'images': images}, receipt, True, 'revision_visual')
                tags[1]['attributes'][0]['value'] = 'pendiente'
                state = review.collect(reader, {'images': images}, receipt)
                self.assertTrue(state['proposal_batches']['tarea33']['confirmed'])
                self.assertFalse(state['proposal_batches']['revision_visual']['confirmed'])
                self.assertEqual([r['etiqueta'] for r in state['images'][:2]], ['no_apta', 'pendiente'])

    def test_propuestas_requieren_confirmacion_y_cambios_la_invalidan(self):
        with tempfile.TemporaryDirectory() as directory:
            proposals = Path(directory) / 'propuestas.json'
            approval = Path(directory) / 'confirmacion.json'
            images = [{'name': f'f{n}', 'cvat_name': f'f{n}', 'split': 'train' if n < 336 else 'val',
                       'origen': 'sintetica', 'etiqueta': 'pendiente'} for n in range(405)]
            train = {f'f{n}': n for n in range(336)}
            val = {f'f{n}': n-336 for n in range(336, 405)}
            receipt = {'status': 'lista_para_revision', 'inventory_sha256': 'hash', 'project_id': 12,
                       'tasks': [{'split': 'train', 'task_id': 37, 'status': 'verificada', 'frames': train},
                                 {'split': 'val', 'task_id': 38, 'status': 'verificada', 'frames': val}]}
            proposals.write_text(json.dumps({'project_id': 12, 'inventory_sha256': 'hash', 'status': 'verificadas',
                                              'targets': [{'task_id': 37, 'frame': 0}]}), encoding='utf-8')
            tag = {'id': 4, 'label_id': 1, 'frame': 0, 'attributes': [
                {'spec_id': 10, 'value': 'no_apta'}, {'spec_id': 11, 'value': 'persona'}]}
            class Reader:
                def listing(self, route):
                    return [{'name': 'Evaluabilidad', 'type': 'tag', 'id': 1,
                             'attributes': [{'id': 10, 'name': 'decision'}, {'id': 11, 'name': 'motivo'}]}]
                def request(self, route):
                    frames = train if '/37/' in route else val
                    if route.endswith('/data/meta'):
                        return {'frames': [{'name': name} for name in frames], 'deleted_frames': []}
                    return {'tags': [tag] if '/37/' in route else [], 'shapes': [], 'tracks': []}
            reader = Reader()
            with patch.object(review, 'PROPOSALS', proposals), patch.object(review, 'APPROVAL', approval), \
                 patch.object(review, 'SECOND_PROPOSALS', Path(directory) / 'inexistente.json'), \
                 patch.object(review, 'SECOND_APPROVAL', Path(directory) / 'inexistente_aprobacion.json'), \
                 patch.object(review, 'digest', return_value='hash'):
                before = review.collect(reader, {'images': images}, receipt)
                self.assertEqual(before['images'][0]['etiqueta'], 'pendiente')
                self.assertEqual(before['images'][0]['propuesta']['decision'], 'no_apta')
                with self.assertRaises(ValueError):
                    review.confirm_proposals(reader, {'images': images}, receipt, False)
                review.confirm_proposals(reader, {'images': images}, receipt, True)
                after = review.collect(reader, {'images': images}, receipt)
                self.assertTrue(after['proposals_confirmed'])
                self.assertEqual(after['images'][0]['etiqueta'], 'no_apta')
                tag['attributes'][1]['value'] = 'carro'
                changed = review.collect(reader, {'images': images}, receipt)
                self.assertFalse(changed['proposals_confirmed'])
                self.assertEqual(changed['images'][0]['etiqueta'], 'pendiente')


if __name__ == '__main__':
    unittest.main()
