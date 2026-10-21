"""Crear solo el ZIP de las seis imágenes de demostración seleccionadas."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from preparar import digest, safe_path

ROOT = Path(__file__).resolve().parents[2]
SELECTION = 'Documentacion/Ejemplos/imagenes_demo_20261020.json'
GUIDE = 'Documentacion/Ejemplos/LEEME_imagenes_demo_20261020.txt'


def build(root=ROOT, output=None):
    root = Path(root).resolve()
    output = Path(output or root / '.publicacion/releases').resolve()
    if not output.is_relative_to(root) or output == root:
        raise ValueError('La salida debe ser una subcarpeta del proyecto.')
    manifest = json.loads((root / SELECTION).read_text(encoding='utf-8'))
    entries = manifest['imagenes']
    if len(entries) != 6 or len({item['archivo'] for item in entries}) != 6:
        raise ValueError('Se requieren las seis imágenes distintas de la selección.')
    members = {}
    for item in entries:
        if item['uso_datos'] not in ('val_real', 'val_sintetica_diagnostico'):
            raise ValueError('No se admite material de entrenamiento o reserva final.')
        source = safe_path(root, item['fuente'])
        safe_path(root, item['archivo'])
        if source.stat().st_size != item['bytes'] or digest(source) != item['sha256']:
            raise ValueError('Falta o cambió una fuente seleccionada: ' + item['fuente'])
        members['Imagenes_demo/' + item['archivo']] = source.read_bytes()
    members['Imagenes_demo/LEEME.md'] = (root / GUIDE).read_text(encoding='utf-8').encode('utf-8')
    members['Imagenes_demo/manifest.json'] = (root / SELECTION).read_bytes()
    output.mkdir(parents=True, exist_ok=True)
    target = safe_path(output, manifest['zip'])
    with tempfile.TemporaryDirectory(dir=output, prefix='imagenes-demo-') as temporary:
        pending = Path(temporary) / 'imagenes.zip'
        with zipfile.ZipFile(pending, 'w') as archive:
            for name, body in sorted(members.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 10, 20, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, body)
        with zipfile.ZipFile(pending) as archive:
            if archive.testzip() is not None or set(archive.namelist()) != set(members):
                raise ValueError('El ZIP no pasó la comprobación de integridad.')
        if target.exists() and digest(target) != digest(pending):
            raise ValueError('Ya existe un ZIP distinto con ese nombre; usar una nueva versión.')
        if not target.exists():
            shutil.copy2(pending, target)
    checksum = target.with_suffix('.sha256')
    checksum.write_text(f'{digest(target)}  {target.name}\n', encoding='utf-8')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, help='Subcarpeta local donde dejar el ZIP.')
    args = parser.parse_args()
    try:
        target = build(output=args.salida)
        print(f'Listo: {target} ({target.stat().st_size / 1024**2:.2f} MiB). Sin publicación automática.')
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
