"""Panel de experimentos local o en Docker; ML corre en un proceso separado."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import gzip
from functools import lru_cache
from io import BytesIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from urllib.parse import parse_qs, quote, urlparse
import uuid
import warnings
import datos_modelos as datasets
from sync_cvat import CvatSync
from PIL import Image, ImageOps, UnidentifiedImageError
from rutas_datos import current_image_path, experiment_parts

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
JOBS = ROOT / 'Laboratorio/Experimentos/panel_pruebas'
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_UPLOAD_PIXELS = 24_000_000
LOCAL_PYTHON = ROOT / '.venv-modelo/Scripts/python.exe'
PYTHON = Path(os.environ.get('MODEL_PYTHON') or
              (str(LOCAL_PYTHON) if LOCAL_PYTHON.exists() else sys.executable))
LOCK = threading.Lock()
ACTIVE = None
DATA_LOCK = threading.Lock()
CATALOG_LOCK = threading.Lock()
CATALOG_CACHE = None
JOB_CACHE_LOCK = threading.Lock()
JOB_CACHE = {}
FINISHED_JOB_RECHECK_SECONDS = 15


def invalidate_catalog():
    global CATALOG_CACHE
    with CATALOG_LOCK:
        CATALOG_CACHE = None


def cached_catalog():
    """Cache reads only; mutations still validate current on-disk data."""
    global CATALOG_CACHE
    with CATALOG_LOCK:
        if CATALOG_CACHE is None or time.monotonic() >= CATALOG_CACHE[0]:
            value = catalog()
            body = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
            CATALOG_CACHE = (time.monotonic() + (5 if ACTIVE else 15), body,
                             gzip.compress(body, compresslevel=1, mtime=0),
                             'W/"' + hashlib.sha256(body).hexdigest() + '"')
        return CATALOG_CACHE


CVAT_SYNC = CvatSync(DATA_LOCK, invalidate_catalog)


def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def relative(path):
    return path.relative_to(ROOT).as_posix()


def file_url(path):
    return '/file?path=' + quote(relative(path))


def dataset_signature(manifest, snapshot):
    images = [{**item, 'archivo': current_image_path('Datos/' + item['archivo']).removeprefix('Datos/')}
              if item.get('archivo') else item for item in manifest['imagenes']]
    return hashlib.sha256(json.dumps(images, sort_keys=True).encode() + snapshot).hexdigest()


def inventory():
    reserve = read_json(ROOT / 'Datos/Registros/reserva_evaluacion.json')
    if not reserve:
        raise ValueError('Falta la configuración de la reserva final.')
    with (ROOT / 'Datos/Registros/inventario.csv').open(encoding='utf-8-sig', newline='') as handle:
        return [item for item in csv.DictReader(handle)
                if item['imagen_id'] not in reserve['image_ids'] and item['grupo_escena'] not in reserve['groups']]


def base_development_images():
    """Expose registered development photos, including reviewed validation variants."""
    from particion_niveles import load_partition
    partition = load_partition(ROOT)
    if not partition:
        return []
    registered = datasets.lider_express_inventory()
    return [{'id': 'Datos/' + registered[name]['archivo'], 'name': name,
             'scene': row['grupo_escena'], 'project_version': 'v2',
             'sha256': row.get('sha256'), 'origin': row.get('origen'),
             'url': file_url(ROOT / 'Datos' / registered[name]['archivo'])}
            for name, row in partition['records'].items()
            if row['effective_split'] in ('train', 'val', 'diagnostico')]


def uploaded_photo(requested):
    """Only accept server-issued image paths, never arbitrary client paths."""
    requested = current_image_path(requested)
    if not isinstance(requested, str) or not re.fullmatch(r'Laboratorio/Experimentos/panel_pruebas/Subidas_panel/[a-f0-9]{32}/imagen\.jpg', requested):
        return None
    path = (ROOT / requested).resolve()
    if not path.is_relative_to((ROOT / 'Laboratorio/Experimentos/panel_pruebas/Subidas_panel').resolve()):
        return None
    metadata = read_json(path.parent / 'foto.json')
    return {**metadata, 'id': requested} if path.is_file() and metadata and current_image_path(metadata.get('id')) == requested else None


def save_uploaded_photo(body, filename):
    """Decode and orient a photo in an isolated area, outside training data."""
    if not body or len(body) > MAX_UPLOAD_BYTES:
        raise ValueError('La foto debe pesar como máximo 15 MB.')
    digest = hashlib.sha256(body).hexdigest()
    # Manual inference also accepts evaluation photos. Uploads stay isolated
    # from the inventory and annotated datasets used for training/validation.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(body)) as source:
                if source.format not in ('JPEG', 'PNG', 'WEBP') or getattr(source, 'n_frames', 1) != 1:
                    raise ValueError('Elige una foto JPG, PNG o WebP sin animación.')
                if source.width * source.height > MAX_UPLOAD_PIXELS:
                    raise ValueError('La foto supera los 24 megapíxeles. Reduce su tamaño y vuelve a subirla.')
                source.load()
                oriented = ImageOps.exif_transpose(source).convert('RGBA')
                image = Image.new('RGB', oriented.size, 'white')
                image.paste(oriented, mask=oriented.getchannel('A'))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('No pudimos abrir la foto. Prueba con un archivo JPG, PNG o WebP válido.') from None
    # Bound full-resolution mask memory; model input size is configured separately.
    image.thumbnail((4096, 4096))
    folder = ROOT / 'Laboratorio/Experimentos/panel_pruebas/Subidas_panel' / uuid.uuid4().hex
    folder.mkdir(parents=True)
    path = folder / 'imagen.jpg'
    image.save(path, quality=95)
    name = Path(str(filename).replace('\\', '/')).name
    name = ''.join(c for c in name if c.isprintable())[:160] or 'Mi foto'
    photo = {'id': relative(path), 'name': name, 'width': image.width, 'height': image.height,
             'sha256_original': digest, 'created_at': datetime.now(timezone.utc).isoformat(), 'source': 'upload'}
    write_json(folder / 'foto.json', photo)
    return {**photo, 'url': file_url(path)}


def model_archive_path():
    return ROOT / '.config-modelo/modelos_archivados.json'


def model_archive_records():
    value = read_json(model_archive_path(), {'schema_version': 1, 'models': {}})
    if not isinstance(value, dict) or not isinstance(value.get('models'), dict):
        raise ValueError('No se pudo leer la lista de modelos quitados. Revisa el registro del laboratorio.')
    return value['models']


def manifest_image_path(photo):
    """Resolve historical names against the same paths as the photo inventory."""
    return current_image_path('Datos/' + photo['archivo'] if photo.get('archivo')
                              else 'Datos/V1/Lider/' + photo['imagen'])


def training_image_ids(model, runs):
    """Include local parent training runs when a model was fine-tuned."""
    by_id = {run['id']: run for run in runs}
    pending, visited, images = [model.get('run')], set(), set()
    while pending:
        run_id = pending.pop()
        if run_id in visited or run_id not in by_id:
            continue
        visited.add(run_id)
        run = by_id[run_id]
        images.update(manifest_image_path(photo) for photo in run['manifest']['imagenes']
                      if photo.get('split') == 'train')
        parent = experiment_parts(run.get('config', {}).get('model', ''))
        if len(parent) > 2 and parent[0] == 'Laboratorio/Experimentos':
            pending.append(parent[1])
    return sorted(images)


def catalog():
    runs, models = [], []
    for path in sorted((ROOT / 'Laboratorio/Experimentos').iterdir()):
        manifest = read_json(path / 'manifest.json') if path.is_dir() else None
        if not manifest:
            continue
        history = []
        csv_path = path / 'entrenamiento/results.csv'
        if csv_path.exists():
            with csv_path.open(newline='', encoding='utf-8-sig') as handle:
                for row in csv.DictReader(handle):
                    try:
                        history.append({key.strip(): float(value) for key, value in row.items()})
                    except (ValueError, TypeError):
                        pass  # Una época en proceso todavía puede tener una fila parcial.
        signature = dataset_signature(manifest, (path / 'snapshot_cvat.json').read_bytes())
        comparisons = []
        for item in read_json(path / 'evaluacion_por_imagen.json', []):
            jpg = path / 'comparaciones' / f"{Path(item['imagen']).stem}_{item['split']}.jpg"
            comparisons.append({**item, 'url': file_url(jpg) if jpg.exists() else None})
        runs.append({'id': path.name, 'manifest': manifest, 'signature': signature,
                     'decision': read_json(path / 'decision_modelo.json', {}).get('current'),
                     'evaluation_protocol': read_json(path / 'protocolo_evaluacion.json', None),
                     'metrics': read_json(path / 'metricas_validacion.json', {}),
                     'history': history, 'comparisons': comparisons,
                     'config': read_json(path / 'config_interfaz.json', {}),
                     'availability': read_json(path / 'metricas_alertas.json', None),
                     'development_evaluation': read_json(path / 'evaluacion_desarrollo.json', None),
                     'ready': (path / 'metricas_validacion.json').exists()})
        for checkpoint in ('best', 'last'):
            weights = path / f'entrenamiento/weights/{checkpoint}.pt'
            if weights.exists():
                models.append({'id': relative(weights), 'name': f'{path.name} · {checkpoint}',
                               'run': path.name, 'imgsz': read_json(path / 'config_interfaz.json', {}).get('imgsz', 640),
                               'classes': manifest.get('clases', []), 'criterion': manifest.get('criterion')})
    for path in sorted((ROOT / 'Modelos/preentrenados').glob('*.pt')):
        models.append({'id': relative(path), 'name': f'{path.stem} · preentrenado genérico', 'run': None, 'imgsz': 640})
    images = [{'id': relative(ROOT / 'Datos' / item['archivo']), 'name': item['imagen_id'],
               'scene': item['grupo_escena'], 'url': file_url(ROOT / 'Datos' / item['archivo'])} for item in inventory()]
    # Historical manifests use REAL_06 / Equilibrado paths; the inventory now
    # calls the same original 06 / lider_006. Bind by the resolved source path.
    v1_paths = {current_image_path('Datos/' + photo['archivo'])
                for run in runs
                if run['manifest'].get('criterion', {}).get('version') == 'disponibilidad_visual_nivel_v1'
                or any(name in run['manifest'].get('clases', [])
                       for name in ('Nivel_vacio', 'Nivel_baja_disponibilidad'))
                for photo in run['manifest']['imagenes']
                if photo.get('archivo') and photo.get('split') in ('train', 'val')}
    images = [{**image, 'project_version': 'v1'} if image['id'] in v1_paths else image for image in images]
    images = list({item['id']: item for item in [*images, *base_development_images()]}.values())
    models = [{**model, 'training_images': training_image_ids(model, runs)} for model in models]
    records = model_archive_records()
    archived = [{**model, 'archived_at': records[model['id']].get('archived_at')}
                for model in models if model['run'] and model['id'] in records]
    visible = [model for model in models if not model['run'] or model['id'] not in records]
    return {'runs': runs, 'models': visible, 'archived_models': archived, 'images': images, 'datasets': datasets.versions(),
            'archived_datasets': datasets.versions(archived=True)}


def record_decision(config):
    """Persist an explicit human decision, retaining prior records atomically."""
    run_id = config.get('run')
    if not isinstance(run_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', run_id):
        raise ValueError('Identificador de ensayo inválido.')
    folder = (ROOT / 'Laboratorio/Experimentos' / run_id).resolve()
    if folder.parent != (ROOT / 'Laboratorio/Experimentos').resolve() or not (folder / 'manifest.json').is_file():
        raise ValueError('El ensayo ya no está disponible.')
    status, reason, author = (config.get(key) for key in ('status', 'reason', 'author'))
    if status not in ('candidato', 'seguir_ajustando', 'descartado'):
        raise ValueError('Elige candidato, seguir ajustando o descartado.')
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 2000:
        raise ValueError('Registra un motivo de hasta 2000 caracteres.')
    if not isinstance(author, str) or not 2 <= len(author.strip()) <= 100:
        raise ValueError('Registra el autor de la decisión (2–100 caracteres).')
    current = dict(status=status, reason=reason.strip(), author=author.strip(), date=datetime.now(timezone.utc).isoformat())
    path = folder / 'decision_modelo.json'
    history = read_json(path, {}).get('history', [])
    temporary = folder / f'.decision_{uuid.uuid4().hex}.tmp'
    temporary.write_text(json.dumps({'current': current, 'history': [*history, current]}, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)
    invalidate_catalog()
    return {'run': run_id, **current}


def change_model_visibility(config, *, archive):
    """Only persist selector visibility; never move or remove model files."""
    model_id = config.get('id')
    if not isinstance(model_id, str) or not model_id:
        raise ValueError('Elige el modelo que quieres quitar o recuperar.')
    data = catalog()
    model = next((item for item in data['models'] + data['archived_models']
                  if item['id'] == model_id), None)
    if not model:
        raise ValueError('Este modelo ya no está disponible. Actualiza la lista.')
    if not model['run']:
        raise ValueError('Los modelos generales se conservan como punto de partida para nuevos ensayos.')
    if archive and ACTIVE:
        status = read_json(JOBS / ACTIVE / 'estado.json', {})
        job_config = status.get('config', {})
        if model_id == job_config.get('model') or model['run'] == job_config.get('run'):
            raise ValueError('Este modelo pertenece a un trabajo en curso. Espera a que termine para quitarlo de la lista.')
    records = model_archive_records()
    if archive:
        records.setdefault(model_id, {'archived_at': datetime.now(timezone.utc).isoformat()})
    else:
        if model_id not in records:
            raise ValueError('Este modelo ya está disponible en la lista.')
        records.pop(model_id)
    path = model_archive_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, {'schema_version': 1, 'models': records})
    invalidate_catalog()
    return {'id': model_id, 'archived': archive}


def number(config, key, low, high, integer=False):
    value = config[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
        raise ValueError(f'{key}: valor fuera del rango {low}–{high}.')
    if integer and int(value) != value:
        raise ValueError(f'{key}: se requiere un número entero.')
    return int(value) if integer else value


def validate(config, data):
    config = {**config, 'image': current_image_path(config.get('image')),
              'model': current_image_path(config.get('model'))}
    models = {item['id']: item for item in data['models']}
    if config.get('model') not in models:
        raise ValueError('Elige un modelo local disponible.')
    action = config.get('action')
    clean = {'action': action, 'model': config['model'], 'imgsz': number(config, 'imgsz', 320, 1280, True)}
    if clean['imgsz'] % 32:
        raise ValueError('El tamaño debe ser múltiplo de 32.')
    if action == 'predict':
        occupancy = config.get('occupancy', False)
        if not isinstance(occupancy, bool):
            raise ValueError('El modo de bordes debe ser verdadero o falso.')
        occupancy_version = config.get('occupancy_version', 'v1')
        if occupancy_version not in ('v1', 'v2') or (not occupancy and occupancy_version != 'v1'):
            raise ValueError('Elige V1 o V2 con la detección de bordes activada.')
        upload = uploaded_photo(config.get('image'))
        if not upload and config.get('image') not in {item['id'] for item in data['images']}:
            raise ValueError('Imagen desconocida o reservada para evaluación final.')
        clean.update(image=config['image'], conf=number(config, 'conf', 0.01, 0.99), nms=number(config, 'nms', 0.1, 0.95))
        run = models[clean['model']]['run']
        source = next((item for item in data['runs'] if item['id'] == run), None)
        if not upload and clean['image'] in training_image_ids(models[clean['model']], data['runs']):
            raise ValueError('Esta foto se usó para entrenar el modelo seleccionado. Elige una foto no usada en su entrenamiento.')
        if source:
            clean['scope'] = source['manifest'].get('scope', 'Modulo')
        if occupancy:
            if not source or source['manifest'].get('criterion', {}).get('version') != 'disponibilidad_visual_nivel_v2_reponer':
                raise ValueError('El experimento con Paulo requiere un modelo de niveles V2.')
            clean['occupancy'] = True
            clean['occupancy_version'] = occupancy_version
        if upload:
            clean.update(image_source='upload', image_name=upload['name'])
        if source and not upload:
            entry = next((item for item in source['manifest']['imagenes']
                          if manifest_image_path(item) == clean['image']), None)
            if entry:
                directory = source['manifest'].get('dataset_dir', 'dataset_modulos')
                if directory not in ('dataset_modulos', 'dataset_niveles'):
                    raise ValueError('Directorio del conjunto inválido.')
                from conjuntos import dataset_directory
                labels = dataset_directory(ROOT, ROOT / 'Laboratorio/Experimentos' / run, source['manifest']) / 'labels'
                clean['truth'] = relative(labels / entry['split'] / (Path(entry['imagen']).stem + '.txt'))
                clean['scope'] = source['manifest'].get('scope', 'Modulo')
                clean['split'] = entry['split']
            elif source['manifest'].get('criterion', {}).get('stage') == 'base':
                from evaluar_desarrollo import development_records, verified_image
                reference = next((photo for photo in development_records(ROOT / 'Laboratorio/Experimentos' / run)
                                  if manifest_image_path(photo) == clean['image']), None)
                if reference:
                    verified_image(reference)
                    clean.update(truth_rows=reference['truth_rows'], split='val')
        return clean
    if action != 'train':
        raise ValueError('Acción desconocida.')
    source = next((item for item in data['runs'] if item['id'] == config.get('source') and item['ready']), None)
    version = next((item for item in data.get('datasets', []) if item['id'] == config.get('source') and item['state'] in ('lista_modulos', 'lista_niveles')), None)
    if not source and not version:
        raise ValueError('Elige un ensayo terminado o una copia de anotaciones revisada.')
    source_report = (version or {}).get('report') or (source or {}).get('manifest', {})
    if source_report.get('clases') == ['Nivel']:
        raise ValueError('V3 requiere exportador, validaciones, partición y evaluación compatibles antes de entrenar desde el panel.')
    purpose = config.get('purpose', '')
    if not isinstance(purpose, str) or len(purpose) > 1000:
        raise ValueError('El propósito del ensayo debe tener como máximo 1000 caracteres.')
    reference = config.get('reference_run', '')
    if reference and not any(run['id'] == reference for run in data['runs']):
        raise ValueError('El ensayo de referencia ya no está disponible.')
    name = config.get('name', '')
    if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}', name):
        raise ValueError('Usa un nombre de 1–48 letras, números, guiones o guiones bajos.')
    clean.update(purpose=purpose.strip(), reference_run=reference, source=(version or source)['id'], source_kind='dataset' if version else 'run', epochs=number(config, 'epochs', 1, 500, True),
                 scope=version.get('scope', 'Modulo') if version else source['manifest'].get('scope', 'Modulo'),
                 batch=number(config, 'batch', 1, 4, True), lr=number(config, 'lr', 0.000001, 0.1),
                 seed=number(config, 'seed', 0, 999999, True),
                 run=f"{name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}")
    return clean


def job_status(path):
    status = read_json(path / 'estado.json', {})
    if 'image' in status.get('config', {}):
        status['config'] = {**status['config'], 'image': current_image_path(status['config']['image'])}
    log = path / 'salida.log'
    if log.exists():
        with log.open('rb') as handle:
            handle.seek(max(0, log.stat().st_size - 6000))
            status['log'] = handle.read().decode('utf-8', errors='replace')
    result = read_json(path / 'resultado.json')
    if status.get('config', {}).get('action') == 'train':
        progress = read_json(path / 'progreso.json', {})
        run_name = status['config'].get('run', '')
        if re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', run_name):
            run = ROOT / 'Laboratorio/Experimentos' / run_name
            environment = read_json(run / 'entorno.json', {})
            progress['device'] = environment.get('gpu') or ('CPU' if environment else None)
            # Sólo imágenes generadas por el ensayo; nunca fotos de la reserva.
            previews = list((run / 'entrenamiento').glob('val_batch*_pred.jpg'))
            if not previews:
                previews = list((run / 'entrenamiento').glob('train_batch*.jpg'))
            if previews:
                preview = max(previews, key=lambda item: item.stat().st_mtime)
                progress['preview_url'] = file_url(preview) + '&v=' + str(preview.stat().st_mtime_ns)
                progress['preview_kind'] = 'validation' if preview.name.startswith('val_') else 'training'
        status['progress'] = progress
    if result:
        status['result'] = result
        if result.get('imagen'):
            status['image_url'] = file_url(path / result['imagen'])
        if result.get('occupancy_image') == 'paulo_senal.jpg':
            status['occupancy_image_url'] = file_url(path / 'paulo_senal.jpg')
        for field, filename in (('occupancy_edges', 'paulo_bordes.png'),
                                ('occupancy_filtered_edges', 'paulo_bordes_niveles.png')):
            if result.get(field + '_image') == filename:
                status[field + '_url'] = file_url(path / filename)
    return status


def file_stamp(path):
    try:
        stat = path.stat()
        return stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size
    except FileNotFoundError:
        return None


def recent_jobs():
    """Read active jobs every poll; revalidate completed files at most every 15s."""
    paths = sorted(JOBS.glob('*/estado.json'), key=lambda path: path.stat().st_mtime_ns, reverse=True)[:30]
    with JOB_CACHE_LOCK:
        keep = {path.parent for path in paths}
        for path in list(JOB_CACHE):
            if path not in keep:
                del JOB_CACHE[path]
        statuses = []
        now = time.monotonic()
        for state in paths:
            path = state.parent
            cached = JOB_CACHE.get(path)
            if cached and now < cached['recheck_at']:
                statuses.append(cached['status'])
                continue
            dependencies = [path / name for name in ('estado.json', 'salida.log', 'resultado.json', 'progreso.json')]
            if cached:
                dependencies.extend(cached['run_files'])
            signature = tuple(file_stamp(item) for item in dependencies)
            if cached and cached['signature'] == signature:
                cached['recheck_at'] = now + FINISHED_JOB_RECHECK_SECONDS
                statuses.append(cached['status'])
                continue
            status = job_status(path)
            if status.get('state') in ('done', 'error', 'interrupted'):
                run_files = []
                run_name = status.get('config', {}).get('run', '')
                if status.get('config', {}).get('action') == 'train' and re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', run_name):
                    run = ROOT / 'Laboratorio/Experimentos' / run_name
                    run_files = [run / 'entorno.json', run / 'entrenamiento']
                    preview = status.get('progress', {}).get('preview_url')
                    if preview:
                        requested = parse_qs(urlparse(preview).query)['path'][0]
                        run_files.append(ROOT / requested)
                # Keep the pre-read stamps so writes during a read force revalidation.
                base_signature = signature[:4]
                JOB_CACHE[path] = {'signature': base_signature + tuple(file_stamp(item) for item in run_files),
                                   'status': status, 'run_files': run_files,
                                   'recheck_at': now + FINISHED_JOB_RECHECK_SECONDS}
            else:
                JOB_CACHE.pop(path, None)
            statuses.append(status)
        return statuses


def launch(config):
    global ACTIVE
    with LOCK:
        if ACTIVE:
            raise ValueError('Hay un trabajo en curso. Espera a que termine para usar la GPU.')
        clean = validate(config, catalog())
        job_id = uuid.uuid4().hex
        job = JOBS / job_id
        job.mkdir(parents=True)
        if clean['action'] == 'train':
            run = ROOT / 'Laboratorio/Experimentos' / clean['run']
            run.mkdir()
            source_dir = datasets.version_path(clean['source']) if clean['source_kind'] == 'dataset' else ROOT / 'Laboratorio/Experimentos' / clean['source']
            shutil.copy2(source_dir / 'snapshot_cvat.json', run / 'snapshot_cvat.json')
            version_file = source_dir / ('version.json' if clean['source_kind'] == 'dataset' else 'version_datos.json')
            if version_file.exists():
                shutil.copy2(version_file, run / 'version_datos.json')
                shutil.copy2(source_dir / 'particion.json', run / 'particion.json')
            write_json(run / 'config_interfaz.json', clean)
        write_json(job / 'solicitud.json', clean)
        write_json(job / 'estado.json', {'id': job_id, 'state': 'running', 'config': clean,
                                       'started_at': datetime.now(timezone.utc).isoformat()})
        ACTIVE = job_id
        invalidate_catalog()
        threading.Thread(target=monitor, args=(job, clean), daemon=True).start()
        return job_status(job)


def monitor(job, config):
    global ACTIVE
    status = read_json(job / 'estado.json', {'id': job.name, 'config': config})
    try:
        with (job / 'salida.log').open('wb') as output:
            process = subprocess.Popen([str(PYTHON), '-u', str(HERE / 'panel_worker.py'), str(job)],
                                       cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            code = process.wait()
        status.update(state='done' if code == 0 else 'error', exit_code=code)
    except Exception as error:
        status.update(state='error', error=str(error))
    finally:
        status['finished_at'] = datetime.now(timezone.utc).isoformat()
        write_json(job / 'estado.json', status)
        with LOCK:
            ACTIVE = None
        invalidate_catalog()


def allowed_file(requested):
    """Authorize an image without constructing the experiment catalog."""
    requested = current_image_path(requested)
    path = (ROOT / requested).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        return None
    parts = experiment_parts(requested)
    if path.is_relative_to((ROOT / datasets.LIDER_EXPRESS / 'imagenes_ordenadas').resolve()):
        if any(path == (ROOT / 'Datos' / item['archivo']).resolve()
               for item in datasets.lider_express_inventory().values()):
            return path
    if uploaded_photo(requested):
        return path
    if requested in {relative(ROOT / 'Datos' / item['archivo']) for item in inventory()}:
        return path
    if requested in {'Datos/' + item['archivo'] for item in datasets.package_inventory().values()}:
        return path
    if len(parts) == 4 and parts[0] in ('Laboratorio/Experimentos', 'Historico/Experimentos'):
        run = ROOT / parts[0] / parts[1]
        if parts[2] == 'comparaciones' and (run / 'manifest.json').is_file():
            allowed = {f"{Path(item['imagen']).stem}_{item['split']}.jpg"
                       for item in read_json(run / 'evaluacion_por_imagen.json', [])}
            if parts[3] in allowed:
                return path
        # Training previews are generated by a run, never raw reserved photos.
        if (parts[2] == 'entrenamiento' and (run / 'manifest.json').is_file() and
                re.fullmatch(r'(?:val_batch\d+_pred|train_batch\d+)\.jpg', parts[3])):
            return path
        if (parts[1] == 'panel_pruebas' and parts[3] in ('prediccion.jpg', 'paulo_senal.jpg', 'paulo_bordes.png', 'paulo_bordes_niveles.png') and
                (JOBS / parts[2] / 'estado.json').is_file()):
            return path
    return None


@lru_cache(maxsize=64)
def thumbnail(path, modified, size):
    """Bounded in-memory previews; originals and dataset files stay intact."""
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail((280, 210))
        output = BytesIO()
        image.convert('RGB').save(output, format='JPEG', quality=72)
        return output.getvalue()


class Handler(BaseHTTPRequestHandler):
    def reply_catalog(self):
        _, plain, compressed, etag = cached_catalog()
        unchanged = any(tag.strip().removeprefix('W/') in (etag.removeprefix('W/'), '*')
                        for tag in self.headers.get('If-None-Match', '').split(','))
        self.send_response(304 if unchanged else 200)
        self.send_header('Cache-Control', 'private, no-cache')
        self.send_header('ETag', etag)
        self.send_header('Vary', 'Accept-Encoding')
        if unchanged:
            self.end_headers()
            return
        use_gzip = len(plain) > 1024 and 'gzip' in self.headers.get('Accept-Encoding', '')
        body = compressed if use_gzip else plain
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        if use_gzip:
            self.send_header('Content-Encoding', 'gzip')
        self.end_headers()
        self.wfile.write(body)

    def reply(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        compressed = len(body) > 1024 and 'gzip' in self.headers.get('Accept-Encoding', '')
        if compressed:
            body = gzip.compress(body, compresslevel=1)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Vary', 'Accept-Encoding')
        if compressed:
            self.send_header('Content-Encoding', 'gzip')
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        host = self.headers.get('Host', '')
        allowed = {f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'}
        return host in allowed and self.headers.get('Origin', f'http://{host}') == f'http://{host}'

    def do_GET(self):
        if not self.local_request():
            self.reply({'error': 'Solo se permite el acceso local.'}, 403)
            return
        url = urlparse(self.path)
        try:
            if url.path == '/api/health':
                return self.reply({'status': 'ok'})
            if url.path == '/api/catalog':
                return self.reply_catalog()
            if url.path == '/api/datasets/sources':
                return self.reply(datasets.import_sources())
            if url.path == '/api/datasets/sync':
                return self.reply(CVAT_SYNC.status())
            if url.path == '/api/jobs':
                return self.reply(recent_jobs())
            if url.path == '/api/datasets/drawing':
                query = parse_qs(url.query)
                try:
                    preview = datasets.drawing_preview(*(query.get(key, [''])[0]
                                                        for key in ('id', 'photo', 'shape_id', 'job_id')))
                except ValueError as error:
                    return self.reply({'error': str(error)}, 400)
                preview['image_url'] = file_url(ROOT / preview.pop('image_path'))
                return self.reply(preview)
            if url.path == '/':
                path = HERE / 'panel.html'
            elif url.path.startswith('/static/'):
                static = (HERE / 'static').resolve()
                path = (static / url.path.removeprefix('/static/')).resolve()
                if not path.is_relative_to(static) or path.suffix not in ('.css', '.js') or not path.is_file():
                    return self.reply({'error': 'Recurso no disponible.'}, 404)
            elif url.path == '/file':
                query = parse_qs(url.query)
                path = allowed_file(query.get('path', [''])[0])
                if path is None or not path.is_file():
                    return self.reply({'error': 'Archivo no disponible.'}, 404)
            else:
                return self.reply({'error': 'Ruta no disponible.'}, 404)
            preview = url.path == '/file' and query.get('preview') == ['thumb']
            stat = path.stat()
            etag = f'"{stat.st_mtime_ns:x}-{stat.st_size:x}-{"thumb" if preview else "full"}"'
            if self.headers.get('If-None-Match') == etag:
                self.send_response(304)
                self.send_header('ETag', etag)
                self.send_header('Cache-Control', 'private, no-cache')
                self.end_headers()
                return
            body = thumbnail(str(path), stat.st_mtime_ns, stat.st_size) if preview else path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg' if preview else mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'private, no-cache')
            self.send_header('ETag', etag)
            self.end_headers()
            self.wfile.write(body)
        except ValueError as error:
            self.reply({'error': str(error)}, 400)
        except Exception as error:
            self.reply({'error': str(error)}, 500)

    def do_POST(self):
        if not self.local_request():
            return self.reply({'error': 'Origen no autorizado.'}, 403)
        if self.path == '/api/photos':
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_UPLOAD_BYTES:
                    self.close_connection = True
                    return self.reply({'error': 'La foto debe pesar como máximo 15 MB.'}, 413)
                if self.headers.get_content_type() not in ('image/jpeg', 'image/png', 'image/webp', 'application/octet-stream'):
                    self.close_connection = True
                    return self.reply({'error': 'Elige una foto JPG, PNG o WebP.'}, 415)
                from urllib.parse import unquote
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ValueError('La carga quedó incompleta. Vuelve a subir la foto.')
                return self.reply(save_uploaded_photo(body, unquote(self.headers.get('X-Filename', 'Mi foto'))), 201)
            except (ValueError, TypeError) as error:
                return self.reply({'error': str(error)}, 400)
            except Exception:
                return self.reply({'error': 'No se pudo guardar la foto. Reintenta la carga.'}, 500)
        if self.path not in ('/api/jobs', '/api/datasets/import', '/api/datasets/approve',
                             '/api/datasets/archive', '/api/datasets/restore',
                             '/api/datasets/sync',
                             '/api/models/archive', '/api/models/restore', '/api/runs/decision'):
            return self.reply({'error': 'Ruta no disponible.'}, 404)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192:
                raise ValueError('Solicitud inválida.')
            config = json.loads(self.rfile.read(length))
            if not isinstance(config, dict):
                raise ValueError('Se requiere una solicitud de objeto JSON.')
            if self.path == '/api/runs/decision':
                with LOCK:
                    result = record_decision(config)
                return self.reply(result)
            if self.path.startswith('/api/models/'):
                with LOCK:
                    result = change_model_visibility(config, archive=self.path.endswith('/archive'))
                return self.reply(result)
            if self.path.startswith('/api/datasets/'):
                if self.path.endswith('/sync'):
                    if config.get('enabled') is True:
                        raise ValueError('CVAT está en modo manual. Usa el botón para traer las anotaciones.')
                    result = CVAT_SYNC.configure(config)
                    return self.reply(result)
                actions = {'/import': datasets.import_lot, '/approve': datasets.approve,
                           '/archive': datasets.archive, '/restore': datasets.restore}
                with DATA_LOCK:
                    result = actions['/' + self.path.rsplit('/', 1)[1]](config)
                    if self.path.endswith('/import'):
                        CVAT_SYNC.configure({'jobs': [source['job_id'] for source in result['sources']],
                                             'validation': [image['imagen_id'] for image in result['report']['imagenes'] if image['split'] == 'val'],
                                             'enabled': False}, result)
                    elif self.path.endswith('/archive'):
                        for source in list(CVAT_SYNC.sources.values()):
                            if source.get('version_id') == config['id']:
                                CVAT_SYNC.configure({**source, 'enabled': False})
                invalidate_catalog()
                return self.reply(result, 201 if self.path.endswith('/import') and not result.get('import_reused') else 200)
            self.reply(launch(config), 202)
        except (ValueError, KeyError, TypeError) as error:
            self.reply({'error': str(error)}, 400)
        except Exception as error:
            self.reply({'error': str(error)}, 500)

    def log_message(self, *_):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8090)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    JOBS.mkdir(parents=True, exist_ok=True)
    for state in JOBS.glob('*/estado.json'):
        value = read_json(state)
        if value['state'] == 'running':
            value.update(state='interrupted', error='El servidor se reinició; revisar la salida antes de repetir el ensayo.')
            write_json(state, value)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    CVAT_SYNC.pause_all()
    print(f'Panel de modelos: http://localhost:{args.port}', flush=True)
    try:
        server.serve_forever()
    finally:
        CVAT_SYNC.close()
        server.server_close()
