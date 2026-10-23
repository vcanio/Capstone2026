"""Copias recortadas para revision visual; no escribe en CVAT ni exporta entrenamiento."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
SOURCE = ROOT / 'Datos/V3/Lider 2'
BOXES = {
    1: (245, 180, 2880, 3780),
    2: (345, 200, 2860, 3780),
    3: (300, 160, 2820, 3740),
    4: (200, 160, 2730, 3740),
    5: (280, 300, 2715, 3790),
}
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 23)
SMALL = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 19)
annotations = json.loads((OUT / 'anotaciones_cvat_lectura.json').read_text(encoding='utf-8'))
metadata = json.loads((OUT / 'meta_cvat.json').read_text(encoding='utf-8'))
manifest = {
    'state': 'vista_previa_no_aprobada_para_entrenamiento',
    'source_job': 67,
    'source_task': 28,
    'cvat_modified': False,
    'original_files_modified': False,
    'transform': 'EXIF transpose, then rectangular crop; no resizing in PNG files',
    'notes': [
        'Recorte conservador: conserva contexto superior y estructura del tramo central.',
        'La perspectiva deja fragmentos laterales; el recorte no demuestra anotacion exhaustiva.',
        'Solo se trasladan las anotaciones manuales existentes. No se anota el nivel superior.',
        'No asignar estos recortes a una particion diferente de su imagen y escena de origen.',
    ],
    'images': [],
}
preview_annotations = []
contact = Image.new('RGB', (1260, 1300), '#f4f4f2')
annotated_contact = contact.copy()
comparison = Image.new('RGB', (1680, 1000), '#f4f4f2')
dc = ImageDraw.Draw(comparison)
dc.text((25, 15), 'Original y ventana de recorte / copia recortada', font=FONT, fill='#151515')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for number, box in BOXES.items():
    name = f'lider_2_{number:03}_0_original.jpg'
    frame = number - 1
    assert metadata['frames'][frame]['name'] == name
    source = SOURCE / name
    before_hash = sha(source)
    original = ImageOps.exif_transpose(Image.open(source)).convert('RGB')
    assert original.size == (3000, 4000)
    cropped = original.crop(box)
    raw_path = OUT / f'lider_2_{number:03}_recorte.png'
    cropped.save(raw_path)
    with Image.open(raw_path) as saved:
        assert saved.size == cropped.size and saved.tobytes() == cropped.tobytes()
    assert sha(source) == before_hash

    shapes = [s for s in annotations['shapes'] if s['frame'] == frame]
    copied_shapes = []
    overlay = Image.new('RGBA', cropped.size)
    draw = ImageDraw.Draw(overlay)
    for shape in shapes:
        assert shape['type'] == 'polygon'
        transformed = copy.deepcopy(shape)
        transformed['source_shape_id'] = transformed.pop('id')
        p = shape['points']
        assert all(box[0] <= p[i] < box[2] and box[1] <= p[i+1] < box[3]
                   for i in range(0, len(p), 2)), 'El recorte cortaria un poligono existente.'
        transformed['points'] = [v - box[i % 2] for i, v in enumerate(p)]
        assert all(abs(transformed['points'][i] + box[i % 2] - v) < 1e-8
                   for i, v in enumerate(p))
        copied_shapes.append(transformed)
        points = list(zip(transformed['points'][::2], transformed['points'][1::2]))
        draw.polygon(points, fill=(18, 125, 220, 40), outline=(0, 100, 220, 255), width=9)
    annotated = Image.alpha_composite(cropped.convert('RGBA'), overlay).convert('RGB')
    annotated.save(OUT / f'lider_2_{number:03}_recorte_anotaciones.jpg', quality=94)
    preview_annotations.append({'file': raw_path.name, 'source_file': name,
                                'source_frame': frame, 'shapes': copied_shapes})
    manifest['images'].append({
        'source': str(source.relative_to(ROOT)),
        'source_sha256': before_hash,
        'source_oriented_size': list(original.size),
        'crop_xyxy': list(box),
        'crop_file': raw_path.name,
        'crop_size': list(cropped.size),
        'crop_sha256': sha(raw_path),
        'copied_manual_shapes': len(shapes),
        'new_shapes': 0,
        'source_polygons_contained': True,
        'original_hash_preserved': True,
        'saved_pixels_match_source_crop': True,
    })

    col, row = (number - 1) % 3, (number - 1) // 3
    for sheet, picture in [(contact, cropped), (annotated_contact, annotated)]:
        picture = ImageOps.contain(picture, (400, 590))
        x, y = col * 420 + (420-picture.width)//2, row * 650 + 48
        sheet.paste(picture, (x, y))
        d = ImageDraw.Draw(sheet)
        d.text((col*420 + 14, row*650 + 13),
               f'{number:03}  |  {cropped.width} x {cropped.height} px', font=FONT, fill='#151515')

    # Una columna por escena: original arriba, recorte abajo.
    x = (number - 1) * 336
    original_view = original.copy()
    ImageDraw.Draw(original_view).rectangle(box, outline=(255, 195, 0), width=20)
    original_view = ImageOps.contain(original_view, (310, 420))
    crop_view = ImageOps.contain(cropped, (310, 450))
    comparison.paste(original_view, (x+(336-original_view.width)//2, 85))
    comparison.paste(crop_view, (x+(336-crop_view.width)//2, 535))
    dc.text((x+16, 55), f'{number:03} · original', font=SMALL, fill='#151515')
    dc.text((x+16, 510), f'{number:03} · recorte', font=SMALL, fill='#151515')

contact.save(OUT / 'recortes_001_005.jpg', quality=94)
annotated_contact.save(OUT / 'recortes_001_005_anotaciones.jpg', quality=94)
comparison.save(OUT / 'comparacion_001_005.jpg', quality=94)
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
(OUT / 'anotaciones_recortadas_vista_previa.json').write_text(
    json.dumps(preview_annotations, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'images': len(manifest['images']),
                  'preserved_manual_shapes': sum(x['copied_manual_shapes'] for x in manifest['images']),
                  'original_hashes_and_saved_crop_pixels_verified': True,
                  'output': str(OUT)}, ensure_ascii=False))
