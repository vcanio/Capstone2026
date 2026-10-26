> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../../Modelos/Actual/README.md).

# Revisión de YOLO11-1

Revisión del 14 de octubre de 2026, hora de Santiago. Se evalúa exclusivamente `YOLO11-1_20261015_013749_f709`. Los ensayos exploratorios anteriores no se usan como comparación.

**El entrenamiento terminó correctamente y el modelo muestra buena localización de los niveles anotados. La validación actual no permite medir detección de vacíos o baja disponibilidad porque no contiene ejemplos de esas clases. Antes de cambiar de arquitectura, conviene resolver la cobertura de evaluación, las regiones excluidas y algunas etiquetas concretas.**

## Ejecución

- Modelo inicial: YOLO11n-seg, resolución 640, batch 2, AdamW, tasa inicial 0,001, semilla 42.
- 92 épocas efectivas, mejor checkpoint en la 72; parada temprana tras 20 épocas sin mejora. Confirmado por `results.csv` y el log. `progreso.json` registra 93 épocas completadas, una discrepancia del contador del panel; no representa una época adicional en el CSV.
- Estado final `done`, código de salida 0. Aprendizaje: aproximadamente 30,4 minutos; proceso completo con evaluación: aproximadamente 33 minutos.
- Las evaluaciones y comparaciones usan [best.pt](entrenamiento/weights/best.pt).
- Las pérdidas de entrenamiento bajan. La validación se estabiliza y fluctúa; su máximo de mAP de máscaras en la época 72 es puntual. Con cinco fotos y dos clases presentes no conviene interpretar esa selección como una optimización demostrada de alertas críticas.

Fuentes: [configuración](config_interfaz.json), [curvas](entrenamiento/results.png), [CSV](entrenamiento/results.csv) y registro de ejecución (archivo local histórico, fuera de la distribución).

## Datos efectivamente utilizados

Se inspeccionó el [manifest del ensayo](manifest.json), no el tamaño original del paquete candidato.

| Conjunto | Fotos | Vacío | Baja | Suficiente | No evaluable |
|---|---:|---:|---:|---:|---:|
| Entrenamiento real | 24 | 11 | 7 | 173 | 1 |
| Entrenamiento sintético | 62 | 69 | 67 | 349 | 6 |
| Validación real | 5 | 0 | 0 | 34 | 2 |

Total: 91 fotos, 683 niveles de entrenamiento y 36 de validación. No hay intersección de identificadores de escena ni hashes registrados entre entrenamiento y validación. Esto no sustituye una auditoría de similitud visual. La reserva final no se abrió y el manifest indica que no se utilizó.

136 de los 154 niveles críticos de entrenamiento son sintéticos, aproximadamente el 88%. Hay datos críticos reales, pero la transferencia a escenas nuevas necesita evaluación propia. Solo siete niveles enseñan la clase no evaluable, uno de ellos real.

## Resultados que sí se pueden interpretar

En las comparaciones desde foto completa, con confianza 0,25 y emparejamiento único por IoU de máscara >= 0,5:

| Medida de validación | Resultado |
|---|---:|
| Niveles anotados localizados, sin exigir estado correcto | 35/36 (97,2%) |
| Suficientes localizados y clasificados correctamente | 33/34 (97,1%) |
| No evaluables clasificados correctamente | 0/2 |
| Predicciones sin pareja geométrica | 12 |
| Alertas emitidas | 2 |
| Alertas incorrectas según las etiquetas actuales | 2 |
| Recall de alertas críticas | No calculable: cero referencias críticas |

El resultado no significa que el modelo falle todos los vacíos: esa capacidad no fue medida fuera del entrenamiento. En entrenamiento reconoce como alerta 153/154 referencias críticas, incluidas 18/18 reales. Es evidencia de ajuste a ejemplos conocidos, no rendimiento en escenas nuevas. Confunde 17 vacíos con baja; ambos estados generan alerta, por lo que no penaliza la misma medida que la clasificación exacta.

La [validación estándar](metricas_validacion.json) registra mAP50 de máscaras de 74,47% y mAP50-95 de 56,59%. Su precisión de 98,22% no es una exactitud general de stock ni la precisión de alertas a confianza 0,25. Es otro resumen del evaluador, con otro procedimiento y solo dos clases presentes en las referencias. No mezclarlo con los recuentos de [alertas](metricas_alertas.json).

## Revisión visual y problemas concretos

Se inspeccionaron las cinco comparaciones de validación, las curvas y dos ejemplos de entrenamiento.

**REAL_04 y REAL_05:** localiza y clasifica correctamente los 12 niveles anotados de cada foto. Las máscaras siguen razonablemente las repisas. Hay diferencias en el cierre superior, pero no impiden el emparejamiento.

**REAL_22:** los seis niveles anotados quedan correctamente localizados y clasificados. Las cinco detecciones extra corresponden visualmente a niveles del tramo izquierdo sin anotaciones. El evaluador las cuenta como falsos positivos porque analiza toda la imagen sin región de exclusión. No son cinco repisas inventadas por el modelo. [Comparación](comparaciones/REAL_22_val.jpg).

**REAL_29:** de los tres niveles anotados, identifica el suficiente, convierte un no evaluable en baja y omite el otro. Además detecta niveles visibles fuera de la región anotada. La alerta es incorrecta respecto de la referencia: cuando no hay evidencia suficiente para decidir, la salida debería preservar esa incertidumbre. [Comparación](comparaciones/REAL_29_val.jpg).

**REAL_30:** produce dos predicciones sobre prácticamente el mismo nivel, una suficiente y otra baja. Se comprobó una IoU de 0,994 entre las máscaras guardadas 03 y 05. El emparejamiento geométrico selecciona la predicción baja para esa referencia y deja la suficiente como extra. Es una contradicción real en la salida; el estado contabilizado también depende del emparejamiento. Hay otra predicción sobre un nivel inferior no anotado. [Comparación](comparaciones/REAL_30_val.jpg).

**REAL_03, entrenamiento:** los polígonos de referencia 6, 7 y 8 aparecen como vacío en niveles derechos que incluyen paquetes visibles. Según la guía que cuenta todo producto visible dentro del nivel, estas etiquetas requieren revisión humana. El modelo también emite estados superpuestos en esta imagen. Esto no autoriza a corregir automáticamente las etiquetas; hay que confirmar la región y el contenido. [Comparación](comparaciones/REAL_03_train.jpg).

**EQ_15_V1, entrenamiento:** el ejemplo sintético muestra localización y estados coherentes con las referencias. Es útil para verificar que el modelo puede representar las clases, pero la imagen participó en el aprendizaje. [Comparación](comparaciones/EQ_15_V1_train.jpg).

La exportación declara `full_image`. Al dejar niveles visibles fuera de la anotación sin recortar ni declarar una región ignorada, entrenamiento y evaluación pueden tratar como fondo regiones que visualmente siguen siendo niveles. Conservar una zona de análisis es válido; hay que hacer que la preparación de imágenes y el evaluador respeten esa misma zona.

## Qué haría a continuación

1. **Añadir una evaluación real con vacíos y bajos de escenas nuevas**, anotada sin consultar las predicciones. Usar primero los pesos actuales permite comprobarlos sin reentrenar. Si esa evaluación se usa para ajustar el sistema, pasa a ser desarrollo; conservar una prueba final independiente.
2. **Revisar REAL_03 y auditar estados críticos del conjunto.** No ajustar etiquetas para hacer coincidir al modelo: aplicar la guía a los productos realmente visibles. Reforzar también ejemplos reales de no evaluable.
3. **Unificar la región de análisis.** Recortar a regiones seleccionadas o implementar exclusiones coherentes; alternativamente anotar todos los niveles que deban ser objetivo en la imagen completa. La solución debe aplicarse a entrenamiento y evaluación, no solo a la visualización.
4. **Resolver predicciones contradictorias del mismo nivel.** Comparar una política que conserve una sola hipótesis por región física, por ejemplo supresión entre clases con cuidado de no unir niveles vecinos. Evaluarla sobre las mismas referencias; no asumir que mejorará sin medirla. El código actual no activa supresión independiente de clase.
5. **Después decidir si hace falta reentrenar o cambiar ajustes.** El estado actual no justifica elegir otra arquitectura ni aumentar épocas como primer paso. Conservar este checkpoint como referencia.

## Alcance de la revisión

Se revisaron archivos guardados, el código de evaluación y las imágenes de comparación. Se reagruparon recuentos por origen real/sintético y se calculó el solapamiento indicado con las máscaras binarias guardadas. No se ejecutó otro entrenamiento ni otra inferencia, no se modificaron etiquetas, pesos o métricas, y no se interfirió con otros trabajos activos. Las detecciones extra y las dudas de anotación impiden interpretar todos los errores registrados como fallos puros del modelo.
