"""Trabajos del panel en un proceso separado para liberar GPU al terminar."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import piloto_modulos as pilot
from rutas_datos import current_image_path


def spatial_order(boxes):
    """Leer de abajo hacia arriba y de izquierda a derecha en cada fila."""
    centers = [(index, (box[1] + box[3]) / 2, max(1, box[3] - box[1]), box[0])
               for index, box in enumerate(boxes)]
    rows = []
    for index, center, height, left in sorted(centers, key=lambda item: (item[1], item[3])):
        # Un ancla fija evita unir filas sucesivas por acumulación de pequeños desfases.
        if rows and abs(center - rows[-1][0]) <= .5 * min(height, rows[-1][1]):
            rows[-1][2].append((left, center, index))
        else:
            rows.append((center, height, [(left, center, index)]))
    return [index for _, _, items in reversed(rows) for _, _, index in sorted(items)]


def execute(job):
    config = json.loads((job / 'solicitud.json').read_text(encoding='utf-8'))
    if config['action'] == 'train':
        from panel_modelos import write_json
        tracking = {'started_at': datetime.now(timezone.utc).isoformat(),
                    'total_epochs': config['epochs'], 'completed_epochs': 0}

        def progress(stage, **values):
            tracking.update(stage=stage, updated_at=datetime.now(timezone.utc).isoformat(), **values)
            write_json(job / 'progreso.json', tracking)

        progress('preparing')
        pilot.RUN = pilot.ROOT / 'Experimentos' / config['run']
        pilot.SEED = config['seed']
        pilot.prepare()
        progress('training')
        pilot.train(config['epochs'], pilot.ROOT / config['model'], config['imgsz'],
                    config['batch'], config['lr'], config['seed'], progress=progress)
        progress('evaluating')
        pilot.evaluate(progress=progress)
        pilot.save_json(job / 'resultado.json', {'run': config['run']})
        progress('done')
        return
    import numpy as np
    import torch
    from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageColor
    from ultralytics import YOLO
    from shapely.geometry import Polygon
    from niveles_modelos import model_states, STATE_LABELS, STATE_COLORS, ALERT_STATES
    from comparar_niveles import COLORS, evaluate_masks
    model = YOLO(str(pilot.ROOT / config['model']))
    states = model_states(model.names)
    levels = states is not None
    source = pilot.ROOT / current_image_path(config['image'])
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert('RGB')
    # Freeze Paulo's input before inference or any display drawing takes place.
    occupancy_rgb = np.array(image, copy=True) if config.get('occupancy') else None
    if occupancy_rgb is not None:
        occupancy_rgb.setflags(write=False)
    result = model.predict(image, conf=config['conf'], iou=config['nms'],
                           imgsz=config['imgsz'], retina_masks=True,
                           device=0 if torch.cuda.is_available() else 'cpu', verbose=False)[0]
    if result.boxes is not None and len(result.boxes):
        # Reordenar el resultado completo conserva la asociación entre máscara,
        # clase y confianza antes de asignar los IDs de imagen y tabla.
        result = result[spatial_order(result.boxes.xyxy.cpu().tolist())]
    width, height = image.size
    detections, masks = [], []
    overlay = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(overlay)
    labels = [STATE_LABELS[state] for state in states] if levels else []
    colors = [STATE_COLORS[state] for state in states] if levels else []
    font = ImageFont.truetype(str(pilot.font_path()), max(16, round(max(width, height) / 54)))
    line_width = max(2, round(max(width, height) / 650))
    badges = []

    def badge(points, cls, number):
        title = labels[cls] if levels else result.names[cls]
        color = ImageColor.getrgb(colors[cls]) if levels else (0, 83, 226)
        left, top = min(p[0] for p in points), min(p[1] for p in points)
        bounds = draw.textbbox((0, 0), title, font=font)
        text_height = font.getbbox('Ágj')[3] - font.getbbox('Ágj')[1]
        padding = max(5, round(font.size * .35))
        box_height = text_height + padding * 2
        number_width = max(box_height - padding, round(draw.textlength(str(number), font=font)) + padding * 2)
        box_width = round(draw.textlength(title, font=font)) + number_width + padding * 4
        x, y = max(0, min(left + 5, width - box_width)), max(0, min(top + 5, height - box_height))
        badges.append((x, y, box_width, box_height, title, str(number), number_width, padding, color, bounds))

    if result.masks is not None:
        for points, confidence, cls, mask in zip(result.masks.xy, result.boxes.conf.cpu().tolist(),
                                                result.boxes.cls.cpu().tolist(), result.masks.data.cpu().numpy()):
            polygon = Polygon(points) if len(points) >= 3 else None
            detections.append({'id': len(detections) + 1, 'clase': result.names[int(cls)], 'confianza': confidence,
                               'contorno_valido': bool(polygon is not None and polygon.is_valid),
                               'alerta': states[int(cls)] in ALERT_STATES if levels else None})
            masks.append(mask)
            if len(points) >= 3:
                color = ImageColor.getrgb(colors[int(cls)]) if levels else (0, 83, 226)
                draw.polygon([tuple(p) for p in points], fill=(*color, 35), outline=(*color, 255), width=line_width)
                badge(points, int(cls), len(detections))
    else:
        for box, confidence, cls in zip(result.boxes.xyxy.cpu().tolist(), result.boxes.conf.cpu().tolist(), result.boxes.cls.cpu().tolist()):
            detections.append({'id': len(detections) + 1, 'clase': result.names[int(cls)], 'confianza': confidence,
                               'contorno_valido': None, 'alerta': states[int(cls)] in ALERT_STATES if levels else None})
            color = ImageColor.getrgb(colors[int(cls)]) if levels else (0, 83, 226)
            draw.rectangle(box, outline=(*color, 255), width=line_width)
            badge([(box[0], box[1]), (box[2], box[3])], int(cls), len(detections))
    occupancy = None
    if config.get('occupancy'):
        from ocupacion_paulo import Analyzer, provenance
        version = config.get('occupancy_version', 'v1')
        analyzer = Analyzer(occupancy_rgb, version=version)
        for index, detection in enumerate(detections):
            detection['occupancy'] = analyzer.analyze(masks[index] if index < len(masks) else None,
                state=detection['clase'].removeprefix('Nivel_'), valid_contour=detection['contorno_valido'] is True)
        signal_image = Image.fromarray(analyzer.overlay())
        signal_draw = ImageDraw.Draw(signal_image)
        scale = signal_image.width / width
        signal_font = ImageFont.truetype(str(pilot.font_path()), max(18, min(30, round(signal_image.width / 44))))
        boxes = result.boxes.xyxy.cpu().tolist() if result.boxes is not None else []
        for index, detection in enumerate(detections):
            measurement = detection['occupancy']
            def percent(value):
                return f'{value:.1f}'.replace('.', ',') + ' %' if value is not None else 'Sin medición'
            if measurement['status'] == 'medido':
                label = (f"Nivel {detection['id']} · Ancho: {percent(measurement['width_signal_pct'])}\n"
                         f"Área: {percent(measurement['area_signal_pct'])} · señal experimental")
                if version == 'v2':
                    label = (f"Nivel {detection['id']} · Combinado: {percent(measurement['combined_signal_pct'])}\n"
                             f"Área: {percent(measurement['area_signal_pct'])} · Ancho: {percent(measurement['width_signal_pct'])}")
            else:
                label = f"Nivel {detection['id']} · Sin medición\nSeñal experimental"
            if index < len(masks) and np.any(masks[index]):
                ys, xs = np.where(masks[index]); left, top = xs.min(), ys.min()
            elif index < len(boxes):
                left, top = boxes[index][:2]
            else:
                continue
            padding, spacing = 7, 4
            label_font = signal_font
            bounds = signal_draw.multiline_textbbox((0, 0), label, font=label_font, spacing=spacing)
            available = max(1, signal_image.width - 2*padding - 2)
            if bounds[2] - bounds[0] > available:
                label_font = signal_font.font_variant(size=max(1, int(signal_font.size*available/(bounds[2]-bounds[0]))))
                bounds = signal_draw.multiline_textbbox((0, 0), label, font=label_font, spacing=spacing)
            label_width, label_height = bounds[2]-bounds[0]+2*padding, bounds[3]-bounds[1]+2*padding
            x = max(0, min(int(left*scale)+4, signal_image.width-label_width))
            y = max(0, min(int(top*scale)+4, signal_image.height-label_height))
            signal_draw.rounded_rectangle((x, y, x+label_width, y+label_height), radius=6,
                                          fill='#101923', outline='#ffc220', width=1)
            signal_draw.multiline_text((x+padding-bounds[0], y+padding-bounds[1]), label,
                                       font=label_font, fill='white', spacing=spacing)
        signal_image.save(job / 'paulo_senal.jpg', quality=90)
        Image.fromarray(analyzer.edges).save(job / 'paulo_bordes.png')
        Image.fromarray(analyzer.filtered_edges).save(job / 'paulo_bordes_niveles.png')
        occupancy = provenance(version, analyzer.p)
        import hashlib
        occupancy.update(input_kind='original_rgb_before_inference',
                         input_rgb_sha256=hashlib.sha256(occupancy_rgb.tobytes()).hexdigest())
    for x, y, w, h, title, number, number_width, padding, color, bounds in badges:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=h / 2,
                               fill=(255, 255, 255, 252), outline=(218, 226, 228, 255))
        inset = max(3, round(padding / 2))
        tint = tuple(round(channel * .14 + 255 * .86) for channel in color)
        draw.rounded_rectangle((x + inset, y + inset, x + inset + number_width, y + h - inset),
                               radius=(h - inset * 2) / 2, fill=(*tint, 255))
        draw.text((x + inset + number_width / 2, y + h / 2), number, font=font,
                  anchor='mm', fill=(24, 51, 59, 255))
        draw.text((x + number_width + padding * 2, y + (h - (bounds[3] - bounds[1])) / 2 - bounds[1]),
                  title, font=font, fill=(24, 51, 59, 255))
    Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB').save(job / 'prediccion.jpg', quality=90)
    truth, truth_classes, matches = [], [], []
    has_truth = 'truth_rows' in config or bool(config.get('truth'))
    if has_truth:
        from conjuntos import experiment_file
        reference_rows = config['truth_rows'] if 'truth_rows' in config else experiment_file(pilot.ROOT, config['truth']).read_text().splitlines()
        for line in reference_rows:
            truth_classes.append(int(line.split()[0]))
            values = list(map(float, line.split()[1:]))
            points = [(x * width, y * height) for x, y in zip(values[::2], values[1::2])]
            raster = Image.new('1', (width, height))
            ImageDraw.Draw(raster).polygon(points, fill=1)
            truth.append(np.asarray(raster, dtype=bool))
        pairs = sorted([(float(np.logical_and(t, m).sum() / max(1, np.logical_or(t, m).sum())), ti, pi)
                        for ti, t in enumerate(truth) for pi, m in enumerate(masks)], reverse=True)
        used_t, used_p = set(), set()
        for iou, ti, pi in pairs:
            if iou >= 0.5 and ti not in used_t and pi not in used_p:
                used_t.add(ti); used_p.add(pi); matches.append(iou)
    metrics = None
    if has_truth and set(model.names.values()) == {'Modulo'}:
        metrics = {'anotados': len(truth), 'aciertos': len(matches), 'omitidos': len(truth) - len(matches),
                   'extras': len(detections) - len(matches), 'iou_medio': sum(matches) / len(matches) if matches else 0}
    elif has_truth and levels:
        detail = evaluate_masks(list(zip(truth_classes, truth)),
            [(states.index(d['clase'].removeprefix('Nivel_')), m) for d, m in zip(detections, masks)], states=states)
        metrics = {'scope': 'Nivel_estados', 'anotados': detail['anotados'], 'aciertos': detail['aciertos'],
                   'omitidos': detail['omitidos'], 'extras': detail['falsos_positivos'],
                   'iou_medio': sum(m['iou_mascara'] for m in detail['parejas'])/max(1, len(detail['parejas'])),
                   'estados_acertados': detail['estados_acertados'], 'alertas_reales': detail['alertas_reales'],
                   'alertas_acertadas': detail['alertas_acertadas'], 'alertas_omitidas': detail['alertas_omitidas'],
                   'falsas_alertas': detail['falsas_alertas']}
    pilot.save_json(job / 'resultado.json', {'detecciones': detections, 'metricas': metrics,
                                            'config': config, 'imagen': 'prediccion.jpg',
                                            'level_states': list(states) if levels else None,
                                            **({'occupancy': occupancy, 'occupancy_image': 'paulo_senal.jpg',
                                                'occupancy_edges_image': 'paulo_bordes.png',
                                                'occupancy_filtered_edges_image': 'paulo_bordes_niveles.png'} if occupancy else {})})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('job', type=Path)
    execute(parser.parse_args().job)
