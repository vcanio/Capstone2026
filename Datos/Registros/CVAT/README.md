# Registro de CVAT

Proyecto [Walmart Stock · Estados por nivel](https://pcvicen.tailca514b.ts.net/projects/7).

## Líder Express: originales y variantes en una tarea

[Abrir tarea 19](https://pcvicen.tailca514b.ts.net/tasks/19). Contiene 236 imágenes: 59 originales reales y 177 variantes IA, en orden original/A/B/C. Una familia completa por trabajo; reparto 80/80/76.

| Responsable | Fotos base | Originales | Variantes | Total | Trabajo |
|---|---|---:|---:|---:|---|
| Vicente Canio · `vi.canio` | 001–020 | 20 | 60 | 80 | [45](https://pcvicen.tailca514b.ts.net/tasks/19/jobs/45) |
| Paulo Guerra · `pau.guera` | 021–040 | 20 | 60 | 80 | [46](https://pcvicen.tailca514b.ts.net/tasks/19/jobs/46) |
| Vicente Vilches · `vi.vilches` | 041–059 | 19 | 57 | 76 | [47](https://pcvicen.tailca514b.ts.net/tasks/19/jobs/47) |

[tarea_19.json](tarea_19.json) registra la carga, la recuperación de cinco polígonos originales y la verificación de anotaciones. La tarea 17 ya estaba ausente al iniciar la unificación; la 18 se eliminó tras validar la nueva. Los seis trabajos anteriores ya no existen. Los registros de esas tareas y sus respaldos están archivados en `.resguardo/unificacion_cvat_lider_express_20261017`.

Se usa la etiqueta `Nivel` de tipo polígono y únicamente `estado`: `reponer`, `suficiente` y `no_evaluable`. El umbral es 30 %. Consultar la [guía](../../../Documentacion/Desarrollo/Guia_anotacion.md) y el [plan de partición](../../../Documentacion/Desarrollo/Plan_particion_lider_express_20261016.md). Se anotan todas; no se ha asignado partición ni habilitado entrenamiento.

Los originales y variantes están en `Datos/V2/lider_express_20261016/imagenes_ordenadas`. El [inventario](../../V2/lider_express_20261016/inventario.csv) relaciona las 236 imágenes con sus trabajos actuales.

## Visibilidad limitada: lote único de 60

**Cierre técnico actualizado:** criterio amodal aplicado por Codex a solicitud del usuario. 308 niveles: 299 suficiente, 9 no_evaluable y 0 reponer; 176 ocluidos. Las cinco incidencias técnicas quedaron resueltas y los trabajos pasaron a validación del equipo. [Revisión actual](revisiones/visibilidad_20261019T222744Z/cierre_criterio/revision_final.html) y [296 candidatos para selección](../Seleccion/lider_express_20261019/README.md). La revisión humana independiente no se certifica por este cierre. Los párrafos de recuentos anteriores conservan la historia de las correcciones.


[Tarea 22](https://pcvicen.tailca514b.ts.net/tasks/22), proyecto 7: **60 variantes IA de 59 familias**, con 24 carros de plástico azul, 24 personas y 12 escenas con cajas. Tres trabajos de veinte imágenes, sin asignación personal: [54](https://pcvicen.tailca514b.ts.net/tasks/22/jobs/54), [55](https://pcvicen.tailca514b.ts.net/tasks/22/jobs/55), [56](https://pcvicen.tailca514b.ts.net/tasks/22/jobs/56).

Las tareas 20 y 21 se sustituyen por esta tarea única tras respaldar y verificar sus imágenes, anotaciones y metadatos. No contenían anotaciones ni incidencias al unificar. La tarea 19 conserva sus 236 imágenes. El respaldo está en `.resguardo/unificacion_visibilidad_20261019`.

Las 30 imágenes de la primera tanda fueron aprobadas por el usuario; las 30 de la segunda requieren revisión independiente. Las tandas se conservan como procedencia. Se importaron 308 polígonos de los originales de la tarea 19, escalados a las ediciones, inicialmente sin estado mediante la opción nativa `__undefined__`. Después de la primera pasada y las correcciones autorizadas, los 308 niveles tienen estado: 286 `suficiente`, 22 `no_evaluable` y 0 `reponer`, con 176 ocluidos. Estos recuentos son provisionales hasta la validación del equipo.

Se aplicaron 30 cambios de estado, una oclusión y un ajuste de contorno en 31 polígonos. La foto 002 ya tenía la corrección propuesta antes de comenzar y se respetó. Se conservaron todos los niveles y se dejaron cinco incidencias abiertas. [Comparativas y validación de las correcciones](revisiones/visibilidad_20261019T222744Z/correcciones/validacion.html), con respaldo en `.resguardo/correcciones_visibilidad_20261019T223458Z`. Los trabajos permanecen en progreso.

Revisar cada contorno y Occluded sobre la edición antes de asignar estados; se incluyeron todos los niveles del original, también el inferior. Registrar una incidencia si sus límites no pueden localizarse. No forzar `no_evaluable` por la presencia de un obstáculo. La tarea 19 conserva sus anotaciones sin cambios. Registro del traspaso (archivo local histórico, fuera de la distribución), con respaldo previo en `.resguardo/traspaso_niveles_visibilidad_20261019`.

Partición `sin_asignar`, familias y escenas juntas, entrenamiento sin habilitar e incorporación al panel pendiente del cierre revisado. Archivos: [lote](../../V2/visibilidad_limitada_20261019/README.md), [galería de 60](../../V2/visibilidad_limitada_20261019/revision_tanda.html), [inventario único](../../V2/visibilidad_limitada_20261019/inventario.csv) y [registro verificado](tarea_22.json).

## Histórico de modelos

La [tarea 16](tarea_16.json) conserva el lote anterior en el proyecto histórico 6, con sus anotaciones y criterio anteriores. No se modificó durante esta unificación. La configuración de acceso está en `Infraestructura/CVAT`.
