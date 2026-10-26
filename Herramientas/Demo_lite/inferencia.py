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

from PIL import Image, ImageOps, UnidentifiedImageError

try:
    from presentacion_niveles import draw_result, occupancy_estimate, spatial_order, font_for, STATES
except ModuleNotFoundError as error:
    if error.name != 'presentacion_niveles':
        raise
    # En el ZIP va junto a inferencia.py; en desarrollo se comparte con el panel.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Modelos'))
    from presentacion_niveles import draw_result, occupancy_estimate, spatial_order, font_for, STATES

MAX_BYTES = 15 * 1024 * 1024
MAX_PIXELS = 24_000_000
V1_CLASSES = ('Nivel_vacio', 'Nivel_baja_disponibilidad', 'Nivel_suficiente', 'Nivel_no_evaluable')
V2_CLASSES = ('Nivel_reponer', 'Nivel_suficiente')
CLASS_PROFILES = (set(V1_CLASSES), set(V2_CLASSES), set((*V2_CLASSES, 'Nivel_no_evaluable')), {'Nivel'})


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
            legacy_sources = {'ocupacion_paulo.py', 'gondola_bordes.py'}
            if set(sources) not in (legacy_sources, legacy_sources | {'gondola_combinacion_ponderada.py'}):
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
                if classes == ['Nivel']:
                    value.update(geometry_only=True, minimum_confidence=.6, default_confidence=.6,
                                 note='Localiza niveles. La ocupación y las recomendaciones se estiman con bordes; confirma la visibilidad de la foto.')
            models.append(value)
        return models

    def analyze(self, body, model_id=None, confidence=None, method='yolo', visibility=None):
        if model_id is None:
            model_id = self.manifest['default_model']
        if model_id not in self.entries:
            raise ValueError('Elige uno de los modelos incluidos.')
        geometry = self.entries[model_id].get('classes') == ['Nivel']
        if confidence is None:
            confidence = .6 if geometry else .25
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not .01 <= confidence <= .99:
            raise ValueError('La confianza debe estar entre 0,01 y 0,99.')
        if method not in ('yolo', 'yolo_paulo', 'yolo_paulo_v2'):
            raise ValueError('Elige YOLO o YOLO + detección de bordes.')
        if geometry:
            from vision_v3 import visibility_check
            visibility_check(visibility)
            if confidence < .6:
                raise ValueError('La confianza mínima de V3 es 0,60.')
        if not self.lock.acquire(blocking=False):
            raise BusyError('Ya hay una foto en análisis. Espera a que termine.')
        try:
            image = read_photo(body)
            if geometry and visibility == 'person':
                from vision_v3 import person_result
                return person_result(image, model_id, method)
            if method in ('yolo_paulo', 'yolo_paulo_v2'):
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
            if method in ('yolo_paulo', 'yolo_paulo_v2') and not (geometry and visibility == 'occluded'):
                extra = analyze_edges(original_rgb, result, detections, version='v2' if method == 'yolo_paulo_v2' else 'v1')
            if geometry:
                from vision_v3 import apply_scope
                apply_scope(detections, visibility, image.width, image.height)
            if extra or (geometry and visibility == 'occluded'):
                annotated, _ = draw_result(image, result, measurements=detections)
            counts = Counter(d['state'] for d in detections)
            return {'image': annotated, 'model': model_id, 'device': 'GPU' if device == 0 else 'CPU',
                    'seconds': round(time.perf_counter() - started, 2), 'detections': detections,
                    'counts': {STATES[c][0]: counts[STATES[c][0]] for c in self.entries[model_id].get('classes', V1_CLASSES)},
                    'width': image.width, 'height': image.height, 'method': method,
                    'geometry_only': geometry, 'visibility': visibility,
                    'visibility_source': 'user' if geometry else None, **extra}
        finally:
            self.lock.release()


def analyze_edges(original_rgb, result, detections, version='v1'):
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
    analyzer = Analyzer(original_rgb, version=version)
    masks = result.masks.data.cpu().numpy() if result.masks is not None else []
    if getattr(result, 'boxes', None) is not None and len(masks):
        order = spatial_order(result.boxes.xyxy.cpu().tolist())
        masks = [masks[i] for i in order if i < len(masks)]
    for index, detection in enumerate(detections):
        mask = (masks[index] > .5).astype('uint8') if index < len(masks) else None
        detection['occupancy'] = analyzer.analyze(mask, state=detection['state'])
        detection['occupancy_estimate'] = occupancy_estimate(detection['occupancy'], version)
    return {'occupancy': provenance(version, analyzer.p), 'occupancy_image': Image.fromarray(analyzer.overlay()),
            'edges_image': Image.fromarray(analyzer.edges),
            'filtered_edges_image': Image.fromarray(analyzer.filtered_edges)}
