"""Auditar los registros de Datos sin modificar imagenes ni anotaciones."""
import csv
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def registered_path(root, value):
    require(isinstance(value, str) and bool(value), 'Ruta registrada vacia o invalida.')
    path = (root / value).resolve()
    require(path.is_relative_to((root / 'Datos').resolve()), f'Ruta fuera de Datos: {value}')
    return path


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def verify(root=ROOT):
    root = Path(root).resolve()
    catalog = read(root / 'Datos/Registros/lotes.json')
    require(catalog['schema_version'] == 1, 'Version de catalogo no reconocida.')
    require(bool(catalog['lotes']), 'El catalogo no contiene lotes.')
    lots, image_hashes, pending_hashes, unique_paths = {}, set(), set(), set()
    records_checked = 0
    for lot in catalog['lotes']:
        lot_id = lot['id']
        require(lot_id not in lots, f'Lote repetido: {lot_id}')
        inventory = registered_path(root, lot['inventario'])
        base = registered_path(root, lot['base_archivos'])
        with inventory.open(encoding='utf-8-sig', newline='') as handle:
            entries = list(csv.DictReader(handle))
        require(len(entries) == lot['imagenes'], f'Cantidad distinta en {lot_id}')
        ids, paths, hashes = set(), set(), set()
        for entry in entries:
            iid = entry[lot['id_columna']]
            require(bool(iid) and iid not in ids, f'ID vacio o repetido en {lot_id}: {iid}')
            ids.add(iid)
            path = (base / entry['archivo']).resolve()
            require(path.is_relative_to(base), f'Ruta fuera del lote {lot_id}: {entry["archivo"]}')
            require(path.suffix.lower() in IMAGE_SUFFIXES, f'Extension inesperada: {path.name}')
            require(path not in paths, f'Ruta repetida: {path.name}')
            paths.add(path)
            unique_paths.add(path)
            require(bool(re.fullmatch(r'[a-f0-9]{64}', entry['sha256'])), f'SHA-256 invalido: {iid}')
            require(digest(path) == entry['sha256'], f'SHA-256 distinto: {path}')
            if entry.get('bytes'):
                require(path.stat().st_size == int(entry['bytes']), f'Tamano distinto: {iid}')
            hashes.add(entry['sha256'])
            records_checked += 1
        if lot.get('manifest'):
            manifest_path = registered_path(root, lot['manifest'])
            manifest = read(manifest_path)
            if isinstance(manifest['imagenes'], list):
                declared = {(item['id'], item['archivo'], item['sha256']) for item in manifest['imagenes']}
                actual = {(item[lot['id_columna']], item['archivo'], item['sha256']) for item in entries}
                require(len(declared) == len(entries) and declared == actual,
                        f'Manifest e inventario no coinciden: {lot_id}')
            else:
                require(manifest['imagenes'] == len(entries), f'Manifest incompleto: {lot_id}')
            if lot['estado'] == 'pendiente_de_reparto':
                require(manifest['estado'] == lot['estado'], f'Estado contradictorio: {lot_id}')
                require(manifest.get('cvat') is None and manifest.get('aprobado_entrenamiento') is False,
                        f'Lote pendiente habilitado para CVAT o entrenamiento: {lot_id}')
                require(manifest['reparto'] == dict(anotacion=0, pruebas=0, evaluacion_final=0,
                                                  pendientes=len(entries)),
                        f'Reparto asignado a un lote pendiente: {lot_id}')
                require(all(item['uso'] == 'pendiente' and item['estado_anotacion'] == 'sin_anotar'
                            and item.get('split', '') in ('', 'pendiente') for item in entries),
                        f'Una foto pendiente tiene un uso asignado: {lot_id}')
                actual_images = {p.resolve() for p in (base / manifest['directorio_imagenes']).rglob('*')
                                 if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES}
                require(actual_images == paths, f'Imagenes sin registrar o faltantes: {lot_id}')
                require(len(hashes) == len(entries), f'Fotos duplicadas en el lote pendiente: {lot_id}')
                require(not pending_hashes.intersection(hashes), 'Foto repetida entre lotes pendientes.')
                pending_hashes.update(hashes)
            else:
                image_hashes.update(hashes)
        else:
            image_hashes.update(hashes)
        lots[lot_id] = len(entries)
    require(not pending_hashes.intersection(image_hashes),
            'Una foto pendiente ya existe en las fuentes o en el set de anotacion.')

    active = read(root / 'Datos/Registros/dataset_activo.json')
    package_manifest = read(registered_path(root, active['manifest']))
    package = package_manifest['imagenes']
    require(len(package) == active['imagenes'], 'Paquete activo incompleto.')
    if package_manifest.get('base_archivos') == 'Datos':
        expected = {registered_path(root, 'Datos/' + item['archivo']) for item in package}
        actual = {p.resolve() for folder in ('Datos/V1/Lider', 'Datos/V1/Sinteticas') for p in (root / folder).rglob('*')
                  if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES}
        require(actual == expected, 'Imagenes adicionales o faltantes en V1.')
        require(len(expected) == len(package) and len({item['sha256'] for item in package}) == len(package),
                'Copias duplicadas dentro de V1.')
    reserve = read(root / 'Datos/Registros/reserva_evaluacion.json')
    scenes = {}
    for image in package:
        require(image['escena'] not in reserve['groups'] and
                Path(image.get('imagen_fuente', '')).stem not in reserve['image_ids'],
                'Una imagen o escena de reserva aparece en el paquete activo.')
        require(image['split'] in ('train', 'val') and
                (image['split'] != 'val' or image['origen'] == 'real'),
                'Particion invalida en el paquete activo.')
        scenes.setdefault(image['escena'], set()).add(image['split'])
    require(all(len(splits) == 1 for splits in scenes.values()),
            'Una escena aparece en entrenamiento y validacion.')
    version_path = registered_path(root, active['version_modelos_ruta'])
    version = read(version_path)
    require(version['id'] == active['version_modelos'], 'Version activa contradictoria.')
    for key, filename in [('snapshot_sha256', 'snapshot_cvat.json'),
                          ('partition_sha256', 'particion.json')]:
        require(digest(version_path.parent / filename) == version[key], f'Copia anotada modificada: {filename}')
    require(len(version['report']['imagenes']) == active['imagenes_activas'], 'Cantidad activa contradictoria.')
    return dict(lotes=lots, registros_verificados=records_checked,
                archivos_imagen_unicos=len(unique_paths),
                fotos_pendientes=len(pending_hashes), imagenes_activas=active['imagenes_activas'])


if __name__ == '__main__':
    try:
        result = verify()
    except (ValueError, KeyError, OSError, TypeError) as error:
        raise SystemExit(f'ERROR: {error}') from None
    print(json.dumps({'estado': 'correcto', **result}, ensure_ascii=False, indent=2))
