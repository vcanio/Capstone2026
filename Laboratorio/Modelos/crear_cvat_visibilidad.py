"""Crear el proyecto CVAT de revisión de visibilidad, sin tocar V3 ni test.

Reanudación conservadora: una carga interrumpida exige inspección manual,
para no duplicar tareas ni repetir una carga cuyo estado se desconoce.
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path

from cvat_sdk import make_client
from cvat_sdk.core.proxies.tasks import ResourceType
from datos_modelos import CvatReader

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'Datos/Preparados/V3/Visibilidad_foto_20261102'
INVENTORY = DATA / 'inventario_pendiente.json'
RECEIPT = DATA / 'cvat_revision.json'
STAGE = ROOT / '.tmp/visibilidad_foto_cvat_20261102'
NAME = 'Activo - Clasificacion visibilidad'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(value):
    tmp = RECEIPT.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(RECEIPT)


def main():
    inventory = json.loads(INVENTORY.read_text(encoding='utf-8'))
    rows = inventory['images']
    if inventory['test_included'] is not False or len(rows) != 405:
        raise ValueError('Inventario de desarrollo inesperado.')
    for row in rows:
        if row['split'] not in ('train', 'val') or row['etiqueta'] != 'pendiente':
            raise ValueError('El inventario contiene etiquetas o particiones inesperadas.')
        if digest(ROOT / row['path']) != row['sha256']:
            raise ValueError('Fuente modificada: ' + row['name'])
    reader = CvatReader()
    projects = [p for p in reader.listing('/projects') if p['name'] == NAME]
    if RECEIPT.exists():
        receipt = json.loads(RECEIPT.read_text(encoding='utf-8'))
        if len(projects) != 1 or projects[0]['id'] != receipt['project_id']:
            raise ValueError('El proyecto existente no coincide con el recibo.')
    else:
        if projects:
            raise ValueError('Ya existe un proyecto sin recibo; revisar antes de continuar.')
        spec = {'name': 'Evaluabilidad', 'type': 'tag', 'color': '#3b82f6', 'attributes': [
            {'name': 'decision', 'mutable': False, 'input_type': 'select', 'default_value': 'pendiente',
             'values': ['pendiente', 'apta', 'no_apta']},
            {'name': 'motivo', 'mutable': False, 'input_type': 'select', 'default_value': 'sin_definir',
             'values': ['sin_definir', 'persona', 'carro', 'cajas', 'otro_obstaculo', 'recorte', 'calidad', 'geometria_incierta']},
        ]}
        project = reader.request('/projects', payload={'name': NAME, 'labels': [spec]})
        receipt = {'project_id': project['id'], 'status': 'en_preparacion',
                   'inventory_sha256': digest(INVENTORY), 'tasks': []}
        save(receipt)
    if receipt['inventory_sha256'] != digest(INVENTORY):
        raise ValueError('El inventario cambió desde la creación del proyecto.')
    print('Proyecto de visibilidad:', receipt['project_id'], flush=True)
    access = json.loads((ROOT / 'Infraestructura/CVAT/acceso_local.json').read_text(encoding='utf-8-sig'))
    with make_client('http://localhost:8082', credentials=(access['username'], access['password'])) as client:
        for split, expected in [('train', 336), ('val', 69)]:
            selected = [row for row in rows if row['split'] == split]
            if len(selected) != expected or len({row['cvat_name'] for row in selected}) != expected:
                raise ValueError('Recuento o nombres duplicados: ' + split)
            existing = next((item for item in receipt['tasks'] if item['split'] == split), None)
            if existing:
                if existing['status'] == 'verificada':
                    print('Tarea ya verificada:', existing['task_id'], flush=True)
                    continue
                raise ValueError('Carga interrumpida: inspeccionar la tarea antes de reanudar: ' + str(existing))
            stage = STAGE / split
            stage.mkdir(parents=True, exist_ok=True)
            for row in selected:
                dest = stage / row['cvat_name']
                source = ROOT / row['path']
                if not dest.exists():
                    os.link(source, dest)
                if not os.path.samefile(source, dest):
                    raise ValueError('El archivo temporal no coincide con su fuente: ' + row['name'])
            task = client.tasks.create(spec={'name': 'Revision visibilidad - ' + split,
                                             'project_id': receipt['project_id'], 'subset': split})
            item = {'split': split, 'task_id': task.id, 'status': 'carga_iniciada', 'expected': expected}
            receipt['tasks'].append(item)
            save(receipt)
            print('Cargando', split, expected, 'imágenes en tarea', task.id, flush=True)
            task.upload_data(resources=[str(stage / row['cvat_name']) for row in selected],
                             resource_type=ResourceType.LOCAL,
                             params={'image_quality': 100, 'sorting_method': 'lexicographical'},
                             wait_for_completion=True, status_check_period=3)
            meta = reader.request(f'/tasks/{task.id}/data/meta')
            frames = {frame['name']: index for index, frame in enumerate(meta['frames'])}
            if len(frames) != expected or set(frames) != {row['cvat_name'] for row in selected}:
                raise ValueError('Los fotogramas cargados no coinciden: ' + split)
            data_id = reader.request(f'/tasks/{task.id}')['data']
            verify_script = ("import hashlib,json,sys;from pathlib import Path;"
                             "p=Path('/home/django/data/data')/sys.argv[1]/'raw';"
                             "print(json.dumps({x.name:hashlib.file_digest(x.open('rb'),'sha256').hexdigest() "
                             "for x in p.iterdir() if x.is_file() and x.name!='index.json'}))")
            checked = subprocess.run(['docker', 'exec', 'walmart_cvat_server', 'python', '-c',
                                      verify_script, str(data_id)], capture_output=True, text=True, check=True)
            raw_hashes = json.loads(checked.stdout)
            if any(raw_hashes.get(row['cvat_name']) != row['sha256'] for row in selected):
                raise ValueError('Los bytes cargados en CVAT no coinciden: ' + split)
            annotation = reader.request(f'/tasks/{task.id}/annotations')
            if annotation['shapes'] or annotation['tags'] or annotation['tracks']:
                raise ValueError('La tarea nueva no está vacía: ' + split)
            item.update(status='verificada', frames=frames, source_hashes_verified=expected)
            save(receipt)
            print('Tarea verificada:', task.id, flush=True)
    receipt['status'] = 'lista_para_revision'
    save(receipt)
    print('Proyecto listo para revisión; sin etiquetas asignadas.', flush=True)


if __name__ == '__main__':
    main()
