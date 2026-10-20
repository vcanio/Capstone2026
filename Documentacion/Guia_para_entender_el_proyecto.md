# Guía para entender Walmart Computer Vision

Esta guía explica los conceptos necesarios para leer el README, interpretar el informe y participar en el proyecto. Está pensada para quienes están aprendiendo visión computacional. Los resultados, configuraciones y evidencias completas se mantienen en sus documentos de referencia.

## Qué estamos construyendo

Queremos apoyar la revisión de góndolas a partir de fotografías. La aplicación busca cada nivel o repisa, dibuja su contorno y asigna un estado de disponibilidad. Por ejemplo, puede señalar cuatro niveles suficientes y uno que necesita reposición.

El modelo actual V2 base utiliza dos estados: `reponer` y `suficiente`. La versión V1 utiliza cuatro: `vacio`, `baja_disponibilidad`, `suficiente` y `no_evaluable`. La siguiente etapa de V2 debe incorporar `no_evaluable` para situaciones donde una persona, carro u otro obstáculo impide decidir. Esa etapa aún no está entrenada ni validada.

La aplicación trabaja con lo visible en una foto. No conoce las unidades que hay detrás de la primera fila ni las existencias de bodega. El criterio inicial del 30 % se usa para etiquetar disponibilidad según el ancho del nivel; todavía debe calibrarse. La confianza de YOLO y la señal experimental de bordes son valores distintos de ese criterio.

## Delimitar un nivel y decidir su estado

**Detección** significa localizar algo en una imagen. **Segmentación** añade la forma de la región: en este proyecto buscamos el contorno completo del nivel, incluso cuando contiene espacios vacíos. La región coloreada resultante se llama **máscara**. Un **polígono** es la figura que dibujamos manualmente para indicar ese contorno durante el etiquetado.

**Clasificar** significa asignar una categoría. Un nivel puede estar bien delimitado y tener una categoría equivocada. Por eso revisamos ambas cosas: dónde dibujó el modelo y qué estado decidió.

**Inferencia** es usar un modelo ya entrenado para analizar una imagen. **Entrenar** es ajustar el modelo con ejemplos etiquetados. Los **pesos** son los archivos que guardan lo aprendido; en nuestros ensayos se conservan como archivos `.pt`. Un **checkpoint** es un guardado de esos pesos durante el entrenamiento.

## Para qué sirve cada herramienta

| Herramienta | Su trabajo en el proyecto | Por qué la utilizamos |
|---|---|---|
| CVAT | Permite dibujar los niveles y asignar sus etiquetas. | Facilita que el equipo revise las mismas imágenes y corrija diferencias. |
| YOLO de segmentación | Aprende con los ejemplos y después dibuja y clasifica niveles. | Resuelve localización y estado con un mismo modelo; comparamos YOLO11 y YOLO26. |
| Ultralytics y PyTorch | Ejecutan el entrenamiento y el análisis con los modelos. | Permiten partir de pesos generales ya entrenados y adaptarlos a nuestras imágenes. |
| OpenCV, Pillow y NumPy | Preparan fotografías y calculan operaciones sobre sus píxeles. | Ayudan a orientar imágenes, trabajar con máscaras y calcular la señal de bordes. |
| Docker | Prepara un entorno con las dependencias del panel. | Facilita ejecutar el laboratorio con una configuración compartida. Los datos y pesos se instalan aparte. |
| Git y GitHub | Guardan cambios del código y permiten integrarlos entre compañeros. | Mantienen el historial y permiten revisar una mejora antes de incorporarla. |
| Walmart Lite | Abre una interfaz local para probar los modelos. | Permite cargar fotografías propias sin instalar todo el laboratorio. |

La **CPU** es el procesador del computador. La **GPU** es la tarjeta gráfica y puede acelerar los cálculos cuando el entorno está configurado para utilizarla. La demo Lite utiliza CPU.

## Cómo organizamos las imágenes

**Dataset** significa conjunto de datos. El nuestro reúne fotografías reales y versiones modificadas con IA. Las versiones modificadas son **sintéticas**: sirven para experimentar y ampliar ejemplos, pero no representan nuevas capturas reales independientes.

Dividimos los datos en tres grupos, llamados **particiones**:

| Grupo | Nombre habitual | Para qué lo usamos |
|---|---|---|
| Entrenamiento | `train` | El modelo utiliza estos ejemplos para aprender. |
| Validación | `val` | Comparamos modelos y ajustes durante el desarrollo. |
| Prueba final | `test` | Lo reservamos para comprobar el resultado después de fijar el modelo y sus ajustes. |

Una **familia** reúne la foto original y sus versiones modificadas. Todas deben quedar en el mismo grupo. Si una original se usara para entrenar y una versión casi idéntica para evaluar, el resultado podría parecer mejor porque el modelo ya vio una imagen muy parecida. A ese problema lo llamamos **fuga de datos**. También agrupamos escenas relacionadas para reducir este riesgo; eso no demuestra por sí solo que el sistema funcione en otros supermercados.

Conservamos **405 imágenes únicas: 96 reales y 309 sintéticas**. Los inventarios suman 435 registros porque algunas referencias se repiten. La validación principal V2 base usa 10 fotografías reales con 51 niveles; las variantes sintéticas se revisan por separado.

## Cómo leer los resultados

La **referencia** es el dibujo y estado revisados por personas. La **predicción** es el resultado del modelo. Comparamos ambos para medir los aciertos y revisar errores; la referencia humana también puede necesitar correcciones.

| Término del informe | Cómo interpretarlo |
|---|---|
| Localizados | Cuántos niveles de referencia encontró el modelo. Encontrar el nivel no garantiza acertar su estado. |
| Estados exactos | Cuántos niveles encontrados también tienen el estado esperado. |
| Omitidos | Niveles de referencia que el modelo no encontró. |
| Extras | Predicciones sin una referencia correspondiente. Hay que revisar si son errores o si faltó anotar una región real. |
| Alerta acertada o TP | El modelo avisa que hay que reponer y la referencia coincide. |
| Falsa alerta o FP | El modelo pide reponer donde la referencia no lo indica. |
| Alerta omitida o FN | Había que reponer, pero el modelo no avisó. |

**Ejemplo real guardado:** YOLO26 V2 encontró 50 de 51 niveles y acertó esos 50 estados. Emitió una alerta de reposición acertada y ninguna falsa. La prueba de alertas fue pequeña: solo había un nivel de reposición en esa validación. El resultado de **1/1** describe ese caso y no demuestra que detecte todos los faltantes de una tienda.

**Ejemplo para entender dos métricas distintas:** YOLO11 V2 encontró los 51 niveles, pero acertó 48 estados. Detectó la única alerta real y emitió cuatro falsas. Su precisión de alertas fue 1/5: de cinco avisos, uno era correcto. Su recall fue 1/1: encontró el único faltante de referencia. Por eso hay que mirar ambas medidas y el número de ejemplos.

**IoU** compara cuánto coinciden dos regiones, de 0 a 1. Se calcula como el área compartida dividida por el área total que cubren ambas. En nuestro informe se comparan máscaras. Un valor alto indica buen ajuste del contorno, aunque el estado todavía puede estar equivocado.

**mAP** resume la relación entre precisión y recall por clase. `mAP50` usa IoU 0,50; `mAP50–95` promedia umbrales de 0,50 a 0,95 en pasos de 0,05. En el informe mostramos métricas de máscaras. El 92,79 % de mAP50–95 no significa que el sistema acierte el 92,79 % de las fotos ni que detecte ese porcentaje de los faltantes de una tienda.

Para leer las cifras con más detalle, consultar las explicaciones de [métricas de Ultralytics](https://docs.ultralytics.com/guides/yolo-performance-metrics/), [validación](https://docs.ultralytics.com/modes/val/) y [segmentación](https://docs.ultralytics.com/tasks/segment/).

## Qué aporta la detección de bordes

YOLO decide dónde están los niveles y qué estado tienen. El análisis adicional revisa cambios de intensidad, color y textura dentro de cada máscara. **Canny** es el algoritmo utilizado para marcar bordes, es decir, cambios de intensidad que pueden corresponder a contornos.

Este análisis muestra mapas para estudiar qué zonas activan la señal y dónde se confunde con carteles, estructuras o fondos. Es experimental: su área o ancho con señal todavía no equivale al porcentaje real de productos. Activarlo no cambia la clase elegida por YOLO.

El equipo comenzó este trabajo en la semana 9 y lo integró con YOLO en la semana 11. El inicio del proyecto se sitúa aproximadamente en agosto; las semanas son referencias del equipo.

## Otros términos que aparecen en las guías

| Término | Significado práctico |
|---|---|
| Oclusión | Una persona, carro o caja tapa parte del nivel. Puede impedir decidir el estado. |
| ROI | Región de interés: parte de la imagen que decidimos analizar o evaluar. |
| Confianza y umbral | Puntuación del modelo y valor mínimo para conservar una predicción. No indican porcentaje de ocupación. |
| NMS | Filtro que reduce predicciones muy superpuestas. Sus ajustes pueden afectar duplicados y niveles cercanos. |
| Deduplicación | Revisión o filtrado de predicciones repetidas sobre el mismo nivel. |
| Posprocesamiento | Operaciones realizadas después de la salida del modelo, como filtrar o numerar detecciones. |
| Snapshot o copia congelada | Versión guardada de datos y anotaciones para saber con qué ejemplos se hizo un ensayo. |
| Hash SHA-256 | Huella digital que permite comprobar si cambió el contenido de un archivo. No verifica que su etiqueta sea correcta. |
| Manifiesto | Lista de archivos y sus datos de control, como tamaño y hash. |
| Semilla o seed | Valor inicial que ayuda a repetir condiciones aleatorias. No garantiza resultados idénticos entre equipos. |
| Batch | Cantidad de imágenes que se procesan juntas en un paso del entrenamiento. |
| Latencia | Tiempo que tarda una operación; para el usuario importa el recorrido completo desde cargar la foto hasta ver el resultado. |
| MVP | Versión mínima con las funciones necesarias para comprobar que la solución resuelve el problema acordado. |

## Por dónde continuar

- Para probar fotos propias: seguir el [inicio del README](../README.md).
- Para instalar el laboratorio: seguir la [guía de réplica](Replicar_proyecto.md).
- Para subir y recibir mejoras del equipo: seguir la [guía de trabajo en equipo](Trabajo_en_equipo.md).
- Para preparar la presentación: revisar el [informe con los 20 casos](Informe_Intermedio_Avance_20261020.md) y la [relación con lo solicitado](Revision_de_requisitos_informe.md).
