# Proyectos de CVAT en el panel

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
- Importar guarda una copia pendiente de revisión, con recuentos y observaciones
  de los polígonos. Las fotos permanecen con partición `pending`: los recuentos
  de entrenamiento y validación no se presentan como una separación existente.
- Aprobar y exportar para entrenar permanece bloqueado. Este cambio incorpora
  consulta y revisión; no habilita el entrenamiento ni la evaluación v2 del panel.

Antes de habilitar entrenamiento, resolver familias y grupos de escena, congelar
las particiones, revisar la cobertura y completar el flujo de modelos v2 del panel.
El fundamento está en `Documentacion/Plan_particion_lider_express_20261016.md`.
Marcar los trabajos como completados en CVAT no sustituye esas comprobaciones.

Las imágenes se leen únicamente desde rutas registradas; se comprueban hashes y
dimensiones al importar. La integración no modifica anotaciones, proyectos ni
estados de trabajo en CVAT.
