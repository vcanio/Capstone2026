"""Cierre autorizado con casos revisados y migración explícita de escenas de val."""
import copy
import csv
import re
from pathlib import Path

import preparacion_v3 as p
from refuerzo_cierre_v3 import summarize, validate_rows

BASE = 'Datos/Preparados/V3/Refuerzos/revision_equipo_20261110/cierre_ampliado'
PLAN = BASE + '/plan_particion.json'
PARENT = 'Datos/Registros/Particiones/v3_cierre_yolo_20261110/particion.json'
REVIEW = 'Datos/Registros/Revisiones/revision_equipo_20261110/fotos_revisadas.csv'
LATEST_REVIEW = 'Datos/Registros/Revisiones/revision_candidato_cierre_20261110/revision.json'


def reviewed_hashes(root):
    with (root / REVIEW).open(encoding='utf-8-sig', newline='') as stream:
        hashes = {r['sha256'] for r in csv.DictReader(stream)}
    return hashes | {r['contexto']['input_sha256'] for r in p.read(root / LATEST_REVIEW)['fotos']}


def promoted_rows(rows, hashes):
    """Migrar componentes completos relacionados con fotos revisadas; sin sorteo."""
    train = {r['name'] for r in rows if r['split'] == 'train' or r['sha256'] in hashes}
    while True:
        scenes = {r['grupo_escena'] for r in rows if r['name'] in train}
        families = {r['familia'] for r in rows if r['name'] in train}
        related = {r['name'] for r in rows if r['grupo_escena'] in scenes or r['familia'] in families}
        if related <= train:
            break
        train |= related
    result = copy.deepcopy(rows)
    for row in result:
        if row['name'] in train:
            row['split'] = 'train'
    return result


def get_plan(root, part):
    reference = part.get('plan_path')
    revision = isinstance(reference, str) and re.fullmatch(re.escape(BASE) + r'/revisiones/[A-Za-z0-9_-]+/plan_particion\.json', reference)
    if (reference != PLAN and not revision) or part.get('plan_sha256') != p.digest(root / reference):
        raise ValueError('Cambió el plan del cierre ampliado.')
    plan = p.read(root / reference)
    if revision:
        folder = Path(reference).parent.as_posix()
        if (plan.get('revision_of_plan') != PLAN
                or plan.get('revision_of_plan_sha256') != p.digest(root / PLAN)
                or plan.get('source_snapshot') != folder + '/snapshot_cvat.json'
                or plan.get('human_review_receipt') != folder + '/cambios.json'
                or not all(ref in plan.get('evidence_sha256', {}) for ref in
                           [plan['source_snapshot'], plan['human_review_receipt'], PLAN])):
            raise ValueError('La revisión debe conservar el plan anterior y fijar la nueva lectura humana de CVAT.')
    if plan.get('approved_by') != 'Vicente' or not plan.get('authorization'):
        raise ValueError('Falta la autorización de uso de los casos revisados.')
    for ref, fingerprint in plan['evidence_sha256'].items():
        if p.digest(root / ref) != fingerprint:
            raise ValueError('Cambió la evidencia del cierre ampliado: ' + ref)
    return plan


def validate_partition(root, reference, value):
    plan = get_plan(root, value)
    if (value.get('schema_version') != 6 or value.get('id') != Path(reference).parent.name
            or value.get('base_partition_path') != PARENT):
        raise ValueError('Identidad de partición ampliada incompatible.')
    parent = p.partition(root, PARENT)
    expected = promoted_rows(parent['imagenes'], reviewed_hashes(root))
    if value.get('imagenes') != expected or value.get('resumen') != summarize(expected):
        raise ValueError('La partición debe conservar las fuentes y migrar solo los componentes revisados.')
    validate_rows(expected)
    train = [r['name'] for r in expected if r['split'] == 'train']
    val = [r['name'] for r in expected if r['split'] == 'val']
    if not train or not any(r['split'] == 'val' and r['origen'] == 'real' for r in expected):
        raise ValueError('Se necesita validación real separada para seleccionar best.pt.')
    if train != plan['selected_train'] or val != plan['selected_val']:
        raise ValueError('La selección difiere del plan ampliado.')
    parent_rows = {r['name']: r for r in parent['imagenes']}
    moved = [r['name'] for r in expected if r['split'] == 'train' and parent_rows[r['name']]['split'] == 'val']
    if moved != plan['moved_val_to_train']:
        raise ValueError('La migración de validación debe quedar registrada íntegramente.')
    reserved = p.read(root / plan['reserved_inventory'])
    if reserved['exact_duplicates_known_sources'] or {r['sha256'] for r in expected} & {r['sha256'] for r in reserved['files']}:
        raise ValueError('La reserva contiene duplicados de desarrollo.')
    if plan.get('initial_model_sha256') != '7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a':
        raise ValueError('El cierre ampliado debe partir del oficial, no del candidato rechazado.')
    return value


def prepare_partition(root, reference, part, client=None):
    from refuerzo_geometria_v3 import save_preparation
    plan = get_plan(root, part)
    return save_preparation(root, reference, part, p.read(root / plan['source_snapshot']))


def choose(root, receipt, images, value):
    part = p.partition(root, receipt['partition_path'])
    plan = get_plan(root, part)
    if (value.get('plan_sha256') != part['plan_sha256']
            or value.get('required_initial_model') != plan['initial_model']
            or value.get('required_initial_model_sha256') != plan['initial_model_sha256']
            or value.get('baseline_sha256') != p.digest(root / plan['baseline_path'])):
        raise ValueError('Cambió el plan, el modelo inicial o la referencia común de validación.')
    train = [r['name'] for r in images if r['split'] == 'train']
    val = [r['name'] for r in images if r['split'] == 'val']
    if train != plan['selected_train'] or val != plan['selected_val']:
        raise ValueError('Faltan imágenes o polígonos del cierre ampliado.')
    return train, []
