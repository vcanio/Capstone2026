"""Archivar pruebas retiradas y verificar la limpieza de Registros del 23/10/2026.

--apply tiene destinos y extensiones acotados; nunca borra fotos originales o etiquetas.
--verify comprueba todos los archivos conservados/archivados frente al inventario previo.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / 'Datos/Registros'
BACKUP = ROOT / '.resguardo/orden_registros_20261023'
RECEIPT = REG / 'Historico/orden_20261023.json'
RETIRED = ('job67_primeras10_20261022', 'parciales_lider_express_t27_20261022',
           'recortes_lider2_001_005_20261022', 'todos_niveles_job67_001_005_20261022')
RELOCATIONS = {
    'Datos/Registros/Seleccion/lider_express_20261019':
        'Datos/Registros/Historico/V2/Seleccion/lider_express_20261019',
    'Datos/Registros/visibilidad_limitada_20261019.json':
        'Datos/Registros/Historico/V2/visibilidad_limitada_20261019.json',
    'Datos/Registros/CVAT/tarea_20.json': 'Datos/Registros/Historico/CVAT/tarea_20.json',
    'Datos/Registros/CVAT/tarea_21.json': 'Datos/Registros/Historico/CVAT/tarea_21.json',
}
# Estos documentos operativos pueden actualizarse; sus bytes previos quedan respaldados.
EDITABLE = {
    'Datos/Registros/README.md', 'Datos/Registros/lotes.json', 'Datos/Registros/CVAT/README.md',
    'Datos/README.md', 'Datos/V2/visibilidad_limitada_20261019/README.md',
    'Datos/Registros/CVAT/revisiones/visibilidad_20261019T222744Z/cierre_criterio/revision_final.html',
    *(f'Datos/Registros/CVAT/revisiones/{name}/README.md' for name in RETIRED),
}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def require(value, message):
    if not value:
        raise ValueError(message)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def checked(path, parent):
    path = path.resolve()
    require(path.is_relative_to(parent.resolve()) and path != parent.resolve(), 'Ruta fuera del alcance: ' + str(path))
    require(not path.is_symlink(), 'No se permiten enlaces simbólicos: ' + str(path))
    return path


def prepare():
    require(not BACKUP.exists() and not RECEIPT.exists(), 'La versión ya existe; usar --verify.')
    before = []
    for p in sorted(REG.rglob('*')):
        if p.is_file():
            checked(p, REG)
            before.append({'path': rel(p), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    actions = []
    for row in before:
        p = ROOT / row['path']
        if p.suffix.lower() in ('.jpg', '.jpeg', '.png') and p.parent.name in RETIRED:
            destination = BACKUP / 'vistas_pruebas_retiradas' / p.relative_to(REG / 'CVAT/revisiones')
            actions.append({**row, 'action': 'archivar_vista', 'destination': rel(destination)})
        elif p.suffix == '.cache':
            require(p.is_relative_to(REG / 'Versiones_modelos') and p.name in ('train.cache', 'val.cache'),
                    'Caché fuera del alcance previsto.')
            actions.append({**row, 'action': 'eliminar_cache_regenerable'})
        else:
            for old, new in RELOCATIONS.items():
                if row['path'] == old or row['path'].startswith(old + '/'):
                    actions.append({**row, 'action': 'mover_historico',
                                    'destination': new + row['path'][len(old):]})
                    break
    require(len([a for a in actions if a['action'] == 'eliminar_cache_regenerable']) == 4,
            'Cambió el inventario de cachés; revisar antes de limpiar.')
    # Respaldo de documentos que se actualizarán, sin copiar datasets completos.
    for name in EDITABLE:
        source = checked(ROOT / name, ROOT)
        require(source.is_file(), 'Documento ausente: ' + name)
        target = checked(BACKUP / 'documentos_previos' / name, BACKUP)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    write(BACKUP / 'inventario_antes.json', before)
    write(BACKUP / 'plan.json', actions)
    return before, actions


def apply():
    before, actions = prepare()
    # Validar todas las rutas y los hashes antes de iniciar el primer traslado.
    for a in actions:
        source = checked(ROOT / a['path'], REG)
        require(sha(source) == a['sha256'], 'Archivo cambiado desde el inventario.')
        if a.get('destination'):
            dest = checked(ROOT / a['destination'], BACKUP if a['action'] == 'archivar_vista' else REG / 'Historico')
            require(not dest.exists(), 'Destino existente: ' + str(dest))
    for a in actions:
        source = ROOT / a['path']
        if a.get('destination'):
            dest = ROOT / a['destination']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest))
            require(sha(dest) == a['sha256'], 'El traslado no conserva los bytes.')
        else:
            # Solo las cuatro cachés de Ultralytics verificadas arriba, nunca images/labels.
            source.unlink()
    for p in [REG / 'Seleccion/lider_express_20261019', REG / 'Seleccion']:
        if p.exists():
            p.rmdir()  # Solo acepta directorios completamente vacíos.
    for name in RETIRED:
        directory = REG / 'CVAT/revisiones' / name
        doc = directory / 'README.md'
        previous = doc.read_text(encoding='utf-8-sig')
        archived = [a for a in actions if a['action'] == 'archivar_vista' and Path(a['path']).parent.name == name]
        for a in archived:
            filename = Path(a['path']).name
            target = os.path.relpath(ROOT / a['destination'], directory).replace('\\', '/')
            previous = previous.replace('](' + filename + ')', '](' + target + ')')
        note = ('> **Prueba histórica retirada / vista previa fuera del dataset.** '
                'El 23/10/2026 sus imágenes de revisión se trasladaron al archivo local '
                f'`.resguardo/orden_registros_20261023/vistas_pruebas_retiradas/{name}/`. '
                'Los planes, coordenadas, verificaciones y reversiones permanecen aquí. '
                'Las cifras e instrucciones siguientes describen aquella prueba, no el estado vigente.\n\n')
        doc.write_text(note + previous, encoding='utf-8')
    # Corregir las tres entradas que enlazaban la selección histórica trasladada.
    path = ROOT / 'Datos/V2/visibilidad_limitada_20261019/README.md'
    path.write_text(path.read_text(encoding='utf-8-sig').replace(
        '../../Registros/Seleccion/', '../../Registros/Historico/V2/Seleccion/'), encoding='utf-8')
    path = REG / 'CVAT/revisiones/visibilidad_20261019T222744Z/cierre_criterio/revision_final.html'
    path.write_text(path.read_text(encoding='utf-8-sig').replace(
        '../../../../Seleccion/', '../../../../Historico/V2/Seleccion/'), encoding='utf-8')
    write(RECEIPT, {'schema_version': 1, 'date': datetime.now(timezone.utc).isoformat(),
                    'backup': rel(BACKUP), 'inventario_previo': rel(BACKUP / 'inventario_antes.json'),
                    'actions': actions, 'editable_documents': sorted(EDITABLE),
                    'image_writes': 0, 'cvat_writes': 0})


def verify():
    receipt = json.loads(RECEIPT.read_text(encoding='utf-8'))
    before = json.loads((BACKUP / 'inventario_antes.json').read_text(encoding='utf-8'))
    actions = {a['path']: a for a in receipt['actions']}
    checked_count = 0
    for row in before:
        name = row['path']
        action = actions.get(name)
        if action:
            require(not (ROOT / name).exists(), 'Archivo retirado aún en su ubicación anterior: ' + name)
            if action.get('destination'):
                require(sha(ROOT / action['destination']) == row['sha256'], 'Archivo histórico alterado: ' + name)
            checked_count += 1
        elif name == 'Datos/Registros/Particiones/v3_458_20261023/verificacion.json':
            report = json.loads((ROOT / name).read_text(encoding='utf-8'))
            require(report['estado'] == 'verificado' and report['hashes_verificados'] == 458
                    and report['training_enabled'] is False, 'Informe V3 regenerado inválido.')
        elif name in EDITABLE:
            require(sha(BACKUP / 'documentos_previos' / name) == row['sha256'], 'Respaldo documental distinto: ' + name)
        else:
            require(sha(ROOT / name) == row['sha256'], 'Archivo conservado modificado: ' + name)
            checked_count += 1
    state = json.loads((REG / 'estado_actual.json').read_text(encoding='utf-8'))
    current = state['proyecto_en_preparacion']
    partition = json.loads((ROOT / current['particion']).read_text(encoding='utf-8'))
    reference = json.loads((ROOT / current['fuente_conteo_anotaciones']).read_text(encoding='utf-8'))
    catalog = json.loads((REG / 'lotes.json').read_text(encoding='utf-8'))
    catalog_ids = {lot['id'] for lot in catalog['lotes']}
    require(set(current['lotes']).issubset(catalog_ids), 'Lote actual ausente del catálogo.')
    require(current['imagenes'] == len(partition['imagenes']) == 458
            and current['resumen_particion'] == partition['resumen']
            and current['poligonos_segun_lectura_de_referencia'] == reference['polygons'] == 2313
            and current['training_enabled'] is False, 'Estado actual contradice las fuentes.')
    # Índices operativos nuevos y documentos editados; no recorre guías históricas congeladas.
    documents = [REG / 'README.md', REG / 'CVAT/README.md', REG / 'Lotes/README.md',
                 REG / 'Particiones/README.md', REG / 'Versiones_modelos/README.md',
                 REG / 'Historico/README.md', REG / 'Historico/CVAT/README.md',
                 REG / 'Historico/V2/README.md', REG / 'CVAT/revisiones/README.md',
                 ROOT / 'Datos/README.md', ROOT / 'Datos/V3/README.md',
                 *(REG / 'CVAT/revisiones' / name / 'README.md' for name in RETIRED)]
    links_checked = 0
    for doc in documents:
        text = doc.read_text(encoding='utf-8')
        require('\ufffd' not in text, 'Codificación incorrecta: ' + rel(doc))
        for value in re.findall(r'\]\(([^)]+)\)', text):
            value = value.strip('<>')
            if urlsplit(value).scheme or value.startswith('#'):
                continue
            target = doc.parent / unquote(value.split('#')[0])
            require(target.is_file(), 'Enlace roto en ' + rel(doc) + ': ' + value)
            links_checked += 1
    media = [a for a in receipt['actions'] if a['action'] == 'archivar_vista']
    cache = [a for a in receipt['actions'] if a['action'] == 'eliminar_cache_regenerable']
    summary = {'estado': 'verificado', 'archivos_previos': len(before),
               'archivos_conservados_o_trasladados_verificados': checked_count,
               'vistas_historicas_archivadas': len(media), 'bytes_archivados': sum(a['bytes'] for a in media),
               'caches_eliminadas': len(cache), 'bytes_cache_eliminados': sum(a['bytes'] for a in cache),
               'registros_historicos_reubicados': sum(a['action'] == 'mover_historico' for a in receipt['actions']),
               'enlaces_documentales_verificados': links_checked, 'lotes_catalogados': len(catalog_ids),
               'informes_regenerables': ['Particiones/v3_458_20261023/verificacion.json'],
               'imagenes_originales_modificadas': 0, 'escrituras_cvat': 0}
    write(REG / 'Historico/verificacion_orden_20261023.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--apply', action='store_true')
    modes.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.apply:
        apply()
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
