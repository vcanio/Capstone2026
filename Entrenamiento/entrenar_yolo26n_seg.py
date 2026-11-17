"""Script reproducible de ajuste fino YOLO26n-seg para la clase única `Nivel`.

Documenta y ejecuta exactamente la configuración del ensayo oficial
`v3_cierre_yolo_contornos_revisados_20261110_222620_aa7c` con `seed=42`
y modo determinista. Por defecto corre en `--dry-run` (sin entrenar ni
alterar el peso oficial).
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_RUN_ID = 'v3_cierre_yolo_contornos_revisados_20261110_222620_aa7c'
OFFICIAL_WEIGHTS_REL = 'Aplicacion/modelos/V3-cierre-revisado-20261110.pt'
OFFICIAL_WEIGHTS_SHA256 = 'dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5'

OFFICIAL_HYPERPARAMETERS = {
    'epochs': 40,
    'patience': 10,
    'imgsz': 640,
    'batch': 2,
    'seed': 42,
    'deterministic': True,
    'optimizer': 'AdamW',
    'lr0': 0.0001,
    'warmup_epochs': 1.0,
    'warmup_bias_lr': 0.0,
    'amp': False,
    'overlap_mask': False,
    'mask_ratio': 2,
    'mosaic': 0.0,
    'mixup': 0.0,
    'copy_paste': 0.0,
    'degrees': 3.0,
    'translate': 0.03,
    'scale': 0.10,
    'shear': 0.0,
    'perspective': 0.0,
    'fliplr': 0.0,
    'flipud': 0.0,
    'hsv_h': 0.01,
    'hsv_s': 0.2,
    'hsv_v': 0.2,
    'workers': 0,
    'cache': False,
    'plots': True,
    'exist_ok': False,
    'resume': False,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_train_args(
    data_yaml: Path,
    project_dir: Path,
    device: str | int = 'cpu',
    fine_tune: bool = True,
    run_name: str = 'entrenamiento',
) -> dict:
    """Construir los argumentos reproducibles de `YOLO.train(...)` para V3."""
    args = dict(OFFICIAL_HYPERPARAMETERS)
    args['data'] = str(data_yaml)
    args['device'] = device
    args['project'] = str(project_dir)
    args['name'] = run_name
    if not fine_tune:
        args.pop('warmup_epochs', None)
        args.pop('warmup_bias_lr', None)
    return args


def verify_official_checkpoint(root: Path = ROOT) -> dict:
    """Verificar presencia e integridad SHA-256 del peso oficial congelado."""
    weights_path = Path(root) / OFFICIAL_WEIGHTS_REL
    if not weights_path.is_file():
        raise FileNotFoundError(f'No se encontró el peso oficial en {weights_path}')
    actual = sha256_file(weights_path)
    if actual != OFFICIAL_WEIGHTS_SHA256:
        raise ValueError(f'SHA-256 inesperado para {OFFICIAL_WEIGHTS_REL}: {actual}')
    return {
        'weights': OFFICIAL_WEIGHTS_REL,
        'sha256': actual,
        'bytes': weights_path.stat().st_size,
    }


def dry_run(data_yaml: Path, project_dir: Path, root: Path = ROOT) -> dict:
    """Validar plantilla YAML, hiperparámetros reproducibles y huella oficial."""
    if not Path(data_yaml).is_file():
        raise FileNotFoundError(f'Falta plantilla o archivo data.yaml: {data_yaml}')
    checkpoint = verify_official_checkpoint(root)
    args = build_train_args(data_yaml, project_dir, device='cpu', fine_tune=True)
    return {
        'status': 'ok',
        'mode': 'dry_run',
        'official_run': OFFICIAL_RUN_ID,
        'checkpoint': checkpoint,
        'train_args': args,
    }


def execute_training(base_weights: Path, data_yaml: Path, project_dir: Path, device: str = 'auto') -> dict:
    """Ejecutar ajuste fino real solo cuando el usuario pasa `--execute` explícitamente."""
    import os
    os.environ.setdefault('YOLO_AUTOINSTALL', 'false')
    import torch
    from ultralytics import YOLO, settings

    settings.update({'sync': False, 'wandb': False, 'mlflow': False, 'tensorboard': False})
    resolved_device = 0 if device == 'auto' and torch.cuda.is_available() else (device if device != 'auto' else 'cpu')
    model = YOLO(str(base_weights))
    if set(model.names.values()) != {'Nivel'}:
        raise ValueError('El checkpoint base para ajuste fino debe tener exclusivamente la clase Nivel.')
    args = build_train_args(data_yaml, project_dir, device=resolved_device, fine_tune=True)
    model.train(**args)
    return {'status': 'completed', 'project_dir': str(project_dir), 'device': resolved_device}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path(__file__).with_name('data.template.yaml'))
    parser.add_argument('--project', type=Path, default=ROOT / 'Experimentos/reproduccion_v3')
    parser.add_argument('--base-weights', type=Path, default=ROOT / OFFICIAL_WEIGHTS_REL)
    parser.add_argument('--device', default='auto')
    parser.add_argument('--dry-run', action='store_true', help='Validar configuración y pesos sin entrenar')
    parser.add_argument('--execute', action='store_true', help='Ejecutar entrenamiento real con Ultralytics')
    args = parser.parse_args()

    if not args.execute:
        print(json.dumps(dry_run(args.data, args.project, ROOT), ensure_ascii=False, indent=2))
        return

    print(json.dumps(execute_training(args.base_weights, args.data, args.project, args.device), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
