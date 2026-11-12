"""Walmart Visión · Visor de alertas (aplicación cliente).

Comparte el motor oficial (`Aplicacion/inferencia.py`, `ocupacion_linea_a.py` y `best.pt`)
sin modificar la aplicación de auditoría técnica en `Aplicacion/`.
"""
import argparse
import base64
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import math
from pathlib import Path
import socket
import sys
import threading
from urllib.parse import urlparse
import webbrowser

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
APP_DIR = PROJECT_ROOT / 'Aplicacion'
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from inferencia import BusyError, MAX_BYTES, ModelRunner  # noqa: E402
from ocupacion_linea_a import CALIBRATED_THRESHOLD_PCT, REVISION_LINEA_A  # noqa: E402

DEFAULT_CONFIDENCE = 0.60
DEFAULT_METHOD = 'yolo_paulo_v2'


def store_diagnosis(detection: dict) -> dict:
    """Describir alertas visuales sin prescribir acciones de reposición."""
    est = detection.get('occupancy_estimate') or {}
    occ = detection.get('occupancy') or {}
    pct = est.get('pct')
    evaluable = isinstance(pct, (int, float)) and math.isfinite(pct)
    state = (est.get('state') or 'revisar') if evaluable else 'revisar'
    max_gap = occ.get('max_gap_pct')
    hyb_body = occ.get('hyb_body_pct')
    fill_pct = occ.get('fill_pct')
    pattern = occ.get('signal_pattern')
    near_frame = bool(detection.get('near_frame'))

    if state == 'reponer':
        if (pct is not None and pct <= 12.0) or (hyb_body is not None and hyb_body < 15.0):
            headline = 'Posible ausencia de producto visible'
        elif (
            max_gap is not None and max_gap >= 45.0 and
            (fill_pct is None or (100.0 - max_gap) <= fill_pct + 5.0)
        ):
            headline = f'Hueco visual estimado en el {round(max_gap)} % del frente'
        elif max_gap is not None and max_gap >= 30.0:
            headline = f'Posible baja disponibilidad (hueco de {round(max_gap)} % del ancho)'
        else:
            headline = 'Índice visual bajo el umbral de alerta'
        return {
            'operational_state': 'reponer',
            'operational_label': 'Alerta por baja disponibilidad',
            'headline': headline,
            'action': 'Revisa la foto y los contornos para confirmar la alerta.',
        }

    if state == 'suficiente':
        gap_note = (
            f'Frente continuo cubierto ({round(100.0 - max_gap)} % del ancho con producto).'
            if isinstance(max_gap, (int, float)) else 'El análisis de esta foto no generó una alerta en este nivel.'
        )
        return {
            'operational_state': 'suficiente',
            'operational_label': 'Sin alerta visual',
            'headline': 'Sin alerta visual detectada',
            'action': gap_note,
        }

    if near_frame:
        headline = 'Estante en el borde de la foto'
        action = 'Revisa el encuadre y toma otra foto que muestre el nivel completo.'
    elif pattern in ('hollow_banner', 'upper_band_only'):
        headline = 'Patrón visual ambiguo en el nivel'
        action = 'Revisa la visibilidad del nivel y toma otra foto si hace falta.'
    else:
        headline = 'Lectura visual ambigua'
        action = 'Revisa la foto; si no hay evidencia suficiente, registra el nivel como no evaluable.'
    return {
        'operational_state': 'revisar',
        'operational_label': 'Requiere revisión' if evaluable else 'No evaluable',
        'headline': headline,
        'action': action,
    }


def enrich_for_store(prediction: dict) -> dict:
    """Añadir resumen de alertas por nivel; conservar los códigos internos del motor."""
    detections = prediction.get('detections') or []
    reponer_ids = []
    revisar_ids = []
    suficiente_ids = []

    for det in detections:
        diag = store_diagnosis(det)
        det['store_diagnosis'] = diag
        st = diag['operational_state']
        if st == 'reponer':
            reponer_ids.append(det['id'])
        elif st == 'revisar':
            revisar_ids.append(det['id'])
        else:
            suficiente_ids.append(det['id'])

    if not detections:
        aisle_state = 'verificar'
        aisle_label = 'Sin niveles detectados'
        aisle_summary = 'Toma la foto de frente incluyendo toda la góndola.'
    elif reponer_ids:
        aisle_state = 'reponer'
        n_rep = len(reponer_ids)
        lv_str = f'nivel {reponer_ids[0]}' if n_rep == 1 else f'niveles {", ".join(map(str, reponer_ids))}'
        aisle_label = f'{n_rep} {"nivel con alerta" if n_rep == 1 else "niveles con alerta"}'
        aisle_summary = f'Posible baja disponibilidad en {lv_str}. Revisa la foto y los contornos.'
    elif revisar_ids:
        aisle_state = 'verificar'
        n_rev = len(revisar_ids)
        aisle_label = f'{n_rev} {"nivel por verificar" if n_rev == 1 else "niveles por verificar"}'
        aisle_summary = 'Verifica los niveles con lectura ambigua.'
    else:
        aisle_state = 'suficiente'
        aisle_label = 'Sin alertas visuales detectadas'
        aisle_summary = f'El análisis no generó alertas en los {len(detections)} niveles detectados.'

    prediction['store_summary'] = {
        'aisle_state': aisle_state,
        'aisle_label': aisle_label,
        'aisle_summary': aisle_summary,
        'total_levels': len(detections),
        'reponer_count': len(reponer_ids),
        'revisar_count': len(revisar_ids),
        'suficiente_count': len(suficiente_ids),
        'reponer_levels': reponer_ids,
        'revisar_levels': revisar_ids,
        'threshold_pct': CALIBRATED_THRESHOLD_PCT,
        'revision': REVISION_LINEA_A,
    }
    return prediction


@lru_cache(maxsize=1)
def demo_catalog() -> dict:
    """Catálogo pequeño de fotos de ejemplo de desarrollo (nunca de test) para demostración en 1 clic."""
    export_dir = PROJECT_ROOT / 'Datos/Preparados/V3/v3_20261105_012333_53df4a59/exportacion_71b4668d/images'
    candidates = [
        ('gondola_pasillo_01', 'Pasillo Snacks · Góndola 1', 'lider_express_020_A_vacios.png'),
        ('gondola_pasillo_02', 'Pasillo Despensa · Góndola 2', 'R238__2710_ma_110.jpg'),
        ('gondola_pasillo_03', 'Pasillo Bebidas · Góndola 3', 'lider_express_046_D_superior_vacio.png'),
        ('gondola_pasillo_04', 'Pasillo Abarrotes · Góndola 4', 'lider_2_122_0_original.jpg'),
    ]
    items = []
    by_id = {}
    if export_dir.is_dir():
        dev_dirs = [export_dir / sub for sub in ('train', 'val_real', 'val_sintetica', 'val')
                    if (export_dir / sub).is_dir()]
        for demo_id, label, filename in candidates:
            for d in dev_dirs:
                target = d / filename
                if target.is_file():
                    rec = {'id': demo_id, 'label': label, 'filename': filename, 'path': str(target)}
                    items.append({'id': demo_id, 'label': label, 'filename': filename})
                    by_id[demo_id] = rec
                    break
    return {'items': items, 'by_id': by_id}


class ClientHandler(BaseHTTPRequestHandler):
    def local_request(self):
        host = self.headers.get('Host', '')
        allowed = {f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'}
        return host in allowed and self.headers.get('Origin', f'http://{host}') == f'http://{host}'

    def send(self, body, status=200, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.local_request():
            return self.send({'error': 'Solo se permite el acceso local.'}, 403)
        path = urlparse(self.path).path
        if path == '/':
            return self.send((HERE / 'interfaz_cliente.html').read_bytes(), content_type='text/html; charset=utf-8')
        if path in ('/favicon.ico', '/favicon.svg', '/logo.svg'):
            return self.send((HERE / 'logo.svg').read_bytes(), content_type='image/svg+xml')
        if path == '/api/health':
            return self.send({
                'status': 'ok',
                'app': 'Walmart Visión · Visor de alertas',
                'revision': REVISION_LINEA_A,
                'threshold_pct': CALIBRATED_THRESHOLD_PCT,
                'analysis_ready': getattr(self.server, 'analysis_ready', False),
            })
        if path == '/api/demo-photos':
            return self.send({'demos': demo_catalog()['items']})
        if path.startswith('/api/demo-photo/'):
            demo_id = path.rsplit('/', 1)[-1]
            entry = demo_catalog()['by_id'].get(demo_id)
            if not entry:
                return self.send({'error': 'Ejemplo no disponible.'}, 404)
            file_path = Path(entry['path'])
            mime = 'image/png' if file_path.suffix.lower() == '.png' else 'image/jpeg'
            return self.send(file_path.read_bytes(), content_type=mime)
        return self.send({'error': 'Ruta no disponible.'}, 404)

    def do_POST(self):
        if not self.local_request():
            return self.send({'error': 'Origen no autorizado.'}, 403)
        route = urlparse(self.path)
        if route.path != '/api/predict':
            return self.send({'error': 'Ruta no disponible.'}, 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BYTES:
                self.close_connection = True
                return self.send({'error': 'Elige una foto de hasta 10 MB.'}, 413)
            if self.headers.get_content_type() not in ('image/jpeg', 'image/png', 'image/webp', 'application/octet-stream'):
                self.close_connection = True
                return self.send({'error': 'Usa una foto JPG, PNG o WebP.'}, 415)
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError('La carga quedó incompleta. Vuelve a seleccionar la foto.')

            default_model = getattr(self.server.runner, 'manifest', {}).get('default_model')
            prediction = self.server.runner.analyze(
                body,
                model_id=default_model,
                confidence=DEFAULT_CONFIDENCE,
                method=DEFAULT_METHOD,
            )
            self.server.analysis_ready = True
            buffer = BytesIO()
            prediction.pop('image').save(buffer, format='JPEG', quality=90)
            prediction['image_url'] = 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
            for extra_img in ('occupancy_image', 'edges_image', 'filtered_edges_image'):
                prediction.pop(extra_img, None)
            enrich_for_store(prediction)
            self.send(prediction)
        except BusyError as error:
            self.send({'error': str(error)}, 409)
        except (ValueError, TypeError) as error:
            self.send({'error': str(error)}, 400)
        except Exception as error:
            print(f'Error al analizar en app cliente: {error}', file=sys.stderr, flush=True)
            self.send({'error': 'No se pudo analizar la foto. Intenta nuevamente con una toma despejada.'}, 500)

    def log_message(self, *_):
        pass


def pick_free_port(preferred: int = 8098) -> int:
    for candidate in range(preferred, preferred + 15):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('127.0.0.1', candidate)) != 0:
                return candidate
    return preferred


def create_server(port=8098, directory=None, device='auto', host='127.0.0.1'):
    runner = ModelRunner(directory or APP_DIR, device=device)
    server = ThreadingHTTPServer((host, port), ClientHandler)
    server.runner = runner
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8098)
    parser.add_argument('--host', choices=('127.0.0.1', '0.0.0.0'), default='127.0.0.1')
    parser.add_argument('--open', action='store_true', help='Abrir navegador automáticamente')
    parser.add_argument('--check', action='store_true', help='Verificar configuración y pesos sin abrir servidor')
    parser.add_argument('--device', choices=('auto', 'cpu'), default='auto')
    parser.add_argument('--app-dir', type=Path, default=APP_DIR,
                        help='Carpeta del motor compartido y modelos (para Docker)')
    args = parser.parse_args()

    if args.check:
        runner = ModelRunner(args.app_dir, device=args.device)
        print(json.dumps({
            'status': 'ok',
            'app': 'Walmart Visión · Cliente Final',
            'models': len(runner.available()),
            'revision': REVISION_LINEA_A,
            'threshold_pct': CALIBRATED_THRESHOLD_PCT,
            'demo_photos': len(demo_catalog()['items']),
        }, ensure_ascii=False, indent=2))
        return

    port = pick_free_port(args.port)
    server = create_server(port=port, directory=args.app_dir, device=args.device, host=args.host)
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Walmart Visión (Cliente Final) activo en: {url}', flush=True)
    if args.open:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
