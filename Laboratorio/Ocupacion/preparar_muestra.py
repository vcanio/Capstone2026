"""Construir y verificar la muestra congelada de desarrollo para calibrar ocupación.

Incluye las 93 fotos elegibles de validación del modelo oficial V3 (59 reales y
34 sintéticas) más 70 fotos de entrenamiento estrictamente disjuntas por escena
(46 reales diversas + 24 variantes de baja disponibilidad/vacías), sin acceder a test
ni modificar anotaciones de CVAT.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
import almacenamiento_datos as storage
sys.path.insert(0, str(ROOT / 'Aplicacion'))
from presentacion_niveles import spatial_order

NOV5_INFORME = ROOT / 'Datos/Preparados/V3/v3_20261105_012333_53df4a59/informe.json'
NOV5_EXPORT_IMAGES = ROOT / 'Datos/Preparados/V3/v3_20261105_012333_53df4a59/exportacion_71b4668d/images'
NOV2_INFORME = ROOT / 'Datos/Preparados/V3/v3_20261102_182957_ebfc930d/informe.json'
NOV2_EXPORT_IMAGES = ROOT / 'Datos/Preparados/V3/v3_20261102_182957_ebfc930d/exportacion_ef996971/images'
OUTPUT_DIR = ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107'
OUTPUT_MANIFEST = OUTPUT_DIR / 'muestra_desarrollo.json'

SEED_SELECTION = 42
SEED_QUEUE_ORDER = 20261107
TARGET_TRAIN_REAL = 46
TARGET_TRAIN_SYNTH_PER_BUCKET = 6  # A_vacios, B_baja, C_mixta, D_superior_vacio -> 24 sintéticas


def _img_id(entry):
    return entry.get('imagen_id') or Path(entry['name']).stem


def _shape_boxes_and_polygons(shapes):
    boxes = []
    polygons = []
    meta = []
    for shape in shapes:
        pts = shape['points']
        pairs = [[round(float(pts[i]), 2), round(float(pts[i + 1]), 2)] for i in range(0, len(pts), 2)]
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        boxes.append([min(xs), min(ys), max(xs), max(ys)])
        polygons.append(pairs)
        meta.append({
            'cvat_shape_id': shape.get('id'),
            'delimitacion': shape.get('delimitacion', 'completa'),
            'occluded': bool(shape.get('occluded', False)),
        })
    order = spatial_order(boxes)
    levels = []
    for level_number, idx in enumerate(order, 1):
        levels.append({
            'level_id': level_number,
            'bbox': [round(v, 2) for v in boxes[idx]],
            'polygon': polygons[idx],
            **meta[idx],
        })
    return levels


def _resolve_fast_image(entry, export_root, split):
    """Usar copia ya orientada EXIF de la exportación si existe; si no, la fuente original."""
    stem_candidates = [
        export_root / split / entry['name'],
        export_root / f"{split}_{entry['origen']}" / entry['name'],
        export_root / ('val_real' if split == 'val' and entry['origen'] == 'real' else 'val_sintetica') / entry['name'],
    ]
    for candidate in stem_candidates:
        logical = candidate.relative_to(ROOT).as_posix()
        if storage.read_path(ROOT, logical).is_file():
            return candidate.relative_to(ROOT).as_posix(), True
    source = storage.read_path(ROOT, entry['path'])
    if not source.is_file():
        raise FileNotFoundError(f"No se encontró la imagen fuente: {entry['path']}")
    return Path(entry['path']).as_posix(), False


def build_manifest():
    nov5 = json.loads(NOV5_INFORME.read_text(encoding='utf-8'))
    nov2 = json.loads(NOV2_INFORME.read_text(encoding='utf-8'))

    elig_nov5 = [img for img in nov5['images'] if img.get('eligible') and img.get('shapes')]
    val_entries = [img for img in elig_nov5 if img['split'] == 'val']
    train_nov5 = [img for img in elig_nov5 if img['split'] == 'train']

    if len(val_entries) != 93:
        raise ValueError(f'Se esperaban 93 fotos elegibles en val y se encontraron {len(val_entries)}.')

    # Escenas y familias prohibidas para train (todo val + exclusiones conservadoras de partición).
    blocked_scenes = {img['grupo_escena'] for img in nov5['images'] if img['split'] != 'train' or not img.get('eligible')}
    blocked_scenes |= {'le_g10', 'le_g18'}
    val_scenes = {img['grupo_escena'] for img in val_entries}
    val_families = {img.get('familia') for img in val_entries if img.get('familia')}
    val_shas = {img['sha256'] for img in val_entries}

    rng = random.Random(SEED_SELECTION)

    # 1. Seleccionar 46 fotos reales de train maximizando diversidad de escenas (1 por grupo_escena primero).
    real_train_pool = [
        img for img in train_nov5
        if img['origen'] == 'real'
        and 'visibilidad_limitada' not in img['path']
        and img['grupo_escena'] not in val_scenes
        and img.get('familia') not in val_families
        and img['sha256'] not in val_shas
    ]
    by_scene = defaultdict(list)
    for img in sorted(real_train_pool, key=_img_id):
        by_scene[img['grupo_escena']].append(img)

    scene_keys = sorted(by_scene.keys())
    rng.shuffle(scene_keys)
    selected_train_real = []
    for scene in scene_keys:
        if len(selected_train_real) >= TARGET_TRAIN_REAL:
            break
        choices = by_scene[scene]
        selected_train_real.append(choices[rng.randrange(len(choices))])

    if len(selected_train_real) < TARGET_TRAIN_REAL:
        picked_shas = {x['sha256'] for x in selected_train_real}
        leftovers = [x for x in sorted(real_train_pool, key=_img_id) if x['sha256'] not in picked_shas]
        rng.shuffle(leftovers)
        selected_train_real.extend(leftovers[:TARGET_TRAIN_REAL - len(selected_train_real)])

    # 2. Seleccionar 24 variantes sintéticas de train (6 A_vacios, 6 B_baja, 6 C_mixta, 6 D_superior_vacio)
    # estrictamente en escenas exclusivas de train del ensayo vigente.
    allowed_train_scenes = {img['grupo_escena'] for img in real_train_pool} - blocked_scenes - val_scenes

    synth_d_pool = [
        img for img in train_nov5
        if img['origen'] == 'sintetica'
        and '_D_' in img['name']
        and img['grupo_escena'] in allowed_train_scenes
        and img['sha256'] not in val_shas
    ]
    rng.shuffle(synth_d_pool)
    selected_d = sorted(synth_d_pool[:TARGET_TRAIN_SYNTH_PER_BUCKET], key=_img_id)

    elig_nov2_train = [
        img for img in nov2['images']
        if img.get('eligible')
        and img.get('shapes')
        and img['split'] == 'train'
        and img['origen'] == 'sintetica'
        and 'visibilidad_limitada' not in img['path']
        and img['grupo_escena'] in allowed_train_scenes
        and img.get('familia') not in val_families
        and img['sha256'] not in val_shas
    ]

    selected_abc = []
    used_abc_scenes = set()
    for tag in ('_A_', '_B_', '_C_'):
        bucket = [img for img in sorted(elig_nov2_train, key=_img_id) if tag in img['name']]
        rng.shuffle(bucket)
        # Preferir escenas distintas entre sí para cubrir más góndolas.
        prioritized = [x for x in bucket if x['grupo_escena'] not in used_abc_scenes] + [
            x for x in bucket if x['grupo_escena'] in used_abc_scenes
        ]
        chosen = prioritized[:TARGET_TRAIN_SYNTH_PER_BUCKET]
        if len(chosen) != TARGET_TRAIN_SYNTH_PER_BUCKET:
            raise ValueError(f'No hay suficientes candidatos en train para variante {tag}: {len(chosen)}')
        used_abc_scenes.update(x['grupo_escena'] for x in chosen)
        selected_abc.extend(sorted(chosen, key=_img_id))

    selected_train = selected_train_real + selected_abc + selected_d
    if len(selected_train) != 70:
        raise ValueError(f'Se esperaban 70 fotos en train y se obtuvieron {len(selected_train)}.')

    # Construir registros normalizados y comprobar separación estricta de escenas y hashes.
    nov2_ids = {id(x) for x in selected_abc}
    records = []
    for item in val_entries + selected_train:
        is_nov2 = id(item) in nov2_ids
        export_dir = NOV2_EXPORT_IMAGES if is_nov2 else NOV5_EXPORT_IMAGES
        serve_path, pre_oriented = _resolve_fast_image(item, export_dir, item['split'])
        levels = _shape_boxes_and_polygons(item['shapes'])
        img_id = _img_id(item)
        records.append({
            'item_key': f"{item['split']}::{img_id}::{item['sha256'][:10]}",
            'imagen_id': img_id,
            'name': item['name'],
            'source_path': Path(item['path']).as_posix(),
            'serve_path': serve_path,
            'serve_pre_oriented': pre_oriented,
            'sha256': item['sha256'],
            'width': int(item['width']),
            'height': int(item['height']),
            'exif_orientation': int(item.get('exif_orientation', 1)),
            'split': item['split'],
            'origen': item['origen'],
            'variante': item.get('variante') or (
                'A_vacios' if '_A_' in item['name'] else
                'B_baja' if '_B_' in item['name'] else
                'C_mixta' if '_C_' in item['name'] else
                'D_superior_vacio' if '_D_' in item['name'] else 'original'
            ),
            'grupo_escena': item['grupo_escena'],
            'familia': item.get('familia'),
            'provenance_export': (
                'Datos/Preparados/V3/v3_20261102_182957_ebfc930d/informe.json'
                if is_nov2 else 'Datos/Preparados/V3/v3_20261105_012333_53df4a59/informe.json'
            ),
            'level_count': len(levels),
            'levels': levels,
        })

    # Verificaciones duras de integridad
    seen_shas = set()
    train_scenes_final = set()
    val_scenes_final = set()
    for rec in records:
        if rec['sha256'] in seen_shas:
            raise ValueError(f"Imagen duplicada por SHA-256 en la muestra: {rec['name']}")
        seen_shas.add(rec['sha256'])
        if rec['split'] == 'val':
            val_scenes_final.add(rec['grupo_escena'])
        else:
            train_scenes_final.add(rec['grupo_escena'])

    leak = train_scenes_final & val_scenes_final
    if leak:
        raise ValueError(f'Fuga de escenas entre train y val detectada: {sorted(leak)}')

    # Orden determinista mezclado para etiquetado ciego sin sesgo secuencial de variantes.
    queue_rng = random.Random(SEED_QUEUE_ORDER)
    indices = list(range(len(records)))
    queue_rng.shuffle(indices)
    for queue_pos, rec_idx in enumerate(indices, 1):
        records[rec_idx]['blind_order'] = queue_pos
        records[rec_idx]['blind_code'] = f"G-{queue_pos:03d}"

    records.sort(key=lambda r: r['blind_order'])

    split_origin = Counter((r['split'], r['origen']) for r in records)
    variant_counts = Counter((r['split'], r['variante']) for r in records)
    manifest = {
        'schema_version': 1,
        'id': 'calibracion_ocupacion_v3_20261107',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'seed_selection': SEED_SELECTION,
        'seed_blind_order': SEED_QUEUE_ORDER,
        'partition_reference': 'Datos/Registros/Particiones/v3_refuerzo_geometria_20261104/particion.json',
        'test_used': False,
        'cvat_modified': False,
        'summary': {
            'total_images': len(records),
            'total_levels': sum(r['level_count'] for r in records),
            'val_images': sum(1 for r in records if r['split'] == 'val'),
            'val_real': split_origin[('val', 'real')],
            'val_sintetica': split_origin[('val', 'sintetica')],
            'val_scenes': len(val_scenes_final),
            'train_images': sum(1 for r in records if r['split'] == 'train'),
            'train_real': split_origin[('train', 'real')],
            'train_sintetica': split_origin[('train', 'sintetica')],
            'train_scenes': len(train_scenes_final),
            'scene_overlap_train_val': 0,
            'variants_by_split': {f'{k[0]}_{k[1]}': v for k, v in sorted(variant_counts.items())},
        },
        'label_schema': {
            'suficiente': {'key': '1', 'alert': False, 'evaluable': True, 'label': 'Suficiente'},
            'baja_disponibilidad': {'key': '2', 'alert': True, 'evaluable': True, 'label': 'Baja disponibilidad'},
            'vacio': {'key': '3', 'alert': True, 'evaluable': True, 'label': 'Vacío'},
            'no_evaluable': {'key': '0', 'alert': None, 'evaluable': False, 'label': 'No evaluable / Dudoso'},
        },
        'images': records,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


if __name__ == '__main__':
    result = build_manifest()
    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
