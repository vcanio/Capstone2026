# Plan de grabación y edición · Walmart Visión

Versión: 21 de octubre de 2026. Video nuevo desde cero; la edición del 20 de octubre se conserva como antecedente y no se reutiliza como grabación actual.

## Decisiones acordadas

- Público: profesores y cliente; explicación práctica y comprensible.
- Duración: 7–8 minutos; el requisito admite entre 5 y 10.
- Imagen: aplicación en pantalla, sin presentación personal ni cámara del equipo.
- Audio: voz facilitada por el usuario, sin música.
- Edición: subtítulos, rótulos breves y acercamientos puntuales para leer los resultados.
- Publicación prevista: YouTube no listado, enlazado desde el README. El enlace todavía no existe.

## Entregar al locutor

Usar el [guion de voz](Guion_locucion_20261021.md) o su [copia de texto](Guion_locucion_20261021.txt). Grabar diez archivos, uno por bloque, llamados `01.wav` a `10.wav`; también se acepta un audio completo o MP3 de buena calidad.

Se recomienda WAV a 48 kHz, mono o estéreo. Es una preferencia para editar, no un requisito para aceptar la grabación. Leer solo los párrafos; no leer títulos, números de bloque ni instrucciones. Pronunciar YOLO26 como «Yolo veintiséis» y V2 como «versión dos». Ritmo orientativo: 140–145 palabras por minuto, con pausas naturales. Dejar aproximadamente un segundo libre al inicio y al final. Si hay un error, repetir la oración dejando una pausa; no es necesario reiniciar todo el bloque.

La duración indicada es una estimación a partir del texto. Al recibir el audio se medirá su duración y se ajustarán las escenas; no acelerar la voz para encajar una tabla de tiempos. Si una frase cambia respecto del guion, actualizar también los subtítulos.

## Escenas que acompañan a cada bloque

| Bloque | Imagen y acción previstas | Evidencia que permite comprobar |
|---|---|---|
| 01 | Portada breve «Walmart Visión · Demostración funcional» y visor actual. Sin nombres ni presentación personal. | Propósito: disponibilidad visual por nivel. |
| 02 | Selección de V2 y V2-YOLO26; mostrar las opciones y la leyenda. Diagrama simple fotografía → YOLO → análisis de bordes → revisión. | Versiones y métodos efectivamente disponibles. |
| 03 | Grabación nueva: elegir una foto, revisar configuración, pulsar Analizar foto y abrir Niveles, Comparar y el detalle. | Recorrido funcional de entrada a resultado. Conservar una secuencia continua del inicio del análisis a su resultado. |
| 04 | Original, salida YOLO y mapa del caso B06. Acercar las dos repisas con faltantes, manteniendo una vista general para ubicarlas. | Caso favorable B06 del informe. Rótulo «Evidencia del informe · B06». |
| 05 | En la ejecución nueva, seleccionar YOLO + detección de bordes, volver a analizar y abrir Bordes y Mediciones de señal por nivel. | Vistas de señal, bordes y tabla. Rótulo «Señal experimental; no es ocupación real». |
| 06 | Original, YOLO y mapa del caso B08. Señalar las cuatro repisas del exhibidor. | Caso favorable B08 del informe. Rótulo «Evidencia del informe · B08». |
| 07 | Original y mapa F01, con un acercamiento al fondo vacío que activa señal. | Falsa activación del fondo; hipótesis y propuesta de mejora. Rótulo «Evidencia del informe · F01». |
| 08 | Original y YOLO F03, alternando ambas vistas. Marcar la repisa intermedia sin contorno, sin dibujar una predicción que el modelo no produjo. | Omisión del localizador y dependencia del análisis de bordes. Rótulo «Evidencia del informe · F03». |
| 09 | Resumen visual de funciones implementadas y dos prioridades de mejora. Vista del informe con los 20 casos. | Alcance actual y límites de la selección visual. |
| 10 | Ubicación de la entrega y guía en el repositorio; cierre breve. | Cómo acceder a la aplicación y las evidencias. La publicación se realiza después de terminar el video. |

Los cuatro casos se seleccionaron por claridad visual y diversidad de comportamiento, no por una clasificación numérica de calidad. Se usarán las figuras ya documentadas en el informe. Sus tablas originales no proporcionan registros suficientes para afirmar métricas nuevas del método combinado. Por eso la narración no anuncia porcentajes de precisión ni cantidades de producto.

## Fuentes de los cuatro casos

Todas las rutas siguientes son relativas a la raíz del repositorio. El [manifiesto de los veinte casos](../Evidencias/casos_yolo_bordes_20261021.json) conserva las descripciones y hashes.

| Caso | Entrada | YOLO | Señal de bordes |
|---|---|---|---|
| B06 · Vinos con dos repisas casi vacías | [Original](../Evidencias/casos_yolo_bordes_20261021/B06_original.jpg) | [Resultado](../Evidencias/casos_yolo_bordes_20261021/B06_yolo.jpg) | [Mapa](../Evidencias/casos_yolo_bordes_20261021/B06_bordes.jpg) |
| B08 · Bebidas en exhibidor central | [Original](../Evidencias/casos_yolo_bordes_20261021/B08_original.jpg) | [Resultado](../Evidencias/casos_yolo_bordes_20261021/B08_yolo.jpg) | [Mapa](../Evidencias/casos_yolo_bordes_20261021/B08_bordes.jpg) |
| F01 · Fondo metálico en una repisa vacía | [Original](../Evidencias/casos_yolo_bordes_20261021/F01_original.jpg) | [Resultado](../Evidencias/casos_yolo_bordes_20261021/F01_yolo.jpg) | [Mapa](../Evidencias/casos_yolo_bordes_20261021/F01_bordes.jpg) |
| F03 · Nivel omitido en alimento para mascotas | [Original](../Evidencias/casos_yolo_bordes_20261021/F03_original.jpg) | [Resultado](../Evidencias/casos_yolo_bordes_20261021/F03_yolo.jpg) | [Mapa](../Evidencias/casos_yolo_bordes_20261021/F03_bordes.jpg) |

Para el recorrido nuevo se puede cargar B06 como ejemplo conocido de desarrollo. Su resultado debe comprobarse en la versión que se grabe. No se presupone que una nueva ejecución reproduzca exactamente las capturas del informe, ya que estas no acreditan todos sus parámetros. Si difiere, conservar ambos resultados con su procedencia y ajustar la explicación. No usar la reserva final para preparar la demostración.

## Comprobación de captura en este equipo

Se inició la aplicación extraída de la entrega Docker del 21 de octubre, con CPU, en `http://127.0.0.1:8097`. El navegador integrado mostró la pantalla de inicio, las opciones V1/V2 y los modelos V2, el método combinado y las pestañas del visor. Esto confirma el acceso a la aplicación, todavía no una inferencia nueva ni una grabación terminada.

Se encontró OBS Studio instalado y se creó una escena vacía llamada `Walmart Vision - prueba 20261021`. No se inició una grabación. El control de la ventana de Brave se detuvo porque la herramienta no pudo verificar con seguridad su dirección. La prueba de grabación continua queda pendiente; no hay un clip nuevo verificado. La escena quedó sin fuentes y las escenas anteriores se conservaron.

Al retomar la prueba, capturar únicamente la ventana del visor. Revisar un clip corto antes de grabar el recorrido completo. El objetivo final es horizontal, 1920 × 1080, con texto legible. La configuración previa de OBS era vertical, por lo que debe prepararse un perfil adecuado o una captura alternativa antes de producir el material final. La voz se incorporará después desde los archivos entregados por el usuario.

## Edición y comprobación final realizadas

1. Se recibió y midió el audio humano (`410,59 s`), alineando las 997 palabras del guion con una coincidencia léxica de `98,80 %` y ajustando la línea de tiempo de las 32 escenas (`421,59 s` en total).
2. Se capturaron las vistas de la interfaz en ejecución local (entrega Docker del 21 de octubre en CPU) junto con una secuencia temporizada de 30 capturas consecutivas del recorrido de análisis sobre `B06_original.jpg` con `V2-YOLO26`.
3. Se montaron las escenas de uso y los cuatro casos del informe (`B06`, `B08`, `F01`, `F03`) mediante [`Laboratorio/Informes/generar_demostracion_video.py`](../../Laboratorio/Informes/generar_demostracion_video.py), identificando explícitamente las figuras del informe y las vistas experimentales de bordes.
4. Se generaron e incrustaron 94 bloques de subtítulos sincronizados en [`Subtitulos_Demostracion_20261021.srt`](Subtitulos_Demostracion_20261021.srt), además de rótulos y recortes ampliados verificados visualmente sin texto truncado.
5. Se exportó `Entregables/Demostracion_Funcional_Walmart_Vision_20261021.mp4` (`1920 × 1080`, `25 fps`, H.264 y AAC a `48 kHz`), comprobando decodificación íntegra sin errores, sincronía y duración de `7 min 01 s` (dentro del rango requerido de 5–10 minutos). El detalle consta en [`verificacion_demo_video_20261021.json`](../Evidencias/verificacion_demo_video_20261021.json).
6. Queda únicamente a cargo del usuario subir el archivo `Entregables/Demostracion_Funcional_Walmart_Vision_20261021.mp4` a YouTube como no listado y pegar la URL resultante si desea enlazarla en línea.
