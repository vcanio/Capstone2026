"""Comprobar servicios y autorización HTTP con datos de desarrollo ya fijados."""
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from migrar_almacenamiento import ROOT,REG,read,write


def get(url):
    with urlopen(url,timeout=60) as response:
        return response.status,response.read()


results=[]
for url in ('http://127.0.0.1:8095/api/models','http://127.0.0.1:8090/api/health','http://127.0.0.1:8090/api/catalog/current'):
    status,body=get(url)
    assert status==200
    results.append(dict(url=url,status=status))
part=read(ROOT/read(ROOT/'Datos/Registros/Particiones/activa_v3.json')['path'])
photo=next(r for r in part['imagenes'] if r['split']=='train' and not r.get('preparation_exclusion'))
url='http://127.0.0.1:8090/file?'+urlencode({'path':photo['path']})
status,body=get(url)
assert hashlib.sha256(body).hexdigest()==photo['sha256']
results.append(dict(url=url,status=status,sha256_correcto=True))
for ref in ('E:/Datasets Walmart/Revision/secret.jpg','../secret','Datos/Registros/Almacenamiento/catalogo.json'):
    url='http://127.0.0.1:8090/file?'+urlencode({'path':ref})
    try:
        get(url)
        raise AssertionError('El panel expuso una ruta no autorizada.')
    except HTTPError as error:
        assert error.code in (400,404)
        results.append(dict(referencia=ref,status=error.code,rechazada=True))
write(REG/'comprobacion_http.json',dict(estado='verificado',peticiones=results,inferencias=0,entrenamiento_iniciado=False))
print('Servicios y autorización: %d comprobaciones correctas.' % len(results))
