# Limpieza y orden completados · 8 de noviembre de 2026

Vicente pidió completar el plan para trabajar con la última versión estable y reunir los antecedentes para documentar el progreso. Se conserva la app local del 8/11, el modelo oficial del 5/11, el ensayo y la preparación vigentes, las fuentes necesarias, las etiquetas humanas de ocupación y las herramientas operativas.

## Resultado

La continuación trasladó **15.999 archivos en 511 lotes, 19,496 GiB lógicos**, a `Historico/`. Sumados los ocho archivos del lote inicial, son **16.007 archivos trasladados**. No se purgaron binarios, fuentes ni cachés; mover dentro del disco no libera ese espacio.

- Ensayos anteriores completos, datasets y pesos existentes en `Historico/Experimentos/`.
- Preparaciones sustituidas, pilotos y selecciones cerradas en `Historico/Datos/`.
- Paquetes, informes, scripts de operaciones y documentación fechada en sus secciones históricas.
- **325 ejecuciones terminadas** del panel archivadas; las fotos subidas y trabajos asociados al ensayo oficial permanecen disponibles en el área operativa.
- `.tmp` queda para servicios y trabajo actual, con las dos excepciones de compatibilidad y el enlace externo documentados en su README.
- Guías, índices, estado estructurado y `AGENTS.md` actualizados. Los textos previos se conservan; evolución del proyecto (`Historico/Evolucion.md`, archivo del entorno local; fuera de esta distribución).

## Compatibilidad y dependencias conservadas

Los 107 enlaces de directorio nuevos son alias ocultos, no copias. El mapa de rutas (`.config-modelo/rutas_historicas.json`, archivo del entorno local; fuera de esta distribución) permite resolver referencias congeladas sin alterar manifiestos. Docker monta explícitamente destinos históricos y el archivo completo en lectura; el lector admite la misma identidad de archivo cuando Docker Desktop representa una junction con una ruta `/mnt/host` diferente a `/app/Historico`.

Se mantienen las fuentes compartidas V1/V2/V3, las particiones y registros CVAT necesarios para procedencia, el núcleo `Bordes` y sus versiones de diagnóstico, los preentrenados utilizados por herramientas compatibles, los entornos instalados y el ZIP oficial. `.publicacion/repositorio` y su worktree conservan sus ubicaciones; no hubo sincronización ni publicación. Las fuentes únicas de fotos no se eliminan por quedar fuera de una selección reducida.

El catálogo habitual muestra un modelo propio, el **best.pt oficial**, y una exportación activa. El prototipo de ocupación y sus etiquetas permanecen en desarrollo; no se sustituyen por la copia portable al consultar comparaciones anteriores.

## Comprobaciones

- Primer control tras los traslados: los 437 lotes de directorios y entregas conservaron todos los hashes. Las posteriores correcciones de enlaces Markdown tienen copia previa y recibo independiente.
- Pruebas de app, Línea A, laboratorio y datos correctas; se añadieron comprobaciones de archivo registrado, límites de rutas y partición de desarrollo con reserva externa.
- Verificación de **275 hashes** de la partición de desarrollo actual, sin fugas de escena/familia detectadas por su validador. La reserva final externa no se abre ni se declara evaluada.
- Paquete aislado probado por HTTP en CPU: `lider_express_014_A_vacios.png` devuelve seis niveles y `lider_express_020_A_vacios.png` cinco; conservan Línea A, umbral 52 y revisión de contornos. Esta comprobación verifica funcionamiento, no precisión exhaustiva.
- App en 8095 y laboratorio en 8090 restablecidos. HTTP 200 en el catálogo de la app, salud y catálogo operativo del laboratorio. Se verificó el acceso al padre histórico desde Docker.
- Los dos pesos oficiales conservan `7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a`; el ZIP publicado conserva `4124744d2615f555280070537ba6308e60025a02729990b3116eda594cc2c3c7`.

Auditoría final (`Historico/Evidencias/Limpieza_20261108/auditoria_final.json`, archivo del entorno local; fuera de esta distribución) · Pruebas (`Historico/Evidencias/Limpieza_20261108/pruebas_finales.json`, archivo del entorno local; fuera de esta distribución) · Paquete aislado (`Historico/Evidencias/Limpieza_20261108/paquete_aislado/verificacion_http.json`, archivo del entorno local; fuera de esta distribución) · Servicios (`Historico/Evidencias/Limpieza_20261108/servicios_verificados.json`, archivo del entorno local; fuera de esta distribución).

## Incidencias y límites explícitos

El verificador global sigue fallando por las fuentes V1 ausentes desde antes (`lider_001.jpg`, `lider_002.jpg`, `lider_003.jpg`). No se restauraron ni se modificó su inventario para ocultar la incidencia. Los enlaces a respaldos retirados anteriormente se mantienen identificados como antecedentes ausentes. No se afirma auditoría global aprobada.

El lote inicial no tomó respaldo de los documentos editados; no se inventa esa copia anterior. Esta continuación sí guardó los textos antes de editarlos. Durante el archivo fue necesario cerrar los logs de la app y reiniciarla; los nuevos logs viven en `.tmp/servicios_actuales`. Un intento de reinicio no se ejecutó por el límite de la revisión automática, y se completó al reanudarse el trabajo.

No se modificaron anotaciones en CVAT, particiones, pesos oficiales ni activos remotos. No se entrenó ni se usó test para inferencias o ajustes. La app local usa Línea A; la release del 5/11 conserva su estimador anterior.

## Recibos y reversión

Los recibos de esta operación están en `Historico/Evidencias/Limpieza_20261108/`, con un alias oculto desde `.tmp/limpieza_orden_20261108`. `movimientos.json` y `movimientos_documentos.json` guardan origen, destino, tamaño y hashes; `antes/` conserva los textos editados desde esta continuación. El lote inicial tiene su propio recibo.

Para revertir un lote: detener solo los lectores afectados, verificar hashes y destinos, retirar únicamente la junction de ese origen (nunca su contenido), devolver cada archivo a su origen sin sobrescribir, restaurar los textos correspondientes y revertir sus entradas de configuración/montajes. No realizar borrados recursivos sobre alias ni reconstruir material que ya faltaba antes de esta operación.

[Plan original](Plan_limpieza_y_orden_20261108.md) · [Mapa del proyecto](Mapa_del_proyecto.md) · [Histórico](../../Historico/README.md).
