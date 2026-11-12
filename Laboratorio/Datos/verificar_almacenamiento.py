"""Verificar identidad de la migración sin inferencia, entrenamiento ni CVAT."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'Laboratorio/Modelos'))
import almacenamiento_datos as storage
import preparacion_v3 as preparation
import entrenamiento_v3 as training
from migrar_almacenamiento import REG, read, write, sha


def verify(full=False):
    manifest = read(REG/'manifiesto_migracion.json')
    copies = read(REG/'copias_verificadas.json')
    if copies['estado'] != 'verificado':
        raise ValueError('Copia no terminada.')
    unique = {}
    physical_hashes = {}
    def unchanged(path, expected):
        stat=path.stat()
        identity=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)
        if identity not in physical_hashes:
            physical_hashes[identity]=sha(path)
        return physical_hashes[identity]==expected
    for row in copies['archivos']:
        external = storage.read_path(ROOT,row['origen'],prefer_external=True)
        if full or row['sha256'] not in unique:
            if not unchanged(external,row['sha256']):
                raise ValueError('Hash externo distinto: '+row['origen'])
            unique[row['sha256']]=row['bytes']
        if not unchanged(ROOT/row['recuperacion_c'],row['sha256']):
            raise ValueError('Respaldo C modificado: '+row['origen'])
        # Direct compatibility access must preserve every frozen consumer too.
        if not unchanged(ROOT/row['origen'],row['sha256']):
            raise ValueError('Referencia lógica no accesible: '+row['origen'])
    for row in manifest['archivos']:
        if row['disco']=='C' and row['accion']=='conservar_en_C':
            if not unchanged(ROOT/row['origen_logico'],row['sha256']):
                raise ValueError('Fuente o metadatos modificados: '+row['origen_logico'])
    print('Exportaciones, respaldos y metadatos: identidades verificadas.',flush=True)
    exceptions = []
    for row in manifest['ausencias_conocidas']:
        if (ROOT/row['origen_logico']).exists():
            raise ValueError('Una ausencia intencional reapareció: '+row['origen_logico'])
        exceptions.append(row['origen_logico'])
    part = preparation.partition(ROOT)
    for row in part['imagenes']:
        if not unchanged(preparation.v3_image_path(ROOT,row['path']),row['sha256']):
            raise ValueError('Partición modificada.')
    source='Datos/Preparados/V3/v3_20261105_012333_53df4a59/exportacion_71b4668d'
    path, export, images = training.validate_export(ROOT,source)
    if export['counts']!={'train':171,'val_real':59,'val_sintetica':34}:
        raise ValueError('Cambió la exportación habilitada.')
    sample=read(ROOT/'Datos/Preparados/V3/Calibracion_ocupacion_20261107/muestra_desarrollo.json')
    by_c={r['origen_logico']:r for r in manifest['archivos'] if r['disco']=='C'}
    for row in sample['images']:
        for field in ('source_path','serve_path'):
            expected=storage.entry(ROOT,row[field])
            if expected is None or not unchanged(storage.read_path(ROOT,row[field]),expected['sha256']):
                raise ValueError('Imagen de muestra modificada: '+row[field])
    frozen = {r['origen_logico']:r for r in manifest['archivos'] if r['disco']=='C' and (
        '/Particiones/' in r['origen_logico'] or '/Calibracion_ocupacion_20261107/' in r['origen_logico']) and not r['destino']}
    official=read(ROOT/'.config-modelo/version_actual_v3.json')
    model_hash=sha(ROOT/official['model'])
    app_manifest=read(ROOT/'Aplicacion/modelos.json')
    for model in app_manifest['models']:
        if sha(ROOT/'Aplicacion'/model['file'])!=model['sha256']:
            raise ValueError('Peso de la aplicación modificado.')
    if model_hash!='7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a' or sha(ROOT/official['package'])!='4124744d2615f555280070537ba6308e60025a02729990b3116eda594cc2c3c7':
        raise ValueError('Modelo o ZIP oficial modificados.')
    result=dict(estado='verificado',created_at=datetime.now(timezone.utc).isoformat(),
                archivos_exportados=len(copies['archivos']), hashes_unicos_exportados=len(unique),
                bytes_logicos_exportados=sum(r['bytes'] for r in copies['archivos']),
                respaldos_C_verificados=True, origenes_logicos_verificados=True,
                fuentes_y_metadatos_C_verificados=True, particion_registros=len(part['imagenes']),
                bloqueadas=sum(bool(r.get('preparation_exclusion')) for r in part['imagenes']),
                exportacion=export['counts'],muestra_registros=len(sample['images']),
                muestra_fuentes_y_serve_verificadas=True,ausencias_conocidas=exceptions,
                pesos_y_zip_oficial_sin_cambios=True,entrenamiento_iniciado=False,
                inferencias_test=0,cvat_modificado=False,publicaciones=0)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full',action='store_true')
    parser.add_argument('--output',type=Path,default=REG/'integridad.json')
    args=parser.parse_args()
    result=verify(args.full)
    write(args.output,result)
    print(json.dumps(result,ensure_ascii=True,indent=2))
