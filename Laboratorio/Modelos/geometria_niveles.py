"""Ajuste visual de niveles a cuatro lados; no modifica las máscaras de YOLO."""
import cv2
import numpy as np


def _valid(points):
    return (np.isfinite(points).all() and cv2.isContourConvex(points.astype('float32'))
            and abs(cv2.contourArea(points.astype('float32'))) > 1)


def _refine(contour, quad):
    """Ajustar rectas robustas a los cuatro bordes, ignorando salientes locales."""
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
