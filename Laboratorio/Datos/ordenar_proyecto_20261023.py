"""Limpiar temporales identificados y comprobar el orden local del 23/10/2026.

No actúa sobre Git, CVAT, entornos instalados, datasets o ensayos.
Archiva fuentes auxiliares; solo elimina bibliotecas temporales y cachés regenerables.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT / '.resguardo/orden_proyecto_20261023'
RECEIPT = BACKUP / 'limpieza.json'
KEEP = {'README.md', 'demo_nueva_20261021', 'walmart_vision_run', 'vision_actual_20261022',
        'vision_ocupacion_20261022', 'visibilidad_v2', 'pruebas_orden_proyecto'}
GIT = 'C:/Program Files/Git/cmd/git.exe'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def bounded(path, parent):
    path = path.resolve()
    require(path.is_relative_to(parent.resolve()) and path != parent.resolve(), 'Ruta fuera del alcance: ' + str(path))
    require(not path.is_symlink() and not path.is_junction(), 'No se operan enlaces: ' + str(path))
    return path


def inventory(path, exclude=()):
    result = []
    candidates = [path] if path.is_file() else sorted(path.rglob('*'))
    for p in candidates:
        require(not p.is_symlink() and not p.is_junction(), 'Enlace inesperado dentro del temporal: ' + str(p))
        if p.is_file() and not any(p.is_relative_to(x) for x in exclude):
            result.append({'path': rel(p), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    return result


def apply():
    require(BACKUP.is_dir() and (BACKUP / 'proteccion.json').is_file(), 'Falta el respaldo previo.')
    require(not RECEIPT.exists(), 'La limpieza ya se aplicó; usar --verify.')
    temporary = ROOT / '.tmp'
    cache = [ROOT / '.tmp/video_tools', ROOT / '.tmp/__pycache__']
    for base in (ROOT / 'Herramientas', ROOT / 'Experimentos/Bordes'):
        cache.extend(p for p in base.rglob('__pycache__')
                     if not {'cvat-v2.77.0', '.runtime', '.entorno-py312'}.intersection(p.parts))
    cache = [bounded(p, ROOT) for p in cache if p.exists()]
    require(all((p.name == '__pycache__' and p.is_relative_to(ROOT / 'Herramientas'))
                or (p.name == '__pycache__' and p.is_relative_to(ROOT / 'Experimentos/Bordes'))
                or p in (ROOT / '.tmp/video_tools', ROOT / '.tmp/__pycache__')
                for p in cache), 'Objetivo de borrado no autorizado por la lista acotada.')
    actions = []
    for p in cache:
        files = inventory(p)
        actions.append({'action': 'eliminar_regenerable', 'source': rel(p),
                        'files': files, 'bytes': sum(f['bytes'] for f in files)})
    for p in sorted(temporary.iterdir()):
        if p.name in KEEP or p in cache:
            continue
        bounded(p, temporary)
        target = bounded(BACKUP / 'temporales_anteriores' / p.name, BACKUP)
        require(not target.exists(), 'Destino de archivo existente: ' + str(target))
        files = inventory(p, cache)
        actions.append({'action': 'archivar_temporal', 'source': rel(p), 'destination': rel(target),
                        'files': files, 'bytes': sum(f['bytes'] for f in files)})
    # Guardar el plan antes de borrar/mover. No se compone una orden de shell con rutas.
    write(BACKUP / 'plan_limpieza.json', actions)
    for action in actions:
        source = ROOT / action['source']
        if action['action'] == 'eliminar_regenerable':
            bounded(source, ROOT)
            shutil.rmtree(source)
        else:
            bounded(source, temporary)
            destination = bounded(ROOT / action['destination'], BACKUP)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
    empty = ROOT / 'tmp'
    empty_removed = False
    if empty.exists():
        require(empty.is_dir() and not any(empty.iterdir()), 'tmp/ dejó de estar vacío; no se elimina.')
        empty.rmdir()
        empty_removed = True
    write(RECEIPT, {'date': datetime.now(timezone.utc).isoformat(), 'actions': actions,
                    'empty_tmp_removed': empty_removed, 'preserved_tmp': sorted(KEEP),
                    'git_writes': 0, 'cvat_writes': 0})


def verify():
    baseline = json.loads((BACKUP / 'proteccion.json').read_text(encoding='utf-8'))
    for item in baseline['files']:
        require(sha(ROOT / item['path']) == item['sha256'], 'Archivo protegido modificado: ' + item['path'])
    repo = ROOT / '.publicacion/repositorio'
    status = subprocess.check_output([GIT, '-C', str(repo), 'status', '--porcelain=v1', '-z'])
    head = subprocess.check_output([GIT, '-C', str(repo), 'rev-parse', 'HEAD']).decode().strip()
    require(hashlib.sha256(status).hexdigest() == baseline['git_status_sha256'] and head == baseline['git_head'],
            'Cambió el checkout Git durante la limpieza.')
    receipt = json.loads(RECEIPT.read_text(encoding='utf-8'))
    archived_count = archived_bytes = cache_count = cache_bytes = 0
    for action in receipt['actions']:
        if action['action'] == 'archivar_temporal':
            source = ROOT / action['source']
            target = ROOT / action['destination']
            require(not source.exists(), 'Temporal archivado reapareció: ' + action['source'])
            for f in action['files']:
                previous = ROOT / f['path']
                archived = target if previous == source else target / previous.relative_to(source)
                require(sha(archived) == f['sha256'], 'Archivo trasladado alterado: ' + f['path'])
            archived_count += len(action['files'])
            archived_bytes += action['bytes']
        else:
            # Cachés pueden reaparecer al ejecutar Python; no son fuentes ni datos aprobados.
            cache_count += len(action['files'])
            cache_bytes += action['bytes']
    return {'estado': 'verificado', 'archivos_protegidos_sin_cambios': len(baseline['files']),
            'archivos_auxiliares_archivados': archived_count, 'bytes_archivados': archived_bytes,
            'archivos_regenerables_eliminados': cache_count, 'bytes_regenerables_eliminados': cache_bytes,
            'git_head_y_cambios_previos_conservados': True, 'git_cambios_previos': baseline['git_status_entries'],
            'cvat_writes': 0, 'reentrenamientos': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.apply:
        apply()
    result = verify()
    write(BACKUP / 'verificacion_limpieza.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
