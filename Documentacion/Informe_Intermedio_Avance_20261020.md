# Informe intermedio de avance
## Walmart Computer Vision

**Corte:** 20 de octubre de 2026, hora de Santiago. **Destinatario:** José Larraín. **Docente guía:** Arturo Vargas, DUOC UC.

**Equipo:** Vicente Canio, Paulo Guerra y Vicente Vilches.

El prototipo permite preparar datos, anotar niveles de góndola, entrenar modelos de segmentación y analizar fotografías desde un panel local. Se conservan cuatro ensayos completos: dos V1 de cuatro estados y dos V2 base de dos estados. La principal tarea pendiente es validar el manejo de oclusiones y demostrar la detección de faltantes con más fotografías reales independientes.

| Indicador verificado | Resultado al corte |
|---|---|
| Imágenes propias únicas | 405: 96 reales y 309 sintéticas |
| Datos usados en V1 | 86 entrenamiento y 5 validación real |
| Datos usados en V2 base | 160 entrenamiento y 10 validación real |
| Mejor mAP50–95 de máscaras V2 | 92,79 %, YOLO26n, sobre 10 fotos reales |
| Alertas reales de validación V2 | 1 acertada de 1; cero falsas en YOLO26n |
| Modelos V2 de tres estados | Pendientes de entrenamiento y evaluación |

La única alerta real de validación permite comprobar un caso, pero no estimar de forma sólida la sensibilidad ante faltantes en una tienda. Los ejemplos de entrenamiento y las variantes sintéticas se identifican por separado. La validación se usa para seleccionar modelos y no constituye una prueba final ciega.

El alcance es disponibilidad visual por nivel en fotografías estáticas. El sistema asigna un estado aprendido; no mide inventario de bodega, profundidad, unidades por SKU ni un porcentaje continuo de ocupación. El umbral del 30 % sigue siendo un criterio inicial de anotación pendiente de calibración con el cliente.

**Contenido:** estado y planificación; documentación técnica; resultados preliminares y 20 casos visuales; reproducibilidad y GitHub; conclusiones y plan de mejora.


<!-- page -->

## 1 Estado de avance del proyecto

Los porcentajes siguientes son estimaciones de ingeniería basadas en cuatro hitos de igual peso por módulo. Cada hito cerrado aporta 25 puntos. La media es 77,8 % (28 de 36 hitos); no representa precisión del modelo ni esfuerzo restante.

| Módulo | Hitos cerrados | Avance y estado | Evidencia |
|---|---|---|---|
| Datos | Captura, inventario, integridad | 75 % en desarrollo | Datos/Registros/lotes.json |
| Anotación colaborativa | Compose, tareas, usuarios, acceso privado | 100 % implementado | Infraestructura/CVAT y tareas 16, 19, 22 |
| Partición | Familias, grupos, listas, verificación | 100 % implementado | Particiones/lider_express_v2_20261019 |
| Importación y exportación | Lectura, revisión, versión, YOLO-Seg | 100 % implementado | datos_modelos.py y conjuntos.py |
| Modelos base | V1 YOLO11/26, V2 base YOLO11/26 | 100 % para esta etapa | Cuatro ensayos en Experimentos |
| Panel | Carga, inferencia, comparación | 75 % en desarrollo | panel_modelos.py y panel_worker.py |
| Distribución | Docker, arranque, Lite V1 | 75 % en desarrollo | Infraestructura/Docker y Entregables |
| Oclusiones V2 | Lote y partición preparados | 50 % en desarrollo | 60 imágenes y tarea 22 |
| Cierre de calidad | Diagnóstico de errores | 25 % en desarrollo | evaluacion_por_imagen.json |

**Hitos restantes:** datos: ampliar faltantes reales; panel: aceptación con tres estados; distribución: Lite V2 probado; oclusiones: revisión semántica final y ensayo de tres estados; cierre: deduplicación, prueba final y aceptación del MVP.

“Implementado” indica que existen código, configuración o artefactos comprobables. El estado en vivo de CVAT y Docker no quedó verificado en esta revisión porque el acceso al motor Docker fue denegado. No equivale a disponibilidad garantizada del servicio.

Las cuatro ejecuciones conservan pesos, parámetros, métricas, partición y entorno. V2 base utiliza la copia aprobada datos_20261019_234626_3df2e643. Algunos README de lotes todavía describen la exportación como pendiente; para el ensayo se toma como evidencia su versión congelada, sin extender esa aprobación al lote de oclusiones.


<!-- page -->

## 1 Planificación y riesgos

![Carta Gantt propuesta](Evidencias/gantt_20261020.png)

La Carta Gantt presenta una replanificación desde el corte. Los hitos anteriores se sustentan en los artefactos V1 del 15 de octubre y en los lotes y versiones V2 del 16 al 19 de octubre. Los nombres de los ensayos usan UTC: las ejecuciones V2 iniciadas el 20 de octubre UTC corresponden al 19 de octubre en Santiago.

La transcripción de la reunión sitúa el cierre en semana 17 y menciona tentativamente el 3 o 4 de diciembre. No se dispone aquí de una línea base aprobada que permita cuantificar retrasos; estas fechas son estimaciones y no compromisos ya acordados.

| Riesgo o dificultad | Evidencia y acción prioritaria |
|---|---|
| Pocos faltantes reales | V2 val contiene un nivel reponer. Capturar y anotar escenas reales adicionales; mantenerlas separadas por escena y sesión. |
| Oclusiones sin validar | V2 base no aprende no_evaluable. Cerrar tarea 22 y medir los tres estados por separado. |
| Etiquetado parcial y duplicados | Hay predicciones extra y estados superpuestos. Revisar ROI y referencias; comparar deduplicación en val sin cambiar test. |
| Diferencias entre copias de anotaciones | Tarea 19 registra 1.229 niveles en un registro antiguo y 1.212 en la exportación usada. Fijar siempre versión y fecha del snapshot. |
| Publicación incompleta | GitHub consultado conserva README V1. Publicar código/documentación de V2 y un manifiesto de artefactos de reproducción. |

El cambio de dimensiones de imágenes de oclusión motivó sustituir las tareas 20/21 por la 22. Existen registros de corrección; falta cerrar la aprobación semántica. No se atribuye un retraso en días sin una planificación anterior verificable.


<!-- page -->

## 2 Documentación técnica de la solución

El objetivo es localizar el espacio completo de cada nivel de góndola y clasificar su disponibilidad. V1 distingue vacío, baja disponibilidad, suficiente y no evaluable. V2 base reúne vacío y baja en reponer; la etapa completa añadirá no_evaluable.

![Arquitectura y flujo](Evidencias/arquitectura_20261020.png)

| Decisión | Justificación y límite |
|---|---|
| Polígonos por nivel completo | Siguen repisas inclinadas e incluyen el espacio vacío. Una detección por producto exigiría otro etiquetado y un catálogo por SKU. |
| YOLO11n y YOLO26n de segmentación | Permiten comparar dos modelos con la misma partición y configuración. Los checkpoints y resultados están conservados; su tamaño no prueba un consumo máximo de RAM. |
| PyTorch y Ultralytics | Proporcionan transferencia desde pesos generales, entrenamiento e inferencia GPU/CPU. Entorno guardado: PyTorch 2.5.1+cu121 y Ultralytics 8.4.174. |
| CVAT y control de versiones | Permiten revisión humana y trazabilidad del estado de cada foto. SHA-256 detecta cambios de bytes, pero no demuestra corrección semántica de etiquetas. |
| Partición por familias y grupos | Evita que original y variantes compartan destinos. No demuestra generalización entre tiendas; los grupos son conservadores y no identidades físicas certificadas. |
| Docker y panel local | Organizan dependencias y facilitan la ejecución. Datos, pesos y configuración deben estar disponibles por separado. |

OpenCV, Pillow y NumPy preparan imágenes y máscaras; Shapely interviene en comprobaciones geométricas. El panel Python y su interfaz HTML/CSS/JavaScript coordinan importación, entrenamiento y pruebas. En inferencia se orienta la foto, se ejecuta YOLO, se numeran niveles y se muestran estados y alertas. La confianza de una detección no es su porcentaje de ocupación.

Los dos modelos V2 base usan imgsz 640, batch 2, seed 42, optimizador AdamW y paciencia 20. Se guardan args.yaml y entorno.json por ensayo. La comparación propia utiliza conf 0,25 y emparejamiento único por IoU de máscara ≥ 0,50.


<!-- page -->

## 2 Datos y preparación

| Procedencia | Reales | Sintéticas | Uso y preparación |
|---|---:|---:|---|
| V1 Lider y reserva | 37 | 0 | 30 de desarrollo y 7 reservadas |
| V1 variantes | 0 | 72 | 102 candidatas al sumar 30 reales; 11 exclusiones; 91 activas |
| V2 Líder Express | 59 | 177 | 59 familias con original y tres variantes; tarea 19 |
| V2 visibilidad limitada | 0 | 60 | Ediciones con 24 carros, 24 personas y 12 cajas; tarea 22 |
| Total único | 96 | 309 | 405 imágenes; los 435 registros incluyen referencias repetidas |

Las fotos reales provienen de capturas del equipo en supermercado. Las variantes IA son ediciones de esas fuentes y no observaciones independientes. Se conserva procedencia, dimensiones, familia y SHA-256 en inventarios. Las exclusiones de V1 responden a problemas de calidad; las variantes V2 se revisan bajo una guía común y sus nombres A/B/C no determinan la etiqueta verdadera.

**Anotación usada por los modelos:** V1 contiene 719 niveles, con 683 en train y 36 en val. La copia V2 base contiene 1.212 niveles: 816 en entrenamiento, 51 en validación real, 153 en diagnóstico sintético y 192 en reserva. Un registro anterior de tarea 19 contiene 1.229; no se suman ambas versiones.

| Destino V2 base | Originales reales | Variantes IA | Aplicación |
|---|---:|---:|---|
| Entrenamiento | 40 | 120 | 160 imágenes usadas para aprender |
| Validación | 10 | 30 | Métrica principal solo en 10 reales; 30 de diagnóstico separado |
| Prueba final | 9 | 27 | Reservadas; no usadas aquí para elegir modelos |

Los 19 grupos conservadores se distribuyen en 14 de entrenamiento, 3 de validación y 2 de prueba. La cantidad de escenas independientes es menor que la de fotos. La verificación comprueba separación de familias y grupos dentro de este reparto.

El lote de oclusiones tiene 308 polígonos, pero existen snapshots con repartos de estados distintos. La revisión del 19 de octubre a las 22:27 UTC registra 256 suficientes, 41 no evaluables y 11 reponer; el registro de partición conserva otra copia de 299/9/0. Hasta cerrar la revisión no se adopta un conteo de clases definitivo.

Para la siguiente etapa se reservan 41 imágenes con obstáculos para train, 10 para val y 9 para test. Solo las aprobadas se incorporarán. Al fusionar, el entrenamiento sería 201 imágenes; la validación principal tendría 10 reales más 10 sintéticas de obstáculos, con métricas separadas. Las 30 variantes A/B/C de diagnóstico mantienen su función auxiliar. No se reportará una métrica agregada de 50 imágenes como si fueran 50 fotos reales.


<!-- page -->

## 3 Resultados preliminares

| Modelo | mAP50 máscara | mAP50–95 máscara | Localizados | Estado exacto | Extras | Alertas acertadas | Falsas alertas |
|---|---:|---:|---:|---:|---:|---:|---:|
| YOLO11-1 | 74,47 % | 56,59 % | 35/36 | 33/36 | 12 | 0/0 | 2 |
| YOLO26-1 | 73,38 % | 62,40 % | 35/36 | 34/36 | 11 | 0/0 | 0 |
| v2_base_yolo11n_01 | 98,44 % | 86,26 % | 51/51 | 48/51 | 8 | 1/1 | 4 |
| v2_base_yolo26n_01 | 99,28 % | 92,79 % | 50/51 | 50/51 | 5 | 1/1 | 0 |

**Fuentes:** metricas_validacion.json, metricas_alertas.json y evaluacion_por_imagen.json de los cuatro ensayos. V1 usa 5 fotos reales y V2 10. Los mAP provienen del evaluador Ultralytics; los conteos se obtienen del emparejamiento propio a conf 0,25 e IoU ≥ 0,50. Sus definiciones y umbrales difieren, por lo que no deben interpretarse como la misma métrica.

YOLO26 V2 logra 50/51 estados exactos, 5 predicciones extra, una omisión y cero falsas alertas. Su precisión de alertas es 1/1 y su recall es 1/1. YOLO11 V2 localiza 51/51 niveles, acierta 48/51 estados y emite 4 falsas alertas: precisión 1/5 y recall 1/1. En V1 no hay referencias de faltantes en val y el recall de alertas no es medible.

La diferencia de mAP50–95 entre los dos modelos V2 es 6,53 puntos a favor de YOLO26. La comparación entre V1 y V2 cambia datos, clases y partición: el salto de 62,40 % a 92,79 % no puede atribuirse exclusivamente a fusionar clases.

**Selección de los 20 casos:** se conserva una selección razonada de 10 resultados completos y 10 errores relevantes. En los éxitos se priorizan escenas reales de val y cobertura de alertas; ocho son de validación real y dos son sintéticos de entrenamiento. En los fallos se priorizan alertas omitidas, falsas alertas, omisiones y problemas de referencia. No constituye un ranking estadístico único entre versiones y particiones distintas. Cada ficha identifica su modelo, origen y métricas verificadas.

La IoU media de cada ficha se calcula solo sobre niveles emparejados; puede ser alta aunque existan omisiones o errores de estado. El resultado esperado es la anotación humana congelada, que también puede contener errores. Las causas visuales se presentan como hipótesis salvo cuando están sustentadas en una auditoría previa.

No se ejecutan nuevas inferencias sobre la reserva para preparar este informe. Las ilustraciones reutilizan comparaciones ya guardadas. Los resultados en train comprueban ajuste y sirven para diagnóstico, no para demostrar generalización.


<!-- page -->

### 3 Mejor caso 1 Alerta real de reposición

**Entrada:** lider_express_040_0_original.jpg · real · val. **Modelo:** v2_base_yolo26n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_040_0_original.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo26n_01_20261020_004933_b105/comparaciones/lider_express_040_0_original_val.jpg)

**Esperado:** 5 niveles: 4 suficiente, 1 reponer. **Obtenido:** 5 predicciones: 4 suficiente, 1 reponer.

**Métricas:** 5/5 localizados; 5/5 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9271. Alertas: 1/1 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** La única referencia reponer de val se detecta y se clasifican correctamente los otros cuatro niveles. El alcance de este éxito es un caso real.

**Comprobación siguiente:** Conservar como regresión y ampliar faltantes reales en escenas independientes.

**Trazabilidad:** registro lider_express_040_0_original.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 2 Seis niveles completos

**Entrada:** lider_express_015_0_original.jpg · real · val. **Modelo:** v2_base_yolo26n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_015_0_original.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo26n_01_20261020_004933_b105/comparaciones/lider_express_015_0_original_val.jpg)

**Esperado:** 6 niveles: 6 suficiente. **Obtenido:** 6 predicciones: 6 suficiente.

**Métricas:** 6/6 localizados; 6/6 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9464. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** Las seis referencias se localizan con estado correcto y sin predicciones adicionales. La IoU media es alta dentro de la validación V2.

**Comprobación siguiente:** Conservar el caso para comprobar que los cambios no degradan niveles suficientes.

**Trazabilidad:** registro lider_express_015_0_original.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 3 Delimitación precisa de cinco niveles

**Entrada:** lider_express_039_0_original.jpg · real · val. **Modelo:** v2_base_yolo26n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_039_0_original.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo26n_01_20261020_004933_b105/comparaciones/lider_express_039_0_original_val.jpg)

**Esperado:** 5 niveles: 5 suficiente. **Obtenido:** 5 predicciones: 5 suficiente.

**Métricas:** 5/5 localizados; 5/5 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9463. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** Las cinco máscaras emparejan referencias y estados. No aparecen alertas de reposición sin referencia.

**Comprobación siguiente:** Repetir la evaluación bajo nuevas sesiones y condiciones de captura.

**Trazabilidad:** registro lider_express_039_0_original.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 4 Máscaras de alta coincidencia

**Entrada:** lider_express_027_0_original.jpg · real · val. **Modelo:** v2_base_yolo11n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_027_0_original.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo11n_01_20261020_002800_ec8d/comparaciones/lider_express_027_0_original_val.jpg)

**Esperado:** 5 niveles: 5 suficiente. **Obtenido:** 5 predicciones: 5 suficiente.

**Métricas:** 5/5 localizados; 5/5 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9530. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** El modelo YOLO11 V2 alcanza coincidencia geométrica elevada en esta foto. Un éxito individual no reemplaza el balance global de falsas alertas.

**Comprobación siguiente:** Usar como comparación entre arquitecturas sobre la misma entrada.

**Trazabilidad:** registro lider_express_027_0_original.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 5 Seis estados suficientes correctos

**Entrada:** lider_express_014_0_original.jpg · real · val. **Modelo:** v2_base_yolo26n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_014_0_original.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo26n_01_20261020_004933_b105/comparaciones/lider_express_014_0_original_val.jpg)

**Esperado:** 6 niveles: 6 suficiente. **Obtenido:** 6 predicciones: 6 suficiente.

**Métricas:** 6/6 localizados; 6/6 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9248. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** Se recuperan las seis referencias sin extras. La clasificación de suficiente coincide con la anotación congelada.

**Comprobación siguiente:** Mantener este caso en las comprobaciones de geometría y orden espacial.

**Trazabilidad:** registro lider_express_014_0_original.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 6 Separaciones entre productos sin falsa alerta

**Entrada:** lider_express_026_0_original.jpg · real · val. **Modelo:** v2_base_yolo26n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_026_0_original.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo26n_01_20261020_004933_b105/comparaciones/lider_express_026_0_original_val.jpg)

**Esperado:** 5 niveles: 5 suficiente. **Obtenido:** 5 predicciones: 5 suficiente.

**Métricas:** 5/5 localizados; 5/5 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9213. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** Los cinco niveles suficientes se clasifican correctamente a pesar de las separaciones visibles entre productos.

**Comprobación siguiente:** Ampliar ejemplos cercanos al umbral del 30 % para contrastar este comportamiento.

**Trazabilidad:** registro lider_express_026_0_original.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 7 Dos módulos completos en V1

**Entrada:** REAL_04.jpg · real · val. **Modelo:** YOLO26-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_004.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO26-1_20261015_021212_c452/comparaciones/REAL_04_val.jpg)

**Esperado:** 12 niveles: 12 suficiente. **Obtenido:** 12 predicciones: 12 suficiente.

**Métricas:** 12/12 localizados; 12/12 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.8984. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** Se localizan doce niveles y se aciertan todos sus estados. La referencia incluye ambos módulos.

**Comprobación siguiente:** Conservar como control de fotografías con varios módulos completos.

**Trazabilidad:** registro REAL_04.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 8 Dos módulos con perspectiva en V1

**Entrada:** REAL_05.jpg · real · val. **Modelo:** YOLO11-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_005.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO11-1_20261015_013749_f709/comparaciones/REAL_05_val.jpg)

**Esperado:** 12 niveles: 12 suficiente. **Obtenido:** 12 predicciones: 12 suficiente.

**Métricas:** 12/12 localizados; 12/12 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.8551. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** Se aciertan doce niveles bajo perspectiva. No se midió el ángulo de cámara; este caso no define un rango angular garantizado.

**Comprobación siguiente:** Capturar series con ángulos documentados para medir el efecto de la perspectiva.

**Trazabilidad:** registro REAL_05.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 9 Cuatro alertas sintéticas de entrenamiento

**Entrada:** lider_express_049_B_baja.png · sintética · train. **Modelo:** v2_base_yolo26n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_049_B_baja.png)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo26n_01_20261020_004933_b105/comparaciones/lider_express_049_B_baja_train.jpg)

**Esperado:** 5 niveles: 1 suficiente, 4 reponer. **Obtenido:** 5 predicciones: 4 reponer, 1 suficiente.

**Métricas:** 5/5 localizados; 5/5 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9701. Alertas: 4/4 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** Se aciertan cuatro alertas y un estado suficiente en una variante sintética ya vista al entrenar. Es evidencia de ajuste.

**Comprobación siguiente:** Comprobar el mismo patrón con faltantes reales fuera de entrenamiento.

**Trazabilidad:** registro lider_express_049_B_baja.png en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Mejor caso 10 Tres estados correctos en V1

**Entrada:** EQ_01_V2.png · sintética · train. **Modelo:** YOLO26-1.

![Imagen original de entrada](../Datos/V1/Sinteticas/EQ_01_V2.png)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO26-1_20261015_021212_c452/comparaciones/EQ_01_V2_train.jpg)

**Esperado:** 10 niveles: 6 suficiente, 2 vacio, 2 baja_disponibilidad. **Obtenido:** 10 predicciones: 2 baja_disponibilidad, 2 vacio, 6 suficiente.

**Métricas:** 10/10 localizados; 10/10 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9443. Alertas: 4/4 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Criterio de éxito:** Se aciertan diez estados en una imagen sintética de train: seis suficientes, dos vacíos y dos bajos. No demuestra desempeño fuera de muestra.

**Comprobación siguiente:** Mantener como diagnóstico del criterio histórico V1.

**Trazabilidad:** registro EQ_01_V2.png en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 1 Omisión y detecciones adicionales

**Entrada:** lider_express_042_0_original.jpg · real · val. **Modelo:** v2_base_yolo26n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_042_0_original.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo26n_01_20261020_004933_b105/comparaciones/lider_express_042_0_original_val.jpg)

**Esperado:** 3 niveles: 3 suficiente. **Obtenido:** 6 predicciones: 6 suficiente.

**Métricas:** 2/3 localizados; 2/3 estados exactos; 1 omitidos; 4 extras. IoU media emparejada 0.8031. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** Se emparejan dos de tres referencias y aparecen cuatro predicciones extra. El encuadre y la cobertura de anotación podrían explicar parte del error.

**Propuesta de mejora:** Revisar cada extra, completar referencias o definir ROI; repetir la medición con la misma política.

**Trazabilidad:** registro lider_express_042_0_original.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 2 Cuatro falsas alertas interclase

**Entrada:** lider_express_028_0_original.jpg · real · val. **Modelo:** v2_base_yolo11n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_028_0_original.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo11n_01_20261020_002800_ec8d/comparaciones/lider_express_028_0_original_val.jpg)

**Esperado:** 5 niveles: 5 suficiente. **Obtenido:** 9 predicciones: 5 suficiente, 4 reponer.

**Métricas:** 5/5 localizados; 2/5 estados exactos; 0 omitidos; 4 extras. IoU media emparejada 0.9453. Alertas: 0/0 acertadas, 0 omitidas y 4 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** Se emiten nueve máscaras frente a cinco referencias suficientes. Se registran cuatro falsas alertas y solo dos estados exactos. La superposición de hipótesis es compatible con duplicados interclase.

**Propuesta de mejora:** Comparar NMS agnóstica y supresión por máscara sobre val. Verificar que no eliminen niveles vecinos legítimos.

**Trazabilidad:** registro lider_express_028_0_original.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 3 Fallo de no evaluable en V1

**Entrada:** REAL_29.jpg · real · val. **Modelo:** YOLO11-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_029.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO11-1_20261015_013749_f709/comparaciones/REAL_29_val.jpg)

**Esperado:** 3 niveles: 1 suficiente, 2 no_evaluable. **Obtenido:** 7 predicciones: 6 suficiente, 1 baja_disponibilidad.

**Métricas:** 2/3 localizados; 1/3 estados exactos; 1 omitidos; 5 extras. IoU media emparejada 0.8558. Alertas: 0/0 acertadas, 0 omitidas y 1 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** Se acierta un estado de tres y se omite un nivel. La referencia contiene dos no evaluables; la escasez de ejemplos V1 es una causa probable.

**Propuesta de mejora:** Añadir oclusiones revisadas y evaluar recall de no_evaluable con denominador explícito.

**Trazabilidad:** registro REAL_29.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 4 Detecciones fuera de las referencias

**Entrada:** REAL_22.jpg · real · val. **Modelo:** YOLO26-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_022.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO26-1_20261015_021212_c452/comparaciones/REAL_22_val.jpg)

**Esperado:** 6 niveles: 6 suficiente. **Obtenido:** 12 predicciones: 12 suficiente.

**Métricas:** 6/6 localizados; 6/6 estados exactos; 0 omitidos; 6 extras. IoU media emparejada 0.8808. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** Las seis referencias centrales son correctas, pero hay seis máscaras sin referencia. Una auditoría debe determinar cuáles representan niveles reales adicionales.

**Propuesta de mejora:** Unificar cobertura de anotación e inferencia antes de atribuir todos los extras al modelo.

**Trazabilidad:** registro REAL_22.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 5 Cinco niveles omitidos

**Entrada:** REAL_02.jpg · real · train. **Modelo:** YOLO26-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_002.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO26-1_20261015_021212_c452/comparaciones/REAL_02_train.jpg)

**Esperado:** 10 niveles: 10 suficiente. **Obtenido:** 5 predicciones: 5 suficiente.

**Métricas:** 5/10 localizados; 5/10 estados exactos; 5 omitidos; 0 extras. IoU media emparejada 0.9327. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** Se detectan cinco de diez niveles anotados. La causa no está aislada: podrían intervenir geometría, contraste o confianza. El JSON a conf fija no demuestra que bajar el umbral recupere las cinco omisiones.

**Propuesta de mejora:** Inspeccionar puntuaciones y medir una curva de confianza en val con el costo de falsos positivos.

**Trazabilidad:** registro REAL_02.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 6 Confusión entre vacío y baja

**Entrada:** REAL_03.jpg · real · train. **Modelo:** YOLO11-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_003.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO11-1_20261015_013749_f709/comparaciones/REAL_03_train.jpg)

**Esperado:** 10 niveles: 7 vacio, 2 suficiente, 1 baja_disponibilidad. **Obtenido:** 14 predicciones: 8 vacio, 2 suficiente, 4 baja_disponibilidad.

**Métricas:** 10/10 localizados; 9/10 estados exactos; 0 omitidos; 4 extras. IoU media emparejada 0.9490. Alertas: 8/8 acertadas, 0 omitidas y 4 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** Se localizan diez referencias, se aciertan nueve estados y se generan cuatro falsas alertas extra. La auditoría previa describe intrusión visual de producto vecino por perspectiva.

**Propuesta de mejora:** Revisar pertenencia al nivel y comparar la formulación reponer; deduplicar conservando la decisión correcta.

**Trazabilidad:** registro REAL_03.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 7 No evaluable clasificado como suficiente

**Entrada:** REAL_07.jpg · real · train. **Modelo:** YOLO26-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_007.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO26-1_20261015_021212_c452/comparaciones/REAL_07_train.jpg)

**Esperado:** 5 niveles: 4 suficiente, 1 no_evaluable. **Obtenido:** 10 predicciones: 10 suficiente.

**Métricas:** 5/5 localizados; 4/5 estados exactos; 0 omitidos; 5 extras. IoU media emparejada 0.9105. Alertas: 0/0 acertadas, 0 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** Se aciertan cuatro estados de cinco y hay cinco predicciones extra. La referencia no evaluable se clasifica como suficiente.

**Propuesta de mejora:** Revisar referencia y cobertura del segundo módulo; entrenar la clase de oclusión con ejemplos variados.

**Trazabilidad:** registro REAL_07.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 8 Alerta crítica omitida

**Entrada:** REAL_11.jpg · real · train. **Modelo:** YOLO26-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_011.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO26-1_20261015_021212_c452/comparaciones/REAL_11_train.jpg)

**Esperado:** 10 niveles: 9 suficiente, 1 baja_disponibilidad. **Obtenido:** 10 predicciones: 10 suficiente.

**Métricas:** 10/10 localizados; 9/10 estados exactos; 0 omitidos; 0 extras. IoU media emparejada 0.9050. Alertas: 0/1 acertadas, 1 omitidas y 0 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** Las diez referencias se localizan, pero el nivel bajo se clasifica como suficiente. Se pierde la única alerta de la imagen; IoU alta no garantiza una decisión correcta.

**Propuesta de mejora:** Revisar la ocupación con dos anotadores y reforzar faltantes reales y niveles inferiores.

**Trazabilidad:** registro REAL_11.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 9 Discrepancia con la anotación

**Entrada:** REAL_25.jpg · real · train. **Modelo:** YOLO11-1.

![Imagen original de entrada](../Datos/V1/Lider/lider_025.jpg)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/YOLO11-1_20261015_013749_f709/comparaciones/REAL_25_train.jpg)

**Esperado:** 12 niveles: 1 vacio, 11 suficiente. **Obtenido:** 13 predicciones: 11 suficiente, 1 vacio, 1 baja_disponibilidad.

**Métricas:** 12/12 localizados; 11/12 estados exactos; 0 omitidos; 1 extras. IoU media emparejada 0.9329. Alertas: 1/1 acertadas, 0 omitidas y 1 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** La predicción discrepa en un estado y emite una máscara adicional. La guía de mejora ya señala una posible etiqueta suficiente incorrecta en un nivel con poco producto.

**Propuesta de mejora:** Resolver la discrepancia humana, versionar la corrección y recalcular; no tratar la etiqueta antigua como verdad definitiva.

**Trazabilidad:** registro REAL_25.jpg en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

### 3 Peor caso 10 Dos alertas omitidas y dos falsas

**Entrada:** lider_express_032_B_baja.png · sintética · train. **Modelo:** v2_base_yolo11n_01.

![Imagen original de entrada](../Datos/V2/lider_express_20261016/imagenes_ordenadas/lider_express_032_B_baja.png)

![Referencia a la izquierda y predicción a la derecha](../Experimentos/v2_base_yolo11n_01_20261020_002800_ec8d/comparaciones/lider_express_032_B_baja_train.jpg)

**Esperado:** 6 niveles: 3 suficiente, 3 reponer. **Obtenido:** 8 predicciones: 5 suficiente, 3 reponer.

**Métricas:** 6/6 localizados; 4/6 estados exactos; 0 omitidos; 2 extras. IoU media emparejada 0.9555. Alertas: 1/3 acertadas, 2 omitidas y 2 falsas. Cuando no hay referencias, el recall de alertas no es medible.

**Error y causa probable:** En una variante sintética de train, se localizan seis niveles, pero se aciertan cuatro estados. Se omiten dos alertas y se generan dos falsas alertas extra.

**Propuesta de mejora:** Comparar con YOLO26 sobre la misma entrada y revisar duplicados y producto disperso; validar el patrón en fotos reales.

**Trazabilidad:** registro lider_express_032_B_baja.png en evaluacion_por_imagen.json del ensayo. Los datos completos están en Evidencias/casos_informe_20261020.json.


<!-- page -->

## 3 Análisis comparativo y mejoras

Los mejores casos comparten niveles completos y delimitables, anotación consistente y ausencia de obstáculos que impidan decidir el estado. Las fichas muestran que ambos modelos pueden resolver múltiples módulos y perspectiva moderada, pero no se midieron sistemáticamente grados de inclinación, iluminación, reflejos, sombras ni desenfoque. No se establece un umbral angular o de luz validado.

Los errores combinan clasificación incorrecta, omisiones y predicciones adicionales. Las fichas 2 y 10 de peores casos muestran falsas alertas y decisiones incompatibles sobre un nivel; las fichas 1, 4 y 7 requieren revisar cobertura de anotación. La ficha 8 demuestra que una geometría correcta puede acompañar una alerta omitida. Las hipótesis deben probarse mediante cambios aislados y medición sobre val.

No se afirma que un porcentaje determinado de falsos positivos sea causado por etiquetas incompletas: falta una auditoría y un denominador documentado. Tampoco se atribuyen errores de forma causal a iluminación o sombras solo por inspección visual.

**Prioridades técnicas:** mantener YOLO26 V2 como referencia provisional; ampliar faltantes reales; cerrar la revisión de oclusiones; comparar posprocesamiento y cobertura de etiquetas; congelar modelo, umbrales y referencias antes de evaluar test.

El lote V2 real de validación pertenece a tres grupos conservadores y el de prueba a dos. La separación de familias evita una fuga conocida, pero no basta para certificar independencia física total o transferencia entre locales. Las nuevas capturas deben incluir sesión, local, familia y política de partición.

Los entornos de entrenamiento registran una GTX 1660 SUPER. Las mediciones de inferencia con batch 1 y 2 no representan una latencia garantizada del panel ni permiten inferir fotogramas por segundo de extremo a extremo. Falta un ensayo reproducible que mida lectura, preparación, inferencia, posprocesamiento y respuesta, además de memoria CPU/GPU.

**Criterios propuestos para aceptación:** medir precisión y recall de reponer y no_evaluable por origen; informar denominadores e intervalos cuando corresponda; comprobar omisiones y duplicados por nivel; definir con el cliente el costo aceptable de falsa alerta frente a omisión; registrar latencia completa y consumo en el hardware de demostración. Los umbrales de aceptación deben acordarse antes de consultar test.


<!-- page -->

## 4 Repositorio y reproducibilidad

La carpeta local organiza código en Herramientas, datos y versiones en Datos, resultados en Experimentos, configuración en Infraestructura y documentación en Documentacion. El README local describe decisiones, arquitectura, datasets, estado e instrucciones.

Repositorio de referencia: https://github.com/vcanio/Capstone2026. La consulta a GitHub del 20 de octubre muestra que el README publicado aún corresponde al laboratorio del 15 de octubre y V1. La carpeta de trabajo carece de .git, por lo que no puede probarse su sincronización con main ni atribuir cambios locales a commits. La consulta y los commits devueltos se conservan en Evidencias/consulta_github_20261020.json. El historial remoto contiene entregas académicas y cambios de README, pero no demuestra por sí solo la participación en el código local V2.

**Pendiente para la publicación:** llevar código y documentación a un checkout verificado, revisar el diff, agregar un manifiesto de datos y pesos compartibles, registrar contribuciones verificables y publicar una versión de entrega. No se deben subir credenciales ni configuraciones privadas. Las imágenes y pesos requieren un mecanismo de acceso para el evaluador; un clon por sí solo no reproduce el laboratorio completo.

Desde la raíz, con Python 3.11 o 3.12 y los datos/modelos necesarios disponibles:

```powershell
python -m venv .venv-modelo
& ./.venv-modelo/Scripts/python.exe -m pip install -r Herramientas/Modelos/requirements.txt
& ./Herramientas/Modelos/iniciar_panel.ps1 -Cpu -Build
# GPU NVIDIA: omitir -Cpu con entorno Docker/GPU configurado
& ./.venv-modelo/Scripts/python.exe Herramientas/verificar_proyecto.py
& ./.venv-modelo/Scripts/python.exe Herramientas/Datos/particionar_lider_express.py --verify
```

Abrir http://localhost:8090, seleccionar V2 y v2_base_yolo26n_01, cargar la foto lider_express_040_0_original y analizar. La evaluación guardada a conf 0,25 contiene cinco niveles, cuatro suficientes y uno reponer. La demostración debe comparar contra esa configuración y referencia. Una foto propia sin etiqueta permite observar una predicción, no calcular precisión.

La demo Walmart Lite distribuida conserva los modelos V1 y descarga dependencias en el primer arranque. Su actualización a V2 y su prueba en otro equipo siguen pendientes. La presencia del ZIP no demuestra funcionamiento offline ni reproducibilidad en un equipo limpio.

**Verificación al corte:** auditoría correcta de 43 documentos, 270 enlaces locales, 435 registros de imágenes, 2 exportaciones compartidas y 52 archivos Python. Pasaron las 11 pruebas de datos; la suite de modelos terminó correctamente con 222 pruebas y una omitida. La partición de 296 imágenes también pasó. El registro y los logs están en Evidencias/verificacion_informe_20261020.json. Las pruebas de código no sustituyen una validación del modelo ni una demostración en hardware externo.


<!-- page -->

## 5 Conclusiones y próximos pasos

Se alcanzó el objetivo de construir un flujo local trazable de datos, anotación, entrenamiento, evaluación e inferencia. Existen cuatro modelos entrenados y comparaciones visuales conservadas. La etapa V2 base mejora las métricas de máscaras respecto de V1 bajo su propio conjunto de validación; su detección real de faltantes aún tiene evidencia escasa.

El panel dispone de carga de imágenes, selección de modelo, ejecución de inferencia y visualización de estados. Los artefactos demuestran implementación, mientras que la disponibilidad del despliegue y la ejecución en un equipo limpio necesitan una comprobación adicional. V2 de tres estados, deduplicación validada, prueba final y distribución actualizada permanecen pendientes.

| Actividad propuesta | Responsable propuesto | Fecha estimada | Criterio de cierre |
|---|---|---|---|
| Cerrar revisión de 308 polígonos de tarea 22 | Paulo Guerra y Vicente Vilches | 27 oct | Snapshot aprobado y discrepancias resueltas |
| Entrenar y comparar V2 de tres estados | Vicente Canio y Paulo Guerra | 3 nov | Ensayos versionados y métricas por origen/clase |
| Evaluar deduplicación y referencias de bordes | Vicente Canio y Paulo Guerra | 10 nov | Comparativa en val sin degradar niveles vecinos |
| Capturar faltantes reales independientes | Vicente Vilches y equipo | 17 nov | Nuevas escenas anotadas y partición versionada |
| Congelar modelo y ejecutar prueba final | Todo el equipo | 26 nov | Test real separado de diagnóstico sintético |
| Validar Lite V2 y publicar entrega reproducible | Vicente Canio y equipo | 26 nov | Ejecución en otro equipo y versión publicada |
| Cerrar informe y preparar defensa | Todo el equipo | 3 o 4 dic | Demostración y documentación consistentes |

Estas asignaciones y fechas son una propuesta de planificación que el equipo debe acordar. La viabilidad de completar el MVP es condicionada: requiere resolver la revisión de etiquetas y el refuerzo real antes de congelar el modelo. El 77,8 % de hitos no autoriza afirmar que resta el 22,2 % del esfuerzo; la captura y validación pueden dominar el tiempo restante.

La evaluación final principal debe separar los nueve originales reales V2 de sus 27 variantes y de las nueve imágenes sintéticas con obstáculos. Las siete fotos reservadas V1 constituyen otro conjunto y deben evaluarse por separado, siempre que no hayan sido usadas para ajustar el método. Si se incorporan nuevas escenas, se crea una versión y se congela su destino antes de consultar resultados. No se combinarán 52 imágenes heterogéneas como una sola prueba real independiente.
