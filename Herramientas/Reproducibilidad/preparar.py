"""Descargar e instalar activos de una Release sin dependencias de terceros.

Solo se instalan los archivos declarados en reproducibilidad/artefactos.json.
No se sobrescriben archivos diferentes ni se ejecuta código de los ZIP.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = 'reproducibilidad/artefactos.json'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root, name):
    p = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or p.is_absolute() or
            any(part in ('', '.', '..') for part in name.split('/'))):
        raise ValueError(f'Ruta de paquete inválida: {name}')
    target = (root / Path(*p.parts)).resolve()
    if not target.is_relative_to(root.resolve()) or target == root.resolve():
        raise ValueError(f'Ruta fuera del destino: {name}')
    return target


def validate_archive(archive, package, root):
    """Validar TODO antes de escribir; incluye hashes y colisiones locales."""
    root = safe_path(root, package['destination']) if package.get('destination') else root
    expected = {f['path']: f for f in package['files']}
    if len(expected) != len(package['files']):
        raise ValueError('El manifiesto repite rutas.')
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries) != len(expected) or len({i.filename for i in entries}) != len(entries):
            raise ValueError('El ZIP contiene archivos repetidos o distintos del manifiesto.')
        for entry in entries:
            target = safe_path(root, entry.filename)
            item = expected.get(entry.filename)
            if (not item or entry.is_dir() or entry.file_size != item['bytes'] or
                    stat.S_ISLNK(entry.external_attr >> 16) or entry.flag_bits & 1):
                raise ValueError(f'Entrada no admitida: {entry.filename}')
            with z.open(entry) as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != item['sha256']:
                    raise ValueError(f'Contenido modificado: {entry.filename}')
            if target.exists() and (not target.is_file() or digest(target) != item['sha256']):
                raise ValueError(f'Hay un archivo local diferente: {entry.filename}. Conserva tu trabajo y usa otra carpeta limpia.')


def install_archive(archive, package, root):
    validate_archive(archive, package, root)
    root = safe_path(root, package['destination']) if package.get('destination') else root
    written = 0
    with zipfile.ZipFile(archive) as z:
        for item in package['files']:
            target = safe_path(root, item['path'])
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.walmart-', delete=False) as temporary:
                temporary_path = Path(temporary.name)
                try:
                    with z.open(item['path']) as source:
                        shutil.copyfileobj(source, temporary, 1024 * 1024)
                except BaseException:
                    temporary.close()
                    temporary_path.unlink(missing_ok=True)
                    raise
            try:
                if digest(temporary_path) != item['sha256']:
                    raise ValueError(f'La copia quedó incompleta: {item["path"]}')
                temporary_path.replace(target)
            finally:
                temporary_path.unlink(missing_ok=True)
            written += 1
    return written


def get_archive(package, assets, cache):
    if Path(package['file']).name != package['file'] or '\\' in package['file']:
        raise ValueError('Nombre inválido de paquete.')
    if assets:
        source = assets / package['file']
        if not source.is_file():
            raise ValueError(f'Falta {source}')
    else:
        cache.mkdir(parents=True, exist_ok=True)
        source = cache / package['file']
        if not source.is_file() or digest(source) != package['sha256']:
            url = package['url']
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname != 'github.com':
                raise ValueError('La descarga debe partir de GitHub por HTTPS.')
            print(f'Descargando {package["file"]} ({package["bytes"] / 1024**2:.1f} MiB)...', flush=True)
            pending = source.with_suffix(source.suffix + '.part')
            try:
                with urlopen(url, timeout=60) as response, pending.open('wb') as output:
                    total = 0
                    while chunk := response.read(1024 * 1024):
                        total += len(chunk)
                        if total > package['bytes']:
                            raise ValueError('La descarga supera el tamaño publicado.')
                        output.write(chunk)
                if pending.stat().st_size != package['bytes'] or digest(pending) != package['sha256']:
                    raise ValueError('La descarga no coincide con el manifiesto.')
                pending.replace(source)
            finally:
                pending.unlink(missing_ok=True)
    if source.stat().st_size != package['bytes'] or digest(source) != package['sha256']:
        raise ValueError(f'Paquete incompleto o modificado: {source.name}')
    return source


def verify_files(package, root):
    root = safe_path(root, package['destination']) if package.get('destination') else root
    for item in package['files']:
        path = safe_path(root, item['path'])
        if not path.is_file() or path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError(f'Falta o cambió {item["path"]}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, help='Carpeta local de activos; no usa Internet.')
    parser.add_argument('--paquetes', nargs='+', default=['datos_fuentes', 'datos_exportados', 'modelos_resultados', 'informe'])
    parser.add_argument('--verificar', action='store_true', help='Comprobar archivos instalados sin descargar ni escribir.')
    args = parser.parse_args(argv)
    try:
        manifest = json.loads((ROOT / MANIFEST).read_text(encoding='utf-8'))
        for name in dict.fromkeys(args.paquetes):
            if name not in manifest['packages']:
                raise ValueError(f'Paquete desconocido: {name}')
            package = manifest['packages'][name]
            if args.verificar:
                verify_files(package, ROOT)
                print(f'{name}: integridad correcta ({len(package["files"])} archivos).', flush=True)
            else:
                source = get_archive(package, args.assets, ROOT / '.artefactos')
                count = install_archive(source, package, ROOT)
                print(f'{name}: listo, {count} archivos incorporados.', flush=True)
        if not args.verificar:
            (ROOT / '.config-modelo').mkdir(exist_ok=True)
            (ROOT / 'Experimentos/panel_pruebas').mkdir(parents=True, exist_ok=True)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f'Error: {error}\nSi la Release aún no está publicada, usa --assets RUTA_A_LOS_ZIP.\n')


if __name__ == '__main__':
    main()
