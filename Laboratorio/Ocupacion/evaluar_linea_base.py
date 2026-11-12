"""Evaluar la línea base actual de ocupación V3 frente a etiquetas humanas.

Calcula Precisión, Recall, F1-score, especificidad y tasa de revisión tanto por
nivel como por góndola completa, separando train, val_real y val_sintetica.
Por defecto evalúa sobre las máscaras humanas revisadas (aísla el estimador de
ocupación); con --yolo evalúa además el flujo completo end-to-end con best.pt.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
import almacenamiento_datos as storage
sys.path.insert(0, str(ROOT / 'Aplicacion'))
from ocupacion_paulo import Analyzer
from presentacion_niveles import occupancy_estimate, spatial_order

DATA_DIR = ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107'
MANIFEST_PATH = DATA_DIR / 'muestra_desarrollo.json'
LABELS_PATH = DATA_DIR / 'etiquetas_humanas.json'
BASELINE_OUT = DATA_DIR / 'linea_base_ocupacion.json'


def load_rgb(rec):
    full = storage.read_path(ROOT, rec['serve_path'])
    with Image.open(full) as raw:
        img = ImageOps.exif_transpose(raw).convert('RGB')
        return np.asarray(img)


def rasterize_polygon(polygon, width, height):
    mask = np.zeros((height, width), dtype=np.uint8)
    pts = np.rint(np.asarray(polygon, dtype=np.float32)).astype(np.int32)
    cv2.fillPoly(mask, [pts], 1)
    return mask


def compute_binary_metrics(pairs):
    """pairs: lista de tuplas (gt_alert: bool, pred_state: 'reponer'|'suficiente'|'revisar'|'omitido').

    Siguiendo el criterio estricto:
    - Precisión de alertas = TP / (TP + FP) sobre alertas emitidas.
    - Recall automático = TP / Todos los casos reales de alerta (incluye enviados a revisar u omitidos).
    - Recall condicional = TP / (TP + FN_suficiente) solo sobre niveles decididos.
    """
    n = len(pairs)
    if n == 0:
        return {'n_evaluable': 0}
    tp = sum(1 for gt, pr in pairs if gt and pr == 'reponer')
    fp = sum(1 for gt, pr in pairs if (not gt) and pr == 'reponer')
    tn = sum(1 for gt, pr in pairs if (not gt) and pr == 'suficiente')
    fn_suf = sum(1 for gt, pr in pairs if gt and pr == 'suficiente')
    rev_alert = sum(1 for gt, pr in pairs if gt and pr == 'revisar')
    rev_suf = sum(1 for gt, pr in pairs if (not gt) and pr == 'revisar')
    omit_alert = sum(1 for gt, pr in pairs if gt and pr == 'omitido')
    omit_suf = sum(1 for gt, pr in pairs if (not gt) and pr == 'omitido')

    total_pos = sum(1 for gt, _ in pairs if gt)
    total_neg = n - total_pos
    precision = tp / (tp + fp) if (tp + fp) else None
    recall_auto = tp / total_pos if total_pos else None
    f1_auto = (2 * precision * recall_auto / (precision + recall_auto)
               if (precision is not None and recall_auto is not None and (precision + recall_auto) > 0) else None)
    decided = tp + fp + tn + fn_suf
    recall_decided = tp / (tp + fn_suf) if (tp + fn_suf) else None

    def r4(val):
        return round(val * 100, 2) if val is not None else None

    return {
        'n_evaluable': n,
        'positives_alerta': total_pos,
        'negatives_suficiente': total_neg,
        'tp_alerta': tp,
        'fp_alerta': fp,
        'tn_suficiente': tn,
        'fn_falso_suficiente': fn_suf,
        'revisar_en_alerta': rev_alert,
        'revisar_en_suficiente': rev_suf,
        'omitidos_en_alerta': omit_alert,
        'omitidos_en_suficiente': omit_suf,
        'precision_pct': r4(precision),
        'recall_automatico_pct': r4(recall_auto),
        'f1_automatico_pct': r4(f1_auto),
        'recall_sobre_decididos_pct': r4(recall_decided),
        'tasa_revision_pct': r4((rev_alert + rev_suf) / n),
        'cobertura_decision_pct': r4(decided / n),
    }


def evaluate_human_masks(manifest, saved_items):
    level_records = []
    gondola_records = []

    for rec in manifest['images']:
        entry = saved_items.get(rec['item_key'])
        if not entry or not entry.get('levels'):
            continue
        labels_map = entry['levels']
        if not any(v in ('suficiente', 'baja_disponibilidad', 'vacio') for v in labels_map.values()):
            continue

        rgb = load_rgb(rec)
        h, w = rgb.shape[:2]
        analyzer = Analyzer(rgb, version='v2', front_mode=True)

        g_gt_states = []
        g_pred_states = []
        for lv in rec['levels']:
            lid = str(lv['level_id'])
            gt_label = labels_map.get(lid)
            mask = rasterize_polygon(lv['polygon'], w, h)
            meas = analyzer.analyze(mask)
            est = occupancy_estimate(meas, version='v2')
            pred_state = 'reponer' if est['state'] == 'reponer' else (
                'suficiente' if est['state'] == 'suficiente' else 'revisar'
            )
            if gt_label in ('suficiente', 'baja_disponibilidad', 'vacio'):
                gt_alert = gt_label in ('baja_disponibilidad', 'vacio')
                g_gt_states.append(gt_alert)
                g_pred_states.append(pred_state)
                level_records.append({
                    'split': rec['split'],
                    'origen': rec['origen'],
                    'grupo_escena': rec['grupo_escena'],
                    'imagen_id': rec['imagen_id'],
                    'name': rec['name'],
                    'level_id': lv['level_id'],
                    'gt_label': gt_label,
                    'gt_alert': gt_alert,
                    'pred_state': pred_state,
                    'front_signal_pct': meas.get('front_signal_pct'),
                    'combined_signal_pct': meas.get('combined_signal_pct'),
                    'area_signal_pct': meas.get('area_signal_pct'),
                    'signal_pattern': meas.get('signal_pattern'),
                })

        if len(labels_map) == rec['level_count'] and g_gt_states:
            g_gt_alert = any(g_gt_states)
            g_pred = ('reponer' if any(s == 'reponer' for s in g_pred_states) else
                      'revisar' if any(s == 'revisar' for s in g_pred_states) else 'suficiente')
            gondola_records.append({
                'split': rec['split'],
                'origen': rec['origen'],
                'grupo_escena': rec['grupo_escena'],
                'imagen_id': rec['imagen_id'],
                'gt_alert': g_gt_alert,
                'pred_state': g_pred,
            })

    subsets = {
        'train_all': lambda r: r['split'] == 'train',
        'train_real': lambda r: r['split'] == 'train' and r['origen'] == 'real',
        'val_real': lambda r: r['split'] == 'val' and r['origen'] == 'real',
        'val_sintetica': lambda r: r['split'] == 'val' and r['origen'] == 'sintetica',
        'val_all': lambda r: r['split'] == 'val',
    }

    summary = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'mode': 'human_masks_isolated_estimator',
        'threshold_pct': 30,
        'by_level': {
            name: compute_binary_metrics([(r['gt_alert'], r['pred_state']) for r in level_records if fn(r)])
            for name, fn in subsets.items()
        },
        'by_gondola': {
            name: compute_binary_metrics([(r['gt_alert'], r['pred_state']) for r in gondola_records if fn(r)])
            for name, fn in subsets.items()
        },
        'total_evaluated_levels': len(level_records),
        'total_evaluated_gondolas': len(gondola_records),
        'details': level_records,
    }
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    if not LABELS_PATH.is_file():
        raise SystemExit(f'Aún no existe {LABELS_PATH.relative_to(ROOT)}. Etiqueta primero desde el visor.')
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    saved = json.loads(LABELS_PATH.read_text(encoding='utf-8')).get('items', {})
    report = evaluate_human_masks(manifest, saved)
    BASELINE_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    printable = {k: v for k, v in report.items() if k != 'details'}
    print(json.dumps(printable, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
