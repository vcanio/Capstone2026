"""Refuerzos versionados por escenas, con procedencia y exclusiones verificables."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import uuid
import preparacion_v3 as p
import datos_modelos as datasets

POLICY = 'refuerzo_geometria_escenas_v1'
BASE = 'Datos/Preparados/V3/Refuerzos/revision_geometria_20261104'


def validate_partition(root, reference, value):
    plan_path = root / BASE / 'cierre/plan_particion.json'
    if (value.get('plan_path') != plan_path.relative_to(root).as_posix()
            or value.get('plan_sha256') != p.digest(plan_path)):
        raise ValueError('Cambió el plan de escenas del refuerzo.')
    plan = p.read(plan_path)
    base = p.partition(root, plan['base_partition_path'])
    if (value.get('id') != Path(reference).parent.name
            or plan['base_partition_sha256'] != p.digest(root / plan['base_partition_path'])
            or value.get('imagenes') != plan['imagenes']
            or plan.get('authorized_by') != 'Vicente'
            or not plan.get('authorization')):
        raise ValueError('La partición no corresponde al plan autorizado.')
    for ref, fingerprint in plan['evidence_sha256'].items():
        if p.digest(root / ref) != fingerprint:
            raise ValueError('Cambió la evidencia de procedencia: ' + ref)
    parent = p.read(root / plan['parent_manifest'])
    replay = p.read(root / BASE / 'repaso_propuesto.json')['fotos']
    incoming = p.read(root / BASE / 'manifest_ingreso_cvat.json')['fotos']
    old = {r['name']: r for r in base['imagenes']}
    additions = {r['nombre_cvat']: r for r in incoming}
    expected = {r['nombre'] for r in replay} | {r['name'] for r in parent['imagenes'] if r['split']=='val'} | set(additions)
    rows = value['imagenes']
    if len(rows) != len(expected) or {r['name'] for r in rows} != expected:
        raise ValueError('La cobertura debe ser 136 casos, R254 excluida, 69 repasos y 69 validaciones históricas.')
    names, hashes, scenes, families = set(), set(), {}, {}
    parent_train = {r['grupo_escena'] for r in parent['imagenes'] if r['split']=='train'}
    replay_names = {r['nombre'] for r in replay}
    parent_val_names = {r['name'] for r in parent['imagenes'] if r['split']=='val'}
    components = {g['id']:g for g in plan['components']}
    for r in rows:
        if r['name'] in names or r['sha256'] in hashes or r['split'] not in ('train','val') or r['origen'] not in ('real','sintetica'):
            raise ValueError('Duplicado o asignación inválida en el refuerzo.')
        names.add(r['name']); hashes.add(r['sha256'])
        path = p.v3_image_path(root,r['path'])
        if Path(r['path']).name != r['name']:
            raise ValueError('Nombre y ruta de imagen incompatibles.')
        for table,key in ((scenes,r['grupo_escena']),(families,r['familia'])):
            if table.setdefault(key,r['split']) != r['split']:
                raise ValueError('Una escena o familia cruza entrenamiento y validación.')
        component = components[r['grupo_escena']]
        if r['split'] != component['split']:
            raise ValueError('La imagen no conserva la asignación de su componente.')
        if r['split']=='val' and parent_train.intersection(component['historical_groups']):
            raise ValueError('Validación contaminada por entrenamiento del padre.')
        if r['name'] in old:
            source=old[r['name']]
            if source['grupo_escena'] not in component['members']:
                raise ValueError('Se rompió la relación con la escena histórica.')
            if r['name'] in replay_names and (r['split']!='train' or r.get('preparation_exclusion')):
                raise ValueError('El repaso debe conservarse íntegro en entrenamiento.')
            if r['name'] in parent_val_names and r['split']=='train' and not r.get('preparation_exclusion'):
                raise ValueError('No incorporar al repaso la validación histórica retirada.')
            for key in ('path','sha256','width','height','task_id','origen','familia'):
                if r[key]!=source[key]: raise ValueError('Cambió una fuente histórica: '+r['name'])
        else:
            source=additions[r['name']]
            if source['grupo'] not in component['members'] or r['familia'] != source['grupo']:
                raise ValueError('Se rompió un bloque de vistas o variantes relacionadas.')
            synthetic=source['id'] in p.read(root / BASE / 'decision_origen_ohiggins_20261104.json')['fotos']
            expected_source={'path':source['archivo'].replace('\\', '/'),'sha256':source['sha256'],
                             'task_id':source['tarea_cvat'],'width':source['dimensiones_orientadas'][0],
                             'height':source['dimensiones_orientadas'][1],'origen':'sintetica' if synthetic else 'real'}
            if any(r[k]!=v for k,v in expected_source.items()):
                raise ValueError('Cambió la procedencia de un caso de refuerzo.')
            if source['id']=='R254' and not r.get('preparation_exclusion'):
                raise ValueError('R254 debe permanecer excluida, nunca como negativo.')
    summary = summarize(rows)
    if value.get('resumen') != summary:
        raise ValueError('El resumen del refuerzo no coincide.')
    return value


def summarize(rows):
    return {s:{'imagenes':len(items),'reales':sum(i['origen']=='real' for i in items),
               'sinteticas':sum(i['origen']=='sintetica' for i in items),
               'grupos':len({i['grupo_escena'] for i in items})}
            for s in ('train','val') if (items:=[r for r in rows if r['split']==s])}


def source_snapshot(root, part, client=None):
    client=client or datasets.CvatReader()
    snapshot={'labels':client.listing('/labels?project_id=11'),'tasks':[]}
    mapping={27:34,28:35,31:39,40:40,41:41,42:42,43:43,44:44}
    parent=p.read(root / p.read(root / part['plan_path'])['parent_manifest'])
    aliases={r['name']:r['cvat_name'] for r in parent['imagenes']}
    for tid in sorted({r['task_id'] for r in part['imagenes']}):
        actual=mapping[tid]
        task=client.request(f'/tasks/{actual}')
        meta=client.request(f'/tasks/{actual}/data/meta')
        if task['project_id']!=11: raise ValueError('Tarea fuera del proyecto autorizado.')
        frames={f['name']:idx for idx,f in enumerate(meta['frames'])}
        selected=[r for r in part['imagenes'] if r['task_id']==tid]
        names={r['name']:aliases.get(r['name'],r['name']) for r in selected}
        for r in selected:
            f=meta['frames'][frames[names[r['name']]]]
            if (f['width'],f['height'])!=(r['width'],r['height']):
                raise ValueError('Cambió la orientación de '+r['name'])
        snapshot['tasks'].append({'task':task,'partition_task_id':tid,'meta':meta,
            'annotations':client.request(f'/tasks/{actual}/annotations'),
            'jobs':datasets.annotation_jobs(client,actual),
            'frames_by_name':{n:frames[a] for n,a in names.items()}})
    return snapshot


def save_preparation(root, reference, part, snapshot):
    for r in part['imagenes']:
        if p.digest(p.v3_image_path(root,r['path']))!=r['sha256']:
            raise ValueError('Imagen modificada: '+r['name'])
    result=p.analyze(part,snapshot)
    stamp=datetime.now(timezone.utc)
    version='v3_'+stamp.strftime('%Y%m%d_%H%M%S_')+uuid.uuid4().hex[:8]
    result.update(id=version,created_at=stamp.isoformat(),partition_id=part['id'],partition_path=reference,
                  partition_sha256=p.digest(root/reference),summary=part['resumen'],partition_note=part['evaluation_note'])
    folder=root/p.OUTPUT/version; folder.mkdir()
    for name,value in [('snapshot_cvat.json',snapshot),('particion.json',part),('informe.json',result)]:
        p.write(folder/name,value)
    return result


def prepare_partition(root, reference, part, client=None):
    return save_preparation(root,reference,part,source_snapshot(root,part,client))


def choose(root, receipt, images, value):
    part=p.partition(root,receipt['partition_path'])
    if part.get('schema_version') == 6:
        from refuerzo_ampliado_v3 import choose as choose_ampliado
        return choose_ampliado(root, receipt, images, value)
    if part.get('schema_version') == 5:
        from refuerzo_cierre_v3 import choose as choose_cierre
        return choose_cierre(root, receipt, images, value)
    plan=p.read(root/part['plan_path'])
    if (value.get('plan_sha256')!=part['plan_sha256'] or value.get('required_initial_model')!=plan['initial_model']
            or value.get('required_initial_model_sha256')!=plan['initial_model_sha256']):
        raise ValueError('La selección no conserva el plan y el padre vigente.')
    selected=[i['name'] for i in images if i['split']=='train']
    if set(selected)!=set(plan['selected_train']) or {i['name'] for i in images if i['split']=='val'}!=set(plan['selected_val']):
        raise ValueError('La exportación no contiene la selección de escenas acordada.')
    return selected,[]
