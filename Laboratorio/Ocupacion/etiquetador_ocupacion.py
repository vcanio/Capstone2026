"""Servidor local de etiquetado rápido por teclado para calibrar ocupación en V3.

No modifica CVAT, pesos ni particiones, no muestra predicciones actuales para
evitar sesgo de confirmación y guarda cada cambio de forma atómica en disco.
"""
import argparse
import csv
from datetime import datetime, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import os
from pathlib import Path
import socket
import sys
import threading
from urllib.parse import urlparse
import webbrowser

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
import almacenamiento_datos as storage
HERE = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107'
MANIFEST_PATH = DATA_DIR / 'muestra_desarrollo.json'
LABELS_JSON_PATH = DATA_DIR / 'etiquetas_humanas.json'
LABELS_CSV_PATH = DATA_DIR / 'etiquetas_humanas.csv'

VALID_LABELS = {'suficiente', 'baja_disponibilidad', 'vacio', 'no_evaluable'}
MAX_PREVIEW_SIDE = 1600


class LabelingStore:
    def __init__(self, manifest_path=MANIFEST_PATH, labels_path=LABELS_JSON_PATH, csv_path=LABELS_CSV_PATH):
        self.manifest_path = Path(manifest_path)
        self.labels_path = Path(labels_path)
        self.csv_path = Path(csv_path)
        self.lock = threading.Lock()
        if not self.manifest_path.is_file():
            from preparar_muestra import build_manifest
            build_manifest()
        self.manifest = json.loads(self.manifest_path.read_text(encoding='utf-8'))
        self.by_key = {img['item_key']: img for img in self.manifest['images']}
        self.by_order = {int(img['blind_order']): img for img in self.manifest['images']}
        self.state = self._load_labels()

    def _load_labels(self):
        if self.labels_path.is_file():
            data = json.loads(self.labels_path.read_text(encoding='utf-8'))
            if isinstance(data, dict) and isinstance(data.get('items'), dict):
                return data
        return {
            'schema_version': 1,
            'manifest_id': self.manifest['id'],
            'annotator': 'Vicente',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': None,
            'items': {},
        }

    def summary_payload(self):
        with self.lock:
            items = self.state['items']
            photo_done = {'total': 0, 'val': 0, 'train': 0}
            level_done = {'total': 0, 'val': 0, 'train': 0}
            level_totals = {'total': 0, 'val': 0, 'train': 0}
            dist = {k: 0 for k in VALID_LABELS}
            gondola_alerts = {'alerta': 0, 'suficiente': 0, 'revisar': 0}

            for img in self.manifest['images']:
                split = img['split']
                n_levels = img['level_count']
                level_totals['total'] += n_levels
                level_totals[split] += n_levels
                saved = items.get(img['item_key'], {}).get('levels', {})
                valid_count = 0
                level_states = []
                for lv in img['levels']:
                    lid = str(lv['level_id'])
                    val = saved.get(lid)
                    if val in VALID_LABELS:
                        valid_count += 1
                        dist[val] += 1
                        level_states.append(val)
                level_done['total'] += valid_count
                level_done[split] += valid_count
                if valid_count == n_levels and n_levels > 0:
                    photo_done['total'] += 1
                    photo_done[split] += 1
                    if any(s in ('baja_disponibilidad', 'vacio') for s in level_states):
                        gondola_alerts['alerta'] += 1
                    elif all(s == 'no_evaluable' for s in level_states):
                        gondola_alerts['revisar'] += 1
                    else:
                        gondola_alerts['suficiente'] += 1

            return {
                'manifest_id': self.manifest['id'],
                'manifest_summary': self.manifest['summary'],
                'label_schema': self.manifest['label_schema'],
                'annotator': self.state.get('annotator', 'Vicente'),
                'updated_at': self.state.get('updated_at'),
                'progress': {
                    'photos_done': photo_done,
                    'levels_done': level_done,
                    'levels_total': level_totals,
                    'label_distribution': dist,
                    'gondola_distribution': gondola_alerts,
                },
                'images': self.manifest['images'],
                'saved': items,
            }

    def save_item(self, payload):
        if not isinstance(payload, dict):
            raise ValueError('Formato JSON inválido.')
        item_key = payload.get('item_key')
        if item_key not in self.by_key:
            raise ValueError('Identificador de fotografía desconocido.')
        img = self.by_key[item_key]
        valid_level_ids = {str(lv['level_id']) for lv in img['levels']}
        incoming_levels = payload.get('levels')
        if not isinstance(incoming_levels, dict):
            raise ValueError('El campo levels debe ser un objeto.')

        cleaned = {}
        for lid, label in incoming_levels.items():
            lid_str = str(lid)
            if lid_str not in valid_level_ids:
                raise ValueError(f'Nivel fuera de rango: {lid_str}')
            if label is None or label == '':
                continue
            if label not in VALID_LABELS:
                raise ValueError(f'Etiqueta no admitida: {label}')
            cleaned[lid_str] = label

        note = str(payload.get('note') or '').strip()[:500]
        annotator = str(payload.get('annotator') or self.state.get('annotator') or 'Vicente').strip()[:80]
        now = datetime.now(timezone.utc).isoformat()

        with self.lock:
            self.state['annotator'] = annotator or 'Vicente'
            self.state['updated_at'] = now
            if cleaned or note:
                self.state['items'][item_key] = {
                    'levels': cleaned,
                    'note': note,
                    'annotator': self.state['annotator'],
                    'updated_at': now,
                }
            else:
                self.state['items'].pop(item_key, None)
            self._persist_locked()
            return self.state['items'].get(item_key, {'levels': {}, 'note': '', 'updated_at': now})

    def _persist_locked(self):
        self.labels_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.labels_path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, self.labels_path)
        self._write_csv_locked()

    def _write_csv_locked(self):
        tmp_csv = self.csv_path.with_suffix('.csv.tmp')
        fieldnames = [
            'blind_code', 'blind_order', 'split', 'origen', 'variante', 'grupo_escena',
            'familia', 'imagen_id', 'name', 'sha256', 'level_id', 'cvat_shape_id',
            'label', 'alert_target', 'evaluable', 'gondola_complete', 'gondola_state',
            'annotator', 'updated_at', 'note',
        ]
        with tmp_csv.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for img in self.manifest['images']:
                entry = self.state['items'].get(img['item_key'], {})
                levels_map = entry.get('levels', {})
                all_labeled = len(levels_map) == img['level_count'] and img['level_count'] > 0
                if not all_labeled:
                    g_state = ''
                elif any(v in ('baja_disponibilidad', 'vacio') for v in levels_map.values()):
                    g_state = 'alerta'
                elif all(v == 'no_evaluable' for v in levels_map.values()):
                    g_state = 'no_evaluable'
                else:
                    g_state = 'suficiente'

                for lv in img['levels']:
                    lid = str(lv['level_id'])
                    label = levels_map.get(lid, '')
                    evaluable = label in ('suficiente', 'baja_disponibilidad', 'vacio') if label else ''
                    alert = (label in ('baja_disponibilidad', 'vacio')) if evaluable is True else ''
                    writer.writerow({
                        'blind_code': img['blind_code'],
                        'blind_order': img['blind_order'],
                        'split': img['split'],
                        'origen': img['origen'],
                        'variante': img['variante'],
                        'grupo_escena': img['grupo_escena'],
                        'familia': img.get('familia') or '',
                        'imagen_id': img['imagen_id'],
                        'name': img['name'],
                        'sha256': img['sha256'],
                        'level_id': lv['level_id'],
                        'cvat_shape_id': lv.get('cvat_shape_id') or '',
                        'label': label,
                        'alert_target': alert,
                        'evaluable': evaluable,
                        'gondola_complete': all_labeled,
                        'gondola_state': g_state,
                        'annotator': entry.get('annotator', ''),
                        'updated_at': entry.get('updated_at', ''),
                        'note': entry.get('note', ''),
                    })
        os.replace(tmp_csv, self.csv_path)


@lru_cache(maxsize=64)
def render_preview_jpeg(rel_path: str) -> bytes:
    full_path = storage.read_path(ROOT, rel_path)
    with Image.open(full_path) as raw:
        img = ImageOps.exif_transpose(raw).convert('RGB')
        if max(img.size) > MAX_PREVIEW_SIDE:
            img.thumbnail((MAX_PREVIEW_SIDE, MAX_PREVIEW_SIDE), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format='JPEG', quality=90, optimize=False)
        return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    def local_request(self):
        host = self.headers.get('Host', '')
        allowed = {f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'}
        origin = self.headers.get('Origin')
        return host in allowed and (origin is None or origin == f'http://{host}')

    def send(self, body, status=200, content_type='application/json; charset=utf-8', extra_headers=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.local_request():
            return self.send({'error': 'Solo se permite acceso local.'}, 403)
        parsed = urlparse(self.path)
        path = parsed.path
        store: LabelingStore = self.server.store

        if path == '/':
            return self.send((HERE / 'interfaz_etiquetador.html').read_bytes(), content_type='text/html; charset=utf-8')
        if path in ('/favicon.ico', '/favicon.svg'):
            svg = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
                   b'<circle cx="16" cy="16" r="15" fill="#1d6ee8"/>'
                   b'<path d="M7 10h18M7 16h18M7 22h18" stroke="#f5b82e" stroke-width="2.6" stroke-linecap="round"/></svg>')
            return self.send(svg, content_type='image/svg+xml')
        if path == '/api/state':
            return self.send(store.summary_payload())
        if path == '/api/export.csv':
            with store.lock:
                store._write_csv_locked()
                csv_bytes = store.csv_path.read_bytes()
            return self.send(
                csv_bytes,
                content_type='text/csv; charset=utf-8',
                extra_headers={'Content-Disposition': 'attachment; filename="etiquetas_humanas_ocupacion_v3.csv"'},
            )
        if path.startswith('/api/photo/'):
            try:
                order_num = int(path.rsplit('/', 1)[-1])
                rec = store.by_order[order_num]
            except (ValueError, KeyError):
                return self.send({'error': 'Fotografía no encontrada.'}, 404)
            jpeg = render_preview_jpeg(rec['serve_path'])
            # Precalentar siguientes dos fotos en segundo plano para transición instantánea.
            def _warm():
                for nxt in (order_num + 1, order_num + 2):
                    if nxt in store.by_order:
                        r = store.by_order[nxt]
                        try:
                            render_preview_jpeg(r['serve_path'])
                        except Exception:
                            pass
            threading.Thread(target=_warm, daemon=True).start()
            return self.send(jpeg, content_type='image/jpeg')

        return self.send({'error': 'Ruta no disponible.'}, 404)

    def do_POST(self):
        if not self.local_request():
            return self.send({'error': 'Origen no autorizado.'}, 403)
        path = urlparse(self.path).path
        if path != '/api/save':
            return self.send({'error': 'Ruta no disponible.'}, 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 256_000:
                return self.send({'error': 'Carga fuera de rango.'}, 413)
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            saved_entry = self.server.store.save_item(payload)
            return self.send({'ok': True, 'saved_entry': saved_entry})
        except (ValueError, json.JSONDecodeError) as err:
            return self.send({'error': str(err)}, 400)

    def log_message(self, *_):
        pass


def pick_free_port(preferred=8096):
    for candidate in range(preferred, preferred + 15):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('127.0.0.1', candidate)) != 0:
                return candidate
    return preferred


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8096)
    parser.add_argument('--open', action='store_true', help='Abrir navegador automáticamente')
    parser.add_argument('--check', action='store_true', help='Verificar manifiesto y decodificación sin abrir servidor')
    args = parser.parse_args()

    store = LabelingStore()
    if args.check:
        first = store.by_order[1]
        jpeg = render_preview_jpeg(first['serve_path'])
        print(json.dumps({
            'check': 'ok',
            'total_images': len(store.manifest['images']),
            'sample_preview_bytes': len(jpeg),
            'labels_file': store.labels_path.relative_to(ROOT).as_posix(),
        }, ensure_ascii=False, indent=2))
        return

    port = pick_free_port(args.port)
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.store = store
    url = f'http://127.0.0.1:{port}'
    print(f'Etiquetador de ocupación V3 activo en: {url}', flush=True)
    print(f'Guardado automático en: {store.labels_path}', flush=True)
    if args.open:
        threading.Timer(0.35, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
