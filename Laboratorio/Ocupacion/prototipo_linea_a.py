"""Prototipo Línea A para calibración de ocupación por nivel (solo Laboratorio).

Reutiliza el preprocesamiento de grilla y exclusión de rieles/barandas de
`Aplicacion/ocupacion_paulo.py`, reemplazando el núcleo decisor por:
1. Normalización anclada a nivel de góndola con pisos físicos de ruido y techos
   mínimos de paquete abastecido (evita amplificar ruido o restar envases lisos).
2. Evidencia híbrida (umbrales físicos absolutos + intensidad normalizada) medida
   sobre el cuerpo vertical útil del nivel (excluyendo cabeza vacía y labio).
3. Penalización continua por el mayor hueco horizontal vacío (`max_gap_pct`).
4. Abstención `revisar` restringida a casos sobre umbral con señal ambigua
   (cartel superior, periferia sin centro o cartel colgante con banda central vacía),
   evitando atrapar niveles verdaderamente vacíos en revisión.
5. Umbral de reposición calibrado (`CALIBRATED_THRESHOLD_PCT = 52.0`).
"""
import math
from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / 'Aplicacion'
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from ocupacion_paulo import Analyzer  # noqa: E402

METHOD_LINEA_A = 'linea_a_v1_gondola_anchorage'
INTERPRETATION_POLICY = 'body_fill_gap_v1'
CALIBRATED_THRESHOLD_PCT = 52.0

# Pesos de señal por celda: densidad Canny, gradiente Sobel, saturación color, textura local.
FEATURE_WEIGHTS = (0.35, 0.28, 0.17, 0.20)
FEATURE_FLOORS = (0.002, 4.0, 0.01, 2.5)
FEATURE_CEIL_MINS = (0.055, 38.0, 0.35, 18.0)

# Evidencia física mínima e híbrida por celda.
ABS_EDGE_DENSITY = 0.018
ABS_GRADIENT = 20.0
ABS_TEXTURE_STD = 10.5
ABS_COLOR_DENSITY = 0.25
HYBRID_SCORE_MIN = 0.36

# Zonas verticales dentro de la grilla (fracción 0–1 de alto de la máscara).
BODY_Y_RANGE = (0.22, 0.90)
SUPPORT_Y_RANGE = (0.30, 0.94)
SUPPORT_COL_MIN_FRAC = 0.22

# Agregación y cota superior por mayor hueco continuo (`100 - max_gap_pct`).
FILL_SCORE_REF = 0.55
GAP_PENALTY_WEIGHT = 1.0

# Guardas espaciales de abstención (solo cuando pct >= threshold_pct).
UPPER_SHARE_REVIEW = 0.88
CENTER_Y_RANGE = (0.35, 0.70)
CENTER_MIN_FILL = 0.25
HOLLOW_UPPER_Y_RANGE = (0.28, 0.56)
HOLLOW_UPPER_MIN_FILL = 0.72
HOLLOW_LOWER_Y_RANGE = (0.54, 0.80)
HOLLOW_LOWER_ROW_MAX = 0.25
HOLLOW_LOWER_MIN_VAL = 0.20


def longest_empty_run_pct(col_covered: np.ndarray, bridge_single: bool = True) -> float:
    """Mayor tramo horizontal continuo sin cobertura de producto (%)."""
    arr = np.asarray(col_covered, dtype=bool).copy()
    if len(arr) == 0:
        return 100.0
    if bridge_single and len(arr) >= 3:
        # Neutralizar columnas aisladas de ruido entre columnas vacías.
        for idx in range(1, len(arr) - 1):
            if arr[idx] and (not arr[idx - 1]) and (not arr[idx + 1]):
                arr[idx] = False
    best = cur = 0
    for covered in arr:
        if not covered:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return 100.0 * best / len(arr)


def extract_cell_features(analyzer: Analyzer, mask: np.ndarray) -> dict | None:
    """Extraer grillas de señal alineadas para una máscara manteniendo exclusión de rieles."""
    level = analyzer._prepare_level(mask, {'status': 'sin_medicion'})
    if isinstance(level, dict):
        return None
    signals = analyzer._measure_cells(level)
    x, y, w, h = level.bounds
    hsv = analyzer.hsv[y:y + h, x:x + w]
    color = ((hsv[..., 1] > analyzer.p.saturation) & (hsv[..., 2] > analyzer.p.min_color_value)).astype(np.float32)
    denom = np.maximum(signals.observed_coverage, 1e-6)
    color_density = cv2.resize(color * signals.observed, level.grid_size, interpolation=cv2.INTER_AREA) / denom
    return {
        'valid': True,
        'valid_cells': int(level.usable.sum()),
        'bounds': tuple(int(v) for v in level.bounds),
        'img_scaled_shape': tuple(int(v) for v in analyzer.rgb.shape[:2]),
        'usable': level.usable.astype(bool),
        'observed_coverage': signals.observed_coverage.astype(np.float32),
        'density': signals.density.astype(np.float32),
        'gradient': signals.gradient.astype(np.float32),
        'color_density': color_density.astype(np.float32),
        'deviation': signals.deviation.astype(np.float32),
    }


def gondola_feature_bounds(level_features: list[dict]) -> tuple | None:
    """Calcular percentiles 10 y 90 globales sobre todos los niveles válidos de la góndola."""
    ds, gs, cs, ts = [], [], [], []
    for feat in level_features:
        if not feat or not feat.get('valid'):
            continue
        usable = np.asarray(feat['usable'], dtype=bool)
        if not usable.any():
            continue
        ds.append(np.asarray(feat['density'], dtype=np.float32)[usable])
        gs.append(np.asarray(feat['gradient'], dtype=np.float32)[usable])
        cs.append(np.asarray(feat['color_density'], dtype=np.float32)[usable])
        ts.append(np.asarray(feat['deviation'], dtype=np.float32)[usable])
    if not ds:
        return None
    d_all, g_all, c_all, t_all = map(np.concatenate, (ds, gs, cs, ts))
    return (
        np.percentile(d_all, [10, 90]),
        np.percentile(g_all, [10, 90]),
        np.percentile(c_all, [10, 90]),
        np.percentile(t_all, [10, 90]),
    )


def _anchored_norm(values: np.ndarray, p10: float, p90: float, floor: float, ceil_min: float) -> np.ndarray:
    lo = min(float(p10), float(floor))
    hi = max(float(p90), float(ceil_min))
    if hi - lo < 1e-6:
        return np.zeros_like(values, dtype=np.float32)
    return np.clip((values - lo) / (hi - lo), 0.0, 1.0)


def _detect_hollow_banner(hyb_ev: np.ndarray, usable: np.ndarray) -> bool:
    """Detectar franja tipo cartel arriba [0.28..0.56] separada por banda vacía [0.54..0.80]."""
    h = usable.shape[0]
    if h < 6:
        return False
    rows = np.arange(h)[:, None]
    upper_band = usable & (rows >= HOLLOW_UPPER_Y_RANGE[0] * h) & (rows < HOLLOW_UPPER_Y_RANGE[1] * h)
    if not upper_band.any() or float(hyb_ev[upper_band].mean()) < HOLLOW_UPPER_MIN_FILL:
        return False
    low_rows = [
        float(hyb_ev[r][usable[r]].mean())
        for r in range(h)
        if HOLLOW_LOWER_Y_RANGE[0] <= (r + 0.5) / h <= HOLLOW_LOWER_Y_RANGE[1] and int(usable[r].sum()) >= 3
    ]
    if len(low_rows) < 2:
        return False
    return (min(low_rows) <= HOLLOW_LOWER_MIN_VAL and
            sum(val <= HOLLOW_LOWER_ROW_MAX for val in low_rows) >= 2)


def compute_cell_maps(feat: dict, gondola_bounds: tuple | None = None) -> dict:
    """Calcular mapas en grilla de intensidad, evidencia híbrida y cobertura de columnas."""
    usable = np.asarray(feat['usable'], dtype=bool)
    density = np.asarray(feat['density'], dtype=np.float32)
    gradient = np.asarray(feat['gradient'], dtype=np.float32)
    color_density = np.asarray(feat['color_density'], dtype=np.float32)
    deviation = np.asarray(feat['deviation'], dtype=np.float32)

    bounds = gondola_bounds or gondola_feature_bounds([feat])
    (d10, d90), (g10, g90), (c10, c90), (t10, t90) = bounds

    dn = _anchored_norm(density, d10, d90, FEATURE_FLOORS[0], FEATURE_CEIL_MINS[0])
    gn = _anchored_norm(gradient, g10, g90, FEATURE_FLOORS[1], FEATURE_CEIL_MINS[1])
    cn = _anchored_norm(color_density, c10, c90, FEATURE_FLOORS[2], FEATURE_CEIL_MINS[2])
    tn = _anchored_norm(deviation, t10, t90, FEATURE_FLOORS[3], FEATURE_CEIL_MINS[3])

    w_d, w_g, w_c, w_t = FEATURE_WEIGHTS
    cell_score = w_d * dn + w_g * gn + w_c * cn + w_t * tn

    abs_ev = (
        (density > ABS_EDGE_DENSITY) |
        ((gradient > ABS_GRADIENT) & (deviation > ABS_TEXTURE_STD)) |
        (color_density > ABS_COLOR_DENSITY)
    )
    hyb_ev = abs_ev | (cell_score >= HYBRID_SCORE_MIN)

    h = usable.shape[0]
    rows = np.arange(h)[:, None]
    body = usable & (rows >= BODY_Y_RANGE[0] * h) & (rows <= BODY_Y_RANGE[1] * h)
    if int(body.sum()) < 4:
        body = usable
    support = usable & (rows >= SUPPORT_Y_RANGE[0] * h) & (rows <= SUPPORT_Y_RANGE[1] * h)
    if int(support.sum()) < 4:
        support = usable

    row_cnt = support.sum(axis=0)
    valid_cols = row_cnt >= 2
    if not valid_cols.any():
        valid_cols = row_cnt >= 1
    col_covered_full = np.zeros(usable.shape[1], dtype=bool)
    if valid_cols.any():
        col_frac = (hyb_ev & support).sum(axis=0)[valid_cols] / row_cnt[valid_cols]
        col_covered_full[valid_cols] = col_frac >= SUPPORT_COL_MIN_FRAC

    return {
        'cell_score': cell_score,
        'abs_ev': abs_ev,
        'hyb_ev': hyb_ev,
        'body': body,
        'support': support,
        'valid_cols': valid_cols,
        'col_covered_full': col_covered_full,
    }


def score_level_from_features(
    feat: dict | None,
    gondola_bounds: tuple | None,
    threshold_pct: float = CALIBRATED_THRESHOLD_PCT,
    near_frame: bool = False,
    apply_scope_rule: bool = False,
) -> dict:
    """Calcular métrica Línea A y clasificación final para un nivel."""
    if not feat or not feat.get('valid'):
        return {
            'method': METHOD_LINEA_A,
            'interpretation_policy': INTERPRETATION_POLICY,
            'status': 'sin_medicion',
            'pct': None,
            'state': 'sin_medicion',
            'label': 'Sin medición',
            'color': '#64748b',
            'review_required': False,
            'review_reason': None,
            'signal_pattern': None,
        }

    usable = np.asarray(feat['usable'], dtype=bool)
    obs_cov = np.asarray(feat['observed_coverage'], dtype=np.float32)
    h = usable.shape[0]
    rows = np.arange(h)[:, None]

    maps = compute_cell_maps(feat, gondola_bounds)
    cell_score = maps['cell_score']
    abs_ev = maps['abs_ev']
    hyb_ev = maps['hyb_ev']
    body = maps['body']
    valid_cols = maps['valid_cols']
    col_covered_full = maps['col_covered_full']

    hyb_body_pct = 100.0 * float(hyb_ev[body].mean())
    abs_body_pct = 100.0 * float(abs_ev[body].mean())
    score_body_pct = min(100.0, 100.0 * float(cell_score[body].mean()) / FILL_SCORE_REF)
    fill_pct = 0.50 * hyb_body_pct + 0.50 * score_body_pct

    if valid_cols.any():
        col_covered = col_covered_full[valid_cols]
        front_hyb_pct = 100.0 * float(col_covered.mean())
        max_gap_pct = longest_empty_run_pct(col_covered, bridge_single=True)
    else:
        front_hyb_pct = 0.0
        max_gap_pct = 100.0

    pct = float(np.clip(min(fill_pct, 100.0 - GAP_PENALTY_WEIGHT * max_gap_pct), 0.0, 100.0))
    if not math.isfinite(pct):
        pct = 0.0

    # Abstención por señal ambigua únicamente si la lectura superaría el umbral.
    sig_w = hyb_ev.astype(np.float32) * obs_cov * usable
    tot_sig = float(sig_w.sum())
    upper_rows = (np.arange(h) + 0.5) / h <= 0.5
    upper_share = float(sig_w[upper_rows].sum()) / tot_sig if tot_sig > 0 else 0.0
    center_zone = usable & (rows >= CENTER_Y_RANGE[0] * h) & (rows <= CENTER_Y_RANGE[1] * h)
    center_fill = float((hyb_ev & center_zone).sum()) / max(1, int(center_zone.sum()))
    hollow_banner = _detect_hollow_banner(hyb_ev, usable)

    pattern = None
    review_reason = None
    review_required = False
    if pct >= threshold_pct:
        if upper_share >= UPPER_SHARE_REVIEW:
            review_required = True
            pattern = 'upper_band_only'
            review_reason = 'Señal concentrada en la mitad superior sobre umbral.'
        elif hollow_banner:
            review_required = True
            pattern = 'hollow_banner'
            review_reason = 'Señal alta tipo cartel sobre banda inferior-media vacía.'
        elif center_fill < CENTER_MIN_FILL:
            review_required = True
            pattern = 'peripheral_ambiguity'
            review_reason = 'Señal periférica sin respaldo central suficiente.'

    if apply_scope_rule and near_frame:
        state = 'revisar'
        label = 'Revisar · zona visible'
        color = '#a16207'
        review_required = True
        pattern = pattern or 'near_frame'
        review_reason = review_reason or 'Contorno junto al encuadre: revisa lo que queda fuera.'
    elif review_required:
        state = 'revisar'
        label = 'Revisar · señal ambigua'
        color = '#a16207'
    elif pct < threshold_pct:
        state = 'reponer'
        label = 'Reponer'
        color = '#dc2626'
    else:
        state = 'suficiente'
        label = 'Suficiente'
        color = '#16a34a'

    return {
        'method': METHOD_LINEA_A,
        'interpretation_policy': INTERPRETATION_POLICY,
        'status': 'medido',
        'pct': round(pct, 2),
        'state': state,
        'label': label,
        'color': color,
        'calibrated_threshold_pct': threshold_pct,
        'fill_pct': round(fill_pct, 2),
        'hyb_body_pct': round(hyb_body_pct, 2),
        'abs_body_pct': round(abs_body_pct, 2),
        'score_body_pct': round(score_body_pct, 2),
        'front_hyb_pct': round(front_hyb_pct, 2),
        'max_gap_pct': round(max_gap_pct, 2),
        'upper_share': round(upper_share, 4),
        'center_fill': round(center_fill, 4),
        'hollow_banner': hollow_banner,
        'review_required': review_required,
        'signal_pattern': pattern,
        'review_reason': review_reason,
        'valid_cells': int(feat.get('valid_cells', usable.sum())),
    }


def analyze_gondola_rgb(
    rgb: np.ndarray,
    masks: list[np.ndarray],
    threshold_pct: float = CALIBRATED_THRESHOLD_PCT,
    near_frames: list[bool] | None = None,
    apply_scope_rule: bool = False,
) -> list[dict]:
    """Ejecutar extracción + normalización anclada de góndola + decisión Línea A desde imagen RGB."""
    analyzer = Analyzer(rgb, version='v2', front_mode=True)
    extracted = [extract_cell_features(analyzer, mask) for mask in masks]
    bounds = gondola_feature_bounds([item for item in extracted if item is not None])
    flags = near_frames if near_frames is not None else [False] * len(masks)
    return [
        score_level_from_features(
            feat,
            bounds,
            threshold_pct=threshold_pct,
            near_frame=bool(nf),
            apply_scope_rule=apply_scope_rule,
        )
        for feat, nf in zip(extracted, flags)
    ]
