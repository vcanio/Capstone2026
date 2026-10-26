"""Incluir el uv oficial de Windows x64, verificando el SHA-256 publicado en PyPI."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'Aplicacion/herramientas'


def main():
    with urlopen('https://pypi.org/pypi/uv/json', timeout=60) as response:
        release = json.load(response)
    artifact = next(item for item in release['urls'] if item['filename'].endswith('win_amd64.whl'))
    with urlopen(artifact['url'], timeout=120) as response:
        body = response.read()
    if hashlib.sha256(body).hexdigest() != artifact['digests']['sha256']:
        raise ValueError('La descarga de uv no coincide con la huella de PyPI.')
    TARGET.mkdir(parents=True, exist_ok=True)
    included = []
    with zipfile.ZipFile(BytesIO(body)) as wheel:
        executable = next(name for name in wheel.namelist() if name.endswith('/scripts/uv.exe'))
        files = {'uv.exe': wheel.read(executable)}
        for name in wheel.namelist():
            if '/licenses/' in name and not name.endswith('/'):
                files['licencias/' + Path(name).name] = wheel.read(name)
        if not any(name.startswith('licencias/') for name in files):
            raise ValueError('Faltan las licencias de uv en el paquete oficial.')
        for name, data in files.items():
            path = TARGET / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            included.append({'file': 'herramientas/' + name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    record = {'package': 'uv', 'version': release['info']['version'], 'source': 'https://pypi.org/project/uv/',
              'wheel_url': artifact['url'], 'wheel_sha256': artifact['digests']['sha256'], 'files': included}
    (TARGET / 'fuente_uv.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'version': record['version'], 'files': included}, ensure_ascii=False))


if __name__ == '__main__':
    main()
