"""Preparar una copia Git revisable y sus activos, sin commit, tag, push ni upload."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from preparar import digest
from verificar_publicacion import secret_fields


def files_under(base):
    if not base.is_dir():
        return []
    files = []
    for folder, dirs, names in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.runtime', '.entorno-py312', 'cvat-v2.77.0', 'panel_pruebas')]
        for name in names:
            p = Path(folder) / name
            if p.suffix not in ('.pyc', '.cache'):
                files.append(p)
    return sorted(files)


def archive(output, files, *, prefix_root=ROOT):
    records = []
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
        for path in files:
            name = path.relative_to(prefix_root).as_posix()
            h = hashlib.sha256()
            count = 0
            with path.open('rb') as source, z.open(name, 'w', force_zip64=True) as target:
                while chunk := source.read(1024 * 1024):
                    h.update(chunk);count += len(chunk);target.write(chunk)
            records.append(dict(path=name, bytes=count, sha256=h.hexdigest()))
    return dict(file=output.name, bytes=output.stat().st_size, sha256=digest(output), files=records)


def copy_code(git, checkout):
    shutil.copy2(ROOT / '.gitignore', checkout / '.gitignore')
    candidates = [ROOT / n for n in ('README.md', '.gitignore', '.gitattributes', '.dockerignore')]
    for base in ('Herramientas', 'Infraestructura', 'Documentacion', 'Contexto', 'Datos', 'Modelos', 'Experimentos', 'Entregables', 'reproducibilidad', '.github'):
        candidates.extend(files_under(ROOT / base))
    names = [f.relative_to(ROOT).as_posix() for f in candidates]
    result = subprocess.run([git, '-C', str(checkout), 'check-ignore', '--no-index', '--stdin', '-z'],
                            input=('\0'.join(names) + '\0').encode(), capture_output=True)
    if result.returncode not in (0, 1):raise ValueError(result.stderr.decode())
    ignored = set(result.stdout.decode().split('\0'))
    copied = []
    for source, name in zip(candidates, names):
        if name in ignored:continue
        if source.suffix == '.json' and secret_fields(json.loads(source.read_text(encoding='utf-8-sig'))):
            raise ValueError('Posible credencial; no se copiará: ' + name)
        target = checkout / name;target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target);copied.append(name)
    return copied


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--git', default='git', help='Ruta del ejecutable Git.')
    p.add_argument('--salida', type=Path, default=ROOT / '.publicacion')
    p.add_argument('--tag', default='avance-2026-10-20')
    p.add_argument('--solo-codigo', action='store_true', help='Actualizar el checkout sin regenerar ZIP existentes.')
    args = p.parse_args()
    out = args.salida.resolve()
    if not out.is_relative_to(ROOT) or out == ROOT:
        p.error('La salida debe ser una subcarpeta del proyecto.')
    checkout = out / 'repositorio'
    if not (checkout / '.git').is_dir():
        p.error('Primero clona https://github.com/vcanio/Capstone2026.git en SALIDA/repositorio.')
    remote = subprocess.check_output([args.git, '-C', str(checkout), 'remote', 'get-url', 'origin'], text=True).strip()
    if remote != 'https://github.com/vcanio/Capstone2026.git':
        p.error('El checkout no corresponde al repositorio esperado.')
    if args.solo_codigo:
        print(f'Código actualizado: {len(copy_code(args.git, checkout))} archivos. Sin commit ni push.', flush=True)
        return
    release = out / 'releases';release.mkdir(exist_ok=True)
    development = out / 'paquetes_desarrollo';development.mkdir(exist_ok=True)
    packages = {}
    data = files_under(ROOT / 'Datos')
    sources = [f for f in data if 'exportaciones' not in f.parts and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.xlsx')]
    exported = [f for f in data if 'exportaciones' in f.parts]
    experiments = files_under(ROOT / 'Experimentos')
    models = [f for f in experiments if f.suffix.lower() in ('.jpg', '.png', '.pt') and f.name != 'last.pt']
    models += [f for f in files_under(ROOT / 'Modelos/preentrenados') if f.suffix == '.pt']
    models += [ROOT / 'Herramientas/Demo_lite/herramientas/uv.exe']
    reports = [f for f in files_under(ROOT / 'Entregables') if f.name.startswith('Informe_Intermedio_Avance_20261020.')]
    for key, name, selected in [
        ('datos_fuentes', 'Walmart_Datos_Fuentes_20261020.zip', sources),
        ('datos_exportados', 'Walmart_Datos_Exportados_20261020.zip', exported),
        ('modelos_resultados', 'Walmart_Modelos_Resultados_20261020.zip', models),
        ('informe', 'Walmart_Informe_Planificacion_20261020.zip', reports),
    ]:
        print(f'Empaquetando {key}: {len(selected)} archivos...', flush=True)
        packages[key] = archive(development / name, selected)
        print(f'{name}: {packages[key]["bytes"] / 1024**2:.1f} MiB.', flush=True)
    lite = ROOT / 'Entregables/Walmart_Lite_V2_Deteccion_Bordes_20261020.zip'
    shutil.copy2(lite, release / lite.name)
    # El ZIP de la demo es independiente; el preparador lo instala en Entregables.
    with zipfile.ZipFile(lite) as z:
        demo_files = [dict(path=i.filename, bytes=i.file_size,
                           sha256=hashlib.sha256(z.read(i)).hexdigest()) for i in z.infolist()]
    packages['demo'] = dict(file=lite.name, bytes=(release / lite.name).stat().st_size,
                           sha256=digest(release / lite.name), files=demo_files, destination='Entregables')
    packages['demo']['url'] = f'https://github.com/vcanio/Capstone2026/releases/download/{quote(args.tag)}/{lite.name}'
    manifest = dict(schema_version=1, version=args.tag, repository='vcanio/Capstone2026',
                    publication='Release pública: solo Walmart Lite. Paquetes de desarrollo: distribución separada con --assets.', packages=packages)
    manifest_path = ROOT / 'reproducibilidad/artefactos.json'
    manifest_path.parent.mkdir(exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    shutil.copy2(manifest_path, development / 'artefactos.json')
    sums = ''.join(f'{digest(f)}  {f.name}\n' for f in sorted(development.iterdir()) if f.is_file() and f.name != 'SHA256SUMS.txt')
    (development / 'SHA256SUMS.txt').write_text(sums, encoding='utf-8')
    copied = copy_code(args.git, checkout)
    (out / 'resumen.json').write_text(json.dumps(dict(checkout=str(checkout), release=str(release),
        archivos_codigo=len(copied), packages={k:{a:b for a,b in v.items() if a != 'files'} for k,v in packages.items()}), indent=2),encoding='utf-8')
    print(f'Listo: {len(copied)} archivos preparados en {checkout}. Sin commit ni push.', flush=True)


if __name__ == '__main__':
    main()
