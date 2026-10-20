# Visibilidad limitada: lote único de 60 imágenes

**60 ediciones de 59 familias en una sola [tarea de CVAT](https://pcvicen.tailca514b.ts.net/tasks/22), proyecto 7.** Distribución: 24 carros con plástico azul, 24 personas y 12 escenas con cajas de reposición. Iluminación y desenfoque excluidos.

Las imágenes se produjeron en dos tandas, conservadas como procedencia en el registro: las 30 de la primera fueron aprobadas por el usuario; las 30 de la segunda mantienen pendiente la validación independiente. El criterio amodal quedó aplicado técnicamente a los 308 niveles por Codex, a solicitud del usuario. Recuento: 299 `suficiente`, 9 `no_evaluable` y 0 `reponer`; 176 ocluidos. Las cinco incidencias técnicas quedaron resueltas. La revisión técnica no certifica una validación humana independiente ni habilita entrenamiento automáticamente.

## Trabajar el lote

- [Comparar las 60 ediciones con sus originales](revision_tanda.html).
- [Planilla única de revisión](registro_revision.xlsx), 60 filas, con el estado de aprobación conservado.
- [Inventario](inventario.csv) y [manifest](manifest.json): archivos, origen, familia, SHA-256, prompt, revisión, frame y trabajo actuales.
- [Guía de CVAT](guia_cvat.md): anotar todos los niveles delimitables, incluido el último.
- [Revisión actual de las 60 imágenes, con criterio aplicado](../../Registros/CVAT/revisiones/visibilidad_20261019T222744Z/cierre_criterio/revision_final.html).
- [296 candidatos para seleccionar entrenamiento, validación y reserva](../../Registros/Seleccion/lider_express_20261019/README.md), combinando las tareas 19 y 22.
- [Comparativas históricas de la primera corrección](../../Registros/CVAT/revisiones/visibilidad_20261019T222744Z/correcciones/validacion.html).

Los tres trabajos de veinte imágenes permanecen sin asignación personal. Las tareas anteriores 20 y 21 tienen respaldo en `.resguardo/unificacion_visibilidad_20261019`, y los borradores intermedios, descartes e historiales de tandas están en `.resguardo/orden_v1_v2_20261019/visibilidad_limitada_intermedios`.

## Niveles tapados

Un polígono `Nivel` por nivel completo cuyo contorno pueda localizarse con claridad. El contorno incluye la parte tapada y se activa `Occluded`. Se asigna `estado` por la evidencia visible: `reponer`, `suficiente` o `no_evaluable`. No forzar una clase por el obstáculo, ni contar compras o productos sostenidos como stock del nivel.

También se revisa el nivel inferior. Bajo oclusión parcial se conserva el contorno completo cuando la geometría tiene respaldo fiable en la escena o en el original verificado de la edición. Se conservaron los niveles inferiores de 001 con cajas, 028, 050 y 053 tras comparar su estructura con los originales y se resolvieron sus incidencias técnicas. Los trabajos están en etapa de validación del equipo. Consultar el [criterio de oclusiones](../../../Documentacion/Criterio_oclusiones_niveles.md) y el [ejemplo didáctico](../../../Documentacion/Ejemplos/README.md).

## Procedencia y partición

Todas las ediciones fueron generadas con ImageGen integrado a partir de originales, sin encadenar variantes. Los originales conservan sus bytes. Los 60 prompts están en `prompts/`, uno por archivo editado. La familia 001 tiene dos ediciones con obstáculos diferentes; ambas permanecen juntas.

El 19 de octubre se aplicó la partición conjunta al inventario, heredada de cada familia original: 41 entrenamiento posterior, 10 validación y 9 evaluación final. Consultar el [registro de partición](../../Registros/Particiones/lider_express_v2_20261019/README.md).
