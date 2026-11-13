"""Visor local de inferencia; no necesita CVAT, Docker ni datos de entrenamiento."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
import sys
import threading
import uuid
from urllib.parse import parse_qs, urlparse
import webbrowser

from inferencia import BusyError, MAX_BYTES, ModelRunner

ROOT = Path(__file__).resolve().parent
REVIEW_VERSION = 'revision_equipo_20261109_v1'


def _encode_prediction_payload(prediction, algorithm_id, base_context, shared_edges=None):
    """Adjuntar contexto de análisis y serializar imágenes PIL a data URLs."""
    prediction['analysis_context'] = {
        **base_context,
        'id': str(uuid.uuid4()),
        'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'occupancy_algorithm': algorithm_id,
        'estimator_revision': (prediction.get('occupancy') or {}).get('revision'),
    }
    buffer = BytesIO()
    prediction.pop('image').save(buffer, format='JPEG', quality=92)
    prediction['image_url'] = 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
    for field in ('occupancy_image', 'edges_image', 'filtered_edges_image'):
        if field in prediction:
            buffer = BytesIO()
            prediction.pop(field).save(buffer, format='PNG')
            url = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
            prediction[field + '_url'] = url
            if shared_edges is not None and field in ('edges_image', 'filtered_edges_image'):
                shared_edges[field + '_url'] = url
        elif shared_edges and field + '_url' in shared_edges:
            prediction[field + '_url'] = shared_edges[field + '_url']
    return prediction


class Handler(BaseHTTPRequestHandler):
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
            return self.send((ROOT / 'interfaz.html').read_bytes(), content_type='text/html; charset=utf-8')
        if path == '/revision_rapida.js':
            return self.send((ROOT / 'revision_rapida.js').read_bytes(), content_type='text/javascript; charset=utf-8')
        if path in ('/favicon.ico', '/favicon.svg'):
            svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="16" r="15" fill="#2563eb"/><path d="M7 10h18M7 16h18M7 22h18M11 10v12M21 10v12" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round"/></svg>'''
            return self.send(svg, content_type='image/svg+xml')
        if path == '/api/models':
            models = self.server.runner.available()
            for item in models:
                entry = getattr(self.server.runner, 'entries', {}).get(item['id'], {})
                if entry.get('sha256'):
                    item['model_sha256'] = entry['sha256']
                    item['inference_sha256'] = hashlib.sha256((ROOT / 'inferencia.py').read_bytes()).hexdigest()
            default = getattr(self.server.runner, 'manifest', {}).get('default_model')
            from ocupacion_basal import METHOD, REVISION, THRESHOLD
            for item in models:
                if item.get('geometry_only'):
                    item['occupancy_algorithms'] = [
                        {'id': 'linea_a', 'name': 'Línea A · actual', 'method': item['occupancy_method'],
                         'revision': item['occupancy_revision'], 'threshold': 52,
                         'source_sha256': hashlib.sha256((ROOT / 'ocupacion_linea_a.py').read_bytes()).hexdigest()},
                        {'id': 'basal', 'name': 'Basal · experimental', 'method': METHOD,
                         'revision': REVISION, 'threshold': THRESHOLD,
                         'source_sha256': hashlib.sha256((ROOT / 'ocupacion_basal.py').read_bytes()).hexdigest()}]
            return self.send({'models': models, 'default_model': default or (models[0]['id'] if models else None)})
        if path == '/api/visibilidad/config':
            try:
                from visibilidad_experimental import load
                _, _, revision = load(self.server.runner.root)
                return self.send({'revision': revision})
            except (ValueError, OSError, TypeError, json.JSONDecodeError):
                return self.send({'error': 'El filtro experimental no tiene un candidato verificado.'}, 400)
        if path == '/api/health':
            return self.send({'status': 'ok', 'app': 'Walmart Visión', 'review_version': REVIEW_VERSION})
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
            params = parse_qs(route.query)
            default_model = getattr(self.server.runner, 'manifest', {}).get('default_model', 'V2-YOLO26')
            model = params.get('model', [default_model])[0]
            confidence = float(params['confidence'][0]) if 'confidence' in params else None
            method = params.get('method', ['yolo'])[0]
            visibility_mode = params.get('visibilidad', ['stable'])[0]
            occupancy_algorithm = params.get('ocupacion', ['linea_a'])[0]
            if occupancy_algorithm not in ('linea_a', 'basal', 'ambos'):
                raise ValueError('Algoritmo de ocupación no disponible.')
            primary_algorithm = params.get('primario', ['linea_a'])[0]
            if primary_algorithm not in ('linea_a', 'basal'):
                raise ValueError('Algoritmo principal no disponible.')
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError('La carga quedó incompleta. Vuelve a seleccionar la foto.')
            options = {}
            if visibility_mode != 'stable':
                options['visibility_mode'] = visibility_mode
            if occupancy_algorithm != 'linea_a':
                options['occupancy_algorithm'] = occupancy_algorithm
            if occupancy_algorithm == 'ambos' and primary_algorithm != 'linea_a':
                options['primary_algorithm'] = primary_algorithm
            prediction = self.server.runner.analyze(body, model, confidence, method, **options)
            entry = getattr(self.server.runner, 'entries', {}).get(model, {})
            base_context = {
                'input_sha256': hashlib.sha256(body).hexdigest(), 'model_sha256': entry.get('sha256'),
                'confidence': confidence if confidence is not None else (.6 if entry.get('classes') == ['Nivel'] else .25),
                'method': method, 'visibility_mode': visibility_mode, 'review_version': REVIEW_VERSION,
                'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                  for name in ('app.py', 'inferencia.py', 'revision_rapida.js', 'interfaz.html')},
            }
            variant_results = prediction.pop('variant_results', None)
            active_algo = primary_algorithm if occupancy_algorithm == 'ambos' else occupancy_algorithm
            shared_edges = {}
            _encode_prediction_payload(prediction, active_algo, base_context, shared_edges)
            if variant_results:
                encoded_variants = {}
                for algo_id, variant_pred in variant_results.items():
                    if algo_id == active_algo:
                        encoded_variants[algo_id] = dict(prediction)
                    else:
                        encoded_variants[algo_id] = _encode_prediction_payload(
                            variant_pred, algo_id, base_context, shared_edges)
                prediction['variants'] = encoded_variants
            self.send(prediction)
        except BusyError as error:
            self.send({'error': str(error)}, 409)
        except (ValueError, TypeError) as error:
            self.send({'error': str(error)}, 400)
        except Exception as error:
            print(f'Error al analizar: {error}', file=sys.stderr, flush=True)
            self.send({'error': 'No se pudo analizar la foto. Revisa la consola o prueba una imagen más pequeña.'}, 500)

    def log_message(self, *_):
        pass


def create_server(port=8095, directory=None, device='auto', host='127.0.0.1'):
    runner = ModelRunner(directory, device)
    server = ThreadingHTTPServer((host, port), Handler)
    server.runner = runner
    return server


def main():
    parser = argparse.ArgumentParser(description='Walmart Visión: probar modelos con fotos propias')
    parser.add_argument('--port', type=int, default=8095)
    parser.add_argument('--host', choices=('127.0.0.1', '0.0.0.0'), default='127.0.0.1',
                        help='Dirección de escucha; 0.0.0.0 para el contenedor Docker')
    parser.add_argument('--open', action='store_true', help='Abrir el navegador')
    parser.add_argument('--check', action='store_true', help='Comprobar dependencias y pesos sin iniciar el visor')
    parser.add_argument('--device', choices=('auto', 'cpu'), default='auto')
    args = parser.parse_args()
    if args.check:
        runner = ModelRunner()
        import torch
        import ultralytics
        if ultralytics.__version__ != '8.4.174':
            raise ValueError('Ejecuta instalar.cmd para instalar Ultralytics 8.4.174.')
        print(f"Listo: {len(runner.available())} modelos, PyTorch {torch.__version__}, Ultralytics {ultralytics.__version__}.")
        return
    try:
        server = create_server(args.port, device=args.device, host=args.host)
    except OSError as error:
        raise SystemExit(f'No se pudo abrir el puerto {args.port}. Cierra otra instancia o usa --port 8096.\n{error}')
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Walmart Visión: {url}\nDeja esta consola abierta. Ctrl+C detiene el visor.', flush=True)
    if args.open:
        threading.Timer(.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
