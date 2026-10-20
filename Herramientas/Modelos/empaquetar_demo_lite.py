"""Crear una entrega de inferencia con lista explícita de archivos y pesos."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Herramientas/Demo_lite'
FILES = ('app.py', 'inferencia.py', 'interfaz.html', 'requirements.txt', 'instalar.cmd', 'iniciar.cmd',
         'preparar.cmd', 'preparar.py', 'LEEME.md', 'herramientas/uv.exe', 'herramientas/fuente_uv.json',
         'herramientas/licencias/LICENSE-APACHE', 'herramientas/licencias/LICENSE-MIT')
EDGE_FILES = {'ocupacion_paulo.py': ROOT / 'Herramientas/Modelos/ocupacion_paulo.py',
              'gondola_bordes.py': ROOT / 'Experimentos/Bordes/gondola_bordes.py'}
RUNS = {'YOLO11-1': 'YOLO11-1_20261015_013749_f709', 'YOLO26-1': 'YOLO26-1_20261015_021212_c452'}
V2_RUNS = {**RUNS, 'V2-YOLO11': 'v2_base_yolo11n_01_20261020_002800_ec8d',
           'V2-YOLO26': 'v2_base_yolo26n_01_20261020_004933_b105'}


def notebook(package='Walmart_Vision_20261020.zip', default_model='V2-YOLO26'):
    cells = []

    def md(text):
        cells.append({'cell_type': 'markdown', 'id': f'markdown-{len(cells)}', 'metadata': {}, 'source': text.splitlines(keepends=True)})

    def code(text):
        cells.append({'cell_type': 'code', 'id': f'code-{len(cells)}', 'metadata': {}, 'source': text.splitlines(keepends=True), 'outputs': [], 'execution_count': None})

    md('''# Probar Walmart Visión en Google Colab

Usa los modelos entrenados YOLO11-1 y YOLO26-1 para analizar una foto, sin volver a entrenar. Ejecuta las celdas en orden.

Opcional: selecciona una GPU en **Entorno de ejecución → Cambiar tipo de entorno de ejecución**. Si no hay GPU, se usará CPU.

**Los archivos que selecciones se subirán al entorno de Google Colab.** No se monta Drive ni se publica una web. El ZIP incluye los modelos y el código; no necesitas subir el dataset.
''')
    code('''%pip -q install ultralytics==8.4.174 pillow==12.3.0 "ipywidgets>=8,<9"
''')
    md('''## Cargar el paquete

Selecciona el ZIP completo **Walmart_Lite_Automatico_20261015.zip** cuando aparezca el botón. La carga puede tardar según tu conexión.
''')
    code('''from google.colab import files
from pathlib import Path
from io import BytesIO
import sys, zipfile

paquetes = files.upload()
zip_names = [name for name in paquetes if name.lower().endswith('.zip')]
if len(zip_names) != 1:
    raise ValueError('Selecciona un único ZIP de Walmart Visión.')
destino = Path('/content/walmart_vision').resolve()
destino.mkdir(exist_ok=True)
with zipfile.ZipFile(BytesIO(paquetes[zip_names[0]])) as archive:
    if sum(item.file_size for item in archive.infolist()) > 100 * 1024 * 1024:
        raise ValueError('El ZIP supera el tamaño esperado para este paquete.')
    for item in archive.infolist():
        if not (destino / item.filename).resolve().is_relative_to(destino):
            raise ValueError('El ZIP contiene una ruta inválida.')
    archive.extractall(destino)
carpeta = destino / 'Walmart_Vision'
if not (carpeta / 'modelos.json').is_file():
    raise ValueError('El archivo no corresponde al ZIP de Walmart Visión.')
sys.path.insert(0, str(carpeta))
from inferencia import ModelRunner
visor = ModelRunner(carpeta)
print('Paquete listo. Modelos:', ', '.join(m['id'] for m in visor.available()))
''')
    md('''## 0. Seleccionar versión y modelo

Selecciona el modelo antes de subir la foto. Para comparar, puedes repetir el análisis con el otro modelo sobre la misma imagen.
''')
    code('''import ipywidgets as widgets
from IPython.display import display
modelos = visor.available()
versiones = [v for v in ('V2', 'V1') if any(('V2' if m['id'].startswith('V2-') else 'V1') == v for m in modelos)]
version = widgets.Dropdown(options=versiones, description='Versión:')
selector = widgets.Dropdown(description='Modelo:')
def actualizar_modelos(change=None):
    selector.options = [m['id'] for m in modelos if ('V2' if m['id'].startswith('V2-') else 'V1') == version.value]
    selector.value = next((m for m in selector.options if '26' in m), selector.options[0])
version.observe(actualizar_modelos, names='value')
actualizar_modelos()
display(version, selector)
''')
    md('''## Subir una foto

Elige una foto JPG, PNG o WebP de hasta 15 MB y 24 megapíxeles. Las fotografías nuevas ayudan a observar el comportamiento; esta prueba no calcula precisión contra anotaciones.
''')
    code('''fotos = files.upload()
if len(fotos) != 1:
    raise ValueError('Selecciona una sola fotografía.')
nombre_foto, contenido_foto = next(iter(fotos.items()))
print('Foto lista:', nombre_foto)
''')
    md('''## Analizar

La confianza mínima predeterminada es 0,25. Puedes cambiarla en la siguiente celda; no representa el porcentaje de producto del nivel. No evaluable no significa vacío.

Para probar el otro modelo, cambia el selector y vuelve a ejecutar esta celda. Para usar otra foto, repite la celda de carga y luego esta.
''')
    code('''confianza = 0.25
usar_bordes = True  # False para ejecutar solo YOLO.
prediccion = visor.analyze(contenido_foto, selector.value, confianza,
                          method='yolo_paulo' if usar_bordes else 'yolo')
print(f"{prediccion['model']} · {prediccion['device']} · {prediccion['seconds']} s")
print('Niveles detectados:', len(prediccion['detections']))
print('Estados:', prediccion['counts'])
from inferencia import read_photo
original = read_photo(contenido_foto)
original_view, niveles_view, bordes_view, comparar_view = [widgets.Output() for _ in range(4)]
with original_view:
    display(original)
with niveles_view:
    display(prediccion['image'])
with bordes_view:
    if usar_bordes:
        print('Amarillo: señal experimental; no es porcentaje validado de producto. YOLO determina el estado.')
        display(prediccion['occupancy_image'])
        display(prediccion['filtered_edges_image'])
        display(prediccion['edges_image'])
    else:
        print('Activa usar_bordes y ejecuta de nuevo para ver estos mapas.')
with comparar_view:
    print('Original')
    display(original)
    print('Niveles detectados por', prediccion['model'])
    display(prediccion['image'])
vistas = widgets.Tab(children=[original_view, niveles_view, bordes_view, comparar_view])
for i, titulo in enumerate(('Original', 'Niveles', 'Bordes', 'Comparar')):
    vistas.set_title(i, titulo)
vistas.selected_index = 1
display(vistas)
ruta_resultado = Path('/content') / f"resultado_{prediccion['model']}.jpg"
prediccion['image'].save(ruta_resultado, quality=92)
''')
    md('''## Descargar el resultado
''')
    code('''files.download(str(ruta_resultado))
''')
    for cell in cells:
        cell['source'] = [line.replace('Walmart_Lite_Automatico_20261015.zip', package)
                          .replace("value='YOLO26-1'", f"value='{default_model}'")
                          .replace('YOLO11-1 y YOLO26-1', 'V1 y V2 base' if default_model.startswith('V2-') else 'YOLO11-1 y YOLO26-1') for line in cell['source']]
    return {'nbformat': 4, 'nbformat_minor': 5, 'metadata': {'colab': {'name': 'Probar_en_Colab.ipynb'},
            'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
            'language_info': {'name': 'python'}}, 'cells': cells}


def build(output, profile='v1'):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        if not (SOURCE / name).is_file():
            raise ValueError(f'Falta {name}')
    uv_source = json.loads((SOURCE / 'herramientas/fuente_uv.json').read_text(encoding='utf-8'))
    for entry in uv_source['files']:
        if hashlib.sha256((SOURCE / entry['file']).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('La herramienta uv no coincide con su fuente verificada.')
    models = []
    weights = {}
    for model_id, run in (V2_RUNS if profile == 'v2' else RUNS).items():
        source = ROOT / 'Experimentos' / run / 'entrenamiento/weights/best.pt'
        body = source.read_bytes()
        metadata = json.loads((ROOT / 'Experimentos' / run / 'manifest.json').read_text(encoding='utf-8-sig'))
        models.append({'id': model_id, 'name': model_id, 'file': f'modelos/{model_id}.pt',
                       'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body), 'source_run': run,
                       'classes': metadata['clases'], 'guide': 'v2 base' if model_id.startswith('V2-') else 'v1.3'})
        weights[f'modelos/{model_id}.pt'] = body
    manifest = {'schema_version': 4, 'product': 'Walmart Visión', 'date': '2026-10-20',
                'guide': 'per_model', 'default_model': 'V2-YOLO26' if profile == 'v2' else 'YOLO26-1', 'ultralytics': '8.4.174',
                'windows_setup': 'private_python_3.12_automatic',
                'task': 'segment', 'purpose': 'inference_only', 'models': models,
                'features': ['yolo', 'paulo_mascara_v2_color_textura'],
                'edge_sources': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in EDGE_FILES.items()}}
    nb = json.dumps(notebook(output.name, manifest['default_model']), ensure_ascii=False, indent=2) + '\n'
    verify_name = 'VERIFICACION_VISION.md'
    verify = (SOURCE / verify_name).read_text(encoding='utf-8') if (SOURCE / verify_name).exists() else 'Verificación de esta entrega pendiente.\n'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in FILES:
            body = (SOURCE / name).read_bytes()
            if name.endswith('.cmd'):
                body = body.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            archive.writestr('Walmart_Vision/' + name, body)
        for name, body in weights.items():
            archive.writestr('Walmart_Vision/' + name, body)
        for name, path in EDGE_FILES.items():
            archive.writestr('Walmart_Vision/' + name, path.read_bytes())
        archive.writestr('Walmart_Vision/modelos.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        archive.writestr('Walmart_Vision/Probar_en_Colab.ipynb', nb)
        archive.writestr('Walmart_Vision/VERIFICACION.md', verify)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('El ZIP no pasó la comprobación de integridad.')
        for entry in models:
            if hashlib.sha256(archive.read('Walmart_Vision/' + entry['file'])).hexdigest() != entry['sha256']:
                raise ValueError('Los pesos del ZIP difieren del original.')
    output.with_suffix('.sha256').write_text(hashlib.sha256(output.read_bytes()).hexdigest() + '  ' + output.name + '\n', encoding='utf-8')
    output.with_name('Probar_en_Colab.ipynb').write_text(nb, encoding='utf-8', newline='\n')
    return {'zip': str(output), 'bytes': output.stat().st_size, 'models': [m['id'] for m in models]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--perfil', choices=('v1', 'v2'), default='v2')
    parser.add_argument('--output')
    args = parser.parse_args()
    output = args.output or str(ROOT / 'Entregables' / ('Walmart_Vision_20261020.zip' if args.perfil == 'v2' else 'Walmart_Vision_V1_20261020.zip'))
    print(json.dumps(build(output, args.perfil), ensure_ascii=False))
