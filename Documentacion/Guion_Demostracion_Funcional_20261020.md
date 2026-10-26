# Guion de la demostración funcional de Walmart Visión

Video de ejecución real editada, con narración sintética en español de Chile y subtítulos. Corte: 20 de octubre de 2026.

Es un montaje que incluye una secuencia continua del análisis y la comparación, junto con capturas ampliadas. Se recortan esperas; no se simulan resultados ni se modifica la aplicación. No constituye una nueva medición de precisión.

Configuración: V2-YOLO26, CPU, confianza 0,25. Tres fotografías reales de validación: 040, 015 y 042. Para 040 se ejecutaron Solo YOLO y YOLO + detección de bordes. La comparación de omisiones y extras de 042 procede de su evaluación conservada.

## 00:00:00 · Walmart Visión · Demostración funcional

Esta es una demostración funcional de Walmart Visión, el proyecto de Vicente Canio, Paulo Guerra y Vicente Vilches. Mostraremos lo que actualmente permite hacer la aplicación: cargar una fotografía de góndola, localizar sus niveles, revisar su estado y explorar un análisis experimental de bordes. El video utiliza capturas de una ejecución real, editadas y narradas para explicar los resultados.

## 00:00:25 · 01 · Elegir versión y modelo

La selección de versión determina los modelos y los estados disponibles. V1 distingue vacío, baja disponibilidad, suficiente y no evaluable. V2 base agrupa vacío y baja disponibilidad en reponer, y conserva suficiente. La aplicación incluye modelos YOLO once y YOLO veintiséis para ambas versiones. En esta demostración utilizaremos V2 con YOLO veintiséis. V2 base todavía no reconoce el estado no evaluable.

## 00:00:54 · 02 · Cargar una fotografía real

Cargamos la fotografía real identificada como cero cuarenta. Podemos seleccionar el archivo desde el equipo o arrastrarlo al visor. La imagen queda lista para analizar. En las anotaciones conservadas del proyecto, este ejemplo tiene cinco niveles: cuatro suficientes y uno que requiere reposición. Esa referencia procede del conjunto de validación; la aplicación de usuario solamente recibe la fotografía y no carga sus etiquetas.

## 00:01:21 · 03 · Revisar la configuración

Para la primera predicción elegimos Solo YOLO y una confianza mínima de cero coma veinticinco. El ajuste de confianza filtra predicciones según el puntaje del modelo. No indica qué porcentaje de productos hay en una repisa. La inferencia se ejecuta localmente en el procesador del computador, usando pesos ya entrenados. No necesitamos iniciar CVAT ni volver a entrenar para probar una fotografía.

## 00:01:47 · 04 · Ejecutar el análisis

Al pulsar Analizar foto, la interfaz muestra el procesamiento y bloquea temporalmente los controles. El modelo busca cada nivel de la góndola, dibuja su contorno y predice su estado. La primera ejecución puede tardar más mientras carga los pesos. Las esperas se han recortado en esta edición; los tiempos que aparecen en el visor corresponden a estas ejecuciones concretas.

## 00:02:11 · 05 · Leer el resultado de reposición

La aplicación encontró cinco niveles. Cuatro aparecen como suficientes y uno como reponer, por lo que el resumen informa un nivel con posible faltante. Cada región se numera y se colorea sobre la fotografía. En este ejemplo, la cantidad de niveles y sus estados coinciden con la referencia documentada. Esta coincidencia comprueba el caso mostrado; no permite concluir que todas las fotografías tendrán el mismo resultado.

## 00:02:38 · 06 · Comparar original y predicción

La pestaña Comparar coloca la foto original junto a la predicción. Esto permite revisar si los contornos siguen las repisas y si el estado tiene sentido visualmente. Aquí se observa el nivel cuatro marcado en rojo como reponer. Los otros cuatro están señalados en verde. Este recorrido apoya la inspección humana y hace visible la evidencia que origina la alerta.

## 00:03:01 · 07 · Consultar el detalle por nivel

Al desplegar Detalle de los niveles, vemos el estado y la confianza de cada detección. El nivel cuatro tiene un puntaje de sesenta y tres por ciento; ese valor expresa confianza de la predicción, no ocupación del nivel. La interfaz también prepara una imagen del resultado mediante Descargar resultado. Las fotografías se procesan en memoria y no se incorporan automáticamente a un entrenamiento.

## 00:03:26 · 08 · Cambiar el método de análisis

Ahora elegimos YOLO más detección de bordes. Al cambiar el método, la aplicación limpia la predicción anterior y pide analizar de nuevo. Este comportamiento evita mostrar un resultado antiguo asociado a una configuración nueva. La función adicional estudia bordes, color y textura dentro de las regiones que encontró YOLO. Su señal es experimental y no sustituye la clasificación del modelo.

## 00:03:52 · 09 · Revisar el mapa de señal

Tras ejecutar el método combinado se habilita Bordes. El mapa resalta en amarillo la señal activada dentro de los niveles. En esta ejecución se conservan los cinco niveles y la misma alerta de reposición. El mapa ayuda a explorar qué zonas activan el algoritmo, pero no representa un porcentaje validado de productos. Fondos con textura, carteles y estructuras de la góndola también pueden producir señal.

## 00:04:18 · 10 · Inspeccionar los contornos

El selector ofrece una vista de bordes dentro de los niveles. Aquí se muestran los contornos limitados a las regiones detectadas. Esta vista permite estudiar la respuesta del análisis sobre productos, espacios y estructuras. Su utilidad actual es revisar el comportamiento del algoritmo y detectar fuentes de error. La necesidad de reposición continúa determinada por el estado que predice YOLO.

## 00:04:43 · 11 · Ver los bordes de la fotografía

También podemos ver los bordes de toda la fotografía. Al comparar ambas vistas distinguimos la información de la escena completa de aquella que queda dentro de cada máscara. Esto hace posible revisar visualmente el procesamiento ya implementado. Un contorno visible por sí solo no identifica un producto ni confirma su disponibilidad. Para interpretar el resultado debemos mantener esa diferencia.

## 00:05:08 · 12 · Consultar las mediciones de señal

La tabla Mediciones de señal por nivel presenta área y ancho con señal activada. En el nivel cuatro aparecen valores distintos para área y ancho, porque describen propiedades diferentes de la señal. Ninguno debe leerse como cantidad real de mercadería. La propia interfaz conserva esta advertencia y mantiene el estado de YOLO. Calibrar estas mediciones requiere una evaluación adicional con referencias adecuadas.

## 00:05:34 · 13 · Probar disponibilidad suficiente

Cambiamos a otra fotografía real, la cero quince, y repetimos Solo YOLO con el mismo modelo y confianza. La aplicación devuelve seis niveles suficientes y ninguna alerta de reposición. La referencia conservada también contiene seis niveles suficientes. Con este ejemplo comprobamos que el flujo permite analizar otra entrada y generar un resumen distinto, sin mantener las predicciones de la imagen anterior.

## 00:06:00 · 14 · Mostrar un caso con errores

La tercera fotografía real es la cero cuarenta y dos. El modelo devuelve seis predicciones suficientes. Sin embargo, la referencia del proyecto contiene tres niveles en el tramo anotado. Por eso un resumen sin alertas no garantiza una detección correcta. Debemos revisar dónde aparecen las regiones y contrastarlas con una referencia, cuando esté disponible. La aplicación no calcula precisión a partir de una foto sin etiquetas.

## 00:06:28 · 15 · Explicar la limitación observada

En la evaluación conservada de esta imagen, un nivel de referencia quedó omitido y cuatro predicciones no tuvieron correspondencia en el tramo anotado. La vista Comparar permite observar regiones sobre zonas vecinas y examinar sus contornos. Estas diferencias muestran una limitación actual. El ejemplo sirve para explicar por qué seguimos necesitando revisión humana y mejoras en la detección; no atribuimos una causa específica sin comprobarla.

## 00:06:55 · 16 · Alcance de lo demostrado

Los tres ejemplos pertenecen a validación y ya eran conocidos durante el desarrollo. Los usamos para comprobar el recorrido de la aplicación, no para estimar precisión global ni para reemplazar la prueba final. El prototipo trabaja con disponibilidad visual por nivel. No cuenta unidades por producto, no consulta inventario de bodega y no mide profundidad. V2 de tres estados y la validación en otro computador siguen pendientes.

## 00:07:23 · 17 · Avances comprobados y próximo paso

Queda demostrado el flujo implementado: cargar una foto, elegir versión y modelo, ejecutar inferencia y revisar máscaras, estados y confianza. También funcionan la comparación visual y los mapas experimentales de bordes. Mostramos un caso con reposición, otro suficiente y un caso con errores. Los próximos pasos son ampliar faltantes reales, completar la revisión de oclusiones y realizar la evaluación final con datos reservados.

## Evidencia y límites

- Aplicación ejecutada desde `.publicacion/vision_qa/extracted/Walmart_Vision`, extraída de la entrega del 20 de octubre.
- Foto 040: 5 detecciones; 4 suficientes y 1 reponer. Mismos estados y confianzas visibles con ambos métodos.
- Foto 015: 6 detecciones suficientes y 0 alertas.
- Foto 042: 6 detecciones suficientes. La evaluación conservada documenta 1 omisión y 4 predicciones sin correspondencia en el tramo de referencia.
- V1 se muestra para comprobar la selección de estados y modelos; no se atribuye una inferencia V1 a estas capturas.
- La imagen del resultado 040 se comprobó a partir del enlace de descarga generado. El navegador no notificó la finalización de la descarga; el video solo indica que la imagen está preparada.
- No se consultó la reserva final. No se acredita instalación en otro equipo ni calibración de ocupación.

Fuentes locales: [guía de uso](Usar_Walmart_Vision.md), [imágenes y referencias](Historico/Uso_Walmart_Vision_V2.md#probar-con-imágenes-de-ejemplo), [informe](Informe_Intermedio_Avance_20261020.md).
