"""Smoke de app local y paquete aislado, prohibiendo lecturas del disco E:."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
REG=ROOT/'Datos/Registros/Almacenamiento'


def one(directory, output):
    # Read authorized development bytes before the isolated app is loaded.
    photo=ROOT/'Datos/V3/lider_express_20261016/imagenes_ordenadas/lider_express_014_A_vacios.png'
    body=photo.read_bytes()
    blocked=[]
    def guard(event,args):
        if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
            value=os.fsdecode(args[0]).replace('\\','/').casefold()
            if value.startswith('e:') or value.startswith('//?/e:'):
                blocked.append(value)
                raise RuntimeError('La app intentó acceder a datasets externos.')
    sys.addaudithook(guard)
    os.environ['WALMART_DATA_ROOT']='Z:/datasets_no_disponibles'
    sys.path.insert(0,str(directory))
    from inferencia import ModelRunner
    runner=ModelRunner(directory,device='cpu')
    prediction=runner.analyze(body,runner.manifest['default_model'],None,'yolo_paulo_v2')
    from ocupacion_linea_a import REVISION_LINEA_A, CALIBRATED_THRESHOLD_PCT
    result=dict(estado='verificado',directorio=str(directory.relative_to(ROOT)),
                foto=photo.name,niveles=len(prediction['detections']),ocupacion=prediction.get('occupancy'),
                revision=REVISION_LINEA_A,umbral=CALIBRATED_THRESHOLD_PCT,disco_E_lecturas=len(blocked),data_root_no_disponible=True,
                inferencias_test=0,entrenamiento_iniciado=False)
    if len(prediction['detections'])!=6 or REVISION_LINEA_A!='linea_a_20261108_contornos_conservados' or CALIBRATED_THRESHOLD_PCT!=52:
        raise ValueError('Cambió el resultado o la revisión de la app.')
    if prediction.get('occupancy',{}).get('method')!='linea_a_v1_gondola_anchorage':
        raise ValueError('La app no utilizó Línea A.')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True))


if __name__=='__main__':
    if len(sys.argv)==3:
        one(Path(sys.argv[1]),Path(sys.argv[2]))
    else:
        cases=[(ROOT/'Aplicacion',REG/'app_sin_E.json'),
               (ROOT/'Historico/Evidencias/Limpieza_20261108/paquete_aislado/extraido/Walmart_Vision',REG/'paquete_aislado_sin_E.json')]
        for directory,output in cases:
            subprocess.run([sys.executable,__file__,str(directory),str(output)],check=True,cwd=directory)
