"""Comprobar enlaces, datos y exportaciones compartidas, sin modificar archivos."""
import ast
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
sys.path.insert(0, str(ROOT / 'Laboratorio/Datos'))
from conjuntos import dataset_directory, verify_export
from verificar_datos import verify as verify_data

EXCLUDED = {'cvat-v2.77.0', '.git', 'node_modules', '__pycache__',
            '.runtime', '.entorno-py312', '.venv-modelo', '.venv-cvat'}


def source_tree(folder):
    """Walk project files without traversing runtimes or compatibility links."""
    for directory, dirs, names in os.walk(folder, followlinks=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDED
                   and not (Path(directory) / d).is_junction()
                   and not (Path(directory) / d).is_symlink()]
        for name in names:
            path = Path(directory) / name
            if not path.is_symlink():
                yield path


def verify(root=ROOT, include_data=True):
    root = Path(root)
    data = verify_data(root) if include_data else {'estado': 'omitido', 'motivo': 'Solo estructura; no es auditoría global de datos.'}
    folders = ('Datos', 'Documentacion', 'Laboratorio', 'Infraestructura', 'Entregables',
               'Aplicacion', 'Modelos', 'Historico')
    documents = [root / 'README.md']
    for folder in folders:
        documents.extend(p for p in source_tree(root / folder) if p.suffix == '.md')
    links = 0
    retired_links = 0
    cleanup = root / '.resguardo/aligerado_20261026'
    retired = set()
    if (cleanup / 'resultado.json').is_file():
        result = json.loads((cleanup / 'resultado.json').read_text(encoding='utf-8'))
        if result.get('state') == 'completed':
            receipt = json.loads((cleanup / 'manifiesto_retiro.json').read_text(encoding='utf-8'))
            aliases_file = root / '.resguardo/reorganizacion_20261026/compatibilidad.json'
            aliases = json.loads(aliases_file.read_text(encoding='utf-8-sig')) if aliases_file.is_file() else []
            def current_reference(value):
                for alias in aliases:
                    old, new = alias['alias'], alias['target']
                    if value == old or value.startswith(old + '/'):
                        value = new + value[len(old):]
                return value
            retired = {current_reference(item['path']) for item in receipt['files'] if item.get('sha256')}
    for path in documents:
        for raw in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
            target = unquote(raw.strip('<>').split('#')[0])
            if not target or urlparse(target).scheme:
                continue
            links += 1
            destination = (path.parent / target).resolve()
            if not destination.exists():
                if destination.is_relative_to(root.resolve()) and destination.relative_to(root.resolve()).as_posix() in retired:
                    retired_links += 1
                else:
                    raise ValueError(f'Enlace local sin destino: {path.relative_to(root)} -> {target}')
    exports = set()
    for path in (root / 'Experimentos').glob('*/manifest.json'):
        metadata = json.loads(path.read_text(encoding='utf-8-sig'))
        if metadata.get('dataset_ref'):
            exports.add(dataset_directory(root, path.parent, metadata))
    for path in exports:
        verify_export(path)
    source_files = [path for base in ('Laboratorio/Modelos', 'Laboratorio/Datos', 'Aplicacion')
                    for path in source_tree(root / base) if path.suffix == '.py']
    for path in source_files:
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    return dict(estado='correcto', documentos=len(documents), enlaces_locales=links,
                enlaces_historicos_retirados_documentados=retired_links,
                exportaciones_compartidas=len(exports), python_sintaxis=len(source_files), datos=data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--structure-only', action='store_true', help='Comprobar enlaces, exportaciones y sintaxis; omitir el inventario de datos.')
    args = parser.parse_args()
    try:
        result = verify(include_data=not args.structure_only)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
        raise SystemExit(f'ERROR: {error}') from None
    print(json.dumps(result, ensure_ascii=False, indent=2))
