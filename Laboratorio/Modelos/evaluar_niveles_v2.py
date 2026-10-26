"""Evaluación de los tres estados a confianza fija y por IoU de máscaras.

El emparejamiento es geométrico e independiente de la clase: un nivel localizado
con estado equivocado cuenta como error de estado, no como un acierto de reposición.
"""
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

STATES = ('reponer', 'suficiente', 'no_evaluable')


def evaluate_masks(truth, predictions, minimum_iou=0.5):
    pairs = sorted((float(np.logical_and(t, p).sum() / max(1, np.logical_or(t, p).sum())), ti, pi)
                   for ti, (_, t) in enumerate(truth) for pi, (_, p) in enumerate(predictions))
    used_t, used_p, matches = set(), set(), []
    for iou, ti, pi in reversed(pairs):
        if iou >= minimum_iou and ti not in used_t and pi not in used_p:
            used_t.add(ti)
            used_p.add(pi)
            matches.append({'referencia': ti, 'prediccion': pi, 'iou_mascara': iou,
                            'real': STATES[truth[ti][0]], 'predicho': STATES[predictions[pi][0]]})
    confusion = {state: Counter() for state in (*STATES, 'sin_referencia')}
    for pair in matches:
        confusion[pair['real']][pair['predicho']] += 1
    for i, (cls, _) in enumerate(truth):
        if i not in used_t:
            confusion[STATES[cls]]['no_detectado'] += 1
    for i, (cls, _) in enumerate(predictions):
        if i not in used_p:
            confusion['sin_referencia'][STATES[cls]] += 1
    return {'referencias': dict(Counter(STATES[c] for c, _ in truth)),
            'predicciones': dict(Counter(STATES[c] for c, _ in predictions)),
            'aciertos': dict(Counter(p['real'] for p in matches if p['real'] == p['predicho'])),
            'parejas': matches, 'omitidos': len(truth) - len(matches),
            'extra': len(predictions) - len(matches),
            'matriz_confusion': {key: dict(value) for key, value in confusion.items()}}


def aggregate(summaries):
    references, predictions, correct = Counter(), Counter(), Counter()
    confusion = {state: Counter() for state in (*STATES, 'sin_referencia')}
    for summary in summaries:
        references.update(summary['referencias'])
        predictions.update(summary['predicciones'])
        correct.update(summary['aciertos'])
        for state, row in summary['matriz_confusion'].items():
            confusion[state].update(row)
    def ratio(a, b):
        return a / b if b else None
    by_class = {}
    for state in STATES:
        tp = correct[state]
        fp, fn = predictions[state] - tp, references[state] - tp
        by_class[state] = {'referencias': references[state], 'predicciones': predictions[state],
                           'tp': tp, 'fp': fp, 'fn': fn, 'precision': ratio(tp, tp + fp),
                           'recall': ratio(tp, tp + fn), 'f1': ratio(2 * tp, 2 * tp + fp + fn)}
    # Reponer es la única alerta de stock. Abstenerse en un nivel reponer
    # cuenta como omisión; no_evaluable jamás cuenta como una alerta acertada.
    alert = by_class['reponer']
    return {'fotos': len(summaries), 'por_clase': by_class,
            'reposicion': {'acertadas': alert['tp'], 'omitidas': alert['fn'],
                           'falsas_alertas': alert['fp'], 'precision': alert['precision'],
                           'recall': alert['recall'], 'f1': alert['f1'],
                           'falsas_por_foto': ratio(alert['fp'], len(summaries))},
            'matriz_confusion': {state: dict(row) for state, row in confusion.items()}}


def evaluate_split(model, records, device, imgsz, confidence=0.25, minimum_iou=0.5):
    """Evalúa cada imagen original a resolución completa, sin augmentation."""
    summaries = []
    for record in records:
        image_path = Path(record['imagen'])
        with Image.open(image_path) as source:
            image = source.convert('RGB')
        width, height = image.size
        truth = []
        for line in Path(record['etiqueta']).read_text(encoding='utf-8-sig').splitlines():
            if not line.strip():
                continue
            values = line.split()
            coords = np.asarray([float(v) for v in values[1:]]).reshape(-1, 2) * [width, height]
            raster = Image.new('1', (width, height))
            ImageDraw.Draw(raster).polygon([tuple(point) for point in coords], fill=1)
            truth.append((int(values[0]), np.asarray(raster, dtype=bool)))
        result = model.predict(image, device=device, imgsz=imgsz, conf=confidence, iou=0.7,
                               retina_masks=True, augment=False, verbose=False)[0]
        predictions = []
        if result.masks is not None:
            for cls, mask in zip(result.boxes.cls.cpu().tolist(), result.masks.data.cpu().numpy()):
                if mask.shape != (height, width):
                    raise ValueError(f'La máscara predicha no coincide con la imagen: {image_path}.')
                predictions.append((int(cls), mask.astype(bool)))
        summaries.append({'imagen': str(image_path), **evaluate_masks(truth, predictions, minimum_iou)})
    return {'confianza': confidence, 'iou_mascara_minimo': minimum_iou,
            'nms_iou': 0.7, 'metodo': 'emparejamiento geométrico voraz por IoU, sin exigir misma clase',
            **aggregate(summaries)}, summaries
