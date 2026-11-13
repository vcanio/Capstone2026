"""Extraer y comprobar integridad, HTTP e inferencia CPU de un ZIP de ambas apps."""
import argparse
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen
import zipfile

from PIL import Image


def free_port():
    with socket.socket() as connection:
        connection.bind(('127.0.0.1', 0))
        return connection.getsockname()[1]


def check(package, photo=None):
    report = {'purpose': 'functional_check_not_accuracy_evaluation', 'device': 'cpu',
              'photo': 'authorized_development_photo' if photo else 'generated_blank_image', 'apps': {}}
    with tempfile.TemporaryDirectory(prefix='walmart-paquete-') as temporary:
        extraction = Path(temporary).resolve()
        with zipfile.ZipFile(package) as archive:
            if archive.testzip() is not None or sum(i.file_size for i in archive.infolist()) > 200 * 1024 * 1024:
                raise ValueError('ZIP corrupto o demasiado grande.')
            for item in archive.infolist():
                relative = PurePosixPath(item.filename)
                if (relative.is_absolute() or '..' in relative.parts or '\\' in item.filename
                        or ':' in item.filename or (item.external_attr >> 16) & 0o170000 == 0o120000
                        or not (extraction / item.filename).resolve().is_relative_to(extraction)):
                    raise ValueError('Ruta no segura en el ZIP.')
            archive.extractall(extraction)
        root = extraction / 'Walmart_Vision'
        manifest = json.loads((root / 'MANIFIESTO_SHA256.json').read_text(encoding='utf-8'))
        files = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
        if files != set(manifest) | {'MANIFIESTO_SHA256.json'}:
            raise ValueError('El inventario extraído no coincide con el manifiesto.')
        for name, expected in manifest.items():
            target = (root / name).resolve()
            if not target.is_relative_to(root) or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                raise ValueError('Hash incorrecto: ' + name)
        report['verified_files'] = len(manifest)
        source = json.loads((root / 'FUENTE.json').read_text(encoding='utf-8'))
        report['source_commit'] = source['commit']
        if photo:
            body = Path(photo).read_bytes()
        else:
            buffer = BytesIO()
            Image.new('RGB', (640, 480), 'white').save(buffer, format='JPEG')
            body = buffer.getvalue()
        environment = dict(os.environ, PYTHONUTF8='1', YOLO_AUTOINSTALL='false',
                           YOLO_CONFIG_DIR=str(extraction / 'config'), MPLCONFIGDIR=str(extraction / 'matplotlib'))
        for name in ('equipo', 'cliente'):
            port = free_port()
            url = 'http://127.0.0.1:' + str(port)
            command = [sys.executable, str(root / ('Aplicacion/app.py' if name == 'equipo' else 'Aplicacion_Cliente/app_cliente.py'))]
            if name == 'cliente':
                command += ['--app-dir', str(root / 'Aplicacion')]
            command += ['--host', '127.0.0.1', '--port', str(port), '--device', 'cpu']
            with (extraction / (name + '.log')).open('w', encoding='utf-8') as log:
                process = subprocess.Popen(command, cwd=root, env=environment, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                try:
                    deadline = time.monotonic() + 45
                    while True:
                        try:
                            with urlopen(url + '/api/health', timeout=2) as response:
                                health = json.load(response)
                            break
                        except OSError:
                            if process.poll() is not None or time.monotonic() > deadline:
                                raise RuntimeError('No arrancó la app ' + name + '; revisar sus dependencias.')
                            time.sleep(.2)
                    with urlopen(url, timeout=10) as response:
                        if response.status != 200:
                            raise ValueError('La interfaz no devuelve HTTP 200.')
                    request = Request(url + '/api/predict?method=yolo_paulo_v2&confidence=0.60', data=body,
                        headers={'Content-Type': 'image/jpeg', 'Origin': url}, method='POST')
                    with urlopen(request, timeout=60) as response:
                        prediction = json.load(response)
                    if prediction.get('model') != source['model']['id']:
                        raise ValueError('La inferencia no usó el modelo oficial.')
                    report['apps'][name] = {'http': 200, 'health': health,
                        'model': prediction['model'], 'detections': len(prediction['detections'])}
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
        if report['apps']['equipo']['detections'] != report['apps']['cliente']['detections']:
            raise ValueError('Las apps no devolvieron el mismo número de niveles.')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', required=True, type=Path)
    parser.add_argument('--foto', type=Path, help='Solo una foto de desarrollo autorizada, nunca test reservado.')
    args = parser.parse_args()
    print(json.dumps(check(args.zip, args.foto), ensure_ascii=False, indent=2))
