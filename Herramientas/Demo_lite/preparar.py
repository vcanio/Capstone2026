"""Preparación privada y reanudable; no usa ni modifica el Python del sistema."""
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime'
READY = RUNTIME / 'listo.json'
REQUIRED = {'torch': '2.5.1', 'torchvision': '0.20.1', 'ultralytics': '8.4.174',
            'numpy': '1.26.4', 'pillow': '12.3.0', 'opencv-python': '4.11.0.86'}


def installed_versions():
    result = {}
    for package in REQUIRED:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = None
    return result


def dependencies_match(installed):
    return all(installed.get(name) and installed[name].split('+')[0] == expected for name, expected in REQUIRED.items())


def fingerprint():
    digest = hashlib.sha256()
    for name in ('preparar.py', 'requirements.txt', 'app.py', 'inferencia.py', 'modelos.json'):
        digest.update(name.encode())
        digest.update((ROOT / name).read_bytes())
    for name in ('ocupacion_paulo.py', 'gondola_bordes.py'):
        if (ROOT / name).is_file():
            digest.update(name.encode())
            digest.update((ROOT / name).read_bytes())
    return digest.hexdigest()


def ready_state():
    return {'folder': str(ROOT), 'python': str(Path(sys.executable).resolve()),
            'fingerprint': fingerprint(), 'packages': installed_versions()}


def is_ready(expected):
    if not dependencies_match(expected['packages']):
        return False
    try:
        return json.loads(READY.read_text(encoding='utf-8')) == expected
    except (OSError, ValueError):
        return False


def main():
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Abre iniciar.cmd para usar el entorno privado de la aplicación.')
    expected = ready_state()
    if is_ready(expected):
        print('Entorno listo.', flush=True)
        return
    RUNTIME.mkdir(exist_ok=True)
    uv = ROOT / 'herramientas/uv.exe'
    source = json.loads((ROOT / 'herramientas/fuente_uv.json').read_text(encoding='utf-8'))
    uv_record = next(item for item in source['files'] if item['file'] == 'herramientas/uv.exe')
    with uv.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != uv_record['sha256']:
            raise RuntimeError('El preparador está incompleto. Extrae de nuevo el ZIP.')
    print('Preparando Walmart Lite. La primera descarga puede tardar varios minutos.', flush=True)
    print('Tu Python instalado y sus paquetes no se modifican.', flush=True)
    with (RUNTIME / 'instalacion.log').open('w', encoding='utf-8') as log:
        log.write('Inicio: ' + datetime.now(timezone.utc).isoformat() + '\n')

        def run(args, message):
            print(message, flush=True)
            log.write(message + '\n')
            log.flush()
            environment = os.environ.copy()
            environment['PYTHONUTF8'] = '1'
            process = subprocess.Popen([str(a) for a in args], cwd=ROOT, env=environment,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding='utf-8', errors='replace',
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            for line in process.stdout:
                print(line.rstrip(), flush=True)
                log.write(line)
                log.flush()
            if process.wait():
                raise RuntimeError(f'{message} no terminó. Revisa .runtime/instalacion.log y vuelve a abrir iniciar.cmd para reintentar.')

        if not dependencies_match(expected['packages']):
            run([uv, '--no-config', 'pip', 'install', '--python', sys.executable,
                 '--index-url', 'https://download.pytorch.org/whl/cpu', 'torch==2.5.1', 'torchvision==0.20.1'],
                '1/3 · Preparando el motor para CPU...')
            run([uv, '--no-config', 'pip', 'install', '--python', sys.executable,
                 '--index-url', 'https://pypi.org/simple', '-r', ROOT / 'requirements.txt'],
                '2/3 · Preparando las dependencias del visor...')
        run([sys.executable, ROOT / 'app.py', '--check'], '3/3 · Comprobando los modelos y el entorno...')
        state = ready_state()
        if not dependencies_match(state['packages']):
            raise RuntimeError('Las versiones instaladas no coinciden. Revisa .runtime/instalacion.log.')
        temporary = READY.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporary.replace(READY)
        print('Walmart Lite está listo.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'\nNo se pudo completar la preparación: {error}', file=sys.stderr, flush=True)
        sys.exit(1)
