"""Galería de consulta limitada a las fotos de entrenamiento de una selección V3."""
from pathlib import Path
from urllib.parse import urlencode
import json

import entrenamiento_v3 as training
import preparacion_v3 as prep
import selecciones_v3 as selections


def metadata(root, identifier):
    selected = prep.read(selections.path_for(root, identifier))
    source = training.export_path(root, selected.get('source'))
    receipt = prep.read(source / 'manifest.json')
    if (receipt.get('reviewed') is not True or receipt.get('reviewed_visible_regions') is not True
            or receipt.get('policy_version') != prep.PREPARATION_POLICY):
        raise ValueError('La fuente requiere una revisión válida.')
    report = prep.read(source.parent / 'informe.json')
    images = [i for i in report['images'] if i['eligible'] and i['split'] in ('train', 'val')]
    images, record = selections.apply(root, selected['source'], images, identifier)
    included = {r['name']: r for r in receipt['included'] if r['split'] == 'train'}
    photos = []
    for image in sorted((r for r in images if r['split'] == 'train'), key=lambda r: r['name']):
        if included.get(image['name'], {}).get('sha256') != image['sha256']:
            raise ValueError('La foto ya no coincide con su exportación revisada.')
        query = urlencode({'selection': identifier, 'photo': image['name']})
        photos.append({'name': image['name'], 'family': image['familia'], 'scene': image['grupo_escena'],
                       'origin': image['origen'], 'sha256': image['sha256'],
                       'width': image['width'], 'height': image['height'], 'shapes': image['shapes'],
                       'hard_example': image['name'] in record.get('hard_examples', record.get('target_images', [])),
                       'cvat_url': (f"http://localhost:8082/tasks/{image.get('cvat_task_id', image['task_id'])}/jobs/{image['job_id']}?frame={image['frame']}"
                                    if record['policy'] != selections.CLEAN_POLICY and all(k in image for k in ('task_id', 'job_id', 'frame')) else None),
                       'url': '/api/v3/selection-image?' + query,
                       'thumbnail': '/api/v3/selection-image?' + query + '&preview=thumb'})
    if len(photos) != record['development_counts']['train']:
        raise ValueError('El recuento de la galería no coincide con la selección.')
    return source, record, photos


def page(root, identifier):
    _, record, photos = metadata(root, identifier)
    data = {'id': identifier, 'label': record['label'], 'photos': photos,
            'synthetic_label': 'Variantes vacías' if record['policy'] == selections.POLICY else 'Variantes sintéticas'}
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    html = (Path(__file__).parent / 'galeria_seleccion_v3.html').read_text(encoding='utf-8')
    return html.replace('@@GALLERY_DATA@@', payload).encode('utf-8')


def image_path(root, identifier, name):
    source, _, photos = metadata(root, identifier)
    photo = next((p for p in photos if p['name'] == name), None)
    if photo is None or Path(name).name != name:
        raise ValueError('Esta foto no forma parte del entrenamiento seleccionado.')
    path = (source / 'images/train' / name).resolve()
    if not path.is_relative_to((source / 'images/train').resolve()) or prep.digest(path) != photo['sha256']:
        raise ValueError('La imagen no coincide con la copia revisada.')
    return path
