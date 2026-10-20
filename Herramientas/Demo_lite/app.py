"""Visor local de inferencia; no necesita CVAT, Docker ni datos de entrenamiento."""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
import sys
import threading
from urllib.parse import parse_qs, urlparse
import webbrowser

from inferencia import BusyError, MAX_BYTES, ModelRunner

ROOT = Path(__file__).resolve().parent


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
        if path == '/api/models':
            return self.send({'models': self.server.runner.available()})
        if path == '/api/health':
            return self.send({'status': 'ok', 'app': 'Walmart Lite'})
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
                return self.send({'error': 'Elige una foto de hasta 15 MB.'}, 413)
            if self.headers.get_content_type() not in ('image/jpeg', 'image/png', 'image/webp', 'application/octet-stream'):
                self.close_connection = True
                return self.send({'error': 'Usa una foto JPG, PNG o WebP.'}, 415)
            params = parse_qs(route.query)
            default_model = getattr(self.server.runner, 'manifest', {}).get('default_model', 'YOLO26-1')
            model = params.get('model', [default_model])[0]
            confidence = float(params.get('confidence', ['0.25'])[0])
            method = params.get('method', ['yolo'])[0]
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError('La carga quedó incompleta. Vuelve a seleccionar la foto.')
            prediction = self.server.runner.analyze(body, model, confidence, method)
            buffer = BytesIO()
            prediction.pop('image').save(buffer, format='JPEG', quality=92)
            prediction['image_url'] = 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
            for field in ('occupancy_image', 'edges_image', 'filtered_edges_image'):
                if field in prediction:
                    buffer = BytesIO()
                    prediction.pop(field).save(buffer, format='PNG')
                    prediction[field + '_url'] = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
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


def create_server(port=8095, directory=None, device='auto'):
    runner = ModelRunner(directory, device)
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.runner = runner
    return server


def main():
    parser = argparse.ArgumentParser(description='Walmart Lite: probar modelos con fotos propias')
    parser.add_argument('--port', type=int, default=8095)
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
        server = create_server(args.port, device=args.device)
    except OSError as error:
        raise SystemExit(f'No se pudo abrir el puerto {args.port}. Cierra otra instancia o usa --port 8096.\n{error}')
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Walmart Lite: {url}\nDeja esta consola abierta. Ctrl+C detiene el visor.', flush=True)
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
