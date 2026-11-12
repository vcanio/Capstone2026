import io
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image

import sys

HERE = Path(__file__).resolve().parent
CLIENT_DIR = HERE.parent
APP_DIR = CLIENT_DIR.parent / 'Aplicacion'
for p in (str(CLIENT_DIR), str(APP_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app_cliente import ClientHandler, demo_catalog, enrich_for_store, store_diagnosis  # noqa: E402


class FakeClientRunner:
    manifest = {'default_model': 'v3-refuerzo-geometria-revision-20261105'}

    def analyze(self, body, model_id=None, confidence=0.60, method='yolo_paulo_v2'):
        image = Image.open(io.BytesIO(body)).convert('RGB')
        return {
            'image': image.copy(),
            'occupancy_image': image.copy(),
            'edges_image': image.copy(),
            'filtered_edges_image': image.copy(),
            'original_image_url': 'data:image/jpeg;base64,AAA',
            'model': {'id': model_id or self.manifest['default_model'], 'name': 'V3 Oficial'},
            'method': {'id': method, 'name': 'Línea A'},
            'device': 'cpu',
            'confidence': confidence,
            'inference_ms': 14.2,
            'width': image.width,
            'height': image.height,
            'summary': {'levels': 3, 'average_confidence': 0.91},
            'detections': [
                {
                    'id': 1,
                    'level_key': 'n1',
                    'label': 'Nivel 1',
                    'position': 'Superior',
                    'confidence': 0.93,
                    'near_frame': False,
                    'display_polygon': [[10.0, 10.0], [190.0, 10.0], [190.0, 60.0], [10.0, 60.0]],
                    'occupancy': {
                        'pct': 4.5,
                        'state': 'vacio',
                        'fill_pct': 6.0,
                        'max_gap_pct': 92.0,
                        'hyb_body_pct': 3.5,
                        'signal_pattern': 'normal',
                    },
                    'occupancy_estimate': {
                        'pct': 4.5,
                        'state': 'reponer',
                        'label': 'Reponer',
                        'threshold_pct': 52.0,
                    },
                },
                {
                    'id': 2,
                    'level_key': 'n2',
                    'label': 'Nivel 2',
                    'position': 'Intermedio 2',
                    'confidence': 0.91,
                    'near_frame': False,
                    'display_polygon': [[10.0, 70.0], [190.0, 70.0], [190.0, 120.0], [10.0, 120.0]],
                    'occupancy': {
                        'pct': 38.0,
                        'state': 'baja',
                        'fill_pct': 42.0,
                        'max_gap_pct': 58.0,
                        'hyb_body_pct': 34.0,
                        'signal_pattern': 'normal',
                    },
                    'occupancy_estimate': {
                        'pct': 38.0,
                        'state': 'reponer',
                        'label': 'Reponer',
                        'threshold_pct': 52.0,
                    },
                },
                {
                    'id': 3,
                    'level_key': 'n3',
                    'label': 'Nivel 3',
                    'position': 'Inferior',
                    'confidence': 0.89,
                    'near_frame': False,
                    'display_polygon': [[10.0, 130.0], [190.0, 130.0], [190.0, 180.0], [10.0, 180.0]],
                    'occupancy': {
                        'pct': 84.0,
                        'state': 'alta',
                        'fill_pct': 92.0,
                        'max_gap_pct': 8.0,
                        'hyb_body_pct': 76.0,
                        'signal_pattern': 'normal',
                    },
                    'occupancy_estimate': {
                        'pct': 84.0,
                        'state': 'suficiente',
                        'label': 'Suficiente',
                        'threshold_pct': 52.0,
                    },
                },
            ],
        }


class StoreDiagnosisTest(unittest.TestCase):
    def test_empty_shelf_translates_to_clear_store_headline(self):
        det = {
            'near_frame': False,
            'occupancy': {'max_gap_pct': 94.0, 'hyb_body_pct': 4.0, 'fill_pct': 5.0},
            'occupancy_estimate': {'state': 'reponer', 'pct': 5.0},
        }
        diag = store_diagnosis(det)
        self.assertEqual(diag['operational_state'], 'reponer')
        self.assertEqual(diag['operational_label'], 'Alerta por baja disponibilidad')
        self.assertIn('Posible ausencia', diag['headline'])

    def test_wide_gap_describes_an_alert_without_replenishment_instructions(self):
        det = {
            'near_frame': False,
            'occupancy': {'max_gap_pct': 58.0, 'hyb_body_pct': 35.0, 'fill_pct': 42.0},
            'occupancy_estimate': {'state': 'reponer', 'pct': 39.0},
        }
        diag = store_diagnosis(det)
        self.assertEqual(diag['operational_state'], 'reponer')
        self.assertIn('58 %', diag['headline'])
        self.assertIn('confirmar la alerta', diag['action'])
        self.assertNotIn('Reponer', diag['action'])

    def test_sufficient_shelf_translates_to_abastecido(self):
        det = {
            'near_frame': False,
            'occupancy': {'max_gap_pct': 10.0, 'hyb_body_pct': 78.0, 'fill_pct': 90.0},
            'occupancy_estimate': {'state': 'suficiente', 'pct': 85.0},
        }
        diag = store_diagnosis(det)
        self.assertEqual(diag['operational_state'], 'suficiente')
        self.assertEqual(diag['operational_label'], 'Sin alerta visual')
        self.assertIn('90 %', diag['action'])

    def test_near_frame_translates_to_verificar_borde(self):
        det = {
            'near_frame': True,
            'occupancy': {'signal_pattern': 'normal'},
            'occupancy_estimate': {'state': 'revisar', 'pct': None},
        }
        diag = store_diagnosis(det)
        self.assertEqual(diag['operational_state'], 'revisar')
        self.assertEqual(diag['operational_label'], 'No evaluable')
        self.assertIn('borde de la foto', diag['headline'])

    def test_missing_reading_never_becomes_a_sufficient_or_empty_result(self):
        for state in ('reponer', 'suficiente', 'revisar'):
            with self.subTest(state=state):
                diag = store_diagnosis({'occupancy_estimate': {'state': state, 'pct': None}})
                self.assertEqual(diag['operational_state'], 'revisar')
                self.assertEqual(diag['operational_label'], 'No evaluable')

    def test_summary_distinguishes_alerts_review_and_absent_detections(self):
        for detections, expected in (
            ([], 'verificar'),
            ([{'id': 1, 'occupancy_estimate': {'pct': None, 'state': 'suficiente'}}], 'verificar'),
            ([{'id': 1, 'occupancy_estimate': {'pct': 80, 'state': 'suficiente'}}], 'suficiente'),
            ([{'id': 1, 'occupancy_estimate': {'pct': 25, 'state': 'reponer'}},
              {'id': 2, 'occupancy_estimate': {'pct': None, 'state': 'revisar'}}], 'reponer'),
        ):
            with self.subTest(expected=expected, detections=detections):
                result = enrich_for_store({'detections': detections})
                self.assertEqual(result['store_summary']['aisle_state'], expected)

    def test_demo_catalog_never_touches_test_split(self):
        cat = demo_catalog()
        for item_id, rec in cat['by_id'].items():
            norm_path = rec['path'].replace('\\', '/').lower()
            self.assertNotIn('/images/test/', norm_path, f'Demo {item_id} apunta a partición test reservada')


class ClientHttpServerTest(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), ClientHandler)
        self.server.runner = FakeClientRunner()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_root_serves_client_interface_without_ml_audit_controls(self):
        with urlopen(f'{self.base_url}/') as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode('utf-8')
        self.assertIn('Walmart Visión · Visor de alertas', html)
        self.assertIn('Exportar todo (CSV)', html)
        self.assertNotIn('Marcar para revisión', html)
        with urlopen(f'{self.base_url}/logo.svg') as resp:
            self.assertEqual(resp.headers.get_content_type(), 'image/svg+xml')
            self.assertEqual(resp.read(), (CLIENT_DIR / 'logo.svg').read_bytes())

    def test_health_and_demo_catalog_endpoints(self):
        with urlopen(f'{self.base_url}/api/health') as resp:
            self.assertEqual(resp.status, 200)
            payload = json.loads(resp.read().decode('utf-8'))
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['threshold_pct'], 52.0)
        self.assertFalse(payload['analysis_ready'])

        with urlopen(f'{self.base_url}/api/demo-photos') as resp:
            self.assertEqual(resp.status, 200)
            demos = json.loads(resp.read().decode('utf-8'))
        self.assertIsInstance(demos.get('demos'), list)

    def test_predict_returns_store_summary_and_strips_internal_debug_maps(self):
        buf = io.BytesIO()
        Image.new('RGB', (200, 200), (225, 230, 238)).save(buf, format='JPEG')
        req = Request(
            f'{self.base_url}/api/predict',
            data=buf.getvalue(),
            headers={
                'Content-Type': 'image/jpeg',
                'Origin': self.base_url,
            },
            method='POST',
        )
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))

        self.assertIn('store_summary', data)
        self.assertEqual(data['store_summary']['aisle_state'], 'reponer')
        self.assertEqual(data['store_summary']['reponer_count'], 2)
        self.assertEqual(data['store_summary']['suficiente_count'], 1)
        self.assertIn('image_url', data)
        self.assertNotIn('edges_image', data)
        self.assertNotIn('filtered_edges_image', data)
        self.assertEqual(data['detections'][0]['store_diagnosis']['operational_label'], 'Alerta por baja disponibilidad')
        # La preparación pertenece al servidor y sobrevive a recargar la pestaña.
        with urlopen(f'{self.base_url}/api/health') as resp:
            self.assertTrue(json.load(resp)['analysis_ready'])

    def test_predict_rejects_foreign_origin(self):
        req = Request(
            f'{self.base_url}/api/predict',
            data=b'123',
            headers={
                'Content-Type': 'image/jpeg',
                'Origin': 'https://sitio-externo.example',
            },
            method='POST',
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 403)
        ctx.exception.close()
        with urlopen(f'{self.base_url}/api/health') as resp:
            self.assertFalse(json.load(resp)['analysis_ready'])


if __name__ == '__main__':
    unittest.main()
