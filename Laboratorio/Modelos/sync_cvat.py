"""Seguimiento persistente de CVAT en lectura; las copias son inmutables."""
import copy
import hashlib
import json
import threading
import time

import datos_modelos as datasets

INTERVAL = 10


def source_key(jobs):
    if (not isinstance(jobs, list) or not 1 <= len(jobs) <= 20 or
            any(type(job) is not int or job < 1 for job in jobs) or len(set(jobs)) != len(jobs)):
        raise ValueError('Selecciona entre 1 y 20 trabajos distintos de CVAT.')
    return ','.join(map(str, sorted(jobs)))


class CvatSync:
    def __init__(self, lock, invalidate, *, reader=None):
        self.lock, self.invalidate = lock, invalidate
        self.state_lock = threading.RLock()
        self.reader = reader or datasets.CvatReader
        self.path = datasets.ROOT / '.config-modelo/sincronizacion_cvat.json'
        self.sources = {}
        self.due = {}
        self.failures = {}
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.thread = None

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        datasets.write(self.path, {'schema_version': 1, 'sources': self.sources})

    def initialize(self):
        with self.state_lock:
            if self.path.exists():
                self.sources = datasets.read(self.path)['sources']
            else:
                self.sources = {}
                # Una sola partición por lote: la de su copia activa más reciente.
                metadata_paths = sorted(datasets.VERSIONS.glob('*/version.json'),
                                        key=lambda p: datasets.read(p).get('created_at', ''), reverse=True)
                seen = set()
                for metadata in metadata_paths:
                    value = datasets.read(metadata)
                    jobs = [source['job_id'] for source in value['sources']]
                    key = source_key(jobs)
                    if key in seen:
                        continue
                    seen.add(key)
                    if (metadata.parent / 'archivo.json').exists():
                        continue
                    partition = datasets.read(metadata.parent / 'particion.json')
                    self.sources[key] = {'jobs': sorted(jobs), 'validation': partition['validation_ids'],
                                         'enabled': True, 'version_id': value['id'], 'state': 'waiting'}
                active = datasets.ROOT / 'Datos/Registros/dataset_activo.json'
                if active.exists():
                    cvat = datasets.read(active).get('cvat', {})
                    if cvat.get('task_id') == 16 and datasets.package_inventory():
                        jobs = cvat['jobs']
                        key = source_key(jobs)
                        if key not in seen:
                            self.sources[key] = {'jobs': sorted(jobs), 'validation': [],
                                                 'enabled': True, 'state': 'waiting'}
                self.save()
            for source in self.sources.values():
                source['state'] = 'waiting' if source['enabled'] else 'paused'

    def status(self):
        with self.state_lock:
            return {'interval_seconds': INTERVAL, 'sources': copy.deepcopy(list(self.sources.values()))}

    def pause_all(self):
        """Modo manual: conservar las copias sin iniciar lectores ni trabajadores."""
        with self.state_lock:
            if self.path.exists():
                self.sources = datasets.read(self.path)['sources']
                for source in self.sources.values():
                    source.update(enabled=False, state='paused')
                    source.pop('error', None)
                self.save()

    def configure(self, config, version=None):
        with self.state_lock:
            return self._configure(config, version)

    def _configure(self, config, version=None):
        key = source_key(config.get('jobs'))
        enabled = config.get('enabled')
        if type(enabled) is not bool:
            raise ValueError('Indica si la sincronización debe estar activa.')
        validation = config.get('validation', [])
        if not isinstance(validation, list) or any(not isinstance(iid, str) for iid in validation):
            raise ValueError('Fotos de validación inválidas.')
        previous = self.sources.get(key, {})
        changed = previous.get('validation') != validation
        source = {**previous, 'jobs': sorted(config['jobs']), 'validation': validation,
                  'enabled': enabled, 'state': 'waiting' if enabled else 'paused',
                  'generation': previous.get('generation', 0) + 1}
        source.pop('error', None)
        if changed:
            source.pop('remote_signature', None)
        if version:
            source['version_id'] = version['id']
            source['last_imported_at'] = version['created_at']
            source.pop('remote_signature', None)
        self.sources[key] = source
        self.due[key] = 0
        self.failures[key] = 0
        self.save()
        self.wake.set()
        return copy.deepcopy(source)

    def remote_signature(self, client, jobs):
        # La versión de anotaciones cambia al guardar, aunque updated_date del
        # job no cambie. Incluir el esquema de la tarea detecta nuevos atributos.
        values, tasks = [], {}
        for job_id in jobs:
            job = client.request(f'/jobs/{job_id}')
            if job.get('type') != 'annotation':
                raise ValueError('Solo se sincronizan trabajos de anotación.')
            task_id = job['task_id']
            if task_id not in tasks:
                task = client.request(f'/tasks/{task_id}')
                datasets.project_scope(task)
                tasks[task_id] = task.get('updated_date')
            annotations = client.request(f'/jobs/{job_id}/annotations')
            # Comparar contenido además de version: algunas importaciones o
            # versiones de CVAT pueden mantener el contador remoto.
            values.append({'job': job_id, 'task': task_id, 'updated': job.get('updated_date'),
                           'annotations': annotations})
        return hashlib.sha256(json.dumps([values, tasks], sort_keys=True).encode()).hexdigest()

    def tick(self):
        with self.state_lock:
            pending = [(key, copy.deepcopy(source)) for key, source in self.sources.items()
                       if source['enabled'] and time.monotonic() >= self.due.get(key, 0)]
        client = None
        for key, requested in pending:
            try:
                client = client or self.reader()
                signature = self.remote_signature(client, requested['jobs'])
                with self.lock:
                    with self.state_lock:
                        source = self.sources[key]
                        if not source['enabled'] or source.get('generation') != requested.get('generation'):
                            continue
                        source['last_checked_at'] = datasets.now()
                        path = datasets.VERSIONS / source.get('version_id', '')
                        if (path / 'archivo.json').exists():
                            source.update(enabled=False, state='paused')
                            self.save()
                            continue
                        changed = signature != source.get('remote_signature') or not (path / 'version.json').exists()
                        recovered = source.get('state') == 'error'
                        if changed:
                            source['state'] = 'syncing'
                    if changed:
                        result = datasets.import_jobs(requested, client=client)
                        self.invalidate()
                    with self.state_lock:
                        source = self.sources[key]
                        if source.get('generation') != requested.get('generation'):
                            continue
                        if changed:
                            source.update(version_id=result['id'], last_imported_at=result['created_at'],
                                          remote_signature=signature)
                        source.update(state='synced')
                        source.pop('error', None)
                        self.failures[key] = 0
                        source.pop('retry_seconds', None)
                        self.due[key] = time.monotonic() + INTERVAL
                        if changed or recovered:
                            self.save()
            except Exception as error:
                client = None
                with self.state_lock:
                    source = self.sources[key]
                    if not source['enabled'] or source.get('generation') != requested.get('generation'):
                        continue
                    self.failures[key] = self.failures.get(key, 0) + 1
                    delay = min(60, INTERVAL * 2 ** min(self.failures[key], 3))
                    source.update(state='error', error=str(error), last_checked_at=datasets.now(),
                                  retry_seconds=delay)
                    self.due[key] = time.monotonic() + delay
                    self.save()

    def run(self):
        while not self.stop.is_set():
            self.wake.clear()
            self.tick()
            self.wake.wait(1)

    def start(self):
        self.initialize()
        self.thread = threading.Thread(target=self.run, name='cvat-sync', daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=2)
