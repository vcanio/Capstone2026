"""Conectar un catálogo existente sin copiar datasets ni modificar manifiestos."""
import argparse
from pathlib import Path
import os
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Laboratorio/Modelos'))
import almacenamiento_datos as storage
from migrar_almacenamiento import write,sha,junction


def connect(data_root, aliases=False):
    if not data_root.is_absolute() or not data_root.is_dir():
        raise ValueError('La raíz de datos debe existir y ser absoluta.')
    os.environ['WALMART_DATA_ROOT']=str(data_root)
    catalog=storage.catalog(ROOT)
    checked=set()
    for ref,row in [*catalog['archivos'].items(),*catalog.get('externos',{}).items()]:
        if row.get('externa') and row['externa'] not in checked:
            path=storage.external_path(ROOT,row)
            if sha(path)!=row['sha256']:
                raise ValueError('SHA-256 distinto: '+ref)
            checked.add(row['externa'])
    if aliases:
        for row in catalog['carpetas']:
            source=ROOT/storage.relative(row['origen'])
            target=data_root/storage.relative(row['destino'])
            if source.is_junction() or source.is_symlink():
                if not source.samefile(target):
                    raise ValueError('Alias existente apunta a otro destino: '+str(source))
                continue
            if source.exists():
                raise ValueError('No se sustituye un directorio existente: '+str(source))
            source.parent.mkdir(parents=True,exist_ok=True)
            if os.name=='nt':
                junction(source,target,ROOT)
            else:
                source.symlink_to(target,target_is_directory=True)
    write(ROOT/'.config-modelo/almacenamiento.local.json',{'data_root':str(data_root)})
    print('Datasets conectados: %d archivos externos verificados; alias=%s.' % (len(checked),aliases))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--crear-alias',action='store_true',help='Compatibilidad para herramientas históricas que abren directorios directamente.')
    args=parser.parse_args()
    connect(args.root,args.crear_alias)
