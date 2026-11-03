"""Filtro opcional de visibilidad: falla cerrado sin candidato verificado."""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageOps

BASE_SHA256 = '0dd6f8dbc448870ac98a3cbb7156f923f7ce21fed3755d4019169ffffd279e81'
POLICY = 'visibilidad_foto_v1'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def full_frame(image):
    rgba = ImageOps.exif_transpose(image).convert('RGBA')
    image = Image.new('RGB', rgba.size, 'white')
    image.paste(rgba, mask=rgba.getchannel('A'))
    image.thumbnail((4096, 4096))
    return ImageOps.pad(image, (640, 640), method=Image.Resampling.BILINEAR,
                        color=(114, 114, 114), centering=(.5, .5))


def load(root):
    """Cargar pesos locales validados; no descarga ni acepta rutas externas."""
    folder = (Path(root) / 'modelos').resolve()
    config_path = folder / 'visibilidad_experimental.json'
    if not config_path.is_file():
        raise ValueError('El filtro experimental aún no tiene un candidato validado.')
    raw_config = config_path.read_bytes()
    config = json.loads(raw_config.decode('utf-8'))
    if config.get('policy') != POLICY or config.get('base_sha256') != BASE_SHA256:
        raise ValueError('La configuración del filtro experimental no es válida.')
    threshold = config.get('threshold')
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not .5 <= threshold <= .99:
        raise ValueError('El umbral del filtro experimental no es válido.')
    paths = []
    for field, expected in [('base_file', BASE_SHA256), ('model_file', config.get('model_sha256'))]:
        name = config.get(field)
        if not isinstance(name, str) or not isinstance(expected, str):
            raise ValueError('Faltan los pesos del filtro experimental.')
        path = (folder / name).resolve()
        if not path.is_relative_to(folder) or not path.is_file() or digest(path) != expected:
            raise ValueError('Los pesos del filtro experimental no coinciden con su registro.')
        paths.append(path)
    return config, paths, hashlib.sha256(raw_config).hexdigest()


def assess(image, root):
    """Devolver estado y huella del clasificador sin exponer su puntuación."""
    import os
    os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
    import numpy as np
    import torch
    from torch import nn
    from ultralytics import YOLO, settings
    config, (base_path, model_path), revision = load(root)
    settings.update({'sync': False, 'wandb': False, 'mlflow': False, 'tensorboard': False})
    network = YOLO(str(base_path)).model
    head = network.model[-1]
    head.linear = nn.Linear(head.linear.in_features, 2)
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)
    if checkpoint.get('classes') != {'no_apta': 0, 'apta': 1} or checkpoint.get('base_sha256') != BASE_SHA256:
        raise ValueError('El candidato de visibilidad no coincide con la política.')
    network.load_state_dict(checkpoint['state_dict'], strict=True)
    network.eval()
    tensor = torch.from_numpy(np.asarray(full_frame(image)).copy()).permute(2, 0, 1).float().div_(255).unsqueeze(0)
    with torch.inference_mode():
        output = network(tensor)
        scores = output[0] if isinstance(output, tuple) else output.softmax(1)
    if tuple(scores.shape) != (1, 2):
        raise ValueError('El filtro experimental devolvió una salida inválida.')
    score = float(scores[0, 1])
    if not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError('El filtro experimental devolvió una puntuación inválida.')
    state = 'no_apta' if score < .5 else 'apta' if score >= config['threshold'] else 'dudosa'
    return {'estado': state, 'politica': POLICY, 'clasificador': config['model_sha256'],
            'revision': revision}
