"""Alcance de las máscaras y lectura experimental de V3."""

def apply_scope(detections, width, height):
    """Añadir alcance y avisos a cada detección, modificando la lista recibida.

    width y height son las dimensiones de la foto en píxeles. near_frame
    conserva el contacto de la máscara original con el encuadre, aunque el
    dibujo haya sido ajustado a cuatro lados. Un recorte exige revisión.
    """
    for detection in detections:
        points = detection['display_polygon']
        near_frame = detection.get('near_frame', any(
            x <= 2 or y <= 2 or x >= width - 3 or y >= height - 3 for x, y in points))
        detection['scope'] = 'Solo zona visible' if near_frame else 'Área detectada · señal experimental'
        if not near_frame and detection.get('occupancy', {}).get('interpretation_policy') == 'front_coverage_v1':
            detection['scope'] = 'Cobertura del frente · experimental'
        detection['notice'] = ('Contorno junto al encuadre: revisa lo que queda fuera.' if near_frame else
                               detection.get('occupancy', {}).get('review_reason') or '')
        reading = detection.get('occupancy_estimate')
        if reading and near_frame:
            reading = {**reading, 'state': 'revisar', 'label': 'Revisar · zona visible', 'color': '#a16207'}
        elif reading and reading['pct'] is None:
            reading = {**reading, 'state': 'revisar',
                       'label': reading['label'] if reading.get('state') == 'revisar' else 'Revisar · sin medición',
                       'color': '#a16207'}
        if reading:
            detection['occupancy_estimate'] = reading
