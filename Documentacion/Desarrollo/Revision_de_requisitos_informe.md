# Relación entre la documentación y lo solicitado

El encargo pide mostrar el avance real del proyecto, analizar las dificultades y proponer mejoras. La entrega conserva sus cinco puntos y explica los términos para que el equipo y una persona externa puedan seguir el razonamiento técnico.

| Punto solicitado | Dónde encontrarlo | Qué se mantiene explícito |
|---|---|---|
| 1 Estado de avance | Sección 1 del [informe](../Informe_Intermedio_Avance_20261020.md) y [planificación](../Planificacion_y_metodologia.md). | Actividades, módulos, porcentajes estimados y evidencias; Gantt desde agosto aproximado; dificultades; responsables y fechas propuestas. Los retrasos no se cuantifican sin una planificación anterior verificable. |
| 2 README técnico | [README del repositorio](../../README.md). | Problema, objetivos, herramientas y motivos de elección, arquitectura, datos, preparación y estado de implementación. |
| 3 Resultados preliminares | Sección 3 del [informe](../Informe_Intermedio_Avance_20261020.md). | Diez casos favorables y diez con errores de YOLO + bordes, con entrada, salida YOLO, mapa de señal, resultado esperado y criterio visual. Cada error incluye una posible causa y una mejora. Los números históricos de YOLO se separan de esta selección; no se inventan métricas globales. |
| 4 GitHub y reproducibilidad | Sección 4 del informe, [uso de Visión](../Usar_Walmart_Vision.md), [laboratorio técnico](Replicar_proyecto.md) y [trabajo en equipo](Trabajo_en_equipo.md). | Estructura, instalación y ejecución de la aplicación con pesos publicados; proceso de desarrollo explicado y repetición de ensayos condicionada a los activos del equipo. El historial Git permite revisar contribuciones; no se inventan participaciones. |
| 5 Conclusiones y próximos pasos | Sección 5 del informe. | Objetivos logrados, componentes operativos, pendientes del MVP, prioridades, responsables propuestos, fechas estimadas y condiciones para cumplir el alcance. |

## Cómo leer y presentar la entrega

La entrega al usuario comprende Walmart Visión y los modelos publicados. CVAT y el panel de entrenamiento se documentan para comprender la construcción y continuar el desarrollo; instalarlos no es un requisito de uso. Esta delimitación no acredita la reproducción pública del laboratorio completo ni sustituye una exigencia adicional que establezca la pauta de evaluación.

Empezar por la [guía para entender el proyecto](../Guia_para_entender_el_proyecto.md). Después, leer el resumen del informe, revisar qué funciona y qué falta, y explicar un caso exitoso y uno fallido con sus imágenes. La configuración exacta y los registros sirven para respaldar esa explicación.

Cada caso debe responder qué imagen se usó, qué esperábamos, qué hizo el modelo y qué aprendimos. Una métrica favorable se presenta junto al número de ejemplos y sus límites. Los veinte casos se conservan como una selección razonada; no se presentan como un ranking estadístico comparable entre datasets distintos.

## Pendientes de la entrega que deben comprobarse

La demo publicada no cierra la validación en otro computador físico. La [pauta de instalación externa](../Usar_Walmart_Vision.md#comprobar-la-instalación-en-otro-computador) indica cómo comprobar y registrar ese recorrido sin instalar el laboratorio. También quedan pendientes ampliar faltantes reales, aprobar las anotaciones con obstáculos, entrenar V2 de tres estados, comparar el filtrado de duplicados y realizar la prueba final. Iluminación, perspectiva, sombras y reflejos se consideran posibles factores, pero no se les atribuye una causa demostrada sin una comparación que la respalde.

La revisión del 21 de octubre incorpora los resultados aportados por el equipo; la preparación del informe no ejecuta nuevas inferencias ni cambia modelos o particiones. Se corrigieron categorías de producto y se excluyeron tablas incompatibles con las imágenes. El caso bueno repetido se sustituyó por la evidencia de cuidado capilar, identificada como variante sintética de diagnóstico. Las métricas de los entrenamientos anteriores conservan su alcance original.
