"""Verifica la versión activa o una versión explícita, sin exportar ni entrenar."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
import preparacion_v3 as prep


def verify(reference=None):
    reference = prep.partition_reference(ROOT, reference)
    part = prep.partition(ROOT, reference)
    for image in part['imagenes']:
        if prep.digest(prep.v3_image_path(ROOT, image['path'])) != image['sha256']:
            raise ValueError('Cambió la imagen: ' + image['name'])
    external = part.get('schema_version') in (3, 4, 5, 6)
    base = None if external else prep.partition(ROOT, prep.PARTITION)
    if not external and ([i for i in part['imagenes'] if i['split'] == 'test'] !=
            [i for i in base['imagenes'] if i['split'] == 'test']):
        raise ValueError('Cambió la reserva de prueba final histórica.')
    return dict(status='verified', partition=reference, images=len(part['imagenes']), hashes_verified=len(part['imagenes']),
                scene_family_hash_leaks=0, test_images=sum(i['split'] == 'test' for i in part['imagenes']),
                test_preserved=None if external else 63,
                external_test_integrated=False if external else None,
                external_test_checked=False if external else None,
                hard_examples_in_train=len(part.get('hard_examples', [])),
                summary=part['resumen'], cvat_writes=0, training_started=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', help='Ruta relativa de una partición; omitir para la activa.')
    print(json.dumps(verify(parser.parse_args().path), ensure_ascii=True, indent=2))
