"""Exportación, entrenamiento y comparación del primer piloto de módulos.

Ejecutar con .venv-modelo/Scripts/python.exe. No modifica CVAT.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

# Aunque conserva el nombre del primer piloto, este archivo también entrena
# niveles y estados. El panel llama a prepare(), train() y evaluate(), en ese orden.
# YOLO/Ultralytics implementa la red y el ajuste de pesos; aquí configuramos
# los datos, los parámetros y los archivos que conserva cada ensayo.
ROOT = Path(__file__).resolve().parents[2]
# Ruta histórica por defecto. El panel la reemplaza por la del ensayo nuevo.
RUN = ROOT / 'Experimentos/piloto_01_vicente_20261002'
# Configuración y recursos gráficos locales para Windows y Docker.
os.environ.setdefault('YOLO_CONFIG_DIR', str(ROOT / '.config-modelo'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.config-modelo/matplotlib'))
sys.stdout.reconfigure(encoding='utf-8')


def save_json(path, value):
    # Conserva registros legibles de datos, entorno, métricas y predicciones.
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def prepare():
    # Flujo actual del panel: preparar la versión de datos seleccionada.
    # La exportación contiene imágenes, etiquetas y data.yaml con las clases
    # y las rutas de entrenamiento/validación; puede reutilizarse entre ensayos.
    if (RUN / 'version_datos.json').exists():
        from datos_modelos import prepare_version
        prepare_version(RUN, RUN, SEED)
        return
    # Flujo histórico del primer piloto: exportar módulos desde un snapshot CVAT.
    # La partición fija y las comprobaciones de cinco fotos solo son de ese piloto;
    # los entrenamientos actuales de niveles usan la rama anterior.
    from shapely.geometry import Polygon
    from shapely.validation import explain_validity
    from PIL import Image
    snap = json.loads((RUN / 'snapshot_cvat.json').read_text(encoding='utf-8'))
    labels = {v['id']: v for v in snap['labels']}
    inventory = {v['imagen_id']: v for v in csv.DictReader(
        (ROOT / 'Datos/Registros/inventario.csv').open(encoding='utf-8-sig', newline=''))}
    reserve = json.loads((ROOT / 'Datos/Registros/reserva_evaluacion.json').read_text(encoding='utf-8-sig'))
    manifest, issues, fatal, seen_groups = [], [], [], {'train': set(), 'val': set()}
    for i, frame in enumerate(snap['frames']):
        stem = Path(frame['name']).stem
        inv = inventory[stem]
        # La reserva final permanece fuera del desarrollo. El hash comprueba
        # que la imagen coincide con el original registrado en el inventario.
        assert stem not in reserve['image_ids'] and inv['grupo_escena'] not in reserve['groups']
        split = 'val' if stem == '28' else 'train'
        seen_groups[split].add(inv['grupo_escena'])
        source = ROOT / 'Datos' / inv['archivo']
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert digest == inv['sha256'], f'Hash distinto: {source.name}'
        with Image.open(source) as im:
            assert im.size == (frame['width'], frame['height'])
        rows, module_count, level_count, keys = [], 0, 0, set()
        for shape in snap['annotations']['shapes']:
            if shape['frame'] != i:
                continue
            label = labels[shape['label_id']]
            spec = {a['id']: a['name'] for a in label['attributes']}
            attrs = {spec[a['spec_id']]: a['value'] for a in shape['attributes']}
            points = list(zip(shape['points'][::2], shape['points'][1::2]))
            poly = Polygon(points)
            # Comprueba la geometría y registra contornos inválidos para su revisión.
            valid = shape['type'] == 'polygon' and len(points) >= 3 and poly.is_valid and poly.area > 1
            # CVAT puede guardar el borde como 3000.0000000000005.
            in_bounds = all(-1e-6 <= x <= frame['width']+1e-6 and -1e-6 <= y <= frame['height']+1e-6 for x, y in points)
            if not valid or not in_bounds:
                item = {'foto': frame['name'], 'shape_id': shape['id'], 'label': label['name'], 'problema': explain_validity(poly) if not valid else 'Puntos fuera del encuadre'}
                issues.append(item)
                if label['name'] == 'Modulo':
                    fatal.append(item)
            if not attrs.get('modulo_id'):
                issues.append({'foto': frame['name'], 'shape_id': shape['id'], 'problema': 'modulo_id vacío', 'label': label['name']})
            if label['name'] == 'Nivel':
                # En este flujo histórico los niveles se revisan, pero no se
                # exportan como ejemplos: la única clase entrenada es Modulo.
                level_count += 1
                key = (attrs.get('modulo_id'), attrs.get('nivel_id'))
                if key in keys:
                    issues.append({'foto': frame['name'], 'shape_id': shape['id'], 'problema': 'Identificador modulo/nivel repetido', 'identificador': key})
                keys.add(key)
                if attrs.get('integridad') == 'pendiente' or attrs.get('limite_superior') == 'pendiente':
                    issues.append({'foto': frame['name'], 'shape_id': shape['id'], 'problema': 'Atributos pendientes', 'atributos': attrs})
                if attrs.get('limite_superior') == 'abierto' and not attrs.get('observacion'):
                    issues.append({'foto': frame['name'], 'shape_id': shape['id'], 'problema': 'Superior abierto sin observación sobre contorno provisional'})
                continue
            if attrs.get('integridad') not in ('completo', 'parcial'):
                fatal.append({'foto': frame['name'], 'shape_id': shape['id'], 'problema': 'Modulo pendiente'})
            module_count += 1
            # Formato YOLO de segmentación: clase seguida de los vértices x,y
            # normalizados entre 0 y 1 respecto del ancho y alto de la imagen.
            rows.append('0 ' + ' '.join(f'{v:.8f}' for x, y in points for v in (min(1.0,max(0.0,x/frame['width'])), min(1.0,max(0.0,y/frame['height'])))))
        for sub in ('images', 'labels'):
            (RUN / 'dataset_modulos' / sub / split).mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, RUN / 'dataset_modulos/images' / split / source.name)
        (RUN / 'dataset_modulos/labels' / split / f'{stem}.txt').write_text('\n'.join(rows) + '\n', encoding='utf-8')
        manifest.append({'imagen': source.name, 'grupo_escena': inv['grupo_escena'], 'sha256': digest, 'split': split, 'modulos': module_count, 'niveles_solo_revision': level_count})
    # Una misma escena no debe aparecer en ambos grupos: podría inflar la evaluación.
    assert seen_groups['train'].isdisjoint(seen_groups['val'])
    assert len(manifest) == 5 and len(seen_groups['train']) == 4 and len(seen_groups['val']) == 1
    save_json(RUN / 'manifest.json', {'snapshot': 'snapshot_cvat.json', 'clases': ['Modulo'], 'imagenes': manifest, 'reserva_utilizada': False, 'semilla': SEED, 'nota': 'Validación de desarrollo de una escena; no test final. Los niveles no participan en este entrenamiento.'})
    save_json(RUN / 'revision_etiquetas.json', issues)
    if fatal:
        raise ValueError(f'Módulos no válidos: {fatal}')
    dataset = RUN / 'dataset_modulos'
    (dataset / 'data.yaml').write_text(f'path: {dataset.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n  0: Modulo\n', encoding='utf-8')
    print(json.dumps({'exportadas': manifest, 'advertencias': len(issues)}, ensure_ascii=False))


# Semilla por defecto para controlar las decisiones aleatorias del ensayo.
SEED = 42


def font_path():
    # Fuente usada por las gráficas y las imágenes de comparación.
    candidates = [os.environ.get('MODEL_FONT'), 'C:/Windows/Fonts/arial.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise ValueError('Falta una fuente TrueType. Configura MODEL_FONT.')


def compute_device():
    import torch
    # Usa la primera GPU NVIDIA disponible mediante CUDA; si no, usa CPU.
    return 0 if torch.cuda.is_available() else 'cpu'


def dataset_directory():
    # Resuelve la exportación del ensayo, incluida la compartida por versión.
    from conjuntos import dataset_directory as resolve_dataset
    return resolve_dataset(ROOT, RUN)


def train(epochs, checkpoint=None, imgsz=640, batch=2, lr=0.001, seed=42, progress=None):
    # epochs: máximo de recorridos del conjunto de entrenamiento.
    # checkpoint: pesos iniciales, generales o best.pt de un ensayo anterior.
    # imgsz: tamaño objetivo de entrada; batch: imágenes por lote.
    # lr: tasa inicial de aprendizaje; seed: semilla; progress: callback del panel.
    # Cada entrenamiento requiere otra carpeta para conservar los resultados previos.
    assert not (RUN / 'entrenamiento').exists(), 'Conservar la ejecución anterior; usar otra carpeta RUN.'
    config_dir = ROOT / '.config-modelo'
    config_dir.mkdir(exist_ok=True)
    shutil.copy2(font_path(), config_dir / 'Arial.ttf')
    import torch
    import ultralytics
    from ultralytics import YOLO, settings
    # Desactiva sincronización e integraciones externas de seguimiento.
    settings.update({'sync': False, 'tensorboard': False, 'wandb': False, 'mlflow': False, 'comet': False})
    device = compute_device()
    # Guarda versiones y hardware para poder interpretar o reproducir el ensayo.
    save_json(RUN / 'entorno.json', {'python': sys.version, 'torch': torch.__version__, 'ultralytics': ultralytics.__version__, 'cuda_runtime': torch.version.cuda,
                                   'gpu': torch.cuda.get_device_name(0) if device == 0 else None,
                                   'capability': torch.cuda.get_device_capability(0) if device == 0 else None,
                                   'device': device})
    # Carga los pesos seleccionados; sin checkpoint usa YOLO11 nano de segmentación.
    # Partir de pesos generales es transferencia de aprendizaje; partir de los
    # propios permite ajuste fino. Esta llamada no reanuda un trabajo interrumpido.
    model = YOLO(str(checkpoint or ROOT / 'Modelos/preentrenados/yolo11n-seg.pt'))
    criterion = json.loads((RUN / 'manifest.json').read_text(encoding='utf-8')).get('criterion') or {}
    v2 = criterion.get('version') == 'disponibilidad_visual_nivel_v2_reponer'
    if progress:
        # Informa al panel del inicio de cada época y de su final, incluida validación.
        model.add_callback('on_train_epoch_start', lambda trainer: progress(
            'training', current_epoch=trainer.epoch + 1))
        model.add_callback('on_fit_epoch_end', lambda trainer: progress(
            'training', completed_epochs=trainer.epoch + 1))
    # Ultralytics predice, calcula el error frente a las etiquetas y ajusta los
    # pesos por lotes. La validación permite seleccionar los mejores pesos.
    model.train(
        data=str(dataset_directory() / 'data.yaml'),  # Rutas y clases del dataset.
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=0,             # Carga datos en el proceso principal.
        device=device,
        seed=seed,
        deterministic=True,    # Solicita operaciones deterministas donde sea posible.
        optimizer='AdamW',      # Algoritmo que actualiza los pesos a partir del error.
        lr0=lr,                # Tasa de aprendizaje inicial.
        patience=20,           # Para tras 20 épocas sin mejorar la puntuación de validación.
        amp=False,             # Desactiva el entrenamiento con precisión mixta.
        overlap_mask=False,    # Mantiene separadas las máscaras de las instancias.
        mask_ratio=2,          # Reduce las máscaras objetivo por un factor de 2.

        # Data augmentation durante el entrenamiento: transforma imágenes y sus
        # etiquetas geométricas juntas. No añade archivos al dataset original.
        # Estas variaciones se suman a las fotos sintéticas ya incluidas en los datos.
        mosaic=0.0,            # Sin combinar varias imágenes en un mosaico.
        mixup=0.0,             # Sin mezclar imágenes por transparencia.
        copy_paste=0.0,        # Sin copiar instancias entre imágenes.
        degrees=0.0 if v2 else 3.0,    # v2 conserva completo el ancho del nivel.
        translate=0.0 if v2 else 0.05,
        scale=0.0 if v2 else 0.15,
        shear=0.0,             # Sin cizallamiento (inclinación de los ejes).
        perspective=0.0,       # Sin distorsión adicional de perspectiva.
        fliplr=0.0,            # Probabilidad cero de volteo horizontal.
        flipud=0.0,            # Probabilidad cero de volteo vertical.
        hsv_h=0.01,            # Variación del tono en el espacio de color HSV.
        hsv_s=0.2,             # Variación de saturación.
        hsv_v=0.2,             # Variación de brillo.

        # Resultados en RUN/entrenamiento: pesos best.pt y last.pt, métricas,
        # configuración y gráficas. best.pt conserva la mejor puntuación de
        # validación (fitness) según el criterio de selección de Ultralytics.
        cache=False,           # Sin caché adicional de imágenes del dataset.
        plots=True,
        project=str(RUN),
        name='entrenamiento',
        exist_ok=False,
    )


def evaluate(progress=None):
    # Evalúa los mejores pesos con el grupo de validación, sin ajustar sus pesos.
    # Esta evaluación de desarrollo no sustituye la reserva de prueba final.
    assert not (RUN / 'validacion').exists(), 'Conservar la validación anterior; usar otra carpeta RUN.'
    import numpy as np
    from ultralytics import YOLO
    run = RUN / 'entrenamiento'
    model = YOLO(str(run / 'weights/best.pt'))
    config = json.loads((RUN / 'config_interfaz.json').read_text(encoding='utf-8')) if (RUN / 'config_interfaz.json').exists() else {}
    metrics = model.val(data=str(dataset_directory() / 'data.yaml'), device=compute_device(), imgsz=config.get('imgsz', 640),
                        batch=1, workers=0, overlap_mask=False, mask_ratio=2,
                        plots=True, project=str(RUN), name='validacion', exist_ok=False)
    save_json(RUN / 'metricas_validacion.json', {k: float(v) for k, v in metrics.results_dict.items()})
    if progress:
        progress('comparing')
    # Añade diagnóstico por imagen para revisar omisiones y falsas detecciones.
    compare()


def compare():
    # Los ensayos actuales de niveles usan el comparador específico de estados.
    if json.loads((RUN / 'manifest.json').read_text(encoding='utf-8')).get('scope') == 'Nivel_estados':
        from comparar_niveles import compare_levels
        compare_levels(RUN, compute_device(), font_path())
        return
    # Comparación histórica de módulos: dibuja referencias y predicciones,
    # exporta máscaras y cuenta aciertos, omisiones y falsos positivos.
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from shapely.geometry import Polygon
    from ultralytics import YOLO
    model = YOLO(str(RUN / 'entrenamiento/weights/best.pt'))
    manifest = json.loads((RUN / 'manifest.json').read_text(encoding='utf-8'))
    out = RUN / 'comparaciones'; out.mkdir(exist_ok=True)
    mask_out = RUN / 'mascaras'; mask_out.mkdir(exist_ok=True)
    font = ImageFont.truetype(str(font_path()), 22)
    summaries = []
    config = json.loads((RUN / 'config_interfaz.json').read_text(encoding='utf-8')) if (RUN / 'config_interfaz.json').exists() else {}
    for item in manifest['imagenes']:
        split, name = item['split'], item['imagen']
        source = RUN / 'dataset_modulos/images' / split / name
        result = model.predict(str(source), device=compute_device(), imgsz=config.get('imgsz', 640), conf=0.25, iou=0.7,
                               retina_masks=True, verbose=False)[0]
        im = Image.open(source).convert('RGB'); w, h = im.size
        truth = []
        for row in (RUN / 'dataset_modulos/labels' / split / f'{Path(name).stem}.txt').read_text().splitlines():
            vals = list(map(float, row.split()[1:])); truth.append(Polygon([(x*w,y*h) for x,y in zip(vals[::2], vals[1::2])]))
        predictions = []
        if result.masks is not None:
            for mask_index, (pts, confidence) in enumerate(zip(result.masks.xy, result.boxes.conf.cpu().tolist())):
                if len(pts) >= 3:
                    poly = Polygon(pts)
                    if not poly.is_valid: poly = poly.buffer(0)
                    if not poly.is_empty:
                        mask = result.masks.data[mask_index].cpu().numpy().astype(bool)
                        assert mask.shape == (h, w)
                        predictions.append((poly, confidence, pts, mask))
        # Numeración para la comparación visual de izquierda a derecha.
        # No constituye una predicción de modulo_id ni modifica los IDs en CVAT.
        truth.sort(key=lambda p: p.centroid.x)
        predictions.sort(key=lambda v: v[0].centroid.x)
        truth_masks = []
        for poly in truth:
            raster = Image.new('1', (w,h))
            ImageDraw.Draw(raster).polygon(list(poly.exterior.coords), fill=1)
            truth_masks.append(np.asarray(raster, dtype=bool))
        # IoU = área de intersección / área de unión de dos máscaras.
        # Empareja primero las mayores coincidencias, sin reutilizar instancias.
        pairs = sorted([(float(np.logical_and(t,m).sum()/np.logical_or(t,m).sum()), ti, pi)
                        for ti,t in enumerate(truth_masks) for pi,(_,_,_,m) in enumerate(predictions)], reverse=True)
        used_t, used_p, matches = set(), set(), []
        for iou, ti, pi in pairs:
            if iou >= 0.5 and ti not in used_t and pi not in used_p:
                used_t.add(ti); used_p.add(pi); matches.append({'anotacion': ti+1, 'prediccion': pi+1, 'iou_mascara': iou})
        invalid_count = sum(not Polygon(v[2]).is_valid for v in predictions)
        tp=len(matches); summary={'imagen': name, 'split': split, 'conf':0.25, 'iou_minimo':0.5, 'anotados':len(truth), 'predichos':len(predictions), 'aciertos':tp, 'omitidos':len(truth)-tp, 'falsos_positivos':len(predictions)-tp, 'contornos_xy_invalidos':invalid_count, 'parejas':matches}
        summaries.append(summary)
        panels=[]
        for title, polygons, color in [('Anotaciones de referencia', [np.array(p.exterior.coords) for p in truth], '#16a34a'),('Predicciones conf >= 0.25', [v[2] for v in predictions], '#2563eb')]:
            panel=im.copy(); panel.thumbnail((1000,750)); scale=panel.width/w; draw=ImageDraw.Draw(panel)
            for idx,pts in enumerate(polygons):
                scaled=[(float(x)*scale,float(y)*scale) for x,y in pts]
                draw.line(scaled+[scaled[0]],fill=color,width=4)
                draw.text(scaled[0],str(idx+1),font=font,fill='white',stroke_width=2,stroke_fill='black')
            bordered=Image.new('RGB',(1000,800),'#111827'); bordered.paste(panel,(0,50)); ImageDraw.Draw(bordered).text((18,12),f'{name} | {split} | {title}',font=font,fill='white'); panels.append(bordered)
        canvas=Image.new('RGB',(2000,800)); canvas.paste(panels[0],(0,0)); canvas.paste(panels[1],(1000,0)); canvas.save(out/f'{Path(name).stem}_{split}.jpg',quality=92)
        save_json(out/f'{Path(name).stem}_predicciones.json', [{'confianza':confidence,'puntos':pts.tolist(),'poligono_xy_valido':Polygon(pts).is_valid} for _,confidence,pts,_ in predictions])
        for idx,(_,_,_,mask) in enumerate(predictions):
            Image.fromarray(mask.astype(np.uint8)*255).save(mask_out/f'{Path(name).stem}_{idx+1:02d}.png')
    save_json(RUN / 'evaluacion_por_imagen.json', summaries)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    # Entrada histórica por consola: ejecuta una acción sobre RUN por defecto.
    # El panel configura RUN y llama a las funciones directamente; no pasa por aquí.
    parser=argparse.ArgumentParser()
    parser.add_argument('accion', choices=['preparar','entrenar','evaluar','comparar'])
    parser.add_argument('--epochs',type=int,default=100)
    args=parser.parse_args()
    if args.accion=='preparar': prepare()
    elif args.accion=='entrenar': train(args.epochs)
    elif args.accion=='evaluar': evaluate()
    else: compare()
