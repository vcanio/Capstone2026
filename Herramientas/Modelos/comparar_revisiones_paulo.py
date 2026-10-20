"""Comparar dos revisiones de señal conservando las mismas detecciones YOLO."""
import argparse
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from conjuntos import dataset_directory
from ocupacion_paulo import ROOT
from piloto_modulos import font_path


def compare(before, after):
    records = []
    for path in sorted(after.glob('*/resultados.json')):
        old = json.loads((before / path.parent.name / path.name).read_text(encoding='utf-8'))
        new = json.loads(path.read_text(encoding='utf-8'))
        for key in ('weights_sha256', 'manifest_sha256', 'yolo_validation'):
            if old[key] != new[key]:
                raise ValueError('La comparación requiere los mismos pesos, datos y resultados YOLO: ' + key)
        old_rows = {(r['foto'], r['nivel']): r for r in old['levels']}
        new_rows = {(r['foto'], r['nivel']): r for r in new['levels']}
        if old_rows.keys() != new_rows.keys():
            raise ValueError('Cambió el conjunto de detecciones.')
        for key, new_row in new_rows.items():
            old_row = old_rows[key]
            if any(old_row[k] != new_row[k] for k in ('estado_yolo', 'confianza_yolo', 'estado_anotado', 'iou_referencia')):
                raise ValueError('Una detección cambió; no atribuir su diferencia solo al método de señal.')
            records.append({'run': new['run'], 'foto': key[0], 'nivel': key[1],
                'estado_yolo': new_row['estado_yolo'], 'estado_anotado': new_row['estado_anotado'],
                'area_antes': old_row['area_signal_pct'], 'area_despues': new_row['area_signal_pct'],
                'ancho_antes': old_row['width_signal_pct'], 'ancho_despues': new_row['width_signal_pct']})
    if not records: raise ValueError('No hay resultados para comparar.')
    output = {'same_yolo_results': True, 'occupancy_accuracy': None,
              'note': 'Cambios de señal, no error de ocupación: faltan referencias numéricas.', 'levels': records}
    (after / 'comparacion_anterior.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    case = next((r for r in records if r['estado_anotado'] == 'reponer' and r['area_antes'] is not None and r['area_despues'] is not None), None)
    if case:
        run = ROOT / 'Experimentos' / case['run']
        manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
        with Image.open(dataset_directory(ROOT, run, manifest) / 'images/val' / case['foto']) as original:
            thumb = original.copy(); thumb.thumbnail((850, 680)); width, height = thumb.size
        panel = Image.new('RGB', (2*width+30, height+130), '#111827')
        font = ImageFont.truetype(str(font_path()), 18); draw = ImageDraw.Draw(panel)
        for index, directory in enumerate((before, after)):
            source = directory / case['run'] / (Path(case['foto']).stem + '.jpg')
            with Image.open(source) as comparison:
                panel.paste(comparison.crop((850, 50, 850+width, 50+height)), (10+index*(width+10), 90))
        for index, suffix in enumerate(('antes', 'despues')):
            x = 10+index*(width+10)
            draw.text((x, 10), ('Antes · oscuridad' if index == 0 else 'Ahora · color y textura'), font=font, fill='white')
            draw.text((x, 40), f"Área: {case['area_'+suffix]:.2f}% | Ancho: {case['ancho_'+suffix]:.2f}%", font=font, fill='white')
        draw.text((10, height+100), 'Misma foto y detecciones. Porcentajes experimentales de señal.', font=font, fill='white')
        panel.save(after / 'antes_despues_040.jpg', quality=92)
        report_path = after / 'informe.html'
        report = report_path.read_text(encoding='utf-8')
        section = f'<h2>Corrección del fondo oscuro · misma detección</h2><p>{html.escape(case["foto"])} · nivel {case["nivel"]}, anotado reponer. Área con señal: {case["area_antes"]}% → {case["area_despues"]}%. Ancho con señal: {case["ancho_antes"]}% → {case["ancho_despues"]}%. Esto verifica una corrección concreta; no mide la precisión global del porcentaje.</p><img src="antes_despues_040.jpg" alt="Antes el fondo oscuro aparece activado; después la señal se concentra en zonas con color o textura">'
        report = report.replace('YOLO + detección de bordes · primera comparación', 'YOLO + detección de bordes · revisión 2: color y textura')
        index = report.index('<h2>')
        report_path.write_text(report[:index]+section+report[index:], encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    arguments = parser.parse_args()
    result = compare(arguments.before, arguments.after)
    print(f"Comparadas {len(result['levels'])} detecciones con resultados YOLO idénticos.")
