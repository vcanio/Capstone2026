"""Auditoría del código publicable; funciona antes de descargar datos y modelos."""
import ast
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import unquote, urlparse
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from preparar import safe_path
from rutas_publicacion import current_reference

PRIVATE = ('.config-modelo/', '.resguardo/', '.tmp/', '.publicacion/', '.artefactos/',
           '.venv-modelo/', '.venv-cvat/', 'Laboratorio/Experimentos/panel_pruebas/', 'Contexto/', 'Historico/Contexto/')
SECRET_KEYS = {'password', 'passwd', 'token', 'api_key', 'secret', 'client_secret', 'access_token', 'auth_token'}


def local_only(name):
    """Material local que no debe entrar en Git ni en activos publicados."""
    path = PurePosixPath(name)
    partition_backup = (path.parts[:3] == ('Datos', 'Registros', 'Particiones') and
                        'respaldo_registros' in path.parts)
    raw_evidence = (path.parts[:2] == ('Documentacion', 'Evidencias') and
                    (path.suffix == '.log' or
                     (path.name.startswith('consulta_github_') and path.suffix == '.json')))
    return name.startswith(PRIVATE) or partition_backup or raw_evidence


def secret_fields(value, path=''):
    findings = []
    if isinstance(value, dict):
        for key, child in value.items():
            where = f'{path}.{key}'
            if (key.lower() in SECRET_KEYS and isinstance(child, str) and child and
                    not child.startswith(('TU_', 'YOUR_', '${', '<'))):
                findings.append(where)
            findings.extend(secret_fields(child, where))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            findings.extend(secret_fields(child, f'{path}[{i}]'))
    return findings


def verify(root=ROOT):
    root = Path(root).resolve()
    manifest = json.loads((root / 'Historico/Reproducibilidad/artefactos.json').read_text(encoding='utf-8'))
    declared = set()
    packages = dict(manifest['packages'])
    local_manifest = root / 'Historico/Reproducibilidad/activos_locales_20261023.json'
    if local_manifest.is_file():
        additional = json.loads(local_manifest.read_text(encoding='utf-8'))['packages']
        if set(packages).intersection(additional):
            raise ValueError('El manifiesto local repite nombres de paquetes publicados.')
        packages.update(additional)
    for package in packages.values():
        if Path(package['file']).name != package['file']:
            raise ValueError('Nombre inválido de activo.')
        if not re.fullmatch(r'[a-f0-9]{64}', package['sha256']):
            raise ValueError('Activo sin SHA-256 válido.')
        # Los enlaces al ZIP y su comprobante identifican un activo real declarado.
        # La ausencia de URL sigue indicando distribucion local, no publicacion.
        if package.get('destination'):
            outer = package['destination'].rstrip('/') + '/' + package['file']
            safe_path(root, outer)
            if local_only(outer):
                raise ValueError('Destino privado de un activo: ' + outer)
            declared.add(current_reference(outer))
            declared.add(current_reference(str(PurePosixPath(outer).with_suffix('.sha256'))))
        for item in package['files']:
            name = (package.get('destination', '').rstrip('/') + '/' + item['path']).lstrip('/')
            safe_path(root, name)
            if local_only(name) or 'acceso_local.json' in name:
                raise ValueError('Un activo incluye configuración privada: ' + name)
            declared.add(current_reference(name))
    git = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], capture_output=True)
    if git.returncode:
        raise ValueError('Ejecutar esta auditoría en el checkout preparado con .git.')
    paths = [root / p for p in git.stdout.decode('utf-8').split('\0') if p]
    links = pending = python = 0
    for path in paths:
        rel = path.relative_to(root).as_posix()
        if local_only(rel):
            raise ValueError('Archivo privado visible para Git: ' + rel)
        if path.name == 'acceso_local.json' or (path.name.startswith('.env') and not path.name.endswith('.example')):
            raise ValueError('Archivo privado visible para Git: ' + rel)
        if path.suffix.lower() in ('.pt', '.zip') or path.stat().st_size >= 50 * 1024**2:
            raise ValueError('Binario o archivo grande fuera de Releases: ' + rel)
        if path.suffix == '.json':
            if secret_fields(json.loads(path.read_text(encoding='utf-8-sig'))):
                raise ValueError('Posible credencial en JSON: ' + rel)
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=rel)
            python += 1
        if path.suffix == '.md':
            for raw in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
                value = unquote(raw.strip('<>').split('#')[0])
                if not value or urlparse(value).scheme:
                    continue
                target = (path.parent / value).resolve()
                if target.exists():
                    links += 1
                elif target.is_relative_to(root) and (target.relative_to(root).as_posix() in declared or
                        any(s.startswith(target.relative_to(root).as_posix().rstrip('/') + '/') for s in declared)):
                    pending += 1
                else:
                    raise ValueError(f'Enlace sin destino ni activo declarado: {rel} -> {value}')
    return dict(estado='correcto', archivos_git=len(paths), python_sintaxis=python,
                enlaces_disponibles=links, enlaces_a_activos_descargables=pending, paquetes=len(packages))


if __name__ == '__main__':
    try:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
    except (ValueError, OSError, SyntaxError) as error:
        raise SystemExit(f'ERROR: {error}') from None
