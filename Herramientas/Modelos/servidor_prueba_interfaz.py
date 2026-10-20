"""Servidor aislado de escenarios sintéticos. Nunca importa, aprueba ni entrena."""
import argparse
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
TRAINING_SCENARIOS = {'preparing':'preparing', 'active':'training', 'evaluating':'evaluating',
                      'comparing':'comparing', 'training_done':'done', 'training_error':'training',
                      'training_interrupted':'training'}
SCENARIOS = ('mixed', 'empty', 'review', 'ready', 'error', 'recover', 'loading', 'technical', 'activity_error', 'prediction', 'archive', 'model_archive', 'import_loading', 'import_error', *TRAINING_SCENARIOS)
COUNTS = {}
SIMULATED_PREDICTION = None
ARCHIVED = set()
ARCHIVED_MODELS = set()
LOCK = threading.Lock()


def fixture(scenario):
    images=[{'id':f'synthetic/{n}.jpg','name':n,'scene':f'test_{n}', 'url':'/fixture.svg'} for n in ('03','28')]
    photo_rows=[{'imagen':n+'.jpg','split':'val' if n=='28' else 'train','modulos':3,'niveles_solo_revision':2} for n in ('03','28')]
    issues=[{'foto':'03','job_id':9001,'shape_id':501,'problema':p,'bloquea_modulos':True} for p in ('Integridad pendiente','modulo_id repetido')]
    fresh={'id':'datos_sinteticos_nueva','created_at':'2026-10-06T15:00:00Z','state':'pendiente_revision',
           'sources':[{'task_id':9000,'job_id':9001}],
           'report':{'imagenes':photo_rows,'incidencias':issues,'bloqueos_modulos':2,'avisos_niveles':0}}
    old=deepcopy(fresh);old.update(id='datos_sinteticos_anterior',created_at='2026-10-01T15:00:00Z',state='lista_modulos',
                                 review={'reviewer':'Revisor de prueba'})
    old['report'].update(incidencias=[],bloqueos_modulos=0)
    run={'id':'piloto_01_sintetico','ready':True,'signature':'fixture',
         'manifest':{'imagenes':photo_rows},'metrics':{'metrics/mAP50-95(M)':0.5,'metrics/mAP50(M)':0.6},
         'history':[{'epoch':1,'metrics/mAP50-95(M)':0.5}], 'config':{},
         'comparisons':[{'imagen':'28.jpg','split':'val','url':'/fixture.svg','anotados':3,'aciertos':2,'omitidos':1,
                         'falsos_positivos':1,'parejas':[{'iou_mascara':0.7}], 'conf':0.25,'contornos_xy_invalidos':1}]}
    models=[{'id':'synthetic/best.pt','name':'Sintético','run':run['id'],'imgsz':640},
            {'id':'synthetic/general.pt','name':'general · preentrenado','run':None,'imgsz':640}]
    if scenario in TRAINING_SCENARIOS:
        run.update(id='ensayo_sintetico',ready=scenario=='training_done',config={'epochs':100})
        run['history']=[] if scenario=='preparing' else [
            {'epoch':n,'time':n*60,'metrics/mAP50-95(M)':0.22+0.025*n,
             'train/seg_loss':2.8/(1+n*.1), 'val/seg_loss':3.2/(1+n*.09)} for n in range(1,19)]
        models[0]['run']=run['id']
    data={'datasets':[fresh,old],'runs':[run],'models':models,'images':images}
    if scenario=='model_archive':
        data['datasets']=[old]
        data['models'].insert(1,{'id':'synthetic/last.pt','name':'Sintético last','run':run['id'],'imgsz':640})
        data['archived_models']=[{**m,'archived_at':'2026-10-13T12:00:00Z'} for m in data['models'] if m['id'] in ARCHIVED_MODELS]
        data['models']=[m for m in data['models'] if m['id'] not in ARCHIVED_MODELS]
    if scenario=='empty':data={key:[] for key in data}
    if scenario=='review':
        fresh['report'].update(incidencias=[],bloqueos_modulos=0);data['datasets']=[fresh]
    if scenario=='ready':data['datasets']=[old]
    if scenario=='technical':
        run['id']='verificacion_panel_sintetica';models[0]['run']=run['id'];data['models']=models[:1]
    if scenario=='archive':
        old['archive_uses'] = [run['id']]
        data['archived_datasets']=[v for v in data['datasets'] if v['id'] in ARCHIVED]
        data['datasets']=[v for v in data['datasets'] if v['id'] not in ARCHIVED]
    return data


class Handler(BaseHTTPRequestHandler):
    def send(self, value, status=200, mime='application/json; charset=utf-8'):
        body=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

    def do_GET(self):
        url=urlparse(self.path)
        if url.path=='/':
            html=(HERE/'panel.html').read_text(encoding='utf-8')
            html=html.replace('<title>Walmart', '<title>Prueba aislada de Walmart')
            html=html.replace('Entorno local</span>','Datos sintéticos de prueba</span>')
            self.send(html.encode('utf-8'),mime='text/html; charset=utf-8');return
        if url.path=='/fixture.svg':
            self.send(b'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="260"><rect width="600" height="260" fill="#edf3f7"/><text x="30" y="120" font-family="sans-serif" font-size="24" fill="#18333b">Imagen sintetica de prueba</text><text x="30" y="155" font-family="sans-serif" font-size="16" fill="#536975">Sin fotos ni anotaciones reales</text></svg>',mime='image/svg+xml');return
        query=parse_qs(urlparse(self.headers.get('Referer','')).query)
        scenario=query.get('scenario',['mixed'])[0]
        if scenario not in SCENARIOS:self.send({'error':'Escenario desconocido'},400);return
        if url.path=='/api/datasets/sources':
            self.send([] if scenario=='empty' else [
                {'id':'task:13','task_id':13,'name':'Piloto sintético · 5 fotos',
                 'group':'Piloto sintético','jobs':[27],'image_ids':['03','05','16','25','28']},
                {'id':'task:14','task_id':14,'name':'Set sintético · 3 fotos · completado','completed_jobs':3,
                 'group':'Set sintético','jobs':[30,31,32],'image_ids':['01','02','04']}]);return
        if url.path=='/api/catalog':
            with LOCK:
                COUNTS[scenario]=COUNTS.get(scenario,0)+1;count=COUNTS[scenario]
            if scenario=='loading':time.sleep(12)
            if scenario=='error' or (scenario=='recover' and count==1):
                self.send({'error':'Fallo simulado de consulta; no afecta al servidor real.'},503);return
            self.send(fixture(scenario));return
        if url.path=='/api/jobs':
            if scenario=='activity_error':
                self.send({'error':'Fallo simulado de actividad.'},503);return
            if scenario=='prediction' and SIMULATED_PREDICTION:
                self.send([SIMULATED_PREDICTION]);return
            if scenario in TRAINING_SCENARIOS:
                now=datetime.now(timezone.utc)
                progress={'stage':TRAINING_SCENARIOS[scenario], 'completed_epochs':0 if scenario=='preparing' else 18,
                          'current_epoch':19, 'total_epochs':100, 'device':'Dispositivo sintético',
                          'started_at':(now-timedelta(minutes=19)).isoformat(),'updated_at':now.isoformat()}
                if scenario!='preparing':progress.update(preview_url='/fixture.svg',preview_kind='validation')
                self.send([{'id':'synthetic_job','state':{'training_done':'done','training_error':'error',
                           'training_interrupted':'interrupted'}.get(scenario,'running'),
                           'config':{'action':'train','run':'ensayo_sintetico','epochs':100},'progress':progress,
                           'log':'Avance simulado; no hay entrenamiento en ejecución.'}]);return
            self.send([]);return
        self.send({'error':'Ruta de prueba desconocida'},404)

    def do_POST(self):
        global SIMULATED_PREDICTION
        scenario=parse_qs(urlparse(self.headers.get('Referer','')).query).get('scenario',['mixed'])[0]
        if scenario in ('import_loading','import_error') and self.path=='/api/datasets/import':
            time.sleep(6)
            if scenario=='import_error':
                self.send({'error':'Error de conexión simulado para comprobar la recuperación.'},400)
            else:
                self.send({**fixture(scenario)['datasets'][0], 'import_reused': True})
            return
        if scenario=='model_archive' and self.path in ('/api/models/archive','/api/models/restore'):
            config=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
            with LOCK:
                data=fixture(scenario)
                model=next((m for m in data['models']+data.get('archived_models',[]) if m['id']==config.get('id')),None)
                if not model or not model['run']:
                    self.send({'error':'Este modelo no se puede quitar de la lista.'},400);return
                archive=self.path.endswith('/archive')
                if archive:ARCHIVED_MODELS.add(model['id'])
                else:ARCHIVED_MODELS.discard(model['id'])
            self.send({'id':model['id'],'archived':archive});return
        if scenario=='archive' and self.path in ('/api/datasets/archive','/api/datasets/restore'):
            config=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
            with LOCK:
                data=fixture(scenario)
                candidates=data['datasets'] if self.path.endswith('/archive') else data['archived_datasets']
                copy=next((v for v in candidates if v['id']==config.get('id')),None)
                if not copy or copy.get('archive_uses'):
                    self.send({'error':'La copia no está disponible para esta acción.'},400);return
                if self.path.endswith('/archive'):ARCHIVED.add(copy['id'])
                else:ARCHIVED.remove(copy['id'])
            self.send(copy);return
        if self.path=='/api/jobs' and scenario=='prediction':
            config=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
            if config.get('action')=='predict':
                result={'config':{**config,'split':'val'},'metricas':{'aciertos':2,'anotados':3,'omitidos':1,'extras':1,'iou_medio':0.7},
                        'detecciones':[{'clase':'Modulo','confianza':0.8,'contorno_valido':False}]}
                SIMULATED_PREDICTION={'id':'synthetic_prediction_'+str(time.monotonic_ns()),'state':'done','config':config,'log':'Predicción sintética, sin ejecutar modelos.',
                                      'image_url':'/fixture.svg','result':result}
                self.send({**SIMULATED_PREDICTION,'state':'running'});return
        self.send({'error':'Este servidor de prueba bloquea todas las escrituras. No importa, revisa ni entrena.'},403)

    def log_message(self, *_):
        pass


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8091);args=parser.parse_args()
    print(f'Pruebas aisladas: http://localhost:{args.port}/?scenario=mixed',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
