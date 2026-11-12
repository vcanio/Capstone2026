"""Visor sandbox local para probar y comparar el prototipo Línea A vs V3 actual.

Uso:
    .\\Aplicacion\\.entorno-py312\\Scripts\\python.exe .\\Laboratorio\\Ocupacion\\visor_linea_a.py --open
O con GPU (si está instalada en .venv-modelo):
    .\\.venv-modelo\\Scripts\\python.exe .\\Laboratorio\\Ocupacion\\visor_linea_a.py --open

Permite subir cualquier fotografía propia o explorar casos de prueba sin
modificar `Aplicacion/`, `best.pt`, CVAT ni revelar niveles pendientes del etiquetador.
"""
import argparse
import base64
from copy import deepcopy
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import math
import os
from pathlib import Path
import socket
import sys
import threading
import time
from urllib.parse import urlparse
import webbrowser

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
APP_DIR = ROOT / 'Aplicacion'
for path_str in (str(APP_DIR), str(HERE)):
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from inferencia import read_photo  # noqa: E402
from ocupacion_paulo import Analyzer  # noqa: E402
from presentacion_niveles import draw_result, occupancy_estimate, spatial_order  # noqa: E402
from vision_v3 import apply_scope  # noqa: E402
from prototipo_linea_a import (  # noqa: E402
    CALIBRATED_THRESHOLD_PCT,
    compute_cell_maps,
    extract_cell_features,
    gondola_feature_bounds,
    score_level_from_features,
)

MODEL_CFG_PATH = ROOT / '.config-modelo/version_actual_v3.json'
EXPORT_IMG_DIR = ROOT / 'Datos/Preparados/V3/v3_20261105_012333_53df4a59/exportacion_71b4668d/images'
MANIFEST_PATH = ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107/muestra_desarrollo.json'
LABELS_PATH = ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107/etiquetas_humanas.json'
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
import almacenamiento_datos as storage

MAX_UPLOAD_JSON_BYTES = 18 * 1024 * 1024
MAX_DISPLAY_SIDE = 1280
ALLOWED_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}


def _pil_to_data_url(image: Image.Image, quality: int = 86) -> str:
    img = image
    if max(img.size) > MAX_DISPLAY_SIDE:
        img = img.copy()
        img.thumbnail((MAX_DISPLAY_SIDE, MAX_DISPLAY_SIDE), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=quality, optimize=False)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/jpeg;base64,{b64}'


@lru_cache(maxsize=1)
def build_sample_catalog() -> dict:
    """Construir catálogo seguro sin revelar ni exponer fotos pendientes de etiquetado ciego."""
    samples = []

    manifest_imgs = []
    saved_items = {}
    if MANIFEST_PATH.is_file():
        manifest_imgs = json.loads(MANIFEST_PATH.read_text(encoding='utf-8')).get('images', [])
    if LABELS_PATH.is_file():
        saved_items = json.loads(LABELS_PATH.read_text(encoding='utf-8')).get('items', {})

    unlabeled_names = set()
    unlabeled_stems = set()
    for rec in manifest_imgs:
        done = len(saved_items.get(rec['item_key'], {}).get('levels', {})) == rec['level_count']
        if not done:
            name = rec['name']
            unlabeled_names.add(name)
            stem = Path(name).stem.split('__')[-1].split('_original')[0]
            if stem:
                unlabeled_stems.add(stem)

    def is_blind_blocked(path: Path) -> bool:
        if path.name in unlabeled_names:
            return True
        return any(st in path.stem for st in unlabeled_stems)

    def add_sample(sample_id: str, category: str, title: str, path: Path, note: str = ''):
        if path.is_file() and not is_blind_blocked(path):
            samples.append({
                'id': sample_id,
                'category': category,
                'title': title,
                'filename': path.name,
                'note': note,
                'path': str(path),
            })

    # 1. Controles históricos en desarrollo (nunca desde test ni pendientes ciegos)
    control_notes = {
        '046': 'Nivel superior vacío con letrero superior (control histórico train).',
        '055': 'Nivel superior vacío sobre botellas (control histórico train).',
    }
    if EXPORT_IMG_DIR.is_dir():
        dev_dirs = [EXPORT_IMG_DIR / sub for sub in ('train', 'val_real', 'val_sintetica', 'val')
                    if (EXPORT_IMG_DIR / sub).is_dir()]
        for code, note in control_notes.items():
            for d in dev_dirs:
                matches = sorted(d.glob(f'lider_express_{code}_D_superior_vacio.*'))
                if matches:
                    add_sample(f'ctrl_{code}', 'casos_clave', f'Control {code}_D (superior vacío)', matches[0], note)
                    break

    # 2. Casos representativos ya etiquetados por Vicente + lista completa de ya etiquetadas
    manifest_by_key = {r['item_key']: r for r in manifest_imgs}
    highlighted = {
        'lider_2_122_0_original.jpg': 'N6 lleno pero liso (antes falso Reponer 21.9 % -> Suficiente).',
        'lider_express_020_A_vacios.png': 'N2 vacío con riel inferior (antes falso Suficiente 79.4 % -> Reponer).',
        'R315__2109_oh_068.jpg': 'N1 inferior abastecido (antes falso Reponer 20.6 % -> Suficiente).',
        'R238__2710_ma_110.jpg': 'N1 baja disponibilidad real (antes Suficiente 46.9 % -> Reponer).',
    }
    labeled_ready = []
    for key, entry in saved_items.items():
        rec = manifest_by_key.get(key)
        if rec and len(entry.get('levels', {})) == rec['level_count']:
            labeled_ready.append(rec)

    for rec in labeled_ready:
        note = highlighted.get(rec['name'])
        if note:
            add_sample(
                f'key_{rec["name"]}',
                'casos_clave',
                f'Caso revisado · {rec["name"]}',
                storage.read_path(ROOT, rec['serve_path']),
                note,
            )

    for rec in sorted(labeled_ready, key=lambda r: int(r.get('blind_order', 9999))):
        add_sample(
            f'lbl_{rec["item_key"]}',
            'ya_etiquetadas',
            f'#{rec.get("blind_order", "?")} · {rec["name"]}',
            storage.read_path(ROOT, rec['serve_path']),
            f'Ya etiquetada por Vicente ({rec["split"]}, {rec["level_count"]} niveles).',
        )

    # 3. Carpeta 04_Imagenes_para_pruebas (priorizando casos ilustrativos arriba y excluyendo pendientes ciegos)
    folder_map = [
        ('02_Ocupacion_baja', 'occ02', '02_Ocupacion_baja'),
        ('03_Nivel_superior_vacio', 'sup', '03_Nivel_superior_vacio'),
        ('01_Ocupacion_media', 'occ01', '01_Ocupacion_media'),
    ]
    priority_names = ('2810_aq_005', '2810_aq_033', '2710_ma_014', '2710_ma_024', '2710_ma_010')
    try:
        pruebas_dir = storage.collection(ROOT, 'pruebas_ocupacion')
    except FileNotFoundError:
        pruebas_dir = None  # Clon público sin colección privada registrada.
    for folder_name, cat_id, _label in folder_map:
        if pruebas_dir is None:
            continue
        folder = pruebas_dir / folder_name
        if not folder.is_dir():
            continue
        files = sorted(
            [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTS],
            key=lambda p: (0 if any(k in p.name for k in priority_names) else 1, p.name.lower()),
        )
        for p in files:
            sid = f'{cat_id}_{len(samples)}'
            add_sample(sid, cat_id, p.name, p, f'Carpeta {folder_name}')

    cat_labels = {
        'casos_clave': 'Casos clave revisados',
        'ya_etiquetadas': 'Ya etiquetadas en 8096',
        'occ02': '02_Ocupacion_baja',
        'sup': '03_Nivel_superior_vacio',
        'occ01': '01_Ocupacion_media',
    }
    counts = {}
    for s in samples:
        counts[s['category']] = counts.get(s['category'], 0) + 1
    categories = [
        {'id': cid, 'label': f'{cat_labels[cid]} ({counts[cid]})', 'count': counts[cid]}
        for cid in ('casos_clave', 'ya_etiquetadas', 'occ02', 'sup', 'occ01')
        if counts.get(cid, 0) > 0
    ]

    by_id = {s['id']: s for s in samples}
    public_list = [{k: v for k, v in s.items() if k != 'path'} for s in samples]
    return {'samples': public_list, 'by_id': by_id, 'categories': categories}


class LineaASandboxEngine:
    """Ejecuta una sola pasada de YOLO best.pt y compara Baseline V3 vs Línea A."""

    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.device = 'cpu'
        self.model_name = 'V3'

    def _ensure_model(self):
        if self.model is not None:
            return self.model, self.device
        os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
        import torch
        from ultralytics import YOLO, settings
        settings.update({'sync': False, 'wandb': False, 'mlflow': False, 'tensorboard': False})
        cfg = json.loads(MODEL_CFG_PATH.read_text(encoding='utf-8'))
        model_path = (ROOT / cfg['model']).resolve()
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        self.model_name = model_path.parent.parent.name
        self.model = YOLO(str(model_path))
        return self.model, self.device

    @staticmethod
    def _render_evidence_image(image: Image.Image, analyzer_rgb: np.ndarray, structures: np.ndarray,
                               feats: list[dict | None], gondola_bounds: tuple | None,
                               detections_a: list[dict], result) -> Image.Image:
        """Visualizar celdas de producto (verde), columnas sin cobertura (rojo) y rieles excluidos (fucsia)."""
        sh, sw = analyzer_rgb.shape[:2]
        prod_map = np.zeros((sh, sw), dtype=bool)
        gap_map = np.zeros((sh, sw), dtype=bool)
        rail_map = np.asarray(structures, dtype=bool)

        for feat in feats:
            if not feat or not feat.get('valid'):
                continue
            bx, by, bw, bh = feat['bounds']
            if bw <= 0 or bh <= 0:
                continue
            x0, y0 = max(0, bx), max(0, by)
            x1, y1 = min(sw, bx + bw), min(sh, by + bh)
            cw, ch = x1 - x0, y1 - y0
            if cw <= 0 or ch <= 0:
                continue
            maps = compute_cell_maps(feat, gondola_bounds)
            hyb_cells = (maps['hyb_ev'] & maps['body']).astype(np.uint8)
            prod_patch = cv2.resize(hyb_cells, (bw, bh), interpolation=cv2.INTER_NEAREST)[
                y0 - by:y0 - by + ch, x0 - bx:x0 - bx + cw
            ] > 0
            prod_map[y0:y1, x0:x1] |= prod_patch

            # Marcar columnas vacías dentro de la zona de soporte que no quedan cubiertas
            empty_cols = (maps['valid_cols'] & (~maps['col_covered_full']))[None, :]
            gap_cells = (empty_cols & maps['support']).astype(np.uint8)
            gap_patch = cv2.resize(gap_cells, (bw, bh), interpolation=cv2.INTER_NEAREST)[
                y0 - by:y0 - by + ch, x0 - bx:x0 - bx + cw
            ] > 0
            gap_map[y0:y1, x0:x1] |= (gap_patch & (~prod_patch))

        gap_map &= ~prod_map

        # Llevar mapa a resolución original para dibujar polígonos/badges consistentes
        w_orig, h_orig = image.size
        base_arr = np.asarray(image).astype(np.float32) * 0.78
        if prod_map.any():
            m_prod = cv2.resize(prod_map.astype(np.uint8), (w_orig, h_orig), interpolation=cv2.INTER_NEAREST) > 0
            base_arr[m_prod] = 0.55 * base_arr[m_prod] + 0.45 * np.array([34, 197, 94], dtype=np.float32)
        if gap_map.any():
            m_gap = cv2.resize(gap_map.astype(np.uint8), (w_orig, h_orig), interpolation=cv2.INTER_NEAREST) > 0
            base_arr[m_gap] = 0.50 * base_arr[m_gap] + 0.50 * np.array([239, 68, 68], dtype=np.float32)
        if rail_map.any():
            m_rail = cv2.resize(rail_map.astype(np.uint8), (w_orig, h_orig), interpolation=cv2.INTER_NEAREST) > 0
            base_arr[m_rail] = 0.40 * base_arr[m_rail] + 0.60 * np.array([192, 38, 211], dtype=np.float32)

        canvas = Image.fromarray(np.clip(base_arr, 0, 255).astype(np.uint8))
        annotated_ev, _ = draw_result(canvas, result, measurements=detections_a)
        return annotated_ev

    def analyze_bytes(self, image_bytes: bytes, confidence: float = 0.60, threshold_pct: float = CALIBRATED_THRESHOLD_PCT) -> dict:
        if not (isinstance(confidence, (int, float)) and math.isfinite(confidence) and 0.25 <= confidence <= 0.99):
            raise ValueError('La confianza debe estar entre 0,25 y 0,99.')
        if not (isinstance(threshold_pct, (int, float)) and math.isfinite(threshold_pct) and 10.0 <= threshold_pct <= 90.0):
            raise ValueError('El umbral debe estar entre 10 % y 90 %.')

        image = read_photo(image_bytes)
        original_rgb = np.asarray(image).copy()

        with self.lock:
            t0 = time.perf_counter()
            model, device = self._ensure_model()
            result = model.predict(
                image, imgsz=640, conf=float(confidence), iou=0.7,
                retina_masks=True, device=device, verbose=False, save=False,
            )[0]

            _, base_detections = draw_result(image, result)
            masks = result.masks.data.cpu().numpy() if result.masks is not None else []
            if getattr(result, 'boxes', None) is not None and len(masks):
                order = spatial_order(result.boxes.xyxy.cpu().tolist())
                ordered_masks = [(masks[i] > 0.5).astype('uint8') for i in order if i < len(masks)]
            else:
                ordered_masks = []

            # 1. Baseline actual V3 (umbral 30 %)
            analyzer = Analyzer(original_rgb, version='v2', front_mode=True)
            dets_b = deepcopy(base_detections)
            for idx, det in enumerate(dets_b):
                mask = ordered_masks[idx] if idx < len(ordered_masks) else None
                det['occupancy'] = analyzer.analyze(mask, state=det['state'])
                est_b = occupancy_estimate(det['occupancy'], version='v2')
                if est_b.get('pct') is not None and est_b.get('state') != 'revisar':
                    est_b = {**est_b, 'label': f"{est_b['label']} · {est_b['pct']:.0f}%"}
                det['occupancy_estimate'] = est_b
            apply_scope(dets_b, image.width, image.height)

            # 2. Prototipo Línea A sobre las mismas máscaras
            feats = [extract_cell_features(analyzer, m) for m in ordered_masks]
            g_bounds = gondola_feature_bounds([f for f in feats if f is not None])
            dets_a = deepcopy(base_detections)
            for idx, det in enumerate(dets_a):
                feat = feats[idx] if idx < len(feats) else None
                res_a = score_level_from_features(
                    feat,
                    g_bounds,
                    threshold_pct=float(threshold_pct),
                    near_frame=bool(det.get('near_frame')),
                    apply_scope_rule=True,
                )
                det['linea_a'] = res_a
                short_label = (res_a['label'] if res_a['state'] == 'revisar' or res_a.get('pct') is None
                               else f"{res_a['label']} · {res_a['pct']:.0f}%")
                det['occupancy_estimate'] = {
                    'pct': res_a.get('pct'),
                    'state': res_a['state'],
                    'label': short_label,
                    'color': res_a['color'],
                }

            img_baseline, _ = draw_result(image, result, measurements=dets_b)
            img_linea_a, _ = draw_result(image, result, measurements=dets_a)
            img_evidence = self._render_evidence_image(
                image, analyzer.rgb, analyzer.structures, feats, g_bounds, dets_a, result
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)

        def gondola_verdict(dets):
            sts = [d['occupancy_estimate']['state'] for d in dets]
            if not sts:
                return 'sin_niveles'
            if any(s == 'reponer' for s in sts):
                return 'reponer'
            if any(s == 'revisar' for s in sts):
                return 'revisar'
            if all(s == 'suficiente' for s in sts):
                return 'suficiente'
            return 'revisar'

        levels_summary = []
        changed_count = 0
        for db, da in zip(dets_b, dets_a):
            eb = db['occupancy_estimate']
            ob = db['occupancy']
            la = da['linea_a']
            changed = eb['state'] != la['state']
            if changed:
                changed_count += 1
            levels_summary.append({
                'id': da['id'],
                'confidence': round(da['confidence'], 3),
                'near_frame': bool(da['near_frame']),
                'changed': changed,
                'baseline': {
                    'state': eb['state'],
                    'label': eb['label'],
                    'pct': eb.get('pct'),
                    'front_signal_pct': ob.get('front_signal_pct'),
                    'combined_signal_pct': ob.get('combined_signal_pct'),
                    'signal_pattern': ob.get('signal_pattern'),
                },
                'linea_a': {
                    'state': la['state'],
                    'label': da['occupancy_estimate']['label'],
                    'pct': la.get('pct'),
                    'fill_pct': la.get('fill_pct'),
                    'max_gap_pct': la.get('max_gap_pct'),
                    'front_hyb_pct': la.get('front_hyb_pct'),
                    'signal_pattern': la.get('signal_pattern'),
                    'review_reason': la.get('review_reason'),
                },
            })

        return {
            'ok': True,
            'width': image.width,
            'height': image.height,
            'device': 'GPU' if device == 0 else 'CPU',
            'model_name': self.model_name,
            'elapsed_ms': elapsed_ms,
            'confidence': float(confidence),
            'threshold_pct': float(threshold_pct),
            'level_count': len(levels_summary),
            'changed_levels': changed_count,
            'gondola_baseline': gondola_verdict(dets_b),
            'gondola_linea_a': gondola_verdict(dets_a),
            'levels': levels_summary,
            'images': {
                'original': _pil_to_data_url(image, quality=84),
                'baseline': _pil_to_data_url(img_baseline, quality=86),
                'linea_a': _pil_to_data_url(img_linea_a, quality=86),
                'evidence': _pil_to_data_url(img_evidence, quality=84),
            },
        }


class SandboxHandler(BaseHTTPRequestHandler):
    def local_request(self):
        host = self.headers.get('Host', '')
        allowed = {f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'}
        origin = self.headers.get('Origin')
        return host in allowed and (origin is None or origin == f'http://{host}')

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
            return self.send({'error': 'Solo se permite acceso local.'}, 403)
        path = urlparse(self.path).path
        if path == '/':
            return self.send((HERE / 'interfaz_visor_linea_a.html').read_bytes(), content_type='text/html; charset=utf-8')
        if path in ('/favicon.ico', '/favicon.svg'):
            svg = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
                   b'<circle cx="16" cy="16" r="15" fill="#1d6ee8"/>'
                   b'<path d="M7 10h18M7 16h18M7 22h18" stroke="#f5b82e" stroke-width="2.6" stroke-linecap="round"/></svg>')
            return self.send(svg, content_type='image/svg+xml')
        if path == '/api/samples':
            cat = build_sample_catalog()
            return self.send({
                'samples': cat['samples'],
                'categories': cat['categories'],
                'default_threshold_pct': CALIBRATED_THRESHOLD_PCT,
            })
        return self.send({'error': 'Ruta no disponible.'}, 404)

    def do_POST(self):
        if not self.local_request():
            return self.send({'error': 'Origen no autorizado.'}, 403)
        if urlparse(self.path).path != '/api/analyze':
            return self.send({'error': 'Ruta no disponible.'}, 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_UPLOAD_JSON_BYTES:
                return self.send({'error': 'Carga fuera de límite (máx 10 MB por foto).'}, 413)
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            if not isinstance(payload, dict):
                return self.send({'error': 'Formato JSON inválido.'}, 400)
            confidence = float(payload.get('confidence', 0.60))
            threshold_pct = float(payload.get('threshold_pct', CALIBRATED_THRESHOLD_PCT))

            sample_id = payload.get('sample_id')
            if sample_id:
                entry = build_sample_catalog()['by_id'].get(sample_id)
                if not entry:
                    return self.send({'error': 'Muestra no encontrada.'}, 404)
                raw_bytes = Path(entry['path']).read_bytes()
                title = entry['title']
                note = entry.get('note', '')
            else:
                b64 = payload.get('image_base64', '')
                if not isinstance(b64, str) or not b64:
                    return self.send({'error': 'Falta imagen o identificador de muestra.'}, 400)
                if ',' in b64 and b64.startswith('data:'):
                    b64 = b64.split(',', 1)[1]
                raw_bytes = base64.b64decode(b64, validate=True)
                title = str(payload.get('filename') or 'Foto subida')[:120]
                note = 'Imagen subida por el usuario.'

            result = self.server.engine.analyze_bytes(raw_bytes, confidence=confidence, threshold_pct=threshold_pct)
            result['title'] = title
            result['note'] = note
            return self.send(result)
        except (ValueError, TypeError, json.JSONDecodeError) as err:
            return self.send({'error': str(err)}, 400)
        except Exception as err:  # pragma: no cover - protección genérica en hilo HTTP
            return self.send({'error': f'Error interno de análisis: {err}'}, 500)

    def log_message(self, *_):
        pass


def pick_free_port(preferred: int = 8097) -> int:
    for candidate in range(preferred, preferred + 15):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('127.0.0.1', candidate)) != 0:
                return candidate
    return preferred


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8097)
    parser.add_argument('--open', action='store_true', help='Abrir navegador automáticamente')
    parser.add_argument('--check', action='store_true', help='Verificar catálogo y motor sin levantar HTTP')
    args = parser.parse_args()

    cat = build_sample_catalog()
    engine = LineaASandboxEngine()
    if args.check:
        engine._ensure_model()
        sample_res = None
        if cat['samples']:
            first_path = Path(cat['by_id'][cat['samples'][0]['id']]['path'])
            sample_res = engine.analyze_bytes(first_path.read_bytes())
        print(json.dumps({
            'check': 'ok',
            'samples_count': len(cat['samples']),
            'device': 'GPU' if engine.device == 0 else 'CPU',
            'sample_levels': sample_res['level_count'] if sample_res else 0,
            'sample_elapsed_ms': sample_res['elapsed_ms'] if sample_res else None,
        }, ensure_ascii=False, indent=2))
        return

    engine._ensure_model()
    port = pick_free_port(args.port)
    server = ThreadingHTTPServer(('127.0.0.1', port), SandboxHandler)
    server.engine = engine
    url = f'http://127.0.0.1:{port}'
    print(f'Visor Prototipo Línea A activo en: {url} (dispositivo: {"GPU" if engine.device == 0 else "CPU"})', flush=True)
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
