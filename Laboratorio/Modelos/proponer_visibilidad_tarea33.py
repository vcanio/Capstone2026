"""Proponer en CVAT las 51 fotos de desarrollo visualmente revisadas de tarea 33.

No modifica la tarea original ni asigna aprobación humana. No incluye test.
Una ejecución parcial requiere inspección y no se reintenta automáticamente.
"""
import hashlib
import json
from pathlib import Path
import sys

import requests
from datos_modelos import CvatReader

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'Datos/Preparados/V3/Visibilidad_foto_20261102'
FILE = DATA / 'propuestas_tarea33.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(value):
    temp = FILE.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(FILE)


def main():
    if FILE.exists():
        raise ValueError('Ya existe un recibo de propuestas. No se repetirá la operación.')
    inventory = read(DATA / 'inventario_pendiente.json')
    source_hash = hashlib.sha256((DATA / 'inventario_pendiente.json').read_bytes()).hexdigest()
    receipt = read(DATA / 'cvat_revision.json')
    visual = read(ROOT / '.tmp/revision_oclusion_20261101/inventario.json')
    if receipt['status'] != 'lista_para_revision' or receipt['inventory_sha256'] != source_hash:
        raise ValueError('El proyecto de revisión o inventario no están verificados.')
    rows = [row for row in inventory['images'] if row['cvat_task_id'] == 33]
    if len(rows) != 51 or {r['name'] for r in rows} != {r['name'] for r in visual}:
        raise ValueError('La revisión visual no coincide con los 51 casos de desarrollo.')
    tasks = {item['split']: item for item in receipt['tasks']}
    counts = {split: sum(r['split'] == split for r in rows) for split in ('train', 'val')}
    if counts != {'train': 41, 'val': 10}:
        raise ValueError('La separación de las propuestas no coincide con la partición.')
    targets = []
    for row in rows:
        source = ROOT / row['path']
        with source.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != row['sha256']:
                raise ValueError('La fuente visual cambió: ' + row['name'])
        reasons = [reason for reason in ('persona', 'carro', 'cajas') if '_' + reason in row['name']]
        if len(reasons) != 1:
            raise ValueError('Revisar motivo manualmente: ' + row['name'])
        task = tasks[row['split']]
        targets.append({'name': row['name'], 'source_task': 33, 'source_frame': row['frame'],
                        'split': row['split'], 'task_id': task['task_id'],
                        'frame': task['frames'][row['cvat_name']], 'sha256': row['sha256'],
                        'proposed_decision': 'no_apta', 'proposed_reason': reasons[0]})
    reader = CvatReader()
    labels = [x for x in reader.listing('/labels?project_id=12') if x['name'] == 'Evaluabilidad' and x['type'] == 'tag']
    if len(labels) != 1:
        raise ValueError('La etiqueta de revisión no coincide.')
    label = labels[0]
    attributes = {item['name']: item['id'] for item in label['attributes']}
    if set(attributes) != {'decision', 'motivo'}:
        raise ValueError('Atributos de revisión inesperados.')
    before = {str(task['task_id']): reader.request(f"/tasks/{task['task_id']}/annotations") for task in receipt['tasks']}
    original = reader.request('/tasks/33/annotations')
    for target in targets:
        if any(tag['frame'] == target['frame'] for tag in before[str(target['task_id'])]['tags']):
            raise ValueError('Ya existe una etiqueta en la imagen: ' + target['name'])
    backup = DATA / 'anotaciones_revision_antes_propuestas.json'
    with backup.open('x', encoding='utf-8') as stream:
        json.dump(before, stream, ensure_ascii=False, indent=2)
    proposal = {'status': 'carga_iniciada', 'project_id': receipt['project_id'],
                'inventory_sha256': source_hash, 'visual_review': '.tmp/revision_oclusion_20261101/inventario.json',
                'targets': targets, 'completed_tasks': []}
    save(proposal)  # El bloqueo de revisión existe antes de enviar la primera etiqueta.
    session = requests.Session()
    session.trust_env = False
    session.headers['Authorization'] = 'Token ' + reader.token
    for task in receipt['tasks']:
        tid = task['task_id']
        if reader.request(f'/tasks/{tid}/annotations') != before[str(tid)]:
            raise ValueError(f'La tarea {tid} cambió antes de la carga; no se sobrescribirá.')
        batch = [item for item in targets if item['task_id'] == tid]
        tags = [{'frame': item['frame'], 'label_id': label['id'], 'source': 'auto', 'attributes': [
            {'spec_id': attributes['decision'], 'value': item['proposed_decision']},
            {'spec_id': attributes['motivo'], 'value': item['proposed_reason']}]} for item in batch]
        response = session.patch(f'http://localhost:8082/api/tasks/{tid}/annotations?action=create',
                                 json={'version': before[str(tid)]['version'], 'tags': tags, 'shapes': [], 'tracks': []}, timeout=120)
        response.raise_for_status()
        after = reader.request(f'/tasks/{tid}/annotations')
        expected_frames = {x['frame'] for x in batch}
        created = [tag for tag in after['tags'] if tag['frame'] in expected_frames]
        if len(created) != len(batch) or {t['frame'] for t in created} != expected_frames:
            raise ValueError('La cantidad de propuestas recibidas no coincide: ' + str(tid))
        for item in batch:
            tag = next(t for t in created if t['frame'] == item['frame'])
            values = {a['spec_id']: a['value'] for a in tag['attributes']}
            if tag['label_id'] != label['id'] or values.get(attributes['decision']) != 'no_apta' or values.get(attributes['motivo']) != item['proposed_reason']:
                raise ValueError('Una propuesta no coincide: ' + item['name'])
            item['tag_id'] = tag['id']
        old = before[str(tid)]
        if after['shapes'] != old['shapes'] or after['tracks'] != old['tracks']:
            raise ValueError('Cambió geometría inesperada en la tarea nueva.')
        old_tags = {x['id']: x for x in old['tags']}
        if any(next((x for x in after['tags'] if x['id'] == i), None) != tag for i, tag in old_tags.items()):
            raise ValueError('Cambió una etiqueta preexistente.')
        proposal['completed_tasks'].append(tid)
        save(proposal)
        print('Propuestas verificadas en tarea', tid, ':', len(batch), flush=True)
    if reader.request('/tasks/33/annotations') != original:
        raise ValueError('La tarea original 33 cambió durante la operación; revisar antes de confirmar.')
    proposal['status'] = 'verificadas'
    proposal['original_task_33_unchanged'] = True
    save(proposal)
    print('51 propuestas listas para revisión humana; ninguna confirmada.', flush=True)


if __name__ == '__main__':
    main()
