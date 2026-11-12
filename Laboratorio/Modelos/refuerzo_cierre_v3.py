"""Extensión aditiva del ensayo oficial: tres casos nuevos y repaso congelado."""
from collections import Counter
import copy
from pathlib import Path

import preparacion_v3 as p

BASE = 'Datos/Preparados/V3/Refuerzos/revision_equipo_20261110'
PLAN = BASE + '/cierre/plan_particion.json'
CLOSURE = 'Datos/Registros/CVAT/revisiones/cierre_delimitacion_cierre_yolo_20261110/snapshot_cvat.json'
ASSIGNMENT = 'Datos/Preparados/V3/Refuerzos/revision_geometria_20261104/cierre/asignacion_recepcion_331.json'
INGRESS = 'Datos/Registros/CVAT/revisiones/ingreso_cierre_yolo_20261110/recibo.json'


def summarize(rows):
    return {split: {'imagenes': len(items), 'reales': sum(i['origen'] == 'real' for i in items),
                    'sinteticas': sum(i['origen'] == 'sintetica' for i in items),
                    'grupos': len({i['grupo_escena'] for i in items})}
            for split in ('train', 'val') if (items := [r for r in rows if r['split'] == split])}


def incoming_rows(root):
    sources = p.read(root / BASE / 'plan_anotacion.json')['fotos_para_anotar']
    assignments = {r['id']: r for r in p.read(root / ASSIGNMENT)['fotos']}
    ingress = p.read(root / INGRESS)
    frames = {r['id']: (t['task_id'], r) for t in ingress['tareas'] for r in t['correspondencia']}
    if {r['id_recepcion'] for r in sources} != {'R065', 'R202', 'R211'}:
        raise ValueError('El cierre admite únicamente los tres casos revisados.')
    rows = []
    for source in sources:
        iid = source['id_recepcion']
        tid, frame = frames[iid]
        assignment = assignments[iid]
        if source['split'] != 'train' or assignment['split'] != 'train' or frame['split'] != 'train':
            raise ValueError('Un caso nuevo no conserva su asignación train.')
        if source['sha256'] != frame['sha256'] or source['escena'] != assignment['scene']:
            raise ValueError('Cambió la identidad o escena de un caso nuevo.')
        rows.append({'imagen_id': iid, 'name': frame['nombre'], 'path': source['original_para_cvat'],
                     'sha256': source['sha256'], 'width': frame['dimensiones_orientadas'][0],
                     'height': frame['dimensiones_orientadas'][1], 'familia': assignment['block'],
                     'grupo_escena': assignment['scene'], 'origen': 'real', 'split': 'train',
                     'task_id': tid, 'role': 'refuerzo_cierre', 'review_id': iid})
    return rows


def validate_rows(rows):
    names, hashes, scenes, families = set(), set(), {}, {}
    for row in rows:
        if row['split'] not in ('train', 'val') or row['origen'] not in ('real', 'sintetica'):
            raise ValueError('El cierre solo admite desarrollo y procedencia identificada.')
        if row['name'] in names or row['sha256'] in hashes:
            raise ValueError('El cierre contiene imágenes duplicadas.')
        names.add(row['name'])
        hashes.add(row['sha256'])
        for mapping, key in ((scenes, row['grupo_escena']), (families, row['familia'])):
            if mapping.setdefault(key, row['split']) != row['split']:
                raise ValueError('Una escena o familia cruza train y validación.')


def get_plan(root, part):
    if part.get('plan_path') != PLAN or part.get('plan_sha256') != p.digest(root / PLAN):
        raise ValueError('Cambió el plan versionado del cierre.')
    plan = p.read(root / PLAN)
    if plan.get('approved_by') != 'Vicente' or not plan.get('authorization'):
        raise ValueError('Falta el cierre humano de anotaciones y preparación.')
    for path, digest in plan['evidence_sha256'].items():
        if p.digest(root / path) != digest:
            raise ValueError('Cambió la evidencia del cierre: ' + path)
    return plan


def validate_partition(root, reference, value):
    plan = get_plan(root, value)
    if value.get('schema_version') != 5 or value.get('id') != Path(reference).parent.name:
        raise ValueError('Identidad de partición de cierre incompatible.')
    if value.get('base_partition_path') != plan['parent_partition']:
        raise ValueError('La extensión debe proceder de la partición oficial congelada.')
    parent = p.read(root / plan['parent_manifest'])
    # La evidencia fija los bytes de la partición y del manifiesto del ensayo
    # terminado. No volver a resolver todo el catálogo histórico por cada
    # validación de esta extensión: sus filas se contrastan aquí con el padre.
    base = p.read(root / plan['parent_partition'])
    if base.get('schema_version') != 4:
        raise ValueError('El padre del cierre debe ser el refuerzo oficial congelado.')
    included = {r['name']: r for r in parent['imagenes']}
    old_rows = [r for r in base['imagenes'] if r['name'] in included]
    if len(old_rows) != len(included):
        raise ValueError('Falta cobertura del ensayo oficial.')
    keys = ('name', 'sha256', 'split', 'origen', 'familia', 'grupo_escena')
    if any(any(r[k] != included[r['name']][k] for k in keys) for r in old_rows):
        raise ValueError('Cambió una asignación o identidad ya aprendida/evaluada.')
    expected = old_rows + incoming_rows(root)
    if value.get('imagenes') != expected or value.get('resumen') != summarize(expected):
        raise ValueError('El cierre debe conservar íntegros train y val oficiales y añadir solo tres train.')
    validate_rows(expected)
    train = [r['name'] for r in expected if r['split'] == 'train']
    val = [r['name'] for r in expected if r['split'] == 'val']
    if train != plan['selected_train'] or val != plan['selected_val']:
        raise ValueError('La selección difiere del plan de cierre.')
    for row in expected:
        if Path(row['path']).name != row['name']:
            raise ValueError('Nombre de imagen incompatible con su ruta.')
    for row in expected[len(old_rows):]:
        p.v3_image_path(root, row['path'])
    return value


def source_snapshot(root, part):
    plan = get_plan(root, part)
    snapshot = copy.deepcopy(p.read(root / plan['parent_snapshot']))
    closure = p.read(root / CLOSURE)
    if snapshot['labels'] != closure['labels']:
        raise ValueError('El cierre y el padre usan etiquetas distintas.')
    ingress = p.read(root / INGRESS)
    tasks = {t['task_id']: t for t in ingress['tareas']}
    for bundle in closure['tasks']:
        tid = bundle['task']['id']
        if tid not in tasks or bundle['task']['project_id'] != 11:
            raise ValueError('Tarea del cierre fuera de la recepción verificada.')
        bundle = copy.deepcopy(bundle)
        bundle['partition_task_id'] = tid
        bundle['frames_by_name'] = {f['name']: i for i, f in enumerate(bundle['meta']['frames'])}
        bundle['jobs'] = [{'id': tasks[tid]['job_id'], 'start_frame': 0,
                           'stop_frame': len(bundle['meta']['frames']) - 1}]
        snapshot['tasks'].append(bundle)
    if len({b.get('partition_task_id', b['task']['id']) for b in snapshot['tasks']}) != len(snapshot['tasks']):
        raise ValueError('Tareas duplicadas en el snapshot compuesto.')
    return snapshot


def prepare_partition(root, reference, part, client=None):
    from refuerzo_geometria_v3 import save_preparation
    return save_preparation(root, reference, part, source_snapshot(root, part))


def choose(root, receipt, images, value):
    part = p.partition(root, receipt['partition_path'])
    plan = get_plan(root, part)
    if (value.get('plan_sha256') != part['plan_sha256']
            or value.get('required_initial_model') != plan['initial_model']
            or value.get('required_initial_model_sha256') != plan['initial_model_sha256']):
        raise ValueError('El cierre debe partir del best.pt oficial registrado en su plan.')
    train = [r['name'] for r in images if r['split'] == 'train']
    val = [r['name'] for r in images if r['split'] == 'val']
    if train != plan['selected_train'] or val != plan['selected_val']:
        raise ValueError('Falta repaso, refuerzo o validación congelada en la exportación.')
    if p.digest(root / plan['baseline_path']) != value.get('baseline_sha256'):
        raise ValueError('Cambió la referencia de evaluación del modelo padre.')
    return train, []
