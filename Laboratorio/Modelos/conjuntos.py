"""Una exportacion verificada por version de datos, compartida entre ensayos."""
import hashlib
import json
from rutas_datos import current_image_path, experiment_parts
from pathlib import Path
import re
import shutil

DIRECTORIES = ('dataset_niveles', 'dataset_modulos')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def export_path(root, version, directory):
    if not isinstance(version, str) or not re.fullmatch(r'datos_\d{8}_\d{6}_[a-f0-9]{8}', version):
        raise ValueError('Version de exportacion invalida.')
    if directory not in DIRECTORIES:
        raise ValueError('Directorio del conjunto invalido.')
    versions = (root / 'Datos/Registros/Versiones_modelos').resolve()
    path = (versions / version / 'exportaciones' / directory).resolve()
    if not path.is_relative_to(versions):
        raise ValueError('Ruta de exportacion fuera de los registros.')
    return path


def dataset_directory(root, run, manifest=None):
    manifest = manifest if manifest is not None else read(run / 'manifest.json')
    directory = manifest.get('dataset_dir', 'dataset_modulos')
    if directory not in DIRECTORIES:
        raise ValueError('Directorio del conjunto invalido.')
    reference = manifest.get('dataset_ref')
    if not reference:
        return run / directory
    if reference['version'] != manifest.get('version_datos') or reference['directorio'] != directory:
        raise ValueError('La referencia del conjunto no corresponde al ensayo.')
    path = export_path(root, reference['version'], directory)
    receipt = path / 'integridad.json'
    if not receipt.is_file() or digest(receipt) != reference['integridad_sha256']:
        raise ValueError('El registro de integridad del conjunto compartido cambio.')
    return path


def content_inventory(directory):
    files = sorted(p for folder in ('images', 'labels') for p in (directory / folder).rglob('*')
                   if p.is_file() and p.suffix != '.cache')
    files.append(directory / 'data.yaml')
    return [{'archivo': p.relative_to(directory).as_posix(), 'sha256': digest(p), 'bytes': p.stat().st_size}
            for p in files]


def verify_export(directory):
    receipt = read(directory / 'integridad.json')
    for item in receipt['archivos']:
        path = (directory / item['archivo']).resolve()
        if not path.is_relative_to(directory.resolve()) or digest(path) != item['sha256']:
            raise ValueError('La exportacion compartida fue modificada: ' + item['archivo'])
    if content_inventory(directory) != receipt['archivos']:
        raise ValueError('La exportacion compartida contiene archivos no registrados.')
    return receipt


def consolidate_export(root, run):
    """Consolidar una exportacion creada localmente; conservar IDs y etiquetas."""
    manifest = read(run / 'manifest.json')
    if manifest.get('dataset_ref'):
        directory = dataset_directory(root, run, manifest)
        verify_export(directory)
        return directory
    kind = manifest.get('dataset_dir', 'dataset_modulos')
    target = export_path(root, manifest['version_datos'], kind)
    local = (run / kind).resolve()
    if not local.is_relative_to(run.resolve()) or local.name not in DIRECTORIES:
        raise ValueError('Exportacion temporal fuera del ensayo.')
    # Sin path absoluto: Ultralytics resuelve las rutas desde este YAML.
    classes = manifest['clases']
    yaml = 'train: images/train\nval: images/val\nnames:\n'
    yaml += ''.join(f'  {i}: {name}\n' for i, name in enumerate(classes))
    (local / 'data.yaml').write_text(yaml, encoding='utf-8')
    candidate = content_inventory(local)
    if target.exists():
        receipt = verify_export(target)
        if receipt['archivos'] != candidate or receipt['clases'] != classes:
            raise ValueError('Esta version ya tiene una exportacion distinta; crear otra version de datos.')
        # Solo se retira el temporal generado dentro de este ensayo, despues de comparar sus hashes.
        shutil.rmtree(local)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(local), str(target))
        receipt = dict(schema_version=1, version=manifest['version_datos'], clases=classes, archivos=candidate)
        (target / 'integridad.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest['dataset_ref'] = dict(version=manifest['version_datos'], directorio=kind,
                                 integridad_sha256=digest(target / 'integridad.json'))
    (run / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return target


def experiment_file(root, value):
    """Resolver referencias historicas a archivos de datasets de un ensayo."""
    path = root / value
    value = current_image_path(value)
    path = root / value
    parts = experiment_parts(value)
    if len(parts) >= 4 and parts[0] in ('Laboratorio/Experimentos', 'Historico/Experimentos') and parts[2] in DIRECTORIES:
        run = root / parts[0] / parts[1]
        manifest = read(run / 'manifest.json')
        if manifest.get('dataset_dir', 'dataset_modulos') == parts[2]:
            directory = dataset_directory(root, run, manifest)
            path = (directory / Path(*parts[3:])).resolve()
            if not path.is_relative_to(directory.resolve()):
                raise ValueError('Archivo fuera del conjunto del ensayo.')
    return path
