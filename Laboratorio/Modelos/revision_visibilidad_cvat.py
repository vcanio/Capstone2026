"""Leer decisiones humanas de CVAT sin modificar el proyecto ni entrenar."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

from datos_modelos import CvatReader

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'Datos/Preparados/V3/Visibilidad_foto_20261102'
PROPOSALS = DATA / 'propuestas_tarea33.json'
APPROVAL = DATA / 'confirmacion_propuestas_tarea33.json'
SECOND_PROPOSALS = DATA / 'propuestas_revision_visual.json'
SECOND_APPROVAL = DATA / 'confirmacion_propuestas_revision_visual.json'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def collect(reader, inventory, receipt):
    if receipt['status'] != 'lista_para_revision':
        raise ValueError('El proyecto CVAT aún no está listo para revisión.')
    if receipt['inventory_sha256'] != digest(DATA / 'inventario_pendiente.json'):
        raise ValueError('El inventario cambió desde la creación de CVAT.')
    labels = reader.listing(f"/labels?project_id={receipt['project_id']}")
    matching = [label for label in labels if label['name'] == 'Evaluabilidad' and label['type'] == 'tag']
    if len(matching) != 1:
        raise ValueError('La etiqueta Evaluabilidad no coincide con el proyecto.')
    label = matching[0]
    attr_names = {item['id']: item['name'] for item in label['attributes']}
    batches = {}
    for batch_id, proposal_path, approval_path in (('tarea33', PROPOSALS, APPROVAL), ('revision_visual', SECOND_PROPOSALS, SECOND_APPROVAL)):
        proposal = read(proposal_path) if proposal_path.exists() else None
        if proposal and (proposal.get('project_id') != receipt['project_id'] or proposal.get('inventory_sha256') != receipt['inventory_sha256']):
            raise ValueError('Las propuestas no coinciden con el proyecto o inventario.')
        targets = {(r['task_id'], r['frame']) for r in proposal.get('targets', [])} if proposal else set()
        if any(targets & batch['targets'] for batch in batches.values()):
            raise ValueError('Un fotograma pertenece a dos lotes de propuestas.')
        batches[batch_id] = {'proposal': proposal, 'approval_path': approval_path, 'targets': targets, 'current': []}
    rows = []
    issues = []
    for task in receipt['tasks']:
        if task['status'] != 'verificada' or task['split'] not in ('train', 'val'):
            raise ValueError('Tarea de revisión no verificada.')
        meta = reader.request(f"/tasks/{task['task_id']}/data/meta")
        actual_frames = {frame['name']: i for i, frame in enumerate(meta['frames'])}
        if actual_frames != task['frames'] or meta.get('deleted_frames'):
            raise ValueError('Los fotogramas de revisión cambiaron; revisar antes de importar.')
        annotations = reader.request(f"/tasks/{task['task_id']}/annotations")
        if annotations['shapes'] or annotations['tracks']:
            raise ValueError('La revisión contiene geometrías inesperadas.')
        tags_by_frame = {}
        for tag in annotations['tags']:
            if tag['label_id'] != label['id']:
                raise ValueError('Etiqueta de revisión desconocida.')
            tags_by_frame.setdefault(tag['frame'], []).append(tag)
        for row in inventory['images']:
            if row['split'] != task['split']:
                continue
            frame = actual_frames[row['cvat_name']]
            tags = tags_by_frame.get(frame, [])
            for batch in batches.values():
              if (task['task_id'], frame) in batch['targets']:
                batch['current'].append({'task_id': task['task_id'], 'frame': frame,
                    'tags': sorted([{'id': tag.get('id'), 'label_id': tag['label_id'],
                                     'attributes': sorted(tag.get('attributes', []), key=lambda a: a['spec_id'])}
                                    for tag in tags], key=lambda t: t.get('id') or 0)})
            decision, reason = 'pendiente', None
            if len(tags) > 1:
                issues.append({'name': row['name'], 'reason': 'multiples_decisiones'})
            elif tags:
                attrs = {attr_names.get(a['spec_id']): a['value'] for a in tags[0]['attributes']}
                decision = attrs.get('decision', 'pendiente')
                reason = attrs.get('motivo', 'sin_definir')
                if decision not in ('apta', 'no_apta', 'pendiente'):
                    issues.append({'name': row['name'], 'reason': 'decision_invalida'})
                    decision = 'pendiente'
                if decision == 'no_apta' and reason in (None, 'sin_definir'):
                    issues.append({'name': row['name'], 'reason': 'motivo_pendiente'})
                    decision = 'pendiente'
                if decision != 'no_apta' and reason not in (None, 'sin_definir'):
                    issues.append({'name': row['name'], 'reason': 'motivo_incompatible'})
                    decision = 'pendiente'
            rows.append({**row, 'etiqueta': decision, 'motivo': reason,
                         'revision_task_id': task['task_id'], 'revision_frame': frame})
    if len(rows) != 405 or len({row['name'] for row in rows}) != 405:
        raise ValueError('La revisión no cubre exactamente las 405 fotos de desarrollo.')
    batch_summary = {}
    for batch_id, batch in batches.items():
      proposals, proposed, current_proposals = batch['proposal'], batch['targets'], batch['current']
      proposal_hash, approved = None, False
      if proposals:
        if len(current_proposals) != len(proposed):
            raise ValueError('Los fotogramas de las propuestas no coinciden con el inventario.')
        canonical = json.dumps(sorted(current_proposals, key=lambda x: (x['task_id'], x['frame'])),
                               ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        proposal_hash = hashlib.sha256(canonical).hexdigest()
        approval = read(batch['approval_path']) if batch['approval_path'].exists() else {}
        approved = proposals.get('status') == 'verificadas' and approval.get('proposal_hash') == proposal_hash
        for row in rows:
            if (row['revision_task_id'], row['revision_frame']) in proposed:
                row['propuesta'] = {'decision': row['etiqueta'], 'motivo': row['motivo'], 'confirmada': approved, 'lote': batch_id}
                if not approved:
                    row['etiqueta'] = 'pendiente'
      batch_summary[batch_id] = {'count': len(proposed), 'confirmed': approved, 'hash': proposal_hash}
    counts = Counter((row['split'], row['origen'], row['etiqueta']) for row in rows)
    return {'project_id': receipt['project_id'], 'inventory_sha256': receipt['inventory_sha256'],
            'test_included': False, 'images': rows, 'issues': issues,
            'proposal_count': batch_summary['tarea33']['count'], 'proposals_confirmed': batch_summary['tarea33']['confirmed'], 'proposal_hash': batch_summary['tarea33']['hash'], 'proposal_batches': batch_summary,
            'counts': [{'split': k[0], 'origen': k[1], 'etiqueta': k[2], 'total': n}
                       for k, n in sorted(counts.items())]}


def confirm_proposals(reader, inventory, receipt, reviewed, batch_id='tarea33'):
    if reviewed is not True:
        raise ValueError('Confirma que revisaste las propuestas antes de aceptarlas.')
    if batch_id not in ('tarea33', 'revision_visual'):
        raise ValueError('Lote de propuestas desconocido.')
    proposal_path, approval_path = (PROPOSALS, APPROVAL) if batch_id == 'tarea33' else (SECOND_PROPOSALS, SECOND_APPROVAL)
    proposals = read(proposal_path) if proposal_path.exists() else None
    if not proposals or proposals.get('status') != 'verificadas':
        raise ValueError('Las propuestas aún no están verificadas.')
    state = collect(reader, inventory, receipt)
    batch = state['proposal_batches'][batch_id]
    if state['issues'] or not batch['count'] or not batch['hash']:
        raise ValueError('Corrige las incidencias antes de confirmar las propuestas.')
    approval = {'project_id': receipt['project_id'], 'proposal_hash': batch['hash'],
                'count': batch['count'], 'reviewed_by': 'Vicente',
                'confirmed_at': datetime.now(timezone.utc).isoformat()}
    temporary = approval_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(approval, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(approval_path)
    return approval


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guardar', type=Path, help='Guardar una copia nueva bajo Datos/Preparados/V3.')
    args = parser.parse_args()
    result = collect(CvatReader(), read(DATA / 'inventario_pendiente.json'), read(DATA / 'cvat_revision.json'))
    if args.guardar:
        target = args.guardar.resolve()
        if not target.is_relative_to(ROOT / 'Datos/Preparados/V3'):
            raise ValueError('La copia debe guardarse bajo Datos/Preparados/V3.')
        with target.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps({'counts': result['counts'], 'issues': result['issues']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
