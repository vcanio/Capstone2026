"""Preparación V3: lectura de CVAT, revisión por foto y exportación sin entrenar."""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from urllib.parse import quote
import uuid

import datos_modelos as datasets
import almacenamiento_datos as storage

PARTITION = 'Datos/Registros/Particiones/v3_458_20261023/particion.json'
ACTIVE_PARTITION = 'Datos/Registros/Particiones/activa_v3.json'
OUTPUT = 'Datos/Preparados/V3'
TASKS = (24, 27, 28, 31)
PREPARATION_POLICY = 'niveles_visibles_revisados_v3_20261025'
CVAT_ACTIVE_SOURCE = 'Datos/Registros/CVAT/fuente_activa_v3.json'


def cvat_source(root, reference, part):
    """Resolver una migración explícita sin reescribir particiones históricas."""
    path = root / CVAT_ACTIVE_SOURCE
    if not path.is_file():
        return None
    config = read(path)
    source_reference = config.get('partition_path')
    if source_reference != reference and not (part.get('schema_version') == 3 and part.get('base_partition_path') == source_reference):
        return None
    if config.get('partition_sha256') != digest(root / source_reference):
        raise ValueError('La partición de la fuente CVAT activa cambió.')
    plan_path = root / 'Datos/Registros/Organizacion_nombres_20261030/plan_nombres_v3.csv'
    receipt_path = root / 'Datos/Registros/Organizacion_nombres_20261030/migracion_cvat.json'
    if config.get('plan_sha256') != digest(plan_path):
        raise ValueError('Cambió el mapa de nombres CVAT activo.')
    receipt = read(receipt_path)
    if receipt.get('status') != 'verified' or receipt.get('project_id') != config.get('project_id'):
        raise ValueError('La migración CVAT activa no está verificada.')
    tasks = {entry['source_task']: entry['task_id'] for entry in receipt['tasks'] if entry['status'] == 'verified'}
    recovery_ref = config.get('task_recovery_receipt')
    if recovery_ref:
        if recovery_ref != 'Datos/Registros/CVAT/revisiones/restauracion_tarea36_20261102/recibo.json':
            raise ValueError('Recibo de restauración CVAT desconocido.')
        recovery = read(root / recovery_ref)
        if (config.get('task_recovery_sha256') != digest(root / recovery_ref)
                or recovery.get('status') != 'verified' or recovery.get('project_id') != config.get('project_id')
                or recovery.get('original_task') != 31 or recovery.get('deleted_task') != tasks.get(31)
                or recovery.get('images') != 11 or recovery.get('shapes') != 47
                or recovery.get('uploaded_hashes_verified') != 11
                or not recovery.get('annotation_geometry_attributes_verified')):
            raise ValueError('La restauración CVAT no está verificada.')
        tasks[31] = recovery['task_id']
    if {str(k): v for k, v in tasks.items()} != config.get('tasks'):
        raise ValueError('Las tareas CVAT no coinciden con la migración verificada.')
    with plan_path.open(encoding='utf-8-sig', newline='') as stream:
        plan = list(csv.DictReader(stream))
    entries = {(int(item['tarea_actual']), item['nombre_actual']): item for item in plan}
    if len(entries) != len(plan) or len(plan) != len(part['imagenes']):
        raise ValueError('El mapa de nombres CVAT tiene duplicados o cobertura incompleta.')
    for row in part['imagenes']:
        item = entries.get((row['task_id'], row['name']))
        if not item or item['sha256'] != row['sha256'] or not item['nombre_propuesto']:
            raise ValueError('El mapa de nombres no coincide con la partición V3.')
    return {'project_id': config['project_id'], 'tasks': tasks, 'entries': entries}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def partition_reference(root, reference=None):
    active = None
    if reference is None:
        pointer = root / ACTIVE_PARTITION
        active = read(pointer) if pointer.is_file() else None
        if active is not None and (not isinstance(active, dict) or not active.get('path')):
            raise ValueError('El puntero de partición activa no es válido.')
        reference = active['path'] if active is not None else PARTITION
    if not isinstance(reference, str) or not re.fullmatch(
            r'Datos/Registros/Particiones/[A-Za-z0-9_-]+/particion\.json', reference):
        raise ValueError('Referencia de partición V3 inválida.')
    if not (root / reference).resolve().is_relative_to((root / 'Datos/Registros/Particiones').resolve()):
        raise ValueError('La partición debe estar dentro de sus registros.')
    if active is not None and digest(root / reference) != active.get('sha256'):
        raise ValueError('La partición activa cambió desde su comprobación.')
    return reference


def v3_image_path(root, value):
    """Resolver las dos rutas históricas V2 dentro de sus ubicaciones V3 actuales."""
    if not isinstance(value, str):
        raise ValueError('Ruta de imagen V3 inválida.')
    for name in ('lider_express_20261016', 'visibilidad_limitada_20261019'):
        prefix = f'Datos/V2/{name}/'
        if value.startswith(prefix):
            value = f'Datos/V3/{name}/' + value[len(prefix):]
            break
    storage.relative(value)
    if not value.startswith('Datos/'):
        raise ValueError('Ruta de imagen V3 inválida.')
    path = storage.read_path(root, value)
    # read_path permits an external file only for this exact catalog reference;
    # the original logical path may be absent on a newly connected machine.
    return path


def partition(root, reference=None, _seen=None, _paths=None):
    reference = partition_reference(root, reference)
    # La cadena contiene las mismas imágenes en varias versiones. Resolver una
    # ruta una sola vez por comprobación evita repetir accesos al montaje; no
    # conserva autorizaciones ni resoluciones entre comprobaciones distintas.
    if _paths is None:
        _paths = {'data_root': (root / 'Datos').resolve(), 'images': {}}
    seen = set(_seen or ())
    if reference in seen:
        raise ValueError('La cadena de particiones contiene un ciclo.')
    seen.add(reference)
    value = read(root / reference)
    if value.get('schema_version') == 6:
        from refuerzo_ampliado_v3 import validate_partition
        return validate_partition(root, reference, value)
    if value.get('schema_version') == 5:
        from refuerzo_cierre_v3 import validate_partition
        return validate_partition(root, reference, value)
    if value.get('schema_version') == 4:
        from refuerzo_geometria_v3 import validate_partition
        return validate_partition(root, reference, value)
    rows = value['imagenes']
    families, scenes, hashes, names = {}, {}, set(), set()
    counts = Counter()
    for row in rows:
        split = row['split']
        if split not in ('train', 'val', 'test') or row['task_id'] not in TASKS:
            raise ValueError('La partición V3 contiene una asignación desconocida.')
        image_paths = _paths['images']
        if row['path'] not in image_paths:
            image_paths[row['path']] = v3_image_path(root, row['path'])
        path = image_paths[row['path']]
        if Path(row['path']).name != row['name']:
            raise ValueError('Ruta de imagen V3 inválida.')
        if row['name'] in names or row['sha256'] in hashes:
            raise ValueError('La partición V3 contiene duplicados.')
        names.add(row['name'])
        hashes.add(row['sha256'])
        for groups, key in ((families, row['familia']), (scenes, row['grupo_escena'])):
            if groups.setdefault(key, split) != split:
                raise ValueError('Hay familias o escenas repartidas entre conjuntos.')
        counts[split] += 1
    expected = {key: item['imagenes'] for key, item in value['resumen'].items()}
    expected_total = 469 if value.get('schema_version') in (2, 3) else 458
    if dict(counts) != expected or sum(counts.values()) != expected_total or counts['test'] != (0 if value.get('schema_version') == 3 else 63):
        raise ValueError('Cambió la partición fijada de 458 imágenes. Revisa sus registros.')
    if value.get('schema_version') == 3:
        base_ref = partition_reference(root, value.get('base_partition_path'))
        base = partition(root, base_ref, seen, _paths)
        train = value.get('moved_test_to_train', [])
        val = value.get('moved_test_to_val', [])
        test_groups = {r['grupo_escena'] for r in base['imagenes'] if r['split'] == 'test'}
        if (base.get('schema_version') != 2 or value.get('id') != Path(reference).parent.name
                or value.get('base_partition_sha256') != digest(root / base_ref)
                or not value.get('authorization', {}).get('text') or set(train) & set(val)
                or len(train) != len(set(train)) or len(val) != len(set(val))
                or set(train) | set(val) != test_groups or len(rows) != len(base['imagenes'])):
            raise ValueError('La redistribución de test carece de procedencia o grupos válidos.')
        for old, new in zip(base['imagenes'], rows):
            target = ('val' if old['grupo_escena'] in val else 'train') if old['split'] == 'test' else old['split']
            if new != {**old, 'split': target}:
                raise ValueError('Solo se permite reasignar grupos completos de la reserva anterior.')
        for split, summary in value['resumen'].items():
            items = [r for r in rows if r['split'] == split]
            if (summary['reales'] != sum(r['origen'] == 'real' for r in items)
                    or summary['sinteticas'] != sum(r['origen'] == 'sintetica' for r in items)
                    or summary['grupos'] != len({r['grupo_escena'] for r in items})
                    or summary['por_tarea'] != {str(k): v for k, v in sorted(Counter(r['task_id'] for r in items).items())}):
                raise ValueError('El resumen no coincide con las imágenes redistribuidas.')
        return value
    if value.get('schema_version') == 2:
        base_ref = partition_reference(root, value.get('base_partition_path'))
        base = partition(root, base_ref, seen, _paths)
        if (value.get('id') != Path(reference).parent.name
                or value.get('base_partition_sha256') != digest(root / base_ref)
                or len(base['imagenes']) != 458 or not value.get('authorization', {}).get('text')
                or value.get('moved_val_to_train') != ['l2_g17']
                or value.get('moved_train_to_val') != []):
            raise ValueError('La ampliación de V3 no conserva su procedencia y traslados autorizados.')
        for old, new in zip(base['imagenes'], rows[:458]):
            target = 'train' if old['grupo_escena'] == 'l2_g17' else old['split']
            if new != {**old, 'split': target}:
                raise ValueError('La ampliación solo admite el traslado documentado de huevos.')
        lot_path = 'Datos/V3/Refuerzo/papeles_20261025/manifest.json'
        if value.get('supplemental_manifest') != lot_path:
            raise ValueError('Lote complementario V3 no registrado.')
        lot = read(root / lot_path)
        additions = rows[458:]
        if len(additions) != 11 or len(lot['imagenes']) != 11:
            raise ValueError('La ampliación debe conservar las 11 tomas del trabajo 72.')
        registered = {i['nombre_original']: i for i in lot['imagenes']}
        for new in additions:
            item = registered.get(new['name'])
            if item is None or any(new[k] != v for k, v in {
                    'path': lot['base_archivos'] + '/' + item['archivo'],
                    'sha256': item['sha256'], 'width': item['ancho'], 'height': item['alto'],
                    'familia': item['familia'], 'task_id': 31, 'split': 'train',
                    'origen': 'real', 'grupo_escena': 'l2_g04'}.items()):
                raise ValueError('Las tomas complementarias no coinciden con su inventario.')
        if {r['name'] for r in additions} != set(registered):
            raise ValueError('La cobertura del lote complementario no coincide.')
        for split, summary in value['resumen'].items():
            items = [r for r in rows if r['split'] == split]
            if (summary['reales'] != sum(r['origen'] == 'real' for r in items)
                    or summary['sinteticas'] != sum(r['origen'] == 'sintetica' for r in items)
                    or summary['grupos'] != len({r['grupo_escena'] for r in items})):
                raise ValueError('El resumen ampliado no coincide con sus imágenes.')
        return value
    if reference != PARTITION:
        base = partition(root, PARTITION, seen, _paths)
        if (value.get('base_partition_path') != PARTITION
                or value.get('base_partition_sha256') != digest(root / PARTITION)
                or value.get('id') != Path(reference).parent.name
                or not value.get('authorization', {}).get('text')):
            raise ValueError('Falta la procedencia y autorización de la nueva partición.')
        to_train = value.get('moved_val_to_train', [])
        to_val = value.get('moved_train_to_val', [])
        if set(to_train) & set(to_val) or len(rows) != len(base['imagenes']):
            raise ValueError('Los cambios de grupos no son válidos.')
        known = {r['grupo_escena'] for r in base['imagenes']}
        if not set(to_train + to_val) <= known:
            raise ValueError('La nueva partición referencia grupos desconocidos.')
        for old, new in zip(base['imagenes'], rows):
            scene = old['grupo_escena']
            target = 'train' if scene in to_train else 'val' if scene in to_val else old['split']
            if ((scene in to_train and old['split'] != 'val')
                    or (scene in to_val and old['split'] != 'train')
                    or new != {**old, 'split': target}):
                raise ValueError('Solo se permiten los traslados documentados de grupos completos; test se conserva.')
        hard = value.get('hard_examples', [])
        if len(hard) != len(set(hard)) or not set(hard) <= {r['name'] for r in rows if r['split'] == 'train'}:
            raise ValueError('Los casos de refuerzo deben pertenecer íntegramente a entrenamiento.')
        for split, summary in value['resumen'].items():
            items = [r for r in rows if r['split'] == split]
            if (summary['reales'] != sum(r['origen'] == 'real' for r in items)
                    or summary['sinteticas'] != sum(r['origen'] == 'sintetica' for r in items)
                    or summary['grupos'] != len({r['grupo_escena'] for r in items})):
                raise ValueError('El resumen de la nueva partición no coincide con sus imágenes.')
        return value
    if expected != {'train': 327, 'val': 68, 'test': 63}:
        raise ValueError('Cambió la partición histórica de 458 imágenes.')
    if (value.get('id') != 'v3_458_20261023'
            or read(root / 'Datos/Registros/CVAT/criterio_v3.json')['images'] != rows
            or digest((root / PARTITION).parent / 'grupos_escena.json') != value['grupos_sha256']
            or digest((root / PARTITION).parent / 'lider2_grupos.json') != value['config_lider2_sha256']):
        raise ValueError('La partición y sus registros de escenas no están sincronizados. Ejecuta su verificador.')
    return value


def status(root):
    part = partition(root)
    latest = root / OUTPUT / 'ultima.json'
    current = read(latest) if latest.is_file() else None
    return {'partition_id': part['id'], 'summary': part['resumen'],
            'preparation_enabled': True, 'training_enabled': False, 'current': current,
            'final_test': final_test_catalog(part)}


def final_test_catalog(part):
    """Mostrar la reserva en su sección, sin incluirla en las fotos de desarrollo."""
    photos = [{'id': row['path'], 'name': row['name'], 'width': row['width'], 'height': row['height'],
               'origin': row['origen'], 'scene': row['grupo_escena'], 'split': 'test',
               'url': '/api/v3/final-image?photo=' + quote(row['name'])}
              for row in part['imagenes'] if row['split'] == 'test']
    return {'images': photos, 'counts': dict(Counter(i['origin'] for i in photos)),
            'analysis_enabled': False, 'partition_id': part['id']}


def final_image_path(root, name):
    photo = next((row for row in partition(root)['imagenes']
                  if row['split'] == 'test' and row['name'] == name), None)
    if photo is None:
        raise ValueError('La foto no pertenece a la prueba final V3.')
    path = v3_image_path(root, photo['path'])
    if not path.is_file() or digest(path) != photo['sha256']:
        raise ValueError('La foto reservada está ausente o cambió. Revisa su inventario.')
    return path


def catalog_status(root):
    """Un fallo de V3 no debe bloquear las versiones históricas del panel."""
    if not (root / PARTITION).is_file():
        return None
    try:
        return status(root)
    except (ValueError, OSError, KeyError, TypeError) as error:
        return {'preparation_enabled': False, 'training_enabled': False, 'current': None,
                'error': 'Revisa los registros V3: ' + str(error)}


def version_path(root, version):
    if not isinstance(version, str) or not re.fullmatch(r'v3_\d{8}_\d{6}_[a-f0-9]{8}', version):
        raise ValueError('Copia V3 inválida.')
    folder = root / OUTPUT / version
    if not (folder / 'informe.json').is_file():
        raise ValueError('La copia V3 ya no está disponible. Vuelve a consultar CVAT.')
    return folder


def report(root, version=None):
    latest = status(root)['current']
    if version is None:
        if latest is None:
            return None
        version = latest['id']
    return read(version_path(root, version) / 'informe.json')


def polygon_ok(points, width, height):
    from shapely.geometry import Polygon
    if (not isinstance(points, list) or len(points) < 6 or len(points) % 2 or
            any(type(p) not in (int, float) or not math.isfinite(p) for p in points)):
        return False
    pairs = list(zip(points[::2], points[1::2]))
    if any(not -1e-9 <= x <= width + 1e-9 or not -1e-9 <= y <= height + 1e-9 for x, y in pairs):
        return False
    poly = Polygon(pairs)
    return poly.is_valid and poly.area > 1


def normalized_points(points, width, height):
    """Normalizar solo residuos de coma flotante de hasta 1e-9 píxeles en el borde."""
    result = []
    for idx, value in enumerate(points):
        limit = width if idx % 2 == 0 else height
        if not -1e-9 <= value <= limit + 1e-9:
            raise ValueError('Coordenada fuera del encuadre.')
        result.append(min(limit, max(0.0, value)) / limit)
    return result


def analyze(part, snapshot):
    """Conservar todos los niveles; apartar la foto entera si alguno no es exportable."""
    labels = {label['id']: label for label in snapshot['labels']}
    by_task = {item.get('partition_task_id', item['task']['id']): item for item in snapshot['tasks']}
    images = []
    for row in part['imagenes']:
        task = by_task[row['task_id']]
        frame = task['frames_by_name'][row['name']]
        annotation = task['annotations']
        issues, warnings, shapes = [], [], []
        def issue(code, detail, shape_id=None):
            issues.append({'code': code, 'detail': detail, 'shape_id': shape_id})
        if row.get('preparation_exclusion'):
            issue('exclusion_documentada', row['preparation_exclusion'])
        if frame in (task.get('meta', {}).get('deleted_frames') or []):
            issue('excluida_cvat', 'Foto desactivada en CVAT. Se conserva su partición y se excluye de la exportación.')
        if annotation.get('tracks') or annotation.get('intervals'):
            issue('geometria_temporal', 'Convertir tracks o intervalos a polígonos independientes antes de preparar.')
        for tag in annotation.get('tags', []):
            if tag.get('frame') == frame:
                issue('revision_foto', 'La foto tiene una marca de revisión en CVAT.')
        for shape in annotation.get('shapes', []):
            if shape.get('frame') != frame:
                continue
            label = labels.get(shape.get('label_id'), {})
            specs = {a['id']: a['name'] for a in label.get('attributes', [])}
            attrs = {specs.get(a['spec_id']): a['value'] for a in shape.get('attributes', [])}
            delim = attrs.get('delimitacion', 'pendiente')
            item = {'id': shape.get('id'), 'points': shape.get('points', []),
                    'delimitacion': delim, 'occluded': shape.get('occluded', False)}
            shapes.append(item)
            if label.get('name') != 'Nivel' or shape.get('type') != 'polygon' or shape.get('outside') or shape.get('elements'):
                issue('tipo_incompatible', 'Solo se admite la clase Nivel con polígonos independientes.', item['id'])
            if delim == 'parcial':
                warnings.append({'code': 'delimitacion_parcial', 'shape_id': item['id'],
                                 'detail': 'Nivel parcial: confirma que la región visible está bien delimitada. Puede exportarse tras revisión; no representa el nivel completo.'})
            elif delim != 'completa':
                issue('delimitacion_' + (delim if delim in ('pendiente', 'parcial') else 'invalida'),
                      'Revisar el perímetro en CVAT; no se aprueba automáticamente.', item['id'])
            if item['occluded']:
                warnings.append({'code': 'oclusion', 'shape_id': item['id'],
                                 'detail': 'Nivel ocluido: confirma que el perímetro es recuperable. El contenido oculto no permite deducir la ocupación total.'})
            if not polygon_ok(item['points'], row['width'], row['height']):
                issue('geometria_invalida', 'Polígono inválido o fuera del encuadre; corregir en CVAT.', item['id'])
            elif any(v < 0 or v > (row['width'] if idx % 2 == 0 else row['height']) for idx, v in enumerate(item['points'])):
                warnings.append({'code': 'precision_numerica_borde', 'shape_id': item['id'],
                                 'detail': 'Residuo numérico de hasta 1e-9 píxeles: CVAT y snapshot intactos; solo la etiqueta YOLO se limita al borde exacto.'})
        if not shapes:
            issue('sin_niveles', 'No hay niveles anotados; no se usará como foto negativa.')
        job = next((j for j in task['jobs'] if j['start_frame'] <= frame <= j['stop_frame']), None)
        if job is None:
            raise ValueError(f"No se encontró el trabajo de {row['name']}.")
        frame_info = task.get('meta', {}).get('frames', [])
        images.append({**row, 'cvat_task_id': task['task']['id'],
                       'cvat_name': frame_info[frame]['name'] if frame < len(frame_info) else row['name'],
                       'frame': frame, 'job_id': job['id'], 'shapes': shapes,
                       'issues': issues, 'warnings': warnings, 'eligible': not issues})
    reasons = Counter(i['code'] for image in images for i in image['issues'])
    return {'images': images, 'image_count': len(images),
            'polygon_count': sum(len(i['shapes']) for i in images),
            'eligible_images': sum(i['eligible'] for i in images),
            'blocked_images': sum(not i['eligible'] for i in images),
            'warning_images': sum(bool(i['warnings']) for i in images),
            'partial_polygons': sum(s['delimitacion'] == 'parcial' for i in images for s in i['shapes']),
            'occluded_polygons': sum(bool(s['occluded']) for i in images for s in i['shapes']),
            'issues': dict(reasons), 'policy_version': PREPARATION_POLICY, 'training_enabled': False}


def prepare(root, client=None, partition_reference_path=None):
    reference = partition_reference(root, partition_reference_path)
    part = partition(root, reference)
    if part.get('schema_version') == 6:
        from refuerzo_ampliado_v3 import prepare_partition
        return prepare_partition(root, reference, part, client)
    if part.get('schema_version') == 5:
        from refuerzo_cierre_v3 import prepare_partition
        return prepare_partition(root, reference, part, client)
    if part.get('schema_version') == 4:
        from refuerzo_geometria_v3 import prepare_partition
        return prepare_partition(root, reference, part, client)
    # Verificar los bytes actuales, sin aceptar rutas ni repartos del navegador.
    for row in part['imagenes']:
        path = v3_image_path(root, row['path'])
        if not path.is_file() or digest(path) != row['sha256']:
            raise ValueError(f"Imagen ausente o modificada: {row['name']}. Revisa el inventario.")
    client = client or datasets.CvatReader()
    source = cvat_source(root, reference, part)
    project_id = source['project_id'] if source else 8
    snapshot = {'labels': client.listing(f'/labels?project_id={project_id}'), 'tasks': []}
    for task_id in sorted({row['task_id'] for row in part['imagenes']}):
        actual_id = source['tasks'][task_id] if source else task_id
        task = client.request(f'/tasks/{actual_id}')
        if task.get('project_id') != project_id:
            raise ValueError('La tarea ya no pertenece al proyecto V3 esperado.')
        meta = client.request(f'/tasks/{actual_id}/data/meta')
        rows = {row['name']: row for row in part['imagenes'] if row['task_id'] == task_id}
        actual_names = {name: source['entries'][(task_id, name)]['nombre_propuesto'] if source else name for name in rows}
        if len(set(actual_names.values())) != len(rows):
            raise ValueError(f'El mapa de nombres de la tarea {task_id} contiene duplicados.')
        rows_by_actual = {actual_names[name]: row for name, row in rows.items()}
        frames = meta['frames']
        if (meta.get('start_frame', 0) != 0 or meta.get('frame_filter', '') not in ('', 'step=1')
                or task.get('size') != len(rows)):
            raise ValueError(f'Cambió la cobertura de la tarea {task_id}. Revisa la partición antes de preparar.')
        if any(type(frame) is not int or not 0 <= frame < len(rows) for frame in (meta.get('deleted_frames') or [])):
            raise ValueError(f'La tarea {task_id} tiene exclusiones fuera de su cobertura.')
        if len(frames) != len(rows) or {f['name'] for f in frames} != set(rows_by_actual):
            raise ValueError(f'Las fotos de la tarea {task_id} no coinciden con la partición.')
        for f in frames:
            if (f['width'], f['height']) != (rows_by_actual[f['name']]['width'], rows_by_actual[f['name']]['height']):
                raise ValueError(f"Cambió la orientación o tamaño de {f['name']}.")
        annotations = client.request(f'/tasks/{actual_id}/annotations')
        if any(type(s.get('frame')) is not int or not 0 <= s['frame'] < len(frames)
               for s in annotations.get('shapes', []) + annotations.get('tags', [])):
            raise ValueError(f'Hay anotaciones fuera de las fotos de la tarea {task_id}.')
        actual_frames = {f['name']: index for index, f in enumerate(frames)}
        snapshot['tasks'].append({'task': task, 'partition_task_id': task_id, 'meta': meta, 'annotations': annotations,
                                  'jobs': datasets.annotation_jobs(client, actual_id),
                                  'frames_by_name': {name: actual_frames[actual] for name, actual in actual_names.items()}})
    result = analyze(part, snapshot)
    stamp = datetime.now(timezone.utc)
    version = 'v3_' + stamp.strftime('%Y%m%d_%H%M%S_') + uuid.uuid4().hex[:8]
    result.update(id=version, created_at=stamp.isoformat(), partition_id=part['id'],
                  partition_path=reference, partition_sha256=digest(root / reference), summary=part['resumen'],
                  partition_note=part.get('evaluation_note', ''))
    folder = root / OUTPUT / version
    folder.mkdir(parents=True)
    write(folder / 'snapshot_cvat.json', snapshot)
    write(folder / 'particion.json', part)
    write(folder / 'informe.json', result)
    latest = {key: result[key] for key in ('id', 'created_at', 'image_count', 'polygon_count', 'eligible_images', 'blocked_images')}
    temporary = folder.parent / 'ultima.tmp'
    write(temporary, latest)
    temporary.replace(folder.parent / 'ultima.json')
    return result


def export(root, config):
    """Exportar regiones visibles revisadas; test siempre fuera del YAML de desarrollo."""
    author = config.get('author')
    if config.get('reviewed') is not True or not isinstance(author, str) or not 2 <= len(author.strip()) <= 100:
        raise ValueError('Registra quién revisó las fotos exportables y confirma su revisión visual.')
    folder = version_path(root, config.get('id'))
    value = read(folder / 'informe.json')
    if value.get('policy_version') != PREPARATION_POLICY:
        raise ValueError('Esta copia usa la política anterior. Vuelve a traer las anotaciones V3 y revisa las regiones visibles antes de exportar.')
    reference = partition_reference(root, value.get('partition_path', PARTITION))
    if reference != PARTITION:
        partition(root, reference)
    if digest(root / reference) != value['partition_sha256']:
        raise ValueError('La partición cambió desde esta consulta. Vuelve a preparar los datos.')
    eligible = [i for i in value['images'] if i['eligible']]
    for split in ('train', 'val'):
        if not any(i['split'] == split and (split == 'train' or i['origen'] == 'real') for i in eligible):
            raise ValueError('Faltan fotos revisadas de entrenamiento o validación real. Corrige CVAT y vuelve a consultar.')
    # La exportación se refiere a la copia fechada, nunca se anuncia como lectura en vivo.
    for row in eligible:
        path = v3_image_path(root, row['path'])
        if not path.is_file() or digest(path) != row['sha256']:
            raise ValueError(f"Cambió la imagen {row['name']}. Vuelve a preparar.")
    out = folder / ('exportacion_' + uuid.uuid4().hex[:8])
    out.mkdir()
    splits = defaultdict(list)
    try:
        for image in eligible:
            split = image['split']
            subset = split if split == 'train' else split + ('_real' if image['origen'] == 'real' else '_sintetica')
            name = image['name']
            target = out / 'images' / subset / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(v3_image_path(root, image['path']), target)
            label = out / 'labels' / subset / (Path(name).stem + '.txt')
            label.parent.mkdir(parents=True, exist_ok=True)
            lines = []
            for shape in image['shapes']:
                p = shape['points']
                coords = normalized_points(p, image['width'], image['height'])
                lines.append('0 ' + ' '.join(format(v, '.12g') for v in coords))
            label.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            splits[subset].append('./images/' + subset + '/' + name)
        for subset, paths in splits.items():
            (out / (subset + '.txt')).write_text('\n'.join(paths) + '\n', encoding='utf-8')
        # El destino se fija en este equipo; al trasladarlo se debe ajustar path.
        (out / 'desarrollo.yaml').write_text('path: ' + json.dumps(out.resolve().as_posix()) + '\ntrain: train.txt\nval: val_real.txt\nnames:\n  0: Nivel\n', encoding='utf-8')
        manifest = {'source_version': value['id'], 'created_at': datetime.now(timezone.utc).isoformat(),
                    'author': author.strip(), 'reviewed': True, 'training_enabled': False,
                    'policy_version': value['policy_version'], 'reviewed_visible_regions': True,
                    'partition_id': value['partition_id'], 'partition_path': reference, 'partition_sha256': value['partition_sha256'],
                    'partition_note': value.get('partition_note', ''),
                    'counts': {key: len(items) for key, items in splits.items()},
                    'included': [{**{key: i[key] for key in ('name', 'split', 'origen', 'familia', 'grupo_escena', 'sha256')},
                                  'shapes': [{key: s[key] for key in ('id', 'delimitacion', 'occluded')} for s in i['shapes']],
                                  'warnings': i.get('warnings', [])} for i in eligible],
                    'excluded': [{'name': i['name'], 'split': i['split'], 'issues': i['issues']} for i in value['images'] if not i['eligible']],
                    'policy': 'Admitir polígonos completos y regiones visibles parciales tras revisión humana explícita, conservando delimitación y oclusión en el manifiesto. Excluir la foto entera ante pendientes, revisión de foto, desactivación en CVAT o geometría incompatible. Test separado del desarrollo. La ocupación visible V3 sigue pendiente de integración; no extrapolar al nivel completo.'}
        write(out / 'manifest.json', manifest)
    except Exception:
        # Conservar una exportación fallida para diagnóstico, sin declararla completa.
        (out / 'INCOMPLETA.txt').write_text('Exportación incompleta. No usar para entrenar.', encoding='utf-8')
        raise
    source = out.relative_to(root).as_posix()
    selection = None
    draft = root / 'Datos/Preparados/V3/Selecciones/segmentacion_v3_sin_tarea33_20261102/revision_pendiente.json'
    if draft.is_file() and read(draft).get('source_report') == (folder / 'informe.json').relative_to(root).as_posix():
        import selecciones_v3
        selection = selecciones_v3.create_no_tapadas(root, source, manifest, eligible)
    return {'path': source, 'counts': manifest['counts'],
            'excluded': len(manifest['excluded']), 'training_enabled': False, 'selection': selection}
