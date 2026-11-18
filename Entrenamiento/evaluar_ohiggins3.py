"""Evaluación reproducible sobre el conjunto de test independiente Ohiggins 3.

Permite:
1. Verificar de forma offline y determinista las métricas publicadas en
   `Documentacion/Evidencias/evaluacion_test_ohiggins3_20261114.json` y
   `Documentacion/Estado_V3_actual.json` (`--verify-receipt`, predeterminado).
2. Reevaluar la segmentación de niveles (IoU >= 0.50) y la estimación de disponibilidad visual
   cuando se provee una carpeta local de imágenes y etiquetas (`--images-dir` y
   `--labels-dir`), sin modificar pesos ni etiquetas.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / 'Aplicacion'
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


def compute_mask_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Calcular IoU entre dos máscaras binarias 2D."""
    a = np.asarray(mask_a, dtype=bool)
    b = np.asarray(mask_b, dtype=bool)
    union = int(np.logical_or(a, b).sum())
    if union == 0:
        return 0.0
    inter = int(np.logical_and(a, b).sum())
    return float(inter) / float(union)


def match_predictions_iou_50(
    pred_masks: list[np.ndarray],
    gt_masks: list[np.ndarray],
    iou_threshold: float = 0.50,
) -> dict:
    """Emparejamiento codicioso 1-a-1 entre máscaras predichas y ground-truth."""
    pairs = []
    for p_idx, p_mask in enumerate(pred_masks):
        for g_idx, g_mask in enumerate(gt_masks):
            iou = compute_mask_iou(p_mask, g_mask)
            if iou >= iou_threshold:
                pairs.append((iou, p_idx, g_idx))
    pairs.sort(reverse=True)
    used_p, used_g, matched_ious = set(), set(), []
    for iou, p_idx, g_idx in pairs:
        if p_idx in used_p or g_idx in used_g:
            continue
        used_p.add(p_idx)
        used_g.add(g_idx)
        matched_ious.append(iou)
    tp = len(matched_ious)
    fp = len(pred_masks) - tp
    fn = len(gt_masks) - tp
    return {
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'matched_ious': matched_ious,
        'mean_iou': round(float(np.mean(matched_ious)), 4) if matched_ious else 0.0,
    }


def compute_confusion_metrics(tp: int, fp: int, fn: int, tn: int) -> dict:
    """Calcular Accuracy, Precision, Recall, Specificity y F1 desde la matriz de confusión."""
    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        'total': total,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'tn': tn,
        'accuracy': round(accuracy, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'specificity': round(specificity, 4),
        'f1': round(f1, 4),
    }


def verify_receipt(root: Path = ROOT) -> dict:
    """Verificar consistencia matemática e integridad de hashes del recibo Ohiggins 3."""
    root = Path(root)
    receipt = json.loads(
        (root / 'Documentacion/Evidencias/evaluacion_test_ohiggins3_20261114.json').read_text(encoding='utf-8')
    )
    state = json.loads((root / 'Documentacion/Estado_V3_actual.json').read_text(encoding='utf-8'))
    manifest = json.loads((root / 'Aplicacion/modelos.json').read_text(encoding='utf-8'))

    weights_path = root / 'Aplicacion' / manifest['models'][0]['file']
    weights_sha = hashlib.sha256(weights_path.read_bytes()).hexdigest()
    expected_sha = receipt['yolo_segmentation']['weights_sha256']
    if weights_sha != expected_sha or state['model']['sha256'] != expected_sha:
        raise ValueError('El SHA-256 del peso oficial no coincide con el recibo congelado.')

    base_raw = receipt['linea_a_occupancy_blind_test']['level_metrics']
    base_calc = compute_confusion_metrics(base_raw['tp'], base_raw['fp'], base_raw['fn'], base_raw['tn'])
    if (
        base_calc['accuracy'] != base_raw['accuracy']
        or base_calc['precision'] != base_raw['precision_reponer']
        or base_calc['recall'] != base_raw['recall_reponer']
        or base_calc['f1'] != base_raw['f1_reponer']
    ):
        raise ValueError('Las métricas de la línea base en el recibo no coinciden.')

    v22_raw = state['validation']['occupancy_test_ohiggins3_v2_2']['by_level']
    v22_calc = compute_confusion_metrics(v22_raw['tp'], v22_raw['fp'], v22_raw['fn'], v22_raw['tn'])
    for metric in ('accuracy', 'precision', 'recall', 'specificity', 'f1'):
        if v22_calc[metric] != v22_raw[metric]:
            raise ValueError(f'La métrica {metric} de v2.2 en Estado_V3_actual.json no coincide.')

    return {
        'status': 'ok',
        'mode': 'verify_receipt',
        'dataset': receipt['dataset']['name'],
        'photos': receipt['dataset']['photos'],
        'levels': receipt['dataset']['gt_polygons_nivel'],
        'weights_sha256': weights_sha,
        'linea_a_base': base_calc,
        'linea_a_v2_2': v22_calc,
    }


def evaluate_directory(images_dir: Path, labels_dir: Path, weights_path: Path, conf: float = 0.60) -> dict:
    """Evaluar la segmentación de niveles y la estimación de disponibilidad visual sobre una carpeta YOLO-seg."""
    import cv2
    from PIL import Image, ImageOps
    from ultralytics import YOLO
    from ocupacion_linea_a import analyze_gondola_rgb

    model = YOLO(str(weights_path))
    image_files = sorted(
        p for p in Path(images_dir).iterdir()
        if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')
    )
    if not image_files:
        raise ValueError(f'No se encontraron imágenes en {images_dir}')

    total_tp = total_fp = total_fn = 0
    all_ious = []
    state_counts = {'reponer': 0, 'suficiente': 0, 'revisar': 0}

    for img_path in image_files:
        with Image.open(img_path) as im:
            rgb = np.asarray(ImageOps.exif_transpose(im).convert('RGB'))
        h, w = rgb.shape[:2]
        lbl_path = Path(labels_dir) / f'{img_path.stem}.txt'
        gt_masks = []
        if lbl_path.is_file():
            for line in lbl_path.read_text(encoding='utf-8').splitlines():
                parts = line.strip().split()
                if len(parts) < 7:
                    continue
                coords = [float(v) for v in parts[1:]]
                pts = np.array(
                    [[coords[i] * w, coords[i + 1] * h] for i in range(0, len(coords), 2)],
                    dtype=np.int32,
                )
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.fillPoly(mask, [pts], 1)
                gt_masks.append(mask)

        result = model.predict(rgb, imgsz=640, conf=conf, iou=0.7, retina_masks=True, verbose=False, save=False)[0]
        pred_masks = (
            [(m > 0.5).astype(np.uint8) for m in result.masks.data.cpu().numpy()]
            if result.masks is not None else []
        )
        matched = match_predictions_iou_50(pred_masks, gt_masks)
        total_tp += matched['tp']
        total_fp += matched['fp']
        total_fn += matched['fn']
        all_ious.extend(matched['matched_ious'])

        for occ in analyze_gondola_rgb(rgb, pred_masks):
            st = occ.get('state', 'revisar')
            state_counts[st] = state_counts.get(st, 0) + 1

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        'status': 'ok',
        'mode': 'evaluate_directory',
        'photos': len(image_files),
        'segmentation_iou_50': {
            'tp': total_tp,
            'fp': total_fp,
            'fn': total_fn,
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4),
            'mean_matched_iou': round(float(np.mean(all_ious)), 4) if all_ious else 0.0,
        },
        'occupancy_predictions': state_counts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-receipt', action='store_true', help='Verificar recibo congelado de Ohiggins 3')
    parser.add_argument('--images-dir', type=Path, help='Carpeta local de imágenes de evaluación')
    parser.add_argument('--labels-dir', type=Path, help='Carpeta local de etiquetas YOLO-seg (.txt)')
    parser.add_argument('--weights', type=Path, default=APP_DIR / 'modelos/V3-cierre-revisado-20261110.pt')
    parser.add_argument('--conf', type=float, default=0.60)
    args = parser.parse_args()

    if args.images_dir and args.labels_dir:
        print(json.dumps(evaluate_directory(args.images_dir, args.labels_dir, args.weights, args.conf), ensure_ascii=False, indent=2))
        return

    print(json.dumps(verify_receipt(ROOT), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
