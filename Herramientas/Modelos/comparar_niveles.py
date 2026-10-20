"""Evaluar localización, estado y alertas por separado, desde la foto completa."""
import json
from collections import Counter
from pathlib import Path

from niveles_modelos import CLASS_NAMES, STATES, STATE_COLORS, ALERT_STATES

COLORS = ('#dc2626', '#f59e0b', '#16a34a', '#64748b')


def evaluate_masks(truth, predictions, minimum_iou=0.5, *, states=STATES):
    """Emparejar por geometría; cada tupla contiene (clase, máscara binaria)."""
    import numpy as np
    pairs = sorted(((float(np.logical_and(t, p).sum() / max(1, np.logical_or(t, p).sum())), ti, pi)
                    for ti, (_, t) in enumerate(truth) for pi, (_, p) in enumerate(predictions)), reverse=True)
    used_t, used_p, matches = set(), set(), []
    for iou, ti, pi in pairs:
        if iou >= minimum_iou and ti not in used_t and pi not in used_p:
            used_t.add(ti); used_p.add(pi)
            matches.append({'anotacion': ti+1, 'prediccion': pi+1, 'iou_mascara': iou,
                            'estado_real': states[truth[ti][0]], 'estado_predicho': states[predictions[pi][0]]})
    true_counts = Counter(states[c] for c, _ in truth)
    pred_counts = Counter(states[c] for c, _ in predictions)
    correct = Counter(m['estado_real'] for m in matches if m['estado_real'] == m['estado_predicho'])
    alert_tp = sum(m['estado_real'] in ALERT_STATES and m['estado_predicho'] in ALERT_STATES for m in matches)
    true_alerts = sum(true_counts[s] for s in ALERT_STATES)
    pred_alerts = sum(pred_counts[s] for s in ALERT_STATES)
    confusion = {s: dict(Counter(m['estado_predicho'] for m in matches if m['estado_real'] == s)) for s in states}
    for ti, (c, _) in enumerate(truth):
        if ti not in used_t:
            row = confusion[states[c]]; row['no_detectado'] = row.get('no_detectado', 0) + 1
    confusion['sin_referencia'] = dict(Counter(states[c] for pi, (c, _) in enumerate(predictions) if pi not in used_p))
    return {'anotados': len(truth), 'predichos': len(predictions), 'aciertos': len(matches),
            'omitidos': len(truth)-len(matches), 'falsos_positivos': len(predictions)-len(matches),
            'parejas': matches, 'estados_acertados': sum(correct.values()),
            'estados_reales': dict(true_counts), 'estados_predichos': dict(pred_counts),
            'aciertos_por_estado': dict(correct), 'matriz_confusion': confusion,
            'alertas_reales': true_alerts, 'alertas_predichas': pred_alerts, 'alertas_acertadas': alert_tp,
            'alertas_omitidas': true_alerts-alert_tp, 'falsas_alertas': pred_alerts-alert_tp,
            'no_evaluables_predichos': pred_counts['no_evaluable']}


def aggregate(summaries, *, states=STATES):
    true_counts, pred_counts, correct = Counter(), Counter(), Counter()
    confusion = {s: Counter() for s in (*states, 'sin_referencia')}
    for s in summaries:
        true_counts.update(s['estados_reales']); pred_counts.update(s['estados_predichos'])
        correct.update(s['aciertos_por_estado'])
        for state, row in s['matriz_confusion'].items():
            confusion[state].update(row)
    ratio = lambda a, b: a / b if b else None
    tp = sum(s['alertas_acertadas'] for s in summaries)
    real = sum(s['alertas_reales'] for s in summaries)
    pred = sum(s['alertas_predichas'] for s in summaries)
    return {'fotos': len(summaries), 'por_estado': {state: {'referencias': true_counts[state],
                'predicciones': pred_counts[state], 'aciertos': correct[state],
                'precision': ratio(correct[state], pred_counts[state]),
                'recall': ratio(correct[state], true_counts[state])} for state in states},
            'alertas': {'reales': real, 'predichas': pred, 'acertadas': tp,
                'omitidas': real-tp, 'falsas': pred-tp, 'precision': ratio(tp, pred), 'recall': ratio(tp, real),
                'falsas_por_foto': ratio(pred-tp, len(summaries))},
            'no_evaluables_predichos': pred_counts['no_evaluable'],
            'matriz_confusion': {s: dict(row) for s, row in confusion.items()}}


def compare_levels(run, device, font_path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from shapely.geometry import Polygon
    from ultralytics import YOLO
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
    config = json.loads((run / 'config_interfaz.json').read_text(encoding='utf-8'))
    model = YOLO(str(run / 'entrenamiento/weights/best.pt'))
    classes = manifest.get('clases', CLASS_NAMES)
    states = tuple(name.removeprefix('Nivel_') for name in classes)
    colors = [STATE_COLORS[state] for state in states]
    assert [model.names[i] for i in range(len(model.names))] == classes
    from conjuntos import dataset_directory
    dataset = dataset_directory(run.parents[1], run, manifest)
    out = run / 'comparaciones'; out.mkdir(exist_ok=True)
    masks_out = run / 'mascaras'; masks_out.mkdir(exist_ok=True)
    font = ImageFont.truetype(str(font_path), 18)
    summaries = []
    for item in manifest['imagenes']:
        name, split = item['imagen'], item['split']
        source = dataset / 'images' / split / name
        with Image.open(source) as original:
            image = original.convert('RGB')
        w, h = image.size
        truth, truth_points, prediction_points, predictions, confidence = [], [], [], [], []
        for line in (dataset / 'labels' / split / (Path(name).stem + '.txt')).read_text().splitlines():
            fields = line.split(); cls = int(fields[0]); pts = np.array(list(map(float, fields[1:]))).reshape(-1, 2) * [w, h]
            mask = Image.new('1', (w, h)); ImageDraw.Draw(mask).polygon([tuple(p) for p in pts], fill=1)
            truth.append((cls, np.asarray(mask, dtype=bool))); truth_points.append((cls, pts))
        result = model.predict(image, device=device, imgsz=config['imgsz'], conf=0.25, iou=0.7,
                               retina_masks=True, verbose=False)[0]
        if result.masks is not None:
            for cls, conf, pts, mask in zip(result.boxes.cls.cpu().tolist(), result.boxes.conf.cpu().tolist(),
                    result.masks.xy, result.masks.data.cpu().numpy()):
                assert mask.shape == (h, w)
                predictions.append((int(cls), mask.astype(bool))); prediction_points.append((int(cls), pts)); confidence.append(conf)
        summary = {'imagen': name, 'split': split, 'scope': 'Nivel_estados', 'conf': 0.25, 'iou_minimo': 0.5,
                   **evaluate_masks(truth, predictions, states=states),
                   'contornos_xy_invalidos': sum(len(p) < 3 or not Polygon(p).is_valid for _, p in prediction_points)}
        summaries.append(summary)
        panels = []
        for title, objects in [('Referencia: niveles y estados', truth_points), ('Predicción: niveles y estados', prediction_points)]:
            panel = image.copy(); panel.thumbnail((1000, 750)); scale = panel.width / w; draw = ImageDraw.Draw(panel)
            for idx, (cls, pts) in enumerate(objects):
                if len(pts) < 3: continue
                scaled = [tuple(p * scale) for p in pts]
                draw.line(scaled + [scaled[0]], fill=colors[cls], width=4)
                draw.text(scaled[0], str(idx+1) + ' ' + states[cls], font=font, fill='white', stroke_width=2, stroke_fill='black')
            bordered = Image.new('RGB', (1000, 800), '#111827'); bordered.paste(panel, (0, 50))
            ImageDraw.Draw(bordered).text((15, 12), f'{name} | {split} | {title}', font=font, fill='white'); panels.append(bordered)
        canvas = Image.new('RGB', (2000, 800)); canvas.paste(panels[0]); canvas.paste(panels[1], (1000, 0))
        canvas.save(out / f'{Path(name).stem}_{split}.jpg', quality=92)
        for idx, (_, mask) in enumerate(predictions):
            Image.fromarray(mask.astype(np.uint8)*255).save(masks_out / f'{Path(name).stem}_{idx+1:02d}.png')
    (run / 'evaluacion_por_imagen.json').write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding='utf-8')
    metrics = {'criterion': manifest['criterion'], 'confidence': 0.25, 'iou_minimo': 0.5,
               'train': aggregate([s for s in summaries if s['split'] == 'train'], states=states),
               'val': aggregate([s for s in summaries if s['split'] == 'val'], states=states)}
    (run / 'metricas_alertas.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
