"""Afinado: pesos propios íntegros, repaso y nuevas fotos fuera de validación/test."""
from pathlib import Path
import copy,shutil,tempfile,unittest
import preparacion_v3 as prep
import entrenamiento_v3 as training
import selecciones_v3 as selections
from test_particiones_versionadas_v3 import VersionedPartitionTests

ROOT=Path(__file__).resolve().parents[3]
EXTENDED='Datos/Registros/Particiones/v3_469_afinado_20261025/particion.json'


class InitialModelTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.relative='Experimentos/parent/entrenamiento/weights/best.pt'
        self.path=self.root/self.relative;self.path.parent.mkdir(parents=True);self.path.write_bytes(b'local fixture')
        self.run=self.path.parents[2]
        prep.write(self.run/'manifest.json',{'criterion':{'version':training.CRITERION},'clases':['Nivel']})
        prep.write(self.run/'metricas_geometria_v3.json',{'criterion':training.CRITERION,'test_used':False})

    def test_completed_one_class_parent_is_fingerprinted_and_later_changes_rejected(self):
        info=training.initial_model(self.root,self.relative)
        self.assertEqual(info['kind'],'fine_tune');self.assertFalse(info['resume'])
        config={'model':self.relative,'initial_model':info}
        training.verify_initial_model(self.root,config)
        self.path.write_bytes(b'changed')
        with self.assertRaises(ValueError):training.verify_initial_model(self.root,config)

    def test_rejects_arbitrary_paths_last_v2_unfinished_or_test_used(self):
        for relative in ('../private.pt','Experimentos/parent/../parent/entrenamiento/weights/best.pt',
                         self.relative.replace('best.pt','last.pt'),[],None):
            with self.subTest(relative=relative),self.assertRaises(ValueError):training.initial_model(self.root,relative)
        manifest=prep.read(self.run/'manifest.json')
        for change in ({'clases':['Nivel_reponer']},{'preparing':True},{'criterion':{'version':'v2'}}):
            prep.write(self.run/'manifest.json',{**manifest,**change})
            with self.assertRaises(ValueError):training.initial_model(self.root,self.relative)
        prep.write(self.run/'manifest.json',manifest)
        prep.write(self.run/'metricas_geometria_v3.json',{'criterion':training.CRITERION,'test_used':True})
        with self.assertRaises(ValueError):training.initial_model(self.root,self.relative)


class FineSamplerTests(unittest.TestCase):
    def fixture(self):
        def row(name,family,group,origin='real',split='train'):
            return dict(name=name,familia=family,grupo_escena=group,origen=origin,split=split)
        rows=[row('f_0_original.jpg','f','g1'),row('f_A_vacios.png','f','g1','sintetica'),
              row('g.jpg','g','g2'),row('g_A_vacios.png','g','g2','sintetica'),
              row('f_D_superior_vacio.png','f','g1','sintetica'),row('new.jpg','new','g3'),
              row('val.jpg','v','g4',split='val'),row('test.jpg','t','g5',split='test')]
        return rows,[r['name'] for r in rows[:4]],['f_D_superior_vacio.png','new.jpg']

    def test_preserves_original_pairs_scene_coverage_and_holdouts(self):
        rows,base,targets=self.fixture()
        names,replay=selections.choose_fine(rows,base,targets,3)
        self.assertEqual(len(names),5);self.assertEqual(len(replay),3)
        self.assertIn('f_0_original.jpg',replay);self.assertIn('g.jpg',replay)
        self.assertTrue(set(targets)<=set(names))
        self.assertNotIn('val.jpg',names);self.assertNotIn('test.jpg',names)
        self.assertEqual(selections.choose_fine(rows,base,targets,3),(names,replay))

    def test_rejects_holdout_targets_missing_pairs_and_too_small_replay(self):
        rows,base,targets=self.fixture()
        for invalid in (targets+['val.jpg'],targets+['test.jpg'],targets+[targets[0]]):
            with self.assertRaises(ValueError):selections.choose_fine(rows,base,invalid,3)
        with self.assertRaises(ValueError):selections.choose_fine(rows,base[1:],targets,3)
        with self.assertRaises(ValueError):selections.choose_fine(rows,base,targets,1)


class ExtendedPartitionTests(unittest.TestCase):
    def setUp(self):
        VersionedPartitionTests.setUp(self)
        for rel in (EXTENDED,'Datos/V3/Refuerzo/papeles_20261025/manifest.json'):
            target=self.root/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,target)

    def test_preserves_63_test_and_adds_only_registered_11_and_moves_eggs(self):
        part=prep.partition(self.root,EXTENDED)
        base=prep.partition(self.root,part['base_partition_path'])
        self.assertEqual(len(part['imagenes']),469)
        self.assertEqual(part['resumen']['val']['imagenes'],69)
        self.assertEqual([r for r in part['imagenes'] if r['split']=='test'],[r for r in base['imagenes'] if r['split']=='test'])
        self.assertEqual(sum(r['task_id']==31 and r['split']=='train' for r in part['imagenes']),11)
        self.assertEqual(sum(r['grupo_escena']=='l2_g17' and r['split']=='train' for r in part['imagenes']),6)

    def test_rejects_new_photo_changes_unauthorized_moves_and_cycles(self):
        original=prep.read(self.root/EXTENDED)
        changes=[]
        v=copy.deepcopy(original);v['imagenes'][-1]['width']+=1;changes.append(v)
        v=copy.deepcopy(original);v['moved_val_to_train'].append('l2_g18');changes.append(v)
        v=copy.deepcopy(original);v['base_partition_path']=EXTENDED;changes.append(v)
        v=copy.deepcopy(original);v['imagenes'][0]['name']='changed.jpg';changes.append(v)
        for v in changes:
            prep.write(self.root/EXTENDED,v)
            with self.assertRaises(ValueError):prep.partition(self.root,EXTENDED)
