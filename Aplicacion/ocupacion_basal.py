"""Cobertura basal experimental para comparar con Línea A, sin modificarla.

Mide señal horizontal visible, no stock ni volumen. Parámetros de ingeniería
pendientes de calibración humana. Conserva Canny y la exclusión de rieles.
"""
import hashlib
from pathlib import Path
from dataclasses import replace

import cv2
import numpy as np

from ocupacion_linea_a import (compute_cell_maps as base_maps,
                              gondola_feature_bounds, longest_empty_run_pct)

METHOD = 'basal_v1_observable_columns'
REVISION = 'basal_20261112_experimental_v2'
POLICY = 'basal_visible_width_v1'
# Criterio de ensayo independiente del índice 52 de Línea A; no calibrado.
THRESHOLD = 30.0
BAND = (0.65, 0.95)
MIN_OBSERVED_CELL = 0.50
MIN_OBSERVED_BAND = 0.60
MIN_OBSERVED_WIDTH = 0.75
MIN_SIGNAL_FRACTION = 0.35
VERTICAL_CELL_PX = 8


def extract_cell_features(analyzer, mask):
    level = analyzer._prepare_level(mask, {'status': 'sin_medicion'})
    if isinstance(level, dict):
        return None
    # Refinar solo el muestreo vertical. Los parámetros y píxeles del detector
    # de rieles son los mismos de Línea A; no alterar sus máscaras ni filtros.
    grid = (level.grid_size[0], max(level.grid_size[1], round(level.height / VERTICAL_CELL_PX)))
    coverage = cv2.resize(level.region.astype(np.float32), grid, interpolation=cv2.INTER_AREA)
    level = replace(level, grid_size=grid, coverage=coverage, usable=coverage >= analyzer.p.cell_coverage)
    signals = analyzer._measure_cells(level)
    x, y, w, h = level.bounds
    hsv = analyzer.hsv[y:y+h, x:x+w]
    color = ((hsv[..., 1] > analyzer.p.saturation) & (hsv[..., 2] > analyzer.p.min_color_value)).astype(np.float32)
    color_density = cv2.resize(color * signals.observed, grid, interpolation=cv2.INTER_AREA) / np.maximum(signals.observed_coverage, 1e-6)
    return {'valid': True, 'valid_cells': int(level.usable.sum()), 'bounds': level.bounds,
            'usable': level.usable, 'mask_coverage': coverage,
            'observed_coverage': signals.observed_coverage, 'observed': signals.observed,
            'density': signals.density, 'gradient': signals.gradient,
            'color_density': color_density, 'deviation': signals.deviation}


def observable_features(feat):
    if feat is None:
        return None
    geometry = np.asarray(feat['usable'], bool)
    coverage = np.asarray(feat.get('mask_coverage', np.ones(geometry.shape)), float)
    ratio = np.asarray(feat['observed_coverage'], float) / np.maximum(coverage, 1e-6)
    return {**feat, 'usable': geometry & (ratio >= MIN_OBSERVED_CELL)}


def feature_bounds(features):
    return gondola_feature_bounds([observable_features(f) for f in features])


def compute_cell_maps(feat, bounds=None):
    geometry = np.asarray(feat['usable'], bool)
    observable = observable_features(feat)
    observed = observable['usable']
    band = np.zeros_like(geometry)
    # Altura relativa por columna: sigue la máscara en la resolución de grilla.
    for col in range(geometry.shape[1]):
        rows = np.flatnonzero(geometry[:, col])
        if rows.size:
            relative = (rows - rows[0] + 0.5) / (rows[-1] - rows[0] + 1)
            band[rows[(relative >= BAND[0]) & (relative <= BAND[1])], col] = True
    n_band = band.sum(axis=0)
    sampled = band & observed
    n_observed = sampled.sum(axis=0)
    domain = geometry.any(axis=0)
    known = domain & (n_band >= 2) & (n_observed >= 2) & (n_observed >= MIN_OBSERVED_BAND * n_band)
    if observed.any():
        maps = base_maps(observable, bounds)
        evidence = maps['hyb_ev'] & sampled
    else:
        evidence = np.zeros_like(geometry)
    signal = evidence.sum(axis=0)
    # Dos filas respaldan también productos estrechos; no borrar una columna
    # solo por tener vecinas vacías. Una única fila no acredita un producto.
    covered = known & (signal >= 2) & (signal >= MIN_SIGNAL_FRACTION * n_observed)
    return {'hyb_ev': evidence, 'band': band, 'sampled': sampled,
            'domain': domain, 'known': known, 'covered': covered}


def score_level_from_features(feat, bounds=None):
    result = {'method': METHOD, 'interpretation_policy': POLICY, 'status': 'sin_medicion',
              'pct': None, 'state': 'sin_medicion', 'label': 'Sin medición', 'color': '#64748b',
              'review_required': False, 'review_reason': None, 'signal_pattern': None,
              'experimental_threshold_pct': THRESHOLD}
    if not feat or not feat.get('valid'):
        return result
    maps = compute_cell_maps(feat, bounds)
    domain, known, covered = (maps[key] for key in ('domain', 'known', 'covered'))
    positions = np.flatnonzero(domain)
    if not positions.size:
        return result
    # Conservar posiciones: las columnas desconocidas no se comprimen ni
    # unen dos huecos separados. El hueco se mide sobre el ancho detectado.
    span = slice(positions[0], positions[-1] + 1)
    count = int(domain.sum())
    known_count = int(known.sum())
    observable_pct = 100.0 * known_count / count
    front = 100.0 * int(covered.sum()) / known_count if known_count else 0.0
    gap = longest_empty_run_pct((covered | ~known)[span], bridge_single=False)
    low = 100.0 * int(covered.sum()) / count
    high = 100.0 * (int(covered.sum()) + count - known_count) / count
    # Abstenerse también cuando lo desconocido podría cambiar la decisión.
    review = known_count < 3 or observable_pct < 100 * MIN_OBSERVED_WIDTH or low < THRESHOLD <= high
    state = 'revisar' if review else 'reponer' if front < THRESHOLD else 'suficiente'
    reason = ('Franja basal insuficientemente observable o con decisión incierta.' if review else None)
    result.update(status='medido', pct=round(front, 2), state=state,
                  label={'revisar': 'Revisar · base no observable', 'reponer': 'Reponer', 'suficiente': 'Suficiente'}[state],
                  color={'revisar': '#a16207', 'reponer': '#dc2626', 'suficiente': '#16a34a'}[state],
                  review_required=review, review_reason=reason,
                  signal_pattern='basal_unobserved' if review else None,
                  front_hyb_pct=round(front, 2), observed_width_pct=round(observable_pct, 2),
                  coverage_lower_pct=round(low, 2), coverage_upper_pct=round(high, 2),
                  max_gap_pct=round(gap, 2), valid_cells=int(maps['sampled'].sum()))
    return result


def provenance():
    return {'method': METHOD, 'revision': REVISION,
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'interpretation_policy': {'name': POLICY, 'threshold_pct': THRESHOLD},
            'meaning': 'Cobertura de señal en el frente observable; no stock físico ni volumen.',
            'calibrated': False, 'threshold_calibration': 'uncalibrated_experimental',
            'parameters': {'band': BAND, 'vertical_cell_px': VERTICAL_CELL_PX, 'min_observed_cell': MIN_OBSERVED_CELL,
                           'min_observed_band': MIN_OBSERVED_BAND,
                           'min_observed_width': MIN_OBSERVED_WIDTH,
                           'min_signal_fraction': MIN_SIGNAL_FRACTION},
            'changes_yolo_state': False}
