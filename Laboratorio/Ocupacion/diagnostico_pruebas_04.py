"""Diagnóstico end-to-end (solo lectura) de Walmart Visión V3 sobre 04_Imagenes_para_pruebas.

Evalúa el modelo oficial V3 (best.pt) y el estimador actual (ocupacion_paulo v2
con front_mode=True y vision_v3.apply_scope) sobre las 281 variantes de
E:\\Datasets Walmart\\04_Imagenes_para_pruebas y sus 97 originales, separando
estrictamente los 85 originales nunca vistos en train/val de los 12 de val.

No modifica imágenes fuente, CVAT, pesos ni el conjunto de test reservado.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
import almacenamiento_datos as storage
sys.path.insert(0, str(ROOT / 'Aplicacion'))

from ocupacion_paulo import Analyzer
from presentacion_niveles import draw_result, occupancy_estimate, spatial_order
from vision_v3 import apply_scope

PRUEBAS_DIR = storage.collection(ROOT, 'pruebas_ocupacion')
CLASIFICACION_CSV = storage.collection(ROOT, 'clasificacion_original')
INVENTARIO_CTRL = storage.collection(ROOT, 'derivados_ocupacion') / '_control/inventario.json'
PROMPTS_CTRL = storage.collection(ROOT, 'derivados_ocupacion') / '_control/prompts_completos.json'
MODEL_CONFIG_PATH = ROOT / '.config-modelo/version_actual_v3.json'
OUT_DIR = ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107/diagnostico_04'

WORD_NUMS = {'THREE': 3, 'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7}


def parse_expected_levels(spec_text: str):
    if not spec_text:
        return None
    m = re.search(r'EXACTLY\s+(\d+|THREE|FOUR|FIVE|SIX|SEVEN)\b', spec_text, flags=re.IGNORECASE)
    if not m:
        return None
    tok = m.group(1).upper()
    return int(tok) if tok.isdigit() else WORD_NUMS.get(tok)


def load_metadata():
    index_data = json.loads((PRUEBAS_DIR / 'INDICE.json').read_text(encoding='utf-8-sig'))
    csv_rows = {}
    with CLASIFICACION_CSV.open('r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            csv_rows[row['destino']] = row

    inv_by_source = {}
    if INVENTARIO_CTRL.is_file():
        for row in json.loads(INVENTARIO_CTRL.read_text(encoding='utf-8-sig')):
            inv_by_source[row['source']] = row['id']

    specs = {}
    if PROMPTS_CTRL.is_file():
        prompts_json = json.loads(PROMPTS_CTRL.read_text(encoding='utf-8-sig'))
        specs = prompts_json.get('specs', {})

    by_orig = defaultdict(list)
    for item in index_data:
        by_orig[item['original']].append(item)

    tasks = []
    for orig_path, variants in sorted(by_orig.items()):
        meta_csv = csv_rows.get(orig_path, {})
        in_val = str(meta_csv.get('usada_validacion', '')).strip().lower() == 'true'
        in_train = str(meta_csv.get('usada_entrenamiento', '')).strip().lower() == 'true'
        ctrl_id = inv_by_source.get(orig_path)
        spec_text = specs.get(str(ctrl_id), '') if ctrl_id is not None else ''
        expected_levels = parse_expected_levels(spec_text)
        already_empty_top = ('already empty' in spec_text.lower() or 'highest physical shelf is already empty' in spec_text.lower())

        common = {
            'original_path': orig_path,
            'original_rel': meta_csv.get('relativa', Path(orig_path).name),
            'locale': Path(meta_csv.get('relativa', Path(orig_path).name)).parts[0] if meta_csv.get('relativa') else Path(orig_path).parent.name,
            'usada_entrenamiento': in_train,
            'usada_validacion': in_val,
            'ctrl_id': ctrl_id,
            'expected_levels': expected_levels,
            'already_empty_top_in_original': already_empty_top,
        }
        tasks.append({
            **common,
            'kind': 'original',
            'tipo': 'original',
            'image_path': str(storage.legacy_external(ROOT, orig_path)),
            'rel_image': Path(orig_path).name,
            'sha256_expected': meta_csv.get('sha256'),
        })
        for v in sorted(variants, key=lambda x: x['tipo']):
            tasks.append({
                **common,
                'kind': 'variant',
                'tipo': v['tipo'],
                'image_path': str(PRUEBAS_DIR / v['imagen']),
                'rel_image': v['imagen'],
                'sha256_expected': v.get('sha256'),
            })
    return tasks


def load_rgb_pil(path: Path):
    with Image.open(path) as raw:
        rgba = ImageOps.exif_transpose(raw).convert('RGBA')
        image = Image.new('RGB', rgba.size, 'white')
        image.paste(rgba, mask=rgba.getchannel('A'))
        image.thumbnail((4096, 4096))
        return image


def run_diagnostic(confidence=0.60, limit=None):
    import os
    os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
    import torch
    from ultralytics import YOLO, settings
    settings.update({'sync': False, 'wandb': False, 'mlflow': False, 'tensorboard': False})

    cfg = json.loads(MODEL_CONFIG_PATH.read_text(encoding='utf-8'))
    model_path = (ROOT / cfg['model']).resolve()
    actual_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if actual_sha != cfg['sha256']:
        raise ValueError(f'SHA-256 del modelo no coincide: {actual_sha} != {cfg["sha256"]}')

    device = 0 if torch.cuda.is_available() else 'cpu'
    model = YOLO(str(model_path))
    tasks = load_metadata()
    if limit:
        tasks = tasks[:limit]

    results = []
    t0 = time.perf_counter()
    for idx, task in enumerate(tasks, 1):
        img_path = Path(task['image_path'])
        pil_img = load_rgb_pil(img_path)
        original_rgb = np.asarray(pil_img).copy()

        res = model.predict(
            pil_img, imgsz=640, conf=float(confidence), iou=0.7,
            retina_masks=True, device=device, verbose=False, save=False,
        )[0]
        _, detections = draw_result(pil_img, res)

        analyzer = Analyzer(original_rgb, version='v2', front_mode=True)
        masks = res.masks.data.cpu().numpy() if res.masks is not None else []
        if getattr(res, 'boxes', None) is not None and len(masks):
            order = spatial_order(res.boxes.xyxy.cpu().tolist())
            masks = [masks[i] for i in order if i < len(masks)]

        for lv_idx, det in enumerate(detections):
            mask = (masks[lv_idx] > 0.5).astype('uint8') if lv_idx < len(masks) else None
            occ = analyzer.analyze(mask, state=det['state'])
            est_raw = occupancy_estimate(occ, 'v2')
            det['occupancy'] = occ
            det['occupancy_raw_state'] = est_raw['state']
            det['occupancy_estimate'] = dict(est_raw)

        apply_scope(detections, pil_img.width, pil_img.height)

        levels_out = []
        for det in detections:
            occ = det['occupancy']
            est_raw = det['occupancy_raw_state']
            est_final = det['occupancy_estimate']['state']
            levels_out.append({
                'id': det['id'],
                'confidence': round(det['confidence'], 4),
                'near_frame': bool(det['near_frame']),
                'raw_state': est_raw,
                'final_state': est_final,
                'final_label': det['occupancy_estimate']['label'],
                'front_signal_pct': occ.get('front_signal_pct'),
                'combined_signal_pct': occ.get('combined_signal_pct'),
                'area_signal_pct': occ.get('area_signal_pct'),
                'width_signal_pct': occ.get('width_signal_pct'),
                'signal_pattern': occ.get('signal_pattern'),
                'review_required': bool(occ.get('review_required')),
                'upper_half_signal_share': occ.get('upper_half_signal_share'),
                'central_evidence_fraction': occ.get('central_evidence_fraction'),
                'lower_edge_evidence_fraction': occ.get('lower_edge_evidence_fraction'),
            })

        raw_states = [l['raw_state'] for l in levels_out]
        final_states = [l['final_state'] for l in levels_out]
        front_vals = [l['front_signal_pct'] for l in levels_out if l['front_signal_pct'] is not None]
        comb_vals = [l['combined_signal_pct'] for l in levels_out if l['combined_signal_pct'] is not None]

        g_raw = ('reponer' if any(s == 'reponer' for s in raw_states) else
                 'revisar' if (not raw_states or any(s == 'revisar' for s in raw_states)) else 'suficiente')
        g_final = ('reponer' if any(s == 'reponer' for s in final_states) else
                   'revisar' if (not final_states or any(s == 'revisar' for s in final_states)) else 'suficiente')

        results.append({
            'tipo': task['tipo'],
            'kind': task['kind'],
            'rel_image': task['rel_image'],
            'original_path': task['original_path'],
            'original_rel': task['original_rel'],
            'locale': task['locale'],
            'usada_validacion': task['usada_validacion'],
            'expected_levels': task['expected_levels'],
            'detected_levels': len(levels_out),
            'already_empty_top_in_original': task['already_empty_top_in_original'],
            'width': pil_img.width,
            'height': pil_img.height,
            'mean_front_pct': round(float(np.mean(front_vals)), 2) if front_vals else None,
            'min_front_pct': round(float(np.min(front_vals)), 2) if front_vals else None,
            'mean_combined_pct': round(float(np.mean(comb_vals)), 2) if comb_vals else None,
            'gondola_raw_state': g_raw,
            'gondola_final_state': g_final,
            'levels': levels_out,
        })
        if idx % 50 == 0 or idx == len(tasks):
            print(f'Procesadas {idx}/{len(tasks)} imágenes ({time.perf_counter() - t0:.1f}s)', flush=True)

    summary = build_summary(results, confidence, 'GPU' if device == 0 else 'CPU', time.perf_counter() - t0)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / 'resultados_completos.json').write_text(
        json.dumps({'summary': summary, 'images': results}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    (OUT_DIR / 'resumen.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary, results


def _stats_bucket(items):
    if not items:
        return {}
    all_levels = [lv for it in items for lv in it['levels']]
    raw_lv_cnt = Counter(lv['raw_state'] for lv in all_levels)
    fin_lv_cnt = Counter(lv['final_state'] for lv in all_levels)
    g_raw_cnt = Counter(it['gondola_raw_state'] for it in items)
    g_fin_cnt = Counter(it['gondola_final_state'] for it in items)
    fronts = [lv['front_signal_pct'] for lv in all_levels if lv['front_signal_pct'] is not None]
    combs = [lv['combined_signal_pct'] for lv in all_levels if lv['combined_signal_pct'] is not None]
    level_match = [it['detected_levels'] == it['expected_levels'] for it in items if it['expected_levels'] is not None]
    level_under = [it['detected_levels'] < it['expected_levels'] for it in items if it['expected_levels'] is not None]
    level_over = [it['detected_levels'] > it['expected_levels'] for it in items if it['expected_levels'] is not None]

    n_lv = max(1, len(all_levels))
    n_im = max(1, len(items))
    return {
        'images': len(items),
        'levels_detected': len(all_levels),
        'expected_levels_exact_match_pct': round(100 * sum(level_match) / len(level_match), 1) if level_match else None,
        'under_detected_images': sum(level_under) if level_under else 0,
        'over_detected_images': sum(level_over) if level_over else 0,
        'front_signal_mean': round(float(np.mean(fronts)), 2) if fronts else None,
        'front_signal_median': round(float(np.median(fronts)), 2) if fronts else None,
        'combined_signal_mean': round(float(np.mean(combs)), 2) if combs else None,
        'level_raw_counts': dict(raw_lv_cnt),
        'level_raw_pct': {k: round(100 * v / n_lv, 1) for k, v in raw_lv_cnt.items()},
        'level_final_counts': dict(fin_lv_cnt),
        'level_final_pct': {k: round(100 * v / n_lv, 1) for k, v in fin_lv_cnt.items()},
        'gondola_raw_counts': dict(g_raw_cnt),
        'gondola_raw_alert_pct': round(100 * g_raw_cnt['reponer'] / n_im, 1),
        'gondola_final_counts': dict(g_fin_cnt),
        'gondola_final_alert_pct': round(100 * g_fin_cnt['reponer'] / n_im, 1),
    }


def _top_shelf_stats(items):
    """Analiza específicamente el nivel más alto en 03_Nivel_superior_vacio."""
    if not items:
        return {}
    raw_cnt = Counter()
    fin_cnt = Counter()
    missing_top_exact = 0
    top_fronts = []
    top_combs = []
    false_sufficient_examples = []
    near_frame_overridden = 0

    for it in items:
        if it['expected_levels'] is not None and it['detected_levels'] < it['expected_levels']:
            missing_top_exact += 1
        if not it['levels']:
            raw_cnt['sin_detecciones'] += 1
            fin_cnt['sin_detecciones'] += 1
            continue
        top = max(it['levels'], key=lambda x: x['id'])
        raw_cnt[top['raw_state']] += 1
        fin_cnt[top['final_state']] += 1
        if top['near_frame'] and top['raw_state'] != top['final_state']:
            near_frame_overridden += 1
        if top['front_signal_pct'] is not None:
            top_fronts.append(top['front_signal_pct'])
        if top['combined_signal_pct'] is not None:
            top_combs.append(top['combined_signal_pct'])
        if top['raw_state'] == 'suficiente' or top['final_state'] == 'suficiente':
            false_sufficient_examples.append({
                'rel_image': it['rel_image'],
                'expected_levels': it['expected_levels'],
                'detected_levels': it['detected_levels'],
                'top_front_pct': top['front_signal_pct'],
                'top_combined_pct': top['combined_signal_pct'],
                'top_raw_state': top['raw_state'],
                'top_final_state': top['final_state'],
                'near_frame': top['near_frame'],
                'signal_pattern': top['signal_pattern'],
            })

    n = len(items)
    false_sufficient_examples.sort(key=lambda x: -(x['top_front_pct'] or 0))
    return {
        'images': n,
        'images_with_fewer_levels_than_expected': missing_top_exact,
        'top_detected_raw_counts': dict(raw_cnt),
        'top_detected_raw_pct': {k: round(100 * v / n, 1) for k, v in raw_cnt.items()},
        'top_detected_final_counts': dict(fin_cnt),
        'top_detected_final_pct': {k: round(100 * v / n, 1) for k, v in fin_cnt.items()},
        'near_frame_overrides_on_top': near_frame_overridden,
        'top_front_mean': round(float(np.mean(top_fronts)), 2) if top_fronts else None,
        'top_front_median': round(float(np.median(top_fronts)), 2) if top_fronts else None,
        'top_combined_mean': round(float(np.mean(top_combs)), 2) if top_combs else None,
        'worst_false_sufficient_top10': false_sufficient_examples[:10],
    }


def _paired_monotonicity(items):
    by_orig = defaultdict(dict)
    for it in items:
        by_orig[it['original_path']][it['tipo']] = it

    pairs_orig_med = []
    pairs_med_low = []
    pairs_orig_low = []
    for orig_path, m in by_orig.items():
        if 'original' in m and 'ocupacion_01' in m:
            f0, f1 = m['original']['mean_front_pct'], m['ocupacion_01']['mean_front_pct']
            if f0 is not None and f1 is not None:
                pairs_orig_med.append((f0, f1))
        if 'ocupacion_01' in m and 'ocupacion_02' in m:
            f1, f2 = m['ocupacion_01']['mean_front_pct'], m['ocupacion_02']['mean_front_pct']
            if f1 is not None and f2 is not None:
                pairs_med_low.append((f1, f2))
        if 'original' in m and 'ocupacion_02' in m:
            f0, f2 = m['original']['mean_front_pct'], m['ocupacion_02']['mean_front_pct']
            if f0 is not None and f2 is not None:
                pairs_orig_low.append((f0, f2))

    def summarize_pair(pairs):
        if not pairs:
            return None
        diffs = [a - b for a, b in pairs]
        drops = sum(1 for d in diffs if d > 0)
        return {
            'n_pairs': len(pairs),
            'decreased_count': drops,
            'decreased_pct': round(100 * drops / len(pairs), 1),
            'mean_drop_pct_pts': round(float(np.mean(diffs)), 2),
        }

    return {
        'original_to_ocupacion_01_media': summarize_pair(pairs_orig_med),
        'ocupacion_01_media_to_ocupacion_02_baja': summarize_pair(pairs_med_low),
        'original_to_ocupacion_02_baja': summarize_pair(pairs_orig_low),
    }


def build_summary(results, confidence, device_label, elapsed_s):
    unseen = [r for r in results if not r['usada_validacion']]
    in_val = [r for r in results if r['usada_validacion']]

    def by_tipo(subset):
        return {
            tipo: _stats_bucket([r for r in subset if r['tipo'] == tipo])
            for tipo in ('original', 'ocupacion_01', 'ocupacion_02', 'superior_vacio')
        }

    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'model': json.loads(MODEL_CONFIG_PATH.read_text(encoding='utf-8'))['run'],
        'confidence': confidence,
        'device': device_label,
        'elapsed_seconds': round(elapsed_s, 1),
        'note': 'Diagnóstico end-to-end (best.pt + ocupacion_paulo v2 front_mode=True + apply_scope). Separación estricta de los 85 originales nunca usados en train/val vs 12 de val.',
        'unseen_85_families': {
            'by_tipo': by_tipo(unseen),
            'top_shelf_03_superior_vacio': _top_shelf_stats([r for r in unseen if r['tipo'] == 'superior_vacio']),
            'paired_monotonicity': _paired_monotonicity(unseen),
        },
        'val_12_families': {
            'by_tipo': by_tipo(in_val),
            'top_shelf_03_superior_vacio': _top_shelf_stats([r for r in in_val if r['tipo'] == 'superior_vacio']),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confidence', type=float, default=0.60)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()
    summary, _ = run_diagnostic(confidence=args.confidence, limit=args.limit)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
