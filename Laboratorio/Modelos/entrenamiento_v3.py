"""Entrenamiento geométrico V3 independiente: una clase Nivel y solo desarrollo."""
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import shutil
import sys

import preparacion_v3 as preparation
import selecciones_v3 as selections
from archivo_historico import within
import almacenamiento_datos as storage

CRITERION = 'geometria_nivel_v3'
DEFAULTS = dict(name='v3_niveles_yolo26n_base', epochs=100, imgsz=640,
                batch=2, lr=0.001, seed=42, patience=20,
                model='Modelos/preentrenados/yolo26n-seg.pt')
DEVELOPMENT = ('train', 'val_real', 'val_sintetica')


def initial_model(root, model):
    general = {f'Modelos/preentrenados/{name}-seg.pt' for name in ('yolo11n', 'yolo26n')}
    if isinstance(model, str) and model in general:
        path = root / model
        if not path.is_file():
            raise ValueError('El modelo general ya no está disponible.')
        return {'kind': 'general', 'model': model, 'sha256': preparation.digest(path)}
    if not isinstance(model, str) or not re.fullmatch(
            r'Experimentos/[A-Za-z0-9_-]+/entrenamiento/weights/best\.pt', model):
        raise ValueError('Elige un modelo general o el best.pt de un ensayo geométrico V3 terminado.')
    path = root / model
    if not within(root, path, root / 'Experimentos') or not path.is_file():
        raise ValueError('Los pesos iniciales deben estar dentro de los ensayos locales.')
    run = path.parents[2]
    manifest = preparation.read(run / 'manifest.json')
    metrics = preparation.read(run / 'metricas_geometria_v3.json')
    if (manifest.get('criterion', {}).get('version') != CRITERION
            or manifest.get('clases') != ['Nivel'] or manifest.get('preparing')
            or metrics.get('criterion') != CRITERION or metrics.get('test_used') is not False):
        raise ValueError('Solo se admite un best.pt geométrico V3 terminado, de una clase Nivel.')
    return {'kind': 'fine_tune', 'model': model, 'sha256': preparation.digest(path),
            'parent_run': run.name, 'parent_manifest_sha256': preparation.digest(run / 'manifest.json'),
            'resume': False}


def verify_initial_model(root, config):
    if config.get('initial_model'):
        if initial_model(root, config['model']) != config['initial_model']:
            raise ValueError('El modelo inicial cambió desde la configuración. No se reutilizarán pesos distintos.')


def subset(image):
    return image['split'] if image['split'] == 'train' else image['split'] + (
        '_real' if image['origen'] == 'real' else '_sintetica')


def export_path(root, source):
    if not isinstance(source, str) or not re.fullmatch(
            r'Datos/Preparados/V3/v3_\d{8}_\d{6}_[a-f0-9]{8}/exportacion_[a-f0-9]{8}', source):
        raise ValueError('Elige una exportación V3 revisada.')
    path = root / source
    if not within(root, path, root / preparation.OUTPUT):
        raise ValueError('Ruta de exportación V3 inválida.')
    if (path / 'INCOMPLETA.txt').exists() or not (path / 'manifest.json').is_file():
        raise ValueError('La exportación está incompleta o ya no existe.')
    return path


def exports(root):
    result = []
    for file in (root / preparation.OUTPUT).glob('v3_*/exportacion_*/manifest.json'):
        try:
            value = preparation.read(file)
            if ((file.parent / 'INCOMPLETA.txt').exists() or value.get('reviewed') is not True
                    or value.get('reviewed_visible_regions') is not True
                    or value.get('policy_version') != preparation.PREPARATION_POLICY):
                continue
            result.append({'id': file.parent.relative_to(root).as_posix(),
                           'copy': value['source_version'], 'created_at': value['created_at'],
                           'author': value['author'], 'counts': value['counts'],
                           'partition_id': value['partition_id'], 'partition_note': value.get('partition_note', ''),
                           'excluded': len(value['excluded'])})
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return sorted(result, key=lambda row: row['created_at'], reverse=True)


def catalog(root, *, include_pilot=True):
    runs = []
    for path in (root / 'Experimentos').glob('*/manifest.json'):
        try:
            manifest = preparation.read(path)
            if manifest.get('criterion', {}).get('version') != CRITERION:
                continue
            import csv
            history_file = path.parent / 'entrenamiento/results.csv'
            history = []
            if history_file.exists():
                with history_file.open(encoding='utf-8-sig') as stream:
                    for row in csv.DictReader(stream):
                        try:
                            values = {k.strip(): float(v) for k, v in row.items()}
                            if all(math.isfinite(v) for v in values.values()):
                                history.append(values)
                        except (ValueError, TypeError):
                            pass
            metrics = path.parent / 'metricas_geometria_v3.json'
            runs.append({'id': path.parent.name, 'history': history,
                         'selection_id': (manifest.get('selection') or {}).get('id'),
                         'metrics': preparation.read(metrics) if metrics.exists() else None,
                         'decision': preparation.read(path.parent / 'decision_modelo.json').get('current') if (path.parent / 'decision_modelo.json').exists() else None,
                         'ready': metrics.exists(), 'source': manifest['source_export'],
                         'best': (path.parent / 'entrenamiento/weights/best.pt').exists()})
        except (OSError, ValueError, KeyError, TypeError):
            continue
    initial_models = [{'id': DEFAULTS['model'], 'label': 'YOLO26n-seg · preentrenado general'},
                      {'id': 'Modelos/preentrenados/yolo11n-seg.pt', 'label': 'YOLO11n-seg · preentrenado general'}]
    from visibilidad_modelos import archived
    hidden = archived(root)
    initial_models += [{'id': 'Experimentos/' + r['id'] + '/entrenamiento/weights/best.pt',
                       'label': r['id'] + ' · best.pt · ajuste fino'} for r in sorted(runs, key=lambda r: r['id'], reverse=True) if r['ready'] and r['best'] and 'Experimentos/' + r['id'] + '/entrenamiento/weights/best.pt' not in hidden]
    from visibilidad_modelos import current
    released = current(root)
    if released:
        initial_models.sort(key=lambda m: m['id'] != released['model'])
        for model in initial_models:
            if model['id'] == released['model']:
                model['label'] = 'V3 vigente · best.pt · próximo refuerzo'
    return {'supported': True, 'exports': exports(root), 'runs': runs, 'selections': selections.catalog(root),
            'initial_models': initial_models,
            'vision_release': released,
            'module_pilot': selections.module_pilot(root) if include_pilot else None,
            'defaults': {**DEFAULTS, **({'model': released['model'], 'lr': .0001, 'epochs': 40, 'patience': 10} if released else {})}, 'criterion': CRITERION, 'test_enabled': False}


def labels_text(image):
    lines = []
    for shape in image['shapes']:
        p = shape['points']
        coords = preparation.normalized_points(p, image['width'], image['height'])
        lines.append('0 ' + ' '.join(format(v, '.12g') for v in coords))
    return '\n'.join(lines) + '\n'


def validate_export(root, source):
    """Vincula exportación, revisión, snapshot y partición; verifica desarrollo sin abrir test."""
    path = export_path(root, source)
    manifest = preparation.read(path / 'manifest.json')
    report = preparation.read(path.parent / 'informe.json')
    reference = preparation.partition_reference(root, manifest.get('partition_path', preparation.PARTITION))
    part = preparation.partition(root, reference)
    frozen = preparation.read(path.parent / 'particion.json')
    snapshot = preparation.read(path.parent / 'snapshot_cvat.json')
    if frozen != part or preparation.digest(root / reference) != manifest.get('partition_sha256'):
        raise ValueError('La partición no coincide con la exportación revisada.')
    if (report.get('partition_path', preparation.PARTITION) != reference
            or report.get('partition_sha256') != manifest.get('partition_sha256')
            or manifest.get('partition_id') != part.get('id')):
        raise ValueError('La referencia de partición no coincide entre informe y exportación.')
    if (manifest.get('reviewed') is not True or manifest.get('reviewed_visible_regions') is not True
            or manifest.get('policy_version') != preparation.PREPARATION_POLICY
            or not isinstance(manifest.get('author'), str) or len(manifest['author'].strip()) < 2
            or manifest.get('source_version') != path.parent.name
            or report.get('id') != path.parent.name):
        raise ValueError('Falta una revisión humana válida de esta exportación V3.')
    derived = preparation.analyze(part, snapshot)
    # Las copias anteriores a la migración de nombres no registraban estos
    # dos campos; solo se completan si el snapshot confirma la identidad vieja.
    recorded = []
    for image, observed in zip(report['images'], derived['images']):
        row = dict(image)
        if 'cvat_task_id' not in row and observed.get('cvat_task_id') == row.get('task_id'):
            row['cvat_task_id'] = observed['cvat_task_id']
        if 'cvat_name' not in row and observed.get('cvat_name') == row.get('name'):
            row['cvat_name'] = observed['cvat_name']
        recorded.append(row)
    if len(report['images']) != len(derived['images']) or recorded != derived['images']:
        raise ValueError('El informe ya no coincide con su snapshot de CVAT.')
    expected = [i for i in derived['images'] if i['eligible']]
    included = [{**{k: i[k] for k in ('name', 'split', 'origen', 'familia', 'grupo_escena', 'sha256')},
                 'shapes': [{k: s[k] for k in ('id', 'delimitacion', 'occluded')} for s in i['shapes']],
                 'warnings': i.get('warnings', [])} for i in expected]
    excluded = [{'name': i['name'], 'split': i['split'], 'issues': i['issues']}
                for i in derived['images'] if not i['eligible']]
    counts = dict(Counter(subset(i) for i in expected))
    if manifest.get('included') != included or manifest.get('excluded') != excluded or manifest.get('counts') != counts:
        raise ValueError('Las inclusiones o exclusiones cambiaron desde la revisión.')
    if not counts.get('train') or not counts.get('val_real'):
        raise ValueError('Faltan fotos de entrenamiento o validación real.')
    dev = [i for i in expected if i['split'] in ('train', 'val')]
    for split in DEVELOPMENT:
        rows = [i for i in dev if subset(i) == split]
        if len({Path(i['name']).stem for i in rows}) != len(rows):
            raise ValueError('Dos imágenes comparten el mismo nombre de etiqueta en ' + split)
        expected_list = ''.join('./images/' + split + '/' + i['name'] + '\n' for i in rows)
        if rows and (path / (split + '.txt')).read_text(encoding='utf-8') != expected_list:
            raise ValueError('La lista de desarrollo no coincide con su partición revisada.')
        for image in rows:
            photo = storage.read_path(root, (path / 'images' / split / image['name']).relative_to(root).as_posix())
            label = path / 'labels' / split / (Path(image['name']).stem + '.txt')
            if preparation.digest(photo) != image['sha256'] or label.read_text(encoding='utf-8') != labels_text(image):
                raise ValueError('Imagen o etiquetas modificadas: ' + image['name'])
    return path, manifest, dev


def validate_config(root, config):
    from visibilidad_modelos import archived
    if config.get('model') in archived(root):
        raise ValueError('El modelo inicial está archivado; recupéralo para usarlo de nuevo.')
    path, manifest, images = validate_export(root, config.get('source'))
    _, selection = selections.apply(root, config['source'], images, config.get('selection'))
    model = config.get('model')
    initialization = initial_model(root, model)
    if selection and selection.get('required_initial_model') and model != selection['required_initial_model']:
        raise ValueError('Este afinado debe partir del best.pt indicado en su plan; conserva el modelo de partida propuesto.')
    if selection and selection.get('required_initial_model_sha256') and initialization['sha256'] != selection['required_initial_model_sha256']:
        raise ValueError('Los pesos iniciales ya no coinciden con el plan de afinado.')
    name = config.get('name', '')
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,48}', name):
        raise ValueError('Nombre: usa 1–48 letras sin tildes, números o guiones.')
    clean = {'action': 'train', 'pipeline': CRITERION, 'project_version': 'v3',
             'source_kind': 'v3_export', 'source': config['source'], 'model': model,
             'name': name, 'scope': 'Nivel_geometria', 'source_manifest_sha256': preparation.digest(path / 'manifest.json'),
             'initial_model': initialization}
    for key, low, high, integer in (('epochs', 1, 500, True), ('imgsz', 320, 960, True),
                                    ('batch', 1, 4, True), ('lr', .000001, .1, False),
                                    ('seed', 0, 999999, True), ('patience', 1, 100, True)):
        value = config.get(key, DEFAULTS.get(key))
        if (type(value) not in (int, float) or not math.isfinite(value)
                or not low <= value <= high or integer and int(value) != value):
            raise ValueError(f'{key}: valor inválido ({low}–{high}).')
        clean[key] = int(value) if integer else value
    if clean['imgsz'] % 32:
        raise ValueError('La resolución debe ser múltiplo de 32.')
    purpose = config.get('purpose', '')
    if not isinstance(purpose, str) or len(purpose) > 1000:
        raise ValueError('El propósito admite hasta 1000 caracteres.')
    clean['purpose'] = purpose.strip()
    if selection:
        clean.update(selection=selection['id'], selection_sha256=selection['sha256'])
    clean['run'] = f"{name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{__import__('uuid').uuid4().hex[:4]}"
    return clean


def register_run(root, config, run):
    """Registro ligero; las copias y la orientación corren en el worker con seguimiento."""
    run.mkdir(exist_ok=False)
    preparation.write(run / 'config_interfaz.json', config)
    preparation.write(run / 'manifest.json', {'criterion': {'version': CRITERION},
        'clases': ['Nivel'], 'scope': 'Nivel_geometria', 'source_export': config['source'],
        'initial_model': config.get('initial_model'),
        'preparing': True, 'test_used': False})


def freeze_run(root, config, run, progress=None):
    verify_initial_model(root, config)
    source, receipt, images = validate_export(root, config['source'])
    if preparation.digest(source / 'manifest.json') != config['source_manifest_sha256']:
        raise ValueError('La exportación cambió desde la configuración.')
    images, selection = selections.apply(root, config['source'], images, config.get('selection'), config.get('selection_sha256'))
    if run.exists():
        if (not preparation.read(run / 'manifest.json').get('preparing')
                or preparation.read(run / 'config_interfaz.json') != config
                or any(p.name not in ('manifest.json', 'config_interfaz.json') for p in run.iterdir())):
            raise ValueError('El ensayo ya contiene datos; usa un ensayo nuevo.')
    else:
        run.mkdir()
    for name in ('snapshot_cvat.json', 'particion.json', 'informe.json'):
        shutil.copy2(source.parent / name, run / name)
    shutil.copy2(source / 'manifest.json', run / 'exportacion_revisada.json')
    if selection:
        preparation.write(run / 'seleccion_entrenamiento.json', selection)
    dataset = run / 'dataset_niveles'
    fingerprints = {}
    preprocessing = []
    for index, image in enumerate(images, 1):
        split = subset(image)
        for kind, filename in (('images', image['name']), ('labels', Path(image['name']).stem + '.txt')):
            target = dataset / kind / split / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            if kind == 'images':
                origin = storage.read_path(root, (source / kind / split / filename).relative_to(root).as_posix())
                target, record = copy_oriented(origin, target, image)
                preprocessing.append(record)
            else:
                shutil.copy2(source / kind / split / filename, target)
            fingerprints[target.relative_to(run).as_posix()] = preparation.digest(target)
        if progress and (index % 10 == 0 or index == len(images)):
            progress('preparing', prepared_images=index, total_images=len(images))
    for split in ('val_real', 'val_sintetica'):
        (dataset / (split + '.yaml')).write_text(
            'path: ' + json.dumps(dataset.resolve().as_posix()) + '\ntrain: images/train\nval: images/' + split + '\nnames:\n  0: Nivel\n', encoding='utf-8')
    preparation.write(run / 'manifest.json', {
        'criterion': {'version': CRITERION}, 'clases': ['Nivel'], 'scope': 'Nivel_geometria',
        'source_export': config['source'], 'source_manifest_sha256': config['source_manifest_sha256'],
        'initial_model': config.get('initial_model'),
        'review': {'author': receipt['author'], 'reviewed': True},
        'counts': {key: sum(subset(i) == key for i in images) for key in DEVELOPMENT},
        'source_counts': receipt['counts'], 'selection': selection,
        'test_used': False, 'files': fingerprints, 'preprocessing': preprocessing,
        'imagenes': [{**i, 'subset': subset(i)} for i in images]})
    preparation.write(run / 'config_interfaz.json', config)


def copy_oriented(source, target, image):
    """Las coordenadas de CVAT ya están orientadas; girar píxeles, nunca los polígonos."""
    from PIL import Image, ImageOps
    with Image.open(source) as photo:
        orientation = photo.getexif().get(274, 1)
        oriented = ImageOps.exif_transpose(photo)
        if oriented.size != (image['width'], image['height']):
            raise ValueError('Dimensiones incompatibles tras orientar: ' + image['name'])
        if orientation != 1:
            # PNG conserva los píxeles decodificados sin otra compresión con pérdida.
            target = target.with_suffix('.png')
            oriented.convert('RGB').save(target, format='PNG', compress_level=1)
        else:
            shutil.copy2(source, target)
    return target, {'source_name': image['name'], 'prepared_name': target.name,
                    'source_sha256': image['sha256'], 'prepared_sha256': preparation.digest(target),
                    'orientation': orientation, 'operation': 'exif_transpose_to_png' if orientation != 1 else 'copy',
                    'polygon_coordinates_changed': False}


def verify_run(run):
    manifest = preparation.read(run / 'manifest.json')
    for relative, expected in manifest['files'].items():
        # Runs use either the canonical laboratory location or its frozen alias.
        # Derive the project root also for isolated validation fixtures.
        root = run.parent.parent
        if run.parent.name == 'Experimentos' and root.name in ('Laboratorio', 'Historico'):
            root = root.parent
        logical = run / relative
        path = storage.read_path(root, logical.relative_to(root).as_posix())
        if not within(root, logical, run) or preparation.digest(path) != expected:
            raise ValueError('Cambió la copia congelada del ensayo: ' + relative)


def train_arguments(config, run, device):
    args = dict(data=str(run / 'dataset_niveles/val_real.yaml'), epochs=config['epochs'],
                imgsz=config['imgsz'], batch=config['batch'], device=device, workers=0,
                seed=config['seed'], deterministic=True, optimizer='AdamW', lr0=config['lr'],
                patience=config['patience'], amp=False, overlap_mask=False, mask_ratio=2,
                mosaic=0., mixup=0., copy_paste=0., degrees=3., translate=.03, scale=.10,
                shear=0., perspective=0., fliplr=0., flipud=0.,
                hsv_h=.01, hsv_s=.2, hsv_v=.2, cache=False, plots=True,
                project=str(run), name='entrenamiento', exist_ok=False, resume=False)
    if config.get('initial_model', {}).get('kind') == 'fine_tune':
        args.update(warmup_epochs=1.0, warmup_bias_lr=0.0)
    return args


def check_runtime(root, config):
    """Prevuelo sin épocas, optimizador, gradientes ni cambios de pesos."""
    from copy import deepcopy
    verify_initial_model(root, config)
    from PIL import Image, ImageOps
    from entrenar_niveles import load_runtime, load_model
    path, manifest, images = validate_export(root, config['source'])
    images, selection = selections.apply(root, config['source'], images, config.get('selection'), config.get('selection_sha256'))
    for image in images:
        photo_path = storage.read_path(root, (path / 'images' / subset(image) / image['name']).relative_to(root).as_posix())
        with Image.open(photo_path) as photo:
            oriented = ImageOps.exif_transpose(photo)
            oriented.load()
            if oriented.size != (image['width'], image['height']):
                raise ValueError('Dimensiones u orientación incompatibles: ' + image['name'])
    torch, runtime = load_runtime()
    model = load_model(root / config['model'], runtime)
    if config.get('initial_model', {}).get('kind') == 'fine_tune' and set(model.names.values()) != {'Nivel'}:
        raise ValueError('El checkpoint inicial no contiene exclusivamente Nivel.')
    from ultralytics.nn.tasks import SegmentationModel
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    network = SegmentationModel(cfg=deepcopy(model.model.yaml), nc=1, ch=3, verbose=False)
    network.load(model.model, verbose=False)
    transferred = None
    if config.get('initial_model', {}).get('kind') == 'fine_tune':
        original = model.model.state_dict()
        current = network.state_dict()
        if set(original) != set(current) or not all(torch.equal(original[k], current[k]) for k in original):
            raise ValueError('El ajuste fino no conserva todos los tensores iniciales.')
        transferred = len(original)
    network.to(device).eval()
    with torch.inference_mode():
        network(torch.zeros(config['batch'], 3, config['imgsz'], config['imgsz'], device=device))
    if network.model[-1].nc != 1:
        raise ValueError('La arquitectura no se adaptó a la clase única.')
    return {'checked_at': datetime.now(timezone.utc).isoformat(), 'source': config['source'],
            'manifest_sha256': preparation.digest(path / 'manifest.json'),
            'counts': {key: sum(subset(i) == key for i in images) for key in DEVELOPMENT},
            'selection': selection,
            'decoded_development_images': len(images), 'device': device,
            'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'ultralytics': runtime.__version__, 'model': config['model'], 'classes': ['Nivel'],
            'batch': config['batch'], 'imgsz': config['imgsz'], 'forward_passed': True,
            'initial_model': config.get('initial_model'), 'transferred_tensors_verified': transferred,
            'optimizer_steps': 0, 'test_images_opened': 0, 'training_started': False}


def epoch_progress_callbacks(progress):
    """La validación final puede repetir on_fit_epoch_end; no es otra época."""
    started = completed = 0

    def start(trainer):
        nonlocal started
        started = max(started, trainer.epoch + 1)
        progress('training', current_epoch=started)

    def end(trainer):
        nonlocal completed
        epoch = trainer.epoch + 1
        if completed < epoch <= started:
            completed = epoch
            progress('training', completed_epochs=completed)

    return start, end


def execute(root, job, progress):
    """Solo el worker invoca esta función tras pulsar Entrenar."""
    from entrenar_niveles import load_runtime, load_model
    config = preparation.read(job / 'solicitud.json')
    verify_initial_model(root, config)
    run = root / 'Experimentos' / config['run']
    if preparation.read(run / 'manifest.json').get('preparing'):
        freeze_run(root, config, run, progress)
    verify_run(run)
    torch, runtime = load_runtime()
    device = 0 if torch.cuda.is_available() else 'cpu'
    preparation.write(run / 'entorno.json', {'python': sys.version, 'torch': torch.__version__,
        'ultralytics': runtime.__version__, 'device': device,
        'gpu': torch.cuda.get_device_name(0) if device == 0 else None})
    model = load_model(root / config['model'], runtime)
    epoch_start, epoch_end = epoch_progress_callbacks(progress)
    model.add_callback('on_train_epoch_start', epoch_start)
    model.add_callback('on_fit_epoch_end', epoch_end)
    args = train_arguments(config, run, device)
    preparation.write(run / 'parametros_v3.json', args)
    progress('training')
    model.train(**args)
    best = run / 'entrenamiento/weights/best.pt'
    if not best.is_file():
        raise ValueError('El ensayo no produjo best.pt.')
    trained = load_model(best, runtime)
    if set(trained.names.values()) != {'Nivel'}:
        raise ValueError('Los pesos no contienen exclusivamente la clase Nivel.')
    progress('evaluating')
    results = {}
    manifest = preparation.read(run / 'manifest.json')
    for split in ('val_real', 'val_sintetica'):
        if not manifest['counts'].get(split):
            continue
        metrics = trained.val(data=str(run / 'dataset_niveles' / (split + '.yaml')),
            split='val', imgsz=config['imgsz'], batch=1, workers=0, device=device,
            conf=.001, iou=.7, max_det=300, overlap_mask=False, mask_ratio=2,
            augment=False, plots=True, project=str(run), name=split, exist_ok=False)
        results[split] = {k: float(v) for k, v in metrics.results_dict.items()}
    verify_run(run)
    preparation.write(run / 'metricas_geometria_v3.json', {
        'criterion': CRITERION, 'sets': results, 'test_used': False,
        'selection': 'best.pt por validación real; sintéticas como diagnóstico separado',
        'occupancy_evaluated': False})
    if (manifest.get('selection') or {}).get('policy') == selections.GEOMETRY_POLICY:
        from evaluar_escenas_refuerzo_v3 import evaluate
        evaluate(root, config['source'], best, run / 'evaluacion_por_escenas.json', model=trained, device=device)
    preparation.write(job / 'resultado.json', {'run': config['run'], 'pipeline': CRITERION,
                                              'metrics': results, 'test_used': False})
    progress('done')
