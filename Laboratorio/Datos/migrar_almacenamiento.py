"""Inventario y migración por manifiesto, sin seguir enlaces de compatibilidad.

No entrena, evalúa imágenes ni modifica particiones. Cada fase es explícita.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / 'Datos/Registros/Almacenamiento'
EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff'}
C_ROOTS = ('Datos', 'Historico/Datos', 'Historico/Experimentos', 'Laboratorio/Experimentos')
KNOWN_ABSENCES = ['Datos/V1/Lider/lider_%03d.jpg' % n for n in (1, 2, 3)]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def physical_files(base):
    """Do not enumerate a junction, symlink or other reparse point."""
    if base.is_symlink() or base.is_junction():
        return
    with os.scandir(base) as entries:
        for entry in sorted(entries, key=lambda e: e.name.casefold()):
            stat = entry.stat(follow_symlinks=False)
            if getattr(stat, 'st_file_attributes', 0) & 0x400 or entry.is_symlink():
                continue
            path = Path(entry.path)
            if entry.is_dir(follow_symlinks=False):
                yield from physical_files(path)
            elif entry.is_file(follow_symlinks=False):
                yield path


def external_relative(value):
    parts = Path(value).parts
    first = parts[0]
    locales = {'Arauco Quilicura', 'Arauco Quilicura 2', 'Express Independencia',
               'Express Sta Luisa', 'Marcoleta', 'Ohiggins', 'Ohiggins 2'}
    if first in locales:
        return (Path('Fuentes') / value).as_posix()
    prefixes = {'03_Variantes_ocupacion': 'Derivados/Ocupacion_20261106',
                '04_Imagenes_para_pruebas': 'Pruebas_ocupacion'}
    if first in prefixes:
        return (Path(prefixes[first]).joinpath(*parts[1:])).as_posix()
    if len(parts) == 1:
        return 'Catalogo/Originales_20261106/' + first
    return Path(value).as_posix()


def inventory(external):
    REG.mkdir(parents=True, exist_ok=True)
    rows = []
    for side, bases, root in [('E', [external], external),
                              ('C', [ROOT / p for p in C_ROOTS], ROOT)]:
        count = 0
        for base in bases:
            for path in physical_files(base):
                rel = path.relative_to(root).as_posix()
                if side == 'C' and (rel.startswith('Datos/Registros/Almacenamiento/')
                                    or 'Fase 1' in rel or 'Fase 2' in rel):
                    continue
                stat = path.stat()
                rows.append(dict(disco=side, ruta=rel, bytes=stat.st_size,
                                 sha256=sha(path), imagen=path.suffix.lower() in EXTS))
                count += 1
                if count % 1000 == 0:
                    print(f'{side}: {count} archivos verificados', flush=True)
        print(f'{side}: fin, {count} archivos', flush=True)
    write(REG / 'inventario_inicial.json', dict(schema_version=1,
          created_at=datetime.now(timezone.utc).isoformat(),
          raices_c=list(C_ROOTS), enlaces_recorridos=False, archivos=rows))
    plan(external, rows)


def plan(external, rows):
    e_hash = defaultdict(list)
    c_hash = defaultdict(list)
    by_c = {}
    for row in rows:
        if row['disco'] == 'E':
            e_hash[row['sha256']].append(row)
        else:
            c_hash[row['sha256']].append(row)
            by_c[row['ruta']] = row
    # Only whole image-only physical directories can be replaced by compatibility
    # aliases. Mixed evidence folders, V1 and sources are preserved locally.
    candidates = {}
    tree = defaultdict(list)
    for row in rows:
        if row['disco'] != 'C':
            continue
        p = Path(row['ruta'])
        for parent in p.parents:
            if parent.as_posix() != '.':
                tree[parent.as_posix()].append(row)
    for folder, files in sorted(tree.items(), key=lambda x: len(Path(x[0]).parts)):
        if (any(folder == p or folder.startswith(p + '/') for p in candidates)
                or not files or not all(f['imagen'] for f in files)
                or folder.startswith(('Datos/V1/', 'Datos/Registros/', 'Datos/Fuentes/'))):
            continue
        # Avoid moving single illustrations beside a report. Sources stay in C
        # as a verified independent recovery copy; repeated exports move first.
        is_dataset = (folder.startswith(('Historico/Datos/Preparados/', 'Historico/Datos/Versiones_modelos/'))
                      or '/dataset' in folder
                      or (folder.startswith('Datos/Preparados/V3/') and '/exportacion_' in folder))
        if not is_dataset:
            continue
        target = 'Historico/Proyecto/' + folder if folder.startswith('Historico/') else 'Exportaciones/Proyecto/' + folder
        candidates[folder] = dict(origen=folder, destino=target, archivos=len(files),
                                   bytes=sum(f['bytes'] for f in files))
    entries = []
    for row in rows:
        ref, h = row['ruta'], row['sha256']
        if row['disco'] == 'E':
            destination = external_relative(ref)
            action = 'ordenar_en_E' if destination != ref else 'conservar_en_E'
            reason = 'Conservar procedencia, clasificación y controles originales.'
        else:
            folder = next((p for p in candidates if ref.startswith(p + '/')), None)
            if folder:
                destination = candidates[folder]['destino'] + ref[len(folder):]
                action = 'ya_existe_en_E' if h in e_hash else 'copiar_a_E'
                reason = 'Exportación raster; metadatos y etiquetas permanecen en C.'
            else:
                matches = [r for r in e_hash.get(h, []) if not r['ruta'].startswith(('01_', '02_'))]
                destination = external_relative(matches[0]['ruta']) if matches else None
                action = 'conservar_en_C'
                reason = 'Fuente independiente, metadatos, evidencia mixta o material protegido.'
        entries.append(dict(origen_logico=ref, origen_fisico=str((external if row['disco']=='E' else ROOT) / ref),
                            disco=row['disco'], destino=destination, sha256=h, bytes=row['bytes'],
                            accion=action, motivo=reason, dependencias=[]))
    # Unique dataset bytes must retain an independent copy on C before removal.
    recovery = {}
    for row in entries:
        if row['disco'] != 'C' or row['accion'] == 'conservar_en_C':
            continue
        h = row['sha256']
        retained = [r for r in entries if r['disco']=='C' and r['sha256']==h and r['accion']=='conservar_en_C']
        if retained:
            recovery[h] = retained[0]['origen_logico']
        elif h not in recovery:
            recovery[h] = '.resguardo/Almacenamiento_20261108/' + h[:2] + '/' + h + Path(row['origen_logico']).suffix.lower()
    exceptions = [dict(origen_logico=p, accion='ausencia_conocida', sha256=None,
                       motivo='Retirada intencional confirmada por Vicente; no restaurar.') for p in KNOWN_ABSENCES]
    coverage = {}
    pointer = read(ROOT / 'Datos/Registros/Particiones/activa_v3.json')
    part = read(ROOT / pointer['path'])
    sample = read(ROOT / 'Datos/Preparados/V3/Calibracion_ocupacion_20261107/muestra_desarrollo.json')
    csv_path = external / 'Clasificacion_imagenes_20261106.csv'
    with csv_path.open(encoding='utf-8-sig', newline='') as f:
        classified = list(csv.DictReader(f))
    recorded_hashes = {r['sha256'] for r in classified}
    missing_csv = []
    for image in part['imagenes']:
        h = image['sha256']
        if h not in c_hash:
            raise ValueError('Fuente actual sin identidad verificada: ' + image['path'])
        if h not in recorded_hashes:
            missing_csv.append(dict(name=image['name'], sha256=h, coincidencias_E=[external_relative(r['ruta']) for r in e_hash.get(h, [])],
                                    fuentes_C=[r['ruta'] for r in c_hash[h]],
                                    estado='presente_en_E' if h in e_hash else 'conservada_en_C_y_exportacion_planificada'))
        for row in entries:
            if row['sha256']==h:
                row['dependencias'].append('particion_activa:' + image['name'])
    sample_rows = sample.get('images', sample.get('imagenes', []))
    if len(sample_rows) != 163:
        raise ValueError('La muestra debe conservar 163 registros.')
    for image in sample_rows:
        for field in ('source_path', 'serve_path'):
            path = ROOT / image[field]
            if not path.is_file():
                raise ValueError('Muestra sin imagen: ' + image[field])
            h = sha(path)
            if field == 'source_path' and h != image['sha256']:
                raise ValueError('Cambió la fuente de la muestra.')
            for row in entries:
                if row['sha256']==h:
                    row['dependencias'].append('muestra:' + field + ':' + image['name'])
    coverage.update(particion_registros=len(part['imagenes']), particion_sin_csv=missing_csv,
                    bloqueadas=sum(bool(r.get('preparation_exclusion')) for r in part['imagenes']),
                    muestra_registros=len(sample_rows), muestra_fuentes_y_serve_verificadas=True,
                    clasificacion_hashes_verificados=sum(sha(Path(r['origen']))==r['sha256'] and sha(Path(r['destino']))==r['sha256'] for r in classified))
    result = dict(schema_version=1, estado='inventariado', enlaces_recorridos=False,
                  carpetas=list(candidates.values()), archivos=entries, ausencias_conocidas=exceptions,
                  recuperacion_c=recovery, cobertura=coverage,
                  espacio_inicial={p:shutil.disk_usage(p)._asdict() for p in ('C:/', 'E:/')})
    write(REG / 'manifiesto_migracion.json', result)
    print(json.dumps(dict(archivos=len(entries), carpetas=len(candidates),
          bytes_candidatos=sum(r['bytes'] for r in candidates.values()),
          bytes_respaldo_unico=sum(next(r['bytes'] for r in entries if r['sha256']==h) for h,p in recovery.items() if p.startswith('.resguardo/')),
          cobertura=coverage), ensure_ascii=True), flush=True)


def checked(base, ref):
    """Every mutation must stay below its explicitly approved physical root."""
    from pathlib import PurePosixPath
    if not isinstance(ref, str) or '\\' in ref or ':' in ref or PurePosixPath(ref).is_absolute() or '..' in PurePosixPath(ref).parts:
        raise ValueError('Destino no seguro: ' + str(ref))
    base = base.resolve()
    target = base / ref
    if target == base or not target.resolve().is_relative_to(base):
        raise ValueError('Destino fuera de la raíz: ' + str(target))
    return target


def aliases_for(ref, history):
    result = {ref}
    for name in ('lider_express_20261016','visibilidad_limitada_20261019'):
        prefix='Datos/V3/'+name+'/'
        if ref.startswith(prefix):
            result.add('Datos/V2/'+name+'/'+ref[len(prefix):])
    if ref.startswith('Laboratorio/Experimentos/'):
        result.add(ref.removeprefix('Laboratorio/'))
    for source, target in history:
        if ref == target or ref.startswith(target + '/'):
            alias = source + ref[len(target):]
            result.add(alias)
            if alias.startswith('Laboratorio/Experimentos/'):
                result.add(alias.removeprefix('Laboratorio/'))
    return result


def build_catalog(external):
    manifest = read(REG / 'manifiesto_migracion.json')
    history = [(r['origen'], r['destino']) for r in read(ROOT / '.config-modelo/rutas_historicas.json')['rutas']]
    files, external_files, legacy = {}, {}, {}
    canonical = {}
    for row in manifest['archivos']:
        if row['destino'] and (row['disco']=='E' or row['accion']!='conservar_en_C'):
            canonical.setdefault(row['sha256'],row['destino'])
    active = read(ROOT / read(ROOT / 'Datos/Registros/Particiones/activa_v3.json')['path'])
    panel_hashes = {r['sha256'] for r in active['imagenes'] if r['split'] in ('train','val') and not r.get('preparation_exclusion') and not r['name'].startswith('R254')}
    for row in manifest['archivos']:
        ref, dest = row['origen_logico'], row['destino']
        if row['disco'] == 'E':
            external_files[dest] = dict(externa=dest, sha256=row['sha256'], bytes=row['bytes'])
            legacy[str(external / ref)] = dest
            legacy[str(external / ref).replace('\\', '/')] = dest
            continue
        dest = dest or canonical.get(row['sha256'])
        item = dict(sha256=row['sha256'], bytes=row['bytes'], externa=dest,
                    panel=row['sha256'] in panel_hashes and Path(ref).suffix.lower() in EXTS,
                    funcion=row['motivo'], dependencias=row['dependencias'])
        for alias in aliases_for(ref, history):
            if alias in files and files[alias]['sha256'] != item['sha256']:
                raise ValueError('Colisión de referencia: ' + alias)
            files[alias] = item
    value = dict(schema_version=1, version='almacenamiento_20261108', archivos=files,
                 externos=external_files, referencias_externas_anteriores=legacy,
                 carpetas=manifest['carpetas'], ausencias_conocidas=manifest['ausencias_conocidas'],
                 colecciones=dict(pruebas_ocupacion='Pruebas_ocupacion',
                                  derivados_ocupacion='Derivados/Ocupacion_20261106',
                                  clasificacion_original='Catalogo/Originales_20261106/Clasificacion_imagenes_20261106.csv'))
    write(REG / 'catalogo.json', value)
    write(ROOT / '.config-modelo/almacenamiento.local.json', {'data_root':str(external)})
    print('Catálogo: %d referencias y %d archivos externos originales.' % (len(files), len(external_files)), flush=True)


def verified_copy(source, target, expected, size):
    if target.is_file():
        if target.stat().st_size != size or sha(target) != expected:
            raise ValueError('Destino existente diferente: ' + str(target))
        return False
    if sha(source) != expected:
        raise ValueError('Cambió el origen: ' + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.migrando')
    if temporary.exists():
        raise ValueError('Copia temporal previa pendiente de revisar: ' + str(temporary))
    shutil.copy2(source, temporary)
    if temporary.stat().st_size != size or sha(temporary) != expected:
        raise ValueError('Copia no verificada: ' + str(temporary))
    temporary.replace(target)
    return True


def organize(external):
    manifest = read(REG / 'manifiesto_migracion.json')
    e_rows = [r for r in manifest['archivos'] if r['disco']=='E']
    receipt = read(REG / 'orden_E.json') if (REG / 'orden_E.json').is_file() else {'movimientos':[], 'enlaces_duros':[]}
    completed = {r['origen'] for r in receipt['movimientos']}
    # Preserve original control bytes in a separate evidence collection first.
    for row in e_rows:
        ref = row['origen_logico']
        if Path(ref).suffix.lower() in ('.json','.txt','.csv','.md'):
            verified_copy(external / ref, checked(external, 'Catalogo/Evidencia_previa_20261108/' + ref), row['sha256'], row['bytes'])
    moves = {}
    for row in e_rows:
        ref, dest = row['origen_logico'], row['destino']
        if ref == dest or ref.startswith(('01_', '02_')):
            continue
        if '/' not in ref:
            moves[ref] = dest
        else:
            old_top = ref.split('/')[0]
            suffix = ref[len(old_top):]
            moves[old_top] = dest[:-len(suffix)]
    for ref, dest in moves.items():
        if ref in completed:
            continue
        source, target = checked(external, ref), checked(external, dest)
        if source.is_junction() or source.is_symlink() or target.exists():
            raise ValueError('Movimiento no físico o destino ocupado: ' + ref)
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        if target.is_dir():
            junction(source, target, external)
        else:
            os.link(target, source)  # Frozen original file remains usable.
        receipt['movimientos'].append({'origen':ref,'destino':dest})
        write(REG / 'orden_E.json', receipt)
    # Verify all originals after the directory moves, before consolidating copies.
    for row in e_rows:
        target = checked(external, row['destino'])
        if sha(target) != row['sha256']:
            raise ValueError('Identidad externa cambió: ' + row['origen_logico'])
    csv_file = external / 'Catalogo/Originales_20261106/Clasificacion_imagenes_20261106.csv'
    with csv_file.open(encoding='utf-8-sig', newline='') as stream:
        classification = list(csv.DictReader(stream))
    done = {r['referencia'] for r in receipt['enlaces_duros']}
    operational = []
    for item in classification:
        old_source, old_copy = Path(item['origen']), Path(item['destino'])
        source_ref, copy_ref = old_source.relative_to(external).as_posix(), old_copy.relative_to(external).as_posix()
        source = checked(external, external_relative(source_ref))
        copy = checked(external, copy_ref)
        if copy_ref not in done:
            if sha(source)!=item['sha256'] or sha(copy)!=item['sha256']:
                raise ValueError('Copia clasificada distinta: ' + copy_ref)
            if not source.samefile(copy):
                temp = copy.with_name(copy.name + '.referencia')
                if temp.exists():
                    raise ValueError('Referencia temporal ya existe: ' + str(temp))
                os.link(source, temp)
                temp.replace(copy)
            if not source.samefile(copy):
                raise ValueError('Enlace duro no verificado.')
            receipt['enlaces_duros'].append(dict(referencia=copy_ref, fuente=external_relative(source_ref),sha256=item['sha256'],bytes=int(item['bytes'])))
            write(REG / 'orden_E.json', receipt)
        operational.append({**item, 'fuente_relativa': external_relative(source_ref), 'copia_clasificada_relativa':copy_ref, 'metodo_actual':'enlace_duro_verificado'})
    write(checked(external,'Catalogo/clasificacion_operativa_v1.json'), operational)
    print('E ordenado; %d referencias clasificadas consolidadas.' % len(receipt['enlaces_duros']),flush=True)


def junction(source, target, permitted_root):
    # Only create an absent directory alias. Never remove through an alias.
    if source.exists() or source.is_junction() or not source.absolute().is_relative_to(permitted_root.absolute()):
        raise ValueError('Origen de enlace no autorizado: ' + str(source))
    subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(source),str(target)], check=True, capture_output=True)


def copy_batches(external):
    manifest = read(REG / 'manifiesto_migracion.json')
    by_ref = {r['origen_logico']:r for r in manifest['archivos'] if r['disco']=='C'}
    recovery = manifest['recuperacion_c']
    e_by_hash = {}
    for r in manifest['archivos']:
        if r['disco']=='E' and not r['origen_logico'].startswith(('01_','02_')):
            e_by_hash.setdefault(r['sha256'], r['destino'])
    copied = []
    # Historical exports first, official run next, active preparation last.
    groups = sorted(manifest['carpetas'], key=lambda g: (0 if g['origen'].startswith('Historico/') else 1 if g['origen'].startswith('Laboratorio/') else 2, g['origen']))
    for group in groups:
        folder = group['origen']
        rows = [r for ref,r in by_ref.items() if ref.startswith(folder+'/')]
        for row in rows:
            ref, h = row['origen_logico'], row['sha256']
            source = checked(ROOT, ref)
            recover = checked(ROOT, recovery[h])
            if recovery[h].startswith('.resguardo/'):
                verified_copy(source, recover, h, row['bytes'])
            elif sha(recover) != h:
                raise ValueError('Fuente de recuperación no verificada: ' + str(recover))
            target = checked(external, row['destino'])
            if not target.exists() and h in e_by_hash:
                canonical = checked(external, e_by_hash[h])
                if sha(canonical) != h:
                    raise ValueError('Fuente externa para referencia distinta: ' + str(canonical))
                target.parent.mkdir(parents=True, exist_ok=True)
                os.link(canonical, target)
                if not target.samefile(canonical):
                    raise ValueError('Referencia externa no verificada.')
            else:
                verified_copy(source, target, h, row['bytes'])
            e_by_hash.setdefault(h, row['destino'])
            copied.append({'origen':ref,'destino':row['destino'],'sha256':h,'bytes':row['bytes'],'recuperacion_c':recovery[h]})
        write(REG / 'copias_verificadas.json', {'estado':'copiando','archivos':copied})
        print('Copiado y verificado: ' + folder, flush=True)
    write(REG / 'copias_verificadas.json', {'estado':'verificado','archivos':copied})


def activate(external):
    manifest = read(REG/'manifiesto_migracion.json')
    copies = read(REG/'copias_verificadas.json')
    if copies['estado'] != 'verificado':
        raise ValueError('Primero debe terminar la copia verificada.')
    receipt = read(REG/'activacion.json') if (REG/'activacion.json').is_file() else {'carpetas':[]}
    done = {r['origen'] for r in receipt['carpetas']}
    for group in manifest['carpetas']:
        ref = group['origen']
        if ref in done:
            continue
        source = checked(ROOT, ref)
        target = checked(external, group['destino'])
        stage_ref = ref + '.antes_externo'
        stage = checked(ROOT, stage_ref)
        if source.is_junction() or source.is_symlink() or stage.exists():
            raise ValueError('Origen no físico o transición pendiente: ' + ref)
        rows = [r for r in copies['archivos'] if r['origen'].startswith(ref+'/')]
        if len(rows) != group['archivos']:
            raise ValueError('Cobertura de lote incompleta.')
        for row in rows:
            if sha(checked(external,row['destino']))!=row['sha256']:
                raise ValueError('Destino externo modificado.')
        source.rename(stage)
        try:
            junction(source,target,ROOT)
        except Exception:
            stage.rename(source)
            raise
        receipt['carpetas'].append(dict(origen=ref,destino=group['destino'],reserva_temporal=stage_ref))
        write(REG/'activacion.json', receipt)
        print('Activado, copia C intacta: ' + ref,flush=True)


def retire(external):
    """Delete only manifested regular files after independent verification.

    There is deliberately no rmtree: directory aliases are never traversed.
    """
    checks = read(REG/'comprobaciones_antes_retiro.json')
    if checks.get('estado') != 'verificado':
        raise ValueError('Faltan comprobaciones de funcionamiento antes del retiro.')
    manifest, activation = read(REG/'manifiesto_migracion.json'), read(REG/'activacion.json')
    copies = read(REG/'copias_verificadas.json')['archivos']
    receipt = read(REG/'retiro.json') if (REG/'retiro.json').is_file() else {'archivos':[],'carpetas':[]}
    done = {r['origen'] for r in receipt['archivos']}
    verified_objects={}
    def unchanged(path,expected):
        stat=path.stat()
        identity=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)
        if identity not in verified_objects:
            verified_objects[identity]=sha(path)
        return verified_objects[identity]==expected
    for group in activation['carpetas']:
        ref = group['origen']
        stage = checked(ROOT,group['reserva_temporal'])
        if stage.is_junction() or stage.is_symlink():
            raise ValueError('Nunca retirar un alias.')
        if ref in receipt['carpetas']:
            continue
        rows = [r for r in copies if r['origen'].startswith(ref+'/')]
        remaining = {stage / r['origen'][len(ref)+1:] for r in rows if r['origen'] not in done}
        if set(physical_files(stage)) != remaining:
            raise ValueError('Contenido temporal inesperado: ' + str(stage))
        # Validate every identity and its recovery copy before removing this lot.
        for row in rows:
            if row['origen'] in done:
                continue
            source = stage / row['origen'][len(ref)+1:]
            destination = checked(external,row['destino'])
            backup = checked(ROOT,row['recuperacion_c'])
            if any(not unchanged(p,row['sha256']) for p in (source,destination,backup)):
                raise ValueError('No retirar: identidad o respaldo distinto.')
        for row in rows:
            if row['origen'] in done:
                continue
            source = stage / row['origen'][len(ref)+1:]
            source.unlink()
            receipt['archivos'].append(row)
        # Remove only empty, non-reparse directories, bottom-up.
        dirs = []
        for directory,names,files in os.walk(stage,followlinks=False):
            for name in names:
                p=Path(directory)/name
                if p.is_junction() or p.is_symlink():
                    raise ValueError('Alias inesperado en temporal.')
                dirs.append(p)
        for p in sorted(dirs,key=lambda p:len(p.parts),reverse=True):
            p.rmdir()
        stage.rmdir()
        receipt['carpetas'].append(ref)
        write(REG/'retiro.json',receipt)
        print('Retirado con respaldo C verificado: ' + ref,flush=True)
    receipt['bytes_logicos_retirados']=sum(r['bytes'] for r in receipt['archivos'])
    receipt['espacio_final']={p:shutil.disk_usage(p)._asdict() for p in ('C:/','E:/')}
    write(REG/'retiro.json',receipt)


def docker_overlay(external):
    manifest = read(REG / 'manifiesto_migracion.json')
    history = [(r['origen'],r['destino']) for r in read(ROOT/'.config-modelo/rutas_historicas.json')['rutas']]
    volumes = [dict(type='bind',source='${WALMART_DATA_ROOT:?Defina WALMART_DATA_ROOT}',target='/datasets',read_only=True,bind={'create_host_path':False})]
    seen = {'/datasets'}
    for group in manifest['carpetas']:
        for alias in sorted(aliases_for(group['origen'],history)):
            if alias.startswith('Laboratorio/Experimentos/'):
                continue
            target = '/app/' + alias
            if target in seen:
                continue
            seen.add(target)
            volumes.append(dict(type='bind',source='${WALMART_DATA_ROOT}/'+group['destino'],target=target,read_only=True,bind={'create_host_path':False}))
    # JSON is valid YAML and avoids quoting Windows drive letters manually.
    write(ROOT/'Infraestructura/Docker/compose.modelos.datos.yml',{'services':{'panel_modelos':{'environment':{'WALMART_DATA_ROOT':'/datasets'},'volumes':volumes}}})
    print('Montajes externos explícitos: %d' % len(volumes),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fase', choices=['inventario','catalogo','ordenar','copiar','docker','activar','retirar'])
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    {'inventario':inventory,'catalogo':build_catalog,'ordenar':organize,'copiar':copy_batches,'docker':docker_overlay,'activar':activate,'retirar':retire}[args.fase](args.root.resolve())
