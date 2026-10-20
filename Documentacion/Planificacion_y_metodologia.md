# Planificación y metodología del proyecto

Inicio aproximado: agosto de 2026. Corte: 20 de octubre de 2026.

![Carta Gantt histórica y propuesta de cierre](Evidencias/gantt_20261020.png)

La detección de bordes comenzó en la semana 9 y se integró con YOLO en la semana 11, según la historia comunicada por el equipo. La escala usa semanas de referencia; no asigna días concretos al comienzo de agosto. El primer commit conservado es del 2 de septiembre de 2026, e5d0fbb, y no fija el inicio real del proyecto.

| Hito y actividad | Sem. | Responsables | Estado | Evidencia y alcance |
|---|---|---|---|---|
| H1 Requerimientos y criterio del 30 % | 1–3 | Todo el equipo | Realizado | Inicio en agosto aproximado; segmentación por nivel y criterio inicial de anotación. |
| H2 Infraestructura y captura V1 | 4–6 | V. Canio / V. Vilches | Realizado | Docker/CVAT e inventarios; 37 originales y 72 variantes sintéticas. |
| H3 Etiquetado V1 y panel YOLO | 7–9 | V. Canio / P. Guerra | Realizado | 91 fotos activas; ensayos YOLO11/26 V1 y demo conservados del 15 de octubre. |
| H4 Desarrollo de detección de bordes | 9–11 | Equipo | Experimental operativo | Inicio en semana 9 informado por el equipo; script y revisiones conservados. |
| H5 Captura y partición V2 | 10 | Todo el equipo | Preparación realizada | 236 imágenes base y 60 con obstáculos; corrección de tareas 20/21 en tarea 22. |
| H6 Integración YOLO y detección de bordes | 11 | Equipo | Experimental operativo | Integración en semana 11 informada por el equipo; panel, adaptador y mapas de señal. |
| H7 Modelos V2 base e informe | 11 | Todo el equipo | Realizado | Dos ensayos V2 base; métricas, informe y entrega Lite con detección de bordes. |
| H8 Revisión de oclusiones y V2 de 3 estados | 12–13 | P. Guerra / V. Vilches | Propuesto pendiente | Cerrar revisión semántica de tarea 22 y entrenar; no se declara completado. |
| H9 Deduplicación y refuerzo de faltantes | 14–15 | V. Canio / P. Guerra | Propuesto pendiente | Comparar posprocesamiento en val y ampliar casos reales sin usar test para ajustar. |
| H10 Evaluación final y prueba en otro PC | 16 | Todo el equipo | Propuesto pendiente | Separar test real/sintético/V1 y comprobar instalación de Lite en otro equipo físico. |
| H11 Documentación y defensa | 17 | Todo el equipo | Propuesto pendiente | Cierre documental y demostración; fecha sujeta a confirmación académica. |

Las actividades futuras son propuestas y sus responsables deben acordarse. La defensa del 3 o 4 de diciembre es tentativa. Preparación del lote y corrección de dimensiones no equivalen a revisión semántica cerrada ni a un modelo de tres estados entrenado. El test final debe informar por separado originales reales, variantes sintéticas y reserva V1.

## Metodología

Trabajamos con un enfoque ágil e iterativo inspirado en principios de Scrum. El equipo mantuvo dos reuniones semanales para revisar avances, revisar nuevas imágenes para anotar, discutir diferencias de etiquetado, ajustar criterios y proponer ideas y mejoras. Los acuerdos orientaron el siguiente ciclo de trabajo y permitieron adaptar los datos y los componentes a los resultados observados.

Esta descripción recoge prácticas de inspección y adaptación. Con la información disponible no se atribuyen roles formales, sprints definidos ni una ejecución completa de los eventos de Scrum. Las dos reuniones semanales se describen como seguimiento del equipo; su frecuencia por sí sola no acredita Scrum formal.

Referencia metodológica: Guía Scrum 2020 de Ken Schwaber y Jeff Sutherland, https://scrumguides.org/scrum-guide.html. Para reforzar la trazabilidad se propone registrar fecha, participantes, avances, acuerdos y pendientes de cada reunión.

Los datos de la figura están en [planificacion_20261020.json](Evidencias/planificacion_20261020.json). El generador reproducible es [generar_gantt.py](../Herramientas/Informes/generar_gantt.py). El informe completo conserva los casos, métricas y limitaciones de evaluación.
