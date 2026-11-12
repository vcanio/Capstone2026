"""Cargar una sola vez el borrador visual en las tareas de revisión, sin aprobarlo."""
import csv
import hashlib
import json
from pathlib import Path
import requests

from datos_modelos import CvatReader, CVAT
import revision_visibilidad_cvat as review
from visibilidad_foto import source_path, sha256

DATA = review.DATA
FILE = review.SECOND_PROPOSALS


def save(data):
    temp = FILE.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(FILE)


def main():
    if FILE.exists():
        raise ValueError('Ya existe un recibo: inspeccionar antes de reintentar.')
    inventory = review.read(DATA / 'inventario_pendiente.json')
    receipt = review.read(DATA / 'cvat_revision.json')
    with (DATA / 'propuestas_revision_visual_borrador.csv').open(encoding='utf-8-sig', newline='') as stream:
        draft = list(csv.DictReader(stream))
    lookup = {row['name']: row for row in inventory['images'] if row['cvat_task_id'] != 33}
    if len(draft) != 354 or len(lookup) != 354 or {r['nombre'] for r in draft} != set(lookup):
        raise ValueError('El borrador no cubre exactamente las 354 fotos restantes.')
    if receipt['inventory_sha256'] != review.digest(DATA / 'inventario_pendiente.json'):
        raise ValueError('El inventario de revisión cambió.')
    tasks = {item['split']: item for item in receipt['tasks']}
    targets = []
    for item in draft:
        row = lookup[item['nombre']]
        task = tasks[row['split']]
        frame = task['frames'][row['cvat_name']]
        if (item['sha256'] != row['sha256'] or item['particion'] != row['split'] or
                int(item['task_revision']) != task['task_id'] or int(item['frame_revision']) != frame or
                sha256(source_path(row)) != row['sha256']):
            raise ValueError('Imagen o identidad no coincide: ' + row['name'])
        if (item['propuesta'], item['motivo']) not in (('apta', 'sin_definir'), ('pendiente', 'sin_definir'), ('no_apta', 'recorte')):
            raise ValueError('Propuesta inválida: ' + row['name'])
        targets.append({'name': row['name'], 'split': row['split'], 'task_id': task['task_id'],
                        'frame': frame, 'sha256': row['sha256'], 'proposed_decision': item['propuesta'],
                        'proposed_reason': item['motivo']})
    reader = CvatReader()
    previous = review.collect(reader, inventory, receipt)
    if not previous['proposals_confirmed'] or previous['issues']:
        raise ValueError('La revisión previa tiene incidencias o dejó de estar confirmada.')
    label = next(x for x in reader.listing(f"/labels?project_id={receipt['project_id']}") if x['name'] == 'Evaluabilidad' and x['type'] == 'tag')
    attrs = {a['name']: a['id'] for a in label['attributes']}
    before = {str(t['task_id']): reader.request(f"/tasks/{t['task_id']}/annotations") for t in receipt['tasks']}
    original = reader.request('/tasks/33/annotations')
    for item in targets:
        if any(t['frame'] == item['frame'] for t in before[str(item['task_id'])]['tags']):
            raise ValueError('Ya existe una decisión en ' + item['name'])
    backup = DATA / 'anotaciones_revision_antes_segundo_lote.json'
    with backup.open('x', encoding='utf-8') as stream:
        json.dump(before, stream, ensure_ascii=False, indent=2)
    proposal = {'status': 'carga_iniciada', 'project_id': receipt['project_id'],
                'inventory_sha256': receipt['inventory_sha256'],
                'draft_sha256': hashlib.sha256((DATA / 'propuestas_revision_visual_borrador.csv').read_bytes()).hexdigest(),
                'targets': targets, 'completed_tasks': []}
    save(proposal)  # El lector bloquea el lote antes de crear cualquier etiqueta.
    session = requests.Session()
    session.trust_env = False
    session.headers['Authorization'] = 'Token ' + reader.token
    for task in receipt['tasks']:
        tid = task['task_id']
        if reader.request(f'/tasks/{tid}/annotations') != before[str(tid)]:
            raise ValueError('Las anotaciones cambiaron durante la operación.')
        batch = [r for r in targets if r['task_id'] == tid]
        tags = [{'frame': r['frame'], 'label_id': label['id'], 'source': 'auto', 'attributes': [
            {'spec_id': attrs['decision'], 'value': r['proposed_decision']},
            {'spec_id': attrs['motivo'], 'value': r['proposed_reason']}]} for r in batch]
        response = session.patch(f'{CVAT}/tasks/{tid}/annotations?action=create',
                                 json={'version': before[str(tid)]['version'], 'tags': tags, 'shapes': [], 'tracks': []}, timeout=120)
        response.raise_for_status()
        after = reader.request(f'/tasks/{tid}/annotations')
        old = before[str(tid)]
        old_by_id = {x['id']: x for x in old['tags']}
        if after['shapes'] != old['shapes'] or after['tracks'] != old['tracks'] or any(
                next((x for x in after['tags'] if x['id'] == key), None) != value for key, value in old_by_id.items()):
            raise ValueError('Una anotación anterior cambió durante la carga.')
        for item in batch:
            found = [t for t in after['tags'] if t['frame'] == item['frame']]
            if len(found) != 1:
                raise ValueError('No hay exactamente una propuesta en ' + item['name'])
            values = {a['spec_id']: a['value'] for a in found[0]['attributes']}
            if values.get(attrs['decision']) != item['proposed_decision'] or values.get(attrs['motivo']) != item['proposed_reason']:
                raise ValueError('Los valores de la propuesta no coinciden: ' + item['name'])
            item['tag_id'] = found[0]['id']
        proposal['completed_tasks'].append(tid)
        save(proposal)
        print('Verificadas:', tid, len(batch), flush=True)
    if reader.request('/tasks/33/annotations') != original:
        raise ValueError('Cambió la tarea original 33.')
    proposal['status'] = 'verificadas'
    proposal['original_task_33_unchanged'] = True
    save(proposal)
    state = review.collect(reader, inventory, receipt)
    if not state['proposals_confirmed'] or state['proposal_batches']['revision_visual']['confirmed'] or state['issues']:
        raise ValueError('El estado de confirmación requiere inspección.')
    print('Segundo lote listo para revisión; la confirmación anterior sigue vigente.')


if __name__ == '__main__':
    main()
