"""Repetir V1 o V2 base desde sus datos congelados, sin consultar CVAT ni test."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Laboratorio/Modelos'))
from conjuntos import dataset_directory, digest, verify_export


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ensayo', required=True, help='ID completo del ensayo conservado en Experimentos.')
    p.add_argument('--nombre', help='ID nuevo; obligatorio para entrenar.')
    p.add_argument('--device', choices=('cpu', 'auto'), default='cpu')
    p.add_argument('--solo-verificar', action='store_true')
    p.add_argument('--epochs', type=int, help='Cambiar el máximo de épocas; omitir para repetir la configuración.')
    args = p.parse_args(argv)
    try:
        for value in (args.ensayo, args.nombre):
            if value is not None and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,119}', value):
                raise ValueError('Los nombres admiten letras, números, guiones y guiones bajos.')
        source = ROOT / 'Laboratorio/Experimentos' / args.ensayo
        manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8-sig'))
        version = json.loads((source / 'version_datos.json').read_text(encoding='utf-8-sig'))
        config = json.loads((source / 'config_interfaz.json').read_text(encoding='utf-8-sig'))
        verify_export(dataset_directory(ROOT, source, manifest))
        for file, key in [('snapshot_cvat.json', 'snapshot_sha256'), ('particion.json', 'partition_sha256')]:
            if digest(source / file) != version[key]:
                raise ValueError(f'Cambió {file}; no se puede repetir esa versión.')
        checkpoint = ROOT / config['model']
        if not checkpoint.resolve().is_relative_to((ROOT / 'Modelos/preentrenados').resolve()) or not checkpoint.is_file():
            raise ValueError('Faltan los pesos generales originales. Ejecuta primero preparar.py.')
        if args.epochs is not None and args.epochs < 1:
            raise ValueError('epochs debe ser positivo.')
        print(f'{args.ensayo}: datos, snapshot, partición y pesos disponibles. Solo train/val; sin CVAT ni test.', flush=True)
        if args.solo_verificar:
            return
        if not args.nombre:
            raise ValueError('Indica --nombre para conservar el ensayo original.')
        target = ROOT / 'Laboratorio/Experimentos' / args.nombre
        target.mkdir(exist_ok=False)
        for name in ('manifest.json', 'version_datos.json', 'snapshot_cvat.json', 'particion.json', 'revision_etiquetas.json'):
            shutil.copy2(source / name, target / name)
        config.update(run=args.nombre, reproduction_of=args.ensayo)
        config['epochs'] = args.epochs or config['epochs']
        (target / 'config_interfaz.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
        import piloto_modulos as pilot
        pilot.RUN = target
        pilot.SEED = config['seed']
        if args.device == 'cpu':
            pilot.compute_device = lambda: 'cpu'
        pilot.train(config['epochs'], checkpoint, config['imgsz'], config['batch'], config['lr'], config['seed'])
        pilot.evaluate()
    except (ValueError, OSError, KeyError) as error:
        p.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
