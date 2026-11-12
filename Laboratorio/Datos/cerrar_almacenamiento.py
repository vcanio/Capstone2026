"""Cerrar el recibo tras el retiro: identidad de enlaces y ahorro observado."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

from migrar_almacenamiento import ROOT,REG,read,write,sha,checked,verified_copy
sys.path.insert(0,str(ROOT/'Laboratorio/Modelos'))
import almacenamiento_datos as storage


def close():
    manifest=read(REG/'manifiesto_migracion.json')
    removed=read(REG/'retiro.json')
    activated=read(REG/'activacion.json')
    if len(removed['carpetas'])!=len(manifest['carpetas']) or len(removed['archivos'])!=3847:
        raise ValueError('El retiro no está completo.')
    external=storage.data_root(ROOT)
    for group in activated['carpetas']:
        original=ROOT/group['origen']
        if not original.is_junction() or not original.samefile(external/group['destino']):
            raise ValueError('Alias de compatibilidad distinto: '+group['origen'])
        if (ROOT/group['reserva_temporal']).exists():
            raise ValueError('Queda un temporal: '+group['reserva_temporal'])
    for row in removed['archivos']:
        original=ROOT/row['origen']
        target=external/row['destino']
        if not original.samefile(target) or original.stat().st_size!=row['bytes'] or not (ROOT/row['recuperacion_c']).is_file():
            raise ValueError('Referencia o copia de recuperación faltante: '+row['origen'])
    part=read(ROOT/read(ROOT/'Datos/Registros/Particiones/activa_v3.json')['path'])
    coverage=[]
    for row in manifest['cobertura']['particion_sin_csv']:
        image=next(r for r in part['imagenes'] if r['sha256']==row['sha256'])
        target=storage.read_path(ROOT,image['path'],prefer_external=True,verify=True)
        coverage.append(dict(name=row['name'],sha256=row['sha256'],destino=target.relative_to(external).as_posix(),estado='verificado_en_E'))
    write(REG/'cobertura_final.json',dict(particion_registros=len(part['imagenes']),sin_correspondencia_csv_resueltas=coverage,pendientes=0))
    current={p:shutil.disk_usage(p)._asdict() for p in ('C:/','E:/')}
    baseline=manifest['espacio_inicial']
    recovery={h:ref for h,ref in manifest['recuperacion_c'].items() if ref.startswith('.resguardo/')}
    backup_bytes=sum((ROOT/ref).stat().st_size for ref in recovery.values())
    order=read(REG/'orden_E.json')
    result=dict(schema_version=1,estado='completado',fecha='2026-11-08',created_at=datetime.now(timezone.utc).isoformat(),
                catalogo='Datos/Registros/Almacenamiento/catalogo.json',
                inventario_archivos=15780,carpetas_externalizadas=len(removed['carpetas']),
                archivos_externalizados=len(removed['archivos']),bytes_logicos_externalizados=removed['bytes_logicos_retirados'],
                hashes_unicos_externalizados=read(REG/'integridad_previa_retiro.json')['hashes_unicos_exportados'],
                copias_recuperacion_unicas_C=len(recovery),bytes_recuperacion_C=backup_bytes,
                clasificados_E_consolidados=len(order['enlaces_duros']),bytes_logicos_copias_E_consolidadas=sum(r['bytes'] for r in order['enlaces_duros']),
                espacio_inicial=baseline,espacio_final=current,
                aumento_libre_C_observado=current['C:/']['free']-baseline['C:/']['free'],
                nota_espacio='Variación libre observada entre mediciones; otros procesos pueden modificar el espacio. Los tamaños lógicos no equivalen a asignación física.',
                windows_verificado=True,docker_verificado=True,app_y_paquete_sin_E=True,
                particion_registros=len(part['imagenes']),exportacion={'train':171,'val_real':59,'val_sintetica':34},
                muestra_registros=163,ausencias_conocidas=manifest['ausencias_conocidas'],
                auditoria_global_aprobada=False,incidencia_estructura_previa='README.md enlaza a Fase 1/, ausente al inicio; no se reconstruye material académico.',
                entrenamiento_iniciado=False,inferencias_test=0,cvat_modificado=False,publicaciones=0)
    write(REG/'estado_actual.json',result)
    # An external receipt is an additional metadata copy, not a second image backup.
    for name in ('catalogo.json','configuracion.ejemplo.json','README.md','inventario_inicial.json','manifiesto_migracion.json',
                 'copias_verificadas.json','activacion.json','retiro.json','orden_E.json','estado_actual.json','cobertura_final.json',
                 'integridad_previa_retiro.json','comprobacion_docker.json','comprobacion_http.json','app_sin_E.json','paquete_aislado_sin_E.json'):
        source=REG/name
        target=checked(external,'Catalogo/Migracion_20261108/'+name)
        verified_copy(source,target,sha(source),source.stat().st_size)
    print('Cierre verificado: %d archivos; C: %.3f GiB libres, aumento observado %.3f GiB.' % (len(removed['archivos']),current['C:/']['free']/2**30,result['aumento_libre_C_observado']/2**30))


if __name__=='__main__':
    close()
