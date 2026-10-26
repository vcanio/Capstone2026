"""Alcance de V3: visibilidad declarada, máscaras originales y lectura experimental."""
VISIBILITY = ('clear', 'partial', 'occluded', 'person')


def visibility_check(value):
    if value not in VISIBILITY:
        raise ValueError('Indica si la góndola está completa, recortada o tapada antes de analizar.')
    return value


def apply_scope(detections, visibility, width, height):
    """No deducir completitud u oclusión de una clase que solo localiza niveles."""
    for detection in detections:
        points = detection['display_polygon']
        near_frame = any(x <= 2 or y <= 2 or x >= width - 3 or y >= height - 3 for x, y in points)
        partial = visibility == 'partial' or near_frame
        detection['scope'] = 'Visibilidad insuficiente' if visibility == 'occluded' else 'Solo zona visible' if partial else 'Área detectada · visibilidad confirmada'
        detection['notice'] = ('Objeto delante: toma otra foto sin obstáculos.' if visibility == 'occluded' else
                               'Contorno junto al encuadre: revisa lo que queda fuera.' if near_frame else
                               'Foto recortada: revisa la parte no visible.' if partial else
                               detection.get('occupancy', {}).get('review_reason') or '')
        reading = detection.get('occupancy_estimate')
        if visibility == 'occluded':
            reading = {'pct': None, 'state': 'revisar', 'label': 'Revisar · objeto delante', 'color': '#a16207'}
        elif reading and partial:
            reading = {**reading, 'state': 'revisar', 'label': 'Revisar · zona visible', 'color': '#a16207'}
        elif reading and reading['pct'] is None:
            reading = {**reading, 'state': 'revisar',
                       'label': reading['label'] if reading.get('state') == 'revisar' else 'Revisar · sin medición',
                       'color': '#a16207'}
        if reading:
            detection['occupancy_estimate'] = reading


def person_result(image, model_id, method):
    return {'image': image, 'model': model_id, 'device': 'Sin inferencia', 'seconds': 0,
            'detections': [], 'counts': {}, 'width': image.width, 'height': image.height,
            'method': method, 'geometry_only': True, 'visibility': 'person',
            'visibility_source': 'user', 'photo_status': 'gondola_tapada',
            'message': 'Góndola tapada. Toma otra foto sin personas delante.'}
