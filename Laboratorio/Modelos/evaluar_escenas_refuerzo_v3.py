"""Diagnóstico geométrico fijo por escenas; nunca carga test ni mide ocupación."""
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone
import json
import numpy as np
from PIL import Image, ImageOps
from shapely.geometry import Polygon, box
import preparacion_v3 as p
import entrenamiento_v3 as t


def match_polygons(truth, predicted, threshold=.5):
    matrix=np.zeros((len(truth),len(predicted)))
    for i,a in enumerate(truth):
        for j,b in enumerate(predicted):
            union=a.union(b).area
            matrix[i,j]=a.intersection(b).area/union if union else 0
    # Emparejamiento bipartito de cardinalidad máxima, orden determinista por IoU.
    # Evita contar dos predicciones del mismo nivel como dos aciertos.
    owner={}
    def augment(i,seen):
        for j in sorted(range(len(predicted)),key=lambda j:(-matrix[i,j],j)):
            if matrix[i,j]<threshold or j in seen:continue
            seen.add(j)
            if j not in owner or augment(owner[j],seen):
                owner[j]=i
                return True
        return False
    for i in range(len(truth)):augment(i,set())
    pairs=sorted((i,j,float(matrix[i,j])) for j,i in owner.items())
    return {'tp':len(pairs),'fp':len(predicted)-len(pairs),'fn':len(truth)-len(pairs),
            'matched_iou_sum':sum(v for _,_,v in pairs),'matches':pairs,
            'gt':len(truth),'predicted':len(predicted),'exact_count':len(truth)==len(predicted)}


def aggregate(rows):
    totals={k:sum(r[k] for r in rows) for k in ('tp','fp','fn','gt','predicted','matched_iou_sum')}
    tp,fp,fn=totals['tp'],totals['fp'],totals['fn']
    return {**totals,'images':len(rows),'precision':tp/(tp+fp) if tp+fp else None,
            'recall':tp/(tp+fn) if tp+fn else None,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
            'mean_matched_iou':totals['matched_iou_sum']/tp if tp else None,
            'exact_count_rate':sum(r['exact_count'] for r in rows)/len(rows) if rows else None}


def evaluate(root, source, weights, output, model=None, device=None):
    export,receipt,images=t.validate_export(root,source)
    part=p.partition(root,receipt['partition_path'])
    if part.get('schema_version') not in (4,5,6):raise ValueError('Este diagnóstico exige la partición documentada del refuerzo.')
    plan=p.read(root/part['plan_path'])
    val=[r for r in images if r['split']=='val']
    if {r['name'] for r in val}!=set(plan['selected_val']):raise ValueError('Cambió el panel de evaluación por escenas.')
    weights=Path(weights).resolve()
    if not weights.is_relative_to((root/'Experimentos').resolve()) or weights.name!='best.pt':
        raise ValueError('Evaluar exclusivamente un best.pt del laboratorio.')
    from entrenar_niveles import load_runtime,load_model
    torch,runtime=load_runtime()
    if model is None:model=load_model(weights,runtime)
    if device is None:device=0 if torch.cuda.is_available() else 'cpu'
    fingerprint=p.digest(weights)
    records=[]
    for idx,r in enumerate(val,1):
        with Image.open(export/'images'/t.subset(r)/r['name']) as im:
            oriented=ImageOps.exif_transpose(im).convert('RGB')
            if oriented.size!=(r['width'],r['height']):raise ValueError('Orientación de evaluación incompatible.')
            pixels=np.asarray(oriented)[:,:,::-1].copy()
        prediction=model.predict(pixels,conf=.6,iou=.7,imgsz=640,max_det=300,device=device,retina_masks=True,verbose=False)[0]
        boundary=box(0,0,r['width'],r['height'])
        truth=[Polygon(list(zip(s['points'][::2],s['points'][1::2]))).intersection(boundary) for s in r['shapes']]
        raw=[] if prediction.masks is None else prediction.masks.xy
        predicted=[]
        for points in raw:
            if len(points)<3:continue
            polygon=Polygon(points)
            if not polygon.is_valid:polygon=polygon.buffer(0)
            predicted.append(polygon.intersection(boundary))
        record={'name':r['name'],'sha256':r['sha256'],'scene':r['grupo_escena'],'origin':r['origen'],
                'role':r.get('role'),'review_id':r.get('review_id'),**match_polygons(truth,predicted)}
        records.append(record)
        if idx%20==0:print(f'Evaluación de desarrollo: {idx}/{len(val)}',flush=True)
    grouped=defaultdict(list)
    for r in records:grouped[(r['origin'],r['scene'])].append(r)
    scenes=[{'origin':o,'scene':scene,**aggregate(rows)} for (o,scene),rows in sorted(grouped.items())]
    totals={origin:{**aggregate([r for r in records if r['origin']==origin]),
                    'scenes':len([s for s in scenes if s['origin']==origin]),
                    'macro_scene_f1':float(np.mean([s['f1'] for s in scenes if s['origin']==origin]))}
            for origin in ('real','sintetica') if any(r['origin']==origin for r in records)}
    value={'created_at':datetime.now(timezone.utc).isoformat(),'weights':weights.relative_to(root.resolve()).as_posix(),
           'weights_sha256':fingerprint,'source':source,'source_manifest_sha256':p.digest(export/'manifest.json'),
           'partition_sha256':receipt['partition_sha256'],'confidence':.6,'confidence_optimal':False,
           'nms_iou':.7,'matching_iou':.5,'imgsz':640,'retina_masks':True,
           'policy':'Emparejamiento uno a uno de cardinalidad máxima a IoU >= 0,50, exploración determinista por IoU; métricas micro y macro por escena/origen; conteo exacto no equivale a geometría correcta.',
           'test_accessed':False,'training_started':False,'occupancy_evaluated':False,
           'totals':totals,'scenes':scenes,'images':records}
    baseline_path=root/(plan['baseline_path'] if part.get('schema_version') in (5,6) else
                        'Datos/Preparados/V3/Refuerzos/revision_geometria_20261104/cierre/baseline_padre_escenas.json')
    if baseline_path.is_file() and Path(output).resolve()!=baseline_path.resolve():
        baseline=p.read(baseline_path)
        keys=('source_manifest_sha256','partition_sha256','confidence','nms_iou','matching_iou','imgsz','retina_masks')
        if any(value[k]!=baseline[k] for k in keys):
            raise ValueError('La referencia del padre usa otro conjunto o condiciones de evaluación.')
        metrics=('precision','recall','f1','mean_matched_iou','exact_count_rate','macro_scene_f1')
        value['comparison']={'baseline_sha256':p.digest(baseline_path),
            'baseline_weights_sha256':baseline['weights_sha256'],
            'candidate_minus_parent':{origin:{key:totals[origin][key]-baseline['totals'][origin][key]
                if totals[origin][key] is not None and baseline['totals'][origin][key] is not None else None
                for key in metrics} for origin in totals}}
    assert p.digest(weights)==fingerprint
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);p.write(output,value)
    return value


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--weights',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[2]
    result=evaluate(root,args.source,root/args.weights,root/args.output)
    print(json.dumps(result['totals'],ensure_ascii=False))
