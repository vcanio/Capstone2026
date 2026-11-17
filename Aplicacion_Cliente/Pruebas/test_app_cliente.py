import io
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from PIL import Image

import sys

HERE = Path(__file__).resolve().parent
CLIENT_DIR = HERE.parent
APP_DIR = CLIENT_DIR.parent / 'Aplicacion'
for p in (str(CLIENT_DIR), str(APP_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app_cliente import (  # noqa: E402
    ClientHandler,
    HistoryStore,
    _attach_gap_spans,
    _normalize_allowed_hosts,
    demo_catalog,
    enrich_for_store,
    rows_from_history,
    store_diagnosis,
)


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
        self.assertEqual(diag['operational_severity'], 'critica')
        self.assertEqual(diag['raw_pct'], 5.0)
        self.assertIn('Posible ausencia', diag['headline'])

    def test_wide_gap_describes_an_alert_without_replenishment_instructions(self):
        det = {
            'near_frame': False,
            'occupancy': {'max_gap_pct': 58.0, 'hyb_body_pct': 35.0, 'fill_pct': 42.0},
            'occupancy_estimate': {'state': 'reponer', 'pct': 39.0},
        }
        diag = store_diagnosis(det)
        self.assertEqual(diag['operational_state'], 'reponer')
        self.assertEqual(diag['operational_severity'], 'alta')
        self.assertEqual(diag['raw_pct'], 39.0)
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
        self.assertEqual(diag['operational_severity'], 'normal')
        self.assertEqual(diag['raw_pct'], 85.0)
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
        self.assertEqual(diag['operational_severity'], 'verificar')
        self.assertIsNone(diag['raw_pct'])
        self.assertIn('borde de la foto', diag['headline'])

    def test_missing_reading_never_becomes_a_sufficient_or_empty_result(self):
        for state in ('reponer', 'suficiente', 'revisar'):
            with self.subTest(state=state):
                diag = store_diagnosis({'occupancy_estimate': {'state': state, 'pct': None}})
                self.assertEqual(diag['operational_state'], 'revisar')
                self.assertEqual(diag['operational_label'], 'No evaluable')
                self.assertEqual(diag['operational_severity'], 'verificar')

    def test_review_level_preserves_raw_pct_when_estimate_is_hidden(self):
        det = {
            'near_frame': False,
            'occupancy': {
                'raw_pct': 41.5,
                'operational_severity': 'verificar',
                'signal_pattern': 'low_contrast_continuous_front',
            },
            'occupancy_estimate': {'state': 'revisar', 'pct': None},
        }
        diag = store_diagnosis(det)
        self.assertEqual(diag['operational_state'], 'revisar')
        self.assertEqual(diag['operational_severity'], 'verificar')
        self.assertEqual(diag['raw_pct'], 41.5)

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

    def test_attach_gap_spans_locates_empty_right_half(self):
        from PIL import ImageDraw

        img = Image.new('RGB', (400, 140), (228, 232, 236))
        draw = ImageDraw.Draw(img)
        for x in range(25, 190, 26):
            draw.rectangle((x, 28, x + 20, 118), fill=(215, 45, 45), outline=(25, 25, 25), width=2)
            draw.rectangle((x + 4, 42, x + 16, 75), fill=(250, 215, 40))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)
        detections = [{
            'id': 1,
            'display_polygon': [[10.0, 10.0], [390.0, 10.0], [390.0, 130.0], [10.0, 130.0]],
        }]
        _attach_gap_spans(buf.getvalue(), detections)
        spans = detections[0].get('gap_spans', [])
        self.assertTrue(spans, 'Debe detectar el hueco en la mitad derecha vacía')
        self.assertGreaterEqual(spans[-1]['end'], 0.8)
        self.assertGreaterEqual(spans[-1]['start'], 0.35)
        self.assertEqual(len(spans[-1]['polygon']), 4)

    def test_foreground_occlusion_translates_to_obstructed_zone_notice(self):
        det = {
            'near_frame': False,
            'occupancy': {'signal_pattern': 'foreground_occlusion', 'raw_pct': 62.0},
            'occupancy_estimate': {'state': 'revisar', 'pct': None},
        }
        diag = store_diagnosis(det)
        self.assertEqual(diag['operational_state'], 'revisar')
        self.assertEqual(diag['operational_severity'], 'verificar')
        self.assertIn('Zona obstruida', diag['headline'])


class ClientHttpServerTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), ClientHandler)
        self.server.runner = FakeClientRunner()
        self.server.history_store = HistoryStore(Path(self.temp_dir.name) / 'historial.sqlite3')
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
        self.assertIn('Exportar Excel (.xlsx)', html)
        self.assertIn('Reporte ejecutivo (PDF)', html)
        self.assertIn('Alerta crítica · baja disponibilidad', html)
        self.assertIn('Severidad Operativa', html)
        self.assertIn('levelRawPct', html)
        self.assertIn('person-poly', html)
        self.assertNotIn('Marcar para revisión', html)
        self.assertNotIn('review-switch', html)
        self.assertNotIn('Verificación humana', html)
        self.assertNotIn('data-quick-level', html)
        with urlopen(f'{self.base_url}/logo.svg') as resp:
            self.assertEqual(resp.headers.get_content_type(), 'image/svg+xml')
            self.assertEqual(resp.read(), (CLIENT_DIR / 'logo.svg').read_bytes())

    def test_level_hover_uses_contour_state_color(self):
        html = (CLIENT_DIR / 'interfaz_cliente.html').read_text(encoding='utf-8')
        hover_line = next(
            (line for line in html.splitlines() if '.shelf-poly:hover' in line),
            '',
        )
        self.assertIn('var(--contour-color)', hover_line)
        self.assertNotIn('#ffc220', hover_line.lower())
        self.assertIn('data-view="gaps"', html)

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

    def test_allow_host_permits_matching_https_origin_only(self):
        self.server.allow_hosts = _normalize_allowed_hosts(['https://demo.trycloudflare.com/'])

        health_req = Request(
            f'{self.base_url}/api/health',
            headers={'Host': 'demo.trycloudflare.com'},
        )
        with urlopen(health_req) as resp:
            self.assertEqual(resp.status, 200)

        buf = io.BytesIO()
        Image.new('RGB', (200, 200), (225, 230, 238)).save(buf, format='JPEG')
        ok_req = Request(
            f'{self.base_url}/api/predict',
            data=buf.getvalue(),
            headers={
                'Content-Type': 'image/jpeg',
                'Host': 'demo.trycloudflare.com',
                'Origin': 'https://demo.trycloudflare.com',
            },
            method='POST',
        )
        with urlopen(ok_req) as resp:
            self.assertEqual(resp.status, 200)

        for bad_headers in (
            {'Host': 'otro.trycloudflare.com', 'Origin': 'https://otro.trycloudflare.com'},
            {'Host': 'demo.trycloudflare.com', 'Origin': 'https://sitio-externo.example'},
            {'Host': 'demo.trycloudflare.com', 'Origin': 'http://demo.trycloudflare.com'},
        ):
            bad_req = Request(
                f'{self.base_url}/api/predict',
                data=buf.getvalue(),
                headers={'Content-Type': 'image/jpeg', **bad_headers},
                method='POST',
            )
            with self.assertRaises(HTTPError) as ctx:
                urlopen(bad_req)
            self.assertEqual(ctx.exception.code, 403)
            ctx.exception.close()

    def test_sqlite_history_persistence_and_xlsx_pdf_exports(self):
        # 1. Historial inicialmente vacío.
        with urlopen(f'{self.base_url}/api/history') as resp:
            self.assertEqual(resp.status, 200)
            initial = json.load(resp)
        self.assertEqual(initial['persistence'], 'sqlite3')
        self.assertEqual(initial['items'], [])

        # 2. Analizar con X-Item-Id persiste directamente en SQLite y se ve en otro dispositivo.
        buf = io.BytesIO()
        Image.new('RGB', (200, 200), (225, 230, 238)).save(buf, format='JPEG')
        pred_req = Request(
            f'{self.base_url}/api/predict',
            data=buf.getvalue(),
            headers={
                'Content-Type': 'image/jpeg',
                'Origin': self.base_url,
                'X-Item-Id': 'g_srv_1',
                'X-Item-Name': 'gondola_pasillo_1.jpg',
            },
            method='POST',
        )
        with urlopen(pred_req) as resp:
            self.assertEqual(resp.status, 200)

        # 3. Actualizar nombre vía POST /api/history y recuperar.
        sync_req = Request(
            f'{self.base_url}/api/history',
            data=json.dumps({
                'items': [{
                    'id': 'g_srv_1',
                    'order': 1,
                    'name': 'gondola_pasillo_1_v2.jpg',
                    'aisle_state': 'reponer',
                    'result': self.server.history_store.list_items()[0]['result'],
                }],
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Origin': self.base_url},
            method='POST',
        )
        with urlopen(sync_req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(json.load(resp)['count'], 1)

        with urlopen(f'{self.base_url}/api/history') as resp:
            items = json.load(resp)['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['name'], 'gondola_pasillo_1_v2.jpg')
        self.assertTrue(items[0]['result']['image_url'].startswith('data:image/jpeg;base64,'))

        # 4. Exportación Excel (.xlsx) desde SQLite y mediante POST de filas.
        with urlopen(f'{self.base_url}/api/export/xlsx') as resp:
            self.assertEqual(resp.status, 200)
            xlsx_bytes = resp.read()
        self.assertTrue(xlsx_bytes.startswith(b'PK\x03\x04'))
        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
            names = set(zf.namelist())
            self.assertIn('xl/workbook.xml', names)
            self.assertIn('xl/worksheets/sheet1.xml', names)
            sheet_xml = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
            self.assertIn('gondola_pasillo_1_v2.jpg', sheet_xml)
            self.assertNotIn('Revisión humana', sheet_xml)

        # 5. Exportación PDF (%PDF-1.4) desde SQLite y mediante POST.
        with urlopen(f'{self.base_url}/api/export/pdf') as resp:
            self.assertEqual(resp.status, 200)
            pdf_bytes = resp.read()
        self.assertTrue(pdf_bytes.startswith(b'%PDF-1.4'))
        self.assertTrue(pdf_bytes.endswith(b'%%EOF\n'))
        self.assertIn(b'gondola_pasillo_1_v2.jpg', pdf_bytes)

        post_pdf_req = Request(
            f'{self.base_url}/api/export/pdf',
            data=json.dumps({
                'rows': [
                    ['Góndola', 'Estado', 'Nivel', 'Resultado', 'Severidad', 'Índice', 'Bruto', 'Hueco', 'Detalle'],
                    ['foto_manual.jpg', 'Con alertas', 'Nivel 1', 'Alerta crítica', 'Crítica', 10, 10, 85, 'Hueco'],
                ],
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Origin': self.base_url},
            method='POST',
        )
        with urlopen(post_pdf_req) as resp:
            self.assertEqual(resp.status, 200)
            post_pdf = resp.read()
        self.assertTrue(post_pdf.startswith(b'%PDF-1.4'))
        self.assertIn(b'foto_manual.jpg', post_pdf)

        # 6. Borrado DELETE /api/history.
        del_req = Request(f'{self.base_url}/api/history', headers={'Origin': self.base_url}, method='DELETE')
        with urlopen(del_req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(json.load(resp)['count'], 0)
        with urlopen(f'{self.base_url}/api/history') as resp:
            self.assertEqual(json.load(resp)['items'], [])

    def test_no_evaluable_person_obstruction_summary_and_export_row(self):
        enriched = enrich_for_store({
            'photo_status': 'no_evaluable',
            'quality_issue': 'persona_obstruyendo',
            'message': 'Persona obstruyendo la góndola (42% del Nivel 2). Toma la foto nuevamente con el pasillo despejado.',
            'detections': [],
        })
        self.assertEqual(enriched['store_summary']['aisle_state'], 'verificar')
        self.assertEqual(enriched['store_summary']['aisle_label'], 'Foto no evaluable')
        rows = rows_from_history([{'name': 'persona_frente.jpg', 'result': enriched}])
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), 9)
        self.assertEqual(rows[1][3], 'Foto no evaluable')
        self.assertIn('Persona obstruyendo', rows[1][8])


if __name__ == '__main__':
    unittest.main()
