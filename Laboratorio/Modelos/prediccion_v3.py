"""Pruebas geométricas V3 en validación y fotos propias; reserva final separada."""
from pathlib import Path
import math
import re

import entrenamiento_v3 as training
import preparacion_v3 as preparation
from archivo_historico import within

MIN_CONFIDENCE = 0.60

def run_path(root, model_id):
    if not isinstance(model_id, str) or not re.fullmatch(
            r'Experimentos/[A-Za-z0-9_-]{1,100}/entrenamiento/weights/(?:best|last)\.pt', model_id):
        raise ValueError('Elige los pesos best o last de un ensayo V3 terminado.')
    model = (root / model_id).resolve()
    run = root / 'Experimentos' / model_id.split('/')[1]
    if (not within(root, run, root / 'Experimentos')
            or not model.is_relative_to(run.resolve()) or not model.is_file()):
        raise ValueError('Los pesos V3 ya no están disponibles.')
    manifest = preparation.read(run / 'manifest.json')
    if (manifest.get('criterion', {}).get('version') != training.CRITERION
            or manifest.get('clases') != ['Nivel'] or not (run / 'metricas_geometria_v3.json').is_file()):
        raise ValueError('Se requiere un modelo geométrico V3 con evaluación terminada.')
    return run, manifest


def catalog(root):
    from visibilidad_modelos import archived, current
    hidden = archived(root)
    released = current(root)
    models, runs = [], []
    for file in (root / 'Experimentos').glob('*/metricas_geometria_v3.json'):
        run = file.parent
        try:
            manifest = preparation.read(run / 'manifest.json')
            if manifest.get('criterion', {}).get('version') != training.CRITERION:
                continue
            config = preparation.read(run / 'config_interfaz.json')
            photos = [{'name': i['name'], 'origin': i['origen'], 'scene': i['grupo_escena']}
                      for i in manifest['imagenes'] if i['split'] == 'val']
            photos.sort(key=lambda i: (i['origin'] != 'real', i['name']))
            runs.append({'id': run.name, 'photos': photos})
            for checkpoint in ('best', 'last'):
                model = run / 'entrenamiento/weights' / (checkpoint + '.pt')
                if model.is_file():
                    models.append({'id': model.relative_to(root).as_posix(), 'run': run.name,
                                   'checkpoint': checkpoint, 'imgsz': config['imgsz'],
                                   'name': run.name + (' · Mejor (best)' if checkpoint == 'best' else ' · Último (last)')})
        except (OSError, ValueError, KeyError, TypeError):
            continue
    models.sort(key=lambda m: (m['run'], m['checkpoint'] == 'best'), reverse=True)
    if released:
        for model in models:
            if model['id'] == released['model']:
                model['name'] = 'V3 vigente · Mejor (best)'
    return {'models': [m for m in models if m['id'] not in hidden],
            'archived_models': [m for m in models if m['id'] in hidden],
            'runs': runs, 'occupancy_enabled': False, 'final_test_enabled': False,
            'minimum_confidence': MIN_CONFIDENCE}


def validation_image(root, model_id, photo):
    run, manifest = run_path(root, model_id)
    row = next((i for i in manifest['imagenes'] if i['split'] == 'val' and i['name'] == photo), None)
    if row is None:
        raise ValueError('Elige una foto de validación; entrenamiento y reserva final quedan fuera.')
    record = next((i for i in manifest.get('preprocessing', []) if i['source_name'] == row['name']), None)
    name = record['prepared_name'] if record else row['name']
    path = run / 'dataset_niveles/images' / training.subset(row) / name
    label = run / 'dataset_niveles/labels' / training.subset(row) / (Path(name).stem + '.txt')
    for file in (path, label):
        if (not file.resolve().is_relative_to(run.resolve()) or not file.is_file()
                or preparation.digest(file) != manifest['files'].get(file.relative_to(run).as_posix())):
            raise ValueError('Cambió la copia de validación. Revisa la integridad del ensayo.')
    return path, label, row


def validate(root, config, uploaded_photo):
    from visibilidad_modelos import archived
    if config.get('model') in archived(root):
        raise ValueError('Este modelo está archivado; recupéralo antes de iniciar otra prueba.')
    run, manifest = run_path(root, config.get('model'))
    if config.get('occupancy') or config.get('occupancy_version', 'v1') != 'v1':
        raise ValueError('Esta prueba V3 localiza niveles; el cálculo de ocupación todavía no está integrado.')
    def number(key, low, high, integer=False):
        value = config.get(key)
        if (type(value) not in (int, float) or not math.isfinite(value)
                or not low <= value <= high or integer and int(value) != value):
            if key == 'conf':
                raise ValueError('Confianza V3: el mínimo aceptado es 0,60; usa un valor entre 0,60 y 0,99.')
            raise ValueError(key + ': valor fuera de rango.')
        return int(value) if integer else value
    clean = {'action': 'predict', 'pipeline': training.CRITERION, 'project_version': 'v3',
             'model': config['model'], 'scope': 'Nivel_geometria',
             'imgsz': number('imgsz', 320, 1280, True),
             'conf': number('conf', MIN_CONFIDENCE, .99), 'nms': number('nms', .1, .95)}
    if clean['imgsz'] % 32:
        raise ValueError('La resolución debe ser múltiplo de 32.')
    if config.get('source_mode') == 'validation':
        image, label, row = validation_image(root, config['model'], config.get('photo'))
        clean.update(image=image.relative_to(root).as_posix(), image_source='v3_validation',
                     image_name=row['name'], origin=row['origen'], split='val',
                     truth_rows=label.read_text(encoding='utf-8').splitlines())
    elif config.get('source_mode') == 'upload':
        upload = uploaded_photo(config.get('image'))
        if not upload:
            raise ValueError('Sube una foto propia antes de analizarla.')
        part = preparation.read(root / preparation.PARTITION)
        digest = upload.get('sha256_original')
        if digest and any(i['split'] == 'test' and i['sha256'] == digest for i in part['imagenes']):
            raise ValueError('Esta imagen pertenece a la reserva final. Usa validación o una foto nueva.')
        if digest and any(i['split'] == 'train' and i['sha256'] == digest for i in manifest['imagenes']):
            raise ValueError('Esta foto se usó para entrenar el modelo. Elige validación o una foto nueva.')
        clean.update(image=upload['id'], image_source='upload', image_name=upload['name'])
    else:
        raise ValueError('Elige validación o subir una foto propia.')
    return clean
