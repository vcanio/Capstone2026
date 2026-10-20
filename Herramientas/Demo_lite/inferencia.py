"""Inferencia autónoma: pesos del paquete y fotografías en memoria."""
from collections import Counter
from io import BytesIO
import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time
import warnings

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

MAX_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 24_000_000
STATES = {
    'Nivel_reponer': ('reponer', 'Reponer', '#dc2626'),
    'Nivel_vacio': ('vacio', 'Vacío', '#dc2626'),
    'Nivel_baja_disponibilidad': ('baja_disponibilidad', 'Baja disponibilidad', '#f59e0b'),
    'Nivel_suficiente': ('suficiente', 'Suficiente', '#16a34a'),
    'Nivel_no_evaluable': ('no_evaluable', 'No evaluable', '#64748b'),
}
V1_CLASSES = ('Nivel_vacio', 'Nivel_baja_disponibilidad', 'Nivel_suficiente', 'Nivel_no_evaluable')
V2_CLASSES = ('Nivel_reponer', 'Nivel_suficiente')
CLASS_PROFILES = (set(V1_CLASSES), set(V2_CLASSES), set((*V2_CLASSES, 'Nivel_no_evaluable')))


class BusyError(ValueError):
    pass


def read_photo(body):
    if not body or len(body) > MAX_BYTES:
        raise ValueError('Elige una foto de hasta 15 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(body)) as source:
                if source.format not in ('JPEG', 'PNG', 'WEBP') or getattr(source, 'n_frames', 1) != 1:
                    raise ValueError('Usa una foto JPG, PNG o WebP sin animación.')
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError('La foto supera los 24 megapíxeles. Reduce su tamaño y vuelve a intentarlo.')
                source.load()
                rgba = ImageOps.exif_transpose(source).convert('RGBA')
                image = Image.new('RGB', rgba.size, 'white')
                image.paste(rgba, mask=rgba.getchannel('A'))
                image.thumbnail((4096, 4096))
                return image
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('No pudimos abrir la imagen. Prueba con un JPG, PNG o WebP válido.') from None


def font_for(size):
    for path in ('C:/Windows/Fonts/arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def draw_result(image, result):
    overlay = Image.new('RGBA', image.size)
    draw = ImageDraw.Draw(overlay)
    font = font_for(max(16, round(max(image.size) / 54)))
    line_width = max(2, round(max(image.size) / 650))
    detections, badges = [], []
    boxes = result.boxes
    if boxes is not None:
        polygons = result.masks.xy if result.masks is not None else None
        for index, (box, confidence, cls) in enumerate(zip(boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist(), boxes.cls.cpu().tolist())):
            name = result.names[int(cls)]
            if name not in STATES:
                raise ValueError('El modelo no contiene los estados de disponibilidad de este paquete.')
            state, label, hex_color = STATES[name]
            color = ImageColor.getrgb(hex_color)
            points = [tuple(map(float, point)) for point in polygons[index]] if polygons is not None else [
                (box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])]
            detections.append({'id': index + 1, 'state': state, 'label': label, 'confidence': float(confidence)})
            if len(points) < 3:
                continue
            draw.polygon(points, fill=(*color, 35), outline=(*color, 255), width=line_width)
            title = label
            bounds = draw.textbbox((0, 0), title, font=font)
            text_height = font.getbbox('Ágj')[3] - font.getbbox('Ágj')[1]
            padding = max(5, round(font.size * .35))
            h = text_height + padding * 2
            number = str(index + 1)
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
                  title, font=font, fill=(24, 51, 59, 255))
    return Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB'), detections


class ModelRunner:
    def __init__(self, directory=None, device='auto'):
        self.root = Path(directory or Path(__file__).resolve().parent).resolve()
        config = self.root / '.runtime/config'
        config.mkdir(parents=True, exist_ok=True)
        os.environ['YOLO_CONFIG_DIR'] = str(config)
        os.environ['MPLCONFIGDIR'] = str(config / 'matplotlib')
        self.device = device
        self.lock = threading.Lock()
        self.models = {}
        self.manifest = json.loads((self.root / 'modelos.json').read_text(encoding='utf-8'))
        self.entries = {item['id']: item for item in self.manifest['models']}
        if 'edge_sources' in self.manifest:
            sources = self.manifest['edge_sources']
            if set(sources) != {'ocupacion_paulo.py', 'gondola_bordes.py'}:
                raise ValueError('El manifiesto de bordes no corresponde a este paquete.')
            for name, expected in sources.items():
                path = self.root / name
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                    raise ValueError('El análisis de bordes está incompleto o modificado. Extrae otra vez el ZIP.')
        for entry in self.entries.values():
            path = (self.root / entry['file']).resolve()
            if not path.is_relative_to(self.root / 'modelos') or not path.is_file():
                raise ValueError(f"Falta el modelo {entry['id']}. Extrae el ZIP completo.")
            with path.open('rb') as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != entry['sha256']:
                    raise ValueError(f"El modelo {entry['id']} está incompleto o modificado. Extrae otra vez el ZIP.")

    def available(self):
        models = []
        for item in self.entries.values():
            value = {'id': item['id'], 'name': item['name']}
            if 'classes' in item:
                classes = item['classes']
                if set(classes) not in CLASS_PROFILES:
                    raise ValueError('Perfil de clases no admitido en el manifiesto.')
                value.update(states=[dict(zip(('key', 'label', 'color'), STATES[c])) for c in classes],
                             guide=item.get('guide', 'v1.3'),
                             note=('Este modelo base distingue reponer y suficiente; no reconoce no evaluable.'
                                   if set(classes) == set(V2_CLASSES) else 'No evaluable se comunica por separado y no significa vacío.'))
            models.append(value)
        return models

    def analyze(self, body, model_id='YOLO26-1', confidence=0.25, method='yolo'):
        if model_id not in self.entries:
            raise ValueError('Elige uno de los modelos incluidos.')
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not .01 <= confidence <= .99:
            raise ValueError('La confianza debe estar entre 0,01 y 0,99.')
        if method not in ('yolo', 'yolo_paulo'):
            raise ValueError('Elige YOLO o YOLO + detección de bordes.')
        if not self.lock.acquire(blocking=False):
            raise BusyError('Ya hay una foto en análisis. Espera a que termine.')
        try:
            image = read_photo(body)
            if method == 'yolo_paulo':
                import numpy as np
                original_rgb = np.asarray(image).copy()
            # No external experiment trackers or downloads are required to predict.
            os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
            import torch
            from ultralytics import YOLO, settings
            settings.update({'sync': False, 'wandb': False, 'mlflow': False, 'tensorboard': False})
            device = 0 if self.device == 'auto' and torch.cuda.is_available() else 'cpu'
            if model_id not in self.models:
                model = YOLO(str(self.root / self.entries[model_id]['file']))
                expected_classes = set(self.entries[model_id].get('classes', V1_CLASSES))
                if expected_classes not in CLASS_PROFILES or set(model.names.values()) != expected_classes:
                    raise ValueError('Las clases del modelo no corresponden a niveles y disponibilidad.')
                self.models[model_id] = model
            started = time.perf_counter()
            result = self.models[model_id].predict(image, imgsz=640, conf=float(confidence), iou=.7,
                                                  retina_masks=True, device=device, verbose=False, save=False)[0]
            annotated, detections = draw_result(image, result)
            extra = {}
            if method == 'yolo_paulo':
                extra = analyze_edges(original_rgb, result, detections)
            counts = Counter(d['state'] for d in detections)
            return {'image': annotated, 'model': model_id, 'device': 'GPU' if device == 0 else 'CPU',
                    'seconds': round(time.perf_counter() - started, 2), 'detections': detections,
                    'counts': {STATES[c][0]: counts[STATES[c][0]] for c in self.entries[model_id].get('classes', V1_CLASSES)},
                    'width': image.width, 'height': image.height, 'method': method, **extra}
        finally:
            self.lock.release()


def analyze_edges(original_rgb, result, detections):
    """Reutiliza el algoritmo de detección de bordes sin dibujar sobre la entrada ni guardar fotos."""
    # En el ZIP ambos archivos se copian junto a inferencia.py. En el laboratorio
    # se usa el mismo módulo de Modelos; no se mantiene otra implementación.
    try:
        from ocupacion_paulo import Analyzer, provenance
    except ModuleNotFoundError as error:
        if error.name != 'ocupacion_paulo':
            raise
        import importlib.util
        import sys
        path = Path(__file__).resolve().parents[1] / 'Modelos/ocupacion_paulo.py'
        spec = importlib.util.spec_from_file_location('ocupacion_paulo', path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        Analyzer, provenance = module.Analyzer, module.provenance
    analyzer = Analyzer(original_rgb)
    masks = result.masks.data.cpu().numpy() if result.masks is not None else []
    for index, detection in enumerate(detections):
        mask = (masks[index] > .5).astype('uint8') if index < len(masks) else None
        detection['occupancy'] = analyzer.analyze(mask, state=detection['state'])
    return {'occupancy': provenance(), 'occupancy_image': Image.fromarray(analyzer.overlay()),
            'edges_image': Image.fromarray(analyzer.edges),
            'filtered_edges_image': Image.fromarray(analyzer.filtered_edges)}
