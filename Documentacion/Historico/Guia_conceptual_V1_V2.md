# Guía para entender Walmart Computer Vision

> Archivo histórico: describe una etapa anterior. Consulta el [estado actual](../../README.md) para conocer la V3 local en pruebas.

Esta guía explica los conceptos necesarios para leer el README, interpretar el informe y participar en el proyecto. Está pensada para quienes están aprendiendo visión computacional. Los resultados, configuraciones y evidencias completas se mantienen en sus documentos de referencia.

**Revisada el 21 de octubre de 2026**, a partir de los ensayos y la entrega de Walmart Visión del 20 de octubre.

## Qué estamos construyendo

Queremos apoyar la revisión de góndolas a partir de fotografías. La aplicación busca cada nivel o repisa, dibuja su contorno y asigna un estado de disponibilidad. Por ejemplo, puede señalar cuatro niveles suficientes y uno que necesita reposición.

Walmart Visión incluye cuatro modelos entrenados: dos de V1 y dos de V2 base. Cada etapa utiliza estados distintos:

| Etapa | Estados | Situación actual |
|---|---|---|
| V1 | `vacio`, `baja_disponibilidad`, `suficiente`, `no_evaluable` | Modelos YOLO11-1 y YOLO26-1 disponibles en Visión. |
| V2 base | `reponer`, `suficiente` | Modelos V2-YOLO11 y V2-YOLO26 disponibles en Visión. Reúne vacío y baja disponibilidad en una misma acción: reponer. |
| V2 con visibilidad limitada | `reponer`, `suficiente`, `no_evaluable` | Preparación de datos con obstáculos; falta aprobación humana final, entrenamiento y validación. No hay un modelo de esta etapa en Visión. |

La aplicación trabaja con lo visible en una foto. No conoce las unidades que hay detrás de la primera fila ni las existencias de bodega. El criterio inicial del 30 % se usa para etiquetar disponibilidad según el ancho del nivel; todavía debe calibrarse. La confianza de YOLO y la señal experimental de bordes son valores distintos de ese criterio.

## Cómo se relacionan las tres interfaces

| Interfaz | Quién la utiliza | Qué hace y qué entrega |
|---|---|---|
| CVAT, anotación de imágenes | Equipo de desarrollo y personas que revisan etiquetas | Abren las fotografías, dibujan un polígono por nivel y asignan su estado. Esas anotaciones se revisan antes de usarse como ejemplos. |
| Panel del laboratorio | Equipo de desarrollo | Importa las anotaciones, comprueba datos y particiones, registra la revisión, entrena y compara modelos. Conserva pesos, configuración y resultados por ensayo. |
| Walmart Visión | Usuario de la aplicación | Carga una fotografía nueva y utiliza los pesos publicados para mostrar niveles y estados. No requiere anotar ni volver a entrenar. |

El proceso de construcción es **fotografías → anotación y revisión en CVAT → preparación y entrenamiento en el laboratorio → pesos publicados → análisis de fotos en Walmart Visión**. El usuario recibe los modelos entrenados junto con la aplicación.

La documentación explica los criterios de anotación, la separación de datos y las decisiones de entrenamiento para que una persona externa comprenda ese proceso. Instalar el panel o CVAT es opcional y corresponde a continuar el desarrollo; los datos, resultados y accesos del equipo se gestionan por separado. La distribución para usuarios finales incluye Visión y sus pesos.

La entrega actual es `Walmart_Vision_20261020.zip`. Se extrae y se abre con `iniciar.cmd`: el primer inicio necesita Internet para preparar su propio Python y las dependencias; después permite analizar fotos localmente sin conexión. Ofrece **Solo YOLO** y **YOLO + detección de bordes**, con las vistas **Original**, **Niveles**, **Bordes** y **Comparar**; Bordes se habilita con el segundo método. Se comprobó la inferencia desde el ZIP en el equipo de desarrollo; la instalación en otro computador físico sigue pendiente. Los pasos y el alcance de esa comprobación están en la [guía de usuario](../../Documentacion/Usar_Walmart_Vision.md).

Para profundizar sin instalar herramientas: [guía de anotación](../../Documentacion/Desarrollo/Guia_anotacion.md), [funcionamiento del panel](../../Herramientas/Modelos/README.md) y [mapa del código](../../Documentacion/Desarrollo/Evolucion_v1_v2.md#dónde-está-cada-parte-del-código).

## Delimitar un nivel y decidir su estado

**Detección** significa localizar algo en una imagen. **Segmentación** añade la forma de la región: en este proyecto buscamos el contorno completo del nivel, incluso cuando contiene espacios vacíos. La región coloreada resultante se llama **máscara**. Un **polígono** es la figura que dibujamos manualmente para indicar ese contorno durante el etiquetado.

**Clasificar** significa asignar una categoría. Un nivel puede estar bien delimitado y tener una categoría equivocada. Por eso revisamos ambas cosas: dónde dibujó el modelo y qué estado decidió.

**Inferencia** es usar un modelo ya entrenado para analizar una imagen. **Entrenar** es ajustar el modelo con ejemplos etiquetados. Los **pesos** son los archivos que guardan lo aprendido; en nuestros ensayos se conservan como archivos `.pt`. Un **checkpoint** es un guardado de esos pesos durante el entrenamiento.

La **confianza** es la puntuación que asigna el modelo a una predicción. Su **umbral** indica la puntuación mínima para mostrarla: subirlo puede quitar predicciones, incluidos niveles correctos. Una confianza de 0,80 no significa que el nivel tenga un 80 % de productos.

## Criterio de disponibilidad

### Estados y criterio inicial

El criterio original V1 distingue los cuatro estados siguientes; V2 base reúne los dos primeros en `reponer`. Analizamos cada nivel entre sus límites laterales y comparamos el ancho que tiene producto con el ancho completo disponible.

| Estado | Criterio |
|---|---|
| **Vacío** | No se ve producto del propio nivel y se puede comprobar todo su contenido. |
| **Baja disponibilidad** | Hay producto, pero ocupa menos del 30 % del ancho completo. |
| **Suficiente** | El producto ocupa el 30 % del ancho completo o más. |
| **No evaluable** | La visibilidad no permite decidir el estado. |

Contamos el producto visible al fondo del propio nivel. No contamos mercancía de un tramo vecino que aparezca por perspectiva. Una **oclusión** ocurre cuando una persona, carro u objeto tapa parte del nivel. Si el producto visible ya alcanza el 30 % del ancho completo, el estado es suficiente; si ni llenando la parte oculta lo alcanzaría, es reponer. Si lo oculto puede cambiar la decisión, usamos no evaluable. Tener un obstáculo no obliga por sí solo a elegir ese estado.

El polígono conserva el nivel completo, incluida la parte tapada, cuando sus límites pueden establecerse de forma fiable. A esto se le llama **criterio amodal**. La geometría puede apoyarse en el original verificado de una edición sintética, pero el estado se decide con el producto visible en la edición. La [guía de anotación](../../Documentacion/Desarrollo/Guia_anotacion.md#oclusiones-y-geometría) detalla este criterio. V2 base todavía no aprende el estado no evaluable.

“Suficiente” significa que supera nuestro umbral visual; no garantiza stock suficiente para la demanda ni presencia de todos los productos.

### Motivos de la decisión

- **Por nivel:** permite ubicar la zona que requiere revisión dentro de la góndola.
- **Por ancho ocupado:** evita considerar el aire sobre botellas o envases bajos como falta de producto. Es una simplificación que puede perder información sobre profundidad y apilamiento.
- **Con una guía común:** permite que todos anoten con las mismas reglas y que los ejemplos de entrenamiento sean coherentes.
- **Con un estado no evaluable:** evita tomar una zona tapada como evidencia de vacío.

Estas son decisiones de diseño del equipo, que debemos comprobar con datos reales.

### Respaldo bibliográfico y límites

**Jha y colaboradores (2022)** explican que el concepto de estante vacío puede resultar ambiguo y establecen reglas explícitas de anotación. Su trabajo respalda la necesidad de definir qué se marca y mantener un criterio consistente. Sus etiquetas son de huecos; no equivalen a nuestros estados por nivel. [Artículo, sección 5](https://arxiv.org/html/2205.13060v2#S5).

**Šikić y colaboradores (2024)** distinguen espacios completamente vacíos de espacios vacíos al frente con productos detrás. Esto respalda aclarar cómo tratamos el producto del fondo y qué entendemos por disponibilidad. [Artículo](https://pmc.ncbi.nlm.nih.gov/articles/PMC10819825/).

**Estas fuentes apoyan el enfoque general y la definición clara de las etiquetas. No demuestran que el 30 % sea el umbral correcto para nuestro proyecto.**

### Por qué se utiliza el 30 %

Lo adoptamos como una regla inicial, sencilla y común para separar presencia reducida de producto del resto de los niveles con producto.

**Es un umbral provisional del equipo. No lo presentamos como una norma de Walmart ni como un valor científicamente validado.** Para justificar su utilidad necesitamos contrastarlo con personas que conozcan la reposición y con fotos reales.

La validación propuesta es revisar la ocupación y la necesidad de reposición de manera independiente, y comparar alternativas como 20 %, 30 % y 40 %. Si el resultado favorece otro valor, habrá que actualizar el criterio y las etiquetas correspondientes.

### Cómo se comprueba el criterio y el modelo

Debemos comprobar dos cosas distintas:

1. **El criterio:** que las personas lo apliquen de forma consistente y que los estados sean útiles para la revisión de reposición.
2. **El modelo:** que encuentre los niveles y prediga correctamente sus estados en escenas que no usó para entrenar.

En la validación histórica V1, las cinco fotos no contienen niveles vacíos ni bajos. La validación V2 base incorpora una única referencia real de reposición; su cobertura de faltantes sigue siendo insuficiente para una estimación robusta. Que el modelo acierte fotos de entrenamiento no demuestra que funcione igual en otras góndolas.

### Explicación breve para presentar

> Nuestro proyecto identifica disponibilidad visual por nivel de góndola. Elegimos trabajar por nivel para ubicar posibles faltantes y usamos el ancho ocupado como una regla común para anotar. V1 distingue vacío, baja disponibilidad, suficiente y no evaluable; V2 base reúne vacío y baja en reponer y conserva suficiente. La etapa V2 con no evaluable sigue pendiente. La literatura respalda definir claramente los espacios vacíos y considerar si hay productos al fondo. El 30 % es un umbral inicial del equipo, pendiente de validación con casos reales y conocimiento de reposición. Nuestro objetivo es apoyar la revisión visual; no medir inventario exacto.

## Para qué sirve cada herramienta

| Herramienta | Su trabajo en el proyecto | Por qué la utilizamos |
|---|---|---|
| CVAT | Permite dibujar los niveles y asignar sus etiquetas. | Facilita que el equipo revise las mismas imágenes y corrija diferencias. |
| YOLO de segmentación | Aprende con los ejemplos y después dibuja y clasifica niveles. | Resuelve localización y estado con un mismo modelo; comparamos YOLO11 y YOLO26. |
| Ultralytics y PyTorch | Ejecutan el entrenamiento y el análisis con los modelos. | Permiten partir de pesos generales ya entrenados y adaptarlos a nuestras imágenes. |
| OpenCV, Pillow y NumPy | Preparan fotografías y calculan operaciones sobre sus píxeles. | Ayudan a orientar imágenes, trabajar con máscaras y calcular la señal de bordes. |
| Docker | Prepara un entorno con las dependencias del panel. | Facilita ejecutar el laboratorio con una configuración compartida. Los datos y pesos se instalan aparte. |
| Git y GitHub | Guardan cambios del código y permiten integrarlos entre compañeros. | Mantienen el historial y permiten revisar una mejora antes de incorporarla. |
| Walmart Visión (antes Walmart Lite) | Abre una interfaz local para probar los modelos. | Permite cargar fotografías propias sin instalar todo el laboratorio. |

La **CPU** es el procesador del computador. La **GPU** es la tarjeta gráfica y puede acelerar los cálculos cuando el entorno está configurado para utilizarla. Walmart Visión utiliza CPU en su entorno automático de Windows.

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

Cada ensayo conserva una **copia congelada de las anotaciones**, también llamada snapshot, junto con la partición y la configuración utilizadas. Esto permite identificar con qué ejemplos se entrenó. El lote de visibilidad limitada añade 60 ediciones con obstáculos y 308 niveles revisados técnicamente; todavía necesita aprobación humana final y no forma parte del entrenamiento V2 base.

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

Esos ejemplos corresponden a la **validación original de diez fotos reales**. El laboratorio conserva además una **evaluación ampliada de desarrollo** sobre esas diez fotos y sus treinta variantes sintéticas, sin volver a entrenar. Sus resultados están en `evaluacion_desarrollo.json` de cada ensayo V2 base y sirven para revisar errores y ajustar el sistema. Las cuarenta imágenes incluyen familias relacionadas: su resumen conjunto no sustituye la validación real ni acredita cuarenta capturas independientes. La reserva final sigue aparte y debe consultarse después de fijar modelo y ajustes. Ver el [procedimiento del panel](../../Herramientas/Modelos/README.md#evaluar-los-pesos-actuales-sobre-las-40-fotos-de-desarrollo).

**IoU** compara cuánto coinciden dos regiones, de 0 a 1. Se calcula como el área compartida dividida por el área total que cubren ambas. En nuestro informe se comparan máscaras. Un valor alto indica buen ajuste del contorno, aunque el estado todavía puede estar equivocado.

**mAP** resume la relación entre precisión y recall por clase. `mAP50` usa IoU 0,50; `mAP50–95` promedia umbrales de 0,50 a 0,95 en pasos de 0,05. En el informe mostramos métricas de máscaras. El 92,79 % de mAP50–95 no significa que el sistema acierte el 92,79 % de las fotos ni que detecte ese porcentaje de los faltantes de una tienda.

Para leer las cifras con más detalle, consultar las explicaciones de [métricas de Ultralytics](https://docs.ultralytics.com/guides/yolo-performance-metrics/), [validación](https://docs.ultralytics.com/modes/val/) y [segmentación](https://docs.ultralytics.com/tasks/segment/).

## Qué aporta la detección de bordes

YOLO decide dónde están los niveles y qué estado tienen. El análisis adicional revisa cambios de intensidad, color y textura dentro de cada máscara. **Canny** es el algoritmo utilizado para marcar bordes, es decir, cambios de intensidad que pueden corresponder a contornos.

La entrega actual incorpora la **revisión 2**, que combina bordes Canny, color y textura sobre la foto original dentro de las máscaras YOLO. Muestra mapas para estudiar qué zonas activan la señal y dónde se confunde con carteles, estructuras o fondos. Cuando no puede medir un nivel, informa el motivo. Es experimental: su área o ancho con señal todavía no equivale al porcentaje real de productos. Activarlo no cambia la clase elegida por YOLO. Los cambios y las comprobaciones están en la [revisión del algoritmo](../../Experimentos/Bordes/REVISION_20261020.md).

El equipo comenzó este trabajo en la semana 9 y lo integró con YOLO en la semana 11. El inicio del proyecto se sitúa aproximadamente en agosto; las semanas son referencias del equipo.

## Por dónde continuar

- Para probar fotos propias: seguir la [guía de Walmart Visión](../../Documentacion/Usar_Walmart_Vision.md).
- Para continuar el desarrollo e instalar el laboratorio: seguir la [guía técnica](../../Documentacion/Desarrollo/Replicar_proyecto.md).
- Para subir y recibir mejoras del equipo: seguir la [guía de trabajo en equipo](../../Documentacion/Desarrollo/Trabajo_en_equipo.md).
- Para preparar la presentación: revisar el [informe con los 20 casos](../../Documentacion/Informe_Intermedio_Avance_20261020.md) y la [relación con lo solicitado](../../Documentacion/Desarrollo/Revision_de_requisitos_informe.md).
