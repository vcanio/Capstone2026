"""Preparación independiente y conservadora del piloto de visibilidad.

Esta herramienta no escribe en CVAT, no inicia entrenamientos y nunca abre test.
Las etiquetas de salida comienzan pendientes y requieren revisión humana.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'Datos/Preparados/V3/v3_20261030_044237_fdcab79c/informe.json'
PARTITION = ROOT / 'Datos/Registros/Particiones/v3_469_afinado_20261025/particion.json'
EXPECTED_PARTITION = 'd0889ff3612f6270db384ad1e77841137979e8a5b5ef5734696a1942fcd37031'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_path(row):
    """Resolver los dos antiguos accesos V2 a sus ubicaciones físicas V3."""
    value = row.get('path')
    if not isinstance(value, str):
        raise ValueError('Falta la ruta de la imagen.')
    for prefix in ('lider_express_20261016', 'visibilidad_limitada_20261019'):
        old = f'Datos/V2/{prefix}/'
        if value.startswith(old):
            value = f'Datos/V3/{prefix}/' + value[len(old):]
            break
    path = (ROOT / value).resolve()
    if not path.is_relative_to((ROOT / 'Datos').resolve()) or not path.is_file():
        raise ValueError('Fuente de imagen fuera de Datos o inexistente: ' + row.get('name', ''))
    return path


def full_frame(image, size=640):
    """Conservar la imagen entera, corregir orientación y añadir márgenes."""
    rgba = ImageOps.exif_transpose(image).convert('RGBA')
    image = Image.new('RGB', rgba.size, 'white')
    image.paste(rgba, mask=rgba.getchannel('A'))
    image.thumbnail((4096, 4096))
    return ImageOps.pad(image, (size, size), method=Image.Resampling.BILINEAR,
                        color=(114, 114, 114), centering=(.5, .5))


def decision(score, threshold):
    if not math.isfinite(score) or not math.isfinite(threshold) or not 0 <= score <= 1 or not .5 <= threshold <= .99:
        raise ValueError('Puntuación o umbral fuera de rango.')
    if score < .5:
        return 'no_apta'
    return 'apta' if score >= threshold else 'dudosa'


def calibrate(rows):
    """Umbral mínimo sin falsos aceptados y con al menos 80 % de aptas."""
    rows = list(rows)
    if any(label not in ('apta', 'no_apta') or not math.isfinite(score) or not 0 <= score <= 1 for label, score in rows):
        raise ValueError('Etiquetas o puntuaciones inválidas.')
    aptas = [score for label, score in rows if label == 'apta']
    blocked = [score for label, score in rows if label == 'no_apta']
    if not aptas or not blocked:
        raise ValueError('La calibración requiere ambas clases.')
    for step in range(50, 100):
        threshold = step / 100
        if not any(score >= threshold for score in blocked) and sum(score >= threshold for score in aptas) / len(aptas) >= .8:
            return threshold
    return None


def build_inventory():
    if sha256(PARTITION) != EXPECTED_PARTITION:
        raise ValueError('La partición activa no coincide con la versión revisada.')
    report = json.loads(REPORT.read_text(encoding='utf-8-sig'))
    if report['partition_sha256'] != EXPECTED_PARTITION:
        raise ValueError('El informe no corresponde a la partición esperada.')
    rows = []
    for image in report['images']:
        if image['split'] not in ('train', 'val') or not image['eligible']:
            continue
        source = ROOT / image['path']
        if not source.is_file() or sha256(source) != image['sha256']:
            raise ValueError(f"Imagen ausente o modificada: {image['name']}")
        rows.append({key: image[key] for key in ('name', 'path', 'sha256', 'split', 'origen',
                                                  'familia', 'grupo_escena', 'cvat_task_id',
                                                  'cvat_name', 'frame')})
        rows[-1].update(etiqueta='pendiente', motivo=None)
    if Counter(row['split'] for row in rows) != {'train': 336, 'val': 69}:
        raise ValueError('Los recuentos de desarrollo no coinciden con el plan.')
    return {'schema': 'visibilidad_foto_revision_v1', 'partition_sha256': EXPECTED_PARTITION,
            'source_report_sha256': sha256(REPORT), 'test_included': False, 'images': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--crear-inventario', type=Path, required=True,
                        help='Ruta nueva dentro del proyecto; no sobrescribe archivos.')
    args = parser.parse_args()
    target = args.crear_inventario.resolve()
    if not target.is_relative_to(ROOT / 'Datos/Preparados/V3'):
        raise ValueError('El inventario debe guardarse en Datos/Preparados/V3.')
    inventory = build_inventory()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(f"Inventario creado: {len(inventory['images'])} imágenes pendientes; test excluido.")


if __name__ == '__main__':
    main()
