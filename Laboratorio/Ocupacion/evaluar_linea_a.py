"""Evaluar prototipo Línea A vs línea base V3 sobre etiquetas humanas (y diag04 opcional).

Uso rápido (solo CPU, sobre imágenes reales y etiquetas humanas guardadas):
    .\\Aplicacion\\.entorno-py312\\Scripts\\python.exe .\\Laboratorio\\Ocupacion\\evaluar_linea_a.py

Calcula métricas comparativas lado a lado (Precisión, Recall automático, F1 y tasa
de revisión por nivel y por góndola), calibrando/reportando la curva de umbral
estrictamente sobre `train` antes de mostrar el desempeño out-of-sample en `val`.
"""
import argparse
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import pickle
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Aplicacion'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ocupacion_paulo import Analyzer  # noqa: E402
from presentacion_niveles import occupancy_estimate  # noqa: E402
from evaluar_linea_base import (  # noqa: E402
    DATA_DIR,
    LABELS_PATH,
    MANIFEST_PATH,
    compute_binary_metrics,
    load_rgb,
    rasterize_polygon,
)
from prototipo_linea_a import (  # noqa: E402
    CALIBRATED_THRESHOLD_PCT,
    analyze_gondola_rgb,
    gondola_feature_bounds,
    score_level_from_features,
)

DEFAULT_OUT = DATA_DIR / 'comparacion_linea_a.json'


def _apply_scope_state(state: str, near_frame: bool, with_scope: bool) -> str:
    return 'revisar' if (with_scope and near_frame) else state


def _train_threshold_analysis(train_records: list[dict], with_scope: bool) -> dict:
    """Derivar rango de separación y curva F1 estrictamente sobre `split == 'train'`."""
    pos_scores = [r['pct'] for r in train_records if r['gt_alert'] and r['pct'] is not None]
    neg_scores = [r['pct'] for r in train_records if (not r['gt_alert']) and r['pct'] is not None]

    max_pos = max(pos_scores) if pos_scores else None
    min_neg = min(neg_scores) if neg_scores else None
    midpoint = round((max_pos + min_neg) / 2.0, 2) if (max_pos is not None and min_neg is not None) else None

    sweep = []
    for thr in range(30, 68, 2):
        pairs = []
        for r in train_records:
            if with_scope and r['near_frame']:
                st = 'revisar'
            elif r['pct'] >= thr and r['review_above_thr']:
                st = 'revisar'
            else:
                st = 'reponer' if r['pct'] < thr else 'suficiente'
            pairs.append((r['gt_alert'], st))
        m = compute_binary_metrics(pairs)
        sweep.append({
            'threshold_pct': thr,
            'f1_pct': m.get('f1_automatico_pct'),
            'precision_pct': m.get('precision_pct'),
            'recall_pct': m.get('recall_automatico_pct'),
            'tp': m.get('tp_alerta'),
            'fp': m.get('fp_alerta'),
            'fn': m.get('fn_falso_suficiente'),
        })

    return {
        'train_levels': len(train_records),
        'train_positives': len(pos_scores),
        'train_negatives': len(neg_scores),
        'max_train_positive_pct': round(max_pos, 2) if max_pos is not None else None,
        'min_train_negative_pct': round(min_neg, 2) if min_neg is not None else None,
        'zero_overlap': bool(max_pos is not None and min_neg is not None and max_pos < min_neg),
        'midpoint_pct': midpoint,
        'sweep': sweep,
    }


def evaluate_human_comparison(manifest: dict, saved_items: dict, threshold_pct: float, with_scope: bool) -> dict:
    """Evaluar línea base V3 vs Línea A directamente desde las imágenes y polígonos CVAT."""
    base_lv, a_lv = [], []
    base_gd, a_gd = [], []
    a_train_raw = []

    for rec in manifest['images']:
        entry = saved_items.get(rec['item_key'])
        if not entry or not entry.get('levels'):
            continue
        labels_map = entry['levels']
        if not any(v in ('suficiente', 'baja_disponibilidad', 'vacio') for v in labels_map.values()):
            continue

        rgb = load_rgb(rec)
        h, w = rgb.shape[:2]
        masks = [rasterize_polygon(lv['polygon'], w, h) for lv in rec['levels']]
        near_frames = [
            any(px <= 2 or py <= 2 or px >= w - 3 or py >= h - 3 for px, py in lv['polygon'])
            for lv in rec['levels']
        ]

        analyzer_base = Analyzer(rgb, version='v2', front_mode=True)
        linea_a_results = analyze_gondola_rgb(
            rgb,
            masks,
            threshold_pct=threshold_pct,
            near_frames=near_frames,
            apply_scope_rule=with_scope,
        )

        g_gt = []
        g_b_pr, g_a_pr = [], []
        for lv, mask, nf, res_a in zip(rec['levels'], masks, near_frames, linea_a_results):
            lid = str(lv['level_id'])
            gt_label = labels_map.get(lid)
            meas_b = analyzer_base.analyze(mask)
            est_b = occupancy_estimate(meas_b, version='v2')
            st_b = est_b['state'] if est_b['state'] in ('reponer', 'suficiente') else 'revisar'
            st_b = _apply_scope_state(st_b, nf, with_scope)
            st_a = res_a['state'] if res_a['state'] in ('reponer', 'suficiente') else 'revisar'

            if gt_label in ('suficiente', 'baja_disponibilidad', 'vacio'):
                gt_alert = gt_label in ('baja_disponibilidad', 'vacio')
                common = {
                    'split': rec['split'],
                    'origen': rec['origen'],
                    'grupo_escena': rec['grupo_escena'],
                    'imagen_id': rec['imagen_id'],
                    'name': rec['name'],
                    'level_id': lv['level_id'],
                    'gt_label': gt_label,
                    'gt_alert': gt_alert,
                    'near_frame': nf,
                }
                base_lv.append({
                    **common,
                    'pred_state': st_b,
                    'pct': meas_b.get('front_signal_pct'),
                    'signal_pattern': meas_b.get('signal_pattern'),
                })
                a_lv.append({
                    **common,
                    'pred_state': st_a,
                    'pct': res_a.get('pct'),
                    'max_gap_pct': res_a.get('max_gap_pct'),
                    'fill_pct': res_a.get('fill_pct'),
                    'signal_pattern': res_a.get('signal_pattern'),
                })
                if rec['split'] == 'train':
                    # Guardar si el filtro espacial pediría revisión suponiendo pct >= thr
                    review_if_above = (res_a.get('upper_share', 0.0) >= 0.88 or
                                       res_a.get('center_fill', 1.0) < 0.25 or
                                       bool(res_a.get('hollow_banner')))
                    a_train_raw.append({
                        'gt_alert': gt_alert,
                        'pct': res_a['pct'],
                        'near_frame': nf,
                        'review_above_thr': review_if_above,
                    })
                g_gt.append(gt_alert)
                g_b_pr.append(st_b)
                g_a_pr.append(st_a)

        if len(labels_map) == rec['level_count'] and g_gt:
            gt_any = any(g_gt)
            meta_g = {
                'split': rec['split'],
                'origen': rec['origen'],
                'grupo_escena': rec['grupo_escena'],
                'imagen_id': rec['imagen_id'],
                'name': rec['name'],
                'gt_alert': gt_any,
            }
            base_gd.append({
                **meta_g,
                'pred_state': ('reponer' if any(s == 'reponer' for s in g_b_pr) else
                               'revisar' if any(s == 'revisar' for s in g_b_pr) else 'suficiente'),
            })
            a_gd.append({
                **meta_g,
                'pred_state': ('reponer' if any(s == 'reponer' for s in g_a_pr) else
                               'revisar' if any(s == 'revisar' for s in g_a_pr) else 'suficiente'),
            })

    subsets = {
        'train_all': lambda r: r['split'] == 'train',
        'train_real': lambda r: r['split'] == 'train' and r['origen'] == 'real',
        'val_real': lambda r: r['split'] == 'val' and r['origen'] == 'real',
        'val_sintetica': lambda r: r['split'] == 'val' and r['origen'] == 'sintetica',
        'val_all': lambda r: r['split'] == 'val',
    }

    def summarize(records):
        return {
            name: compute_binary_metrics([(r['gt_alert'], r['pred_state']) for r in records if fn(r)])
            for name, fn in subsets.items()
        }

    def error_list(records):
        return {
            'false_positives': [
                {'split': r['split'], 'origen': r['origen'], 'name': r['name'], 'level_id': r['level_id'],
                 'gt': r['gt_label'], 'pct': r['pct'], 'pattern': r['signal_pattern']}
                for r in records if (not r['gt_alert']) and r['pred_state'] == 'reponer'
            ],
            'false_negatives': [
                {'split': r['split'], 'origen': r['origen'], 'name': r['name'], 'level_id': r['level_id'],
                 'gt': r['gt_label'], 'pct': r['pct'], 'pattern': r['signal_pattern']}
                for r in records if r['gt_alert'] and r['pred_state'] == 'suficiente'
            ],
            'revisar': [
                {'split': r['split'], 'origen': r['origen'], 'name': r['name'], 'level_id': r['level_id'],
                 'gt': r['gt_label'], 'pct': r['pct'], 'pattern': r['signal_pattern']}
                for r in records if r['pred_state'] == 'revisar'
            ],
        }

    return {
        'n_labeled_levels': len(a_lv),
        'n_complete_gondolas': len(a_gd),
        'with_scope_near_frame': with_scope,
        'threshold_pct_linea_a': threshold_pct,
        'train_threshold_calibration': _train_threshold_analysis(a_train_raw, with_scope),
        'baseline_v3': {
            'threshold_pct': 30,
            'by_level': summarize(base_lv),
            'by_gondola': summarize(base_gd),
            'errors': error_list(base_lv),
        },
        'linea_a': {
            'threshold_pct': threshold_pct,
            'by_level': summarize(a_lv),
            'by_gondola': summarize(a_gd),
            'errors': error_list(a_lv),
        },
    }


def evaluate_cached_diag04(cache_path: Path, threshold_pct: float) -> dict:
    """Evaluar baseline vs Línea A sobre `04_Imagenes_para_pruebas` y controles usando caché."""
    with gzip.open(cache_path, 'rb') as f:
        cache = pickle.load(f)

    def summarize_diag_group(records):
        buckets = {}
        for tipo in ('original', 'ocupacion_01', 'ocupacion_02', 'superior_vacio'):
            imgs = [r for r in records if r['tipo'] == tipo]
            if not imgs:
                continue
            b_lv = {'reponer': 0, 'suficiente': 0, 'revisar': 0}
            a_lv = {'reponer': 0, 'suficiente': 0, 'revisar': 0}
            b_gd = {'reponer': 0, 'suficiente': 0, 'revisar': 0}
            a_gd = {'reponer': 0, 'suficiente': 0, 'revisar': 0}
            b_top = {'reponer': 0, 'suficiente': 0, 'revisar': 0}
            a_top = {'reponer': 0, 'suficiente': 0, 'revisar': 0}

            for img in imgs:
                valid_lvs = [l for l in img['levels'] if l.get('valid')]
                bounds = gondola_feature_bounds(valid_lvs)
                b_sts, a_sts = [], []
                for lv in valid_lvs:
                    st_b = lv['baseline_final_state']
                    res_a = score_level_from_features(
                        lv, bounds, threshold_pct=threshold_pct,
                        near_frame=lv['near_frame'], apply_scope_rule=True,
                    )
                    st_a = res_a['state']
                    if st_b in b_lv:
                        b_lv[st_b] += 1
                    if st_a in a_lv:
                        a_lv[st_a] += 1
                    b_sts.append((lv['level_id'], st_b))
                    a_sts.append((lv['level_id'], st_a))

                def g_agg(sts):
                    vals = [s for _, s in sts]
                    return ('reponer' if any(s == 'reponer' for s in vals) else
                            'revisar' if any(s == 'revisar' for s in vals) else 'suficiente')

                b_gd[g_agg(b_sts)] += 1
                a_gd[g_agg(a_sts)] += 1
                if tipo == 'superior_vacio' and b_sts and (
                    img['expected_levels'] is None or len(valid_lvs) == img['expected_levels']
                ):
                    b_top[max(b_sts, key=lambda x: x[0])[1]] += 1
                    a_top[max(a_sts, key=lambda x: x[0])[1]] += 1

            entry = {
                'images': len(imgs),
                'baseline_v3': {'levels': b_lv, 'gondolas': b_gd},
                'linea_a': {'levels': a_lv, 'gondolas': a_gd},
            }
            if sum(b_top.values()):
                entry['baseline_v3']['top_exact'] = b_top
                entry['linea_a']['top_exact'] = a_top
            buckets[tipo] = entry
        return buckets

    unseen = [r for r in cache['diag04'] if not r['usada_validacion']]
    unseen_non_oh = [r for r in unseen if r['locale'] != 'Ohiggins']
    val12 = [r for r in cache['diag04'] if r['usada_validacion']]

    ctrl_res = {}
    for img in cache.get('controls', []):
        valid_lvs = [l for l in img['levels'] if l.get('valid')]
        bounds = gondola_feature_bounds(valid_lvs)
        top = max(valid_lvs, key=lambda x: x['level_id'])
        res_a = score_level_from_features(top, bounds, threshold_pct=threshold_pct, near_frame=top['near_frame'], apply_scope_rule=True)
        ctrl_res[img['name']] = {
            'level_id': top['level_id'],
            'baseline_v3': {'state': top['baseline_final_state'], 'pct': top['baseline_occ'].get('front_signal_pct'), 'pattern': top['baseline_occ'].get('signal_pattern')},
            'linea_a': {'state': res_a['state'], 'pct': res_a['pct'], 'pattern': res_a['signal_pattern']},
        }

    return {
        'unseen_85_families_all': summarize_diag_group(unseen),
        'unseen_non_ohiggins_originals_only': summarize_diag_group([r for r in unseen_non_oh if r['tipo'] == 'original']),
        'val_12_families': summarize_diag_group(val12),
        'controls_top': ctrl_res,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threshold', type=float, default=CALIBRATED_THRESHOLD_PCT, help='Umbral de reposición Línea A (%).')
    parser.add_argument('--with-scope', action='store_true', help='Aplicar regla de recorte near_frame -> revisar igual que en inferencia.')
    parser.add_argument('--diag04-cache', type=Path, default=None, help='Caché opcional .pkl.gz para resumir 04_Imagenes_para_pruebas y controles.')
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT, help='Archivo JSON de salida.')
    args = parser.parse_args()

    if not LABELS_PATH.is_file():
        raise SystemExit(f'Falta {LABELS_PATH}.')
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    saved = json.loads(LABELS_PATH.read_text(encoding='utf-8')).get('items', {})

    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'human_evaluation': evaluate_human_comparison(manifest, saved, args.threshold, args.with_scope),
    }
    if args.diag04_cache:
        report['diag04_evaluation'] = evaluate_cached_diag04(args.diag04_cache, args.threshold)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
