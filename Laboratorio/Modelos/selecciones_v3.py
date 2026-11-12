"""Selecciones reproducibles de entrenamiento; heredan revisión y partición V3."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import re

import preparacion_v3 as preparation
from archivo_historico import within

DIRECTORY = 'Datos/Preparados/V3/Selecciones'
POLICY = 'originales_una_vacia_por_familia_v1'
HARD_POLICY = 'originales_una_vacia_mas_refuerzo_v1'
FINE_POLICY = 'afinado_dirigido_con_repaso_v1'
CLEAN_POLICY = 'segmentacion_sin_obstruccion_v1'
NO_TAPADAS_POLICY = 'segmentacion_sin_tarea33_ni_whatsapp_v2'
from refuerzo_geometria_v3 import POLICY as GEOMETRY_POLICY


def choose_no_tapadas(root, receipt, images, value):
    part = preparation.partition(root, partition_path(root, receipt))
    rows = {row['name']: row for row in part['imagenes']}
    evidence = root / 'Datos/Preparados/V3/Visibilidad_foto_20261102/decision_vicente_segundo_lote_20261102.json'
    if preparation.digest(evidence) != value.get('whatsapp_receipt_sha256'):
        raise ValueError('Cambió la decisión sobre las cinco fotos WhatsApp.')
    decision = preparation.read(evidence)
    whatsapp = set(decision.get('whatsapp_excluidas', []))
    if decision.get('status') != 'verificada' or len(whatsapp) != 5:
        raise ValueError('Falta la decisión verificada sobre las cinco fotos WhatsApp.')
    if any(i['name'] not in rows for i in images):
        raise ValueError('La exportación contiene imágenes fuera de la partición.')
    def keep(i):
        return rows[i['name']]['task_id'] != 24 and i['name'] not in whatsapp
    selected = [i['name'] for i in images if i['split'] == 'train' and keep(i)]
    excluded = [i['name'] for i in images if i['split'] == 'train' and not keep(i)]
    excluded_val = [i['name'] for i in images if i['split'] == 'val' and not keep(i)]
    return selected, excluded, excluded_val


def create_no_tapadas(root, source, receipt, images):
    """Completar el plan autorizado solo después de una exportación revisada."""
    draft = root / DIRECTORY / 'segmentacion_v3_sin_tarea33_20261102' / 'revision_pendiente.json'
    plan = preparation.read(draft)
    report = root / preparation.OUTPUT / receipt['source_version'] / 'informe.json'
    if (receipt.get('reviewed') is not True or receipt.get('reviewed_visible_regions') is not True
            or plan.get('source_report') != report.relative_to(root).as_posix()
            or plan.get('source_report_sha256') != preparation.digest(report)):
        raise ValueError('La revisión exportada no coincide con el plan de segmentación.')
    identifier = 'sin_tarea33_' + Path(source).name.replace('exportacion_', '')
    evidence = root / 'Datos/Preparados/V3/Visibilidad_foto_20261102/decision_vicente_segundo_lote_20261102.json'
    model = 'Modelos/preentrenados/yolo26n-seg.pt'
    value = {'id': identifier, 'policy': NO_TAPADAS_POLICY, 'approved': True,
             'approved_by': receipt['author'], 'authorization': 'Vicente solicitó excluir toda la tarea 33, las fotos desactivadas y las cinco WhatsApp, y preparar el entrenamiento.',
             'created_at': datetime.now(timezone.utc).isoformat(), 'source': source,
             'source_manifest_sha256': preparation.digest(root / source / 'manifest.json'),
             'partition_sha256': preparation.digest(root / partition_path(root, receipt)),
             'whatsapp_receipt_sha256': preparation.digest(evidence),
             'required_initial_model': model, 'required_initial_model_sha256': preparation.digest(root / model),
             'label': 'Sin tarea 33 ni cinco WhatsApp', 'recommended': True,
             'trial_name': 'v3_segmentacion_sin_tapadas',
             'purpose': 'Segmentación de niveles desde YOLO26n-seg general; excluir tarea 33 y cinco WhatsApp de desarrollo.',
             'training_defaults': {'model': model, 'epochs': 40, 'patience': 10, 'lr': .0001, 'batch': 2, 'imgsz': 640, 'seed': 42}}
    selected, excluded, excluded_val = choose_no_tapadas(root, receipt, images, value)
    result = [i for i in images if (i['split'] == 'val' and i['name'] not in set(excluded_val)) or i['name'] in set(selected)]
    counts = dict(Counter('train' if i['split'] == 'train' else 'val_' + i['origen'] for i in result))
    if counts != plan['proposed_counts']:
        raise ValueError('Los recuentos no coinciden con el plan revisable.')
    value.update(selected_train=selected, excluded_train=excluded, excluded_val=excluded_val, development_counts=counts)
    folder = root / DIRECTORY / identifier
    folder.mkdir(parents=True, exist_ok=False)
    preparation.write(folder / 'seleccion.json', value)
    apply(root, source, images, identifier)
    return identifier


def choose_without_obstructions(root, images, value):
    """Excluir solo las fotos de train autorizadas, sin cambiar validación."""
    base = root / 'Datos/Preparados/V3/Visibilidad_foto_20261102'
    obstacle_path = base / 'propuesta_seleccion_segmentacion_sin_obstruccion.json'
    review_path = base / 'decision_vicente_segundo_lote_20261102.json'
    if (preparation.digest(obstacle_path) != value.get('obstacle_manifest_sha256') or
            preparation.digest(review_path) != value.get('whatsapp_receipt_sha256')):
        raise ValueError('Cambió la evidencia de las exclusiones de segmentación.')
    obstacle = preparation.read(obstacle_path)
    review = preparation.read(review_path)
    blocked = [x for x in obstacle['selection'] if x['split'] == 'train']
    whatsapp = review.get('whatsapp_excluidas', [])
    if (obstacle.get('schema') != 'propuesta_exclusion_segmentacion_v1' or len(blocked) != 41
            or review.get('status') != 'verificada' or len(whatsapp) != 5
            or any('whatsapp image' not in name.lower() for name in whatsapp)):
        raise ValueError('La evidencia de fotos excluidas no coincide con la revisión.')
    train = [row for row in images if row['split'] == 'train']
    by_name = {row['name']: row for row in train}
    excluded = {x['name'] for x in blocked} | set(whatsapp)
    if (len(excluded) != 46 or not excluded <= set(by_name)
            or any(by_name[x['name']]['sha256'] != x['sha256'] for x in blocked)):
        raise ValueError('Las exclusiones no coinciden con el entrenamiento revisado.')
    return ([row['name'] for row in train if row['name'] not in excluded],
            [row['name'] for row in train if row['name'] in excluded])


def choose_fine(images, base_names, target_names, replay_size=64):
    """Reforzar casos nuevos y conservar cobertura de escenas sin usar predicciones."""
    train = {r['name']: r for r in images if r['split'] == 'train'}
    targets = set(target_names)
    if len(targets) != len(target_names) or not targets or not targets <= set(train):
        raise ValueError('Los casos de afinado deben estar revisados y asignados a train.')
    candidates = {n: train[n] for n in base_names if n in train and n not in targets}
    groups = sorted({r['grupo_escena'] for r in candidates.values()})
    chosen = set()
    # Cada variante de superior vacío conserva su original como repaso.
    for name in sorted(targets):
        if name.endswith('_D_superior_vacio.png'):
            family = train[name]['familia']
            matches = [n for n, r in candidates.items() if r['familia'] == family and r['origen'] == 'real']
            if len(matches) != 1:
                raise ValueError('Falta el original de una variante de superior vacío.')
            chosen.add(matches[0])
    for group in groups:
        if any(candidates[n]['grupo_escena'] == group for n in chosen):
            continue
        real = sorted(n for n, r in candidates.items() if r['grupo_escena'] == group and r['origen'] == 'real')
        if not real:
            raise ValueError('Falta un original de repaso para la escena ' + group)
        chosen.add(real[len(real) // 2])
    if len(chosen) > replay_size:
        raise ValueError('El tamaño de repaso no cubre los originales emparejados y las escenas.')
    # Añadir vacíos y después originales por turnos entre escenas.
    for group in groups:
        empty = sorted(n for n, r in candidates.items() if r['grupo_escena'] == group and n.endswith('_A_vacios.png') and n not in chosen)
        if empty and len(chosen) < replay_size:
            chosen.add(empty[0])
    while len(chosen) < replay_size:
        previous = len(chosen)
        for group in groups:
            available = sorted((n for n, r in candidates.items() if r['grupo_escena'] == group and n not in chosen),
                               key=lambda n: (candidates[n]['origen'] != 'real', n))
            if available and len(chosen) < replay_size:
                chosen.add(available[0])
        if len(chosen) == previous:
            raise ValueError('No hay suficientes imágenes de repaso.')
    keep = targets | chosen
    return [r['name'] for r in images if r['split'] == 'train' and r['name'] in keep], sorted(chosen)


def fine_plan(root, value, images):
    relative = value.get('fine_plan')
    if not isinstance(relative, str) or not re.fullmatch(r'Datos/Preparados/V3/Refuerzos/[A-Za-z0-9_-]+/plan\.json', relative):
        raise ValueError('Plan de afinado inválido.')
    path = root / relative
    if preparation.digest(path) != value.get('fine_plan_sha256'):
        raise ValueError('El plan de afinado cambió.')
    plan = preparation.read(path)
    base_path = path_for(root, plan['base_selection'])
    if preparation.digest(base_path) != plan['base_selection_sha256']:
        raise ValueError('Cambió la selección histórica usada como repaso.')
    base = preparation.read(base_path)
    selected, replay = choose_fine(images, base['selected_train'], plan['target_images'], plan['replay_size'])
    if (plan.get('approved') is not True or replay != plan['replay_images']
            or selected != plan['selected_train'] or value.get('required_initial_model') != plan['initial_model']
            or value.get('required_initial_model_sha256') != plan['initial_model_sha256']
            or value.get('source') != plan['source_export']
            or value.get('target_images') != plan['target_images']):
        raise ValueError('La selección no coincide con su plan de afinado autorizado.')
    return selected, [i['name'] for i in images if i['split'] == 'train' and i['name'] not in set(selected)]


def partition_path(root, receipt):
    return preparation.partition_reference(root, receipt.get('partition_path', preparation.PARTITION))


def choose_with_refuerzo(root, receipt, images, policy, hard_examples):
    selected, excluded = choose(images)
    if policy == POLICY:
        if hard_examples:
            raise ValueError('La selección ordinaria no admite excepciones ocultas.')
        return selected, excluded
    if policy != HARD_POLICY:
        raise ValueError('Política de selección desconocida.')
    part = preparation.partition(root, partition_path(root, receipt))
    expected = part.get('hard_examples', [])
    if not expected or hard_examples != expected:
        raise ValueError('El refuerzo debe coincidir con los casos autorizados de la partición.')
    names = {i['name'] for i in images if i['split'] == 'train'}
    if not set(expected) <= names:
        raise ValueError('Faltan casos de refuerzo revisados en entrenamiento.')
    keep = set(selected) | set(expected)
    train = [i['name'] for i in images if i['split'] == 'train']
    return [n for n in train if n in keep], [n for n in train if n not in keep]


def choose(images):
    """Todos los reales de train y una A_vacios revisada por familia sintética."""
    train = [i for i in images if i['split'] == 'train']
    real_families = {i['familia'] for i in train if i['origen'] == 'real'}
    families = {i['familia'] for i in train if i['origen'] == 'sintetica'}
    empty = {}
    for family in sorted(families):
        candidates = [i for i in train if i['familia'] == family
                      and i['origen'] == 'sintetica' and i['name'] == family + '_A_vacios.png']
        if family not in real_families or len(candidates) != 1:
            raise ValueError('Falta un original o una variante vacía única y revisada: ' + family)
        empty[family] = candidates[0]['name']
    selected = [i['name'] for i in train if i['origen'] == 'real' or i['name'] == empty.get(i['familia'])]
    if not selected or len(selected) != len(set(selected)):
        raise ValueError('La selección de entrenamiento está vacía o contiene duplicados.')
    return selected, [i['name'] for i in train if i['name'] not in set(selected)]


def path_for(root, identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier):
        raise ValueError('Identificador de selección V3 inválido.')
    path = root / DIRECTORY / identifier / 'seleccion.json'
    if not within(root, path, root / DIRECTORY) or not path.is_file():
        raise ValueError('La selección V3 ya no está disponible.')
    return path


def apply(root, source, images, identifier, expected_sha256=None):
    if not identifier:
        if expected_sha256:
            raise ValueError('Falta la selección que corresponde al hash indicado.')
        return images, None
    path = path_for(root, identifier)
    value = preparation.read(path)
    if expected_sha256 and preparation.digest(path) != expected_sha256:
        raise ValueError('La selección cambió desde la configuración del ensayo.')
    source_manifest = root / source / 'manifest.json'
    receipt = preparation.read(source_manifest)
    if (value.get('id') != identifier or value.get('policy') not in (POLICY, HARD_POLICY, FINE_POLICY, CLEAN_POLICY, NO_TAPADAS_POLICY, GEOMETRY_POLICY)
            or value.get('approved') is not True or not isinstance(value.get('approved_by'), str)
            or len(value['approved_by'].strip()) < 2
            or value.get('source') != source
            or value.get('source_manifest_sha256') != preparation.digest(source_manifest)
            or value.get('partition_sha256') != preparation.digest(root / partition_path(root, receipt))):
        raise ValueError('La selección no corresponde a la exportación revisada y su partición.')
    from refuerzo_geometria_v3 import choose as choose_geometry
    selected, excluded = (choose_geometry(root, receipt, images, value) if value['policy'] == GEOMETRY_POLICY else
                          fine_plan(root, value, images) if value['policy'] == FINE_POLICY else
                          choose_no_tapadas(root, receipt, images, value)[:2] if value['policy'] == NO_TAPADAS_POLICY else
                          choose_without_obstructions(root, images, value) if value['policy'] == CLEAN_POLICY else
                          choose_with_refuerzo(root, receipt, images, value['policy'], value.get('hard_examples', [])))
    if value.get('selected_train') != selected or value.get('excluded_train') != excluded:
        raise ValueError('La selección no coincide con su política y evidencias registradas.')
    excluded_val = choose_no_tapadas(root, receipt, images, value)[2] if value['policy'] == NO_TAPADAS_POLICY else []
    if value['policy'] == NO_TAPADAS_POLICY and value.get('excluded_val') != excluded_val:
        raise ValueError('Las exclusiones de validación no coinciden con la decisión.')
    result = [i for i in images if (i['split'] == 'val' and i['name'] not in set(excluded_val)) or i['name'] in set(selected)]
    counts = dict(Counter('train' if i['split'] == 'train' else 'val_' + i['origen'] for i in result))
    if counts != value.get('development_counts'):
        raise ValueError('Los recuentos de la selección no coinciden con desarrollo.')
    return result, {**value, 'sha256': preparation.digest(path), 'path': path.relative_to(root).as_posix()}


def create(root, source, receipt, images, *, identifier, author, authorization, hard_examples=None):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', identifier) or len(author.strip()) < 2 or not authorization.strip():
        raise ValueError('La selección requiere identificación, autor y autorización explícita.')
    policy = HARD_POLICY if hard_examples else POLICY
    selected, excluded = choose_with_refuerzo(root, receipt, images, policy, hard_examples or [])
    result = [i for i in images if i['split'] == 'val' or i['name'] in set(selected)]
    value = {'id': identifier, 'policy': policy, 'approved': True, 'approved_by': author,
             'authorization': authorization, 'created_at': datetime.now(timezone.utc).isoformat(),
             'label_review': 'heredada de la exportación revisada; sin cambiar polígonos',
             'source': source, 'source_manifest_sha256': preparation.digest(root / source / 'manifest.json'),
             'source_review_author': receipt['author'], 'partition_sha256': preparation.digest(root / partition_path(root, receipt)),
             'selected_train': selected, 'excluded_train': excluded,
             'development_counts': dict(Counter('train' if i['split'] == 'train' else 'val_' + i['origen'] for i in result)),
             'label': 'Originales + una variante vacía por familia',
             'trial_name': 'v3_niveles_una_vacia',
             'purpose': 'Comparar originales + una variante vacía por familia frente a la base V3, con el mismo modelo, resolución y validación. Confianza operativa mínima 0,60. Sin módulo ni test.'}
    if hard_examples:
        value.update(hard_examples=hard_examples, label='Originales + una vacía + casos conflictivos',
                     recommended=True,
                     trial_name='v3_niveles_refuerzo_papeles',
                     purpose='Aprender los casos conflictivos, incluidos papeles, con grupos completos trasladados a entrenamiento. Nueva validación: no comparar directamente con métricas históricas. Inicio desde YOLO26n-seg preentrenado. Test reservado; solo clase Nivel.')
    folder = root / DIRECTORY / identifier
    folder.mkdir(parents=True, exist_ok=False)
    preparation.write(folder / 'seleccion.json', value)
    for name, rows in [('train_seleccion.txt', selected), ('train_apartadas.txt', excluded)]:
        (folder / name).write_text('\n'.join(rows) + '\n', encoding='utf-8')
    apply(root, source, images, identifier)
    return value


def catalog(root):
    from visibilidad_modelos import current
    closed = set((current(root) or {}).get('closed_selection_ids', []))
    rows = []
    for path in (root / DIRECTORY).glob('*/seleccion.json'):
        try:
            value = preparation.read(path)
            if value.get('id') not in closed and value.get('approved') is True and value.get('policy') in (POLICY, HARD_POLICY, FINE_POLICY, CLEAN_POLICY, NO_TAPADAS_POLICY, GEOMETRY_POLICY):
                rows.append({**{key: value[key] for key in ('id', 'source', 'label', 'development_counts', 'trial_name', 'purpose')},
                             'recommended': value.get('recommended', False), 'created_at': value.get('created_at', ''),
                             'excluded_train_count': len(value.get('excluded_train', [])),
                             'excluded_val_count': len(value.get('excluded_val', [])),
                             'training_defaults': value.get('training_defaults', {}),
                             'required_initial_model': value.get('required_initial_model')})
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return sorted(rows, key=lambda r: (r['recommended'], r['created_at'], r['id']), reverse=True)


def module_pilot(root):
    try:
        value = preparation.read(root / 'Datos/Preparados/V3/Pilotos/modulos_20261025/piloto.json')
        if (value.get('training_supported') is False and set(value['tasks']) == {'train', 'val'}
                and all(t.get('annotations_verified') for t in value['tasks'].values())):
            if (root / preparation.ACTIVE_PARTITION).is_file():
                value['partition_note'] = 'Las tareas del piloto conservan su reparto histórico 8/4; no representan la validación del nuevo ensayo. Los módulos siguen pendientes de revisión y fuera del entrenamiento.'
            return value
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None
