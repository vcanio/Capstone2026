"""La reorganización conserva referencias históricas sin exponer la reserva."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import datos_modelos as datasets
import panel_modelos as panel
from rutas_datos import current_image_path, current_inventory_path


class ImagePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_prefixes_preserve_filenames_and_leave_unrelated_paths_alone(self):
        self.assertEqual(current_inventory_path('Imagenes/01.jpg'), 'V1/Lider/lider_001.jpg')
        self.assertEqual(current_image_path('Datos/Equilibrado_v1_20261013/reales/REAL_01.jpg'),
                         'Datos/V1/Lider/lider_001.jpg')
        for path in ('Datos/Imagenes_extra/01.jpg', 'Laboratorio/Experimentos/run/prediccion.jpg', None):
            self.assertEqual(current_image_path(path), path)

    def test_old_image_link_resolves_but_reserve_and_unknown_files_do_not(self):
        expected = self.root / 'Datos/V1/Lider/lider_001.jpg'
        with patch.object(panel, 'ROOT', self.root), \
             patch.object(panel, 'inventory', return_value=[{'archivo': 'V1/Lider/lider_001.jpg'}]), \
             patch.object(datasets, 'package_inventory', return_value={}):
            self.assertEqual(panel.allowed_file('Datos/Imagenes/01.jpg'), expected)
            self.assertIsNone(panel.allowed_file('Datos/Imagenes/14.jpg'))
            self.assertIsNone(panel.allowed_file('Datos/Evaluacion_final/Reservadas/14.jpg'))
            self.assertIsNone(panel.allowed_file('Datos/Imagenes/../../private.json'))

    def test_historical_upload_metadata_is_read_from_new_folder(self):
        iid = 'a' * 32
        previous = f'Datos/Fotos_prueba/{iid}/imagen.jpg'
        current = f'Laboratorio/Experimentos/panel_pruebas/Subidas_panel/{iid}/imagen.jpg'
        image = self.root / current
        image.parent.mkdir(parents=True)
        image.write_bytes(b'fixture')
        image.with_name('foto.json').write_text(json.dumps({'id': previous, 'name': 'mi_foto.jpg'}))
        with patch.object(panel, 'ROOT', self.root):
            self.assertEqual(panel.uploaded_photo(previous)['id'], current)
            self.assertEqual(panel.allowed_file(previous), image)
            self.assertIsNone(panel.uploaded_photo(current.replace('/imagen.jpg', '/../imagen.jpg')))

    def test_initial_lider_names_keep_legacy_links_and_express(self):
        self.assertEqual(current_image_path('Datos/Para_anotar/Originales/03.jpg'),
                         'Datos/V1/Lider/lider_003.jpg')
        self.assertEqual(current_image_path('Datos/Evaluacion_final/Reservadas/14.jpg'),
                         'Datos/V1/Reservadas/lider_014.jpg')
        for path in ('Datos/V1/Lider/lider_003.jpg',
                     'Datos/V2/lider_express_20261016/imagenes/lider_express_003.jpg'):
            self.assertEqual(current_image_path(path), path)

    def test_review_of_saved_version_resolves_old_registered_package_path(self):
        previous = 'Equilibrado_v1_20261013/reales/REAL_01.jpg'
        current = 'V1/Lider/lider_001.jpg'
        with patch.object(datasets, 'ROOT', self.root):
            self.assertEqual(datasets.safe_image_path({'archivo': previous}, {'REAL_01': {'archivo': current}}),
                             self.root / 'Datos' / current)
            with self.assertRaises(ValueError):
                datasets.safe_image_path({'archivo': '../private.json'}, {})

    def test_previous_real_and_synthetic_copies_resolve_to_canonical_files(self):
        for split in ('entrenamiento', 'validacion'):
            previous = f'Datos/Para_anotar/Equilibrado_v1_20261013/reales/{split}/REAL_03.jpg'
            self.assertEqual(current_image_path(previous), 'Datos/V1/Lider/lider_003.jpg')
        self.assertEqual(current_image_path('Datos/Equilibrado_v1_20261013/sinteticas/entrenamiento/EQ_01_V1.png'),
                         'Datos/V1/Sinteticas/EQ_01_V1.png')


if __name__ == '__main__':
    unittest.main()
