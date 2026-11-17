"""Preparación reproducible de anotaciones CVAT a formato YOLO-seg (criterio V3).

Incluye:
- Regla de la mediana sobre portaprecio para niveles superiores abiertos.
- Validación anti-fuga por escenas y SHA-256 entre train, val y test.
- Normalización de polígonos de clase única `Nivel` a YOLO-seg.
- Normalización EXIF de píxeles preservando coordenadas CVAT originales.
"""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import shutil
import statistics
import tempfile


def _to_pairs(points):
    """Normalizar puntos [[x, y], ...] o [x0, y0, ...] a lista de tuplas float."""
    if not points:
        raise ValueError('Polígono vacío.')
    if isinstance(points[0], (list, tuple)):
        pairs = [(float(p[0]), float(p[1])) for p in points]
    else:
        if len(points) % 2 != 0:
            raise ValueError('Lista de coordenadas impar.')
        pairs = [(float(points[i]), float(points[i + 1])) for i in range(0, len(points), 2)]
    if len(pairs) < 3 or any(not (math.isfinite(x) and math.isfinite(y)) for x, y in pairs):
        raise ValueError('Polígono inválido o con coordenadas no finitas.')
    return pairs


def polygon_area(points) -> float:
    """Área absoluta de un polígono mediante la fórmula del lazo (Shoelace)."""
    pairs = _to_pairs(points)
    area = 0.0
    n = len(pairs)
    for i in range(n):
        x1, y1 = pairs[i]
        x2, y2 = pairs[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def project_open_top_shelf_by_median(
    lower_polygons: list,
    support_left: tuple[float, float],
    support_right: tuple[float, float],
    img_width: int,
    img_height: int,
) -> dict:
    """Proyectar nivel superior abierto usando la mediana de altura de inferiores.

    Aplica el criterio oficial V3:
    1. Calcula la altura central de cada polígono inferior del mismo módulo.
    2. Obtiene la mediana exacta sin redondear.
    3. Proyecta hacia arriba desde los puntos de apoyo sobre el portaprecio.
    4. Si la proyección supera el borde superior (y < 0), recorta al encuadre
       y marca `delimitacion='parcial'`.
    """
    if not lower_polygons:
        raise ValueError('Se requieren polígonos inferiores para proyectar el nivel superior.')
    ul_x, yl = float(support_left[0]), float(support_left[1])
    ur_x, yr = float(support_right[0]), float(support_right[1])
    if ur_x <= ul_x:
        raise ValueError('support_right debe estar a la derecha de support_left.')
    if img_width <= 1 or img_height <= 1:
        raise ValueError('Dimensiones de imagen inválidas.')

    heights = []
    for poly in lower_polygons:
        pairs = _to_pairs(poly)
        if len(pairs) < 4:
            raise ValueError('Cada nivel inferior de referencia requiere al menos 4 vértices.')
        ys = sorted(p[1] for p in pairs)
        height = (ys[-2] + ys[-1] - ys[0] - ys[1]) / 2.0
        if height <= 0:
            raise ValueError('Altura de referencia no positiva.')
        heights.append(height)

    median_height = statistics.median(heights)
    full_projection = [
        [ul_x, yl - median_height],
        [ur_x, yr - median_height],
        [ur_x, yr],
        [ul_x, yl],
    ]
    clipped = any(
        x < 0.0 or y < 0.0 or x > float(img_width) or y > float(img_height)
        for x, y in full_projection
    )
    points = [
        [min(float(img_width), max(0.0, x)), min(float(img_height), max(0.0, y))]
        for x, y in full_projection
    ]
    return {
        'points': points,
        'full_projection': full_projection,
        'median_height': median_height,
        'clipped': clipped,
        'delimitacion': 'parcial' if clipped else 'completa',
        'references_count': len(heights),
    }


def validate_scene_partition(records: list[dict]) -> dict:
    """Verificar partición anti-fuga por escena (`grupo_escena`) y SHA-256."""
    scenes_by_split: dict[str, set[str]] = defaultdict(set)
    hashes_by_split: dict[str, set[str]] = defaultdict(set)
    counts: dict[str, int] = defaultdict(int)

    for row in records:
        split = row.get('split')
        if split not in ('train', 'val', 'test'):
            raise ValueError(f'Split inválido: {split!r}')
        scene = row.get('grupo_escena')
        sha = row.get('sha256')
        if not scene or not sha:
            raise ValueError('Cada registro debe incluir grupo_escena y sha256.')
        scenes_by_split[split].add(scene)
        hashes_by_split[split].add(sha)
        counts[split] += 1

    splits = ('train', 'val', 'test')
    for i, a in enumerate(splits):
        for b in splits[i + 1:]:
            shared_scenes = scenes_by_split[a] & scenes_by_split[b]
            if shared_scenes:
                raise ValueError(f'Fuga de escena entre {a} y {b}: {sorted(shared_scenes)[:5]}')
            shared_hashes = hashes_by_split[a] & hashes_by_split[b]
            if shared_hashes:
                raise ValueError(f'SHA-256 duplicado entre {a} y {b}: {len(shared_hashes)} archivos')

    return {
        'counts': dict(counts),
        'scenes': {k: len(v) for k, v in scenes_by_split.items()},
        'unique_sha256': sum(len(v) for v in hashes_by_split.values()),
    }


def polygon_to_yolo_seg_line(points, width: int, height: int, class_id: int = 0) -> str:
    """Convertir un polígono en píxeles a una línea normalizada YOLO-seg."""
    if width <= 1 or height <= 1:
        raise ValueError('Dimensiones inválidas para normalización.')
    pairs = _to_pairs(points)
    if polygon_area(pairs) <= 1.0:
        raise ValueError('Polígono degenerado (área <= 1 px²).')
    normalized = []
    for x, y in pairs:
        if not (-1e-6 <= x <= width + 1e-6 and -1e-6 <= y <= height + 1e-6):
            raise ValueError('Coordenada fuera del encuadre de la imagen.')
        nx = min(float(width), max(0.0, x)) / float(width)
        ny = min(float(height), max(0.0, y)) / float(height)
        normalized.append(f'{nx:.6f} {ny:.6f}')
    return f'{int(class_id)} ' + ' '.join(normalized)


def orient_image_preserving_cvat_polygons(
    source_path: Path,
    target_path: Path,
    expected_width: int | None = None,
    expected_height: int | None = None,
) -> dict:
    """Aplicar `exif_transpose` sobre píxeles sin alterar coordenadas CVAT."""
    from PIL import Image, ImageOps

    source_path = Path(source_path)
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as photo:
        orientation = int(photo.getexif().get(274, 1))
        oriented = ImageOps.exif_transpose(photo)
        if expected_width is not None and expected_height is not None:
            if oriented.size != (expected_width, expected_height):
                raise ValueError(
                    f'Dimensiones incompatibles tras orientar {source_path.name}: '
                    f'{oriented.size} != {(expected_width, expected_height)}'
                )
        if orientation != 1:
            target_path = target_path.with_suffix('.png')
            oriented.convert('RGB').save(target_path, format='PNG', compress_level=1)
        else:
            shutil.copy2(source_path, target_path)
    return {
        'prepared_path': str(target_path),
        'orientation': orientation,
        'operation': 'exif_transpose_to_png' if orientation != 1 else 'copy',
        'polygon_coordinates_changed': False,
    }


def export_cvat_json(snapshot_path: Path, images_dir: Path, output_dir: Path, partition_path: Path | None = None) -> dict:
    """Exportar un snapshot JSON de CVAT a estructura YOLO-seg (`images/` y `labels/`)."""
    snapshot = json.loads(Path(snapshot_path).read_text(encoding='utf-8-sig'))
    partition = json.loads(Path(partition_path).read_text(encoding='utf-8-sig')) if partition_path else None
    split_by_name = {}
    if partition:
        validate_scene_partition(partition['imagenes'])
        split_by_name = {row['name']: row['split'] for row in partition['imagenes']}

    output_dir = Path(output_dir)
    exported = 0
    polygons_total = 0
    for task_entry in snapshot.get('tasks', []):
        frames = task_entry.get('meta', {}).get('frames', [])
        shapes = task_entry.get('annotations', {}).get('shapes', [])
        by_frame = defaultdict(list)
        for s in shapes:
            if s.get('type') == 'polygon':
                by_frame[s['frame']].append(s)
        for frame_idx, meta in enumerate(frames):
            name = meta['name']
            split = split_by_name.get(name, 'train')
            src = Path(images_dir) / name
            if not src.is_file():
                continue
            dst_img = output_dir / 'images' / split / name
            info = orient_image_preserving_cvat_polygons(src, dst_img, meta.get('width'), meta.get('height'))
            stem = Path(info['prepared_path']).stem
            dst_lbl = output_dir / 'labels' / split / f'{stem}.txt'
            dst_lbl.parent.mkdir(parents=True, exist_ok=True)
            lines = [
                polygon_to_yolo_seg_line(s['points'], meta['width'], meta['height'], class_id=0)
                for s in by_frame.get(frame_idx, [])
            ]
            dst_lbl.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
            exported += 1
            polygons_total += len(lines)
    return {'exported_images': exported, 'exported_polygons': polygons_total, 'output_dir': str(output_dir)}


def run_self_check() -> dict:
    """Comprobar reglas de mediana, anti-fuga, normalización YOLO-seg y EXIF."""
    from PIL import Image

    # 1. Regla de mediana exacta sobre 4 niveles inferiores (sin redondear).
    lowers = [
        [[100, 700], [500, 700], [500, 810], [100, 810]],   # h=110
        [[100, 560], [500, 560], [500, 680], [100, 680]],   # h=120
        [[100, 420], [500, 420], [500, 545], [100, 545]],   # h=125
        [[100, 280], [500, 280], [500, 400], [100, 400]],   # h=120
    ]
    proj = project_open_top_shelf_by_median(lowers, (100, 260), (500, 265), 1000, 1000)
    assert proj['median_height'] == 120.0
    assert proj['delimitacion'] == 'completa' and not proj['clipped']
    assert proj['points'][0] == [100.0, 140.0] and proj['points'][1] == [500.0, 145.0]

    clipped_proj = project_open_top_shelf_by_median(lowers, (100, 90), (500, 95), 1000, 1000)
    assert clipped_proj['delimitacion'] == 'parcial' and clipped_proj['clipped']
    assert clipped_proj['points'][0][1] == 0.0 and clipped_proj['points'][1][1] == 0.0

    # 2. Validación anti-fuga por escenas y SHA-256.
    clean = [
        {'split': 'train', 'grupo_escena': 'e1', 'sha256': 'a1'},
        {'split': 'val', 'grupo_escena': 'e2', 'sha256': 'b1'},
        {'split': 'test', 'grupo_escena': 'e3', 'sha256': 'c1'},
    ]
    part_summary = validate_scene_partition(clean)
    assert part_summary['unique_sha256'] == 3
    try:
        validate_scene_partition(clean + [{'split': 'test', 'grupo_escena': 'e1', 'sha256': 'd1'}])
        raise AssertionError('Debió rechazar fuga de escena entre train y test.')
    except ValueError:
        pass

    # 3. Normalización YOLO-seg.
    line = polygon_to_yolo_seg_line(proj['points'], 1000, 1000, class_id=0)
    assert line.startswith('0 0.100000 0.140000 ')

    # 4. Orientación EXIF preservando dimensiones esperadas.
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        src = tmp_dir / 'rotada.jpg'
        img = Image.new('RGB', (40, 20), (200, 100, 50))
        exif = img.getexif()
        exif[274] = 6  # Rotación 90° CW -> al transponer queda 20x40.
        img.save(src, format='JPEG', exif=exif)
        info = orient_image_preserving_cvat_polygons(src, tmp_dir / 'out.jpg', 20, 40)
        assert info['operation'] == 'exif_transpose_to_png'
        assert info['polygon_coordinates_changed'] is False

    return {
        'status': 'ok',
        'median_check': proj['median_height'],
        'clipped_check': clipped_proj['delimitacion'],
        'partition_check': part_summary,
        'exif_check': info['operation'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-check', action='store_true', help='Validar reglas de mediana, anti-fuga y YOLO-seg')
    parser.add_argument('--cvat-json', type=Path, help='Snapshot JSON de CVAT a exportar')
    parser.add_argument('--images-dir', type=Path, help='Carpeta con imágenes fuente')
    parser.add_argument('--output-dir', type=Path, help='Directorio destino del dataset YOLO-seg')
    parser.add_argument('--partition-json', type=Path, help='Registro de partición anti-fuga por escenas')
    args = parser.parse_args()

    if args.self_check or not args.cvat_json:
        print(json.dumps(run_self_check(), ensure_ascii=False, indent=2))
        return

    if not args.images_dir or not args.output_dir:
        raise SystemExit('ERROR: --cvat-json requiere --images-dir y --output-dir.')
    summary = export_cvat_json(args.cvat_json, args.images_dir, args.output_dir, args.partition_json)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
