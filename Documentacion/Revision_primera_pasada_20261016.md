# Primera pasada: revisión y propuesta para el siguiente entrenamiento

16 de octubre de 2026 · Proyecto Walmart · Revisión de archivos locales.

**La primera pasada sirve como prototipo de localización y clasificación de niveles. Todavía no permite demostrar detección de faltantes en escenas nuevas. La siguiente ronda debe mejorar las referencias y la evaluación antes de aumentar épocas o cambiar de arquitectura.**

## 1. Qué se hizo realmente

La conversación recuperada menciona unas 90 fotos, tres anotadores, una caja por nivel y una decisión visual alrededor del 30 %. El proyecto local documenta una evolución: hoy utiliza **polígonos por nivel y segmentación de instancias de cuatro clases**, con guía v1.3. El porcentaje orienta la anotación humana; el programa predice la clase aprendida, sin calcular explícitamente ocupación o inventario.

El paquete inicial tenía 102 imágenes. Tras 11 exclusiones, ambos ensayos utilizaron estas 91:

| Partición y origen | Fotos | Vacío | Baja | Suficiente | No evaluable |
|---|---:|---:|---:|---:|---:|
| Entrenamiento real | 24 | 11 | 7 | 173 | 1 |
| Entrenamiento sintético | 62 | 69 | 67 | 349 | 6 |
| Validación real | 5 | 0 | 0 | 34 | 2 |

Son **683 niveles para entrenar y 36 para validar**. El nombre «Equilibrado» no significa igualdad de niveles por clase: suficiente representa el 76,4 % de las referencias de entrenamiento.

Los 182 archivos exportados de imágenes y etiquetas son idénticos por SHA-256 entre YOLO11-1 y YOLO26-1. No hay intersección de IDs, grupos de escena registrados o hashes de imágenes exportadas entre train y val. Esto verifica la partición declarada; no equivale a una búsqueda exhaustiva de similitud visual o de escenas mal identificadas.

**Conviene conservar:** guía común, anotación humana de sintéticas, exclusiones de material defectuoso, agrupación por escena, validación real, versiones de datos aprobadas y ensayos completos con pesos, configuración y métricas. Estos elementos permiten revisar decisiones sin perder la primera referencia.

Fuentes: [manifest](../Experimentos/YOLO26-1_20261015_021212_c452/manifest.json), [guía v1.3](Guia_anotacion_CVAT.md) y [recuento independiente](Revision_primera_pasada_20261016.json).

## 2. Hallazgos que cambian la siguiente ronda

### La validación no mide el objetivo principal

Las cinco fotos pertenecen a **tres escenas** y carecen de vacíos y bajos. No se puede medir recall de alertas críticas, escoger su umbral ni decidir qué modelo detecta mejor faltantes. También se seleccionó best.pt y se aplicó parada temprana usando una validación sin esas clases: la selección del checkpoint no estuvo respaldada por desempeño en faltantes nuevos.

Hay 35/36 niveles localizados por ambos modelos, independientemente de acertar el estado. Eso es un resultado de localización sobre este conjunto, no una exactitud del 97 % en disponibilidad.

### La evidencia crítica depende mucho de las sintéticas

De 154 niveles vacíos o bajos de entrenamiento, **136 son sintéticos: 88,3 %**. Las 62 imágenes sintéticas activas abarcan ocho escenas; no aportan 62 escenas independientes.

Los vacíos reales aparecen en cinco fotos de cuatro escenas y los bajos reales en siete fotos de cinco escenas. La clase no evaluable solo tiene un nivel real, en una escena; sus seis ejemplos sintéticos proceden también de una única escena. En validación, ambos modelos aciertan 0/2 no evaluables; YOLO26 tampoco emite esa clase en las predicciones guardadas de entrenamiento a confianza 0,25.

Esto justifica ampliar datos reales de esas clases. No demuestra que las sintéticas perjudiquen: su contribución todavía no se ha aislado en un experimento.

### La región anotada y la imagen de aprendizaje no coinciden

La guía elige tramos completos y deja fragmentos fuera. La exportación conserva la foto completa, sin declarar esas regiones como ignoradas. Por ejemplo, en REAL_22 se anotó el tramo central, pero el modelo detecta niveles visibles del izquierdo; el evaluador los registra como extras. En entrenamiento, una región objetivo visible sin etiqueta puede tratarse como fondo.

Para la siguiente versión elegir una política consistente:

- **Opción inicial recomendada:** preparar encuadres por tramo completo o por grupo de tramos, manteniendo todos los niveles y el contexto necesario, y anotarlos exhaustivamente. Excluir encuadres que no permitan decidir o delimitar según la guía.
- Si se conservan las fotos completas con anotación parcial, implementar regiones ignoradas que respeten tanto entrenamiento como evaluación. Una máscara visual en el panel no basta.

Un recorte no debe eliminar producto ni cambiar el ancho de referencia para conservar artificialmente una etiqueta. Todos los recortes de una escena permanecen en su partición. Mantener ejemplos con carteles y otras estructuras reales para medir falsas detecciones.

### Hay errores de etiquetas y de salida que requieren acciones diferentes

La documentación señala discrepancias pendientes de revisión en REAL_25. Revisar el original con dos personas y la guía antes de crear la próxima copia. En REAL_03, el diagnóstico posterior aclara que los productos del extremo pertenecen al tramo vecino y mantiene vacío en el nivel inferior derecho; no repetir la sugerencia anterior de cambiarlo a baja solo por ver paquetes proyectados dentro del polígono.

También existen predicciones de estados distintos sobre un mismo nivel. La supresión entre clases redujo duplicados en las pruebas guardadas de REAL_03, pero no garantiza escoger el estado correcto. Evaluar esa política por separado, sobre varias escenas, contando también niveles vecinos eliminados.

Fuentes: [comparación REAL_22](../Experimentos/YOLO26-1_20261015_021212_c452/comparaciones/REAL_22_val.jpg), [REAL_29 y carteles](../Experimentos/YOLO26-1_20261015_021212_c452/comparaciones/REAL_29_val.jpg), diagnóstico corregido de REAL_03 (archivo local histórico, fuera de la distribución) y [casos REAL_11/REAL_25](Guia_mejora_modelo_paso_a_paso.md#10-ejemplos-concretos-fotos-11-y-25).

## 3. Augmentation que ya utilizaron

Hay dos procesos distintos: generar fotografías sintéticas previamente, revisadas y anotadas en CVAT, y transformar imágenes durante el entrenamiento. Los dos ensayos configuraron:

| Transformación durante aprendizaje | Valor guardado |
|---|---:|
| Tono, saturación y brillo | hsv_h=0.01, hsv_s=0.2, hsv_v=0.2 |
| Rotación | degrees=3 |
| Desplazamiento | translate=0.05 |
| Escala | scale=0.15 |
| Mosaic, MixUp, CutMix, Copy-Paste | 0 |
| Volteos horizontal y vertical | 0 |
| Perspectiva y shear | 0 |

No hace falta activar augment=True por ver augment: false en args.yaml: ese argumento se utiliza para augmentation en predicción. Los parámetros de aprendizaje son los anteriores y los lotes guardados muestran transformaciones. AutoAugment y erasing figuran en la configuración general, pero son opciones del flujo de clasificación; su presencia no demuestra que se usaran en esta segmentación. Véanse [predicción](https://docs.ultralytics.com/modes/predict/) y [augmentation de Ultralytics](https://docs.ultralytics.com/guides/yolo-data-augmentation/).

**Precaución específica del criterio por ancho:** una transformación que corte producto o los límites del nivel puede invalidar su estado original. Por ejemplo, recortar el extremo abastecido de un suficiente puede dejar un fragmento que parece vacío. Es un riesgo de coherencia de etiquetas que debe comprobarse; esta revisión no cuantificó su frecuencia en los lotes completos.

Mi propuesta inicial es conservar variación suave de color y usar geometría que mantenga visible el nivel completo. Si todavía no se verifica esa condición, probar una configuración conservadora con degrees=0, translate=0 y scale=0, frente a la configuración actual sobre exactamente los mismos datos. No añadir de entrada borrado de regiones, mezclas o recortes agresivos.

Fuentes locales: [args.yaml](../Experimentos/YOLO26-1_20261015_021212_c452/entrenamiento/args.yaml), [función train](../Herramientas/Modelos/piloto_modulos.py) y [lote de entrenamiento guardado](../Experimentos/YOLO26-1_20261015_021212_c452/entrenamiento/train_batch0.jpg). Las propuestas anteriores son decisiones para este proyecto, pendientes de comparación.

## 4. Qué dicen los dos entrenamientos

| Medida sobre la validación actual | YOLO11-1 | YOLO26-1 |
|---|---:|---:|
| Épocas registradas en CSV | 92 | 52 |
| Época de mayor mAP50-95 de máscaras | 72 | 32 |
| mAP50-95 de máscaras de best.pt | 56,59 % | 62,40 % |
| Niveles localizados | 35/36 | 35/36 |
| Suficientes con estado correcto | 33/34 | 34/34 |
| No evaluables con estado correcto | 0/2 | 0/2 |
| Alertas críticas emitidas | 2 | 0 |
| Recall de alertas críticas | No medible | No medible |

La evaluación por imagen usa confianza 0,25 y emparejamiento único por IoU de máscara ≥ 0,5; el mAP usa el evaluador estándar y otros umbrales. No mezclar sus interpretaciones. Los recuentos de extras están afectados por la anotación parcial.

YOLO26 es un candidato razonable para la siguiente comparación. Su mejor mAP no establece superioridad en faltantes y sus cero alertas no prueban sensibilidad. Conservar ambos checkpoints y evaluar ambos de nuevo cuando exista una validación representativa.

## 5. Secuencia concreta para la ronda 2

1. **Capturar escenas reales nuevas.** Mantener el [reparto de 40 fotos por persona](Guia_mejora_modelo_paso_a_paso.md) como objetivo operativo: 12 orientadas a vacío, 12 a baja, 12 a suficiente y cuatro a no evaluable. Contar después niveles y escenas por estado; no confundir la cuota de fotos con balance de clases. Cubrir perspectiva, producto del fondo, tramos vecinos, niveles inferiores y carteles.
2. **Separar antes de generar variantes.** Reservar aproximadamente una cuarta parte de las escenas nuevas para validación real, asegurando las cuatro clases y diversidad por clase. Mantener las cinco fotos antiguas fuera del entrenamiento. Conservar la reserva final separada y auditar que no se haya usado para ajustar decisiones antes de presentarla como independiente.
3. **Revisión cruzada.** Rotar Vicente → Paulo → Vilches → Vicente. Revisar todos los críticos, los no evaluables y los casos próximos al 30 %. Registrar desacuerdos iniciales sobre un mismo subconjunto antes de resolverlos; así se comprueba si el criterio se aplica consistentemente. No cambiar el 30 % en esta misma ronda sin una evaluación específica del criterio.
4. **Corregir cobertura y etiquetas.** Resolver la región de análisis y las discrepancias señaladas; conservar los archivos de los ensayos históricos. Crear una nueva versión con datos antiguos útiles corregidos más nuevos, con procedencia y particiones. El importador actual requiere adaptación para registrar/fusionar nuevos lotes: una tarea nueva en CVAT no los incorpora automáticamente.
5. **Evaluar primero los pesos actuales.** Ejecutar ambos best.pt sobre la nueva validación real con la región coherente. Esta es la referencia antes de reentrenar. No comparar sus porcentajes antiguos con porcentajes nuevos sobre otro conjunto.
6. **Entrenar un candidato y comparar.** Para la mejora práctica puede partirse de best.pt con el conjunto ampliado completo. Mantener inicialmente 640, batch 2, AdamW, semilla 42, máximo 100 épocas y paciencia 20. Una tasa 0.0001 es una hipótesis conservadora para ajuste fino que debe medirse; no un valor óptimo demostrado. Documentar cualquier cambio respecto a la primera pasada. La política de augmentation está fijada en código y requiere adaptarlo si se ensaya otra configuración.

Si el objetivo específico es **saber cuánto ayudan las sintéticas**, hacer este par controlado antes de más búsquedas de parámetros:

| Ensayo | Mismo punto de partida | Datos de entrenamiento | Evaluación |
|---|---|---|---|
| R2-real | YOLO26n-seg general preentrenado | Reales antiguos corregidos + reales nuevos | Misma validación real nueva |
| R2-mixto | El mismo checkpoint general | Exactamente los mismos reales + sintéticas revisadas | La misma validación |

Mantener idénticos resolución, augmentation, optimizador, tasa, semilla y límites de entrenamiento. Registrar las épocas efectivas: añadir imágenes cambia el número de actualizaciones por época, por lo que este par compara dos recetas de entrenamiento, no un efecto aislado con idéntico presupuesto de cómputo.

**No iniciar ese contraste desde best.pt de la primera pasada:** ya aprendió de sintéticas y la rama «real» conservaría esa exposición. El ajuste fino desde best.pt es útil para mejorar el sistema, pero responde a otra pregunta.

## 6. Cómo decidir si mejoró

Usar como medida principal el recall de alertas vacío+baja, acompañado de precisión de alertas y falsas alertas por foto. Reportar también recall separado de vacío y baja, matriz de estados, no evaluables, localización, duplicados y tiempo de inferencia. Mostrar numeradores y denominadores, además de porcentajes; los niveles de una misma escena no son observaciones independientes.

Elegir candidatos con la misma política de inferencia y el mismo conjunto. Si se compara 640 frente a 960 o NMS entre clases, hacerlo como experimento de inferencia separado antes de atribuir el efecto al aprendizaje. La prueba de 960 en REAL_03 recuperó localización, pero no acertó el estado; esa foto pertenece al entrenamiento.

No hay todavía un mínimo acordado de recall ni un coste aceptable de falsas alertas. Comparar los compromisos observados y acordar el criterio operativo con el equipo. Antes de afirmar uso en cámaras de vigilancia, añadir evaluación de las cámaras previstas.

## 7. Alcance y trazabilidad de esta revisión

Se recontaron las etiquetas exportadas, se verificaron clase y formato/rango de coordenadas, se reagruparon las evaluaciones por imagen y se cotejaron las métricas guardadas. Se compararon 182 archivos por SHA-256 entre ensayos y se verificaron los hashes de los 91 originales contra el manifest. Se inspeccionaron visualmente REAL_22, REAL_29 y train_batch0 de YOLO26; no se revisaron visualmente todas las imágenes.

Detalle de reproducibilidad: 64 imágenes exportadas coinciden en bytes con el original. Cuatro tienen orientación EXIF 6 y su exportación orientada se reprodujo exactamente. Otras 23 tienen orientación 1 y bytes distintos, con diferencias medias RGB de 0,092–0,136 sobre 255 frente al original. Sus dimensiones coinciden y ambos ensayos usan copias idénticas. La preparación actual no reproduce esos 23 hashes; la causa histórica no quedó determinada. En adelante conviene registrar **hash del original, hash exportado y versión del exportador** por separado.

El entorno guardado del entrenamiento es Ultralytics 8.4.174 / Torch 2.5.1+cu121, con GTX 1660 SUPER. La biblioteca local de .venv-modelo es otra versión de Ultralytics; no se usó para inferir ni se asumió equivalente al entorno histórico. Docker estaba detenido. No se ejecutaron entrenamiento o inferencia nuevos, no se alteraron anotaciones o pesos y no se abrió el contenido de las siete imágenes de reserva final.

Los números y comprobaciones están en [Revision_primera_pasada_20261016.json](Revision_primera_pasada_20261016.json). Las recomendaciones técnicas se contrastaron con documentación oficial vigente; los parámetros efectivamente usados proceden de los archivos locales conservados.
