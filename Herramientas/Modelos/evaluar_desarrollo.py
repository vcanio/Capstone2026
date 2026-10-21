"""Evaluar pesos existentes con las fotos revisadas de desarrollo V2."""
import argparse
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re

import datos_modelos as datasets
from particion_niveles import load_partition, verify_binding
from rutas_datos import current_image_path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('YOLO_CONFIG_DIR', str(ROOT / '.config-modelo'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.config-modelo/matplotlib'))


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def development_records(run):
    """Use the reviewed snapshot bound to these weights, without changing its export."""
    run = Path(run)
    partition = load_partition(datasets.ROOT)
    if not partition:
        raise ValueError('Falta la partición registrada de desarrollo V2.')
    names = ('manifest.json', 'snapshot_cvat.json', 'particion.json', 'version_datos.json')
    signature = tuple(digest(run / name) for name in names)
    return _reviewed_records(str(run.resolve()), signature, partition['binding']['sha256'])


@lru_cache(maxsize=8)
def _reviewed_records(run_name, signature, binding_hash):
    run = Path(run_name)
    manifest, snapshot, partition, metadata = [read(run / name) for name in
        ('manifest.json', 'snapshot_cvat.json', 'particion.json', 'version_datos.json')]
    if (metadata.get('state') != 'lista_niveles' or not metadata.get('review') or
            metadata.get('id') != manifest.get('version_datos') or
            signature[1] != metadata.get('snapshot_sha256') or
            signature[2] != metadata.get('partition_sha256')):
        raise ValueError('Las anotaciones revisadas no coinciden con la copia del modelo.')
    if manifest.get('criterion', {}).get('stage') != 'base':
        raise ValueError('Esta evaluación requiere un modelo V2 de la etapa base.')
    report, rows = datasets.inspect(snapshot, partition['validation_ids'])
    verify_binding(datasets.ROOT, partition, report)
    if (report.get('bloqueos_entrenamiento') or report['clases'] != manifest['clases'] or
            report.get('partition_binding') != manifest.get('partition_binding')):
        raise ValueError('La revisión y la partición no corresponden a las clases del modelo.')
    return [{**photo, 'truth_rows': rows[photo['imagen_id']]}
            for photo in report['imagenes'] if photo['split'] in ('val', 'diagnostico')]


def verified_image(photo):
    path = datasets.ROOT / current_image_path('Datos/' + photo['archivo'])
    if digest(path) != photo['sha256']:
        raise ValueError('La imagen revisada cambió: ' + photo['imagen'])
    return path


def evaluate(run, *, device=None):
    import numpy as np
    import torch
    from PIL import Image, ImageDraw, ImageOps
    from ultralytics import YOLO
    from comparar_niveles import evaluate_masks, aggregate

    run = Path(run).resolve()
    records = development_records(run)
    manifest, config = read(run / 'manifest.json'), read(run / 'config_interfaz.json')
    weights = run / 'entrenamiento/weights/best.pt'
    model = YOLO(str(weights))
    classes = [model.names[i] for i in range(len(model.names))]
    if classes != manifest['clases']:
        raise ValueError('Los pesos no coinciden con las clases de las anotaciones.')
    states = tuple(name.removeprefix('Nivel_') for name in classes)
    device = device if device is not None else 0 if torch.cuda.is_available() else 'cpu'
    summaries = []
    for index, photo in enumerate(records, 1):
        with Image.open(verified_image(photo)) as original:
            image = ImageOps.exif_transpose(original).convert('RGB')
        truth = []
        for line in photo['truth_rows']:
            values = line.split()
            coords = np.asarray(list(map(float, values[1:]))).reshape(-1, 2) * image.size
            mask = Image.new('1', image.size)
            ImageDraw.Draw(mask).polygon([tuple(point) for point in coords], fill=1)
            truth.append((int(values[0]), np.asarray(mask, dtype=bool)))
        prediction = model.predict(image, conf=.25, iou=.7, imgsz=config['imgsz'],
                                   device=device, retina_masks=True, verbose=False)[0]
        predicted = []
        if prediction.masks is not None:
            for cls, mask in zip(prediction.boxes.cls.cpu().tolist(), prediction.masks.data.cpu().numpy()):
                if mask.shape != (image.height, image.width):
                    raise ValueError('La máscara no coincide con la foto completa.')
                predicted.append((int(cls), mask.astype(bool)))
        summaries.append({'imagen': photo['imagen'], 'sha256': photo['sha256'],
                          **evaluate_masks(truth, predicted, states=states)})
        print(f'{run.name}: {index}/{len(records)} {photo["imagen"]}', flush=True)
    value = {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
             'model': weights.relative_to(ROOT).as_posix(), 'weights_sha256': digest(weights),
             'snapshot_sha256': digest(run / 'snapshot_cvat.json'),
             'partition_binding': manifest['partition_binding'],
             'confidence': .25, 'nms_iou': .7, 'minimum_mask_iou': .5, 'imgsz': config['imgsz'],
             'metrics': aggregate(summaries, states=states), 'images': summaries}
    output = run / 'evaluacion_desarrollo.json'
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(output)
    print(json.dumps({'run': run.name, 'metrics': value['metrics']}, ensure_ascii=False), flush=True)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', args.run):
        parser.error('Nombre de ensayo inválido.')
    evaluate(ROOT / 'Experimentos' / args.run)


if __name__ == '__main__':
    main()
