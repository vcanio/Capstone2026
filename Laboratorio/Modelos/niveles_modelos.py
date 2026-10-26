"""Criterio v1: exportar niveles con estado, sin dependencias de módulos."""
import csv
import hashlib
import math
from collections import Counter
from pathlib import Path

STATES = ('vacio', 'baja_disponibilidad', 'suficiente', 'no_evaluable')
CLASS_NAMES = ['Nivel_' + state for state in STATES]
CRITERION = {'version': 'disponibilidad_visual_nivel_v1', 'threshold': 0.30,
             'measure': 'presencia de producto por ancho útil evaluable',
             'threshold_validated': False, 'non_evaluable_alert': False}

STATE_LABELS = {'vacio': 'Vacío', 'baja_disponibilidad': 'Baja disponibilidad',
                'reponer': 'Reponer', 'suficiente': 'Suficiente', 'no_evaluable': 'No evaluable'}
STATE_COLORS = dict(zip(STATES, ('#dc2626', '#f59e0b', '#16a34a', '#64748b')), reponer='#dc2626')
ALERT_STATES = {'vacio', 'baja_disponibilidad', 'reponer'}


def model_states(names):
    names = list(names.values()) if isinstance(names, dict) else list(names)
    states = tuple(name.removeprefix('Nivel_') for name in names)
    if names != ['Nivel_' + state for state in states] or set(states) not in (
            set(STATES), {'reponer', 'suficiente'}, {'reponer', 'suficiente', 'no_evaluable'}):
        return None
    return states


def inspect_levels(snapshot, validation_ids, *, states=STATES, criterion=CRITERION, partition_pending=False,
                   fixed_splits=None):
    from PIL import Image, ImageOps
    from shapely.geometry import Polygon
    from shapely.validation import explain_validity
    import datos_modelos as datasets
    inventory, packaged = datasets.snapshot_inventory(snapshot)
    if not isinstance(validation_ids, list) or (not validation_ids and not packaged and not partition_pending) or any(not isinstance(v, str) for v in validation_ids):
        raise ValueError('Indica al menos una foto de validación de desarrollo.')
    reserve = datasets.read(datasets.ROOT / 'Datos/Registros/reserva_evaluacion.json')
    frames = snapshot['frames']
    ids = [Path(f['name']).stem for f in frames]
    if not frames or len(ids) != len(set(ids)):
        raise ValueError('No se pueden mezclar fotos repetidas en una copia.')
    if set(ids) - inventory.keys() or set(validation_ids) - set(ids):
        raise ValueError('Selecciona fotos de validación que estén en estos trabajos y en el inventario interno.')
    groups = {inventory[i]['grupo_escena'] for i in validation_ids}
    labels = {l['id']: l for l in snapshot['labels']}
    if any(l['name'] != 'Nivel' or not any(a['name'] == 'estado' for a in l['attributes']) for l in labels.values()):
        raise ValueError('Se requieren polígonos Nivel con el atributo estado del criterio seleccionado.')
    if partition_pending and any(set(a.get('values', [])) != set(states)
                                 for l in labels.values() for a in l['attributes'] if a['name'] == 'estado'):
        raise ValueError('El proyecto 7 requiere exactamente los estados reponer, suficiente y no_evaluable.')
    if snapshot['annotations'].get('tracks') or snapshot['annotations'].get('tags'):
        raise ValueError('Se requieren polígonos de imágenes, sin tracks ni tags.')
    by_frame = {i: [] for i in range(len(frames))}
    for s in snapshot['annotations']['shapes']:
        if type(s['frame']) is not int or s['frame'] not in by_frame:
            raise ValueError('Índice de anotación inválido.')
        by_frame[s['frame']].append(s)
    issues, images, rows, seen = [], [], {}, set()
    counts = Counter()
    split_counts = {split: Counter() for split in ('train', 'val')}
    def issue(iid, s, message, blocking=True):
        issues.append({'foto': iid, 'shape_id': s.get('id'), 'job_id': s.get('imported_job_id'),
            'problema': message, 'clase': 'Nivel', 'categoria': 'niveles',
            'bloquea_entrenamiento': blocking, 'bloquea_modulos': False})
    for i, frame in enumerate(frames):
        iid = ids[i]; inv = inventory[iid]
        if iid in reserve['image_ids'] or inv['grupo_escena'] in reserve['groups']:
            raise ValueError('El trabajo contiene fotos o escenas reservadas para evaluación final.')
        source = datasets.safe_image_path(inv, inventory)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != inv['sha256'] or digest in seen:
            raise ValueError('Original modificado o foto duplicada en esta copia.')
        seen.add(digest)
        with Image.open(source) as im:
            oriented_size = (im.height, im.width) if im.getexif().get(274, 1) in (5, 6, 7, 8) else im.size
            if oriented_size != (frame['width'], frame['height']):
                raise ValueError(f'Dimensiones diferentes de CVAT: {iid}.')
        split = fixed_splits[iid] if fixed_splits is not None else 'pending' if partition_pending else inv['split'] if packaged else 'val' if inv['grupo_escena'] in groups else 'train'
        split_counts.setdefault(split, Counter())
        image_counts, exported, polys = Counter(), [], set()
        for s in by_frame[i]:
            label = labels.get(s['label_id'])
            if not label:
                raise ValueError('Etiqueta desconocida en la copia.')
            names = {a['id']: a['name'] for a in label['attributes']}
            attrs = {a['name']: a.get('default_value', '') for a in label['attributes']}
            if any(a['spec_id'] not in names for a in s['attributes']):
                raise ValueError('Atributo desconocido; vuelve a importar el esquema completo.')
            attrs.update({names[a['spec_id']]: a['value'] for a in s['attributes']})
            state = attrs.get('estado', 'pendiente')
            counts[state] += 1; split_counts[split][state] += 1; image_counts[state] += 1
            if state not in states:
                issue(iid, s, 'Estado pendiente o ajeno al criterio seleccionado: ' + state)
            pts = s.get('points', [])
            good = (s['type'] == 'polygon' and not s.get('outside') and not s.get('elements') and
                    len(pts) >= 6 and not len(pts) % 2 and all(type(v) in (int, float) and math.isfinite(v) for v in pts))
            poly = Polygon(zip(pts[::2], pts[1::2])) if good else None
            if not good or not poly.is_valid or poly.area <= 1:
                issue(iid, s, 'Polígono inválido: ' + (explain_validity(poly) if poly else 'tipo/puntos'))
                good = False
            elif any(x < -1e-6 or x > frame['width'] + 1e-6 or y < -1e-6 or y > frame['height'] + 1e-6
                     for x, y in zip(pts[::2], pts[1::2])):
                issue(iid, s, 'Puntos fuera del encuadre'); good = False
            if good:
                key = poly.normalize().wkb_hex
                if key in polys:
                    issue(iid, s, 'Polígono de nivel duplicado')
                polys.add(key)
            if good and state in states:
                exported.append(str(states.index(state)) + ' ' + ' '.join(f'{v:.8f}' for x, y in
                    zip(pts[::2], pts[1::2]) for v in (min(1, max(0, x/frame['width'])), min(1, max(0, y/frame['height'])))))
        if not by_frame[i]:
            issue(iid, {}, 'Foto sin niveles: revisa que el trabajo esté completo')
        images.append({'imagen': iid + source.suffix, 'imagen_id': iid, 'archivo': inv['archivo'],
            'grupo_escena': inv['grupo_escena'], 'sha256': digest, 'split': split,
            'modulos': 0, 'niveles': len(by_frame[i]), 'niveles_solo_revision': 0,
            'estados': dict(image_counts)})
        rows[iid] = exported
    if not packaged and not partition_pending and not any(i['split'] == 'train' for i in images):
        raise ValueError('Debe quedar una escena de entrenamiento separada de validación.')
    warnings = []
    if packaged:
        for split, name in (('train', 'entrenamiento'), ('val', 'validación')):
            if not any(image['split'] == split for image in images):
                issue('', {}, f'El lote no contiene fotos de {name}; conserva ambas particiones antes de entrenar.')
        warnings.append('Partición fija del paquete: validación real, sintéticas solo para entrenamiento. La sincronización no aprueba las anotaciones.')
    if fixed_splits is not None:
        warnings.append('Etapa base: reponer y suficiente. No evaluable se incorpora en la etapa de visibilidad. Solo train y val se exportan; diagnóstico sintético y reserva final quedan fuera.')
        warnings.append('Cobertura real reducida de reponer: 2 niveles en entrenamiento, 1 en validación y 1 en reserva. Las métricas sintéticas se informan por separado.')
    if partition_pending:
        issue('', {}, 'Líder Express: falta revisar y congelar familias, grupos de escena y particiones de entrenamiento, validación y evaluación. La importación permite revisar anotaciones; no habilita el entrenamiento.')
    for state in (() if partition_pending else states):
        if not split_counts['train'][state]:
            issue('', {}, f'Sin ejemplos de {state} en entrenamiento; cambia la partición o agrega ejemplos.')
        if not split_counts['val'][state]:
            warnings.append(f'Sin {state} en validación: no se podrá medir esa clase.')
    critical = f"{counts['reponer']} niveles reponer" if 'reponer' in states else f"{counts['vacio']} vacíos y {counts['baja_disponibilidad']} bajos"
    warnings.append(f"Casos críticos: {critical}. "
                    'Revisa recall por estado y falsas alertas; muchos niveles suficientes pueden ocultar errores críticos.')
    criterion = {**criterion, 'guide': 'v1.3', 'export_mode': 'full_image'} if packaged else criterion
    return {'scope': 'Nivel_estados', 'criterion': criterion, 'imagenes': images, 'incidencias': issues,
            **({'package': 'Equilibrado_v1_20261013'} if packaged else {}),
            **({'partition_pending': True, 'lot': 'lider_express_20261016'} if partition_pending else {}),
            'bloqueos_entrenamiento': sum(i['bloquea_entrenamiento'] for i in issues), 'bloqueos_modulos': 0,
            'avisos_atributos': 0, 'avisos_niveles': 0, 'estados': dict(counts),
            'estados_por_split': {k: dict(v) for k, v in split_counts.items()},
            'advertencias': warnings, 'clases': ['Nivel_' + state for state in states]}, rows
