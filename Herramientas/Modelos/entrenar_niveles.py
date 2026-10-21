"""Entrenar segmentación de niveles con el criterio v2 de tres estados.

Requiere un dataset YOLO de segmentación ya anotado, revisado y separado
en entrenamiento/validación. Ver Documentacion/Desarrollo/Entrenamiento_niveles_v2.md.
No importa CVAT ni convierte automáticamente las etiquetas del criterio v1.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys

import numpy as np
import yaml
from PIL import Image
from shapely.geometry import Polygon


ROOT = Path(__file__).resolve().parents[2]
CRITERION = 'disponibilidad_visual_nivel_v2_reponer'
# El orden importa: el primer número de cada etiqueta YOLO es el ID de clase.
# Reponer agrupa niveles vacíos y con producto en menos del 30% del ancho.
# Ese criterio se aplica al anotar: la red aprende las clases, no mide ese ancho.
CLASSES = ('Nivel_reponer', 'Nivel_suficiente', 'Nivel_no_evaluable')
ULTRALYTICS_VERSION = '8.4.174'
# Se conserva el lector de Pillow antes del monkey-patch opcional de Ultralytics;
# una imagen corrupta debe fallar, sin intentar instalar plugins automáticamente.
PIL_OPEN = Image.open


def check_compatibility():
    try:
        installed = version('ultralytics')
    except PackageNotFoundError:
        installed = 'no instalado'
    if installed != ULTRALYTICS_VERSION:
        raise ValueError(f'Ultralytics incompatible: {installed}; se requiere {ULTRALYTICS_VERSION}, '
                         f'igual que Docker. Instala con "{sys.executable}" -m pip install '
                         f'-r "{ROOT / "Herramientas/Modelos/requirements.txt"}".')
    return installed


def load_runtime():
    check_compatibility()
    # Carpeta exclusiva del script: importar YOLO no restablece los ajustes del panel
    # ni los ajustes generales del usuario. Debe existir antes de importar la librería.
    config = ROOT / '.config-modelo' / 'niveles_v2'
    (config / 'Ultralytics').mkdir(parents=True, exist_ok=True)
    os.environ['YOLO_CONFIG_DIR'] = str(config)
    os.environ['MPLCONFIGDIR'] = str(config / 'matplotlib')
    os.environ['YOLO_AUTOINSTALL'] = 'false'
    os.environ['YOLO_OFFLINE'] = 'true'
    try:
        import torch
        import ultralytics
    except ImportError as error:
        raise ValueError(f'Faltan dependencias del entorno: {error}. Ejecuta pip check e instala '
                         'Herramientas/Modelos/requirements.txt.') from error
    # Ultralytics parchea Image.open para intentar cargar plugins HEIF ante
    # cualquier error. Conservamos Pillow: un PNG corrupto debe seguir generando
    # su error de imagen, también si el panel se usa en este mismo proceso.
    Image.open = PIL_OPEN
    from ultralytics import settings
    settings.update({'sync': False, 'tensorboard': False, 'wandb': False, 'mlflow': False, 'comet': False})
    # Una fuente local evita que YOLO intente descargar Arial al dibujar métricas.
    fonts = [os.environ.get('MODEL_FONT'), 'C:/Windows/Fonts/arial.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    font = next((Path(path) for path in fonts if path and Path(path).is_file()), None)
    if font is None:
        raise ValueError('Falta una fuente TrueType local. Configura MODEL_FONT.')
    target = config / 'Ultralytics' / 'Arial.ttf'
    if font.resolve() != target.resolve():
        shutil.copy2(font, target)
    return torch, ultralytics


def load_model(checkpoint, runtime):
    checkpoint = Path(checkpoint).resolve(strict=True)
    if checkpoint.suffix.lower() != '.pt':
        raise ValueError('--modelo debe ser un archivo local .pt de segmentación.')
    try:
        model = runtime.YOLO(str(checkpoint))
    except Exception as error:
        raise ValueError(f'No se pudo cargar {checkpoint.name} con Ultralytics {runtime.__version__}: '
                         f'{type(error).__name__}: {error}. Comprueba el entorno y los pesos.') from error
    if model.task != 'segment':
        raise ValueError('El modelo de partida debe ser de segmentación (por ejemplo yolo26n-seg.pt).')
    return model


def verify_image(path, formats, imread):
    """Verifica integridad con Pillow y decodificación con el cargador real de YOLO."""
    try:
        with PIL_OPEN(path) as source:
            source.verify()
        with PIL_OPEN(path) as source:
            if source.format.lower() not in formats | {'jpeg2000'}:
                raise ValueError(f'Formato interno no admitido: {source.format}.')
            if source.getexif().get(274, 1) != 1:
                raise ValueError('Aplica la orientación EXIF a imagen y etiquetas antes de entrenar.')
            source.load()
            width, height = source.size
            if min(width, height) < 10:
                raise ValueError('YOLO exige imágenes de al menos 10 x 10 píxeles.')
            if source.format == 'JPEG' and not path.read_bytes().endswith(b'\xff\xd9'):
                raise ValueError('JPEG incompleto: falta su marcador final.')
        decoded = imread(str(path))
        if decoded is None or decoded.shape != (height, width, 3) or str(decoded.dtype) != 'uint8':
            raise ValueError('El cargador de YOLO no devuelve una imagen RGB/BGR uint8 del mismo tamaño.')
    except Exception as error:
        raise ValueError(f'Imagen inválida {path}: {error}') from error
    return width, height


def file_hash(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def save_json(path, value):
    def numeric(item):
        if isinstance(item, np.generic):
            return item.item()
        raise TypeError(f'No se puede serializar {type(item).__name__}.')
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=numeric, allow_nan=False) + '\n', encoding='utf-8')


def validate_dataset(data_file, allow_incomplete=False):
    """Comprueba imágenes, polígonos y partición sin cargar pesos ni entrenar."""
    load_runtime()
    from ultralytics.data.utils import IMG_FORMATS
    from ultralytics.utils.patches import imread
    data_file = Path(data_file).resolve(strict=True)
    data = yaml.safe_load(data_file.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('data.yaml debe contener un mapa de rutas y clases.')
    names = data.get('names')
    if isinstance(names, dict) and set(names) == {0, 1, 2}:
        names = [names[i] for i in range(3)]
    # Acepta los nombres simples de CVAT o los nombres Nivel_* del laboratorio,
    # conservando siempre el orden 0=reponer, 1=suficiente, 2=no_evaluable.
    if names not in (list(CLASSES), ['reponer', 'suficiente', 'no_evaluable']):
        raise ValueError('Clases incompatibles: usa 0=Nivel_reponer, '
                         '1=Nivel_suficiente, 2=Nivel_no_evaluable. '
                         'El dataset anterior de cuatro clases no sirve directamente.')
    if 'nc' in data and data['nc'] != 3:
        raise ValueError('nc debe ser 3 para el criterio nuevo.')

    # Las rutas relativas se resuelven respecto de data.yaml, nunca del cwd.
    if data.get('path') is not None and not isinstance(data['path'], str):
        raise ValueError('path debe ser una ruta de texto en data.yaml.')
    base = Path(data.get('path') or '.')
    base = (data_file.parent / base).resolve()
    report = {'criterio': CRITERION, 'data_original': str(data_file),
              'data_sha256': file_hash(data_file), 'clases': list(CLASSES),
              'splits': {}, 'advertencias': []}
    normalized = {'path': str(base), 'names': list(CLASSES)}
    hashes, families = {}, {}
    # Si hay test, se verifica su separación, pero no se usa para ajustar ni elegir pesos.
    for split in ('train', 'val', *(['test'] if 'test' in data else [])):
        # Este script usa el layout images/train, images/val y labels equivalente.
        # No selecciona fotos al azar: la partición debe estar decidida por escenas.
        value = data.get(split)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'Falta la carpeta {split} en data.yaml.')
        folder = (base / value).resolve(strict=True)
        if not folder.is_dir() or folder.name != split or folder.parent.name != 'images':
            raise ValueError(f'{split} debe apuntar a una carpeta images/{split}.')
        normalized[split] = str(folder)
        labels = folder.parent.parent / 'labels' / split
        # Mismo inventario que la versión fijada de YOLO, incluidos MPO/AVIF/etc.
        images = sorted(p for p in folder.rglob('*') if p.suffix[1:].lower() in IMG_FORMATS and p.is_file())
        if not images:
            raise ValueError(f'No hay imágenes en {folder}.')
        counts, records, label_paths = Counter(), [], set()
        for image in images:
            width, height = verify_image(image, IMG_FORMATS, imread)
            label = labels / image.relative_to(folder).with_suffix('.txt')
            if label in label_paths:
                raise ValueError(f'Dos imágenes comparten la misma etiqueta: {label}.')
            label_paths.add(label)
            # Un .txt vacío es válido para una imagen sin niveles; que falte
            # el archivo puede ocultar una anotación perdida y se rechaza.
            if not label.is_file():
                raise ValueError(f'Falta la etiqueta de {image.name}: {label}.')
            image_hash = file_hash(image)
            if image_hash in hashes and hashes[image_hash] != split:
                raise ValueError(f'Imagen duplicada entre particiones: {image.name}.')
            hashes[image_hash] = split
            # Detecta familias conocidas del lote Líder Express: original y A/B/C
            # deben permanecer juntos. Otras vistas del mismo tramo requieren revisión humana.
            family = re.fullmatch(r'(lider_express_\d+)_(?:0_original|[ABC]_.+)', image.stem)
            if family:
                key = family.group(1)
                if key in families and families[key] != split:
                    raise ValueError(f'Familia repartida entre particiones: {key}.')
                families[key] = split
            for line_number, line in enumerate(label.read_text(encoding='utf-8-sig').splitlines(), 1):
                if not line.strip():
                    continue
                fields = line.split()
                location = f'{label}:{line_number}'
                # Segmentación: clase x1 y1 x2 y2 x3 y3 ... (no cajas de detección).
                if len(fields) < 7 or (len(fields) - 1) % 2 or fields[0] not in {'0', '1', '2'}:
                    raise ValueError(f'Etiqueta de segmentación inválida en {location}.')
                coords = [float(v) for v in fields[1:]]
                if any(not math.isfinite(v) or not 0 <= v <= 1 for v in coords):
                    raise ValueError(f'Coordenadas fuera de [0, 1] en {location}.')
                polygon = Polygon(zip(coords[::2], coords[1::2]))
                if not polygon.is_valid or polygon.area <= 0:
                    raise ValueError(f'Polígono inválido o sin área en {location}.')
                counts[CLASSES[int(fields[0])]] += 1
            records.append({'imagen': str(image), 'sha256': image_hash,
                            'etiqueta': str(label), 'etiqueta_sha256': file_hash(label),
                            'ancho': width, 'alto': height,
                            'relativo': image.relative_to(folder).as_posix()})
        missing = [name for name in CLASSES if not counts[name]]
        if missing and (split == 'train' or not allow_incomplete):
            hint = ('. Añade ejemplos revisados de esas clases.' if split == 'train' else
                    '. Para un ensayo exploratorio usa --permitir-validacion-incompleta.')
            raise ValueError(f'Faltan ejemplos en {split}: ' + ', '.join(missing) + hint)
        if missing:
            report['advertencias'].append(f'Sin ejemplos en {split} para: ' + ', '.join(missing))
        report['splits'][split] = {'imagenes': len(images), 'niveles_por_clase': dict(counts),
                                   'archivos': records}
    return normalized, report


def snapshot_dataset(run, dataset, report):
    """Copia solo el inventario revisado, sin cachés .cache ni .npy anteriores."""
    snapshot = run / 'dataset'
    frozen = {'path': str(snapshot), 'names': list(CLASSES)}
    frozen_report = json.loads(json.dumps(report))
    for split, info in frozen_report['splits'].items():
        frozen[split] = f'images/{split}'
        for item in info['archivos']:
            for path_key, hash_key, folder in [('imagen', 'sha256', 'images'),
                                                ('etiqueta', 'etiqueta_sha256', 'labels')]:
                source = Path(item[path_key])
                relative = Path(item['relativo'])
                target = snapshot / folder / split / (relative if folder == 'images' else relative.with_suffix('.txt'))
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                if file_hash(target) != item[hash_key]:
                    raise ValueError(f'El archivo cambió después de revisarlo: {source}. Revisa otra vez los datos.')
                item['origen_' + path_key] = str(source)
                item[path_key] = str(target)
    data_file = snapshot / 'data.yaml'
    data_file.write_text(yaml.safe_dump(frozen, allow_unicode=True, sort_keys=False), encoding='utf-8')
    # Revalidar la copia detecta también modificaciones concurrentes durante la lectura.
    _, checked = validate_dataset(data_file, allow_incomplete=bool(report['advertencias']))
    expected = [(r['sha256'], r['etiqueta_sha256']) for v in frozen_report['splits'].values() for r in v['archivos']]
    actual = [(r['sha256'], r['etiqueta_sha256']) for v in checked['splits'].values() for r in v['archivos']]
    if expected != actual:
        raise ValueError('La copia del dataset cambió durante su comprobación.')
    return frozen, frozen_report


def verify_snapshot(report):
    for info in report['splits'].values():
        for item in info['archivos']:
            if file_hash(Path(item['imagen'])) != item['sha256'] or file_hash(Path(item['etiqueta'])) != item['etiqueta_sha256']:
                raise ValueError('La copia del ensayo fue modificada; sus métricas no son reproducibles.')


def evaluate_model(model, run, data_file, report, device, args, split='val'):
    from evaluar_niveles_v2 import evaluate_split
    if [model.names[i] for i in range(3)] != list(CLASSES):
        raise ValueError('Los pesos entrenados no conservan el orden de clases esperado.')
    directory = 'validacion' if split == 'val' else 'evaluacion_final'
    metrics = model.val(data=str(data_file), split=split, device=device,
                        imgsz=args.imgsz, batch=1, workers=0, overlap_mask=False,
                        mask_ratio=2, plots=True, project=str(run), name=directory, exist_ok=False)
    save_json(run / f'metricas_{directory}.json', {
        'agregadas': {key: float(value) for key, value in metrics.results_dict.items()},
        'por_clase_yolo': metrics.summary(),
        'cobertura_completa': all(report['splits'][split]['niveles_por_clase'].get(name, 0) for name in CLASSES),
    })
    summary, per_image = evaluate_split(model, report['splits'][split]['archivos'], device,
                                       args.imgsz, args.conf, args.iou_mascara)
    save_json(run / f'alertas_{split}.json', summary)
    save_json(run / f'por_imagen_{split}.json', per_image)


def train(args, dataset, report):
    """Crea un ensayo independiente y evalúa sus mejores pesos."""
    checkpoint = Path(args.modelo).resolve(strict=True)
    if checkpoint.suffix.lower() != '.pt':
        raise ValueError('--modelo debe ser un archivo local .pt de segmentación.')
    # Los ensayos v2 se guardan en una subcarpeta propia: el panel actual sigue
    # interpretando cuatro estados y todavía no puede visualizar estos modelos.
    run = ROOT / 'Experimentos' / 'niveles_v2' / args.nombre
    if run.exists():
        raise ValueError(f'Ya existe el ensayo {run}. Usa otro --nombre.')
    torch, ultralytics = load_runtime()
    device = (0 if torch.cuda.is_available() else 'cpu') if args.device == 'auto' else args.device
    model = load_model(checkpoint, ultralytics)
    run.mkdir(parents=True, exist_ok=False)
    # Cada ensayo tiene imágenes y etiquetas propias. cache=False controla la caché
    # de imágenes; la copia nueva evita reutilizar cachés de etiquetas antiguas.
    dataset, report = snapshot_dataset(run, dataset, report)
    data_file = run / 'data.yaml'
    data_file.write_text(yaml.safe_dump(dataset, allow_unicode=True, sort_keys=False), encoding='utf-8')
    save_json(run / 'revision_datos.json', report)
    save_json(run / 'configuracion.json', {**vars(args), 'criterio': CRITERION,
              'creado_utc': datetime.now(timezone.utc).isoformat(),
              'modelo_sha256': file_hash(checkpoint), 'device_elegido': device})
    save_json(run / 'entorno.json', {'python': sys.version, 'torch': torch.__version__,
              'ultralytics': ultralytics.__version__, 'cuda_runtime': torch.version.cuda})

    # La biblioteca calcula los errores de cajas, clases y máscaras, y ajusta
    # los pesos con AdamW. Las anotaciones son la referencia de lo que debe aprender.
    model.train(
        data=str(data_file),
        epochs=args.epochs,     # Máximo de recorridos del dataset de entrenamiento.
        imgsz=args.imgsz,       # Tamaño objetivo de entrada (640 por defecto).
        batch=args.batch,       # Imágenes por lote; reducir si falta memoria GPU.
        device=device,
        workers=0,
        seed=args.seed,
        deterministic=True,
        optimizer='AdamW',
        lr0=args.lr,            # Tasa de aprendizaje inicial.
        patience=args.patience, # Épocas sin mejora antes de detenerse.
        resume=False,          # Ensayo nuevo; puede partir de pesos anteriores.
        amp=False,
        overlap_mask=False,
        mask_ratio=2,
        # Augmentation suave: transforma imagen y polígonos de forma consistente.
        # Se aplica al entrenar y no crea imágenes permanentes en el dataset.
        degrees=3.0,           # Rotación de hasta +/-3 grados.
        translate=0.05,        # Desplazamiento de hasta 5% del ancho/alto.
        scale=0.15,            # Factor de escala entre 0.85 y 1.15.
        hsv_h=0.01,            # Variación del tono.
        hsv_s=0.2,             # Variación de saturación.
        hsv_v=0.2,             # Variación de brillo.
        mosaic=0.0, mixup=0.0, copy_paste=0.0,
        shear=0.0, perspective=0.0, fliplr=0.0, flipud=0.0,
        cache=False, plots=True,
        project=str(run), name='entrenamiento', exist_ok=False,
    )
    verify_snapshot(report)
    # Evalúa best.pt; test solo se consulta si se solicitó explícitamente.
    best = run / 'entrenamiento' / 'weights' / 'best.pt'
    trained = load_model(best, ultralytics)
    evaluate_model(trained, run, data_file, report, device, args)
    if args.evaluar_test:
        evaluate_model(trained, run, data_file, report, device, args, split='test')
    verify_snapshot(report)
    print(f'Entrenamiento terminado. Mejores pesos: {best}')
    return run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', help='data.yaml del dataset YOLO de tres clases.')
    parser.add_argument('--nombre', default=datetime.now().strftime('niveles_%Y%m%d_%H%M%S'), help='Nombre nuevo del ensayo.')
    parser.add_argument('--modelo', default=str(ROOT / 'Modelos/preentrenados/yolo26n-seg.pt'), help='Pesos locales de segmentación.')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--batch', type=int, default=2)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--patience', type=int, default=20)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--device', default='auto', help='auto, cpu o índice de GPU (por ejemplo 0).')
    parser.add_argument('--solo-verificar', action='store_true', help='Revisar datos sin entrenar ni crear un ensayo.')
    parser.add_argument('--verificar-entorno', action='store_true', help='Comprobar versión y cargar el modelo real, sin entrenar.')
    parser.add_argument('--permitir-validacion-incompleta', action='store_true', help='Permite un ensayo exploratorio si faltan clases en val/test.')
    parser.add_argument('--evaluar-test', action='store_true', help='Evaluar también el grupo test independiente después de entrenar.')
    parser.add_argument('--conf', type=float, default=0.25, help='Confianza fija para medir alertas.')
    parser.add_argument('--iou-mascara', type=float, default=0.5, help='IoU mínimo para emparejar niveles por máscara.')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', args.nombre):
        parser.error('--nombre debe usar letras sin tildes, números, guiones o guiones bajos (máximo 80).')
    if min(args.epochs, args.imgsz, args.batch, args.patience) <= 0 or not math.isfinite(args.lr) or args.lr <= 0:
        parser.error('epochs, imgsz, batch, patience y lr deben ser positivos.')
    if args.seed < 0 or not re.fullmatch(r'auto|cpu|\d+', args.device):
        parser.error('Usa seed no negativa y device auto, cpu o un índice de GPU.')
    if not 0 < args.conf <= 1 or not 0 < args.iou_mascara <= 1:
        parser.error('conf e iou-mascara deben estar entre 0 (excluido) y 1.')
    if not args.data and not args.verificar_entorno:
        parser.error('Indica --data o usa --verificar-entorno.')
    try:
        if args.verificar_entorno:
            _, runtime = load_runtime()
            load_model(args.modelo, runtime)
            print(f'Entorno compatible: Ultralytics {runtime.__version__}; modelo cargado correctamente.')
            if not args.data:
                return
        dataset, report = validate_dataset(args.data, args.permitir_validacion_incompleta)
        if args.evaluar_test and 'test' not in dataset:
            raise ValueError('--evaluar-test requiere test: images/test en data.yaml.')
        for split, info in report['splits'].items():
            print(f"{split}: {info['imagenes']} imágenes; niveles: {info['niveles_por_clase']}")
        for warning in report['advertencias']:
            print('Advertencia: ' + warning)
        if args.solo_verificar or args.verificar_entorno:
            print('Dataset compatible con el criterio v2. No se inició entrenamiento.')
            return
        train(args, dataset, report)
    except (ValueError, OSError, yaml.YAMLError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
