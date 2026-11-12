"""Acceso explícito y portable a archivos registrados; nunca autoriza un disco entero."""
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

CATALOG = 'Datos/Registros/Almacenamiento/catalogo.json'
CONFIG = '.config-modelo/almacenamiento.local.json'


def relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or ':' in value
            or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts
            or str(PurePosixPath(value)) != value):
        raise ValueError('Referencia de datos inválida.')
    return value


@lru_cache(maxsize=8)
def _catalog(path, mtime, size):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise ValueError('Versión de catálogo no admitida.')
    files = data['archivos']
    if not isinstance(files, dict):
        raise ValueError('Catálogo de datos inválido.')
    for ref, row in files.items():
        relative(ref)
        if row.get('externa'):
            relative(row['externa'])
        h = row.get('sha256', '')
        if len(h) != 64 or any(c not in '0123456789abcdef' for c in h) or type(row.get('bytes')) is not int or row['bytes'] < 0:
            raise ValueError('Identidad de datos inválida: ' + ref)
    return data


def catalog(root):
    path = Path(root) / CATALOG
    if not path.is_file():
        return {'schema_version': 1, 'archivos': {}, 'carpetas': []}
    stat = path.stat()
    return _catalog(str(path), stat.st_mtime_ns, stat.st_size)


def data_root(root):
    value = os.environ.get('WALMART_DATA_ROOT')
    config = Path(root) / CONFIG
    if not value and config.is_file():
        value = json.loads(config.read_text(encoding='utf-8'))['data_root']
    if not value:
        raise FileNotFoundError('Configure WALMART_DATA_ROOT o .config-modelo/almacenamiento.local.json para conectar los datasets.')
    path = Path(value)
    if not path.is_absolute():
        raise ValueError('WALMART_DATA_ROOT debe ser una ruta absoluta.')
    return path


def external_path(root, row):
    base = data_root(root).resolve()
    path = (base / relative(row['externa'])).resolve()
    if not path.is_relative_to(base):
        raise ValueError('El archivo registrado sale de la raíz de datos.')
    if not path.is_file():
        raise FileNotFoundError('Dataset no disponible: conecte WALMART_DATA_ROOT; falta ' + row['externa'])
    if path.stat().st_size != row['bytes']:
        raise ValueError('Cambió el tamaño del dato registrado: ' + row['externa'])
    return path


def entry(root, reference):
    return catalog(root)['archivos'].get(relative(reference))


def read_path(root, reference, *, verify=False, prefer_external=False):
    """Conservar referencias congeladas y comprobar el límite de cada archivo."""
    reference = relative(reference)
    root = Path(root).resolve()
    row = entry(root, reference)
    local = root / reference
    resolved = local.resolve()
    if row and row.get('externa') and (prefer_external or not local.is_file() or not resolved.is_relative_to(root)):
        path = external_path(root, row)
    elif resolved.is_relative_to(root):
        path = local
    else:
        # Existing archive aliases have an additional, independent allowlist.
        from archivo_historico import registered_target
        target = registered_target(root, reference)
        if target is None or not local.is_file() or not local.samefile(target):
            raise ValueError('Ruta fuera del proyecto y del catálogo.')
        path = target
    if verify and row:
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != row['sha256']:
                raise ValueError('Cambió el SHA-256 registrado: ' + reference)
    return path


def authorized(root, path, base):
    """Only an exact catalog file may cross a caller's logical boundary."""
    root, path, base = Path(root), Path(path), Path(base)
    try:
        path.relative_to(base)
        reference = path.relative_to(root).as_posix()
        row = entry(root, reference)
        if not row or not row.get('externa'):
            return False
        return path.is_file() and path.samefile(external_path(root, row))
    except (ValueError, OSError):
        return False


def collection(root, name):
    """Resolve a declared collection for local tools, without HTTP authorization."""
    ref = catalog(root).get('colecciones', {}).get(name)
    if not ref:
        raise FileNotFoundError('Colección no registrada: ' + name)
    base = data_root(root).resolve()
    path = (base / relative(ref)).resolve()
    if not path.is_relative_to(base):
        raise ValueError('Colección fuera de la raíz de datos.')
    return path


def legacy_external(root, value):
    """Translate original absolute paths only through their exact recorded key."""
    ref = catalog(root).get('referencias_externas_anteriores', {}).get(str(value))
    if ref is None:
        raise ValueError('Referencia externa no registrada: ' + str(value))
    return external_path(root, catalog(root)['externos'][ref])
