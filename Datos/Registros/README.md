# Registros de datos y anotaciones

| Archivo o carpeta | Qué consultar |
|---|---|
| [lotes.json](lotes.json) | Catálogo de procedencia: inventario, ubicación y estado de cada lote. |
| [dataset_activo.json](dataset_activo.json) | Set y copia revisada usados por los ensayos vigentes. |
| [inventario.csv](inventario.csv) | Inventario de las 37 fuentes de Lider: 30 de desarrollo y 7 reservas finales. Incluye nombre original, nombre actual lider_001.jpg, etc., y local. Sus rutas son relativas a Datos/, aunque este CSV esté en Registros/. |
| [Lotes/Equilibrado_v1_20261013](Lotes/Equilibrado_v1_20261013/manifest.json) | Registro de las 102 imágenes de procedencia; referencia las fotos de V1 sin duplicarlas. Sus rutas son relativas a Datos/. |
| `Versiones_modelos/` | Anotaciones importadas de CVAT, particiones y revisiones. Conservar sus bytes y crear una versión nueva ante cambios de anotación. |
| [CVAT](CVAT/README.md) | Recibo de la tarea vigente y organización del equipo. |
| [reserva_evaluacion.json](reserva_evaluacion.json) | IDs y escenas separados de entrenamiento y validación. |

El catálogo distingue las fuentes iniciales, el paquete Equilibrado v1 y la captura Líder Express. **No sumar sus cantidades como si fueran fotos independientes**: Equilibrado referencia las mismas 30 fotos reales de Lider; no almacena otras copias. Sus 72 sintéticas son archivos distintos.

Los campos de aprobación y uso de los inventarios originales reflejan su preparación. Para saber qué se utilizó para entrenar, consultar la copia revisada indicada por dataset_activo.json, que tiene 91 imágenes activas tras 11 exclusiones. Los cambios de ruta o procedencia se registran sin cambiar los IDs históricos, los hashes ni la copia revisada.

Los lotes nuevos conservan su inventario y manifest junto a sus imágenes; lotes.json los enlaza sin duplicarlos. Líder Express tiene 59 fotos asignadas a anotación en la [tarea 19](CVAT/tarea_19.json), repartidas 80/80/76 (originales y variantes). La importación a modelos y el entrenamiento siguen sin habilitar: el importador requiere registrar el nuevo esquema y las escenas antes de incorporar esta tarea.

Las rutas de este directorio se usan en Herramientas/Modelos. Los ensayos guardados conservan sus referencias históricas a las imágenes; rutas_datos.py sigue resolviéndolas. Para desplegar la reorganización en una imagen Docker previa, reconstruir el panel con el código actualizado.

Cada versión de datos puede tener una sola carpeta exportaciones/dataset_niveles, con imágenes y etiquetas preparadas para entrenar y un registro de integridad. Los ensayos la referencian mediante dataset_ref; no mantienen otra copia completa por modelo.

[Flujo común](../README.md) · Comprobación y recuperación del ordenamiento (archivo local histórico, fuera de la distribución).
