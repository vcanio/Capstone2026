# Proyectos de CVAT en el panel

Esta guía corresponde a la **integración del laboratorio de desarrollo**. Para usar los modelos publicados, seguir [Usar Walmart Visión](Usar_Walmart_Vision.md); no se necesita CVAT. La conexión del laboratorio a CVAT es opcional y utiliza una cuenta personal.

El botón **Cargar proyectos y tareas de CVAT** consulta los proyectos incorporados
al laboratorio y sus tareas compatibles con los inventarios locales registrados.
La consulta conserva los nombres y estados actuales de CVAT. No importa anotaciones
ni aprueba copias automáticamente.

La incorporación se mantiene manual en `PROJECT_SCOPES` y `project_scope()` de
`Herramientas/Modelos/datos_modelos.py`. Los proyectos 4 y 6 conservan sus flujos
históricos. El proyecto 7 incorpora exclusivamente la tarea 19 de Líder Express.
Agregar otro proyecto también requiere comprobar su esquema, inventario y criterio;
el número de proyecto por sí solo no habilita sus tareas.

## Líder Express: proyecto 7, tarea 19

- Inventario: `Datos/V2/lider_express_20261016/inventario.csv`.
- Registro: `Datos/V2/lider_express_20261016/manifest.json`.
- Criterio: `disponibilidad_visual_nivel_v2_reponer`, con los estados `reponer`,
  `suficiente` y `no_evaluable`. No se convierten las cuatro clases históricas.
- Los originales se identifican en CVAT por el nombre terminado en `_0_original`;
  se conserva su familia original y el hash del archivo registrado.
- Importar la tarea completa guarda una copia pendiente de revisión, con recuentos
  y observaciones de los polígonos. Si está disponible la partición fijada, la
  etapa base utiliza 160 imágenes para entrenamiento y 10 originales reales para
  validación. Las 30 variantes de diagnóstico y las 36 imágenes finales quedan
  fuera de la exportación de entrenamiento/validación.
- El panel permite revisar, aprobar, exportar y entrenar **V2 base de dos estados**:
  `Nivel_reponer` y `Nivel_suficiente`. La aprobación exige geometrías, estados y
  partición válidos; importar no aprueba automáticamente.
- Las copias importadas antes de la adaptación a V2 base deben volver a importarse.
  Si falta la partición fijada o quedan incidencias, se mantiene el bloqueo de esa
  copia. Marcar un trabajo como completado en CVAT no sustituye la revisión local.

La indicación anterior de que todo el entrenamiento V2 estaba bloqueado describía
la etapa inicial de integración. La etapa base ya dispone de partición y ensayos
conservados; consultar el [registro de partición](../Datos/Registros/Particiones/lider_express_v2_20261019/README.md)
y el [flujo vigente del panel](../Herramientas/Modelos/README.md).

**V2 completo de tres estados sigue pendiente:** el lote con obstáculos de la tarea
22 requiere aprobación final de sus estados antes de entrenar y validar esa etapa.
La consulta de proyectos del panel admite la tarea 19 del proyecto 7; no incorpora
automáticamente la tarea 22. El script de [entrenamiento de tres estados](Entrenamiento_niveles_v2.md)
requiere un dataset preparado y aprobado con esas clases. La disponibilidad de ese
script no acredita un modelo de tres estados entrenado.

Las imágenes se leen únicamente desde rutas registradas; se comprueban hashes y
dimensiones al importar. La integración no modifica anotaciones, proyectos ni
estados de trabajo en CVAT.
