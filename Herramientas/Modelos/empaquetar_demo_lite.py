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
         'herramientas/licencias/LICENSE-APACHE', 'herramientas/licencias/LICENSE-MIT',
         'Dockerfile', '.dockerignore', 'compose.yaml', 'requirements-docker.txt', 'DOCKER.md',
         'VERIFICACION_DOCKER.md', 'VERIFICACION_OCUPACION.md')
EDGE_FILES = {'ocupacion_paulo.py': ROOT / 'Herramientas/Modelos/ocupacion_paulo.py',
              'gondola_bordes.py': ROOT / 'Experimentos/Bordes/gondola_bordes.py',
              'gondola_combinacion_ponderada.py': ROOT / 'Experimentos/Bordes/gondola_combinacion_ponderada.py'}
SUPPORT_FILES = {'geometria_niveles.py': ROOT / 'Herramientas/Modelos/geometria_niveles.py'}
RUNS = {'V2-YOLO11': 'v2_base_yolo11n_01_20261020_002800_ec8d',
        'V2-YOLO26': 'v2_base_yolo26n_01_20261020_004933_b105'}


def notebook(package='Walmart_Vision_Actual_20261023.zip'):
    cells = []

    def md(text):
        cells.append({'cell_type': 'markdown', 'id': f'markdown-{len(cells)}', 'metadata': {}, 'source': text.splitlines(keepends=True)})

    def code(text):
        cells.append({'cell_type': 'code', 'id': f'code-{len(cells)}', 'metadata': {}, 'source': text.splitlines(keepends=True), 'outputs': [], 'execution_count': None})

    md('''# Probar Walmart Visión en Google Colab

Usa los modelos entrenados V2-YOLO11 y V2-YOLO26 para analizar una foto, sin volver a entrenar. Ejecuta las celdas en orden.

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
    md('''## Seleccionar modelo

Selecciona el modelo antes de subir la foto. Para comparar, puedes repetir el análisis con el otro modelo sobre la misma imagen.
''')
    code('''import ipywidgets as widgets
from IPython.display import display
modelos = visor.available()
selector = widgets.Dropdown(options=[m['id'] for m in modelos],
                            value=visor.manifest['default_model'], description='Modelo:')
display(selector)
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

La confianza mínima predeterminada es 0,25. Puedes cambiarla en la siguiente celda; no representa el porcentaje de producto del nivel. El modelo distingue reponer y suficiente; no reconoce no evaluable.

Para probar el otro modelo, cambia el selector y vuelve a ejecutar esta celda. Para usar otra foto, repite la celda de carga y luego esta.
''')
    code('''confianza = 0.25
usar_bordes = True  # False para ejecutar solo YOLO.
prediccion = visor.analyze(contenido_foto, selector.value, confianza,
                          method='yolo_paulo_v2' if usar_bordes else 'yolo')
print(f"{prediccion['model']} · {prediccion['device']} · {prediccion['seconds']} s")
print('Niveles detectados:', len(prediccion['detections']))
print('Estados YOLO:', prediccion['counts'])
if usar_bordes:
    print('Ocupación estimada: rojo bajo el 30 %; verde desde el 30 %. Estimación experimental.')
    for nivel in prediccion['detections']:
        lectura = nivel['occupancy_estimate']
        porcentaje = str(lectura['pct']) + ' %' if lectura['pct'] is not None else 'Sin medición'
        print('Nivel', nivel['id'], porcentaje, lectura['label'])
from inferencia import read_photo
original = read_photo(contenido_foto)
original_view, niveles_view, bordes_view, comparar_view = [widgets.Output() for _ in range(4)]
with original_view:
    display(original)
with niveles_view:
    display(prediccion['image'])
with bordes_view:
    if usar_bordes:
        print('Amarillo: señal experimental. Los colores de Niveles usan la ocupación estimada y el umbral del 30 %.')
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
        cell['source'] = [line.replace('Walmart_Lite_Automatico_20261015.zip', package) for line in cell['source']]
    return {'nbformat': 4, 'nbformat_minor': 5, 'metadata': {'colab': {'name': 'Probar_en_Colab.ipynb'},
            'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
            'language_info': {'name': 'python'}}, 'cells': cells}


def build(output):
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
    for model_id, run in RUNS.items():
        source = ROOT / 'Experimentos' / run / 'entrenamiento/weights/best.pt'
        body = source.read_bytes()
        metadata = json.loads((ROOT / 'Experimentos' / run / 'manifest.json').read_text(encoding='utf-8-sig'))
        models.append({'id': model_id, 'name': model_id, 'file': f'modelos/{model_id}.pt',
                       'sha256': hashlib.sha256(body).hexdigest(), 'bytes': len(body), 'source_run': run,
                       'classes': metadata['clases'], 'guide': 'v2 base'})
        weights[f'modelos/{model_id}.pt'] = body
    manifest = {'schema_version': 5, 'product': 'Walmart Visión', 'date': '2026-10-23',
                'guide': 'v2 base', 'default_model': 'V2-YOLO26', 'ultralytics': '8.4.174',
                'windows_setup': 'private_python_3.12_automatic',
                'task': 'segment', 'purpose': 'inference_only', 'models': models,
                'features': ['yolo', 'paulo_mascara_v2_combinacion_ponderada'],
                'edge_sources': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in EDGE_FILES.items()}}
    nb = json.dumps(notebook(output.name), ensure_ascii=False, indent=2) + '\n'
    verify_name = 'VERIFICACION_ACTUAL.md'
    verify = (SOURCE / verify_name).read_text(encoding='utf-8') if (SOURCE / verify_name).exists() else 'Verificación de esta entrega pendiente.\n'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in FILES:
            body = (SOURCE / name).read_bytes()
            if name.endswith('.cmd'):
                body = body.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            elif name in ('Dockerfile', '.dockerignore', 'compose.yaml', 'requirements-docker.txt',
                          'DOCKER.md', 'VERIFICACION_DOCKER.md'):
                body = body.replace(b'\r\n', b'\n')
            archive.writestr('Walmart_Vision/' + name, body)
        for name, body in weights.items():
            archive.writestr('Walmart_Vision/' + name, body)
        for name, path in (EDGE_FILES | SUPPORT_FILES).items():
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
    parser.add_argument('--output')
    args = parser.parse_args()
    output = args.output or str(ROOT / 'Entregables/Walmart_Vision_Actual_20261023.zip')
    print(json.dumps(build(output), ensure_ascii=False))
