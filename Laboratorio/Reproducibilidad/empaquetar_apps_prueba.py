"""Crear un ZIP nuevo con las apps cliente/equipo y un solo motor V3 compartido."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
from empaquetar_demo_lite import build as build_team

CLIENT_FILES = ('app_cliente.py', 'interfaz_cliente.html', 'iniciar_cliente.cmd', 'README.md')
PACKAGE_ROOT = 'Walmart_Vision'


def build(output):
    output = Path(output).resolve()
    if output.exists() or output.with_suffix('.sha256').exists():
        raise ValueError('La entrega ya existe; usa un nombre nuevo para conservarla.')
    output.parent.mkdir(parents=True, exist_ok=True)
    entries = {}
    with tempfile.TemporaryDirectory(prefix='walmart_apps_') as temporary:
        team_zip = Path(temporary) / 'equipo.zip'
        build_team(team_zip, v3=True)
        with zipfile.ZipFile(team_zip) as archive:
            for info in archive.infolist():
                relative = Path(info.filename).relative_to('Walmart_Vision').as_posix()
                entries['Aplicacion/' + relative] = archive.read(info)
    for name in CLIENT_FILES:
        body = (ROOT / 'Aplicacion_Cliente' / name).read_bytes()
        if name.endswith('.cmd'):
            body = body.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        entries['Aplicacion_Cliente/' + name] = body
    entries['compose.apps.yaml'] = (ROOT / 'compose.apps.yaml').read_bytes().replace(b'\r\n', b'\n')
    for name, target in (('iniciar_cliente.cmd', 'Aplicacion_Cliente\\iniciar_cliente.cmd'),
                         ('iniciar_equipo.cmd', 'Aplicacion\\iniciar.cmd')):
        entries[name] = ('@echo off\r\ncall "%~dp0' + target + '" %*\r\n').encode()
    entries['LEEME.md'] = """# Walmart Visión · prueba de cliente y equipo · 10/11/2026

Extrae todo el ZIP en una carpeta con permisos de escritura.

- Windows x64: abre `iniciar_cliente.cmd` (puerto 8098) o `iniciar_equipo.cmd` (8095).
  El primer inicio descarga Python 3.12 y dependencias en Aplicacion; requiere Internet.
- macOS/Linux con Docker Desktop: desde esta carpeta ejecuta
  `docker compose -f compose.apps.yaml up --build -d --wait`.
  Abre http://127.0.0.1:8098 (cliente) y http://127.0.0.1:8095 (equipo).
  Para detener: `docker compose -f compose.apps.yaml down`.

Cliente: fotos propias, prioridades, checklist y hoja CSV. Equipo: marcado por nivel/zona,
comparación y exportación de lotes de revisión. Consulta los README de ambas carpetas
y Aplicacion/REVISION_EQUIPO.md. Cada colega ejecuta su copia local; los lotes se comparten
manualmente. No hay sincronización entre computadores ni alojamiento web de las apps.
El dataset y las fotos del catálogo local de demostración no se incluyen: carga tus fotos.

Usa el modelo oficial del 5/11 y Línea A del 8/11, índice visual preliminar de 0 a 100,
umbral 52. No mide porcentaje físico de stock ni detecta personas u obstáculos.
Revisa los contornos y la visibilidad. Es una versión de prueba, sin evaluación final.
La release del 5/11 se conserva como distribución histórica independiente.
""".encode('utf-8')
    manifest = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(entries.items())}
    entries['MANIFIESTO_SHA256.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, body in entries.items():
            archive.writestr(PACKAGE_ROOT + '/' + name, body)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('El ZIP no pasó la comprobación de integridad.')
        for name, digest in manifest.items():
            if hashlib.sha256(archive.read(PACKAGE_ROOT + '/' + name)).hexdigest() != digest:
                raise ValueError('Hash incorrecto: ' + name)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256').write_text(digest + '  ' + output.name + '\n', encoding='utf-8')
    return {'zip': str(output), 'bytes': output.stat().st_size, 'sha256': digest,
            'files': len(entries), 'apps': ['cliente', 'equipo']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False, indent=2))
