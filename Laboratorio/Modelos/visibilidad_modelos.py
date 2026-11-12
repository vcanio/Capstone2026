"""Archivado reversible compartido; nunca modifica pesos o ensayos."""
import json


def archived(root):
    path = root / '.config-modelo/modelos_archivados.json'
    return json.loads(path.read_text(encoding='utf-8')).get('models', {}) if path.is_file() else {}


def current(root):
    path = root / '.config-modelo/version_actual_v3.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None
