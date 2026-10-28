"""Medición experimental dentro de las máscaras de niveles de YOLO.

Lectura recomendada: Parameters → Analyzer.analyze → front_coverage.
V1 mide área; V2 conserva área/ancho 70/30. V3 usa el motor V2 con
front_mode=True para medir cobertura del frente. La presentación interpreta
los porcentajes y las reglas de revisión en presentacion_niveles.py.
"""
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
FRAGMENTED_STRUCTURE_POLICY = 'rieles_fragmentados_inferiores_v2'

# Umbrales experimentales de interpretación: no son una calibración de stock.
FRONT_SUPPORT_START = .35  # Ignorar el 35 % superior al buscar respaldo frontal.
FRONT_MIN_ROWS = 2  # Celdas verticales contiguas que respaldan una columna.
SUFFICIENT_FRONT_PCT = 30
ABSOLUTE_EDGE_DENSITY = .012
ABSOLUTE_GRADIENT = 16
ABSOLUTE_TEXTURE_STD = 9
LOWER_BAND_MIN_SHARE = .98
LOWER_BAND_MAX_CENTRAL_EVIDENCE = .05
LOWER_BAND_MAX_EDGE_EVIDENCE = .03
MAX_STRUCTURE_FRACTION = .20  # Una banda más extensa no se acepta como riel.
UPPER_ONLY_SIGNAL_SHARE = .95
CENTRAL_WINDOW = (.15, .40, .85, .65)  # Izquierda, arriba, derecha, abajo (0–1).
MIN_CENTRAL_EVIDENCE = .10
LOWER_REGION_START = .65
MIN_LOWER_EDGE_EVIDENCE = .25
FEATURE_WEIGHTS = (.35, .30, .20, .15)  # Bordes, gradiente, color, textura.



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


def fragmented_lower_rails(edges, cell):
    """Agrupa tramos casi colineales de barandas en el tercio inferior.

    Exige cobertura horizontal extensa; no extrapola a través de huecos
    grandes ni elimina una franja inferior fija o los lados de los envases.
    El margen incluye el halo de los filtros de gradiente/color/textura.
    """
    height, width = edges.shape
    blocked = np.zeros_like(edges, dtype=np.uint8)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30,
                           minLineLength=max(2*cell, round(.08*width)), maxLineGap=10)
    if lines is None:
        return blocked
    candidates = []
    for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
        if x2 < x1:
            x1, y1, x2, y2 = x2, y2, x1, y1
        if x2 == x1 or abs(y2-y1) > .08*(x2-x1) or min(y1, y2) < .65*height:
            continue
        slope = (y2-y1)/(x2-x1)
        center_y = y1 + slope*(width/2-x1)
        candidates.append((center_y, slope, int(x1), int(x2)))
    groups = []
    tolerance = max(3, round(cell*.25))
    for line in sorted(candidates):
        if not groups or line[0]-groups[-1][0][0] > tolerance:
            groups.append([])
        groups[-1].append(line)
    for group in groups:
        spans = []
        for _, _, left, right in sorted(group, key=lambda item: item[2]):
            if spans and left <= spans[-1][1]:
                spans[-1][1] = max(spans[-1][1], right)
            else:
                spans.append([left, right])
        covered = sum(right-left for left, right in spans)
        if covered < .5*width or spans[-1][1]-spans[0][0] < .65*width:
            continue
        center_y = float(np.median([line[0] for line in group]))
        slope = float(np.median([line[1] for line in group]))
        # Unir solo huecos pequeños respaldados por tramos colineales cercanos.
        joined = []
        for left, right in spans:
            if joined and left-joined[-1][1] <= max(10, round(.03*width)):
                joined[-1][1] = right
            else:
                joined.append([left, right])
        for left, right in joined:
            cv2.line(blocked, (left, round(center_y+slope*(left-width/2))),
                     (right, round(center_y+slope*(right-width/2))), 1,
                     max(7, round(cell*.5)+4))
    return blocked


def lower_band_is_low_signal(band, lower_share, combined, width, central, lower_edges):
    """Reconocer señal débil en la base sin respaldo suficiente de producto.

    Las proporciones usan 0–1; combined y width usan porcentajes de 0–100.
    Es una excepción experimental a la revisión por franja horizontal.
    """
    return (band and lower_share >= LOWER_BAND_MIN_SHARE
            and combined < SUFFICIENT_FRONT_PCT and width == 0
            and central < LOWER_BAND_MAX_CENTRAL_EVIDENCE
            and lower_edges < LOWER_BAND_MAX_EDGE_EVIDENCE)


def front_coverage(active, evidence, usable):
    """Ancho respaldado por señal en al menos dos filas contiguas.

    active, evidence y usable son matrices booleanas de filas × columnas.
    Omite el 35 % superior como heurística para reducir cartelería; no la
    reconoce semánticamente. Devuelve un porcentaje 0–100 o None sin columnas.
    La altura libre sobre un producto no reduce su aporte al frente.
    """
    # Cada columna cuenta una sola vez aunque haya muchos píxeles de señal.
    rows = np.arange(usable.shape[0])[:, None]
    support_zone = usable & (rows >= FRONT_SUPPORT_START*usable.shape[0])
    supported = active & evidence & support_zone
    consecutive = supported[1:] & supported[:-1]
    valid_columns = support_zone.sum(axis=0) >= FRONT_MIN_ROWS
    covered_columns = consecutive.any(axis=0) & valid_columns
    if not valid_columns.any():
        return None
    return 100 * float(covered_columns.sum()) / int(valid_columns.sum())


def contiguous_column_coverage(active, usable, fraction):
    """Fracción de columnas con un tramo continuo respecto de su altura útil."""
    rows = usable.sum(axis=0)
    valid = rows > 0
    runs = np.zeros(active.shape[1], dtype=int)
    longest = np.zeros_like(runs)
    for row in (active & usable):
        runs = np.where(row, runs + 1, 0)
        longest = np.maximum(longest, runs)
    covered = (longest >= np.ceil(rows*fraction)) & valid
    return 100 * float(covered.sum()) / int(valid.sum()) if valid.any() else None


@dataclass(frozen=True)
class Parameters:
    """Configuración de imagen/grilla y compatibilidad de métodos anteriores.

    Tamaños en píxeles; fracciones en 0–1. Los campos *_pct usan 0–100.
    No todos los parámetros se aplican a todas las versiones del estimador.
    """
    # Resolución, grilla y detector de bordes.
    max_side: int = 1600
    cell: int = 24
    canny_low: int = 40
    canny_high: int = 120
    edge_density: float = .04
    margin: float = .03
    opening: int = 3
    line: float = .04
    # Evidencia de color y textura.
    color_fraction: float = .35
    saturation: int = 70
    min_color_value: int = 50
    texture_std: float = 4.
    texture_max_value: int = 90
    # Cobertura de máscara y métricas históricas de área/ancho.
    cell_coverage: float = .5
    column_fraction: float = .15
    min_column_rows: int = 2
    surface_weight: float = .70
    width_row_fraction: float = .20  # Solo se conserva para compatibilidad de configuraciones.
    width_contiguous_fraction: float = .45
    coherence_max_gap_pct: float = 45.
    band_signal_share: float = .90


@lru_cache(maxsize=2)
def paulo(version='v1'):
    """Cargar una vez las funciones clásicas de bordes de la versión solicitada."""
    if version not in ('v1', 'v2'):
        raise ValueError('Versión de bordes inválida.')
    filename = 'gondola_combinacion_ponderada.py' if version == 'v2' else 'gondola_bordes.py'
    portable = Path(__file__).with_name(filename)
    source = portable if portable.is_file() else ROOT / 'Laboratorio/Experimentos/Bordes' / filename
    spec = importlib.util.spec_from_file_location('paulo_' + version, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def provenance(version='v1', parameters=None):
    """Registrar parámetros y hashes para identificar cómo se obtuvo una medición.

    Estos datos describen el cálculo; no certifican precisión ni calibración.
    La integración V3 añade su política frontal en inferencia.analyze_edges.
    """
    if version not in ('v1', 'v2'):
        raise ValueError('Versión de bordes inválida.')
    portable = Path(__file__).with_name('gondola_bordes.py')
    base = Path(__file__).parent if portable.is_file() else ROOT
    files = ([Path(__file__), portable] if portable.is_file() else
             [Path(__file__), ROOT / 'Laboratorio/Experimentos/Bordes/gondola_bordes.py',
              ROOT / 'Laboratorio/Experimentos/Bordes/Versiones/gondola_bordes_paulo_20261020.py'])
    if version == 'v2':
        files.append(base / ('gondola_combinacion_ponderada.py' if portable.is_file() else
                             'Laboratorio/Experimentos/Bordes/gondola_combinacion_ponderada.py'))
    return {'method': WEIGHTED_METHOD if version == 'v2' else METHOD,
            'parameters': asdict(parameters or Parameters(opening=1 if version == 'v2' else 3)),
            'interpretation_policy': ({'name': 'spatial_signal_abstention_v3', 'upper_height_fraction': .5,
                                       'minimum_signal_share': UPPER_ONLY_SIGNAL_SHARE,
                                       'central_window': list(CENTRAL_WINDOW),
                                       'minimum_central_evidence': MIN_CENTRAL_EVIDENCE,
                                       'minimum_lower_edge_fraction': MIN_LOWER_EDGE_EVIDENCE,
                                       'absolute_edge_density': ABSOLUTE_EDGE_DENSITY,
                                       'absolute_gradient': ABSOLUTE_GRADIENT, 'absolute_deviation': ABSOLUTE_TEXTURE_STD} if version == 'v2' else None),
            'mask_policy': 'yolo_raster_v1',
            'structure_policy': FRAGMENTED_STRUCTURE_POLICY if version == 'v2' else STRUCTURE_POLICY,
            'sources': {p.relative_to(base).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'calibrated': False, 'changes_yolo_state': False,
            'meaning': 'Señal de bordes/color/textura; no porcentaje validado de producto ni confianza YOLO.'}


@dataclass(frozen=True)
class _LevelGrid:
    """Región de un nivel: máscaras en píxeles y cobertura en la grilla.

    region: matriz binaria de alto × ancho del recorte, con margen erosionado.
    coverage: fracción de máscara por celda; usable: celdas que admiten medición.
    grid_size mantiene el orden (columnas, filas) que requiere OpenCV.
    """
    x: int
    y: int
    width: int
    height: int
    region: np.ndarray
    grid_size: tuple[int, int]
    coverage: np.ndarray
    usable: np.ndarray

    @property
    def bounds(self):
        return self.x, self.y, self.width, self.height


@dataclass(frozen=True)
class _CellSignals:
    """Señales de un nivel, antes y después de la limpieza morfológica.

    observed está en píxeles; las demás matrices están en filas × columnas
    de la grilla. raw_active es la activación previa al cierre; active alimenta
    el área y el mapa fucsia. V1 no calcula gradiente ni umbral ponderado.
    """
    observed: np.ndarray
    observed_coverage: np.ndarray
    active: np.ndarray
    density: np.ndarray
    raw_active: np.ndarray | None = None
    gradient: np.ndarray | None = None
    deviation: np.ndarray | None = None
    threshold: float | None = None


class Analyzer:
    """Preparar la foto una vez y reutilizar sus mapas para cada nivel.

    rgb: arreglo uint8 de alto × ancho × 3 canales RGB.
    Las máscaras se reciben a la resolución original; los mapas internos
    pueden reducirse según max_side para acotar el coste del análisis.
    """
    def __init__(self, rgb, parameters=None, version='v1', front_mode=False):
        if version not in ('v1', 'v2'):
            raise ValueError('Versión de bordes inválida.')
        self.version = version
        self.front_mode = front_mode and version == 'v2'
        self.method = WEIGHTED_METHOD if version == 'v2' else METHOD
        self.p = parameters or Parameters(opening=1 if version == 'v2' else 3)
        if not (np.isfinite(self.p.surface_weight) and 0 <= self.p.surface_weight <= 1 and
                np.isfinite(self.p.width_row_fraction) and 0 <= self.p.width_row_fraction <= 1 and
                np.isfinite(self.p.width_contiguous_fraction) and 0 < self.p.width_contiguous_fraction <= 1 and
                np.isfinite(self.p.coherence_max_gap_pct) and 0 <= self.p.coherence_max_gap_pct <= 100 and
                np.isfinite(self.p.band_signal_share) and 0 < self.p.band_signal_share <= 1):
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
        """Medir una máscara binaria de YOLO sin alterar la imagen ni la predicción.

        mask debe tener el mismo alto × ancho que la foto original. Devuelve
        un diccionario de métricas o status='sin_medicion' con su motivo.
        valid_contour solo registra una advertencia sobre el polígono visual.
        La decisión Reponer/Suficiente se toma en presentacion_niveles.py.
        """
        missing = {'method': self.method, 'status': 'sin_medicion', 'area_signal_pct': None,
                   'width_signal_pct': None, 'calibrated': False}
        if self.version == 'v2':
            missing['combined_signal_pct'] = None
        if state == 'no_evaluable':
            return {**missing, 'reason': 'YOLO asignó no evaluable; se omite la medición.'}

        # 1. Alinear la máscara y construir las celdas que se pueden analizar.
        level = self._prepare_level(mask, missing)
        if isinstance(level, dict):
            return level

        # 2. Excluir estructura y medir bordes, color, gradiente y textura.
        signals = self._measure_cells(level)

        # 3. Conservar área y ancho históricos; V3 añade cobertura del frente.
        area, width = self._measure_legacy_coverage(level, signals)
        extra = {}
        if self.version == 'v2':
            width, extra = self._measure_v2(level, signals, area)

        # 4. Acumular la señal para dibujar el mapa de todos los niveles.
        x, y, w, h = level.bounds
        active, observed = signals.active, signals.observed
        self.signal[y:y+h, x:x+w] |= (cv2.resize(active.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0) & (observed > 0)
        return {'method': self.method, 'status': 'medido', 'area_signal_pct': round(area, 2), **extra,
                'width_signal_pct': round(width, 2) if width is not None else None,
                'mask_source': 'yolo_raster', 'contour_warning': not bool(valid_contour),
                'calibrated': False, 'valid_cells': int(level.usable.sum()),
                'structure_policy': FRAGMENTED_STRUCTURE_POLICY if self.version == 'v2' else STRUCTURE_POLICY,
                'reason': None if width is not None else 'Altura insuficiente para proyectar columnas.'}

    def _prepare_level(self, mask, missing) -> _LevelGrid | dict:
        """Validar la máscara y devolver su región/grilla o un motivo de rechazo."""
        if mask is None:
            return {**missing, 'reason': 'Falta una máscara alineada con la foto.'}
        mask = np.asarray(mask)
        if mask.shape != self.original_shape:
            return {**missing, 'reason': 'Falta una máscara alineada con la foto.'}
        if not np.isfinite(mask).all() or not ((mask == 0) | (mask == 1)).all():
            return {**missing, 'reason': 'La máscara de píxeles no es binaria o contiene valores inválidos.'}
        # La máscara raster pertenece a YOLO. Un cruce del polígono visual
        # no invalida sus píxeles; nunca sustituirla por su caja.
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
        return _LevelGrid(x, y, w, h, region, grid_size, coverage, usable)

    def _exclude_structure(self, level: _LevelGrid):
        """Excluir rieles sin quitar más del límite permitido de la región.

        Devuelve la máscara observada y la referencia previa al filtro de
        barandas fragmentadas. Ambas tienen el tamaño en píxeles del recorte.
        """
        x, y, w, h = level.bounds
        region = level.region
        structure = horizontal_structures(self.structure_edges[y:y+h, x:x+w]*region, self.p.cell)
        # Una trama densa también produce muchas rectas de Hough. Los rieles
        # deben ser bandas finas, no ocupar una parte extensa del nivel.
        if float((structure*region).sum()) > MAX_STRUCTURE_FRACTION*float(region.sum()):
            structure.fill(0)
        reference_observed = region * (1-structure)
        if self.version == 'v2':
            fragments = fragmented_lower_rails(self.structure_edges[y:y+h, x:x+w]*region, self.p.cell)
            # Conservar la exclusión anterior si la propuesta abarca demasiado.
            combined = np.maximum(structure, fragments)
            if float((combined*region).sum()) <= MAX_STRUCTURE_FRACTION*float(region.sum()):
                structure = combined
        observed = region * (1-structure)
        self.structures[y:y+h, x:x+w] |= (structure > 0) & (region > 0)
        return observed, reference_observed

    def _measure_cells(self, level: _LevelGrid) -> _CellSignals:
        """Extraer señal por celda, preservando la referencia previa a excluir rieles."""
        x, y, w, h = level.bounds
        region, grid_size, usable = level.region, level.grid_size, level.usable
        raw_active = gradient = deviation = threshold = None
        # Primero se observan píxeles sin rieles; después se resumen por celda.
        observed, reference_observed = self._exclude_structure(level)
        line_width = self.rgb.shape[1] if self.version == 'v2' else w
        raw_edges = self.edges[y:y+h, x:x+w]
        # La cobertura del nivel sigue siendo el denominador de ocupación.
        # Para color/textura/gradiente solo se observan píxeles sin estructura.
        observed_coverage = cv2.resize(observed.astype(np.float32), grid_size, interpolation=cv2.INTER_AREA)
        denominator = np.maximum(observed_coverage, 1e-6)
        edges = paulo(self.version).quitar_lineas_largas(raw_edges, max(30, round(self.p.line*line_width)))
        filtered = self.filtered_edges[y:y+h, x:x+w]
        np.maximum(filtered, edges * observed, out=filtered)
        density = cv2.resize((edges > 0).astype(np.float32)*observed, grid_size, interpolation=cv2.INTER_AREA) / denominator
        # V1 combina condiciones directas. V2 reemplaza esta activación por
        # una suma ponderada normalizada de las cuatro características.
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
            gradient = cv2.resize(self.gradient[y:y+h, x:x+w]*observed, grid_size,
                                  interpolation=cv2.INTER_AREA) / denominator
            features = (density, gradient, color_density, deviation)
            references = features
            if not np.array_equal(reference_observed, observed):
                # Excluir un riel no debe amplificar el fondo débil restante.
                # Conservar la referencia anterior a la exclusión.
                ref_coverage = cv2.resize(reference_observed.astype(np.float32), grid_size,
                                         interpolation=cv2.INTER_AREA)
                ref_denominator = np.maximum(ref_coverage, 1e-6)
                def ref_mean(values):
                    return cv2.resize(values*reference_observed, grid_size,
                                      interpolation=cv2.INTER_AREA) / ref_denominator
                ref_gray = ref_mean(gray)
                references = (ref_mean((edges > 0).astype(np.float32)),
                              ref_mean(self.gradient[y:y+h, x:x+w]), ref_mean(color),
                              np.sqrt(np.maximum(ref_mean(gray*gray)-ref_gray*ref_gray, 0)))
            # Percentiles y Otsu solo usan celdas cubiertas por la máscara YOLO.
            def normalized(values, reference):
                normalized_map = np.zeros_like(values, dtype=np.float32)
                low, high = np.percentile(reference[usable], [10, 90])
                if high-low >= 1e-6:
                    normalized_map[usable] = np.clip((values[usable]-low)/(high-low), 0., 1.)
                return normalized_map
            coefficients = FEATURE_WEIGHTS
            score = sum(weight*normalized(value, reference)
                        for weight, value, reference in zip(coefficients, features, references))
            reference_score = sum(weight*normalized(reference, reference)
                                  for weight, reference in zip(coefficients, references))
            # La exclusión puede quitar evidencia, pero no crearla al promediar
            # menos píxeles en una celda parcialmente cubierta.
            score = np.minimum(score, reference_score)
            threshold = source.umbral_adaptativo(reference_score[usable])
            raw_active = (score >= threshold) & usable
            active = raw_active
        active = (active & usable).astype(np.uint8)
        if self.p.opening > 1:
            active = cv2.morphologyEx(active, cv2.MORPH_OPEN, np.ones((self.p.opening, self.p.opening), np.uint8))
        if self.p.opening > 1 or self.version == 'v2':
            active = cv2.morphologyEx(active, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        active = active.astype(bool) & usable & (observed_coverage > 0)
        return _CellSignals(observed, observed_coverage, active, density,
                            raw_active, gradient, deviation, threshold)

    def _measure_legacy_coverage(self, level: _LevelGrid, signals: _CellSignals):
        """Área y ancho de los métodos anteriores, conservados como diagnóstico."""
        coverage, usable = level.coverage, level.usable
        active, observed_coverage = signals.active, signals.observed_coverage
        weights = coverage * usable
        area = 100 * float((active*observed_coverage*usable).sum()) / float(weights.sum())
        column_rows = usable.sum(axis=0)
        valid_columns = column_rows >= self.p.min_column_rows
        required = np.maximum(self.p.min_column_rows, np.ceil(column_rows*self.p.column_fraction))
        active_columns = (active.sum(axis=0) >= required) & valid_columns
        width = 100 * float(active_columns.sum()) / int(valid_columns.sum()) if valid_columns.any() else None
        return area, width

    def _measure_v2(self, level: _LevelGrid, signals: _CellSignals, area):
        """Calcular diagnóstico 70/30, revisión espacial y, en V3, cobertura frontal."""
        usable = level.usable
        active, raw_active = signals.active, signals.raw_active
        observed_coverage = signals.observed_coverage
        density, gradient, deviation = signals.density, signals.gradient, signals.deviation
        threshold = signals.threshold
        # Diagnóstico histórico: se conserva aunque V3 presente el frente.
        width = contiguous_column_coverage(raw_active, usable, self.p.width_contiguous_fraction)
        extra = {'combined_signal_pct': round(self.p.surface_weight*area + (1-self.p.surface_weight)*width, 2),
                 'adaptive_threshold': round(threshold, 6)}
        # Un cartel superior puede aportar área y ancho sobre una zona vacía.
        # Conservar las métricas para diagnóstico y revisar esa señal.
        signal_weights = active * observed_coverage * usable
        upper_half = (np.arange(active.shape[0]) + .5) / active.shape[0] <= .5
        total_signal = float(signal_weights.sum())
        upper_share = float(signal_weights[upper_half].sum()) / total_signal if total_signal else 0.
        thirds = np.array_split(signal_weights, 3, axis=0)
        vertical_profile = [float(part.sum()) / total_signal if total_signal else 0. for part in thirds]
        row_signal = signal_weights.sum(axis=1)
        window = max(1, int(np.ceil(active.shape[0] / 3)))
        band_share = (max(float(row_signal[i:i+window].sum())
                          for i in range(active.shape[0]-window+1)) / total_signal
                      if total_signal else 0.)
        coherence_gap = width - area
        band_ambiguity = total_signal > 0 and band_share >= self.p.band_signal_share
        incoherent = (extra['combined_signal_pct'] >= SUFFICIENT_FRONT_PCT and
                      coherence_gap >= self.p.coherence_max_gap_pct)
        review_required = band_ambiguity or incoherent or (total_signal > 0 and upper_share >= UPPER_ONLY_SIGNAL_SHARE)
        # La normalización relativa puede amplificar fondo o estructura.
        # Esta comprobación solo cambia la interpretación: mapas, métricas,
        # denominadores y máscaras de YOLO se conservan exactamente.
        left, top, right, bottom = CENTRAL_WINDOW
        yy, xx = np.indices(usable.shape)
        central_columns = (xx >= left*usable.shape[1]) & (xx < right*usable.shape[1])
        center = usable & central_columns & (yy >= top*usable.shape[0]) & (yy < bottom*usable.shape[0])
        absolute_evidence = (density > ABSOLUTE_EDGE_DENSITY) | (
            (gradient > ABSOLUTE_GRADIENT) & (deviation > ABSOLUTE_TEXTURE_STD))
        central_density = float((raw_active & center & absolute_evidence).sum()) / max(1, int(center.sum()))
        lower = usable & central_columns & (yy >= LOWER_REGION_START*usable.shape[0])
        lower_edges = float(((density > ABSOLUTE_EDGE_DENSITY) & lower).sum()) / max(1, int(lower.sum()))
        # Una señal débil confinada a la base, sin respaldo de bordes,
        # no debe por sí sola impedir la lectura de baja ocupación.
        lower_band_low_signal = lower_band_is_low_signal(
            band_ambiguity, vertical_profile[2], extra['combined_signal_pct'],
            width, central_density, lower_edges)
        if lower_band_low_signal:
            review_required = False
        # Un producto bajo con bordes en la base continúa siendo medible.
        # Falta de respaldo no certifica vacío ni detecta un cartel.
        peripheral_ambiguity = (total_signal > 0 and central_density < MIN_CENTRAL_EVIDENCE and lower_edges < MIN_LOWER_EDGE_EVIDENCE
                                and extra['combined_signal_pct'] >= SUFFICIENT_FRONT_PCT)
        review_required |= peripheral_ambiguity
        extra.update(review_required=review_required,
                     signal_pattern=('lower_band_low_signal' if lower_band_low_signal else
                                     'upper_band_only' if upper_share >= UPPER_ONLY_SIGNAL_SHARE and total_signal > 0 else
                                     'horizontal_band' if band_ambiguity else
                                     'incoherent_width' if incoherent else
                                     'peripheral_ambiguity' if peripheral_ambiguity else None),
                     vertical_signal_thirds=[round(value, 6) for value in vertical_profile],
                     max_third_window_signal_share=round(band_share, 6),
                     width_area_gap_pct=round(coherence_gap, 2),
                     upper_half_signal_share=round(upper_share, 6),
                     central_evidence_fraction=round(central_density, 6),
                     lower_edge_evidence_fraction=round(lower_edges, 6),
                     review_reason=(('Señal concentrada en la franja superior: puede ser un cartel o el fondo. '
                                     if upper_share >= UPPER_ONLY_SIGNAL_SHARE else
                                     'Señal concentrada en una franja horizontal. ' if band_ambiguity else
                                     'Cobertura horizontal incoherente con el área de señal. ' if incoherent else
                                     'Señal periférica sin respaldo central suficiente: puede ser estructura, cartel o fondo. ') +
                                    'Revisa si hay productos; no se confirma ocupación.'
                                    if review_required else None))
        if self.front_mode:
            # Lectura vigente de V3: respaldo por columna sin exigir que los
            # productos llenen toda la altura. Se asume lleno detrás del frente.
            front = front_coverage(raw_active, absolute_evidence, usable)
            # Evidencia de producto en el frente permite filas bajas;
            # carteles superiores y señales débiles conservan la abstención.
            if front is not None and front >= SUFFICIENT_FRONT_PCT:
                extra.update(review_required=False, review_reason=None,
                             signal_pattern='front_product_evidence')
            extra.update(front_signal_pct=round(front, 2) if front is not None else None,
                         interpretation_policy='front_coverage_v1')
        return width, extra

    def overlay(self):
        """Devolver una copia RGB con la señal acumulada resaltada en fucsia."""
        output = self.rgb.copy()
        output[self.signal] = (.25*output[self.signal] + .75*np.array([230, 40, 190])).astype(np.uint8)
        return output
