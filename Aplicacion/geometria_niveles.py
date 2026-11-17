"""Ajuste visual de niveles a cuatro lados; no modifica las máscaras de YOLO."""
import statistics

import cv2
import numpy as np


def _valid(points):
    """Comprobar convexidad, coordenadas finitas y área no degenerada."""
    return (np.isfinite(points).all() and cv2.isContourConvex(points.astype('float32'))
            and abs(cv2.contourArea(points.astype('float32'))) > 1)


def _refine(contour, quad):
    """Ajustar cuatro rectas y devolver sus intersecciones o None si no son fiables.

    contour y quad contienen puntos (x, y) en píxeles, ordenados por el borde.
    El ajuste robusto reduce la influencia de salientes locales de la máscara.
    """
    # Muestrear por longitud evita que los tramos en escalera pesen más que
    # los tramos rectos simplificados por el extractor de contornos.
    following = np.roll(contour, -1, axis=0)
    lengths = np.linalg.norm(following - contour, axis=1)
    spacing = max(.5, lengths.sum() / 1500)
    samples = np.concatenate([
        start + np.arange(max(1, int(np.ceil(length / spacing))))[:, None]
        / max(1, int(np.ceil(length / spacing))) * (end - start)
        for start, end, length in zip(contour, following, lengths)])
    edges = np.roll(quad, -1, axis=0) - quad
    length2 = np.sum(edges * edges, axis=1)
    if np.any(length2 < 1):
        return None
    relative = samples[:, None, :] - quad[None, :, :]
    position = np.sum(relative * edges, axis=2) / length2
    nearest = quad[None, :, :] + np.clip(position, 0, 1)[..., None] * edges
    distances = np.linalg.norm(samples[:, None, :] - nearest, axis=2)
    side = distances.argmin(axis=1)
    lines = []
    for index in range(4):
        selected = samples[(side == index) & (position[:, index] > .08)
                           & (position[:, index] < .92)]
        if len(selected) < 4:
            return None
        vx, vy, x, y = cv2.fitLine(selected.astype('float32'), cv2.DIST_WELSCH,
                                  0, .01, .01).reshape(-1)
        lines.append((np.array([x, y]), np.array([vx, vy])))
    corners = []
    for index in range(4):
        start, direction = lines[index - 1]
        end, other = lines[index]
        matrix = np.column_stack((direction, -other))
        if abs(np.linalg.det(matrix)) < .05:
            return None
        corners.append(start + np.linalg.solve(matrix, end - start)[0] * direction)
    return np.asarray(corners, dtype='float32')


def level_quadrilateral(points, size):
    """Devolver cuatro esquinas en orden de contorno o None sin ajuste fiable.

    Conserva la perspectiva (no exige ángulos rectos en la fotografía). Se usa
    exclusivamente para dibujar: clasificación, ocupación e IoU usan la salida
    original del modelo. Las coordenadas quedan dentro de la imagen.
    """
    contour = np.asarray(points, dtype='float32').reshape(-1, 2)
    if len(contour) < 3 or not np.isfinite(contour).all() or min(size) < 2:
        return None
    if abs(cv2.contourArea(contour)) <= 1:
        return None
    hull = cv2.convexHull(contour).reshape(-1, 2)
    perimeter = cv2.arcLength(hull, True)
    if perimeter <= 0:
        return None
    initial = None
    for fraction in np.linspace(.002, .10, 100):
        simplified = cv2.approxPolyDP(hull, fraction * perimeter, True).reshape(-1, 2)
        if len(simplified) == 4:
            initial = simplified
            break
        if len(simplified) < 4:
            break
    if initial is None:
        initial = cv2.boxPoints(cv2.minAreaRect(hull))
    if not _valid(initial):
        return None

    # Comparar a escala acotada, sin depender del tamaño de la foto.
    # Rechazar formas que cambien demasiado la región predicha.
    def raster(polygon, lower, scale):
        canvas = np.zeros((384, 384), dtype='uint8')
        coords = np.rint((polygon - lower) * scale + 1).astype('int32')
        cv2.fillPoly(canvas, [coords], 1)
        return canvas
    original_area = abs(cv2.contourArea(contour))
    candidates = [initial]
    refined = _refine(contour, initial)
    if refined is not None:
        candidates.insert(0, refined)
    best, best_score = None, .55
    for candidate in candidates:
        candidate = candidate.copy()
        candidate[:, 0] = candidate[:, 0].clip(0, size[0] - 1)
        candidate[:, 1] = candidate[:, 1].clip(0, size[1] - 1)
        if not _valid(candidate):
            continue
        if not .5 <= abs(cv2.contourArea(candidate)) / original_area <= 1.8:
            continue
        # Incluir también las esquinas ajustadas en el lienzo; recortar al
        # límite del contorno original ocultaría expansiones indebidas.
        combined = np.concatenate((contour, candidate))
        lower = combined.min(axis=0)
        scale = 380 / max(float(np.ptp(combined, axis=0).max()), 1)
        reference = raster(contour, lower, scale)
        predicted = raster(candidate, lower, scale)
        score = np.logical_and(reference, predicted).sum() / max(
            1, np.logical_or(reference, predicted).sum())
        if score > best_score:
            best, best_score = candidate, score
    return best.tolist() if best is not None else None


def _polygon_metrics(detection: dict) -> dict | None:
    """Extraer alturas, anchos y esquinas clave desde `display_polygon`."""
    raw = detection.get('display_polygon') or []
    if len(raw) < 3:
        return None
    pts = [(float(p[0]), float(p[1])) for p in raw]
    if not all(np.isfinite(x) and np.isfinite(y) for x, y in pts):
        return None
    xs = [p[0] for p in pts]
    ys = sorted(p[1] for p in pts)
    height_px = (ys[-2] + ys[-1] - ys[0] - ys[1]) / 2.0 if len(pts) >= 4 else (ys[-1] - ys[0])
    width_px = max(xs) - min(xs)
    if height_px <= 0 or width_px <= 0:
        return None
    by_y = sorted(pts, key=lambda p: p[1])
    bottom_two = sorted(by_y[-2:], key=lambda p: p[0])
    return {
        'det': detection,
        'pts': pts,
        'center_y': sum(p[1] for p in pts) / len(pts),
        'min_y': ys[0],
        'max_y': ys[-1],
        'min_x': min(xs),
        'max_x': max(xs),
        'width_px': width_px,
        'height_px': height_px,
        'bottom_left': bottom_two[0],
        'bottom_right': bottom_two[1],
    }


def project_open_top_level(
    detections: list[dict],
    width: int,
    height: int,
    support_y: tuple[float, float] | None = None,
) -> dict | None:
    """Proyectar un polígono candidato de nivel superior usando la mediana inferior."""
    if width <= 1 or height <= 1:
        return None
    metrics = [m for m in (_polygon_metrics(d) for d in (detections or [])) if m is not None]
    if len(metrics) < 2:
        return None
    metrics.sort(key=lambda m: m['center_y'])
    top = metrics[0]
    ref_levels = metrics[1:] if len(metrics) >= 3 or support_y is not None else metrics
    median_height = float(statistics.median(m['height_px'] for m in ref_levels))
    if median_height <= 1.0:
        return None

    ul_x = top['bottom_left'][0]
    ur_x = top['bottom_right'][0]
    if ur_x <= ul_x:
        ul_x, ur_x = top['min_x'], top['max_x']
    if support_y is not None:
        yl, yr = float(support_y[0]), float(support_y[1])
    else:
        yl, yr = float(top['bottom_left'][1]), float(top['bottom_right'][1])

    full_projection = [
        [round(ul_x, 2), round(yl - median_height, 2)],
        [round(ur_x, 2), round(yr - median_height, 2)],
        [round(ur_x, 2), round(yr, 2)],
        [round(ul_x, 2), round(yl, 2)],
    ]
    clipped = any(y < 0.0 for _, y in full_projection)
    polygon = [
        [
            round(min(float(width - 1), max(0.0, x)), 2),
            round(min(float(height - 1), max(0.0, y)), 2),
        ]
        for x, y in full_projection
    ]
    return {
        'polygon': polygon,
        'full_projection': full_projection,
        'median_height': round(median_height, 2),
        'clipped': clipped,
    }


def check_open_top_shelf(detections: list[dict], width: int, height: int) -> dict | None:
    """Detectar si el nivel superior está truncado respecto a la mediana de inferiores."""
    if width <= 1 or height <= 1:
        return None
    metrics = [m for m in (_polygon_metrics(d) for d in (detections or [])) if m is not None]
    if len(metrics) < 3:
        return None
    metrics.sort(key=lambda m: m['center_y'])
    top = metrics[0]
    lowers = metrics[1:]
    median_lower_height = float(statistics.median(m['height_px'] for m in lowers))
    median_lower_width = float(statistics.median(m['width_px'] for m in lowers))
    if median_lower_height <= 1.0 or median_lower_width <= 1.0:
        return None

    is_truncated = (
        top['height_px'] < 0.50 * median_lower_height
        and top['width_px'] >= 0.70 * median_lower_width
        and top['min_y'] > 8.0
    )
    if not is_truncated:
        return None

    support = (top['bottom_left'][1], top['bottom_right'][1])
    projected = project_open_top_level(detections, width, height, support_y=support)
    if projected is None:
        return None
    top['det']['open_top_truncated'] = True
    top['det']['open_top_projected_polygon'] = projected['polygon']
    return {
        'detection_id': top['det'].get('id'),
        'top_height': round(top['height_px'], 2),
        'median_lower_height': round(median_lower_height, 2),
        'projected_polygon': projected['polygon'],
        'clipped': projected['clipped'],
    }
