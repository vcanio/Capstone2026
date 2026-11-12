import math
import importlib.util
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from visibilidad_foto import calibrate, decision, full_frame, source_path
from revision_visibilidad_cvat import collect
from entrenamiento_visibilidad import split_groups


class VisibilidadFotoTests(unittest.TestCase):
    def test_preprocesado_conserva_extremos_de_foto_vertical(self):
        image = Image.new('RGB', (100, 200), 'black')
        for x in range(100):
            for y in range(10):
                image.putpixel((x, y), (255, 0, 0))
                image.putpixel((x, 199-y), (0, 255, 0))
        result = full_frame(image)
        self.assertEqual(result.size, (640, 640))
        self.assertEqual(result.getpixel((320, 10)), (255, 0, 0))
        self.assertEqual(result.getpixel((320, 630)), (0, 255, 0))
        self.assertEqual(result.getpixel((0, 320)), (114, 114, 114))

    def test_entrenamiento_e_inferencia_comparten_preprocesado(self):
        app_path = Path(__file__).resolve().parents[3] / 'Aplicacion/visibilidad_experimental.py'
        spec = importlib.util.spec_from_file_location('visibility_app_preflight', app_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        image = Image.new('RGBA', (170, 91), (255, 0, 0, 64))
        self.assertEqual(full_frame(image).tobytes(), module.full_frame(image).tobytes())

    def test_decision_fronteras_y_no_finitos(self):
        self.assertEqual(decision(.499, .7), 'no_apta')
        self.assertEqual(decision(.5, .7), 'dudosa')
        self.assertEqual(decision(.7, .7), 'apta')
        for score in (math.nan, math.inf, -.01, 1.01):
            with self.assertRaises(ValueError):
                decision(score, .7)

    def test_calibracion_minima_sin_falsas_aceptaciones(self):
        self.assertEqual(calibrate([('apta', .9)] * 4 + [('apta', .7), ('no_apta', .7)]), .71)
        self.assertIsNone(calibrate([('apta', .7), ('no_apta', .8)]))
        with self.assertRaises(ValueError):
            calibrate([('apta', .9)])

    def test_ruta_historica_usa_fuente_v3_y_rechaza_fuera_de_datos(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual = root / 'Datos/V3/visibilidad_limitada_20261019/imagenes/foto.png'
            actual.parent.mkdir(parents=True)
            actual.write_bytes(b'imagen')
            with patch('visibilidad_foto.ROOT', root):
                self.assertEqual(source_path({'path': 'Datos/V2/visibilidad_limitada_20261019/imagenes/foto.png'}), actual.resolve())
                with self.assertRaises(ValueError):
                    source_path({'path': '../fuera.png'})

    def test_revision_sin_etiqueta_y_duplicados_no_se_aprueban(self):
        images = [{'name': f'foto_{n}', 'cvat_name': f'foto_{n}',
                   'split': 'train' if n < 336 else 'val', 'origen': 'real',
                   'etiqueta': 'pendiente'} for n in range(405)]
        train = {f'foto_{n}': n for n in range(336)}
        val = {f'foto_{n}': n-336 for n in range(336, 405)}
        receipt = {'status': 'lista_para_revision', 'inventory_sha256': 'abc', 'project_id': 12,
                   'tasks': [{'split': 'train', 'task_id': 37, 'status': 'verificada', 'frames': train},
                             {'split': 'val', 'task_id': 38, 'status': 'verificada', 'frames': val}]}
        tag = {'label_id': 1, 'frame': 0, 'attributes': [{'spec_id': 10, 'value': 'apta'},
                                                        {'spec_id': 11, 'value': 'sin_definir'}]}

        class Reader:
            def listing(self, route):
                return [{'name': 'Evaluabilidad', 'type': 'tag', 'id': 1,
                         'attributes': [{'id': 10, 'name': 'decision'}, {'id': 11, 'name': 'motivo'}]}]

            def request(self, route):
                frames = train if '/37/' in route else val
                if route.endswith('/data/meta'):
                    return {'frames': [{'name': name} for name in frames], 'deleted_frames': []}
                return {'tags': [tag, tag] if '/37/' in route else [], 'shapes': [], 'tracks': []}

        with patch('revision_visibilidad_cvat.digest', return_value='abc'), \
             patch('revision_visibilidad_cvat.PROPOSALS', Path('__test_no_proposals__.json')), \
             patch('revision_visibilidad_cvat.SECOND_PROPOSALS', Path('__test_no_second_proposals__.json')):
            result = collect(Reader(), {'images': images}, receipt)
        self.assertEqual(len(result['images']), 405)
        self.assertTrue(all(row['etiqueta'] == 'pendiente' for row in result['images']))
        self.assertEqual(result['issues'][0]['reason'], 'multiples_decisiones')

    def test_particion_interna_es_determinista_y_no_separa_escenas(self):
        rows = [{'grupo_escena': f'g{n}', 'etiqueta': label}
                for n in range(10) for label in ('apta', 'no_apta')]
        fit, cal = split_groups(rows)
        self.assertEqual((fit, cal), split_groups(rows))
        self.assertFalse({r['grupo_escena'] for r in fit} & {r['grupo_escena'] for r in cal})
        self.assertEqual({r['etiqueta'] for r in fit}, {'apta', 'no_apta'})
        self.assertEqual({r['etiqueta'] for r in cal}, {'apta', 'no_apta'})

    def test_particion_rechaza_clase_ausente(self):
        with self.assertRaises(ValueError):
            split_groups([{'grupo_escena': f'g{n}', 'etiqueta': 'apta'} for n in range(10)])


if __name__ == '__main__':
    unittest.main()
