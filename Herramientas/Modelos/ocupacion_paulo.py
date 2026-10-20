"""Señal experimental de Paulo dentro de máscaras YOLO; nunca decide el estado."""
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
METHOD = 'paulo_mascara_v2_color_textura'


@dataclass(frozen=True)
class Parameters:
    max_side: int = 1600
    cell: int = 24
    canny_low: int = 40
    canny_high: int = 120
    edge_density: float = .04
    margin: float = .03
    opening: int = 3
    line: float = .04
    color_fraction: float = .35
    saturation: int = 70
    min_color_value: int = 50
    texture_std: float = 4.
    texture_max_value: int = 90
    cell_coverage: float = .5
    column_fraction: float = .15
    min_column_rows: int = 2


@lru_cache(maxsize=1)
def paulo():
    source = ROOT / 'Experimentos/Bordes/gondola_bordes.py'
    spec = importlib.util.spec_from_file_location('paulo_original', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def provenance():
    files = [Path(__file__), ROOT / 'Experimentos/Bordes/gondola_bordes.py',
             ROOT / 'Experimentos/Bordes/Versiones/gondola_bordes_paulo_20261020.py']
    return {'method': METHOD, 'parameters': asdict(Parameters()),
            'mask_policy': 'yolo_raster_v1',
            'sources': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'calibrated': False, 'changes_yolo_state': False,
            'meaning': 'Señal de bordes/color/textura; no porcentaje validado de producto ni confianza YOLO.'}


class Analyzer:
    def __init__(self, rgb, parameters=None):
        self.p = parameters or Parameters()
        if self.p.cell < 2 or self.p.max_side < 32 or not 0 <= self.p.margin < .5:
            raise ValueError('Parámetros de escala o margen inválidos.')
        if not (0 <= self.p.canny_low < self.p.canny_high <= 255 and
                0 <= self.p.saturation <= 255 and 0 <= self.p.min_color_value <= 255 and
                0 <= self.p.texture_max_value <= 255 and self.p.texture_std >= 0 and
                0 < self.p.cell_coverage <= 1 and 0 <= self.p.color_fraction <= 1 and
                0 <= self.p.column_fraction <= 1 and self.p.min_column_rows >= 1 and self.p.opening >= 1):
            raise ValueError('Parámetros de color, textura o grilla inválidos.')
        self.original_shape = rgb.shape[:2]
        scale = min(1., self.p.max_side / max(rgb.shape[:2]))
        self.rgb = cv2.resize(rgb, (max(1, round(rgb.shape[1]*scale)), max(1, round(rgb.shape[0]*scale))), interpolation=cv2.INTER_AREA)
        bgr = cv2.cvtColor(self.rgb, cv2.COLOR_RGB2BGR)
        self.edges = paulo().mapa_bordes(bgr, self.p.canny_low, self.p.canny_high)
        self.filtered_edges = np.zeros_like(self.edges)
        self.hsv = cv2.cvtColor(cv2.GaussianBlur(bgr, (5, 5), 0), cv2.COLOR_BGR2HSV)
        self.gray_texture = cv2.medianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), 5).astype(np.float32)
        self.signal = np.zeros(self.rgb.shape[:2], dtype=bool)

    def analyze(self, mask, state=None, valid_contour=True):
        missing = {'method': METHOD, 'status': 'sin_medicion', 'area_signal_pct': None,
                   'width_signal_pct': None, 'calibrated': False}
        if state == 'no_evaluable':
            return {**missing, 'reason': 'YOLO asignó no evaluable; se omite la medición.'}
        if mask is None:
            return {**missing, 'reason': 'Falta una máscara alineada con la foto.'}
        mask = np.asarray(mask)
        if mask.shape != self.original_shape:
            return {**missing, 'reason': 'Falta una máscara alineada con la foto.'}
        if not np.isfinite(mask).all() or not ((mask == 0) | (mask == 1)).all():
            return {**missing, 'reason': 'La máscara de píxeles no es binaria o contiene valores inválidos.'}
        # The raster is YOLO's segmentation. A self-touching display polygon
        # does not invalidate these pixels; never replace them with its box.
        valid = cv2.resize(mask.astype(np.uint8), (self.rgb.shape[1], self.rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
        ys, xs = np.where(valid)
        if not len(xs):
            return {**missing, 'reason': 'La máscara está vacía.'}
        x, y, w, h = int(xs.min()), int(ys.min()), int(xs.max()-xs.min()+1), int(ys.max()-ys.min()+1)
        mx, my = max(1, round(w*self.p.margin)), max(1, round(h*self.p.margin))
        region = valid[y:y+h, x:x+w]
        region = cv2.erode(region, np.ones((2*my+1, 2*mx+1), np.uint8), borderType=cv2.BORDER_CONSTANT, borderValue=0)
        if w < self.p.cell or h < self.p.cell or int(region.sum()) < self.p.cell**2:
            return {**missing, 'reason': 'El nivel es demasiado pequeño para esta grilla.'}
        grid_size = max(1, round(w/self.p.cell)), max(1, round(h/self.p.cell))
        coverage = cv2.resize(region.astype(np.float32), grid_size, interpolation=cv2.INTER_AREA)
        usable = coverage >= self.p.cell_coverage
        if not usable.any():
            return {**missing, 'reason': 'No hay suficientes celdas dentro de la máscara.'}
        edges = paulo().quitar_lineas_largas(self.edges[y:y+h, x:x+w], max(30, round(self.p.line*w)))
        filtered = self.filtered_edges[y:y+h, x:x+w]
        np.maximum(filtered, edges * region, out=filtered)
        density = cv2.resize((edges > 0).astype(np.float32)*region, grid_size, interpolation=cv2.INTER_AREA) / np.maximum(coverage, 1e-6)
        active = density > self.p.edge_density
        if self.p.color_fraction > 0:
            hsv = self.hsv[y:y+h, x:x+w]
            color = ((hsv[..., 1] > self.p.saturation) & (hsv[..., 2] > self.p.min_color_value)).astype(np.float32)
            color_density = cv2.resize(color*region, grid_size, interpolation=cv2.INTER_AREA) / np.maximum(coverage, 1e-6)
            active |= color_density > self.p.color_fraction
        if self.p.texture_std > 0:
            gray = self.gray_texture[y:y+h, x:x+w]
            mean = cv2.resize(gray*region, grid_size, interpolation=cv2.INTER_AREA) / np.maximum(coverage, 1e-6)
            mean2 = cv2.resize(gray*gray*region, grid_size, interpolation=cv2.INTER_AREA) / np.maximum(coverage, 1e-6)
            deviation = np.sqrt(np.maximum(mean2-mean*mean, 0))
            active |= (deviation > self.p.texture_std) & (mean < self.p.texture_max_value)
        active = (active & usable).astype(np.uint8)
        if self.p.opening > 1:
            active = cv2.morphologyEx(active, cv2.MORPH_OPEN, np.ones((self.p.opening, self.p.opening), np.uint8))
            active = cv2.morphologyEx(active, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        active = active.astype(bool) & usable
        weights = coverage * usable
        area = 100 * float((active*weights).sum()) / float(weights.sum())
        column_rows = usable.sum(axis=0)
        valid_columns = column_rows >= self.p.min_column_rows
        required = np.maximum(self.p.min_column_rows, np.ceil(column_rows*self.p.column_fraction))
        active_columns = (active.sum(axis=0) >= required) & valid_columns
        width = 100 * float(active_columns.sum()) / int(valid_columns.sum()) if valid_columns.any() else None
        self.signal[y:y+h, x:x+w] |= (cv2.resize(active.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0) & (region > 0)
        return {'method': METHOD, 'status': 'medido', 'area_signal_pct': round(area, 2),
                'width_signal_pct': round(width, 2) if width is not None else None,
                'mask_source': 'yolo_raster', 'contour_warning': not bool(valid_contour),
                'calibrated': False, 'valid_cells': int(usable.sum()),
                'reason': None if width is not None else 'Altura insuficiente para proyectar columnas.'}

    def overlay(self):
        output = self.rgb.copy()
        output[self.signal] = (.55*output[self.signal] + .45*np.array([255, 194, 32])).astype(np.uint8)
        return output
