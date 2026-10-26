"""Fija/verifica las 458 imágenes V3 por familia y escena, sin exportar ni entrenar.

Uso desde la raíz: .venv-cvat/Scripts/python.exe Laboratorio/Datos/particionar_v3_458.py --verify
--apply se admite una sola vez; conserva respaldo íntegro de los registros modificados.
No consulta ni escribe CVAT. Las listas son un catálogo de asignación, no datos YOLO aprobados.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import html
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import os

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Datos/Registros/Particiones/v3_458_20261023'
OLD = ROOT / 'Datos/Registros/Particiones/lider_express_v2_20261019'
BACKUP = ROOT / '.resguardo/particion_v3_458_20261023'
REG = ROOT / 'Datos/Registros/CVAT/criterio_v3.json'
TASK = ROOT / 'Datos/Registros/CVAT/tarea_28.json'
LOT = ROOT / 'Datos/V3/Lider 2'
PART = 'Datos/Registros/Particiones/v3_458_20261023/particion.json'
MUTABLE = [REG, TASK, LOT / 'manifest.json', LOT / 'inventario.csv', LOT / 'README.md']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def csv_read(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def csv_write(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def configuration():
    inherited = read(OLD / 'grupos_escena.json')
    groups = [{**g, 'familias': [f'lider_express_{n:03d}' for n in g['familias']],
               'local_id': 'lider_express', 'procedencia': 'particion_20261019_conservada'}
              for g in inherited['grupos']]
    new = read(OUT / 'lider2_grupos.json')
    photos = [n for g in new['grupos'] for n in g['fotos']]
    require(sorted(photos) == list(range(1, 123)), 'La revisión debe cubrir 001-122 una sola vez.')
    groups += [{**g, 'familias': [f'lider_2_{n:03d}' for n in g['fotos']],
                'local_id': 'lider_2', 'procedencia': 'revision_visual_20261023'}
               for g in new['grupos']]
    require(len({g['id'] for g in groups}) == len(groups), 'ID de grupo repetido.')
    return {'schema_version': 1, 'unidad': 'familia_y_grupo_escena_conservador',
            'alcance': new['alcance'], 'metodo_lider2': new['metodo'],
            'grupos': groups}


def assigned_rows(original, config):
    by_family = {}
    for group in config['grupos']:
        require(group['split'] in ('train', 'val', 'test'), 'Split inválido en configuración.')
        for family in group['familias']:
            require(family not in by_family, 'Familia repetida: ' + family)
            by_family[family] = group
    records = copy.deepcopy(original['images'])
    for row in records:
        g = by_family[row['familia']]
        if row['task_id'] != 28:
            require((row['grupo_escena'], row['split']) == (g['id'], g['split']),
                    'No se permite mover una asignación anterior: ' + row['name'])
        else:
            row.update(grupo_escena=g['id'], split=g['split'],
                       grupo_escena_estado='revisado_visualmente_por_asistente')
    require({r['familia'] for r in records} == set(by_family), 'Familias faltantes o sobrantes.')
    return records


def validate(records):
    require(len(records) == 458, 'Deben existir exactamente 458 imágenes.')
    for key in ('name', 'path', 'sha256'):
        require(len({r[key] for r in records}) == 458, 'Duplicados en ' + key)
    families, groups = defaultdict(set), defaultdict(set)
    for r in records:
        require(r['split'] in ('train', 'val', 'test'), 'Imagen sin asignar.')
        families[r['familia']].add(r['split'])
        groups[r['grupo_escena']].add(r['split'])
        path = (ROOT / r['path']).resolve()
        require(path.is_relative_to(ROOT) and path.is_file(), 'Ruta inválida: ' + r['path'])
        require(path.stat().st_size == r['bytes'] and digest(path) == r['sha256'],
                'Bytes modificados: ' + r['name'])
    require(all(len(s) == 1 for s in families.values()), 'Fuga entre variantes de una familia.')
    require(all(len(s) == 1 for s in groups.values()), 'Fuga entre vistas de una escena.')
    require(len(families) == 181 and len(groups) == 43, 'Cantidad inesperada de familias/grupos.')
    old = read(OLD / 'particion.json')['imagenes']
    by_name = {Path(r['name']).stem: r for r in records}
    for before in old:
        after = by_name[before['cvat_name']]
        require(all(after[k] == before[k] for k in ('sha256', 'familia', 'grupo_escena', 'split')),
                'Se alteró la reserva o partición histórica: ' + before['cvat_name'])
    reserve = read(ROOT / 'Datos/Registros/reserva_evaluacion.json')
    _, history = csv_read(ROOT / 'Datos/Registros/inventario.csv')
    reserved_hashes = {r['sha256'] for r in history
                       if r['imagen_id'] in reserve['image_ids'] or r['grupo_escena'] in reserve['groups']}
    require(not reserved_hashes.intersection(r['sha256'] for r in records), 'Reserva histórica incluida.')
    summary = {}
    for split in ('train', 'val', 'test'):
        subset = [r for r in records if r['split'] == split]
        summary[split] = {'imagenes': len(subset),
                          'reales': sum(r['origen'] == 'real' for r in subset),
                          'sinteticas': sum(r['origen'] != 'real' for r in subset),
                          'grupos': len({r['grupo_escena'] for r in subset}),
                          'por_tarea': dict(sorted(Counter(r['task_id'] for r in subset).items()))}
    return summary


def lists(records):
    result = {}
    for split in ('train', 'val', 'test'):
        subset = sorted((r for r in records if r['split'] == split), key=lambda r: r['name'])
        result[split + '_catalogo'] = subset
        if split != 'train':
            result[split + '_real_principal'] = [r for r in subset if r['origen'] == 'real']
            result[split + '_sintetica_diagnostico'] = [r for r in subset if r['origen'] != 'real']
    return result


def partition_metadata(records):
    return {'estado': 'fijada_por_familia_y_escena', 'registro': PART,
            'unidad': 'familia_y_grupo_escena_conservador',
            'imagenes_por_split': dict(Counter(r['split'] for r in records)),
            'habilita_entrenamiento': False}


def write_catalog(records, config):
    """Documento local: enlaces a los originales, sin copiar ni cargar todas las fotos."""
    esc = html.escape
    body = ['<!doctype html><html lang="es"><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>458 imágenes V3 · Catálogo por escena</title>',
            '<style>body{font:16px/1.5 system-ui;margin:36px auto;max-width:1100px;padding:0 20px;color:#183040}',
            'a{color:#075b89}table{border-collapse:collapse;width:100%;margin:16px 0 40px}',
            'td,th{padding:7px 10px;border-bottom:1px solid #d5dfe5;text-align:left}',
            'nav{display:flex;gap:12px;flex-wrap:wrap}section{scroll-margin-top:20px}',
            'small{color:#435b69}h2{margin-top:44px}</style><body>',
            '<h1>458 imágenes V3, organizadas por escena</h1>',
            '<p>327 entrenamiento · 68 validación · 63 prueba final. '
            '181 originales reales y 277 variantes sintéticas. 43 grupos conservadores.</p>',
            '<p>Las imágenes conservan sus archivos originales. Los enlaces abren cada fotografía. '
            'Este catálogo no aprueba anotaciones ni inicia entrenamiento.</p>',
            '<p><a href="README.md">Registro y reglas</a> · <a href="inventario.csv">Descargar inventario CSV</a>'
            ' · <a href="verificacion.json">Verificación</a></p>',
            '<nav><a href="#train">Entrenamiento</a><a href="#val">Validación</a>'
            '<a href="#test">Prueba final</a><a href="#evidencia">Evidencia de revisión</a></nav>']
    for split, title in [('train', 'Entrenamiento'), ('val', 'Validación'), ('test', 'Prueba final')]:
        body.append(f'<h2 id="{split}">{title}</h2>')
        for group in config['grupos']:
            if group['split'] != split:
                continue
            subset = sorted((r for r in records if r['grupo_escena'] == group['id']), key=lambda r:r['name'])
            body.append(f'<section id="{group["id"]}"><h3>{group["id"]} · {len(subset)} imágenes</h3>')
            body.append('<p>' + esc(group['motivo']) + '</p>')
            body.append('<table><tr><th>Imagen</th><th>Familia</th><th>Origen</th><th>Tarea CVAT</th></tr>')
            for r in subset:
                url = quote(os.path.relpath(ROOT / r['path'], OUT).replace('\\', '/'), safe='/')
                body.append(f'<tr><td><a href="{url}" target="_blank">{esc(r["name"])}</a></td>'
                            f'<td>{esc(r["familia"])}</td><td>{esc(r["origen"])}</td><td>{r["task_id"]}</td></tr>')
            body.append('</table></section>')
    body.append('<h2 id="evidencia">Revisión visual de Líder 2 antes de fijar el reparto</h2><ul>')
    for p in sorted((OUT / 'evidencia').glob('*.jpg')):
        body.append(f'<li><a href="evidencia/{p.name}">Fotos {p.stem.replace("_", "–")}</a></li>')
    body.append('</ul><p>La prueba queda reservada desde esta versión. No usarla para ajustar el modelo '
                'ni los umbrales. Las futuras variantes heredan el grupo y la partición de su original.</p></body></html>')
    (OUT / 'catalogo_escenas.html').write_text('\n'.join(body), encoding='utf-8')


def apply(original, config, records, summary):
    require(not (OUT / 'particion.json').exists() and not BACKUP.exists(),
            'Ya existe esta versión/respaldo. Use --verify; no se sobrescribe.')
    # Respaldar todo antes de modificar el primer registro.
    for path in MUTABLE:
        target = BACKUP / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    protected = {relative(p): digest(p) for p in OLD.rglob('*') if p.is_file()}
    for path in [ROOT / 'Datos/Registros/reserva_evaluacion.json', ROOT / 'Datos/Registros/inventario.csv']:
        protected[relative(path)] = digest(path)
    now = datetime.now(timezone.utc).isoformat()
    write(OUT / 'grupos_escena.json', config)
    data = {'schema_version': 1, 'id': OUT.name, 'created_at': now,
            'criterion_version': 'area_util_nivel_v3', 'estado': 'fijada_pendiente_revision_anotaciones',
            'aprobado_entrenamiento': False, 'training_enabled': False,
            'resumen': summary, 'imagenes': records,
            'grupos_sha256': digest(OUT / 'grupos_escena.json'),
            'config_lider2_sha256': digest(OUT / 'lider2_grupos.json'),
            'respaldo': relative(BACKUP), 'archivos_protegidos_sha256': protected,
            'fuentes_respaldadas_sha256': {relative(p): digest(BACKUP / p.relative_to(ROOT)) for p in MUTABLE},
            'politica': {'familias_y_escenas_sin_cruces': True, 'asignaciones_anteriores_conservadas': 336,
                         'evaluacion_principal': 'solo_originales_reales',
                         'sinteticas_val_test': 'diagnostico_separado',
                         'test': 'reservado_para_evaluacion_final_sin_ajuste_de_modelo_ni_umbrales',
                         'futuras_variantes': 'heredar_familia_grupo_y_split_del_original',
                         'exportacion_y_entrenamiento': 'no_habilitados_por_esta_particion'}}
    write(OUT / 'particion.json', data)
    columns = ['name', 'path', 'task_id', 'familia', 'grupo_escena', 'split', 'origen', 'sha256']
    csv_write(OUT / 'inventario.csv', columns, [{k: r[k] for k in columns} for r in records])
    (OUT / 'listas').mkdir()
    for name, subset in lists(records).items():
        (OUT / 'listas' / (name + '.txt')).write_text(''.join(r['path'] + '\n' for r in subset), encoding='utf-8')
    evidence = OUT / 'evidencia'
    evidence.mkdir()
    contacts = sorted((ROOT / '.tmp/escenas_lider2_20261023').glob('*.jpg'))
    require(len(contacts) == 11, 'Faltan hojas de contacto revisadas.')
    for path in contacts:
        shutil.copy2(path, evidence / path.name)
    write_catalog(records, config)
    if (ROOT / '.tmp/preparacion_v3_20261023.json').is_file():
        shutil.copy2(ROOT / '.tmp/preparacion_v3_20261023.json', OUT / 'estado_anotaciones_referencia.json')
    updated = copy.deepcopy(original)
    updated['images'] = records
    updated['partition'] = {**partition_metadata(records), 'fijada_at': now}
    write(REG, updated)
    new_by_name = {r['name']: r for r in records if r['task_id'] == 28}
    for path, key in [(TASK, 'frames'), (LOT / 'manifest.json', 'images')]:
        value = read(path)
        for r in value[key]:
            assigned = new_by_name[r['name']]
            for k in ('grupo_escena', 'split', 'grupo_escena_estado'):
                r[k] = assigned[k]
        value.update(split='ver_inventario', particion=partition_metadata(list(new_by_name.values())))
        value['scene_grouping' if path == TASK else 'scene_grouping_status'] = 'revisado_visualmente_por_asistente'
        write(path, value)
    fields, rows = csv_read(LOT / 'inventario.csv')
    for r in rows:
        assigned = new_by_name[r['archivo']]
        r.update(grupo_escena=assigned['grupo_escena'], particion_modelo=assigned['split'])
    csv_write(LOT / 'inventario.csv', fields, rows)


def verify(config):
    saved = read(OUT / 'particion.json')
    original = read(BACKUP / REG.relative_to(ROOT))
    records = assigned_rows(original, config)
    summary = validate(records)
    require(saved['imagenes'] == records and saved['resumen'] == json.loads(json.dumps(summary)),
            'La partición difiere del plan reproducible.')
    require(saved['grupos_sha256'] == digest(OUT / 'grupos_escena.json')
            and read(OUT / 'grupos_escena.json') == config
            and saved['config_lider2_sha256'] == digest(OUT / 'lider2_grupos.json'), 'Configuración alterada.')
    for name, sha in saved['archivos_protegidos_sha256'].items():
        require(digest(ROOT / name) == sha, 'Archivo histórico modificado: ' + name)
    for name, sha in saved['fuentes_respaldadas_sha256'].items():
        require(digest(BACKUP / name) == sha, 'Respaldo alterado: ' + name)
    current = read(REG)
    require(current['images'] == records, 'Registro V3 sin sincronizar.')
    require(current['training_pipeline_supported'] is False, 'No se debe habilitar entrenamiento.')
    allowed_top = {'images', 'partition'}
    require({k: v for k, v in current.items() if k not in allowed_top}
            == {k: v for k, v in original.items() if k not in allowed_top}, 'Cambios ajenos en registro V3.')
    by_name = {r['name']: r for r in records if r['task_id'] == 28}
    for path, key in [(TASK, 'frames'), (LOT / 'manifest.json', 'images')]:
        current = read(path)
        before = read(BACKUP / path.relative_to(ROOT))
        require(current['training_enabled'] is False, 'No se debe habilitar el lote.')
        require(current['particion'] == partition_metadata(list(by_name.values())), 'Metadatos del lote distintos.')
        for previous, actual in zip(before[key], current[key], strict=True):
            expected = copy.deepcopy(previous)
            for k in ('grupo_escena', 'split', 'grupo_escena_estado'):
                expected[k] = by_name[previous['name']][k]
            require(expected == actual, 'Cambios ajenos en imagen ' + previous['name'])
        allowed = {key, 'split', 'particion', 'scene_grouping', 'scene_grouping_status'}
        require({k:v for k,v in before.items() if k not in allowed}
                == {k:v for k,v in current.items() if k not in allowed}, 'Cambios ajenos en manifest/tarea.')
    fields, actual = csv_read(LOT / 'inventario.csv')
    old_fields, before = csv_read(BACKUP / (LOT / 'inventario.csv').relative_to(ROOT))
    require(fields == old_fields, 'Campos de inventario alterados.')
    for previous, row in zip(before, actual, strict=True):
        assigned = by_name[previous['archivo']]
        require(row == {**previous, 'grupo_escena': assigned['grupo_escena'], 'particion_modelo': assigned['split']},
                'Cambios ajenos en inventario.')
    columns, inventory = csv_read(OUT / 'inventario.csv')
    require(inventory == [{k: str(r[k]) for k in columns} for r in records], 'Catálogo CSV distinto.')
    for name, subset in lists(records).items():
        require((OUT / 'listas' / (name + '.txt')).read_text(encoding='utf-8').splitlines()
                == [r['path'] for r in subset], 'Lista distinta: ' + name)
    catalog = (OUT / 'catalogo_escenas.html').read_text(encoding='utf-8')
    require(catalog.count('<tr><td>') == 458 and catalog.count('<section id=') == 43,
            'Catálogo visual incompleto.')
    return {'estado': 'verificado', 'imagenes': 458, 'hashes_verificados': 458,
            'familias': 181, 'grupos_conservadores': 43, 'resumen': summary,
            'asignaciones_anteriores_conservadas': 336, 'fugas_familia_escena_hash': 0,
            'archivos_historicos_verificados': len(saved['archivos_protegidos_sha256']),
            'escrituras_cvat': 0, 'training_enabled': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--apply', action='store_true')
    modes.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    config = configuration()
    if args.apply:
        original = read(REG)
        records = assigned_rows(original, config)
        summary = validate(records)
        apply(original, config, records, summary)
    result = verify(config)
    write(OUT / 'verificacion.json', {**result, 'checked_at': datetime.now(timezone.utc).isoformat()})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
