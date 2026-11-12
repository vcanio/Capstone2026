"""La galería muestra solo train seleccionado y valida las imágenes servidas."""
import json,re,unittest
from pathlib import Path
from PIL import Image
import galeria_seleccion_v3 as gallery
import preparacion_v3 as prep
import selecciones_v3 as selections
import test_selecciones_v3 as selection_tests


class GalleryTests(unittest.TestCase):
    def setUp(self):
        selection_tests.SelectionTests.setUp(self)
        source=self.root/self.source
        for i in self.images:
            i.update(eligible=True,grupo_escena=i['familia'])
            path=source/'images'/('train' if i['split']=='train' else 'val_real')/i['name']
            path.parent.mkdir(parents=True,exist_ok=True);Image.new('RGB',(100,100)).save(path)
            i['sha256']=prep.digest(path)
        receipt={**self.receipt,'reviewed':True,'reviewed_visible_regions':True,'policy_version':prep.PREPARATION_POLICY,
                 'included':[{k:i[k] for k in ['name','split','sha256']} for i in self.images]}
        prep.write(source/'manifest.json',receipt)
        prep.write(source.parent/'informe.json',{'images':self.images})
        path=selections.path_for(self.root,self.identifier)
        record=prep.read(path);record['source_manifest_sha256']=prep.digest(source/'manifest.json');prep.write(path,record)

    def test_page_contains_only_selected_training_photos(self):
        html=gallery.page(self.root,self.identifier).decode()
        data=json.loads(re.search(r'<script id="gallery-data" type="application/json">(.*?)</script>',html,re.S)[1])
        self.assertEqual([p['name'] for p in data['photos']],['family_0_original.jpg','family_A_vacios.png'])
        self.assertNotIn('val.jpg',html);self.assertNotIn('family_B_baja.png',html)

    def test_excluded_validation_unknown_and_traversal_are_rejected(self):
        for name in ['family_B_baja.png','val.jpg','missing.jpg','../manifest.json']:
            with self.subTest(name=name),self.assertRaises(ValueError):gallery.image_path(self.root,self.identifier,name)
        self.assertTrue(gallery.image_path(self.root,self.identifier,'family_A_vacios.png').is_file())

    def test_changed_photo_or_invalid_selection_cannot_be_served(self):
        path=gallery.image_path(self.root,self.identifier,'family_A_vacios.png');path.write_bytes(b'changed')
        with self.assertRaises(ValueError):gallery.image_path(self.root,self.identifier,path.name)
        with self.assertRaises(ValueError):gallery.page(self.root,'../private')
