"""Resolver la partición v2 registrada; el navegador no elige sus destinos."""
import hashlib
import json
from pathlib import Path
from rutas_datos import current_image_path

RELATIVE = 'Datos/Registros/Particiones/lider_express_v2_20261019/particion.json'
BASE_STATES = ('reponer', 'suficiente')


def load_partition(root):
    path = root / RELATIVE
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    groups_path = path.parent / 'grupos_escena.json'
    if hashlib.sha256(groups_path.read_bytes()).hexdigest() != data['grupo_config_sha256']:
        raise ValueError('Cambió la agrupación de escenas. Revisa el registro de partición antes de importar.')
    configured = json.loads(groups_path.read_text(encoding='utf-8-sig'))
    groups = {g['id']: g for g in configured['grupos']}
    families, scenes, names, hashes = {}, {}, set(), set()
    records = {}
    for row in data['imagenes']:
        split = row['split']
        group = groups[row['grupo_escena']]
        if (split not in ('train', 'val', 'test') or split != group['split'] or
                int(row['familia'].rsplit('_', 1)[1]) not in group['familias']):
            raise ValueError('La partición registrada no coincide con sus grupos de escena.')
        for key, registry in (('familia', families), ('grupo_escena', scenes)):
            if registry.setdefault(row[key], split) != split:
                raise ValueError('Una familia o escena cruza particiones.')
        if row['cvat_name'] in names or row['sha256'] in hashes:
            raise ValueError('Hay imágenes duplicadas en la partición registrada.')
        names.add(row['cvat_name']); hashes.add(row['sha256'])
        if row['task_id'] != 19:
            continue
        effective = 'reserva' if split == 'test' else 'diagnostico' if split == 'val' and row['origen'] != 'real' else split
        records[row['cvat_name']] = {**row, 'archivo': current_image_path(row['archivo']), 'effective_split': effective}
    if len(records) != 236 or len(families) != 59:
        raise ValueError('La partición base debe conservar sus 236 imágenes y 59 familias.')
    binding = {'path': RELATIVE, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'stage': 'base'}
    return {'records': records, 'binding': binding}


def verify_binding(root, metadata, report):
    if report.get('partition_binding') != metadata.get('fixed_partition'):
        raise ValueError('La copia usa otra partición. Trae nuevamente las anotaciones de CVAT.')
