"""Comprobar enlaces, datos y exportaciones compartidas, sin modificar archivos."""
import ast
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Herramientas/Modelos'))
sys.path.insert(0, str(ROOT / 'Herramientas/Datos'))
from conjuntos import dataset_directory, verify_export
from verificar_datos import verify as verify_data


def verify(root=ROOT):
    root = Path(root)
    data = verify_data(root)
    folders = ('Datos', 'Documentacion', 'Herramientas', 'Infraestructura', 'Entregables',
               'Experimentos', 'Modelos', 'reproducibilidad')
    documents = [root / 'README.md']
    for folder in folders:
        documents.extend(p for p in (root / folder).rglob('*.md') if 'cvat-v2.77.0' not in p.parts)
    links = 0
    for path in documents:
        for raw in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
            target = unquote(raw.strip('<>').split('#')[0])
            if not target or urlparse(target).scheme:
                continue
            links += 1
            if not (path.parent / target).exists():
                raise ValueError(f'Enlace local sin destino: {path.relative_to(root)} -> {target}')
    exports = set()
    for path in (root / 'Experimentos').glob('*/manifest.json'):
        metadata = json.loads(path.read_text(encoding='utf-8-sig'))
        if metadata.get('dataset_ref'):
            exports.add(dataset_directory(root, path.parent, metadata))
    for path in exports:
        verify_export(path)
    source_files = [path for base in ('Modelos', 'Datos', 'Demo_lite')
                    for path in (root / 'Herramientas' / base).rglob('*.py')]
    for path in source_files:
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    return dict(estado='correcto', documentos=len(documents), enlaces_locales=links,
                exportaciones_compartidas=len(exports), python_sintaxis=len(source_files), datos=data)


if __name__ == '__main__':
    try:
        result = verify()
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
        raise SystemExit(f'ERROR: {error}') from None
    print(json.dumps(result, ensure_ascii=False, indent=2))
