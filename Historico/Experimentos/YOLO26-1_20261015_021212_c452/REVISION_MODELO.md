> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../../Modelos/Actual/README.md).

# Revisión de YOLO26-1 y comparación con YOLO11-1

14 de octubre de 2026, hora de Santiago. Comparación exclusiva de los dos entrenamientos nuevos. No se usan los ensayos exploratorios anteriores.

**YOLO26 mejora el mAP de máscaras y acierta un nivel suficiente adicional en esta validación. Ambos localizan 35/36 niveles anotados. No se puede elegir un ganador para detectar faltantes: las cinco fotos de validación no contienen vacíos ni bajos, y ninguno reconoce los dos no evaluables a confianza 0,25.**

## Comparabilidad verificada

- Misma copia `datos_20261015_012453_4ba1d339`.
- Snapshot, partición y entorno idénticos byte a byte.
- Mismos 182 archivos de imágenes y etiquetas por SHA-256: 91 imágenes y 91 etiquetas. Los archivos cache se excluyeron.
- Misma resolución 640, batch 2, tasa inicial 0,001, semilla 42 y máximo de 100 épocas. El código común usa AdamW y paciencia 20.
- En la configuración de interfaz solo cambian pesos iniciales y nombre del ensayo. Las arquitecturas y sus funciones de pérdida son diferentes: no comparar directamente sus pérdidas absolutas.

Fuentes: [configuración YOLO26](config_interfaz.json), [configuración YOLO11](../YOLO11-1_20261015_013749_f709/config_interfaz.json) y los datasets guardados en ambos ensayos.

## Ejecución y métricas

YOLO26 terminó correctamente, estado `done` y código 0. Realizó 52 épocas; la mejor fue la 32. La parada fue por 20 épocas sin mejora, no por un error. Aprendizaje: unos 22,1 minutos; proceso completo: unos 24,6 minutos. Esta duración menor incluye menos épocas y no demuestra mayor velocidad por época o de inferencia.

| Medida | YOLO11-1 | YOLO26-1 |
|---|---:|---:|
| Épocas / mejor época | 92 / 72 | 52 / 32 |
| mAP50 de máscaras | 74,47% | 73,38% |
| mAP50-95 de máscaras | 56,59% | 62,40% |
| Niveles localizados, independientemente del estado | 35/36 | 35/36 |
| Suficientes correctamente localizados y clasificados | 33/34 | 34/34 |
| No evaluables correctamente identificados | 0/2 | 0/2 |
| Predicciones sin pareja geométrica | 12 | 11 |
| Alertas incorrectas según las referencias actuales | 2 | 0 |
| Recall de vacíos/bajos en validación | No calculable | No calculable |

Los recuentos usan confianza 0,25 y emparejamiento único por IoU de máscara >= 0,5. El mAP procede de la validación estándar, que evalúa otro conjunto de umbrales; no es porcentaje de exactitud de stock. La mejora de mAP50-95 es de 5,81 puntos porcentuales, mientras mAP50 baja 1,09 puntos.

YOLO26 emite únicamente suficiente en las cinco fotos a ese filtro. Cero falsas alertas es favorable sobre estos negativos, pero no demuestra sensibilidad a faltantes. Además, clasifica un no evaluable como suficiente y omite el otro: no emitir una alerta no equivale a reconocer correctamente la incertidumbre.

Fuentes: [métricas YOLO26](metricas_validacion.json), [alertas YOLO26](metricas_alertas.json), [métricas YOLO11](../YOLO11-1_20261015_013749_f709/metricas_validacion.json) y [alertas YOLO11](../YOLO11-1_20261015_013749_f709/metricas_alertas.json).

## Inspección visual

Se inspeccionaron las cinco comparaciones de validación, REAL_03 de entrenamiento y las curvas.

- **REAL_04 y REAL_05:** ambos localizan y clasifican los 12 niveles anotados de cada foto. YOLO26 mantiene una separación clara entre repisas; el borde superior sigue teniendo diferencias respecto de las referencias.
- **REAL_30:** YOLO26 acierta los tres niveles suficientes y no repite la contradicción suficiente/baja de YOLO11 sobre el nivel inferior anotado. Su región superior se extiende más arriba que la referencia, por lo que no es una mejora uniforme de todos los bordes. [Imagen](comparaciones/REAL_30_val.jpg).
- **REAL_22:** acierta los seis niveles anotados, pero registra seis detecciones extra. Varias son repisas visibles fuera de la zona anotada; los contornos también muestran irregularidades. No interpretar todas las extras como objetos inventados. [Imagen](comparaciones/REAL_22_val.jpg).
- **REAL_29:** además de fallar los dos no evaluables, identifica dos paneles azules de cartelería superior como niveles suficientes. Son falsos candidatos estructurales visibles, distintos de las repisas reales sin anotaciones. [Imagen](comparaciones/REAL_29_val.jpg).
- **REAL_03, entrenamiento:** ajusta mejor varias etiquetas vacías que YOLO11, pero mantiene una superposición vacío/baja y omite un nivel crítico. Siguen presentes las referencias vacías con paquetes visibles que requieren revisión humana; coincidir con ellas no certifica un criterio correcto. [Imagen](comparaciones/REAL_03_train.jpg).

## Ajuste a entrenamiento, separado de generalización

| Alertas sobre imágenes de entrenamiento | YOLO11 | YOLO26 |
|---|---:|---:|
| Críticas acertadas, reales + sintéticas | 153/154 | 152/154 |
| Falsas alertas según referencias | 37 | 13 |
| Vacíos con estado exacto correcto | 63/80 | 77/80 |
| Bajos con estado exacto correcto | 73/74 | 70/74 |
| Críticas acertadas, solo fotos reales | 18/18 | 16/18 |
| Falsas alertas, solo fotos reales | 5 | 2 |

Se reagruparon los resultados por prefijo REAL/EQ mediante la misma función de agregación del evaluador. YOLO26 ofrece menos falsas alertas registradas, con algunas omisiones adicionales. Los números muestran ajuste a datos conocidos; no son un test independiente ni establecen superioridad general. Las anotaciones incompletas y dudosas afectan también estos recuentos.

## Recomendación

Conservar ambos `best.pt`. YOLO26 es un candidato competitivo y obtiene mejor mAP de máscaras en este conjunto, pero no hay base suficiente para reemplazar definitivamente YOLO11 como detector de faltantes.

El siguiente experimento útil es evaluar ambos sobre el mismo lote nuevo de fotos reales con vacíos, bajos, suficientes y no evaluables, manteniendo idéntica región de análisis y criterio de emparejamiento. Incluir casos con carteles y otras estructuras horizontales para comprobar falsos candidatos. Revisar antes las etiquetas señaladas y hacer coherente la exclusión de zonas entre anotación, entrenamiento y evaluación. Si el lote se usa para elegir o ajustar modelos, tratarlo como validación de desarrollo y conservar una prueba final independiente.

Se revisaron resultados guardados y archivos locales. No se ejecutó entrenamiento ni inferencia adicional, ni se modificaron pesos, métricas o anotaciones. No se abrió la reserva final.
