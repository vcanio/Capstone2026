"""Pruebas unitarias y de regresión del prototipo Línea A y su visor sandbox."""
import base64
from http.server import ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Ocupacion'))

from evaluar_linea_base import LABELS_PATH, MANIFEST_PATH, load_rgb, rasterize_polygon  # noqa: E402
from prototipo_linea_a import (  # noqa: E402
    CALIBRATED_THRESHOLD_PCT,
    analyze_gondola_rgb,
    gondola_feature_bounds,
    longest_empty_run_pct,
    score_level_from_features,
)
from visor_linea_a import LineaASandboxEngine, SandboxHandler, build_sample_catalog  # noqa: E402


def _synthetic_feature(
    shape=(10, 40),
    density=0.0,
    gradient=2.0,
    color=0.0,
    deviation=1.0,
):
    h, w = shape
    return {
        'valid': True,
        'valid_cells': h * w,
        'usable': np.ones(shape, dtype=bool),
        'observed_coverage': np.ones(shape, dtype=np.float32),
        'density': np.full(shape, density, dtype=np.float32),
        'gradient': np.full(shape, gradient, dtype=np.float32),
        'color_density': np.full(shape, color, dtype=np.float32),
        'deviation': np.full(shape, deviation, dtype=np.float32),
    }


class TestPrototipoLineaA(unittest.TestCase):
    def test_longest_empty_run_bridges_single_noise_column(self):
        arr = np.array([True] * 4 + [False] * 5 + [True] + [False] * 4 + [True] * 6)
        # Puenteando la columna aislada, el tramo vacío continuo mide 10 / 20 = 50 %
        self.assertAlmostEqual(longest_empty_run_pct(arr, bridge_single=True), 50.0, places=2)
        self.assertAlmostEqual(longest_empty_run_pct(arr, bridge_single=False), 25.0, places=2)

    def test_full_stocked_vs_uniform_stocked_vs_empty(self):
        stocked = _synthetic_feature(density=0.07, gradient=42.0, color=0.45, deviation=20.0)
        uniform_bright = _synthetic_feature(density=0.025, gradient=26.0, color=0.40, deviation=14.0)
        empty = _synthetic_feature(density=0.001, gradient=3.0, color=0.0, deviation=1.5)

        bounds = gondola_feature_bounds([stocked, uniform_bright, empty])
        r_stocked = score_level_from_features(stocked, bounds)
        r_uniform = score_level_from_features(uniform_bright, bounds)
        r_empty = score_level_from_features(empty, bounds)

        self.assertEqual(r_stocked['state'], 'suficiente')
        self.assertGreaterEqual(r_stocked['pct'], 80.0)
        # Normalización anclada con pisos físicos evita restar envases uniformes como fondo.
        self.assertEqual(r_uniform['state'], 'suficiente')
        self.assertGreaterEqual(r_uniform['pct'], 70.0)
        self.assertEqual(r_empty['state'], 'reponer')
        self.assertLess(r_empty['pct'], 15.0)

    def test_empty_gondola_floor_prevents_noise_stretch(self):
        empty = _synthetic_feature(density=0.001, gradient=3.0, color=0.0, deviation=1.5)
        res = score_level_from_features(empty, gondola_feature_bounds([empty]))
        self.assertEqual(res['state'], 'reponer')
        self.assertLess(res['pct'], 15.0)

    def test_half_shelf_gap_triggers_reponer(self):
        feat = _synthetic_feature(density=0.07, gradient=42.0, color=0.45, deviation=20.0)
        # 50 % derecha completamente vacía
        feat['density'][:, 20:] = 0.0
        feat['gradient'][:, 20:] = 3.0
        feat['color_density'][:, 20:] = 0.0
        feat['deviation'][:, 20:] = 1.5
        res = score_level_from_features(feat, gondola_feature_bounds([feat]))
        self.assertAlmostEqual(res['max_gap_pct'], 50.0, delta=3.0)
        self.assertEqual(res['state'], 'reponer')
        self.assertLess(res['pct'], CALIBRATED_THRESHOLD_PCT)

    def test_thin_bottom_rail_does_not_inflate_coverage(self):
        # Reproduce la falla 020_A_vacios N2: franja fina horizontal en el riel inferior sin producto arriba.
        feat = _synthetic_feature(shape=(10, 40), density=0.001, gradient=4.0, color=0.0, deviation=2.0)
        feat['density'][9, :] = 0.08
        feat['gradient'][9, :] = 50.0
        feat['deviation'][9, :] = 22.0
        res = score_level_from_features(feat, gondola_feature_bounds([feat]))
        self.assertEqual(res['state'], 'reponer')
        self.assertLess(res['pct'], 25.0)

    def test_low_upper_banner_is_reponer_not_trapped_in_revisar(self):
        # Cartel pequeño superior sobre nivel vacío (< umbral): debe ir a reponer, no quedarse atrapado en revisar.
        feat = _synthetic_feature(shape=(10, 40), density=0.0, gradient=2.0, color=0.0, deviation=1.0)
        feat['density'][0:2, :12] = 0.08
        feat['gradient'][0:2, :12] = 50.0
        feat['deviation'][0:2, :12] = 22.0
        res = score_level_from_features(feat, gondola_feature_bounds([feat]))
        self.assertEqual(res['state'], 'reponer')

    def test_hollow_banner_over_empty_midband_abstains_to_revisar(self):
        # Reproduce la geometría de 024_D N5: franja de cartel en 30-55%, aire vacío en 60-78% y riel en 80-95%.
        feat = _synthetic_feature(shape=(10, 40), density=0.001, gradient=4.0, color=0.0, deviation=2.0)
        for rows in (slice(3, 6), slice(8, 10)):
            feat['density'][rows, :] = 0.08
            feat['gradient'][rows, :] = 55.0
            feat['color_density'][rows, :] = 0.6
            feat['deviation'][rows, :] = 25.0
        res = score_level_from_features(feat, gondola_feature_bounds([feat]))
        self.assertGreaterEqual(res['pct'], CALIBRATED_THRESHOLD_PCT)
        self.assertTrue(res['hollow_banner'])
        self.assertEqual(res['state'], 'revisar')
        self.assertEqual(res['signal_pattern'], 'hollow_banner')

    def test_real_regression_samples_end_to_end_rgb(self):
        if not MANIFEST_PATH.is_file():
            self.skipTest('Integración: requiere la muestra privada de ocupación.')
        manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))['images']
        by_name = {r['name']: r for r in manifest}

        # 1. Estante lleno uniforme (antes daba falso positivo en 21.95 %) -> Suficiente
        rec_full = by_name['lider_2_122_0_original.jpg']
        rgb_full = load_rgb(rec_full)
        h, w = rgb_full.shape[:2]
        masks_full = [rasterize_polygon(lv['polygon'], w, h) for lv in rec_full['levels']]
        out_full = analyze_gondola_rgb(rgb_full, masks_full)
        self.assertEqual(out_full[5]['state'], 'suficiente')  # N6
        self.assertGreaterEqual(out_full[5]['pct'], 75.0)

        # 2. Nivel vacío con riel inferior (antes daba falso Suficiente en 79.41 %) -> Reponer
        rec_rail = by_name['lider_express_020_A_vacios.png']
        rgb_rail = load_rgb(rec_rail)
        hr, wr = rgb_rail.shape[:2]
        masks_rail = [rasterize_polygon(lv['polygon'], wr, hr) for lv in rec_rail['levels']]
        out_rail = analyze_gondola_rgb(rgb_rail, masks_rail)
        self.assertEqual(out_rail[1]['state'], 'reponer')  # N2
        self.assertLess(out_rail[1]['pct'], 35.0)

        # 3. Llamada de nivel único aislado también funciona sin fallar
        single = analyze_gondola_rgb(rgb_full, [masks_full[5]])
        self.assertEqual(len(single), 1)
        self.assertEqual(single[0]['state'], 'suficiente')


class _DummyResult:
    boxes = None
    masks = None
    names = {0: 'Nivel'}


class TestVisorLineaASandbox(unittest.TestCase):
    def test_sample_catalog_never_exposes_unlabeled_blind_or_test_items(self):
        if not MANIFEST_PATH.is_file():
            self.skipTest('Integración: requiere la muestra privada de ocupación.')
        cat = build_sample_catalog()
        manifest_imgs = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))['images']
        saved_items = json.loads(LABELS_PATH.read_text(encoding='utf-8')).get('items', {}) if LABELS_PATH.is_file() else {}
        unlabeled_names = set()
        unlabeled_stems = set()
        for rec in manifest_imgs:
            if len(saved_items.get(rec['item_key'], {}).get('levels', {})) != rec['level_count']:
                unlabeled_names.add(rec['name'])
                stem = Path(rec['name']).stem.split('__')[-1].split('_original')[0]
                if stem:
                    unlabeled_stems.add(stem)

        for sample in cat['samples']:
            path = Path(cat['by_id'][sample['id']]['path'])
            self.assertNotIn('\\test\\', str(path).lower())
            self.assertNotIn('/test/', path.as_posix().lower())
            self.assertNotIn(sample['filename'], unlabeled_names)
            for st in unlabeled_stems:
                self.assertNotIn(st, path.stem, f'Fuga de muestra ciega pendiente en visor: {sample["filename"]}')

    def test_render_evidence_image_handles_bounds_safely(self):
        img = Image.new('RGB', (160, 120), color=(20, 30, 40))
        rgb = np.zeros((120, 160, 3), dtype=np.uint8)
        structures = np.zeros((120, 160), dtype=bool)
        feat = _synthetic_feature(shape=(8, 12), density=0.07, gradient=42.0, color=0.45, deviation=20.0)
        feat['bounds'] = (10, 10, 140, 80)
        bounds = gondola_feature_bounds([feat])
        rendered = LineaASandboxEngine._render_evidence_image(
            img, rgb, structures, [feat], bounds, [], _DummyResult()
        )
        self.assertEqual(rendered.size, (160, 120))

    def test_http_sandbox_endpoints_and_origin_guards(self):
        class StubEngine:
            def analyze_bytes(self, raw_bytes, confidence=0.60, threshold_pct=CALIBRATED_THRESHOLD_PCT):
                return {
                    'ok': True,
                    'width': 64,
                    'height': 48,
                    'device': 'CPU',
                    'model_name': 'stub',
                    'elapsed_ms': 1.2,
                    'confidence': confidence,
                    'threshold_pct': threshold_pct,
                    'level_count': 1,
                    'changed_levels': 0,
                    'gondola_baseline': 'suficiente',
                    'gondola_linea_a': 'suficiente',
                    'levels': [],
                    'images': {
                        'original': 'data:image/jpeg;base64,AA==',
                        'baseline': 'data:image/jpeg;base64,AA==',
                        'linea_a': 'data:image/jpeg;base64,AA==',
                        'evidence': 'data:image/jpeg;base64,AA==',
                    },
                }

        server = ThreadingHTTPServer(('127.0.0.1', 0), SandboxHandler)
        server.engine = StubEngine()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_port
            base = f'http://127.0.0.1:{port}'

            with urlopen(f'{base}/') as resp:
                self.assertEqual(resp.status, 200)
                html = resp.read().decode('utf-8')
                self.assertIn('/api/analyze', html)

            with urlopen(f'{base}/api/samples') as resp:
                data = json.loads(resp.read().decode('utf-8'))
                self.assertEqual(data['default_threshold_pct'], CALIBRATED_THRESHOLD_PCT)
                self.assertIn('categories', data)
                self.assertIsInstance(data['samples'], list)

            buf = BytesIO()
            Image.new('RGB', (32, 24), color=(120, 80, 40)).save(buf, format='JPEG')
            b64 = base64.b64encode(buf.getvalue()).decode('ascii')
            req = Request(
                f'{base}/api/analyze',
                data=json.dumps({'image_base64': b64, 'filename': 'demo.jpg', 'threshold_pct': 50}).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'Origin': base},
                method='POST',
            )
            with urlopen(req) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                self.assertTrue(res['ok'])
                self.assertEqual(res['threshold_pct'], 50.0)
                self.assertEqual(res['title'], 'demo.jpg')

            # Petición cross-origin debe rechazarse con 403
            bad_req = Request(
                f'{base}/api/analyze',
                data=b'{}',
                headers={'Content-Type': 'application/json', 'Origin': 'http://evil.example'},
                method='POST',
            )
            with self.assertRaises(HTTPError) as ctx:
                urlopen(bad_req)
            self.assertEqual(ctx.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()
