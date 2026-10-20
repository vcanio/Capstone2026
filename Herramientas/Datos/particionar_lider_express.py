"""Fijar o verificar la particion por escenas de las tareas 19 y 22, sin entrenar.

No modifica CVAT, imagenes, copias previas de modelos ni la reserva historica.
La aplicacion conserva respaldos de los registros locales que actualiza.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
PARTITION = ROOT / 'Datos/Registros/Particiones/lider_express_v2_20261019'
LOTS = {19: 'lider_express_20261016', 22: 'visibilidad_limitada_20261019'}
STATES = {'reponer', 'suficiente', 'no_evaluable'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def scene_map(config):
    result = {}
    ids = set()
    for group in config['grupos']:
        require(group['id'] not in ids, 'Grupo de escena duplicado.')
        ids.add(group['id'])
        require(group['split'] in ('train', 'val', 'test'), 'Split de grupo invalido.')
        for number in group['familias']:
            family = f'lider_express_{number:03}'
            require(family not in result, 'Familia en dos grupos: ' + family)
            result[family] = group
    require(set(result) == {f'lider_express_{n:03}' for n in range(1, 60)}, 'Deben estar exactamente las 59 familias.')
    return result


def annotation_counts(snapshot):
    from shapely.geometry import Polygon
    import math
    annotations, frames = snapshot['annotations'], snapshot['meta']['frames']
    require(not annotations['tracks'] and not annotations['tags'], 'Se requieren shapes, sin tracks ni tags.')
    require(not snapshot['meta'].get('deleted_frames'), 'Hay frames excluidos; revisar la particion.')
    names = {a['id']: a['name'] for label in snapshot['labels'] for a in label['attributes']}
    label_names = {label['id']: label['name'] for label in snapshot['labels']}
    counts = {Path(frame['name']).stem: Counter() for frame in frames}
    require(len(counts) == len(frames), 'Nombres de frames duplicados.')
    geometries = defaultdict(set)
    for shape in annotations['shapes']:
        index = shape['frame']
        require(type(index) is int and 0 <= index < len(frames), 'Frame de poligono invalido.')
        require(label_names[shape['label_id']] == 'Nivel', 'Etiqueta ajena a Nivel.')
        values = [a['value'] for a in shape['attributes'] if names[a['spec_id']] == 'estado']
        require(len(values) == 1 and values[0] in STATES, 'Estado ausente o pendiente; no inferir predeterminados.')
        points = shape['points']
        require(shape['type'] == 'polygon' and not shape.get('outside') and len(points) >= 6
                and len(points) % 2 == 0 and all(math.isfinite(v) for v in points), 'Poligono no valido.')
        polygon = Polygon(zip(points[::2], points[1::2]))
        require(polygon.is_valid and polygon.area > 1, 'Geometria invalida.')
        frame = frames[index]
        require(all(0 <= x <= frame['width'] and 0 <= y <= frame['height']
                    for x, y in zip(points[::2], points[1::2])), 'Puntos fuera de imagen.')
        key = polygon.normalize().wkb_hex
        require(key not in geometries[index], 'Poligono duplicado en una imagen.')
        geometries[index].add(key)
        counts[Path(frame['name']).stem][values[0]] += 1
    require(all(counts.values()), 'Hay fotos sin niveles.')
    return counts


def make_records(config, verify_images=True):
    groups = scene_map(config)
    records, source_hashes = [], {}
    for task, lot in LOTS.items():
        base = ROOT / 'Datos/V2' / lot
        snapshot_path = PARTITION / 'fuentes' / f'tarea_{task}.json'
        snapshot = read(snapshot_path)
        require(snapshot['task']['id'] == task and snapshot['task']['project_id'] == 7, 'Tarea equivocada.')
        counts = annotation_counts(snapshot)
        source_hashes[snapshot_path.relative_to(ROOT).as_posix()] = digest(snapshot_path)
        fields, rows = csv_rows(base / 'inventario.csv')
        require(len(rows) == (236 if task == 19 else 60), 'Cantidad de imagenes inesperada.')
        require({Path(row['archivo']).stem for row in rows} == set(counts), 'Inventario y frames no coinciden.')
        for row in rows:
            path = (base / row['archivo']).resolve()
            require(path.is_relative_to(base.resolve()), 'Ruta fuera del lote.')
            require(path.is_file(), 'Imagen ausente: ' + row['archivo'])
            if verify_images:
                require(digest(path) == row['sha256'], 'Imagen modificada: ' + row['imagen_id'])
            family = row['imagen_origen_id']
            group = groups[family]
            records.append({'imagen_id': row['imagen_id'], 'cvat_name': path.stem,
                            'archivo': path.relative_to(ROOT).as_posix(), 'sha256': row['sha256'],
                            'task_id': task, 'familia': family, 'grupo_escena': group['id'],
                            'split': group['split'], 'origen': row['origen'],
                            'etapa': 'base' if task == 19 else 'visibilidad',
                            'estados': dict(counts[path.stem])})
    require(len({r['imagen_id'] for r in records}) == 296, 'IDs repetidos.')
    require(len({r['sha256'] for r in records}) == 296, 'Bytes de imagen duplicados.')
    reserve = read(ROOT / 'Datos/Registros/reserva_evaluacion.json')
    _, historical = csv_rows(ROOT / 'Datos/Registros/inventario.csv')
    reserved_hashes = {r['sha256'] for r in historical
                       if r['imagen_id'] in reserve['image_ids'] or r['grupo_escena'] in reserve['groups']}
    require(not reserved_hashes.intersection(r['sha256'] for r in records), 'Contiene una imagen de reserva historica.')
    return sorted(records, key=lambda r: (r['task_id'], r['cvat_name'])), source_hashes


def validate(records):
    families, groups = defaultdict(set), defaultdict(set)
    summary = {}
    for row in records:
        require(row['split'] in ('train', 'val', 'test'), 'Particion invalida.')
        families[row['familia']].add(row['split'])
        groups[row['grupo_escena']].add(row['split'])
    require(all(len(s) == 1 for s in families.values()), 'Filtracion entre variantes de una familia.')
    require(all(len(s) == 1 for s in groups.values()), 'Filtracion entre escenas.')
    for split in ('train', 'val', 'test'):
        subset = [r for r in records if r['split'] == split]
        base = [r for r in subset if r['etapa'] == 'base']
        real = [r for r in base if r['origen'] == 'real']
        visibility = [r for r in subset if r['etapa'] == 'visibilidad']
        states_real = sum((Counter(r['estados']) for r in real), Counter())
        require(states_real['reponer'] and states_real['suficiente'], 'Sin cobertura real de ambas clases en ' + split)
        require(not any(r['estados'].get('no_evaluable') for r in base), 'Cambio en el alcance binario de la etapa base.')
        summary[split] = {'familias': len({r['familia'] for r in subset}),
                          'grupos': len({r['grupo_escena'] for r in subset}),
                          'base': len(base), 'base_reales': len(real),
                          'base_sinteticas': len(base) - len(real),
                          'visibilidad': len(visibility), 'total': len(subset),
                          'estados_base': dict(sum((Counter(r['estados']) for r in base), Counter())),
                          'estados_base_reales': dict(states_real),
                          'estados_visibilidad_provisionales': dict(sum((Counter(r['estados']) for r in visibility), Counter()))}
    return summary


def list_members(records):
    lists = {}
    for split in ('train', 'val', 'test'):
        base = [r for r in records if r['split'] == split and r['etapa'] == 'base']
        if split == 'train':
            lists['base_train'] = base
        else:
            lists['base_' + split + '_real'] = [r for r in base if r['origen'] == 'real']
            lists['base_' + split + '_sintetica_diagnostico'] = [r for r in base if r['origen'] != 'real']
        lists['visibilidad_' + split + '_pendiente_revision'] = [
            r for r in records if r['split'] == split and r['etapa'] == 'visibilidad']
    return lists


def backup(path):
    target = PARTITION / 'respaldo_registros' / path.relative_to(ROOT)
    require(not target.exists(), 'Ya hay respaldo; no sobrescribir la particion existente.')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def apply(config, records, sources, summary):
    require(not (PARTITION / 'particion.json').exists(), 'La particion ya esta fijada. Usa --verify.')
    lists = list_members(records)
    write(PARTITION / 'particion.json', {
        'schema_version': 1, 'id': PARTITION.name, 'created_at': datetime.now(timezone.utc).isoformat(),
        'estado': 'fijada_por_grupos_conservadores', 'criterion': config['criterio'],
        'grupo_config_sha256': digest(PARTITION / 'grupos_escena.json'),
        'fuentes_sha256': sources, 'resumen': summary, 'imagenes': records,
        'aprobado_entrenamiento': False,
        'pendientes': ['Auditoria humana de cobertura: vacios frente a poco stock dentro de reponer.',
                       'Cerrar revision de imagenes, estados, geometria y oclusion de tarea 22.',
                       'Preparar exportacion y entrenamiento v2 con dos clases en etapa base y tres en etapa posterior.'],
        'politica': {'etapa_1': 'Solo base. Train real+sintetica. Validacion principal y test reales; sinteticas en diagnosticos separados.',
                     'etapa_2': 'Anadir solo visibilidad_train tras cerrar revision; visibilidad_val para desarrollo, visibilidad_test reservada.',
                     'test': 'No usar test para elegir parametros, corregir el algoritmo ni seleccionar versiones. Comparacion final tras congelar metodos.',
                     'limitaciones': 'Solo 4 niveles reales reponer: train 2, val 1, test 1. Sin no_evaluable real. No mide generalizacion entre locales.'},
        'listas': {name: {'archivo': 'listas/' + name + '.txt', 'imagenes': len(rows)} for name, rows in lists.items()}
    })
    for name, rows in lists.items():
        path = PARTITION / 'listas' / (name + '.txt')
        path.parent.mkdir(exist_ok=True)
        path.write_text(''.join(r['archivo'] + '\n' for r in rows), encoding='utf-8')
    for task, lot in LOTS.items():
        base = ROOT / 'Datos/V2' / lot
        path = base / 'inventario.csv'
        fields, rows = csv_rows(path)
        by_id = {r['imagen_id']: r for r in records if r['task_id'] == task}
        backup(path)
        for row in rows:
            assigned = by_id[row['imagen_id']]
            row.update(grupo_escena=assigned['grupo_escena'], particion_modelo=assigned['split'])
        temporary = path.with_suffix('.csv.tmp')
        with temporary.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        temporary.replace(path)
        path = base / 'manifest.json'
        manifest = read(path)
        backup(path)
        manifest['particion'] = {'estado': 'fijada_por_escena', 'registro': (PARTITION / 'particion.json').relative_to(ROOT).as_posix(),
                                 'unidad': 'familia_y_grupo_escena_conservador',
                                 'imagenes_por_split': dict(Counter(r['split'] for r in by_id.values())),
                                 'revision_cobertura_vacios_y_bajo_stock': 'pendiente'}
        manifest['particion_modelo'] = 'ver_inventario'
        if task == 19:
            manifest['split'] = 'ver_inventario'
            manifest['nota'] = '236 anotadas. Particion por familias/escenas fijada; no habilita entrenamiento ni modifica el reparto de CVAT.'
            manifest['estado'] = 'anotado_particionado_pendiente_auditoria'
        manifest['aprobado_entrenamiento'] = False
        write(path, manifest)
    path = ROOT / 'Datos/Registros/lotes.json'
    catalog = read(path); backup(path)
    for lot in catalog['lotes']:
        if lot['id'] in LOTS.values():
            lot['particion'] = (PARTITION / 'particion.json').relative_to(ROOT).as_posix()
            lot['aprobado_entrenamiento'] = False
            lot['nota'] += ' Particion de modelos fijada por familias y grupos de escena el 19/10; consultar registro de particion. No habilita entrenamiento.'
    write(path, catalog)


def verify(config, records, sources, summary):
    saved = read(PARTITION / 'particion.json')
    normalized = [{**r, 'archivo': r['archivo'].replace('Datos/Pendientes/', 'Datos/V2/')} for r in saved['imagenes']]
    require(normalized == records and saved['resumen'] == summary, 'El registro fijado no coincide con las fuentes.')
    require(saved['fuentes_sha256'] == sources, 'Se modificaron las copias de CVAT.')
    require(saved['grupo_config_sha256'] == digest(PARTITION / 'grupos_escena.json'), 'Se modificaron los grupos fijados.')
    for task, lot in LOTS.items():
        _, rows = csv_rows(ROOT / 'Datos/V2' / lot / 'inventario.csv')
        assigned = {r['imagen_id']: r for r in records if r['task_id'] == task}
        require(all(r['grupo_escena'] == assigned[r['imagen_id']]['grupo_escena']
                    and r['particion_modelo'] == assigned[r['imagen_id']]['split'] for r in rows), 'Inventario sin aplicar.')
        manifest = read(ROOT / 'Datos/V2' / lot / 'manifest.json')
        require(manifest['particion']['registro'] == (PARTITION / 'particion.json').relative_to(ROOT).as_posix()
                and manifest['aprobado_entrenamiento'] is False, 'Manifest no coincide.')
    for name, rows in list_members(records).items():
        require((PARTITION / 'listas' / (name + '.txt')).read_text(encoding='utf-8').splitlines()
                == [r['archivo'] for r in rows], 'Lista alterada: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--apply', action='store_true')
    modes.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    config = read(PARTITION / 'grupos_escena.json')
    records, sources = make_records(config)
    summary = validate(records)
    if args.apply:
        apply(config, records, sources, summary)
    verify(config, records, sources, summary)
    print(json.dumps({'estado': 'verificado', 'imagenes': len(records), 'resumen': summary}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
