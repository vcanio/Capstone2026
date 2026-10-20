# Guía paso a paso para mejorar el modelo

Fecha: 15 de octubre de 2026. Aplicada al proyecto Walmart de niveles de góndola y disponibilidad.

**Sí: podemos tomar el modelo que ya entrenamos y volver a entrenarlo con más imágenes marcadas. Para esta siguiente ronda, usaremos los datos anteriores corregidos más los nuevos, conservando fotos separadas para evaluar.**

El ciclo de trabajo es:

**Encontrar errores → reunir ejemplos → marcar y revisar → preparar los datos → entrenar otra versión → comparar.**

Subir una foto a **Probar una foto** solo permite analizarla. El modelo no aprende automáticamente de ella.

## 1. Guardar ejemplos de los errores

Prueba el modelo actual y guarda la foto original de cada caso que quieras mejorar. Anota qué debería haber hecho.

| Error que observas | Qué registrar |
|---|---|
| No encuentra un nivel | Qué nivel falta, por ejemplo: inferior derecho. |
| Marca dos veces el mismo nivel | Qué detecciones corresponden al mismo nivel y qué estados les asigna. |
| Encuentra el nivel, pero confunde su estado | Estado esperado y motivo según la guía de anotación. |
| Marca un cartel como nivel | Qué elemento confundió con una repisa. |
| El contorno queda mal | Qué borde se sale o qué parte del nivel falta. |

Conserva también ejemplos donde funciona bien: servirán para comprobar que la nueva versión mantiene esos aciertos.

## 2. Reunir más fotos de esas situaciones

Busca otras fotos parecidas al problema, pero con variedad de tramos, productos, ángulos e iluminación. Repetir muchas veces la misma foto no sustituye escenas diferentes.

Para nuestro proyecto conviene priorizar:

- Niveles realmente vacíos y con baja disponibilidad.
- Niveles tapados cuyo estado no pueda decidirse.
- Niveles vacíos junto a tramos con productos, especialmente con perspectiva.
- Carteles y otras estructuras horizontales que se confundan con niveles.
- Niveles suficientes, para conservar ejemplos de funcionamiento habitual.

Guarda los originales nuevos en la carpeta de imágenes del lote. En `Datos/V2/lider_express_20261016/imagenes_ordenadas/`, los originales se identifican por `*_0_original.jpg` y conviven con variantes IA; usa el inventario para seleccionar únicamente las fotos reales. Registra archivo original, local, fecha, tramo físico y SHA-256 en su inventario, y enlaza el lote en `Datos/Registros/lotes.json`. Las 59 fotos de Líder Express se asignaron a anotación en la tarea 19 el 17 de octubre de 2026, con reparto 80/80/76 (originales y variantes). Su [guía específica](Guia_anotacion_lider_express_20261016.md) usa reponer, suficiente y no_evaluable. Sigue el [flujo común](../Datos/README.md).

**No hay una cantidad de fotos que garantice la mejora.** El [plan de captura del equipo](Guia_mejora_modelo_paso_a_paso.md) propone 40 por persona como primera ronda; lo importante es cubrir los errores con ejemplos útiles y revisados.

## 3. Separar las fotos para aprender y para comprobar

Antes de entrenar, divide los datos en dos grupos:

| Grupo | Para qué sirve |
|---|---|
| Entrenamiento | El modelo aprende de estas fotos y sus anotaciones. |
| Validación | Comparamos versiones con fotos que no se usan para ajustar directamente sus pesos. |

Como orientación, el plan propone reservar aproximadamente una cuarta parte de las **escenas nuevas** para validación. Comprueba que incluya vacíos, bajos, suficientes y no evaluables.

Todas las vistas de un mismo tramo físico, sus recortes y sus variantes deben quedar en el mismo grupo. Si una foto casi igual aparece en ambos, la evaluación puede parecer mejor de lo que realmente es.

Mantén las cinco fotos actuales de validación fuera del entrenamiento y conserva aparte la reserva final. Si usas una foto para decidir ajustes, considérala parte del desarrollo, no una prueba final independiente.

## 4. Marcar las fotos en CVAT

Usa el mismo esquema del proyecto: etiqueta **Nivel**, polígono completo y estado. Sigue la [guía de anotación v1.3](Guia_anotacion_CVAT.md).

| Estado | Regla sencilla |
|---|---|
| Vacío | No hay producto visible del propio nivel y puedes comprobarlo completo. |
| Baja disponibilidad | Hay producto, pero ocupa menos del 30 % del ancho completo. |
| Suficiente | El producto ocupa el 30 % del ancho completo o más. |
| No evaluable | La visibilidad no permite decidir el estado. |

Marca todos los niveles de los tramos completos elegidos, incluidos los que el modelo ya detecta bien. El polígono rodea todo el espacio del nivel, incluidos los huecos; no solo los productos.

Cuenta producto visible al fondo **del propio nivel**. Los productos de un tramo vecino que aparecen por perspectiva no cambian su estado. Si no puedes decidir a qué nivel pertenecen y eso cambia la clasificación, deja el caso para revisión.

Si usas predicciones para adelantar el marcado, corrígelas antes de aceptarlas. Un nivel físico debe tener una anotación y un estado, aunque el modelo proponga dos.

## 5. Revisar las etiquetas anteriores y las nuevas

Pide una segunda revisión de los vacíos, bajos y casos próximos al 30 %. Resuelve los estados pendientes y comprueba que los contornos sigan el mismo criterio.

Corrige una etiqueta cuando contradiga la evidencia y la guía; no la cambies solo porque el modelo prediga otra cosa.

Por ejemplo, en el diagnóstico de **REAL_03** se confirmó que los paquetes del extremo derecho pertenecían al tramo vecino. Se mantuvo vacío en el nivel inferior derecho. Ese caso sirve para enseñar pertenencia espacial; no hay que cambiarlo a baja solo para coincidir con la predicción.

## 6. Preparar una versión con los datos anteriores más los nuevos

La nueva versión debe reunir:

- Las fotos anteriores de entrenamiento que sigan siendo útiles, con sus etiquetas revisadas.
- Las fotos nuevas destinadas al entrenamiento, con sus etiquetas revisadas.
- La validación separada, con sus anotaciones y escenas identificadas.

**Este paso requiere preparación técnica en el laboratorio actual.** Crear una carpeta o una tarea nueva en CVAT no incorpora automáticamente sus imágenes al panel. Hay que registrar la procedencia de las fotos y preparar una versión ampliada; el importador actual no ofrece una fusión automática de la tarea 16 con cualquier tarea nueva.

Una vez registrado el lote y preparado el importador: guarda en CVAT, actualiza las tareas en **Preparar datos**, trae las anotaciones, revisa el informe y aprueba la copia correspondiente. Selecciona después esa versión ampliada al entrenar.

El catálogo de lotes está en Datos/Registros/lotes.json. Para una tarea nueva hay que registrar IDs, rutas, hashes y escenas compatibles con el importador. El flujo actual reconoce las fuentes históricas y la tarea 16; la incorporación de otra tarea necesita adaptar su registro antes de importarla. La tarea nueva debe conservar el esquema Nivel y estado de la guía vigente.

## 7. Crear un entrenamiento desde el modelo actual

Con la versión ampliada lista, entra en **Entrenar**:

1. Escribe un nombre nuevo, por ejemplo `YOLO26_mejora_02`.
2. En **Datos de entrenamiento**, selecciona la copia ampliada y revisada.
3. En **Modelo de partida**, elige el modelo del proyecto que quieras mejorar: YOLO11-1 o YOLO26-1, preferiblemente sus pesos **Mejor (best)**.
4. Si no ves los pesos, activa **Mostrar todas las versiones y pesos** en **Gestionar modelos**.
5. Comprueba que el texto de ayuda indique que continúa desde los pesos de ese ensayo.
6. Registra los ajustes e inicia el nuevo entrenamiento. Conserva el ensayo anterior.

El archivo `best.pt` guarda una versión de lo aprendido. Partir de él para entrenar con el conjunto ampliado se llama **ajuste fino**. No necesitas empezar desde el modelo general cada vez.

No aumentes las épocas como primera respuesta a cualquier error. Primero mejora los datos y comprueba resultados. Para una primera comparación, conserva la resolución y evita cambiar muchos ajustes a la vez; la tasa de aprendizaje y la duración pueden necesitar ajuste según la validación.

Esto es un ensayo nuevo. **Reanudar un entrenamiento interrumpido** es otra operación: continúa un trabajo que quedó a medias.

## 8. Tratar los niveles duplicados como una comprobación aparte

Si aparecen dos contornos sobre el mismo nivel, puede haber confusión entre estados y también un problema en el filtro que elimina detecciones superpuestas.

En el proyecto ya se observaron predicciones de vacío y baja sobre una misma región. Se probó un filtro que compara superposiciones aunque las clases sean distintas: eliminó el duplicado de REAL_03. Esa prueba no está aplicada como solución general al panel.

El siguiente paso técnico es probar ese filtro en varias escenas y comprobar dos cosas: que reduzca duplicados y que conserve los niveles vecinos reales.

**Eliminar el duplicado no garantiza acertar el estado.** Se puede dejar una sola detección y conservar la clasificación equivocada.

También puedes explorar la confianza en **Ajustes de detección**: subirla oculta candidatos débiles y puede ocultar niveles reales; bajarla deja pasar más candidatos y también más errores. Cambiarla no reentrena el modelo ni corrige por sí solo lo aprendido.

## 9. Comparar el modelo anterior y el nuevo

Evalúa ambos sobre la misma validación, con los mismos filtros y la misma región de análisis. Si amplías la validación, vuelve a evaluar también el modelo anterior en ella; no compares directamente porcentajes de conjuntos diferentes.

Revisa los resultados por foto y completa una tabla como esta:

| Qué comprobar | Modelo anterior | Modelo nuevo |
|---|---|---|
| Niveles que no encuentra | | |
| Niveles duplicados | | |
| Estados equivocados | | |
| Vacíos o bajos que no señala como alerta | | |
| Alertas incorrectas en niveles suficientes | | |
| No evaluables que reconoce correctamente | | |
| Tiempo de análisis por foto | | |

Elige la nueva versión si mejora los errores importantes y conserva un resultado aceptable en los demás casos. Si empeora, conserva la anterior y usa los nuevos errores para decidir la siguiente ronda.

**Nuestra prioridad actual:** los dos ensayos se entrenaron con 86 fotos y se validaron con 5 reales. Esas cinco contienen 34 niveles suficientes y 2 no evaluables, pero ningún vacío ni bajo. Necesitamos ampliar esa evaluación para comprobar la detección de faltantes en escenas nuevas.

## 10. Ejemplos concretos: fotos 11 y 25

Revisión de los originales y de las etiquetas exportadas para YOLO26-1, realizada el 15 de octubre de 2026. Ambas fotos ya participaron en el entrenamiento. Lo siguiente documenta qué revisar; no modifica CVAT ni los datos históricos del ensayo.

Los números que muestra el panel identifican predicciones de esa foto: pueden cambiar si aparece un nivel antes omitido. Para ubicar una corrección en CVAT, usa también su posición física.

### Foto 11: falta el nivel inferior izquierdo

La referencia usada para entrenar incluye ese nivel y lo clasifica como **baja disponibilidad**. La foto tiene 10 niveles anotados en los dos tramos centrales; la captura del resultado muestra 9 detecciones.

**Qué hacer:**

1. Comprobar en CVAT que ese polígono y su estado siguen correctos. Si ya están bien, conservarlos: no hay que dibujar otra anotación encima.
2. Comprobar en desarrollo si otra confianza o resolución permite recuperar el nivel. Si aparece, verificar también su estado y los errores adicionales; encontrarlo no basta para dar el ajuste por bueno.
3. Reunir otras escenas con niveles inferiores casi vacíos y producto en un extremo, marcando el nivel completo como corresponda.
4. Entrenar con el conjunto ampliado y comprobar la mejora en escenas distintas. Añadir de nuevo la misma foto no crea un ejemplo nuevo ni una evaluación independiente.

Aquí el nivel **sí se enseñó**, pero el modelo no lo muestra en esa predicción. Tener una anotación correcta no garantiza que siempre la reproduzca.

### Foto 25: estados equivocados en las detecciones 4 y 2

En la captura, señalas estas correcciones:

| Posición física | Predicción mostrada | Estado que indicas |
|---|---|---|
| Segundo nivel desde abajo, tramo derecho; detección 4 | Suficiente | Baja disponibilidad |
| Nivel inferior del tramo derecho; detección 2 | Baja disponibilidad | Vacío |

**Hallazgo:** en la copia usada para entrenar, ambos polígonos tienen la clase **suficiente**. REAL_25 contiene 12 anotaciones: 11 suficientes y un vacío, correspondiente al nivel inferior izquierdo. Por tanto, hay una discrepancia entre las referencias de entrenamiento y los estados que señalas.

**Qué hacer:**

1. Abrir la foto original en CVAT y localizar esos dos polígonos.
2. Revisar el ancho ocupado por producto del propio nivel y los límites del tramo. Los productos de la estantería vecina no cuentan para ese nivel.
3. Confirmados tus estados con la guía, cambiar el segundo nivel derecho desde abajo de **suficiente a baja_disponibilidad**, y el inferior derecho de **suficiente a vacio**. Mantener el contorno completo si está bien dibujado.
4. Revisar otras etiquetas con el mismo problema, para evitar ejemplos contradictorios.
5. Guardar, traer las anotaciones a una copia nueva, revisarla y entrenar un ensayo nuevo con las correcciones y más ejemplos similares.

Editar CVAT no cambia el modelo ya entrenado. El cambio entra en el aprendizaje cuando se usa la copia corregida en un entrenamiento nuevo. Tampoco hay que editar los archivos guardados del ensayo anterior: conservan lo que ese modelo recibió.

### Cómo aplicar esto a los demás casos

La primera pregunta para cada error es: **¿la anotación usada para entrenar estaba correcta?**

| Caso | Acción inicial | Cómo reforzarlo |
|---|---|---|
| Falta un nivel y tampoco estaba anotado | Añadir su polígono y estado en la fuente de anotaciones. | Revisar que no falten otros niveles objetivo. |
| Falta un nivel que sí estaba bien anotado | Conservar la etiqueta y revisar filtros, resolución y dificultad de la escena. | Incorporar escenas similares y evaluar otra versión. |
| Estado equivocado y etiqueta de entrenamiento incorrecta | Corregir el estado según la guía. | Auditar casos similares y entrenar con la copia corregida. |
| Estado equivocado aunque la etiqueta era correcta | Conservarla. | Añadir ejemplos variados del estado correcto y otros que ayuden a distinguirlo. |
| Dos predicciones del mismo nivel | Comprobar que exista una sola anotación de ese nivel. | Evaluar el filtro de superposiciones y las confusiones entre estados. |
| Cartel confundido con nivel | No anotarlo como Nivel; comprobar los niveles reales de esa imagen. | Añadir escenas con carteles y repisas correctamente anotadas. |
| Contorno equivocado | Revisar primero el polígono de referencia. | Corregirlo si hace falta y añadir otras perspectivas. |
| Contenido imposible de decidir por ocultación | Aplicar no_evaluable cuando corresponda. | Incluir ejemplos revisados de ese estado. |

Después de corregir, compara siempre con escenas separadas del entrenamiento. Que mejore una foto conocida comprueba ese caso; no demuestra por sí solo que se corrigieron todos los parecidos.

## Lista para cada ronda

- [ ] Guardamos errores concretos y ejemplos donde funciona bien.
- [ ] Reunimos escenas nuevas y variadas, especialmente casos críticos reales.
- [ ] Separamos entrenamiento y validación por tramo físico.
- [ ] Marcamos y revisamos los niveles con el mismo criterio.
- [ ] Preparamos una versión ampliada con datos anteriores corregidos y datos nuevos.
- [ ] Entrenamos un ensayo nuevo desde el `best.pt` elegido.
- [ ] Comprobamos los duplicados sin asumir que reentrenar los resolverá todos.
- [ ] Comparamos ambos modelos sobre las mismas fotos y con los mismos filtros.
- [ ] Registramos el resultado y conservamos la versión anterior.

## Capturar escenas nuevas

La propuesta inicial es de 40 fotos útiles por persona, preferentemente en locales distintos: 12 con un vacío confirmado, 12 con baja disponibilidad, 12 suficientes y cuatro no evaluables. Para tres personas son 120 fotos. Es una orientación para ampliar cobertura, no una cantidad que garantice precisión. Cada foto cuenta una vez para la cuota; después se anotan todos los niveles de los tramos elegidos y se cuentan por clase, escena, local y partición.

Priorizar encuadres frontales o casi frontales, nítidos, con ancho completo, límites y detalle de productos al fondo. Usar la cámara normal y el archivo original. Cubrir varias familias de productos, locales, horarios y condiciones; registrar las carencias sin cambiar etiquetas para cumplir cuotas. Conservar la mejor toma de encuadres casi idénticos. Otras visitas, recortes y variantes del mismo tramo permanecen en su grupo de escena.

Registrar nombre original, local, fecha, autor cuando se conozca, escena física, objetivo provisional y fuente celular o cámara. El inventario común añade dimensiones y SHA-256. Usar la convención vigente de [Datos](../Datos/README.md), como lider_express_001.jpg; no crear nombres de clase en el archivo. El objetivo de búsqueda no sustituye el estado revisado en CVAT.

Como orientación de pilotaje, separar aproximadamente una cuarta parte de las escenas nuevas para validación de desarrollo, con casos críticos presentes. No repartir cada cuarta foto al azar. La reserva final sigue independiente. Las pruebas con celular no demuestran transferencia a cámaras de seguridad; esa evaluación requiere imágenes reales del entorno previsto.

Las 59 fotos de Lider Express están asignadas a anotación en la tarea 19: 20 para Canio, 20 para Guerra y 19 para Vilches. Este reparto no define su partición de entrenamiento, validación o evaluación; sus grupos de escena siguen pendientes de identificar.

## Demostrar y explicar el proyecto

Para una demostración breve: explicar el criterio, mostrar una anotación de CVAT, analizar una foto con cada modelo, revisar un acierto y una limitación y presentar qué se mejorará en la siguiente ronda. Aclarar si la foto fue usada para entrenar. Subirla al panel realiza inferencia y no cambia los pesos.

El prototipo predice disponibilidad visual, sin consultar inventario ni contar unidades exactas. La validación actual carece de vacíos y bajos: mostrar una predicción no demuestra precisión sobre faltantes nuevos. La [defensa del criterio](Defensa_criterio_disponibilidad.md) contiene la explicación para presentar y la [revisión de la primera pasada](Revision_primera_pasada_20261016.md) conserva la evidencia y el siguiente experimento recomendado.

## Referencias

- [Guía para marcar en CVAT](Guia_anotacion_CVAT.md).
- [Uso del panel](../Herramientas/Modelos/README.md).
- Diagnóstico de omisión, duplicado y perspectiva en REAL_03 (archivo local histórico, fuera de la distribución).
- [Revisión de YOLO11-1](../Experimentos/YOLO11-1_20261015_013749_f709/REVISION_MODELO.md) y [comparación con YOLO26-1](../Experimentos/YOLO26-1_20261015_021212_c452/REVISION_MODELO.md).
- [Ultralytics: ajuste fino desde pesos entrenados](https://docs.ultralytics.com/guides/finetuning-guide).
