"""Preparar explícitamente un candidato experimental en la app local.

No modifica el modelo V3 ni activa el filtro en la ruta normal de la app.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil

from entrenamiento_visibilidad import ROOT, WEIGHT, WEIGHT_SHA256, sha256
from visibilidad_foto import decision


def prepare(run_name):
    if not re.fullmatch(r'visibilidad_foto_[0-9]{8}_[0-9]{6}_[0-9a-f]{4}', run_name):
        raise ValueError('Nombre de ensayo de visibilidad inválido.')
    run = ROOT / 'Experimentos' / run_name
    result = json.loads((run / 'resultado.json').read_text(encoding='utf-8'))
    if result.get('schema') != 'visibilidad_foto_ensayo_v1' or result.get('test_used') is not False:
        raise ValueError('El ensayo no tiene la procedencia requerida.')
    job_root = ROOT / 'Experimentos/panel_pruebas'
    matching = []
    for state_path in job_root.glob('*/estado.json'):
        state = json.loads(state_path.read_text(encoding='utf-8'))
        if state.get('config', {}).get('run') == run_name and state.get('state') == 'done':
            matching.append(state_path.parent / 'revision_visibilidad.json')
    if len(matching) != 1 or not matching[0].is_file() or sha256(matching[0]) != result.get('snapshot_sha256'):
        raise ValueError('No se encuentra la revisión congelada del trabajo terminado.')
    snapshot = json.loads(matching[0].read_text(encoding='utf-8'))
    threshold = result.get('threshold')
    val = result.get('validation', [])
    if threshold is None or len(val) != 69 or any(r.get('split') != 'val' for r in val):
        raise ValueError('El ensayo no tiene umbral y validación completos.')
    expected_val = {r['name']: r['etiqueta'] for r in snapshot['images'] if r['split'] == 'val'}
    if len(expected_val) != 69 or len({r['name'] for r in val}) != 69 or any(expected_val.get(r['name']) != r['etiqueta'] for r in val):
        raise ValueError('La validación no coincide con la revisión congelada.')
    for row in val:
        if row['decision'] != decision(row['score_apta'], threshold):
            raise ValueError('Las decisiones no coinciden con el umbral congelado.')
    apt = [row for row in val if row['etiqueta'] == 'apta']
    blocked = [row for row in val if row['etiqueta'] == 'no_apta']
    if len(apt) + len(blocked) != 69 or not apt or not blocked:
        raise ValueError('La validación debe contener ambas clases revisadas.')
    if (sum(x['decision'] == 'apta' for x in apt) / len(apt) < .8 or
            any(x['decision'] == 'apta' for x in blocked)):
        raise ValueError('El candidato no cumple los criterios experimentales de aceptación.')
    checkpoint = run / 'best.pt'
    if sha256(WEIGHT) != WEIGHT_SHA256 or sha256(checkpoint) != result.get('checkpoint_sha256'):
        raise ValueError('Los pesos no coinciden con los hashes del ensayo.')
    target = ROOT / 'Aplicacion/modelos'
    base_name = 'visibilidad_base_' + WEIGHT_SHA256[:12] + '.pt'
    model_name = 'visibilidad_candidato_' + result['checkpoint_sha256'][:12] + '.pt'
    for source, name, expected in [(WEIGHT, base_name, WEIGHT_SHA256),
                                   (checkpoint, model_name, result['checkpoint_sha256'])]:
        destination = target / name
        if destination.exists():
            if sha256(destination) != expected:
                raise ValueError('El archivo de destino ya existe con otro contenido.')
        else:
            temporary = destination.with_suffix('.descarga')
            with source.open('rb') as inp, temporary.open('xb') as out:
                shutil.copyfileobj(inp, out)
            if sha256(temporary) != expected:
                raise ValueError('La copia de los pesos no coincide.')
            os.replace(temporary, destination)
    config = {'policy': 'visibilidad_foto_v1', 'base_file': base_name, 'base_sha256': WEIGHT_SHA256,
              'model_file': model_name, 'model_sha256': result['checkpoint_sha256'], 'threshold': threshold,
              'run': run_name, 'experimental': True, 'test_used': False}
    destination = target / 'visibilidad_experimental.json'
    if destination.exists():
        previous_hash = sha256(destination)
        backup = target / ('visibilidad_experimental_' + previous_hash[:12] + '.json')
        if not backup.exists():
            shutil.copy2(destination, backup)
    temporary = target / 'visibilidad_experimental.json.tmp'
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(config, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    os.replace(temporary, destination)
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', help='ID del ensayo terminado de visibilidad')
    args = parser.parse_args()
    result = prepare(args.run)
    print('Candidato experimental preparado:', result['run'])
    print('Abrir explícitamente: http://127.0.0.1:8095/?visibilidad=experimental')


if __name__ == '__main__':
    main()
