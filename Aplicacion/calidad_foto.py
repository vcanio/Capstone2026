"""Chequeo determinista de calidad fotográfica (nitidez y exposición) previo a inferencia."""
import cv2
import numpy as np
from PIL import Image

QUALITY_POLICY = 'calidad_foto_v1'
TARGET_MAX_SIDE = 1024
MIN_AUTO_CHECK_SIDE = 240

# Umbrales conservadores calibrados sobre 294 capturas reales válidas (0 rechazos en train/val/Ohiggins 3):
# mínimos reales observados: lap_var >= 285.14, tenengrad >= 11555.24, v_mean in [109.65, 171.28],
# dark_frac <= 0.1925, blown_frac <= 0.0365.
BLUR_LAP_VAR_MIN = 120.0
BLUR_SOFT_LAP_VAR_MIN = 180.0
BLUR_SOFT_TENENGRAD_MIN = 8000.0
DARK_V_MEAN_MIN = 45.0
DARK_MODERATE_V_MEAN_MIN = 65.0
DARK_FRAC_MAX = 0.55
BRIGHT_V_MEAN_MAX = 225.0
BLOWN_FRAC_MAX = 0.30


def measure_photo_quality(image: Image.Image) -> dict:
    """Medir nitidez (Laplaciano/Tenengrad) y exposición (HSV) normalizando la escala a 1024 px."""
    rgb = np.asarray(image.convert('RGB'))
    h, w = rgb.shape[:2]
    scale = TARGET_MAX_SIDE / float(max(h, w, 1))
    if scale < 1.0:
        resized = cv2.resize(
            rgb,
            (max(1, round(w * scale)), max(1, round(h * scale))),
            interpolation=cv2.INTER_AREA,
        )
    else:
        resized = rgb

    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(resized, cv2.COLOR_RGB2HSV)

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    tenengrad = float(np.mean(gx * gx + gy * gy))

    v = hsv[..., 2]
    s = hsv[..., 1]
    return {
        'lap_var': round(lap_var, 2),
        'tenengrad': round(tenengrad, 2),
        'v_mean': round(float(v.mean()), 2),
        'dark_frac': round(float((v < 25).mean()), 4),
        'blown_frac': round(float(((v > 248) & (s < 30)).mean()), 4),
    }


def assess_photo_quality(image: Image.Image) -> dict:
    """Evaluar si la captura es legible antes de localizar niveles y medir ocupación."""
    metrics = measure_photo_quality(image)
    v_mean = metrics['v_mean']
    dark_frac = metrics['dark_frac']
    blown_frac = metrics['blown_frac']
    lap_var = metrics['lap_var']
    tenengrad = metrics['tenengrad']

    if v_mean < DARK_V_MEAN_MIN or (v_mean < DARK_MODERATE_V_MEAN_MIN and dark_frac > DARK_FRAC_MAX):
        return {
            'usable': False,
            'status': 'subexpuesta',
            'reason': 'Foto demasiado oscura para evaluar la góndola. Toma otra con mejor iluminación.',
            'policy': QUALITY_POLICY,
            'metrics': metrics,
        }
    if v_mean > BRIGHT_V_MEAN_MAX or blown_frac > BLOWN_FRAC_MAX:
        return {
            'usable': False,
            'status': 'sobreexpuesta',
            'reason': 'Foto demasiado brillante o con reflejo extremo para evaluar la góndola. Toma otra foto.',
            'policy': QUALITY_POLICY,
            'metrics': metrics,
        }
    if lap_var < BLUR_LAP_VAR_MIN or (lap_var < BLUR_SOFT_LAP_VAR_MIN and tenengrad < BLUR_SOFT_TENENGRAD_MIN):
        return {
            'usable': False,
            'status': 'desenfoque',
            'reason': 'Foto demasiado borrosa o movida para evaluar la góndola. Toma otra foto nítida.',
            'policy': QUALITY_POLICY,
            'metrics': metrics,
        }
    return {
        'usable': True,
        'status': 'ok',
        'reason': '',
        'policy': QUALITY_POLICY,
        'metrics': metrics,
    }
