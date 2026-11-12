import unittest
from pathlib import Path
from unittest.mock import patch
import selecciones_v3 as s

class SinTapadasTests(unittest.TestCase):
    def test_excluye_tarea_33_de_train_y_validacion_y_cinco_whatsapp(self):
        rows = [{'name': 'tapada_train', 'task_id': 24}, {'name': 'tapada_val', 'task_id': 24},
                {'name': 'normal', 'task_id': 27}] + [{'name': f'whatsapp_{i}', 'task_id': 31} for i in range(5)]
        images = [{'name': r['name'], 'split': 'val' if r['name'] == 'tapada_val' else 'train'} for r in rows]
        with patch.object(s.preparation, 'partition', return_value={'imagenes': rows}), \
             patch.object(s, 'partition_path', return_value='particion'), \
             patch.object(s.preparation, 'digest', return_value='hash'), \
             patch.object(s.preparation, 'read', return_value={'status':'verificada','whatsapp_excluidas':[f'whatsapp_{i}' for i in range(5)]}):
            selected, excluded, excluded_val = s.choose_no_tapadas(Path('.'), {}, images, {'whatsapp_receipt_sha256':'hash'})
        self.assertEqual(selected, ['normal'])
        self.assertEqual(len(excluded), 6)
        self.assertEqual(excluded_val, ['tapada_val'])

if __name__ == '__main__': unittest.main()
