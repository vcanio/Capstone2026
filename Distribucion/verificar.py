"""Verificar el producto publicable sin datos privados ni el laboratorio interno."""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEYS = {'password', 'passwd', 'token', 'api_key', 'secret', 'client_secret', 'access_token', 'auth_token'}
ALLOWED_DIRS = {'Aplicacion', 'Aplicacion_Cliente', 'Documentacion', 'Distribucion', 'Entregables', '.github', 'Fase 1', 'Fase 2'}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_file(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
        raise ValueError('Ruta inválida: ' + name)
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()) or not path.is_file():
        raise ValueError('Archivo ausente o fuera del producto: ' + name)
    return path


def verify_model(root=ROOT):
    root = Path(root)
    app = root / 'Aplicacion'
    value = json.loads((app / 'modelos.json').read_text(encoding='utf-8-sig'))
    models = value.get('models', [])
    if (len(models) != 1 or value.get('default_model') != models[0].get('id')
            or models[0].get('classes') != ['Nivel'] or not models[0].get('official')):
        raise ValueError('Se requiere un único modelo oficial de clase Nivel.')
    model = models[0]
    name = model['file']
    if not name.startswith('modelos/') or PurePosixPath(name).suffix != '.pt':
        raise ValueError('Ruta inválida del modelo oficial.')
    path = safe_file(app, name)
    if path.stat().st_size != model['bytes'] or sha256(path) != model['sha256']:
        raise ValueError('El peso oficial no coincide con su tamaño/SHA-256.')
    for name, expected in value.get('edge_sources', {}).items():
        if PurePosixPath(name).name != name or sha256(safe_file(app, name)) != expected:
            raise ValueError('El motor no coincide con edge_sources: ' + name)
    if set(value.get('edge_sources', {})) != {'ocupacion_paulo.py', 'ocupacion_linea_a.py', 'gondola_bordes.py', 'gondola_combinacion_ponderada.py'}:
        raise ValueError('El manifiesto no identifica todos los módulos del motor.')
    for name, expected in value.get('experimental_sources', {}).items():
        if PurePosixPath(name).name != name or sha256(safe_file(app, name)) != expected:
            raise ValueError('El algoritmo experimental no coincide con experimental_sources: ' + name)
    for name in ('inferencia.py', 'presentacion_niveles.py', 'geometria_niveles.py', 'vision_v3.py',
                 'visibilidad_experimental.py', 'revision_rapida.js'):
        safe_file(app, name)
    uv = json.loads((app / 'herramientas/fuente_uv.json').read_text(encoding='utf-8'))
    for entry in uv['files']:
        resource = safe_file(app, entry['file'])
        if sha256(resource) != entry['sha256'] or resource.stat().st_size != entry['bytes']:
            raise ValueError('Herramienta uv o licencia alterada: ' + entry['file'])
    state = json.loads((root / 'Documentacion/Estado_V3_actual.json').read_text(encoding='utf-8'))
    if state['model']['sha256'] != model['sha256'] or state['model']['id'] != model['id']:
        raise ValueError('La ficha de estado y el modelo no coinciden.')
    return {'id': model['id'], 'sha256': model['sha256'], 'edge_sources': value['edge_sources']}


def git_files(root=ROOT):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                            check=True, capture_output=True)
    return sorted({name for name in result.stdout.decode('utf-8').split('\0')
                   if name and (Path(root) / name).is_file()})


def secret_fields(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if (key.lower() in SECRET_KEYS and isinstance(child, str) and child
                    and not child.startswith(('TU_', 'YOUR_', '${', '<'))):
                raise ValueError('Campo secreto con valor: ' + key)
            secret_fields(child)
    elif isinstance(value, list):
        for child in value:
            secret_fields(child)


def verify_links(root, names):
    root = Path(root).resolve()
    known = set(names)
    links = 0
    for name in names:
        if not name.endswith('.md'):
            continue
        source = root / name
        for raw in re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8-sig')):
            parts = urlsplit(raw.strip('<>'))
            if parts.scheme or not parts.path:
                continue
            target = (source.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f'Enlace fuera del producto: {name} -> {raw}')
            relative = target.relative_to(root).as_posix()
            if relative not in known and not any(p.startswith(relative.rstrip('/') + '/') for p in known):
                raise ValueError(f'Enlace sin archivo publicado: {name} -> {raw}')
            links += 1
    return links


def verify(root=ROOT):
    root = Path(root).resolve()
    model = verify_model(root)
    names = git_files(root)
    python = 0
    for name in names:
        parts = PurePosixPath(name).parts
        if len(parts) > 1 and parts[0] not in ALLOWED_DIRS:
            raise ValueError('Carpeta ajena al producto: ' + parts[0])
        if (any(part in {'.runtime', '.entorno-py312', '__pycache__', '.config-modelo', '.resguardo', '.publicacion'}
                or part.startswith('.venv') for part in parts)
                or (parts[-1].startswith('.env') and not parts[-1].endswith('.example'))
                or parts[-1] == 'acceso_local.json'):
            raise ValueError('Archivo privado o de entorno visible para publicación: ' + name)
        if len(parts) == 1 and (parts[0].startswith('.env') or parts[0].endswith(('.zip', '.log'))):
            raise ValueError('Archivo local visible para publicación: ' + name)
        path = safe_file(root, name)
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=name)
            python += 1
        if path.suffix == '.json':
            secret_fields(json.loads(path.read_text(encoding='utf-8-sig')))
        if path.suffix.lower() == '.pt' and name != 'Aplicacion/' + json.loads((root / 'Aplicacion/modelos.json').read_text(encoding='utf-8'))['models'][0]['file']:
            raise ValueError('Peso adicional no declarado: ' + name)
        if path.suffix.lower() in {'.exe', '.dll', '.zip', '.7z', '.pkl', '.cache', '.log'} and name != 'Aplicacion/herramientas/uv.exe':
            raise ValueError('Binario o salida no prevista: ' + name)
    academic = json.loads((root / 'Documentacion/Evidencias/integridad_academica.json').read_text(encoding='utf-8'))
    protected = {p for p in names if p.startswith(('Fase 1/', 'Fase 2/'))}
    if protected != set(academic['files']):
        raise ValueError('Cambió el inventario de Fase 1/Fase 2.')
    for name, expected in academic['files'].items():
        if sha256(root / name) != expected:
            raise ValueError('Se alteró un documento académico protegido: ' + name)
    return {'estado': 'correcto', 'archivos': len(names), 'python_sintaxis': python,
            'enlaces_locales': verify_links(root, names), 'archivos_academicos_intactos': len(protected),
            'modelo': model}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.root), ensure_ascii=False, indent=2))
    except (ValueError, OSError, SyntaxError, subprocess.CalledProcessError) as error:
        raise SystemExit('ERROR: ' + str(error)) from None
