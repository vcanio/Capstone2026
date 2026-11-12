"""Resolve registered archive locations without changing frozen artifact IDs."""
import json
from pathlib import Path, PurePosixPath

REGISTRY = '.config-modelo/rutas_historicas.json'


def mappings(root):
    path = Path(root) / REGISTRY
    if not path.is_file():
        return []
    rows = json.loads(path.read_text(encoding='utf-8'))['rutas']
    result = []
    for row in rows:
        source, target = row['origen'], row['destino']
        if any(not isinstance(v, str) or '\\' in v or PurePosixPath(v).is_absolute()
               or '..' in PurePosixPath(v).parts or ':' in v for v in (source, target)):
            raise ValueError('Registro de archivo histórico inválido.')
        if not target.startswith('Historico/'):
            raise ValueError('El archivo debe permanecer en Histórico.')
        result.append((source, target))
        if source.startswith('Laboratorio/Experimentos/'):
            result.append((source.removeprefix('Laboratorio/'), target))
    return result


def registered_target(root, reference):
    """Return only an explicitly mapped descendant contained in the archive."""
    if not isinstance(reference, str) or '\\' in reference or ':' in reference:
        return None
    relative = PurePosixPath(reference)
    if relative.is_absolute() or '..' in relative.parts:
        return None
    for source, target in mappings(root):
        if reference == source or reference.startswith(source + '/'):
            suffix = reference[len(source):].lstrip('/')
            base = Path(root) / target
            path = base / suffix
            archive = (Path(root) / 'Historico').resolve()
            if (base.resolve().is_relative_to(archive)
                    and path.resolve().is_relative_to(base.resolve())):
                return path
    return None


def within(root, path, base):
    """Accept the original boundary or the exact registered relocation only."""
    root, path, base = Path(root), Path(path), Path(base)
    if path.resolve().is_relative_to(base.resolve()):
        return True
    from almacenamiento_datos import authorized
    if authorized(root, path, base):
        return True
    try:
        reference = path.relative_to(root).as_posix()
        path.relative_to(base)  # A mapping cannot broaden the caller's logical boundary.
    except ValueError:
        return False
    target = registered_target(root, reference)
    if target is None:
        return False
    if path.resolve() == target.resolve():
        return True
    # Docker Desktop can expose a Windows junction through /mnt/host while
    # the explicit archive bind uses /app/Historico. Accept only the identical
    # filesystem object, not arbitrary paths or merely matching file contents.
    try:
        return path.samefile(target)
    except OSError:
        return False


def read_path(root, reference):
    """Read archived jobs even after their old directory has been removed."""
    target = registered_target(root, reference)
    return target if target is not None else Path(root) / reference
