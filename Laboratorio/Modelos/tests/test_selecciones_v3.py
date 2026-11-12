"""Selección sin fugas, revisión heredada, integridad y copia real del ensayo."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import entrenamiento_v3 as training
import preparacion_v3 as prep
import selecciones_v3 as selection


class SelectionTests(unittest.TestCase):
    def test_exclusion_obstrucciones_conserva_validacion_y_verifica_huellas(self):
        base = self.root / 'Datos/Preparados/V3/Visibilidad_foto_20261102'
        base.mkdir(parents=True)
        blocked = [{'name': f'tapada_{n}.png', 'split': 'train', 'sha256': f'hash_{n}'} for n in range(41)]
        whatsapp = [f'WhatsApp Image {n}.jpg' for n in range(5)]
        obstacle = base / 'propuesta_seleccion_segmentacion_sin_obstruccion.json'
        decision = base / 'decision_vicente_segundo_lote_20261102.json'
        prep.write(obstacle, {'schema': 'propuesta_exclusion_segmentacion_v1', 'selection': blocked})
        prep.write(decision, {'status': 'verificada', 'whatsapp_excluidas': whatsapp})
        value = {'obstacle_manifest_sha256': prep.digest(obstacle), 'whatsapp_receipt_sha256': prep.digest(decision)}
        images = [dict(x) for x in blocked] + [{'name': x, 'split': 'train', 'sha256': 'w'} for x in whatsapp]
        images += [{'name': 'limpia.jpg', 'split': 'train', 'sha256': 'ok'}, {'name': 'validacion.jpg', 'split': 'val'}]
        selected, excluded = selection.choose_without_obstructions(self.root, images, value)
        self.assertEqual(selected, ['limpia.jpg'])
        self.assertEqual(len(excluded), 46)
        self.assertNotIn('validacion.jpg', excluded)
        images[0]['sha256'] = 'otro'
        with self.assertRaises(ValueError):
            selection.choose_without_obstructions(self.root, images, value)

    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.source='Datos/Preparados/V3/v3_20261025_000000_12345678/exportacion_12345678'
        self.receipt={'author':'Vicente','counts':{'train':3,'val_real':1,'val_sintetica':1,'test_real':1}}
        path=self.root/self.source;path.mkdir(parents=True)
        prep.write(path/'manifest.json',self.receipt)
        partition=self.root/prep.PARTITION;partition.parent.mkdir(parents=True);prep.write(partition,{'unchanged':True})
        self.images=[{'name':name,'familia':family,'origen':origin,'split':split,'shapes':[],
            'width':100,'height':100} for name,family,origin,split in [
            ('family_0_original.jpg','family','real','train'),('family_A_vacios.png','family','sintetica','train'),
            ('family_B_baja.png','family','sintetica','train'),('val.jpg','val','real','val'),
            ('val_A_vacios.png','val','sintetica','val')]]
        self.identifier='fixture_selection'
        selection.create(self.root,self.source,self.receipt,self.images,identifier=self.identifier,
                         author='Vicente',authorization='Petición explícita de prueba')

    def test_keeps_real_and_empty_preserves_all_validation_and_does_not_read_test(self):
        images,record=selection.apply(self.root,self.source,self.images,self.identifier)
        self.assertEqual([i['name'] for i in images],['family_0_original.jpg','family_A_vacios.png','val.jpg','val_A_vacios.png'])
        self.assertEqual(record['excluded_train'],['family_B_baja.png'])
        self.assertEqual(record['development_counts'],{'train':2,'val_real':1,'val_sintetica':1})
        self.assertEqual(selection.apply(self.root,self.source,self.images,None),(self.images,None))

    def test_rejects_reassignment_additions_missing_empty_unapproved_and_changed_hashes(self):
        path=selection.path_for(self.root,self.identifier);original=path.read_bytes()
        for change in [{'selected_train':['val.jpg']},{'approved':False},{'source':'other'},
                       {'excluded_train':[]},{'development_counts':{'train':3}}]:
            with self.subTest(change=change):
                value=prep.read(path);value.update(change);prep.write(path,value)
                with self.assertRaises(ValueError):selection.apply(self.root,self.source,self.images,self.identifier)
                path.write_bytes(original)
        for identifier in ['../private','missing',True]:
            with self.assertRaises(ValueError):selection.apply(self.root,self.source,self.images,identifier)
        with self.assertRaises(ValueError):selection.choose([i for i in self.images if '_A_vacios' not in i['name']])
        with self.assertRaises(ValueError):selection.apply(self.root,self.source,self.images,self.identifier,'changed')
        prep.write(self.root/self.source/'manifest.json',{'changed':True})
        with self.assertRaises(ValueError):selection.apply(self.root,self.source,self.images,self.identifier)

    def test_config_and_frozen_dataset_use_only_selected_train_and_retain_source_counts(self):
        from PIL import Image
        source=self.root/self.source
        for name in ['snapshot_cvat.json','particion.json','informe.json']:prep.write(source.parent/name,{})
        for i in self.images:
            split=training.subset(i)
            photo=source/'images'/split/i['name'];photo.parent.mkdir(parents=True,exist_ok=True)
            Image.new('RGB',(100,100)).save(photo);i['sha256']=prep.digest(photo)
            label=source/'labels'/split/(Path(i['name']).stem+'.txt');label.parent.mkdir(parents=True,exist_ok=True);label.write_text('')
        weights=self.root/training.DEFAULTS['model'];weights.parent.mkdir(parents=True);weights.write_bytes(b'fixture')
        with patch.object(training,'validate_export',return_value=(source,self.receipt,self.images)):
            config=training.validate_config(self.root,{**training.DEFAULTS,'source':self.source,'selection':self.identifier})
            run=self.root/'Experimentos'/config['run'];run.parent.mkdir()
            training.freeze_run(self.root,config,run)
        manifest=prep.read(run/'manifest.json')
        self.assertEqual(manifest['counts']['train'],2);self.assertEqual(manifest['source_counts']['train'],3)
        self.assertEqual(len(manifest['imagenes']),4)
        self.assertFalse((run/'dataset_niveles/images/train/family_B_baja.png').exists())
        self.assertFalse(list((run/'dataset_niveles').glob('images/test*')))
        self.assertTrue((source/'images/train/family_B_baja.png').exists())
        training.verify_run(run)
        self.assertEqual(manifest['selection']['sha256'],config['selection_sha256'])
