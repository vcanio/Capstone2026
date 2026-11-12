"""Entrenador experimental de visibilidad; no se ejecuta al importar.

Requiere una revisión CVAT exportada explícitamente por el usuario. Solo
admite train/val y conserva la validación fuera de la selección de umbral.
"""
import argparse
from collections import Counter, defaultdict
import copy
import json
import os
from pathlib import Path
import random

from visibilidad_foto import ROOT, REPORT, calibrate, decision, full_frame, sha256, source_path

WEIGHT = ROOT / 'Modelos/preentrenados/yolo26n-cls.pt'
WEIGHT_SHA256 = '0dd6f8dbc448870ac98a3cbb7156f923f7ce21fed3755d4019169ffffd279e81'
LABELS = {'no_apta': 0, 'apta': 1}


def split_groups(rows, seed=42):
    """Partición determinista por escena, equilibrada por clases."""
    groups = defaultdict(list)
    for row in rows:
        groups[row['grupo_escena']].append(row)
    if len(groups) < 5:
        raise ValueError('Se requieren al menos cinco escenas independientes en train.')
    totals = Counter(row['etiqueta'] for row in rows)
    if set(totals) != set(LABELS):
        raise ValueError('Train requiere ambas clases revisadas.')
    names = sorted(groups)
    rng = random.Random(seed)
    size = max(1, round(len(names) * .2))
    best = None
    for _ in range(5000):
        chosen = frozenset(rng.sample(names, size))
        cal = [r for name in sorted(chosen) for r in groups[name]]
        fit = [r for name in names if name not in chosen for r in groups[name]]
        c = Counter(r['etiqueta'] for r in cal)
        f = Counter(r['etiqueta'] for r in fit)
        if set(c) != set(LABELS) or set(f) != set(LABELS):
            continue
        error = sum(abs(c[label] / totals[label] - .2) for label in LABELS)
        rank = (error, tuple(sorted(chosen)))
        if best is None or rank < best[0]:
            best = (rank, fit, cal)
    if best is None:
        raise ValueError('No se puede separar calibración por escenas con ambas clases.')
    return best[1], best[2]


def prepare(snapshot):
    if snapshot.get('test_included') is not False or snapshot.get('issues'):
        raise ValueError('La revisión contiene incidencias o no garantiza la reserva de test.')
    images = snapshot['images']
    if len(images) != 405 or Counter(x['split'] for x in images) != {'train': 336, 'val': 69}:
        raise ValueError('La revisión debe corresponder a las 405 fotos de desarrollo.')
    inventory_path = ROOT / 'Datos/Preparados/V3/Visibilidad_foto_20261102/inventario_pendiente.json'
    if snapshot.get('inventory_sha256') != sha256(inventory_path):
        raise ValueError('La revisión no corresponde al inventario congelado.')
    inventory = json.loads(inventory_path.read_text(encoding='utf-8-sig'))
    if sha256(REPORT) != inventory.get('source_report_sha256'):
        raise ValueError('Cambió el informe de anotaciones utilizado para comparar V3.')
    original = {row['name']: row for row in inventory['images']}
    identity = ('name', 'path', 'sha256', 'split', 'origen', 'familia', 'grupo_escena', 'cvat_task_id', 'cvat_name', 'frame')
    if len(original) != len(images) or len({row['name'] for row in images}) != len(images):
        raise ValueError('Hay nombres duplicados o ausentes en la revisión.')
    if any(row['name'] not in original or any(row.get(k) != original[row['name']].get(k) for k in identity)
           for row in images):
        raise ValueError('La identidad o partición de una imagen cambió desde el inventario.')
    if any(x['etiqueta'] not in (*LABELS, 'pendiente') for x in images):
        raise ValueError('La revisión contiene una etiqueta desconocida.')
    val = [x for x in images if x['split'] == 'val']
    if any(x['etiqueta'] == 'pendiente' for x in val):
        raise ValueError('Completa la revisión de las 69 fotos de validación.')
    train = [x for x in images if x['split'] == 'train' and x['etiqueta'] in LABELS]
    for row in train + val:
        path = source_path(row)
        if sha256(path) != row['sha256']:
            raise ValueError('La fuente no coincide con la revisión: ' + row['name'])
    if {x['grupo_escena'] for x in train} & {x['grupo_escena'] for x in val}:
        raise ValueError('Hay escenas compartidas entre entrenamiento y validación.')
    fit, calibration = split_groups(train)
    if not WEIGHT.is_file() or sha256(WEIGHT) != WEIGHT_SHA256:
        raise ValueError('Falta el peso general de clasificación o su hash no coincide.')
    return fit, calibration, val


def train(snapshot_path, output, progress=lambda *a, **k: None):
    """Entrenar solo cuando se invoque explícitamente desde un trabajo del usuario."""
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
    import numpy as np
    import torch
    import ultralytics
    from PIL import Image, ImageDraw, ImageEnhance, ImageOps
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
    from ultralytics import YOLO

    snapshot_path = Path(snapshot_path).resolve()
    if not (snapshot_path.is_relative_to((ROOT / 'Datos/Preparados/V3').resolve()) or
            (snapshot_path.is_relative_to((ROOT / 'Experimentos/panel_pruebas').resolve()) and
             snapshot_path.name == 'revision_visibilidad.json')):
        raise ValueError('La revisión debe estar en Datos/Preparados/V3.')
    snapshot = json.loads(snapshot_path.read_text(encoding='utf-8-sig'))
    fit, cal, val = prepare(snapshot)
    stable = json.loads((ROOT / '.config-modelo/version_actual_v3.json').read_text(encoding='utf-8-sig'))
    baseline_path = (ROOT / stable['model']).resolve()
    if not baseline_path.is_relative_to((ROOT / 'Experimentos').resolve()) or not baseline_path.is_file():
        raise ValueError('El modelo V3 estable no está disponible.')
    baseline_hash = sha256(baseline_path)
    if baseline_hash != stable['sha256']:
        raise ValueError('Los pesos V3 no coinciden con el registro estable.')
    output = Path(output).resolve()
    if not output.is_relative_to((ROOT / 'Experimentos').resolve()):
        raise ValueError('El ensayo debe estar en Laboratorio/Experimentos.')
    output.mkdir(parents=True, exist_ok=False)
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    class Photos(Dataset):
        def __init__(self, rows, augment=False):
            self.rows, self.augment = rows, augment
        def __len__(self):
            return len(self.rows)
        def __getitem__(self, index):
            row = self.rows[index]
            with Image.open(source_path(row)) as source:
                image = full_frame(source)
            if self.augment:
                image = ImageEnhance.Brightness(image).enhance(random.uniform(.9, 1.1))
                image = ImageEnhance.Color(image).enhance(random.uniform(.9, 1.1))
            tensor = torch.from_numpy(np.asarray(image).copy()).permute(2, 0, 1).float().div_(255)
            return tensor, LABELS[row['etiqueta']]

    def evaluate(network, rows):
        network.eval()
        scores = []
        with torch.no_grad():
            for inputs, _ in DataLoader(Photos(rows), batch_size=2, shuffle=False, num_workers=0):
                result = network(inputs.to(device))
                probabilities = result[0] if isinstance(result, tuple) else result.softmax(1)
                scores.extend(probabilities[:, 1].cpu().tolist())
        return scores

    def quality(rows, scores):
        total = Counter(row['etiqueta'] for row in rows)
        correct = Counter(row['etiqueta'] for row, score in zip(rows, scores)
                          if (score >= .5) == (row['etiqueta'] == 'apta'))
        balanced = sum(correct[label] / total[label] for label in LABELS) / 2
        false_accepts = sum(row['etiqueta'] == 'no_apta' and score >= .5 for row, score in zip(rows, scores))
        return balanced, false_accepts

    model = YOLO(str(WEIGHT)).model
    head = model.model[-1]
    head.linear = nn.Linear(head.linear.in_features, 2)
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.0001)
    loss_fn = nn.CrossEntropyLoss()
    loader = DataLoader(Photos(fit, augment=True), batch_size=2, shuffle=True, num_workers=0,
                        generator=torch.Generator().manual_seed(42))
    history, best, best_state, stagnant = [], None, None, 0
    progress('training', total_epochs=40, completed_epochs=0)
    for epoch in range(1, 41):
        model.train()
        total_loss = 0.
        for inputs, labels in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(inputs.to(device))
            loss = loss_fn(logits, labels.to(device))
            if not torch.isfinite(loss):
                raise ValueError('Pérdida no finita; ensayo detenido.')
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach())
        scores = evaluate(model, cal)
        balanced, false_accepts = quality(cal, scores)
        history.append({'epoch': epoch, 'loss': total_loss / len(loader),
                        'balanced_accuracy': balanced, 'false_accepts': false_accepts})
        rank = (balanced, -false_accepts)
        if best is None or rank > best:
            best = rank
            best_state = copy.deepcopy({key: value.cpu() for key, value in model.state_dict().items()})
            best_epoch, stagnant = epoch, 0
        else:
            stagnant += 1
        progress('training', completed_epochs=epoch, total_epochs=40)
        if stagnant >= 10:
            break
    model.load_state_dict(best_state)
    model.to(device)
    cal_scores = evaluate(model, cal)
    threshold = calibrate([(row['etiqueta'], score) for row, score in zip(cal, cal_scores)])
    torch.save({'state_dict': best_state, 'classes': LABELS, 'base_sha256': WEIGHT_SHA256}, output / 'best.pt')
    if threshold is not None:
        progress('evaluating', completed_epochs=len(history), total_epochs=40)
    # La validación no se consulta si la calibración no ha producido umbral.
    val_scores = evaluate(model, val) if threshold is not None else []
    evaluation = [{**{key: row[key] for key in ('name', 'split', 'origen', 'grupo_escena', 'etiqueta', 'motivo')},
                   'score_apta': score, 'decision': decision(score, threshold) if threshold is not None else 'sin_umbral'}
                  for row, score in zip(val, val_scores)]
    if threshold is not None:
        # Comparación geométrica exclusiva de validación: no calcula ocupación.
        progress('comparing', completed_epochs=len(history), total_epochs=40)
        from presentacion_niveles import draw_result
        model.to('cpu')
        if device.type == 'cuda':
            torch.cuda.empty_cache()
        if sha256(baseline_path) != baseline_hash:
            raise ValueError('Los pesos V3 cambiaron durante el ensayo.')
        baseline = YOLO(str(baseline_path))
        report_path = ROOT / 'Datos/Preparados/V3/v3_20261030_044237_fdcab79c/informe.json'
        report = json.loads(report_path.read_text(encoding='utf-8-sig'))
        truth = {x['name']: x for x in report['images'] if x['split'] == 'val'}
        compare_dir = output / 'comparaciones'
        compare_dir.mkdir()
        for index, (row, evaluation_row) in enumerate(zip(val, evaluation)):
            if row['name'] not in truth:
                raise ValueError('Falta la referencia de validación para ' + row['name'])
            with Image.open(source_path(row)) as source:
                rgba = ImageOps.exif_transpose(source).convert('RGBA')
                image = Image.new('RGB', rgba.size, 'white')
                image.paste(rgba, mask=rgba.getchannel('A'))
            original_width, original_height = image.size
            image.thumbnail((4096, 4096))
            prediction = baseline.predict(image, imgsz=640, conf=.6, iou=.7, retina_masks=True,
                                          device=0 if device.type == 'cuda' else 'cpu', verbose=False, save=False)[0]
            annotated, detections = draw_result(image, prediction)
            masks = prediction.masks.data.cpu().numpy() if prediction.masks is not None else []
            usable = (len(detections) > 0 and len(masks) == len(detections)
                      and all(mask.shape == (image.height, image.width) and np.isfinite(mask).all()
                              and np.all((mask >= 0) & (mask <= 1)) and np.any(mask > .5) for mask in masks)
                      and not any(d.get('near_frame', False) for d in detections))
            reference = image.copy()
            draw = ImageDraw.Draw(reference)
            for shape in truth[row['name']]['shapes']:
                points = [(x * image.width / original_width, y * image.height / original_height)
                          for x, y in zip(shape['points'][::2], shape['points'][1::2])]
                if len(points) >= 3:
                    draw.line(points + [points[0]], fill='#00ffff', width=3)
            reference.thumbnail((600, 700))
            annotated.thumbnail((600, 700))
            comparison = Image.new('RGB', (1200, 740), '#17212b')
            labels_draw = ImageDraw.Draw(comparison)
            labels_draw.text((10, 10), 'Anotación de referencia', fill='white')
            labels_draw.text((610, 10), 'Predicción V3 sin filtro', fill='white')
            comparison.paste(reference, (0, 35))
            comparison.paste(annotated, (600, 35))
            filename = f'{index:03d}.jpg'
            comparison.save(compare_dir / filename, quality=90)
            evaluation_row.update(baseline_levels=len(detections), reference_levels=len(truth[row['name']]['shapes']),
                                  baseline_near_frame=any(d.get('near_frame', False) for d in detections),
                                  v3_geometry_check=bool(usable), comparison_image=filename,
                                  filtered_outcome='niveles' if evaluation_row['decision'] == 'apta' and usable else 'no_evaluable')
    result = {'schema': 'visibilidad_foto_ensayo_v1', 'snapshot_sha256': sha256(snapshot_path),
              'base_sha256': WEIGHT_SHA256, 'checkpoint_sha256': sha256(output / 'best.pt'),
              'v3_baseline_sha256': baseline_hash,
              'seed': 42, 'device': str(device), 'deterministic': True,
              'versions': {'torch': torch.__version__, 'ultralytics': ultralytics.__version__, 'numpy': np.__version__},
              'parameters': {'epochs': 40, 'patience': 10, 'optimizer': 'AdamW', 'lr': .0001,
                             'batch': 2, 'size': 640, 'precision': 'float32', 'augmentation': 'brightness_color_0.9_1.1'},
              'best_epoch': best_epoch, 'threshold': threshold,
              'candidate_enabled': False, 'test_used': False, 'history': history,
              'fit_names': [row['name'] for row in fit], 'calibration_names': [row['name'] for row in cal],
              'calibration': [{'name': row['name'], 'etiqueta': row['etiqueta'], 'score_apta': score}
                              for row, score in zip(cal, cal_scores)],
              'validation': evaluation}
    apt = [row for row in evaluation if row['etiqueta'] == 'apta']
    blocked = [row for row in evaluation if row['etiqueta'] == 'no_apta']
    result['acceptance'] = {'candidate_for_testing': bool(threshold is not None and len(evaluation) == 69 and apt and blocked
                               and sum(x['decision'] == 'apta' for x in apt) / len(apt) >= .8
                               and not any(x['decision'] == 'apta' for x in blocked)),
                            'aptas': len(apt), 'aptas_aceptadas': sum(x['decision'] == 'apta' for x in apt),
                            'no_aptas': len(blocked), 'no_aptas_aceptadas': sum(x['decision'] == 'apta' for x in blocked),
                            'nota': 'Criterio experimental aplicado a todas las no aptas; no demuestra generalización real.'}
    summaries = []
    for field in ('origen', 'grupo_escena', 'motivo'):
        for value in sorted({str(row.get(field)) for row in evaluation}):
            subset = [row for row in evaluation if str(row.get(field)) == value]
            apt = [row for row in subset if row['etiqueta'] == 'apta']
            blocked = [row for row in subset if row['etiqueta'] == 'no_apta']
            summaries.append({'group_by': field, 'group': value, 'photos': len(subset),
                              'aptas': len(apt), 'aptas_aceptadas': sum(x['decision'] == 'apta' for x in apt),
                              'no_aptas': len(blocked), 'no_aptas_aceptadas': sum(x['decision'] == 'apta' for x in blocked)})
    result['validation_summary'] = summaries
    (output / 'resultado.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    progress('done', completed_epochs=len(history), total_epochs=40)
    return result
