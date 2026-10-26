"""Importación de CVAT en lectura, revisión y versiones de módulos para el panel."""
import copy
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid
from rutas_datos import current_image_path, current_inventory_path

ROOT = Path(__file__).resolve().parents[2]
VERSIONS = ROOT / 'Datos/Registros/Versiones_modelos'
CVAT = os.environ.get('CVAT_URL', 'http://localhost:8082/api').rstrip('/')
PROJECT_SCOPES = {4: 'Modulo', 6: 'Nivel_estados', 7: 'Nivel_estados'}
LIDER_EXPRESS = 'Datos/V2/lider_express_20261016'
V2_STATES = ('reponer', 'suficiente', 'no_evaluable')
V2_CRITERION = 'disponibilidad_visual_nivel_v2_reponer'


def project_scope(task):
    scope = PROJECT_SCOPES.get(task.get('project_id'))
    if not scope or (task.get('project_id') == 7 and task.get('id') != 19):
        raise ValueError('La tarea no está incorporada a los proyectos internos del laboratorio.')
    return scope


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


class CvatReader:
    def __init__(self):
        if os.environ.get('CVAT_ENABLED', 'true').lower() in ('false', '0', 'no'):
            raise ValueError('CVAT está deshabilitado. Inicia el panel con -ConCvat y configura tu acceso para traer anotaciones.')
        access_path = Path(os.environ.get('CVAT_ACCESS_FILE') or
                           ROOT / 'Infraestructura/CVAT/acceso_local.json')
        if not access_path.is_file():
            raise ValueError('Falta tu configuración de CVAT. Copia acceso_cvat.example.json a un archivo privado y configura CVAT_ACCESS_FILE.')
        access = read(access_path)
        if not all(isinstance(access.get(k), str) and access[k] for k in ('username', 'password')):
            raise ValueError('Completa username y password en tu archivo privado de acceso a CVAT.')
        login = self.request('/auth/login', payload={k: access[k] for k in ('username', 'password')})
        self.token = login['key']

    def request(self, route, payload=None):
        headers = {'Content-Type': 'application/json'}
        if os.environ.get('CVAT_HOST_HEADER'):
            headers['Host'] = os.environ['CVAT_HOST_HEADER']
        if hasattr(self, 'token'):
            headers['Authorization'] = 'Token ' + self.token
        request = Request(CVAT + route, headers=headers,
                          data=json.dumps(payload).encode() if payload is not None else None)
        try:
            with urlopen(request, timeout=10) as response:
                return json.load(response)
        except HTTPError as error:
            raise ValueError(f'CVAT respondió {error.code}. Revisa el acceso local y el job.') from None
        except (URLError, TimeoutError):
            raise ValueError('No se pudo conectar a CVAT. Comprueba el servicio y la URL configurada.') from None

    def listing(self, route):
        result, page = [], 1
        while True:
            data = self.request(route + ('&' if '?' in route else '?') + f'page_size=100&page={page}')
            result.extend(data['results'])
            if not data['next']:
                return result
            page += 1


def package_inventory():
    """Inventario registrado de la tarea 16; nunca aceptar rutas enviadas por CVAT."""
    directory = ROOT / 'Datos/V1/Equilibrado_v1_20261013'
    manifest = directory / 'manifest.json'
    consolidated = ROOT / 'Datos/Registros/Lotes/Equilibrado_v1_20261013/manifest.json'
    if consolidated.exists():
        manifest = consolidated
    if not manifest.exists():
        return {}
    reserve = read(ROOT / 'Datos/Registros/reserva_evaluacion.json')
    result = {}
    metadata = read(manifest)
    shared = metadata.get('base_archivos') == 'Datos'
    base = ROOT / 'Datos' if shared else directory
    for entry in metadata['imagenes']:
        source = (base / entry['archivo']).resolve()
        allowed = ((ROOT / 'Datos/V1/Lider', ROOT / 'Datos/V1/Sinteticas')
                   if shared else (directory,))
        if not any(source.is_relative_to(folder.resolve()) for folder in allowed):
            raise ValueError('Ruta del paquete fuera de su directorio.')
        original_id = Path(entry.get('imagen_fuente', '')).stem
        if original_id in reserve['image_ids'] or entry['escena'] in reserve['groups']:
            raise ValueError('El paquete contiene una foto o escena de reserva final.')
        if entry['split'] not in ('train', 'val') or (entry['split'] == 'val' and entry['origen'] != 'real'):
            raise ValueError('Partición inválida: la validación del paquete requiere fotos reales.')
        iid = entry['id']
        expected_stem = f'lider_{int(original_id):03}' if shared and entry['origen'] == 'real' and original_id.isdigit() else iid
        if iid in result or source.stem != expected_stem:
            raise ValueError('Identificadores repetidos o incompatibles en el paquete.')
        result[iid] = {'imagen_id': iid, 'archivo': source.relative_to(ROOT / 'Datos').as_posix(),
                       'grupo_escena': entry['escena'], 'sha256': entry['sha256'],
                       'split': entry['split'], 'origen': entry['origen'],
                       'ancho': entry['ancho'], 'alto': entry['alto']}
    groups = {}
    for entry in result.values():
        groups.setdefault(entry['grupo_escena'], set()).add(entry['split'])
    if any(len(splits) != 1 for splits in groups.values()):
        raise ValueError('Una escena del paquete aparece en entrenamiento y validación.')
    return result


def lider_express_inventory():
    """Registro manual de la tarea 19; sus escenas y partición siguen pendientes."""
    base = ROOT / LIDER_EXPRESS
    manifest = base / 'manifest.json'
    if not manifest.exists():
        return {}
    metadata = read(manifest)
    if (metadata.get('cvat', {}).get('task_id') != 19 or
            metadata.get('cvat', {}).get('project_id') != 7 or metadata.get('criterio') != V2_CRITERION):
        raise ValueError('El registro local de Líder Express no corresponde a la tarea 19 y su criterio v2.')
    result = {}
    with (base / 'inventario.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            source = (base / row['archivo']).resolve()
            if not source.is_relative_to((base / 'imagenes_ordenadas').resolve()):
                raise ValueError('Ruta de Líder Express fuera del directorio registrado.')
            iid = source.stem  # El original incluye _0_original en CVAT.
            if iid in result:
                raise ValueError('Fotos duplicadas en el registro de Líder Express.')
            result[iid] = {**row, 'imagen_id': iid, 'archivo': source.relative_to(ROOT / 'Datos').as_posix(),
                           'grupo_escena': row.get('grupo_escena') or 'pendiente',
                           'familia': row.get('imagen_origen_id'), 'split': row.get('particion_modelo', 'pending')}
    return result


def snapshot_inventory(snapshot):
    if any(source.get('task_id') == 19 for source in snapshot['sources']):
        if any(source.get('task_id') != 19 for source in snapshot['sources']):
            raise ValueError('Importa la tarea 19 en una copia separada de los lotes anteriores.')
        return lider_express_inventory(), False
    packaged = any(source.get('task_id') == 16 for source in snapshot['sources'])
    if packaged:
        if any(source.get('task_id') != 16 for source in snapshot['sources']):
            raise ValueError('Importa la tarea 16 separada del inventario histórico.')
        return package_inventory(), True
    with (ROOT / 'Datos/Registros/inventario.csv').open(encoding='utf-8-sig', newline='') as handle:
        return {row['imagen_id']: row for row in csv.DictReader(handle)}, False


def safe_image_path(image, registered=None):
    path = (ROOT / 'Datos' / current_inventory_path(image['archivo'])).resolve()
    if path.is_relative_to((ROOT / LIDER_EXPRESS / 'imagenes_ordenadas').resolve()) and any(
            current_inventory_path(image['archivo']) == current_inventory_path(item['archivo'])
            for item in (registered if registered is not None else lider_express_inventory()).values()):
        return path
    if path.is_relative_to((ROOT / 'Datos/V1/Lider').resolve()):
        return path
    if any(path.is_relative_to((ROOT / folder).resolve()) for folder in (
            'Datos/V1/Equilibrado_v1_20261013', 'Datos/V1/Sinteticas')) and any(current_inventory_path(image['archivo']) == current_inventory_path(item['archivo'])
           for item in (registered if registered is not None else package_inventory()).values()):
        return path
    raise ValueError('Ruta de imagen fuera del inventario registrado.')


def active_job_frames(job, meta):
    """Mantener índices de CVAT al excluir fotos marcadas como eliminadas."""
    if meta.get('included_frames') or meta.get('frame_filter'):
        raise ValueError('Este lote usa cuadros seleccionados o saltados; no se puede importar.')
    frames = meta['frames']
    start, stop = job['start_frame'], job['stop_frame']
    if len(frames) != stop - start + 1:
        raise ValueError('Los índices de imágenes del trabajo no coinciden con sus metadatos.')
    deleted = meta.get('deleted_frames') or []
    if (not isinstance(deleted, list) or any(type(i) is not int or not start <= i <= stop for i in deleted)
            or len(deleted) != len(set(deleted))):
        raise ValueError('Índices de fotos excluidas inválidos en CVAT.')
    deleted = set(deleted)
    return [(start + i, frame) for i, frame in enumerate(frames) if start + i not in deleted]


def annotation_jobs(client, task_id):
    jobs = [j for j in client.listing(f'/jobs?task_id={task_id}&type=annotation')
            if j.get('task_id') == task_id and j.get('type') == 'annotation']
    if not jobs or len(jobs) > 20 or len({j['id'] for j in jobs}) != len(jobs):
        raise ValueError('El lote debe contener entre 1 y 20 trabajos de anotación distintos.')
    return sorted(jobs, key=lambda j: (j['start_frame'], j['id']))


def import_sources(client=None):
    """Una opción por lote completo; nunca ofrecer trabajos sueltos."""
    client = client or CvatReader()
    with (ROOT / 'Datos/Registros/inventario.csv').open(encoding='utf-8-sig', newline='') as handle:
        inventory = {row['imagen_id']: row for row in csv.DictReader(handle)}
    reserve = read(ROOT / 'Datos/Registros/reserva_evaluacion.json')
    allowed = {key for key, row in inventory.items()
               if key not in reserve['image_ids'] and row['grupo_escena'] not in reserve['groups']}
    package = package_inventory()
    express = lider_express_inventory()
    projects = {p['id']: p['name'] for p in client.listing('/projects') if p['id'] in PROJECT_SCOPES}
    tasks = {t['id']: t for t in client.listing('/tasks') if t.get('project_id') in PROJECT_SCOPES
             and (t['project_id'] != 7 or t['id'] == 19)}
    grouped = {task_id: [] for task_id in tasks}
    for job in client.listing('/jobs?type=annotation'):
        if job.get('type') == 'annotation' and job.get('task_id') in tasks:
            grouped[job['task_id']].append(job)
    result = []
    for task_id, jobs in grouped.items():
        if not jobs or len(jobs) > 20:
            continue
        jobs.sort(key=lambda j: (j['start_frame'], j['id']))
        ids, excluded, valid = [], [], True
        for job in jobs:
            meta = client.request(f"/jobs/{job['id']}/data/meta")
            try:
                active = active_job_frames(job, meta)
            except ValueError:
                valid = False
                break
            ids.extend(Path(frame['name']).stem for _, frame in active)
            excluded.extend(Path(frame['name']).stem for index, frame in enumerate(meta['frames'])
                            if job['start_frame'] + index in (meta.get('deleted_frames') or []))
        registered = express.keys() if task_id == 19 else package.keys() if task_id == 16 else allowed
        if not valid or not ids or len(ids) != len(set(ids)) or set(ids) - registered:
            continue
        task = tasks[task_id]
        completed = sum(j.get('state') == 'completed' for j in jobs)
        result.append({'id': f'task:{task_id}', 'task_id': task_id,
                       'project_id': task['project_id'],
                       'project_name': projects.get(task['project_id'], f"Proyecto {task['project_id']}"),
                       'name': f"{task['name']} · {len(ids)} fotos" + (' · completado' if completed == len(jobs) else ''),
                       'group': task['name'], 'scope': project_scope(task),
                       'jobs': [j['id'] for j in jobs], 'image_ids': ids,
                       'completed_jobs': completed, 'excluded_image_ids': excluded,
                       **({'criterion_version': V2_CRITERION, 'pending_partition': True,
                           'fixed_validation': True, 'validation_ids': [],
                           'validation_note': 'Tarea 19 · criterio v2: escenas y partición pendientes. Puedes importar para revisar; el entrenamiento permanece bloqueado.'} if task_id == 19 else {}),
                       **({'package': 'Equilibrado_v1_20261013', 'fixed_validation': True,
                           'validation_ids': [iid for iid in ids if package[iid]['split'] == 'val']} if task_id == 16 else {})})
    from particion_niveles import load_partition
    if any(source['task_id'] == 19 for source in result):
        partition = load_partition(ROOT)
        if partition:
            for source in result:
                if source['task_id'] == 19:
                    source.update(pending_partition=False,
                                  validation_ids=[name for name, row in partition['records'].items() if row['effective_split'] == 'val'],
                                  validation_note='Etapa base: 160 imágenes para aprender y 10 reales para validar. 30 variantes de diagnóstico y 36 imágenes finales quedan fuera del entrenamiento.')
    return sorted(result, key=lambda source: (source['task_id'] != 19, source['task_id'] != 16, source['scope'] != 'Nivel_estados', source['task_id']))


def import_lot(config, *, client=None):
    """Resolver los trabajos del lote en CVAT, sin confiar en una lista del navegador."""
    task_id = config.get('task_id')
    if type(task_id) is not int or task_id < 1:
        raise ValueError('Selecciona un lote de CVAT o indica su número de tarea; no se importan trabajos sueltos.')
    client = client or CvatReader()
    task = client.request(f'/tasks/{task_id}')
    project_scope(task)
    jobs = annotation_jobs(client, task_id)
    return import_jobs({'jobs': [j['id'] for j in jobs], 'validation': config.get('validation', ['28'])}, client=client)


def image_track_shapes(tracks, job):
    """Normalizar solo tracks visibles en la última foto, sin inferir otros cuadros.

    Un track con una sola clave anterior puede extenderse por otras fotos. Aquí
    solo se acepta la última: su duración visible está limitada por el job.
    """
    result = []
    for track in tracks:
        keys = track.get('shapes', [])
        if (len(keys) != 1 or track.get('elements') or
                keys[0].get('type') != 'polygon' or keys[0].get('outside', False) or
                type(keys[0].get('frame')) is not int or
                keys[0]['frame'] != job['stop_frame'] or
                track.get('frame') != keys[0]['frame']):
            raise ValueError(
                f"El track {track.get('id')} del job {job.get('id')} puede abarcar varias fotos "
                'o no es un polígono visible. En CVAT, revísalo y conviértelo a formas '
                'independientes por foto antes de guardar y volver a importar.')
        shape = copy.deepcopy(keys[0])
        shape.pop('outside', None)
        attrs = {a['spec_id']: copy.deepcopy(a) for a in track.get('attributes', [])}
        attrs.update({a['spec_id']: copy.deepcopy(a) for a in shape.get('attributes', [])})
        shape.update(id=f"track {track['id']}", label_id=track['label_id'],
                     group=track.get('group', 0), source=track.get('source', 'manual'),
                     attributes=list(attrs.values()), imported_track_id=track['id'])
        result.append(shape)
    return result


def fetch_snapshot(job_ids, client=None):
    if not isinstance(job_ids, list) or not 1 <= len(job_ids) <= 20 or any(type(j) is not int or j < 1 for j in job_ids):
        raise ValueError('Selecciona entre 1 y 20 IDs de jobs válidos.')
    if len(set(job_ids)) != len(job_ids):
        raise ValueError('Un job no puede importarse dos veces.')
    client = client or CvatReader()
    snapshot = {'exported_at': now(), 'labels': [], 'frames': [],
                'annotations': {'shapes': [], 'tracks': [], 'tags': []}, 'sources': []}
    labels = {}
    for job_id in job_ids:
        job = client.request(f'/jobs/{job_id}')
        task = client.request(f"/tasks/{job['task_id']}")
        scope = project_scope(task)
        if job.get('type') != 'annotation':
            raise ValueError('Solo se importan trabajos de anotación.')
        if snapshot.get('scope', scope) != scope:
            raise ValueError('Importa los trabajos de módulos y los de estados por nivel en copias separadas.')
        snapshot['scope'] = scope
        meta = client.request(f'/jobs/{job_id}/data/meta')
        active = active_job_frames(job, meta)
        frames = meta['frames']
        annotations = client.request(f'/jobs/{job_id}/annotations')
        if annotations.get('tags'):
            raise ValueError(f'El job {job_id} tiene tags sin contorno. Revísalos en CVAT; '
                             'se requieren polígonos de Modulo y Nivel por foto.')
        converted = image_track_shapes(annotations.get('tracks', []), {**job, 'id': job_id})
        for label in client.listing(f'/labels?job_id={job_id}'):
            if label['id'] in labels and labels[label['id']] != label:
                raise ValueError('El esquema de etiquetas cambió durante la importación. Repite la lectura.')
            labels[label['id']] = label
        offset = len(snapshot['frames'])
        frame_map = {cvat_frame: offset + i for i, (cvat_frame, _) in enumerate(active)}
        snapshot['frames'].extend(frame for _, frame in active)
        for original in [*annotations['shapes'], *converted]:
            shape = copy.deepcopy(original)
            local_frame = shape['frame'] - job['start_frame']
            if not 0 <= local_frame < len(frames):
                raise ValueError('Anotación fuera de los índices del job.')
            if original['frame'] not in frame_map:
                continue
            shape.update(frame=frame_map[original['frame']], imported_job_id=job_id, cvat_frame=original['frame'])
            snapshot['annotations']['shapes'].append(shape)
        source = {'job_id': job_id, 'task_id': job['task_id'], 'task_name': task['name'],
                  'project_id': task['project_id'],
                  'assignee': job.get('assignee'), 'state': job.get('state'),
                  'updated_date': job.get('updated_date'),
                  'start_frame': job['start_frame'], 'stop_frame': job['stop_frame']}
        if meta.get('deleted_frames'):
            source['excluded_frames'] = [{'cvat_frame': i, 'name': frames[i - job['start_frame']]['name']} for i in meta['deleted_frames']]
        if converted:
            source.update(original_tracks=copy.deepcopy(annotations['tracks']),
                          normalization={'kind': 'single_visible_frame_track_to_polygon',
                                         'track_ids': [s['imported_track_id'] for s in converted],
                                         'cvat_modified': False})
        snapshot['sources'].append(source)
    snapshot['labels'] = list(labels.values())
    return snapshot


def annotation_id(value, prefix):
    """Comparar M1/M01 y N1/N01 sin cambiar los atributos guardados en CVAT."""
    if not isinstance(value, str) or not re.fullmatch(prefix + r'[0-9]+', value):
        return None
    number = value[1:].lstrip('0')
    return prefix + number if number else None


def inspect(snapshot, validation_ids):
    if snapshot_scope(snapshot) == 'Nivel_estados':
        from niveles_modelos import inspect_levels
        if any(source.get('project_id') == 7 for source in snapshot['sources']):
            from niveles_modelos import CRITERION
            from particion_niveles import BASE_STATES, load_partition
            partition = load_partition(ROOT)
            if partition:
                inventory = lider_express_inventory()
                registered = partition['records']
                names = {Path(frame['name']).stem for frame in snapshot['frames']}
                if names != set(registered):
                    raise ValueError('Importa la tarea 19 completa: se requieren las 236 imágenes de la partición fijada.')
                for name in names:
                    row = registered[name]
                    inv = inventory.get(name, {})
                    if (inv.get('sha256') != row['sha256'] or inv.get('grupo_escena') != row['grupo_escena']
                            or inv.get('split') != row['split'] or 'Datos/' + inv.get('archivo', '') != row['archivo']):
                        raise ValueError('Inventario y partición no coinciden. Revisa el registro antes de importar.')
                fixed = {name: row['effective_split'] for name, row in registered.items()}
                validation = [name for name, split in fixed.items() if split == 'val']
                report, rows = inspect_levels(snapshot, validation, states=BASE_STATES,
                    criterion={**CRITERION, 'version': V2_CRITERION, 'stage': 'base'}, fixed_splits=fixed)
                report.update(partition_binding=partition['binding'], partition_pending=False, stage='base',
                              trained_states=list(BASE_STATES), fixed_partition=True,
                              partition_counts=dict(Counter(fixed.values())))
                return report, rows
            return inspect_levels(snapshot, validation_ids, states=V2_STATES,
                                  criterion={**CRITERION, 'version': V2_CRITERION}, partition_pending=True)
        return inspect_levels(snapshot, validation_ids)
    from PIL import Image, ImageOps
    from shapely.geometry import Polygon
    from shapely.validation import explain_validity
    if not isinstance(validation_ids, list) or not validation_ids or any(not isinstance(v, str) for v in validation_ids):
        raise ValueError('Indica al menos una foto de validación de desarrollo.')
    with (ROOT / 'Datos/Registros/inventario.csv').open(encoding='utf-8-sig', newline='') as handle:
        inventory = {row['imagen_id']: row for row in csv.DictReader(handle)}
    reserve = read(ROOT / 'Datos/Registros/reserva_evaluacion.json')
    frames = snapshot['frames']
    ids = [Path(f['name']).stem for f in frames]
    if not frames or len(set(ids)) != len(ids):
        raise ValueError('Fotos repetidas: conserva una referencia acordada por foto; no mezcles las tres versiones del piloto.')
    if set(ids) - inventory.keys():
        raise ValueError('Hay fotos que no pertenecen al inventario interno. Registra su procedencia antes de importarlas.')
    if set(validation_ids) - set(ids):
        raise ValueError('Todas las fotos de validación deben estar en los jobs seleccionados.')
    groups = {inventory[v]['grupo_escena'] for v in validation_ids}
    labels = {label['id']: label for label in snapshot['labels']}
    issues, images, rows_by_image, seen_hashes = [], [], {}, set()

    def issue(photo, shape, message, blocking, category=None):
        issues.append({'foto': photo, 'shape_id': shape.get('id'),
                       'job_id': shape.get('imported_job_id'), 'problema': message,
                       'bloquea_modulos': blocking,
                       'clase': labels.get(shape.get('label_id'), {}).get('name'),
                       'categoria': category or ('modulos' if blocking else 'niveles')})

    by_frame = {i: [] for i in range(len(frames))}
    if snapshot['annotations'].get('tracks') or snapshot['annotations'].get('tags'):
        raise ValueError('Se requieren polígonos de imágenes, sin tracks ni tags.')
    for shape in snapshot['annotations']['shapes']:
        if type(shape['frame']) is not int or shape['frame'] not in by_frame:
            raise ValueError('Índice de anotación inválido.')
        by_frame[shape['frame']].append(shape)
    for index, frame in enumerate(frames):
        image_id = ids[index]
        inv = inventory[image_id]
        if image_id in reserve['image_ids'] or inv['grupo_escena'] in reserve['groups']:
            raise ValueError('El job contiene una foto o escena reservada para evaluación final.')
        source = (ROOT / 'Datos' / inv['archivo']).resolve()
        if not source.is_relative_to(ROOT / 'Datos'):
            raise ValueError('Ruta del inventario fuera de Datos.')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != inv['sha256']:
            raise ValueError(f'Original modificado: {image_id}.')
        if digest in seen_hashes:
            raise ValueError('Hay fotos con contenido idéntico. Conserva una sola referencia por imagen.')
        seen_hashes.add(digest)
        with Image.open(source) as image:
            oriented_size = (image.height, image.width) if image.getexif().get(274, 1) in (5, 6, 7, 8) else image.size
            if oriented_size != (frame['width'], frame['height']):
                raise ValueError(f'Dimensiones diferentes de CVAT: {image_id}.')
        modules, levels, keys, polygons, rows = set(), [], set(), set(), []
        module_count = 0
        for shape in by_frame[index]:
            label = labels.get(shape['label_id'])
            if not label or label['name'] not in ('Modulo', 'Nivel'):
                raise ValueError('Se encontraron clases distintas de Modulo/Nivel.')
            is_module = label['name'] == 'Modulo'
            spec = {a['id']: a['name'] for a in label['attributes']}
            attrs = {a['name']: a.get('default_value', '') for a in label['attributes']}
            attrs.update({spec[a['spec_id']]: a['value'] for a in shape['attributes']})
            values = shape['points']
            good = (shape['type'] == 'polygon' and not shape.get('outside') and
                    not shape.get('elements') and len(values) >= 6 and len(values) % 2 == 0 and
                    all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values))
            points = list(zip(values[::2], values[1::2])) if good else []
            poly = Polygon(points) if good else None
            if not good or not poly.is_valid or poly.area <= 1:
                issue(image_id, shape, 'Polígono inválido: ' + (explain_validity(poly) if poly else 'tipo/puntos'), is_module)
                good = False
            elif not all(-1e-6 <= x <= frame['width'] + 1e-6 and -1e-6 <= y <= frame['height'] + 1e-6 for x, y in points):
                issue(image_id, shape, 'Puntos fuera del encuadre', is_module)
                good = False
            module_id = annotation_id(attrs.get('modulo_id', ''), 'M')
            if not module_id:
                issue(image_id, shape, 'modulo_id debe tener formato M1', False, 'atributos')
            if attrs.get('integridad') not in ('completo', 'parcial'):
                issue(image_id, shape, 'Integridad pendiente', False, 'atributos')
            if is_module:
                module_count += 1
                if module_id and module_id in modules:
                    issue(image_id, shape, 'modulo_id repetido', False, 'atributos')
                if module_id:
                    modules.add(module_id)
                if good:
                    canonical = poly.normalize().wkb_hex
                    if canonical in polygons:
                        issue(image_id, shape, 'Polígono de módulo duplicado', True)
                    polygons.add(canonical)
                    rows.append('0 ' + ' '.join(f'{v:.8f}' for x, y in points for v in
                                              (min(1, max(0, x/frame['width'])), min(1, max(0, y/frame['height'])))))
            else:
                levels.append((shape, attrs))
                level_id = annotation_id(attrs.get('nivel_id', ''), 'N')
                key = (module_id, level_id)
                if not level_id or key in keys:
                    issue(image_id, shape, 'nivel_id inválido o repetido dentro del módulo', False, 'atributos')
                keys.add(key)
                if attrs.get('limite_superior') not in ('abierto', 'cerrado'):
                    issue(image_id, shape, 'Límite superior pendiente', False)
        for shape, attrs in levels:
            parent_id = annotation_id(attrs.get('modulo_id', ''), 'M')
            if not parent_id or parent_id not in modules:
                issue(image_id, shape, 'Nivel sin módulo padre existente', False, 'atributos')
        if not module_count:
            issue(image_id, {}, 'Foto sin módulos: revisa que el trabajo esté completo', True)
        split = 'val' if inv['grupo_escena'] in groups else 'train'
        images.append({'imagen': image_id + source.suffix, 'imagen_id': image_id, 'archivo': inv['archivo'],
                       'grupo_escena': inv['grupo_escena'], 'sha256': digest, 'split': split,
                       'modulos': module_count, 'niveles_solo_revision': len(levels)})
        rows_by_image[image_id] = rows
    if not any(item['split'] == 'train' for item in images):
        raise ValueError('Debe quedar al menos una escena de entrenamiento separada de validación.')
    return {'imagenes': images, 'incidencias': issues,
            'bloqueos_modulos': sum(i['bloquea_modulos'] for i in issues),
            'avisos_atributos': sum(i['categoria'] == 'atributos' for i in issues),
            'avisos_niveles': sum(i['categoria'] == 'niveles' for i in issues)}, rows_by_image


def snapshot_scope(snapshot):
    inferred = 'Nivel_estados' if {l['name'] for l in snapshot['labels']} == {'Nivel'} and any(
        a['name'] == 'estado' for l in snapshot['labels'] for a in l['attributes']) else 'Modulo'
    scope = snapshot.get('scope', inferred)
    if scope not in ('Modulo', 'Nivel_estados') or scope != inferred:
        raise ValueError('El esquema no corresponde al tipo de entrenamiento de esta copia.')
    return scope


def version_path(version_id, *, allow_archived=False):
    if not isinstance(version_id, str) or not re.fullmatch(r'datos_[0-9]{8}_[0-9]{6}_[a-f0-9]{8}', version_id):
        raise ValueError('Versión de datos inválida.')
    path = VERSIONS / version_id
    if not path.is_dir():
        raise ValueError('Versión desconocida.')
    if not path.resolve().is_relative_to(VERSIONS.resolve()):
        raise ValueError('Ruta de versión inválida.')
    if not allow_archived and (path / 'archivo.json').exists():
        raise ValueError('Esta copia está archivada. Recupérala antes de usarla.')
    return path


def version_usage_index():
    """Read experiment references once for the whole version list."""
    uses = {}
    for name in ('config_interfaz.json', 'version_datos.json', 'manifest.json'):
        for path in (ROOT / 'Laboratorio/Experimentos').glob(f'*/{name}'):
            value = read(path)
            ids = {value.get('id'), value.get('version_datos')}
            if value.get('source_kind') == 'dataset':
                ids.add(value.get('source'))
            for version_id in ids - {None}:
                uses.setdefault(version_id, set()).add(path.parent.name)
    for path in (ROOT / 'Laboratorio/Experimentos/panel_pruebas').glob('*/solicitud.json'):
        value = read(path)
        if value.get('source') and value.get('source_kind') == 'dataset':
            uses.setdefault(value['source'], set()).add(value.get('run') or path.parent.name)
    return {version_id: sorted(names) for version_id, names in uses.items()}


def version_uses(version_id):
    return version_usage_index().get(version_id, [])


def versions(*, archived=False):
    uses = version_usage_index()
    return [{**read(p), 'archive_uses': uses.get(p.parent.name, []),
             **({'archived_at': read(p.parent / 'archivo.json')['archived_at']} if archived else {})}
            for p in sorted(VERSIONS.glob('*/version.json'), reverse=True)
            if (p.parent / 'archivo.json').exists() == archived]


def archive(config):
    path = version_path(config.get('id'))
    uses = version_uses(path.name)
    if uses:
        raise ValueError('Esta copia se conserva porque la usan estos ensayos: ' + ', '.join(uses))
    record = {'id': path.name, 'archived_at': now()}
    write(path / 'archivo.json', record)
    return record


def restore(config):
    path = version_path(config.get('id'), allow_archived=True)
    marker = path / 'archivo.json'
    if not marker.exists():
        raise ValueError('Esta copia no está archivada.')
    marker.unlink()
    return read(path / 'version.json')


def import_signature(snapshot, validation):
    """Comparar dibujos y partición; las fechas de lectura no crean versiones."""
    shapes = copy.deepcopy(snapshot['annotations']['shapes'])
    for shape in shapes:
        # El cuadro original es procedencia adicional en las copias nuevas.
        shape.pop('cvat_frame', None)
        shape['attributes'] = sorted(shape.get('attributes', []), key=lambda a: a['spec_id'])
    labels = copy.deepcopy(snapshot['labels'])
    for label in labels:
        label['attributes'] = sorted(label.get('attributes', []), key=lambda a: a['id'])
    stable = {'frames': snapshot['frames'], 'labels': sorted(labels, key=lambda label: label['id']),
              'shapes': sorted(shapes, key=lambda shape: json.dumps(shape, sort_keys=True)),
              'sources': sorted([{'job_id': s['job_id'], 'task_id': s.get('task_id'), **({'excluded_frames': s['excluded_frames']} if s.get('excluded_frames') else {})}
                                 for s in snapshot['sources']], key=lambda s: s['job_id']),
              'validation': sorted(set(validation)), 'guide': 'v2'}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, allow_nan=False).encode()).hexdigest()


def import_jobs(config, *, client=None):
    snapshot = fetch_snapshot(config.get('jobs'), client=client) if client else fetch_snapshot(config.get('jobs'))
    inventory, packaged = snapshot_inventory(snapshot)
    if any(s.get('task_id') == 19 for s in snapshot['sources']):
        validation = []
    elif packaged:
        validation = [Path(frame['name']).stem for frame in snapshot['frames']
                      if inventory.get(Path(frame['name']).stem, {}).get('split') == 'val']
    else:
        validation = config.get('validation', ['28'])
    report, _ = inspect(snapshot, validation)
    signature = import_signature(snapshot, validation)
    binding = report.get('partition_binding')
    cvat_status = {'checked_at': now(), 'completed_jobs': sum(source.get('state') == 'completed' for source in snapshot['sources']),
                   'total_jobs': len(snapshot['sources'])}
    for metadata in sorted(VERSIONS.glob('*/version.json'), reverse=True):
        if (metadata.parent / 'archivo.json').exists():
            continue
        value = read(metadata)
        old_snapshot, partition = metadata.parent / 'snapshot_cvat.json', metadata.parent / 'particion.json'
        if (hashlib.sha256(old_snapshot.read_bytes()).hexdigest() != value['snapshot_sha256'] or
                hashlib.sha256(partition.read_bytes()).hexdigest() != value['partition_sha256']):
            continue
        old_partition = read(partition)
        if (old_partition.get('guia') == 'v2' and old_partition.get('fixed_partition') == binding
                and import_signature(read(old_snapshot), old_partition['validation_ids']) == signature):
            if value['report'] != report:
                value['report'] = report
                write(metadata, value)
                write(metadata.parent / 'revision_etiquetas.json', report['incidencias'])
            value['cvat_status'] = cvat_status
            write(metadata, value)
            return {**value, 'import_reused': True}
    version_id = 'datos_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_') + uuid.uuid4().hex[:8]
    path = VERSIONS / version_id
    path.mkdir(parents=True)
    write(path / 'snapshot_cvat.json', snapshot)
    write(path / 'particion.json', {'validation_ids': validation, 'guia': 'v2',
                                  **({'fixed_partition': binding} if binding else {})})
    write(path / 'revision_etiquetas.json', report['incidencias'])
    value = {'id': version_id, 'state': 'pendiente_revision', 'created_at': now(),
             'snapshot_sha256': hashlib.sha256((path / 'snapshot_cvat.json').read_bytes()).hexdigest(),
             'partition_sha256': hashlib.sha256((path / 'particion.json').read_bytes()).hexdigest(),
             'sources': snapshot['sources'], 'report': report, 'scope': snapshot_scope(snapshot), 'cvat_status': cvat_status}
    write(path / 'version.json', value)
    return value


def drawing_preview(version_id, photo, shape_id, job_id):
    """Servir un dibujo de una copia activa, solo con fotos internas de desarrollo."""
    path = version_path(version_id)
    value = read(path / 'version.json')
    snapshot_file = path / 'snapshot_cvat.json'
    if hashlib.sha256(snapshot_file.read_bytes()).hexdigest() != value['snapshot_sha256']:
        raise ValueError('La copia fue modificada. Vuelve a importar las anotaciones.')
    snapshot = read(snapshot_file)
    frames = [(i, frame) for i, frame in enumerate(snapshot['frames']) if Path(frame['name']).stem == photo]
    if len(frames) != 1:
        raise ValueError('Foto desconocida en esta copia.')
    index, frame = frames[0]
    source = next((s for s in snapshot['sources'] if str(s['job_id']) == str(job_id)), None)
    if not source:
        raise ValueError('Trabajo desconocido en esta copia.')
    matches = [s for s in snapshot['annotations']['shapes'] if s['frame'] == index and
               str(s.get('id')) == str(shape_id) and
               str(s.get('imported_job_id', source['job_id'] if len(snapshot['sources']) == 1 else None)) == str(job_id)]
    if len(matches) != 1:
        raise ValueError('Dibujo desconocido en esta foto y trabajo.')
    image = next((i for i in value['report']['imagenes'] if i['imagen_id'] == photo), None)
    reserve = read(ROOT / 'Datos/Registros/reserva_evaluacion.json')
    if not image or photo in reserve['image_ids'] or image['grupo_escena'] in reserve['groups']:
        raise ValueError('Esta foto no está disponible para revisión de desarrollo.')
    original = safe_image_path(image)
    if hashlib.sha256(original.read_bytes()).hexdigest() != image['sha256']:
        raise ValueError('La imagen original cambió; no se puede mostrar sobre esta copia.')
    shape = matches[0]
    label = next((l for l in snapshot['labels'] if l['id'] == shape['label_id']), None)
    if not label:
        raise ValueError('Etiqueta desconocida.')
    names = {a['id']: a['name'] for a in label['attributes']}
    attrs = {names[a['spec_id']]: a['value'] for a in shape['attributes']}
    cvat_frame = shape.get('cvat_frame')
    if cvat_frame is None and len(snapshot['sources']) == 1:
        start = source.get('start_frame')
        if start is None:
            org = read(ROOT / 'Datos/Registros/CVAT/organizacion.json') if (ROOT / 'Datos/Registros/CVAT/organizacion.json').exists() else {}
            start = next((j['start_frame'] for task in org.get('tasks', []) if task['id'] == source.get('task_id')
                          for j in task['jobs'] if j['id'] == source['job_id']), None)
        if start is not None:
            cvat_frame = start + index
    return {'photo': photo, 'image_path': current_image_path('Datos/' + image['archivo']),
            'width': frame['width'], 'height': frame['height'], 'shape_id': shape['id'],
            'type': shape['type'], 'points': shape['points'], 'label': label['name'],
            'attributes': attrs, 'job_id': source['job_id'], 'task_id': source.get('task_id'),
            'cvat_frame': cvat_frame, 'created_at': value['created_at']}


def prepare_version(path, run, seed=42):
    """Materializar una versión aprobada, comprobando de nuevo originales y etiquetas."""
    from PIL import Image, ImageOps
    value = read(path / ('version_datos.json' if (path / 'version_datos.json').exists() else 'version.json'))
    snapshot_file = path / 'snapshot_cvat.json'
    if hashlib.sha256(snapshot_file.read_bytes()).hexdigest() != value['snapshot_sha256']:
        raise ValueError('La copia de anotaciones fue modificada. Importa una versión nueva.')
    if hashlib.sha256((path / 'particion.json').read_bytes()).hexdigest() != value['partition_sha256']:
        raise ValueError('La partición fue modificada. Importa una versión nueva.')
    report, rows = inspect(read(snapshot_file), read(path / 'particion.json')['validation_ids'])
    from particion_niveles import verify_binding
    verify_binding(ROOT, read(path / 'particion.json'), report)
    levels = value.get('scope') == 'Nivel_estados'
    if report.get('bloqueos_entrenamiento', report['bloqueos_modulos']):
        raise ValueError('Hay errores de anotación que deben corregirse en CVAT y volver a importar.')
    if value['state'] != ('lista_niveles' if levels else 'lista_modulos'):
        raise ValueError('Falta la revisión humana de esta copia.')
    directory = 'dataset_niveles' if levels else 'dataset_modulos'
    if (run / directory).exists() or ((run / 'manifest.json').exists() and read(run / 'manifest.json').get('dataset_ref')):
        raise ValueError('El conjunto ya existe; conserva esa ejecución.')
    dataset = run / directory
    training_images = [item for item in report['imagenes'] if item['split'] in ('train', 'val')]
    for item in training_images:
        for sub in ('images', 'labels'):
            (dataset / sub / item['split']).mkdir(parents=True, exist_ok=True)
        source = ROOT / current_image_path('Datos/' + item['archivo'])
        target = dataset / 'images' / item['split'] / item['imagen']
        with Image.open(source) as image:
            if image.getexif().get(274, 1) == 1:
                shutil.copy2(source, target)
            else:
                ImageOps.exif_transpose(image).convert('RGB').save(target, quality=95)
        (dataset / 'labels' / item['split'] / (item['imagen_id'] + '.txt')).write_text(
            '\n'.join(rows[item['imagen_id']]) + '\n', encoding='utf-8')
    from niveles_modelos import CLASS_NAMES
    classes = report.get('clases', CLASS_NAMES) if levels else ['Modulo']
    write(run / 'manifest.json', {'snapshot': 'snapshot_cvat.json', 'clases': classes,
                                 'scope': value.get('scope', 'Modulo'), 'dataset_dir': directory,
                                 'criterion': report.get('criterion'), 'estados': report.get('estados'),
                                 'estados_por_split': report.get('estados_por_split'),
                                 'imagenes': training_images, 'reserva_utilizada': False,
                                 'partition_binding': report.get('partition_binding'),
                                 'partition_counts': report.get('partition_counts'),
                                 'semilla': seed, 'version_datos': value['id'],
                                 'revision': value['review'],
                                 'orientacion_imagenes': 'EXIF aplicada en las copias; originales conservados',
                                 'nota': 'Validación de desarrollo por escena. No evaluable no genera alerta de stock.' if levels else
                                         'Validación de desarrollo por escena. Niveles conservados solo para revisión.'})
    write(run / 'revision_etiquetas.json', report['incidencias'])
    (dataset / 'data.yaml').write_text(f'path: {dataset.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n' +
                                     ''.join(f'  {i}: {name}\n' for i, name in enumerate(classes)), encoding='utf-8')
    if levels:
        from conjuntos import consolidate_export
        consolidate_export(ROOT, run)


def approve(config):
    path = version_path(config.get('id'))
    value = read(path / 'version.json')
    if value['state'] != 'pendiente_revision':
        raise ValueError('Esta versión ya tiene una revisión registrada.')
    reviewer = config.get('reviewer', '')
    if not isinstance(reviewer, str) or not 2 <= len(reviewer.strip()) <= 100 or config.get('reviewed') is not True:
        raise ValueError('Registra quién revisó las anotaciones y confirma la revisión humana.')
    if hashlib.sha256((path / 'snapshot_cvat.json').read_bytes()).hexdigest() != value['snapshot_sha256']:
        raise ValueError('La copia fue modificada. Importa una versión nueva.')
    if hashlib.sha256((path / 'particion.json').read_bytes()).hexdigest() != value['partition_sha256']:
        raise ValueError('La partición fue modificada. Importa una versión nueva.')
    report, _ = inspect(read(path / 'snapshot_cvat.json'), read(path / 'particion.json')['validation_ids'])
    from particion_niveles import verify_binding
    verify_binding(ROOT, read(path / 'particion.json'), report)
    if report.get('bloqueos_entrenamiento', report['bloqueos_modulos']):
        raise ValueError('Corrige los bloqueos en CVAT y vuelve a importar antes de registrar la revisión.')
    levels = value.get('scope') == 'Nivel_estados'
    value.update(state='lista_niveles' if levels else 'lista_modulos', report=report,
                 review={'reviewer': reviewer.strip(), 'date': now(),
                         'guide': report.get('criterion', {}).get('version', 'disponibilidad_visual_nivel_v1') if levels else 'v2',
                         'scope': value.get('scope', 'Modulo'),
                         'note': 'Revisión humana de niveles y estados registrada.' if levels else
                                 'Declaración humana registrada; no constituye aprobación de niveles.'})
    write(path / 'version.json', value)
    return value
