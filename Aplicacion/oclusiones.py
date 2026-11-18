"""Detección y evaluación de oclusiones frontales (personas, carros o intrusos).

Implementa la política de zonas obstruidas u ofuscadas (Sección 5.6):
- Si la obstrucción supera el 25 % del área o ancho del nivel, se deriva a
  `Revisar · zona obstruida` sin interpretarlo como falta de producto ni stock.
- Si la obstrucción es parcial (entre 5 % y 25 %), se descuentan esas celdas
  de la máscara evaluable en el estimador para medir solo el frente visible claro.
"""
import os
from pathlib import Path

import cv2
import numpy as np

OCCLUSION_POLICY = 'oclusiones_v1'
REVIEW_AREA_FRAC = 0.25
MIN_MASK_COL_FRAC = 0.05
COLUMN_OCCLUSION_FRAC = 0.35
COCO_OCCLUSION_CLASSES = (0,)  # person
COCO_OCCLUSION_CONF = 0.35
PHOTO_BLOCK_LEVEL_FRAC = 0.15
PHOTO_BLOCK_FRAME_FRAC = 0.10


def _resize_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    arr = np.asarray(mask) > 0
    if arr.shape == shape:
        return arr
    return cv2.resize(arr.astype(np.uint8), (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST) > 0


def evaluate_level_occlusion(
    level_mask: np.ndarray,
    external_occlusion_mask: np.ndarray | None = None,
) -> dict:
    """Medir intersección entre un polígono/máscara `Nivel` y una máscara de oclusión."""
    level_bool = np.asarray(level_mask) > 0
    level_pixels = int(level_bool.sum())
    if external_occlusion_mask is None or level_pixels == 0:
        return {
            'policy': OCCLUSION_POLICY,
            'occluded_area_frac': 0.0,
            'occluded_width_frac': 0.0,
            'occluded_col_frac_by_x': np.zeros(0, dtype=np.float32),
            'requires_review': False,
            'should_mask_columns': False,
        }

    occ_bool = _resize_mask(external_occlusion_mask, level_bool.shape)
    inter = level_bool & occ_bool
    occluded_area_frac = float(inter.sum()) / float(level_pixels)

    xs = np.flatnonzero(level_bool.any(axis=0))
    if len(xs) == 0:
        occluded_col_frac_by_x = np.zeros(0, dtype=np.float32)
        occluded_width_frac = 0.0
    else:
        x0, x1 = int(xs.min()), int(xs.max())
        sub_lvl = level_bool[:, x0:x1 + 1].sum(axis=0)
        sub_int = inter[:, x0:x1 + 1].sum(axis=0)
        occluded_col_frac_by_x = (sub_int / np.maximum(sub_lvl, 1)).astype(np.float32)
        active = sub_lvl > 0
        occluded_width_frac = (
            float((occluded_col_frac_by_x[active] > COLUMN_OCCLUSION_FRAC).mean())
            if active.any() else 0.0
        )

    requires_review = (
        occluded_area_frac >= REVIEW_AREA_FRAC
        or occluded_width_frac >= REVIEW_AREA_FRAC
    )
    should_mask_columns = (
        not requires_review
        and (
            occluded_area_frac >= MIN_MASK_COL_FRAC
            or occluded_width_frac >= MIN_MASK_COL_FRAC
        )
    )
    return {
        'policy': OCCLUSION_POLICY,
        'occluded_area_frac': round(occluded_area_frac, 4),
        'occluded_width_frac': round(occluded_width_frac, 4),
        'occluded_col_frac_by_x': occluded_col_frac_by_x,
        'requires_review': requires_review,
        'should_mask_columns': should_mask_columns,
    }


def _hsv_distance(a: np.ndarray, b: np.ndarray) -> float:
    dh = min(abs(float(a[0]) - float(b[0])), 180.0 - abs(float(a[0]) - float(b[0]))) * 2.0
    ds = float(a[1]) - float(b[1])
    dv = float(a[2]) - float(b[2])
    return float(np.sqrt(dh * dh + ds * ds + dv * dv))


def _contiguous_runs(flag: np.ndarray) -> list[tuple[int, int]]:
    runs = []
    idx = 0
    n = len(flag)
    while idx < n:
        if flag[idx]:
            end = idx + 1
            while end < n and flag[end]:
                end += 1
            runs.append((idx, end))
            idx = end
        else:
            idx += 1
    return runs


def detect_intrusions_from_rgb(
    rgb: np.ndarray | None,
    level_masks: list[np.ndarray | None],
) -> list[np.ndarray | None]:
    """Detectar intrusiones verticales frontales (persona o carro) que cruzan >= 2 niveles.

    Operación conservadora: únicamente marca una franja horizontal acotada (15%–60%
    del ancho) cuando el riel inter-nivel desaparece en un bloque vertical continuo
    con color HSV uniforme que atraviesa ambos niveles adyacentes y la brecha.
    """
    out: list[np.ndarray | None] = [None] * len(level_masks)
    if rgb is None or len(level_masks) < 2:
        return out

    h_img, w_img = rgb.shape[:2]
    entries = []
    for idx, mask in enumerate(level_masks):
        if mask is None:
            continue
        arr = np.asarray(mask)
        if arr.shape != (h_img, w_img):
            continue
        ys, xs = np.where(arr > 0)
        if not len(xs):
            continue
        entries.append((idx, int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max()), (ys.min() + ys.max()) * 0.5))

    if len(entries) < 2:
        return out

    entries.sort(key=lambda item: item[5])
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
    gy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)

    for pos in range(len(entries) - 1):
        up_idx, up_y0, up_y1, up_x0, up_x1, _ = entries[pos]
        lo_idx, lo_y0, lo_y1, lo_x0, lo_x1, _ = entries[pos + 1]
        ox0 = max(up_x0, lo_x0)
        ox1 = min(up_x1, lo_x1) + 1
        span_w = ox1 - ox0
        if span_w < max(32, int(0.40 * min(up_x1 - up_x0 + 1, lo_x1 - lo_x0 + 1))):
            continue

        gap_h = lo_y0 - up_y1
        if not (4 <= gap_h <= 80):
            continue
        gy0 = max(0, up_y1 - 2)
        gy1 = min(h_img, lo_y0 + 2)
        if gy1 - gy0 < 4:
            continue

        col_gy = gy[gy0:gy1, ox0:ox1].mean(axis=0)
        col_gx = gx[gy0:gy1, ox0:ox1].mean(axis=0)
        rail_gy_ref = float(np.percentile(col_gy, 75))
        rail_gx_ref = float(np.percentile(col_gx, 50))
        if rail_gy_ref <= 28.0 or rail_gy_ref <= 1.8 * max(rail_gx_ref, 1.0):
            continue

        broken = (col_gy < 0.35 * rail_gy_ref) & ((col_gy < 8.0) | (col_gy < 0.30 * col_gx))
        unbroken = ~broken
        if int(unbroken.sum()) < max(12, int(0.25 * span_w)):
            continue
        rail_hsv = np.median(hsv[gy0:gy1, ox0:ox1][:, unbroken, :], axis=(0, 1))

        for s0, s1 in _contiguous_runs(broken):
            run_frac = float(s1 - s0) / float(span_w)
            if not (0.15 <= run_frac <= 0.60):
                continue
            gap_hsv = np.median(hsv[gy0:gy1, ox0 + s0:ox0 + s1, :], axis=(0, 1))
            if _hsv_distance(gap_hsv, rail_hsv) <= 45.0:
                continue
            up_hsv = np.median(hsv[up_y0:up_y1 + 1, ox0 + s0:ox0 + s1, :], axis=(0, 1))
            lo_hsv = np.median(hsv[lo_y0:lo_y1 + 1, ox0 + s0:ox0 + s1, :], axis=(0, 1))
            if _hsv_distance(up_hsv, gap_hsv) < 35.0 and _hsv_distance(lo_hsv, gap_hsv) < 35.0:
                for target_idx, ty0, ty1 in ((up_idx, up_y0, up_y1), (lo_idx, lo_y0, lo_y1)):
                    if out[target_idx] is None:
                        out[target_idx] = np.zeros((h_img, w_img), dtype=np.uint8)
                    out[target_idx][ty0:ty1 + 1, ox0 + s0:ox0 + s1] = 1
    return out


def load_coco_occlusion_model(weights_path: Path | str):
    """Cargar YOLO26n-seg COCO local sin habilitar descargas automáticas ni rastreadores."""
    os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
    from ultralytics import YOLO, settings

    settings.update({'sync': False, 'wandb': False, 'mlflow': False, 'tensorboard': False})
    return YOLO(str(weights_path))


def detect_person_union_mask(
    rgb: np.ndarray | None,
    model=None,
    device: str | int = 'cpu',
    conf: float = COCO_OCCLUSION_CONF,
    classes: tuple[int, ...] = COCO_OCCLUSION_CLASSES,
) -> np.ndarray | None:
    """Segmentar personas en primer plano (clase COCO `person`) y devolver máscara unión."""
    if model is None or rgb is None:
        return None

    h_img, w_img = rgb.shape[:2]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    result = model.predict(
        bgr,
        imgsz=640,
        conf=float(conf),
        iou=0.5,
        classes=list(classes),
        retina_masks=True,
        device=device,
        verbose=False,
        save=False,
    )[0]

    occ_union = np.zeros((h_img, w_img), dtype=np.uint8)
    masks_obj = getattr(result, 'masks', None)
    if masks_obj is not None and getattr(masks_obj, 'data', None) is not None:
        raw_occ = masks_obj.data.cpu().numpy()
        for occ_m in raw_occ:
            resized = _resize_mask(occ_m > 0.5, (h_img, w_img))
            occ_union |= resized.astype(np.uint8)
    elif getattr(result, 'boxes', None) is not None and getattr(result.boxes, 'xyxy', None) is not None:
        for box in result.boxes.xyxy.cpu().tolist():
            x0 = max(0, min(w_img, int(round(box[0]))))
            y0 = max(0, min(h_img, int(round(box[1]))))
            x1 = max(0, min(w_img, int(round(box[2]))))
            y1 = max(0, min(h_img, int(round(box[3]))))
            if x1 > x0 and y1 > y0:
                occ_union[y0:y1, x0:x1] = 1
    return occ_union if occ_union.any() else None


def extract_person_polygons(
    person_mask: np.ndarray | None,
    min_area_frac: float = 0.005,
    max_polygons: int = 4,
) -> list[list[list[float]]]:
    """Extraer contornos simplificados `[x, y]` de la máscara de persona para overlay sutil."""
    if person_mask is None:
        return []
    mask_u8 = (np.asarray(person_mask) > 0).astype(np.uint8)
    h, w = mask_u8.shape[:2]
    if h == 0 or w == 0 or not mask_u8.any():
        return []
    contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = max(16.0, float(h * w) * float(min_area_frac))
    contours = sorted((c for c in contours if cv2.contourArea(c) >= min_area), key=cv2.contourArea, reverse=True)
    polygons: list[list[list[float]]] = []
    for cnt in contours[:max_polygons]:
        eps = max(2.0, 0.006 * cv2.arcLength(cnt, True))
        approx = cv2.approxPolyDP(cnt, eps, True)
        pts = approx.reshape(-1, 2)
        if len(pts) < 3:
            continue
        polygons.append([[round(float(x), 1), round(float(y), 1)] for x, y in pts])
    return polygons


def draw_subtle_person_overlay(image, person_polygons: list[list[list[float]]]):
    """Dibujar silueta translúcida ámbar sutil sobre la imagen anotada cuando hay obstrucción."""
    if not person_polygons:
        return image
    from PIL import Image, ImageDraw

    base = image.convert('RGBA')
    overlay = Image.new('RGBA', base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, 'RGBA')
    width = max(2, int(round(max(base.size) / 480)))
    for poly in person_polygons:
        if len(poly) < 3:
            continue
        pts = [(float(p[0]), float(p[1])) for p in poly]
        draw.polygon(pts, fill=(255, 191, 81, 38), outline=(255, 204, 107, 190), width=width)
    return Image.alpha_composite(base, overlay).convert('RGB')


def photo_blocked_by_person(
    level_masks: list[np.ndarray | None],
    person_mask: np.ndarray | None,
    img_shape: tuple[int, int],
    min_level_frac: float = PHOTO_BLOCK_LEVEL_FRAC,
    min_frame_frac_if_no_levels: float = PHOTO_BLOCK_FRAME_FRAC,
) -> dict:
    """Determinar si una persona obstruye la góndola lo suficiente para marcar `no_evaluable`."""
    if person_mask is None:
        return {'blocked': False, 'max_level_occlusion_frac': 0.0, 'frame_person_frac': 0.0, 'reason': ''}
    resized_person = _resize_mask(person_mask, img_shape)
    frame_frac = float(resized_person.mean()) if resized_person.size else 0.0

    valid_levels = [lm for lm in (level_masks or []) if lm is not None]
    if not valid_levels:
        blocked = frame_frac >= min_frame_frac_if_no_levels
        return {
            'blocked': blocked,
            'max_level_occlusion_frac': 0.0,
            'frame_person_frac': round(frame_frac, 4),
            'reason': 'Persona obstruyendo la góndola o la cámara. Toma otra foto despejada.' if blocked else '',
        }

    max_lvl = 0.0
    max_w = 0.0
    for lm in valid_levels:
        ev = evaluate_level_occlusion(lm, resized_person)
        max_lvl = max(max_lvl, float(ev['occluded_area_frac']))
        max_w = max(max_w, float(ev['occluded_width_frac']))
    blocked = max_lvl >= min_level_frac or max_w >= min_level_frac
    return {
        'blocked': blocked,
        'max_level_occlusion_frac': round(max_lvl, 4),
        'frame_person_frac': round(frame_frac, 4),
        'reason': 'Persona obstruyendo la góndola. Toma otra foto despejada.' if blocked else '',
    }


def detect_coco_occlusions(
    rgb: np.ndarray | None,
    level_masks: list[np.ndarray | None],
    model=None,
    device: str | int = 'cpu',
    conf: float = COCO_OCCLUSION_CONF,
    classes: tuple[int, ...] = COCO_OCCLUSION_CLASSES,
) -> list[np.ndarray | None]:
    """Detectar personas en primer plano con YOLO COCO y devolver máscaras por nivel.

    Si no se proporciona `model` o no hay detecciones COCO, recurre a la detección
    geométrica/cromática `detect_intrusions_from_rgb`.
    """
    if model is None or rgb is None or not level_masks:
        return detect_intrusions_from_rgb(rgb, level_masks)

    occ_union = detect_person_union_mask(rgb, model=model, device=device, conf=conf, classes=classes)
    if occ_union is not None and occ_union.any():
        return [occ_union if lm is not None else None for lm in level_masks]
    return detect_intrusions_from_rgb(rgb, level_masks)
