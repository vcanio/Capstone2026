"""Presentación compartida por Walmart Visión y el laboratorio de modelos."""
import math
from pathlib import Path
from PIL import Image, ImageColor, ImageDraw, ImageFont
from geometria_niveles import level_quadrilateral

STATES = {
    'Nivel': ('detectado', 'Nivel detectado', '#2563eb'),
    'Nivel_reponer': ('reponer', 'Reponer', '#dc2626'),
    'Nivel_vacio': ('vacio', 'Vacío', '#dc2626'),
    'Nivel_baja_disponibilidad': ('baja_disponibilidad', 'Baja disponibilidad', '#f59e0b'),
    'Nivel_suficiente': ('suficiente', 'Suficiente', '#16a34a'),
    'Nivel_no_evaluable': ('no_evaluable', 'No evaluable', '#64748b'),
}


def font_for(size):
    for path in ('C:/Windows/Fonts/arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def spatial_order(boxes):
    """Ordenar niveles de abajo hacia arriba (nivel 1 abajo) y de izquierda a derecha en cada fila."""
    centers = [(index, (box[1] + box[3]) / 2, max(1, box[3] - box[1]), box[0])
               for index, box in enumerate(boxes)]
    rows = []
    for index, center, height, left in sorted(centers, key=lambda item: (item[1], item[3])):
        if rows and abs(center - rows[-1][0]) <= .5 * min(height, rows[-1][1]):
            rows[-1][2].append((left, center, index))
        else:
            rows.append((center, height, [(left, center, index)]))
    return [index for _, _, items in reversed(rows) for _, _, index in sorted(items)]


def occupancy_estimate(measurement, version='v1'):
    """Lectura de presentación; conserva la predicción YOLO por separado."""
    field = 'combined_signal_pct' if version == 'v2' else 'area_signal_pct'
    value = measurement.get(field)
    if (measurement.get('status') != 'medido' or isinstance(value, bool) or
            not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100):
        return {'pct': None, 'state': 'sin_medicion', 'label': 'Sin medición', 'color': '#64748b'}
    if measurement.get('review_required'):
        return {'pct': None, 'state': 'revisar', 'label': 'Revisar · señal ambigua', 'color': '#a16207'}
    low = value < 30
    return {'pct': value, 'state': 'reponer' if low else 'suficiente',
            'label': 'Reponer' if low else 'Suficiente', 'color': '#dc2626' if low else '#16a34a'}


def draw_result(image, result, measurements=None):
    overlay = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(overlay)
    font = font_for(max(16, round(max(image.size) / 54)))
    line_width = max(2, round(max(image.size) / 650))
    detections, badges = [], []
    boxes = result.boxes
    if boxes is not None:
        polygons = result.masks.xy if result.masks is not None else None
        xyxy, confs, clss = boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist(), boxes.cls.cpu().tolist()
        for level_id, index in enumerate(spatial_order(xyxy), 1):
            box, confidence, cls = xyxy[index], confs[index], clss[index]
            name = result.names[int(cls)]
            if name not in STATES:
                raise ValueError('El modelo no contiene los estados de disponibilidad de este paquete.')
            state, label, hex_color = STATES[name]
            reading = measurements[level_id - 1].get('occupancy_estimate') if measurements is not None else None
            if reading:
                hex_color = reading['color']
            color = ImageColor.getrgb(hex_color)
            points = [tuple(map(float, point)) for point in polygons[index]] if polygons is not None else [
                (box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
            quad = level_quadrilateral(points, image.size) if polygons is not None and name != 'Nivel' else None
            if quad is not None:
                points = [tuple(point) for point in quad]
            detections.append({'id': level_id, 'state': state, 'label': label, 'confidence': float(confidence),
                               'display_polygon': points, 'contour_adjusted': quad is not None})
            if len(points) < 3:
                continue
            draw.polygon(points, fill=(*color, 35), outline=(*color, 255), width=line_width)
            title = label
            if reading:
                pct = (f"{reading['pct']:.2f}".rstrip('0').rstrip('.').replace('.', ',')
                       if reading['pct'] is not None else None)
                if name == 'Nivel' and reading['pct'] is not None:
                    pct = str(round(reading['pct']))
                title = f"{pct} % · {reading['label']}" if pct is not None else reading['label']
            bounds = draw.textbbox((0, 0), title, font=font)
            text_height = font.getbbox('Ágj')[3] - font.getbbox('Ágj')[1]
            padding = max(5, round(font.size * .35))
            h = text_height + padding * 2
            number = str(level_id)
            number_width = max(h - padding, round(draw.textlength(number, font=font)) + padding * 2)
            w = round(draw.textlength(title, font=font)) + number_width + padding * 4
            x = max(0, min(min(p[0] for p in points) + 5, image.width - w))
            y = max(0, min(min(p[1] for p in points) + 5, image.height - h))
            badges.append((x, y, w, h, title, number, number_width, padding, color, bounds))
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
                  title, font=font, fill=(*tuple(round(channel * .65) for channel in color), 255)
                  if measurements is not None else (24, 51, 59, 255))
    return Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB'), detections


