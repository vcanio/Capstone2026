"""Línea A: índice experimental de disponibilidad visual por nivel.

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
import hashlib

import cv2
import numpy as np

from ocupacion_paulo import Analyzer
from oclusiones import detect_intrusions_from_rgb, evaluate_level_occlusion

METHOD_LINEA_A = 'linea_a_v1_gondola_anchorage'
REVISION_LINEA_A = 'linea_a_20261116_v2_2_cajas_sacos_picada'
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
# Color saturado requiere respaldo mínimo de borde/textura para no contar tableros lisos vacíos.
ABS_COLOR_MIN_EDGE = 0.012
ABS_COLOR_MIN_GRAD = 16.0
ABS_COLOR_MIN_STD = 7.5
HYBRID_SCORE_MIN = 0.36

# Descarte de cielo abierto en estantes superiores sin producto (solo cuando hay mapas direccionales).
VERT_EDGE_MIN = 22.0
BRIGHT_CEILING_MIN_V = 145
BRIGHT_CEILING_MAX_S = 45
CEILING_LEVEL_MIN_BRIGHT = 0.35
CEILING_LEVEL_MAX_GX = 22.0
CEILING_LEVEL_MAX_GX_GY_RATIO = 0.72
CEILING_LEVEL_MAX_COLOR = 0.18
CEILING_LEVEL_MAX_LOW_VX = 0.25
CEILING_LOW_Y_RANGE = (0.50, 0.92)
CEILING_CELL_MAX_COLOR = 0.20
CEILING_CELL_MAX_GX = 24.0
CEILING_CELL_MIN_BRIGHT = 0.25
CEILING_CELL_MAX_GX_GY_RATIO = 0.85
CEILING_SCORE_FACTOR = 0.25

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

# Descarte de piso/bandeja expuesta en vista picada.
FLOOR_LEVEL_MAX_GX_GY_RATIO = 0.68
FLOOR_LEVEL_MAX_VX = 0.18
FLOOR_LEVEL_MAX_COLOR = 0.18
FLOOR_TOP_MAX_DENSITY = 0.026
FLOOR_TOP_MAX_VX = 0.10
FLOOR_CELL_MAX_VX = 0.15
FLOOR_CELL_MAX_GX_GY_RATIO = 0.78
FLOOR_CELL_MAX_COLOR = 0.20

# Puenteo de islas débiles y huecos acumulados.
WEAK_ISLAND_MAX_WIDTH = 2
WEAK_ISLAND_MIN_FRAC = 0.35
SIGNIFICANT_GAP_MIN_PCT = 15.0
ACCUMULATED_GAP_WEIGHT = 0.85

# Reglas combinadas de alerta e incertidumbre por bajo contraste.
FACING_GAP_ALERT_PCT = 35.0
FACING_FRONT_MAX_PCT = 68.0
ACCUMULATED_GAP_ALERT_PCT = 45.0
LOW_CONTRAST_MIN_PCT = 36.0
LOW_CONTRAST_MAX_GAP_PCT = 33.0
LOW_CONTRAST_MIN_FRONT_PCT = 65.0
LOW_CONTRAST_MAX_BRIGHT_FRAC = 0.15


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


def extract_cell_features(
    analyzer: Analyzer,
    mask: np.ndarray,
    occlusion_mask: np.ndarray | None = None,
) -> dict | None:
    """Extraer grillas de señal alineadas para una máscara manteniendo exclusión de rieles."""
    level = analyzer._prepare_level(mask, {'status': 'sin_medicion'})
    if isinstance(level, dict):
        return None
    occ_info = evaluate_level_occlusion(mask, occlusion_mask) if occlusion_mask is not None else None
    usable = level.usable.astype(bool)
    if occ_info and occ_info['should_mask_columns'] and occlusion_mask is not None:
        occ_scaled = cv2.resize(
            (np.asarray(occlusion_mask) > 0).astype(np.uint8),
            (analyzer.rgb.shape[1], analyzer.rgb.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )
        x0, y0, w0, h0 = level.bounds
        occ_grid = cv2.resize(
            occ_scaled[y0:y0 + h0, x0:x0 + w0].astype(np.float32),
            level.grid_size,
            interpolation=cv2.INTER_AREA,
        )
        masked_usable = usable & (occ_grid < 0.5)
        if masked_usable.any():
            usable = masked_usable
        else:
            occ_info = {**occ_info, 'requires_review': True, 'should_mask_columns': False}
    signals = analyzer._measure_cells(level)
    x, y, w, h = level.bounds
    hsv = analyzer.hsv[y:y + h, x:x + w]
    gray = analyzer.gray_texture[y:y + h, x:x + w]
    gx = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
    gy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
    denom = np.maximum(signals.observed_coverage, 1e-6)
    raw_signals = {
        'color_density': ((hsv[..., 1] > analyzer.p.saturation) & (hsv[..., 2] > analyzer.p.min_color_value)).astype(np.float32),
        'gx': gx,
        'gy': gy,
        'vx': (gx > VERT_EDGE_MIN).astype(np.float32),
        'bu': ((hsv[..., 2] > BRIGHT_CEILING_MIN_V) & (hsv[..., 1] < BRIGHT_CEILING_MAX_S)).astype(np.float32),
    }
    cell_maps = {
        name: (cv2.resize(arr * signals.observed, level.grid_size, interpolation=cv2.INTER_AREA) / denom).astype(np.float32)
        for name, arr in raw_signals.items()
    }
    features = {
        'valid': True,
        'valid_cells': int(usable.sum()),
        'bounds': tuple(int(v) for v in level.bounds),
        'img_scaled_shape': tuple(int(v) for v in analyzer.rgb.shape[:2]),
        'usable': usable,
        'observed_coverage': signals.observed_coverage.astype(np.float32),
        'observed': signals.observed,
        'density': signals.density.astype(np.float32),
        'gradient': signals.gradient.astype(np.float32),
        'deviation': signals.deviation.astype(np.float32),
        **cell_maps,
    }
    if occ_info and (occ_info['requires_review'] or occ_info['should_mask_columns']):
        features['occlusion_info'] = occ_info
    return features


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


def _open_ceiling_mask(feat: dict, body: np.ndarray, usable: np.ndarray, color_density: np.ndarray) -> np.ndarray | None:
    """Identificar celdas de techo abierto cuando el nivel completo muestra estructura de techo sin producto."""
    if any(feat.get(k) is None for k in ('gx', 'gy', 'vx', 'bu')):
        return None
    gx = np.asarray(feat['gx'], dtype=np.float32)
    gy = np.asarray(feat['gy'], dtype=np.float32)
    vx = np.asarray(feat['vx'], dtype=np.float32)
    bu = np.asarray(feat['bu'], dtype=np.float32)
    h = usable.shape[0]
    rows = np.arange(h)[:, None]
    low = usable & (rows >= CEILING_LOW_Y_RANGE[0] * h) & (rows <= CEILING_LOW_Y_RANGE[1] * h)
    if int(low.sum()) < 2:
        low = body

    gx_mean = float(gx[body].mean())
    gy_mean = float(gy[body].mean())
    is_open_ceiling = (
        float(bu[body].mean()) >= CEILING_LEVEL_MIN_BRIGHT
        and gx_mean < CEILING_LEVEL_MAX_GX
        and gx_mean < CEILING_LEVEL_MAX_GX_GY_RATIO * max(gy_mean, 1e-3)
        and float(color_density[body].mean()) < CEILING_LEVEL_MAX_COLOR
        and float(vx[low].mean()) <= CEILING_LEVEL_MAX_LOW_VX
    )
    if not is_open_ceiling:
        return None
    return (
        (color_density < CEILING_CELL_MAX_COLOR)
        & (gx < CEILING_CELL_MAX_GX)
        & ((bu > CEILING_CELL_MIN_BRIGHT) | (gx < CEILING_CELL_MAX_GX_GY_RATIO * gy))
    )


def _relative_vertical_bands(
    usable: np.ndarray,
    y_range: tuple[float, float],
    fallback_full: bool = True,
) -> np.ndarray:
    """Calcular banda vertical relativa por columna cuando hay inclinación significativa."""
    h = usable.shape[0]
    lo, hi = y_range
    col_heights = []
    for col in range(usable.shape[1]):
        rows = np.flatnonzero(usable[:, col])
        if rows.size:
            col_heights.append(int(rows[-1] - rows[0] + 1))

    if not col_heights:
        return usable.copy() if fallback_full else np.zeros_like(usable, dtype=bool)

    if float(np.median(col_heights)) >= 0.85 * h:
        rows = np.arange(h)[:, None]
        band = usable & (rows >= lo * h) & (rows <= hi * h)
        if fallback_full and int(band.sum()) < 4:
            return usable.copy()
        return band

    band = np.zeros_like(usable, dtype=bool)
    mid = 0.5 * (lo + hi)
    for col in range(usable.shape[1]):
        rows = np.flatnonzero(usable[:, col])
        if rows.size == 0:
            continue
        col_h = rows[-1] - rows[0] + 1
        rel_idx = rows - rows[0]
        selected = rows[(rel_idx >= lo * col_h) & (rel_idx <= hi * col_h)]
        if selected.size == 0 and fallback_full:
            rel_center = (rel_idx + 0.5) / col_h
            best_idx = int(np.argmin(np.abs(rel_center - mid)))
            selected = rows[best_idx:best_idx + 1]
        band[selected, col] = True
    if fallback_full and int(band.sum()) < 4:
        return usable.copy()
    return band


def _upper_lower_zones(usable: np.ndarray, body: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Dividir la máscara usable en zona superior (< 0.50 h) e inferior [0.55..0.90 h]."""
    h = usable.shape[0]
    rows = np.arange(h)[:, None]
    top_u = usable & (rows < 0.50 * h)
    bot_u = usable & (rows >= 0.55 * h) & (rows <= 0.90 * h)
    if not top_u.any():
        top_u = body
    if not bot_u.any():
        bot_u = body
    return top_u, bot_u


def _is_white_stocked_packages(
    feat: dict,
    top_u: np.ndarray,
    bot_u: np.ndarray,
    color_density: np.ndarray,
    is_top_level: bool = False,
) -> bool:
    """Reconocer paquetes/sacos blancos abastecidos en la base sin confundirlos con techo."""
    if any(feat.get(k) is None for k in ('bu', 'vx')):
        return False
    bu = np.asarray(feat['bu'], dtype=np.float32)
    vx = np.asarray(feat['vx'], dtype=np.float32)
    top_bu = float(bu[top_u].mean())
    bot_bu = float(bu[bot_u].mean())
    bot_vx = float(vx[bot_u].mean())
    if float(color_density[top_u].mean()) >= 0.22 and bot_vx >= 0.18 and bot_bu > top_bu + 0.25:
        return True
    # Sacos o cajas blancas apiladas en niveles no superiores bajo sombra del estante de arriba.
    return (
        not is_top_level
        and top_bu < 0.28
        and bot_bu >= 0.55
        and bot_bu > top_bu + 0.22
        and bot_vx >= 0.14
    )


def _open_ceiling_mask_v2(
    feat: dict,
    body: np.ndarray,
    top_u: np.ndarray,
    bot_u: np.ndarray,
    usable: np.ndarray,
    color_density: np.ndarray,
    is_top_level: bool = False,
) -> np.ndarray | None:
    """Detectar cielo abierto en niveles superiores incluyendo cerchas y luminarias de techo."""
    if any(feat.get(k) is None for k in ('gx', 'gy', 'vx', 'bu')):
        return None
    if _is_white_stocked_packages(feat, top_u, bot_u, color_density, is_top_level=is_top_level):
        return None

    base_ceil = _open_ceiling_mask(feat, body, usable, color_density)
    if base_ceil is not None:
        return base_ceil
    if not is_top_level:
        return None

    gx = np.asarray(feat['gx'], dtype=np.float32)
    gy = np.asarray(feat['gy'], dtype=np.float32)
    vx = np.asarray(feat['vx'], dtype=np.float32)
    bu = np.asarray(feat['bu'], dtype=np.float32)

    bu_body = float(bu[body].mean())
    gx_mean = float(gx[body].mean())
    gy_mean = float(gy[body].mean())
    col_body = float(color_density[body].mean())

    bu_topu = float(bu[top_u].mean())
    bu_botu = float(bu[bot_u].mean())
    col_topu = float(color_density[top_u].mean())
    col_botu = float(color_density[bot_u].mean())
    vx_botu = float(vx[bot_u].mean())
    gx_botu = float(gx[bot_u].mean())
    gy_botu = float(gy[bot_u].mean())

    pattern_a = (
        bu_body >= 0.45
        and gx_mean < 24.5
        and gx_mean < 0.55 * max(gy_mean, 1e-3)
        and col_body < 0.14
        and col_botu < 0.08
    )
    pattern_b = (
        bu_topu >= 0.58
        and bu_botu >= 0.48
        and col_topu < 0.10
        and col_body < 0.18
        and gx_mean < 26.0
        and gx_mean < 0.82 * max(gy_mean, 1e-3)
    )
    pattern_c = (
        bu_botu >= 0.55
        and col_botu < 0.18
        and vx_botu <= 0.12
        and gx_botu < 0.72 * max(gy_botu, 1e-3)
    )
    if pattern_c:
        return (vx < 0.20) | (color_density < 0.30)
    if pattern_a or pattern_b:
        return (color_density < 0.30) & ((bu > 0.20) | (gx < 0.90 * gy) | (vx < 0.20))
    return None


def _exposed_floor_mask(
    feat: dict,
    body: np.ndarray,
    top_u: np.ndarray,
    bot_u: np.ndarray,
    color_density: np.ndarray,
) -> np.ndarray | None:
    """Identificar celdas de bandeja/piso expuesto sin bordes verticales de envases."""
    if any(feat.get(k) is None for k in ('gx', 'gy', 'vx')):
        return None
    if _is_white_stocked_packages(feat, top_u, bot_u, color_density):
        return None
    gx = np.asarray(feat['gx'], dtype=np.float32)
    gy = np.asarray(feat['gy'], dtype=np.float32)
    vx = np.asarray(feat['vx'], dtype=np.float32)
    density = np.asarray(feat['density'], dtype=np.float32)
    gx_mean = float(gx[body].mean())
    gy_mean = float(gy[body].mean())
    top_low_detail = (
        float(density[top_u].mean()) < FLOOR_TOP_MAX_DENSITY
        or float(vx[top_u].mean()) < FLOOR_TOP_MAX_VX
    )
    is_exposed_floor = (
        gx_mean < FLOOR_LEVEL_MAX_GX_GY_RATIO * max(gy_mean, 1e-3)
        and float(vx[body].mean()) <= FLOOR_LEVEL_MAX_VX
        and float(color_density[body].mean()) < FLOOR_LEVEL_MAX_COLOR
        and top_low_detail
    )
    if not is_exposed_floor:
        return None
    return (
        (vx < FLOOR_CELL_MAX_VX)
        & (gx < FLOOR_CELL_MAX_GX_GY_RATIO * gy)
        & (color_density < FLOOR_CELL_MAX_COLOR)
    )


def _is_bicolor_printed_box(
    feat: dict,
    top_u: np.ndarray,
    bot_u: np.ndarray,
    usable: np.ndarray,
    color_density: np.ndarray,
) -> bool:
    """Detectar cajas máster grandes con franja superior clara/impresa y banda inferior de color sólido."""
    if any(feat.get(k) is None for k in ('bu', 'vx')):
        return False
    bu = np.asarray(feat['bu'], dtype=np.float32)
    vx = np.asarray(feat['vx'], dtype=np.float32)
    top_bu = float(bu[top_u].mean())
    top_col = float(color_density[top_u].mean())
    bot_col = float(color_density[bot_u].mean())
    h = usable.shape[0]
    row_vx = [float(vx[r, usable[r]].mean()) for r in range(h) if usable[r].any()]
    max_row_vx = max(row_vx, default=0.0)
    return top_bu >= 0.14 and bot_col >= 0.60 and (bot_col - top_col) >= 0.35 and max_row_vx >= 0.25


def _has_recessed_upper_product(
    feat: dict,
    top_u: np.ndarray,
    bot_u: np.ndarray,
    usable: np.ndarray,
) -> bool:
    """Detectar producto apoyado al fondo (mitad superior) sobre bandeja oscura en vista picada."""
    if any(feat.get(k) is None for k in ('bu', 'vx', 'gx', 'gy')):
        return False
    bu = np.asarray(feat['bu'], dtype=np.float32)
    vx = np.asarray(feat['vx'], dtype=np.float32)
    gx = np.asarray(feat['gx'], dtype=np.float32)
    gy = np.asarray(feat['gy'], dtype=np.float32)
    top_vx = float(vx[top_u].mean())
    bot_vx = float(vx[bot_u].mean())
    bot_bu = float(bu[bot_u].mean())
    gx_m = float(gx[usable].mean())
    gy_m = float(gy[usable].mean())
    return (
        top_vx >= 0.19
        and top_vx >= 1.45 * max(bot_vx, 1e-3)
        and bot_bu < 0.10
        and gx_m >= 0.85 * max(gy_m, 1e-3)
    )


def analyze_column_gaps(
    col_covered: np.ndarray,
    col_frac: np.ndarray | None = None,
    bridge_single: bool = True,
) -> dict:
    """Filtrar islas débiles entre tramos vacíos y medir hueco máximo y acumulado."""
    arr = np.asarray(col_covered, dtype=bool).copy()
    n = len(arr)
    if n == 0:
        return {
            'filtered_covered': arr,
            'max_gap_pct': 100.0,
            'significant_gaps_pct': 100.0,
            'effective_gap_pct': 100.0,
        }

    # Identificar corridas continuas de columnas cubiertas antes de filtrar islas.
    covered_runs: list[tuple[int, int]] = []
    idx = 0
    while idx < n:
        if arr[idx]:
            end = idx + 1
            while end < n and arr[end]:
                end += 1
            covered_runs.append((idx, end))
            idx = end
        else:
            idx += 1

    fracs = np.asarray(col_frac, dtype=np.float32) if col_frac is not None else None
    for start, end in covered_runs:
        if start == 0 or end == n:
            continue  # Solo se neutralizan islas entre tramos vacíos.
        width = end - start
        if width == 1 and bridge_single:
            arr[start:end] = False
        elif width <= WEAK_ISLAND_MAX_WIDTH and fracs is not None:
            if float(np.max(fracs[start:end])) < WEAK_ISLAND_MIN_FRAC:
                arr[start:end] = False

    empty_gaps_pct: list[float] = []
    idx = 0
    while idx < n:
        if not arr[idx]:
            end = idx + 1
            while end < n and not arr[end]:
                end += 1
            empty_gaps_pct.append(100.0 * (end - idx) / n)
            idx = end
        else:
            idx += 1

    max_gap_pct = max(empty_gaps_pct, default=0.0)
    significant_gaps_pct = min(
        100.0,
        sum(gap for gap in empty_gaps_pct if gap >= SIGNIFICANT_GAP_MIN_PCT),
    )
    effective_gap_pct = max(max_gap_pct, ACCUMULATED_GAP_WEIGHT * significant_gaps_pct)
    return {
        'filtered_covered': arr,
        'max_gap_pct': max_gap_pct,
        'significant_gaps_pct': significant_gaps_pct,
        'effective_gap_pct': effective_gap_pct,
    }


def _top_level_flags(extracted: list[dict | None]) -> list[bool]:
    """Identificar cuál de los niveles extraídos ocupa la posición más alta en la imagen."""
    centers = [
        (idx, feat['bounds'][1] + 0.5 * feat['bounds'][3])
        for idx, feat in enumerate(extracted)
        if feat is not None and feat.get('bounds') is not None
    ]
    flags = [False] * len(extracted)
    if len(centers) >= 2:
        top_idx = min(centers, key=lambda item: item[1])[0]
        flags[top_idx] = True
    return flags


def compute_cell_maps(
    feat: dict,
    gondola_bounds: tuple | None = None,
    is_top_level: bool = False,
) -> dict:
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

    color_ev = (color_density > ABS_COLOR_DENSITY) & (
        (density > ABS_COLOR_MIN_EDGE) | ((gradient > ABS_COLOR_MIN_GRAD) & (deviation > ABS_COLOR_MIN_STD))
    )
    abs_ev = (
        (density > ABS_EDGE_DENSITY)
        | ((gradient > ABS_GRADIENT) & (deviation > ABS_TEXTURE_STD))
        | color_ev
    )

    body = _relative_vertical_bands(usable, BODY_Y_RANGE)
    support = _relative_vertical_bands(usable, SUPPORT_Y_RANGE)
    top_u, bot_u = _upper_lower_zones(usable, body)

    ceil_mask = _open_ceiling_mask_v2(
        feat, body, top_u, bot_u, usable, color_density, is_top_level=is_top_level
    )
    floor_mask = _exposed_floor_mask(feat, body, top_u, bot_u, color_density)

    suppression = np.zeros_like(usable, dtype=bool)
    if ceil_mask is not None:
        suppression |= ceil_mask
    if floor_mask is not None:
        suppression |= floor_mask

    if suppression.any():
        abs_ev = abs_ev & (~suppression)
        cell_score = np.where(suppression, cell_score * CEILING_SCORE_FACTOR, cell_score)
        hyb_ev = abs_ev | ((cell_score >= HYBRID_SCORE_MIN) & (~suppression))
    else:
        hyb_ev = abs_ev | (cell_score >= HYBRID_SCORE_MIN)

    if (
        ceil_mask is None
        and floor_mask is None
        and _is_bicolor_printed_box(feat, top_u, bot_u, usable, color_density)
    ):
        box_color = usable & (color_density > ABS_COLOR_DENSITY)
        abs_ev = abs_ev | box_color
        hyb_ev = hyb_ev | box_color
        cell_score = np.where(box_color, np.maximum(cell_score, 0.55), cell_score)

    recessed_upper = False
    if (
        ceil_mask is None
        and floor_mask is None
        and _has_recessed_upper_product(feat, top_u, bot_u, usable)
    ):
        rec_body = _relative_vertical_bands(usable, (0.04, 0.62))
        rec_supp = _relative_vertical_bands(usable, (0.06, 0.65))
        if float(hyb_ev[rec_body].mean()) > float(hyb_ev[body].mean()) + 0.10:
            body = rec_body
            support = rec_supp
            recessed_upper = True

    row_cnt = support.sum(axis=0)
    valid_cols = usable.any(axis=0) & (row_cnt >= 1)
    col_frac_full = np.zeros(usable.shape[1], dtype=np.float32)
    col_covered_full = np.zeros(usable.shape[1], dtype=bool)
    if valid_cols.any():
        col_frac = (hyb_ev & support).sum(axis=0)[valid_cols] / np.maximum(row_cnt[valid_cols], 1)
        col_frac_full[valid_cols] = col_frac
        col_covered_full[valid_cols] = col_frac >= SUPPORT_COL_MIN_FRAC

    return {
        'cell_score': cell_score,
        'abs_ev': abs_ev,
        'hyb_ev': hyb_ev,
        'body': body,
        'support': support,
        'valid_cols': valid_cols,
        'col_frac_full': col_frac_full,
        'col_covered_full': col_covered_full,
        'floor_mask_active': floor_mask is not None,
        'ceil_mask_active': ceil_mask is not None,
        'recessed_upper_product': recessed_upper,
    }


def score_level_from_features(
    feat: dict | None,
    gondola_bounds: tuple | None,
    threshold_pct: float = CALIBRATED_THRESHOLD_PCT,
    near_frame: bool = False,
    apply_scope_rule: bool = False,
    is_top_level: bool = False,
) -> dict:
    """Calcular métrica Línea A y clasificación final para un nivel."""
    if not feat or not feat.get('valid'):
        return {
            'method': METHOD_LINEA_A,
            'interpretation_policy': INTERPRETATION_POLICY,
            'status': 'sin_medicion',
            'pct': None,
            'raw_pct': None,
            'state': 'sin_medicion',
            'label': 'Sin medición',
            'color': '#64748b',
            'operational_severity': 'sin_medicion',
            'review_required': False,
            'review_reason': None,
            'signal_pattern': None,
        }

    usable = np.asarray(feat['usable'], dtype=bool)
    obs_cov = np.asarray(feat['observed_coverage'], dtype=np.float32)
    h = usable.shape[0]
    rows = np.arange(h)[:, None]

    maps = compute_cell_maps(feat, gondola_bounds, is_top_level=is_top_level)
    cell_score = maps['cell_score']
    abs_ev = maps['abs_ev']
    hyb_ev = maps['hyb_ev']
    body = maps['body']
    valid_cols = maps['valid_cols']
    col_frac_full = maps['col_frac_full']
    col_covered_full = maps['col_covered_full']

    hyb_body_pct = 100.0 * float(hyb_ev[body].mean())
    abs_body_pct = 100.0 * float(abs_ev[body].mean())
    score_body_pct = min(100.0, 100.0 * float(cell_score[body].mean()) / FILL_SCORE_REF)
    fill_pct = 0.50 * hyb_body_pct + 0.50 * score_body_pct

    if valid_cols.any():
        col_covered = col_covered_full[valid_cols]
        col_frac = col_frac_full[valid_cols]
        gap_info = analyze_column_gaps(col_covered, col_frac=col_frac, bridge_single=True)
        front_hyb_pct = 100.0 * float(gap_info['filtered_covered'].mean())
        max_gap_pct = gap_info['max_gap_pct']
        significant_gaps_pct = gap_info['significant_gaps_pct']
        effective_gap_pct = gap_info['effective_gap_pct']
    else:
        front_hyb_pct = 0.0
        max_gap_pct = 100.0
        significant_gaps_pct = 100.0
        effective_gap_pct = 100.0

    pct = float(np.clip(min(fill_pct, 100.0 - effective_gap_pct), 0.0, 100.0))
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
        if upper_share >= UPPER_SHARE_REVIEW and not maps.get('recessed_upper_product'):
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

    bu_arr = feat.get('bu')
    is_dark_level = (
        bu_arr is not None
        and float(np.asarray(bu_arr, dtype=np.float32)[body].mean()) < LOW_CONTRAST_MAX_BRIGHT_FRAC
    )
    low_contrast_front = (
        is_dark_level
        and (LOW_CONTRAST_MIN_PCT <= pct < threshold_pct)
        and (max_gap_pct < LOW_CONTRAST_MAX_GAP_PCT)
        and (front_hyb_pct >= LOW_CONTRAST_MIN_FRONT_PCT)
    )
    facing_gap_alert = (
        (max_gap_pct >= FACING_GAP_ALERT_PCT and front_hyb_pct < FACING_FRONT_MAX_PCT)
        or (significant_gaps_pct >= ACCUMULATED_GAP_ALERT_PCT)
    )

    occ_info = feat.get('occlusion_info')
    occ_review = bool(occ_info and occ_info.get('requires_review'))

    if apply_scope_rule and near_frame:
        state = 'revisar'
        label = 'Revisar · zona visible'
        color = '#a16207'
        review_required = True
        pattern = pattern or 'near_frame'
        review_reason = review_reason or 'Contorno junto al encuadre: revisa lo que queda fuera.'
    elif occ_review:
        state = 'revisar'
        label = 'Revisar · zona obstruida'
        color = '#a16207'
        review_required = True
        pattern = 'foreground_occlusion'
        review_reason = 'Zona obstruida por persona u objeto externo frente al estante.'
    elif review_required:
        state = 'revisar'
        label = 'Revisar · señal ambigua'
        color = '#a16207'
    elif low_contrast_front:
        state = 'revisar'
        label = 'Revisar · baja iluminación / contraste'
        color = '#a16207'
        review_required = True
        pattern = 'low_contrast_continuous_front'
        review_reason = 'Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.'
    elif pct < threshold_pct or facing_gap_alert:
        state = 'reponer'
        label = 'Reponer'
        color = '#dc2626'
    else:
        state = 'suficiente'
        label = 'Suficiente'
        color = '#16a34a'

    if state == 'reponer':
        severity = 'critica' if (pct <= 15.0 or max_gap_pct >= 60.0) else 'alta'
    elif state == 'revisar':
        severity = 'verificar'
    else:
        severity = 'normal'

    raw_pct = round(pct, 2)
    result = {
        'method': METHOD_LINEA_A,
        'interpretation_policy': INTERPRETATION_POLICY,
        'status': 'medido',
        'pct': raw_pct,
        'raw_pct': raw_pct,
        'state': state,
        'label': label,
        'color': color,
        'operational_severity': severity,
        'calibrated_threshold_pct': threshold_pct,
        'fill_pct': round(fill_pct, 2),
        'hyb_body_pct': round(hyb_body_pct, 2),
        'abs_body_pct': round(abs_body_pct, 2),
        'score_body_pct': round(score_body_pct, 2),
        'front_hyb_pct': round(front_hyb_pct, 2),
        'max_gap_pct': round(max_gap_pct, 2),
        'significant_gaps_pct': round(significant_gaps_pct, 2),
        'effective_gap_pct': round(effective_gap_pct, 2),
        'upper_share': round(upper_share, 4),
        'center_fill': round(center_fill, 4),
        'hollow_banner': hollow_banner,
        'review_required': review_required,
        'signal_pattern': pattern,
        'review_reason': review_reason,
        'floor_mask_active': maps['floor_mask_active'],
        'ceil_mask_active': maps['ceil_mask_active'],
        'valid_cells': int(feat.get('valid_cells', usable.sum())),
    }
    if occ_info and (occ_info.get('requires_review') or occ_info.get('should_mask_columns')):
        result['occlusion_pct'] = round(100.0 * float(occ_info['occluded_area_frac']), 2)
        result['occlusion_masked'] = bool(occ_info.get('should_mask_columns'))
    return result


def analyze_gondola_rgb(
    rgb: np.ndarray,
    masks: list[np.ndarray],
    threshold_pct: float = CALIBRATED_THRESHOLD_PCT,
    near_frames: list[bool] | None = None,
    apply_scope_rule: bool = False,
    is_top_levels: list[bool] | None = None,
    occlusion_masks: list[np.ndarray | None] | None = None,
) -> list[dict]:
    """Ejecutar extracción + normalización anclada de góndola + decisión Línea A desde imagen RGB."""
    analyzer = Analyzer(rgb, version='v2', front_mode=True)
    occ_masks = occlusion_masks if occlusion_masks is not None else detect_intrusions_from_rgb(rgb, masks)
    extracted = [
        extract_cell_features(
            analyzer,
            mask,
            occlusion_mask=occ_masks[idx] if idx < len(occ_masks) else None,
        )
        for idx, mask in enumerate(masks)
    ]
    bounds = gondola_feature_bounds([item for item in extracted if item is not None])
    flags = near_frames if near_frames is not None else [False] * len(masks)
    top_flags = is_top_levels if is_top_levels is not None else _top_level_flags(extracted)
    return [
        score_level_from_features(
            feat,
            bounds,
            threshold_pct=threshold_pct,
            near_frame=bool(nf),
            apply_scope_rule=apply_scope_rule,
            is_top_level=bool(tl),
        )
        for feat, nf, tl in zip(extracted, flags, top_flags)
    ]


def provenance():
    """Identificar el algoritmo portable y su umbral de ajuste preliminar."""
    return {
        'method': METHOD_LINEA_A,
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'revision': REVISION_LINEA_A,
        'interpretation_policy': {'name': INTERPRETATION_POLICY,
                                  'threshold_pct': CALIBRATED_THRESHOLD_PCT},
        'meaning': 'Índice de disponibilidad visual de 0 a 100; no es porcentaje físico de stock.',
        'calibrated': False,
        'threshold_calibration': 'preliminary_development_human_labels',
        'changes_yolo_state': False,
    }
