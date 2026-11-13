"""Construir un ZIP nuevo de ambas apps desde el producto, sin el laboratorio."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verificar import ROOT, git_files, verify

PACKAGE_ROOT = 'Walmart_Vision'
LEGAL_FILES = ('LICENSE', 'NOTICE.md', 'LICENCIAS.md')


def build(output, root=ROOT):
    root, output = Path(root).resolve(), Path(output).resolve()
    checksum = output.with_suffix('.sha256')
    if output.suffix.lower() != '.zip':
        raise ValueError('La salida debe tener extensión .zip.')
    if output.exists() or checksum.exists():
        raise ValueError('La entrega ya existe; usa un nombre nuevo.')
    status = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True)
    if status.strip():
        raise ValueError('Se requiere un clon limpio: guarda las fuentes en un commit antes de empaquetar.')
    audit = verify(root)
    ref = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if not re.fullmatch(r'[a-f0-9]{40}', ref):
        raise ValueError('No se pudo identificar el commit fuente.')
    entries = {}
    names = git_files(root)
    selected_names = {name for name in names
        if ((Path(name).parts[0] in ('Aplicacion', 'Aplicacion_Cliente', 'Documentacion', 'Distribucion')
             and 'Pruebas' not in Path(name).parts and 'tests' not in Path(name).parts)
            or name in (*LEGAL_FILES, 'compose.apps.yaml', 'README.md', 'Entregables/README.md'))}
    # Las guías se conservan con sus rutas originales: todos sus enlaces relativos
    # siguen funcionando. Los documentos académicos y las herramientas internas
    # no se incorporan al ZIP de uso.
    for name in sorted(selected_names):
        body = (root / name).read_bytes()
        if name.endswith('.md'):
            # README remite al material académico que no se distribuye en este ZIP.
            from urllib.parse import quote, unquote, urlsplit
            def link(match):
                label, raw = match.groups()
                url = urlsplit(raw.strip('<>'))
                if url.scheme or not url.path:
                    return match.group(0)
                target = ((root / name).parent / unquote(url.path)).resolve()
                relative = target.relative_to(root).as_posix()
                if relative not in selected_names and not any(p.startswith(relative.rstrip('/') + '/') for p in selected_names):
                    kind = 'tree' if target.is_dir() else 'blob'
                    address = 'https://github.com/vcanio/Capstone2026/' + kind + '/' + ref + '/' + quote(relative, safe='/')
                    if url.fragment:
                        address += '#' + url.fragment
                    return '[' + label + '](' + address + ')'
                return match.group(0)
            body = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', link, body.decode('utf-8-sig')).encode('utf-8')
        if name.endswith('.cmd'):
            body = body.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        entries[name] = body
    for app, target in (('cliente', 'Aplicacion_Cliente\\iniciar_cliente.cmd'), ('equipo', 'Aplicacion\\iniciar.cmd')):
        entries['iniciar_' + app + '.cmd'] = ('@echo off\r\ncall "%~dp0' + target + '" %*\r\n').encode()
    entries['LEEME.md'] = ('''# Walmart Visión · apps cliente y equipo

Extrae todo. Windows x64: iniciar_cliente.cmd (8098) o iniciar_equipo.cmd (8095).
La primera preparación descarga Python 3.12 y dependencias; requiere Internet.
Docker: docker compose -f compose.apps.yaml up --build -d --wait.

Ambas apps comparten un solo modelo oficial y Línea A, índice visual preliminar
0–100 con umbral 52. Revisa contornos y visibilidad; no mide stock físico ni
detecta personas u obstáculos. Carga fotos propias; no se incluye el dataset.
Las fotos y revisiones no entrenan el modelo. La limpieza del recorrido cliente
elimina su sesión guardada. No hay sincronización entre computadores.

Consulta README.md, Documentacion/ y las guías de cada app. Código original:
AGPL-3.0-only; LICENSE, NOTICE.md y LICENCIAS.md conservan avisos y procedencia.
Este paquete de comprobación no sustituye activos ni notas de releases anteriores.
Fuente del checkout: https://github.com/vcanio/Capstone2026/tree/''' + ref + '\n').encode('utf-8')
    entries['FUENTE.json'] = (json.dumps({'repository': 'https://github.com/vcanio/Capstone2026',
        'commit': ref, 'model': audit['modelo'], 'purpose': 'inference_only',
        'working_tree_clean': True}, ensure_ascii=False, indent=2) + '\n').encode()
    manifest = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(entries.items())}
    entries['MANIFIESTO_SHA256.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Construir en un temporal y crear el destino con exclusión para no pisar
    # una entrega existente si otro proceso usa el mismo nombre.
    with tempfile.TemporaryFile() as temporary:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name, body in entries.items():
                archive.writestr(PACKAGE_ROOT + '/' + name, body)
        temporary.seek(0)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP corrupto.')
            for name, expected in manifest.items():
                if hashlib.sha256(archive.read(PACKAGE_ROOT + '/' + name)).hexdigest() != expected:
                    raise ValueError('Hash incorrecto: ' + name)
        temporary.seek(0)
        with output.open('xb') as destination:
            while block := temporary.read(1024 * 1024):
                destination.write(block)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    with checksum.open('x', encoding='utf-8', newline='\n') as destination:
        destination.write(digest + '  ' + output.name + '\n')
    return {'zip': str(output), 'sha256': digest, 'bytes': output.stat().st_size,
            'files': len(entries), 'source_commit': ref, 'apps': ['cliente', 'equipo']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output), ensure_ascii=False, indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit('ERROR: ' + str(error)) from None
