"""Versiones de reparto: traslados autorizados, historia y reserva independientes."""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import preparacion_v3 as prep
import selecciones_v3 as selections
from test_selecciones_v3 import SelectionTests

ROOT = Path(__file__).resolve().parents[3]
REFERENCE = 'Datos/Registros/Particiones/v3_458_refuerzo_papeles_20261025/particion.json'


class VersionedPartitionTests(unittest.TestCase):
    def setUp(self):
        if not (ROOT / REFERENCE).is_file():
            self.skipTest('Requiere la partición histórica local, fuera del clon público.')
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for relative in (prep.PARTITION, REFERENCE, 'Datos/Registros/CVAT/criterio_v3.json',
                         'Datos/Registros/Particiones/v3_458_20261023/grupos_escena.json',
                         'Datos/Registros/Particiones/v3_458_20261023/lider2_grupos.json'):
            target = self.root / relative; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.value = prep.read(self.root / REFERENCE)

    def test_active_pointer_preserves_explicit_historical_partition_and_test(self):
        prep.write(self.root / prep.ACTIVE_PARTITION,
                   {'path': REFERENCE, 'sha256': prep.digest(self.root / REFERENCE)})
        active = prep.partition(self.root)
        historic = prep.partition(self.root, prep.PARTITION)
        self.assertEqual(active['resumen']['train']['imagenes'], 320)
        self.assertEqual(historic['resumen']['train']['imagenes'], 327)
        self.assertEqual([i for i in active['imagenes'] if i['split'] == 'test'],
                         [i for i in historic['imagenes'] if i['split'] == 'test'])
        self.assertTrue(set(active['hard_examples']) <= {i['name'] for i in active['imagenes'] if i['split'] == 'train'})

    def test_rejects_geometry_edits_test_moves_unrecorded_moves_and_missing_authorization(self):
        cases = []
        v = copy.deepcopy(self.value); v['imagenes'][0]['width'] += 1; cases.append(v)
        v = copy.deepcopy(self.value); v['authorization'] = {}; cases.append(v)
        v = copy.deepcopy(self.value); v['moved_val_to_train'].append('l2_g05'); cases.append(v)
        v = copy.deepcopy(self.value); v['moved_train_to_val'] = []; cases.append(v)
        v = copy.deepcopy(self.value); v['hard_examples'].append('unknown.jpg'); cases.append(v)
        v = copy.deepcopy(self.value); v['resumen']['val']['reales'] += 1; cases.append(v)
        for value in cases:
            prep.write(self.root / REFERENCE, value)
            with self.assertRaises(ValueError): prep.partition(self.root, REFERENCE)

    def test_rejects_unsafe_reference_and_changed_active_hash(self):
        for ref in ('../private', '/outside/particion.json', True):
            with self.assertRaises(ValueError): prep.partition_reference(self.root, ref)
        prep.write(self.root / prep.ACTIVE_PARTITION, {'path': REFERENCE, 'sha256': 'changed'})
        with self.assertRaises(ValueError): prep.partition(self.root)


class HardSelectionTests(unittest.TestCase):
    def setUp(self):
        SelectionTests.setUp(self)

    def test_adds_only_authorized_train_exceptions_retains_validation_and_checks_coverage(self):
        with patch.object(prep, 'partition', return_value={'hard_examples': ['family_B_baja.png']}):
            selections.create(self.root, self.source, self.receipt, self.images,
                              identifier='hard', author='Vicente', authorization='Explícita',
                              hard_examples=['family_B_baja.png'])
            rows, record = selections.apply(self.root, self.source, self.images, 'hard')
            self.assertEqual(record['development_counts']['train'], 3)
            self.assertEqual([r for r in rows if r['split'] == 'val'],
                             [r for r in self.images if r['split'] == 'val'])
            with self.assertRaises(ValueError):
                selections.apply(self.root, self.source, self.images[1:], 'hard')
        with patch.object(prep, 'partition', return_value={'hard_examples': ['val.jpg']}):
            with self.assertRaises(ValueError):
                selections.create(self.root, self.source, self.receipt, self.images,
                                  identifier='bad', author='Vicente', authorization='Explícita', hard_examples=['val.jpg'])
