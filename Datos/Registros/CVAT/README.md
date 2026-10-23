# CVAT: tareas y anotaciones

Esta carpeta relaciona imágenes locales con tareas, trabajos y anotaciones. Guarda recibos de carga y verificaciones fechadas. La aplicación y su configuración de acceso están en `Infraestructura/CVAT`.

## Trabajo actual: V3

Proyecto [Walmart Stock · V3](https://pcvicen.tailca514b.ts.net/projects/8), clase geométrica única `Nivel`. **458 imágenes y 2.313 polígonos según la lectura de referencia del 23/10/2026.** Esta organización no aprueba anotaciones ni habilita entrenamiento.

| Tarea | Contenido | Imágenes | Polígonos | Registro |
|---|---|---:|---:|---|
| [27](https://pcvicen.tailca514b.ts.net/tasks/27) | Líder Express: originales + A/B/C/D | 276 | 1.416 | [tarea_27.json](tarea_27.json) |
| [24](https://pcvicen.tailca514b.ts.net/tasks/24) | Variantes con personas, carros y cajas | 60 | 308 | [tarea_24.json](tarea_24.json) |
| [28](https://pcvicen.tailca514b.ts.net/tasks/28) | Originales de Líder 2 | 122 | 589 | [tarea_28.json](tarea_28.json) |

- [criterio_v3.json](criterio_v3.json): procedencia de las 458 imágenes, hashes, tareas, familias y particiones. Sus campos de importación antiguos conservan el estado de aquella carga; para recuentos actuales usar `live_task_counts` y la [lectura de referencia](../Particiones/v3_458_20261023/estado_anotaciones_referencia.json).
- [Partición V3 vigente](../Particiones/v3_458_20261023/README.md): **327 / 68 / 63**, fijada por escenas. Líder 2 tiene **86 / 18 / 18**; no sigue pendiente de reparto.
- [Revisiones](revisiones/README.md): apoyos sobre portaprecio, medianas, superiores y conservación de niveles manuales. Consultar antes de intervenir para evitar duplicados.
- [Criterio de anotación](../../../Documentacion/Desarrollo/Criterio_V3_niveles.md) y [regla de mediana](../../../Documentacion/Desarrollo/Regla_nivel_superior_mediana_V3.md): instrucciones geométricas vigentes, también publicadas en el proyecto.

`delimitacion` y `Occluded` son atributos administrativos. `Revision_foto` es una etiqueta de revisión. No se convierten en clases adicionales de YOLO.

## Registros de criterios anteriores

| Archivo | Alcance histórico |
|---|---|
| [organizacion.json](organizacion.json) | Proyecto V2, responsables, trabajos y etiquetas de disponibilidad. Sigue consultado por el panel heredado. |
| [tarea_16.json](tarea_16.json) | V1: 102 imágenes de procedencia, 91 activas en la copia revisada. |
| [tarea_19.json](tarea_19.json) | V2: 236 imágenes de Líder Express, trabajos 45–47. Sus fotos se reutilizan en V3, tarea 27, con otro criterio. |
| [tarea_22.json](tarea_22.json) | V2: 60 variantes de visibilidad, trabajos 54–56. Sus fotos se reutilizan en V3, tarea 24. |
| [Tareas 20 y 21 sustituidas](../Historico/CVAT/README.md) | Recibos archivados de las tandas reunidas en tarea 22. |

Los estados `reponer`, `suficiente` y `no_evaluable` pertenecen al criterio V2. No describen el objetivo de entrenamiento geométrico de V3. Cambiar de criterio no borra los registros previos ni aprueba las anotaciones para el modelo nuevo.

[Volver al índice de Registros](../README.md).
