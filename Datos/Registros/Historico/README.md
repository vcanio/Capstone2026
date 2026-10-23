# Histórico y limpieza de registros

Esta sección contiene antecedentes sustituidos y el recibo de la organización del **23/10/2026**. El trabajo actual se consulta en [estado_actual.json](../estado_actual.json).

| Contenido | Qué representa |
|---|---|
| [CVAT](CVAT/README.md) | Recibos de las tareas 20 y 21, sustituidas por la tarea 22. |
| [V2](V2/README.md) | Selección antigua de 296 candidatas y resumen histórico de visibilidad limitada. |
| [Plan y recibo de limpieza](orden_20261023.json) | Cada traslado o eliminación, ruta previa, destino, tamaño y SHA-256. |
| [Verificación de conservación](verificacion_orden_20261023.json) | Comprobación contra el inventario anterior. |

## Qué se limpió

- **113 imágenes auxiliares de pruebas retiradas**, 152.017.274 bytes (152,0 MB decimales), se archivaron fuera del área operativa en `.resguardo/orden_registros_20261023/vistas_pruebas_retiradas/`. Son recortes y superposiciones de primeras fotos de Líder 2 y del ensayo retirado de parciales de tarea 27. No son imágenes originales del dataset. El traslado reduce el contenido de `Registros`; no se presenta como espacio liberado del disco.
- **Cuatro cachés regenerables**, 251.269 bytes, se eliminaron de las exportaciones antiguas. Se conservaron sus fotos, etiquetas e integridad.
- **Seis archivos históricos** se reubicaron aquí: tres de la selección V2, un resumen de visibilidad y dos recibos de tareas sustituidas.
- Se actualizaron índices y catálogo para diferenciar V3 en preparación de los modelos anteriores. Los documentos previos editados se respaldaron en `.resguardo/orden_registros_20261023/documentos_previos/`.

## Qué se conserva

Las 458 imágenes activas, su reparto por escenas, los polígonos de CVAT y los datos usados por ensayos anteriores. Los planes, IDs, coordenadas, verificaciones y reversiones de las pruebas retiradas siguen en sus rutas de `CVAT/revisiones/` para mantener las referencias de las guías y la trazabilidad. Sus README señalan su condición histórica y enlazan las vistas archivadas cuando corresponde.

Los archivos heredados que consulta el código conservan sus rutas: `dataset_activo.json`, `inventario.csv`, `reserva_evaluacion.json`, `CVAT/organizacion.json` y los recibos V1/V2 reutilizados. Su alcance está explicado en el [índice principal](../README.md).

No se eliminaron JSON por estar vacíos o repetir un nombre: pueden ser parte de una versión de datos. La revisión de duplicados exactos encontró únicamente dos revisiones de etiquetas de dos bytes; se conservaron por esa función.
