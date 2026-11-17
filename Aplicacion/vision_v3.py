"""Alcance de las máscaras y lectura experimental de V3."""
from geometria_niveles import check_open_top_shelf


def apply_scope(detections, width, height):
    """Añadir alcance y avisos a cada detección, modificando la lista recibida.

    width y height son las dimensiones de la foto en píxeles. near_frame
    conserva el contacto de la máscara original con el encuadre, aunque el
    dibujo haya sido ajustado a cuatro lados. Un recorte exige revisión.
    """
    check_open_top_shelf(detections, width, height)
    for detection in detections:
        points = detection['display_polygon']
        near_frame = detection.get('near_frame', any(
            x <= 2 or y <= 2 or x >= width - 3 or y >= height - 3 for x, y in points))
        open_top_truncated = bool(detection.get('open_top_truncated'))
        detection['scope'] = 'Solo zona visible' if near_frame else 'Área detectada · señal experimental'
        if not near_frame and detection.get('occupancy', {}).get('interpretation_policy') == 'front_coverage_v1':
            detection['scope'] = 'Cobertura del frente · experimental'
        if not near_frame and detection.get('occupancy', {}).get('interpretation_policy') == 'body_fill_gap_v1':
            detection['scope'] = 'Disponibilidad visual · Línea A'
        if not near_frame and detection.get('occupancy', {}).get('interpretation_policy') == 'basal_visible_width_v1':
            detection['scope'] = 'Frente observable · Basal experimental'
        if near_frame:
            detection['notice'] = 'Contorno junto al encuadre: revisa lo que queda fuera.'
        elif open_top_truncated:
            open_top_msg = 'Nivel superior con altura reducida sin tope físico claro: revisa posible nivel superior abierto.'
            existing_notice = detection.get('occupancy', {}).get('review_reason') or ''
            detection['notice'] = f'{existing_notice} {open_top_msg}'.strip() if existing_notice else open_top_msg
        else:
            detection['notice'] = detection.get('occupancy', {}).get('review_reason') or ''
        reading = detection.get('occupancy_estimate')
        if reading and near_frame:
            reading = {**reading, 'state': 'revisar', 'label': 'Revisar · zona visible', 'color': '#a16207'}
        elif reading and open_top_truncated and reading.get('state') == 'suficiente':
            reading = {**reading, 'state': 'revisar', 'label': 'Revisar · nivel superior abierto', 'color': '#a16207'}
        elif reading and reading['pct'] is None:
            reading = {**reading, 'state': 'revisar',
                       'label': reading['label'] if reading.get('state') == 'revisar' else 'Revisar · sin medición',
                       'color': '#a16207'}
        if reading:
            detection['occupancy_estimate'] = reading
