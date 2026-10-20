"""Comparar YOLO y señal de detección de bordes en la validación de desarrollo V2, sin entrenar."""
import argparse
from datetime import datetime, timezone
import csv
import hashlib
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from comparar_niveles import aggregate, evaluate_masks
from conjuntos import dataset_directory, digest
from ocupacion_paulo import Analyzer, ROOT, provenance
from panel_worker import spatial_order
from piloto_modulos import font_path
from particion_niveles import load_partition


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def development_entries(manifest, partition):
    if manifest.get('criterion', {}).get('version') != 'disponibilidad_visual_nivel_v2_reponer':
        raise ValueError('Este experimento requiere un ensayo V2.')
    entries = [item for item in manifest['imagenes'] if item['split'] == 'val']
    expected = {name for name, item in partition['records'].items() if item['effective_split'] == 'val'}
    if {Path(item['imagen']).stem for item in entries} != expected or len(entries) != len(expected):
        raise ValueError('La validación debe coincidir con las 10 fotos reales de la partición base.')
    return entries


def experiment(run, out, partition, device):
    from ultralytics import YOLO
    from shapely.geometry import Polygon
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8-sig'))
    config = json.loads((run / 'config_interfaz.json').read_text(encoding='utf-8-sig'))
    entries = development_entries(manifest, partition)
    dataset = dataset_directory(ROOT, run, manifest)
    receipt = json.loads((dataset / 'integridad.json').read_text(encoding='utf-8-sig'))
    hashes = {entry['archivo']: entry['sha256'] for entry in receipt['archivos']}
    classes = manifest['clases']; states = tuple(c.removeprefix('Nivel_') for c in classes)
    weights = run / 'entrenamiento/weights/best.pt'
    model = YOLO(str(weights))
    if [model.names[i] for i in range(len(model.names))] != classes:
        raise ValueError('Las clases de los pesos no coinciden con el ensayo.')
    directory = out / run.name; directory.mkdir()
    rows, summaries, gallery = [], [], []
    font = ImageFont.truetype(str(font_path()), 18)
    for item in entries:
        name = item['imagen']; stem = Path(name).stem
        source = dataset / 'images/val' / name; label = dataset / 'labels/val' / (stem + '.txt')
        for path in (source, label):
            if digest(path) != hashes[path.relative_to(dataset).as_posix()]:
                raise ValueError('Cambió una foto o etiqueta exportada: ' + name)
        image = Image.open(source).convert('RGB'); width, height = image.size
        truth = []
        for line in label.read_text().splitlines():
            fields = line.split(); points = np.array(list(map(float, fields[1:]))).reshape(-1, 2)*[width, height]
            mask = Image.new('1', image.size); ImageDraw.Draw(mask).polygon([tuple(p) for p in points], fill=1)
            truth.append((int(fields[0]), np.asarray(mask, dtype=bool)))
        result = model.predict(image, conf=.25, iou=.7, imgsz=config['imgsz'], retina_masks=True, device=device, verbose=False)[0]
        if result.boxes is not None and len(result.boxes):
            result = result[spatial_order(result.boxes.xyxy.cpu().tolist())]
        analyzer = Analyzer(np.asarray(image)); predictions, detections = [], []
        if result.masks is not None:
            for index, (cls, confidence, points, mask) in enumerate(zip(result.boxes.cls.cpu().tolist(), result.boxes.conf.cpu().tolist(), result.masks.xy, result.masks.data.cpu().numpy()), 1):
                state = states[int(cls)]; valid = len(points) >= 3 and Polygon(points).is_valid
                signal = analyzer.analyze(mask, state, valid)
                predictions.append((int(cls), mask.astype(bool)))
                detections.append({'nivel': index, 'estado_yolo': state, 'confianza_yolo': round(confidence, 5), **signal})
        summary = evaluate_masks(truth, predictions, states=states); summaries.append(summary)
        matched = {pair['prediccion']: pair for pair in summary['parejas']}
        for detection in detections:
            match = matched.get(detection['nivel'], {})
            rows.append({'foto': name, **detection, 'estado_anotado': match.get('estado_real'), 'iou_referencia': match.get('iou_mascara')})
        reference = image.copy(); reference.thumbnail((850, 680))
        signal_image = Image.fromarray(analyzer.overlay()); signal_image.thumbnail((850, 680))
        scale = reference.width/width
        for index, (cls, mask) in enumerate(predictions, 1):
            ys, xs = np.where(mask)
            if len(xs):
                for panel in (reference, signal_image):
                    ImageDraw.Draw(panel).text((int(xs.min()*scale)+3, int(ys.min()*scale)+3), f'{index} {states[cls]}', font=font, fill='white', stroke_width=2, stroke_fill='black')
        canvas = Image.new('RGB', (1700, 740), '#111827')
        canvas.paste(reference, (0, 50)); canvas.paste(signal_image, (850, 50))
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 12), 'YOLO: niveles numerados | ' + name, font=font, fill='white')
        draw.text((862, 12), 'Detección de bordes: señal de bordes/color/textura', font=font, fill='white')
        canvas.save(directory / (stem + '.jpg'), quality=90)
        gallery.append({'photo': name, 'image': run.name + '/' + stem + '.jpg'})
        print(run.name, name, len(predictions), 'niveles', flush=True)
    with (directory / 'niveles.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        fields = list(dict.fromkeys(key for row in rows for key in row)) if rows else ['foto', 'nivel']
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    matched_rows = [r for r in rows if r['estado_anotado'] is not None]
    signal_groups = {state: {'niveles': len(group := [r for r in matched_rows if r['estado_anotado'] == state and r['status'] == 'medido']),
        'area_mediana': float(np.median([r['area_signal_pct'] for r in group])) if group else None,
        'ancho_mediano': float(np.median(widths)) if (widths := [r['width_signal_pct'] for r in group if r['width_signal_pct'] is not None]) else None} for state in states}
    output = {'run': run.name, 'weights_sha256': digest(weights), 'manifest_sha256': digest(run / 'manifest.json'),
              'yolo_validation': aggregate(summaries, states=states), 'signal_by_human_state': signal_groups,
              'measured': sum(r['status'] == 'medido' for r in rows), 'detections': len(rows),
              'percentage_accuracy': None, 'levels': rows, 'gallery': gallery}
    save(directory / 'resultados.json', output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--device', default='auto')
    args = parser.parse_args()
    import torch
    partition = load_partition(ROOT)
    if not partition: raise ValueError('Falta la partición base registrada.')
    runs = [(ROOT / 'Experimentos' / name).resolve() for name in args.runs]
    if any(run.parent != (ROOT / 'Experimentos').resolve() for run in runs):
        raise ValueError('Indica nombres de ensayos dentro de Experimentos.')
    for run in runs:
        development_entries(json.loads((run / 'manifest.json').read_text(encoding='utf-8-sig')), partition)
    args.out.mkdir(parents=True, exist_ok=False)
    metadata = {'created_at': datetime.now(timezone.utc).isoformat(), 'partition': partition['binding'],
                'split': 'val', 'uses_final_reserve': False, 'occupancy': provenance(), 'runs': args.runs,
                'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    save(args.out / 'experimento.json', metadata)
    results = [experiment(run, args.out, partition, 0 if torch.cuda.is_available() else 'cpu') if args.device == 'auto'
               else experiment(run, args.out, partition, args.device) for run in runs]
    save(args.out / 'resumen.json', [{k: v for k, v in r.items() if k not in ('levels', 'gallery')} for r in results])
    parts = ['<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>YOLO + detección de bordes · experimento V2</title><style>body{font:16px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#172b4d}img{max-width:100%;height:auto}table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #dde4ee;text-align:left}summary{cursor:pointer}</style><h1>YOLO + detección de bordes · primera comparación</h1><p>10 fotos de validación de desarrollo por modelo. Amarillo indica señal de bordes/color dentro del nivel detectado. Los porcentajes son experimentales: no miden precisión ni ocupación real validada y no cambian el estado de YOLO. La reserva final queda fuera.</p>']
    for result in results:
        a = result['yolo_validation']['alertas']
        parts.append(f'<h2>{html.escape(result["run"])}</h2><p>Alertas YOLO: {a["acertadas"]} acertadas, {a["omitidas"]} omitidas y {a["falsas"]} falsas. Señal medible en {result["measured"]}/{result["detections"]} detecciones.</p>')
        for photo in result['gallery']:
            parts.append(f'<details><summary>{html.escape(photo["photo"])}</summary><img src="{html.escape(photo["image"])}" alt="Niveles YOLO y señal de detección de bordes"><table><tr><th>Nivel</th><th>YOLO</th><th>Anotado</th><th>Área con señal</th><th>Ancho con señal</th></tr>')
            for row in (r for r in result['levels'] if r['foto'] == photo['photo']):
                fmt = lambda value: 'Sin medición' if value is None else f'{value:.1f} %'
                parts.append(f'<tr><td>{row["nivel"]}</td><td>{html.escape(row["estado_yolo"])}</td><td>{html.escape(row["estado_anotado"] or "Sin pareja")}</td><td>{fmt(row["area_signal_pct"])}</td><td>{fmt(row["width_signal_pct"])}</td></tr>')
            parts.append('</table></details>')
    (args.out / 'informe.html').write_text(''.join(parts) + '</html>', encoding='utf-8')


if __name__ == '__main__':
    main()
