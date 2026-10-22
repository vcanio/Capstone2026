"""Señal experimental de detección de bordes dentro de máscaras YOLO; nunca decide el estado."""
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
METHOD = 'paulo_mascara_v2_color_textura'
WEIGHTED_METHOD = 'paulo_mascara_v2_combinacion_ponderada'
STRUCTURE_POLICY = 'rieles_horizontales_v1'


def horizontal_structures(edges, cell):
    """Rieles largos: excluir su banda de todas las señales, no solo de Canny.

    La longitud se exige respecto del nivel y se limita la pendiente para no
    tratar los lados verticales de envases como estructuras de la góndola.
    """
    blocked = np.zeros_like(edges, dtype=np.uint8)
    minimum = max(3*cell, round(.45*edges.shape[1]))
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50,
                            minLineLength=minimum, maxLineGap=10)
    if lines is not None:
        for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
            if abs(x2-x1) >= minimum and abs(y2-y1) <= .12*abs(x2-x1):
                cv2.line(blocked, (int(x1), int(y1)), (int(x2), int(y2)), 1, max(7, round(cell*.5)))
    return blocked


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
    surface_weight: float = .70
    width_row_fraction: float = .20


@lru_cache(maxsize=2)
def paulo(version='v1'):
    if version not in ('v1', 'v2'):
        raise ValueError('Versión de bordes inválida.')
    filename = 'gondola_combinacion_ponderada.py' if version == 'v2' else 'gondola_bordes.py'
    portable = Path(__file__).with_name(filename)
    source = portable if portable.is_file() else ROOT / 'Experimentos/Bordes' / filename
    spec = importlib.util.spec_from_file_location('paulo_' + version, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def provenance(version='v1', parameters=None):
    if version not in ('v1', 'v2'):
        raise ValueError('Versión de bordes inválida.')
    portable = Path(__file__).with_name('gondola_bordes.py')
    base = Path(__file__).parent if portable.is_file() else ROOT
    files = ([Path(__file__), portable] if portable.is_file() else
             [Path(__file__), ROOT / 'Experimentos/Bordes/gondola_bordes.py',
              ROOT / 'Experimentos/Bordes/Versiones/gondola_bordes_paulo_20261020.py'])
    if version == 'v2':
        files.append(base / ('gondola_combinacion_ponderada.py' if portable.is_file() else
                             'Experimentos/Bordes/gondola_combinacion_ponderada.py'))
    return {'method': WEIGHTED_METHOD if version == 'v2' else METHOD,
            'parameters': asdict(parameters or Parameters(opening=1 if version == 'v2' else 3)),
            'mask_policy': 'yolo_raster_v1',
            'structure_policy': STRUCTURE_POLICY,
            'sources': {p.relative_to(base).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'calibrated': False, 'changes_yolo_state': False,
            'meaning': 'Señal de bordes/color/textura; no porcentaje validado de producto ni confianza YOLO.'}


class Analyzer:
    def __init__(self, rgb, parameters=None, version='v1'):
        if version not in ('v1', 'v2'):
            raise ValueError('Versión de bordes inválida.')
        self.version = version
        self.method = WEIGHTED_METHOD if version == 'v2' else METHOD
        self.p = parameters or Parameters(opening=1 if version == 'v2' else 3)
        if not (np.isfinite(self.p.surface_weight) and 0 <= self.p.surface_weight <= 1 and
                np.isfinite(self.p.width_row_fraction) and 0 <= self.p.width_row_fraction <= 1):
            raise ValueError('Los pesos de superficie y ancho deben estar entre 0 y 1.')
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
        self.edges = paulo(self.version).mapa_bordes(bgr, self.p.canny_low, self.p.canny_high)
        self.filtered_edges = np.zeros_like(self.edges)
        self.structures = np.zeros_like(self.edges, dtype=bool)
        self.hsv = cv2.cvtColor(cv2.GaussianBlur(bgr, (5, 5), 0), cv2.COLOR_BGR2HSV)
        self.gray_texture = cv2.medianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), 5).astype(np.float32)
        # El Canny de producto puede borrar por completo un riel tenue. Buscar
        # estructuras con umbrales menores permite excluir también su textura.
        self.structure_edges = cv2.Canny(self.gray_texture.astype(np.uint8), 10, 30)
        if self.version == 'v2':
            gx = cv2.Sobel(self.gray_texture, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(self.gray_texture, cv2.CV_32F, 0, 1, ksize=3)
            self.gradient = cv2.magnitude(gx, gy)
        self.signal = np.zeros(self.rgb.shape[:2], dtype=bool)

    def analyze(self, mask, state=None, valid_contour=True):
        missing = {'method': self.method, 'status': 'sin_medicion', 'area_signal_pct': None,
                   'width_signal_pct': None, 'calibrated': False}
        if self.version == 'v2':
            missing['combined_signal_pct'] = None
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
        line_width = self.rgb.shape[1] if self.version == 'v2' else w
        raw_edges = self.edges[y:y+h, x:x+w]
        structure = horizontal_structures(self.structure_edges[y:y+h, x:x+w]*region, self.p.cell)
        # Una trama densa también produce muchas rectas de Hough. Los rieles
        # deben ser bandas finas, no ocupar una parte extensa del nivel.
        if float((structure*region).sum()) > .20*float(region.sum()):
            structure.fill(0)
        observed = region * (1-structure)
        self.structures[y:y+h, x:x+w] |= (structure > 0) & (region > 0)
        # La cobertura del nivel sigue siendo el denominador de ocupación.
        # Para color/textura/gradiente solo se observan píxeles sin estructura.
        observed_coverage = cv2.resize(observed.astype(np.float32), grid_size, interpolation=cv2.INTER_AREA)
        denominator = np.maximum(observed_coverage, 1e-6)
        edges = paulo(self.version).quitar_lineas_largas(raw_edges, max(30, round(self.p.line*line_width)))
        filtered = self.filtered_edges[y:y+h, x:x+w]
        np.maximum(filtered, edges * observed, out=filtered)
        density = cv2.resize((edges > 0).astype(np.float32)*observed, grid_size, interpolation=cv2.INTER_AREA) / denominator
        active = density > self.p.edge_density
        if self.p.color_fraction > 0 or self.version == 'v2':
            hsv = self.hsv[y:y+h, x:x+w]
            color = ((hsv[..., 1] > self.p.saturation) & (hsv[..., 2] > self.p.min_color_value)).astype(np.float32)
            color_density = cv2.resize(color*observed, grid_size, interpolation=cv2.INTER_AREA) / denominator
            active |= color_density > self.p.color_fraction
        if self.p.texture_std > 0 or self.version == 'v2':
            gray = self.gray_texture[y:y+h, x:x+w]
            mean = cv2.resize(gray*observed, grid_size, interpolation=cv2.INTER_AREA) / denominator
            mean2 = cv2.resize(gray*gray*observed, grid_size, interpolation=cv2.INTER_AREA) / denominator
            deviation = np.sqrt(np.maximum(mean2-mean*mean, 0))
            active |= (deviation > self.p.texture_std) & (mean < self.p.texture_max_value)
        if self.version == 'v2':
            source = paulo('v2')
            # Percentiles and Otsu see only cells covered by YOLO's raster.
            def normalized(values):
                normalized_map = np.zeros_like(values, dtype=np.float32)
                normalized_map[usable] = source.normalizar_por_roi(values[usable])
                return normalized_map
            gradient = cv2.resize(self.gradient[y:y+h, x:x+w]*observed, grid_size,
                                  interpolation=cv2.INTER_AREA) / denominator
            score = (.35*normalized(density) + .30*normalized(gradient) +
                     .20*normalized(color_density) + .15*normalized(deviation))
            threshold = source.umbral_adaptativo(score[usable])
            raw_active = (score >= threshold) & usable
            active = raw_active
        active = (active & usable).astype(np.uint8)
        if self.p.opening > 1:
            active = cv2.morphologyEx(active, cv2.MORPH_OPEN, np.ones((self.p.opening, self.p.opening), np.uint8))
        if self.p.opening > 1 or self.version == 'v2':
            active = cv2.morphologyEx(active, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        active = active.astype(bool) & usable & (observed_coverage > 0)
        weights = coverage * usable
        area = 100 * float((active*observed_coverage*usable).sum()) / float(weights.sum())
        column_rows = usable.sum(axis=0)
        valid_columns = column_rows >= self.p.min_column_rows
        required = np.maximum(self.p.min_column_rows, np.ceil(column_rows*self.p.column_fraction))
        active_columns = (active.sum(axis=0) >= required) & valid_columns
        width = 100 * float(active_columns.sum()) / int(valid_columns.sum()) if valid_columns.any() else None
        extra = {}
        if self.version == 'v2':
            valid_columns = column_rows > 0
            fractions = raw_active.sum(axis=0) / np.maximum(column_rows, 1)
            covered_columns = (fractions >= self.p.width_row_fraction) & valid_columns
            width = 100 * float(covered_columns.sum()) / int(valid_columns.sum())
            extra = {'combined_signal_pct': round(self.p.surface_weight*area + (1-self.p.surface_weight)*width, 2),
                     'adaptive_threshold': round(threshold, 6)}
        self.signal[y:y+h, x:x+w] |= (cv2.resize(active.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0) & (observed > 0)
        return {'method': self.method, 'status': 'medido', 'area_signal_pct': round(area, 2), **extra,
                'width_signal_pct': round(width, 2) if width is not None else None,
                'mask_source': 'yolo_raster', 'contour_warning': not bool(valid_contour),
                'calibrated': False, 'valid_cells': int(usable.sum()),
                'structure_policy': STRUCTURE_POLICY,
                'reason': None if width is not None else 'Altura insuficiente para proyectar columnas.'}

    def overlay(self):
        output = self.rgb.copy()
        output[self.signal] = (.55*output[self.signal] + .45*np.array([255, 194, 32])).astype(np.uint8)
        return output
