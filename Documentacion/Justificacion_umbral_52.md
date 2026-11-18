# Justificación técnica del umbral 52 del índice de disponibilidad visual

## Qué representa

El estimador produce un índice visual entre 0 y 100 a partir de bordes, gradientes, color, textura y huecos. El corte 52 convierte ese índice en una decisión de alerta. No expresa un porcentaje físico de productos, unidades o volumen; tampoco es la confianza de YOLO, que en cliente es 0,60. El 30 % del enunciado es una referencia inicial que exige justificar el criterio final; no existe una equivalencia automática entre ese porcentaje físico y la escala del índice.

Esta justificación reconstruye lo que permiten afirmar los registros históricos. No inventa una regla de selección a posteriori ni modifica el umbral. La [evidencia agregada](Evidencias/justificacion_umbral_52.json) conserva los barridos y métricas tal como estaban guardados, junto con los SHA-256 de las fuentes privadas. No incluye fotografías ni etiquetas por imagen.

## Ajuste inicial y comprobación posterior

El recibo del 8/11 registra **164 niveles etiquetados: 52 de ajuste y 112 de validación**, correspondientes a 10 y 21 góndolas, respectivamente. El [evaluador histórico](https://github.com/vcanio/Capstone2026/blob/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Laboratorio/Ocupacion/evaluar_linea_a.py) restringe el barrido a `split == train`, de 30 a 66 en incrementos de 2. Calcula precisión, recall automático y F1 frente a las etiquetas humanas `baja_disponibilidad`/`vacio` como alerta y `suficiente` como no alerta. Los casos no evaluables se excluyen de la decisión binaria.

En los 52 niveles de ajuste había **6 alertas y 46 suficientes**. El mayor índice entre las alertas era **44,49**, y el menor entre los suficientes, **55,88**. Con la regla `índice < umbral`, los cortes muestreados **46, 48, 50, 52 y 54** separaban correctamente las dos clases en ese registro:

| Umbral | TP | FP | FN | Precisión | Recall automático | F1 |
|---|---:|---:|---:|---:|---:|---:|
| 30 | 4 | 0 | 2 | 100,00 % | 66,67 % | 80,00 % |
| 44 | 5 | 0 | 1 | 100,00 % | 83,33 % | 90,91 % |
| 46, 48, 50, **52**, 54 | 6 | 0 | 0 | 100,00 % | 100,00 % | 100,00 % |
| 56 | 6 | 1 | 0 | 85,71 % | 100,00 % | 92,31 % |

**Interpretación técnica:** 52 es un punto de operación admisible dentro de una meseta que recupera las alertas perdidas con 30 sin introducir la falsa alerta observada con 56. Los datos justifican usarlo como corte preliminar. **No prueban que deba ser exactamente 52 y no 50 o 54.** El punto medio entre 44,49 y 55,88 que guarda el recibo es **50,19**, no 52; no se atribuye su elección a esa fórmula ni a un máximo único de F1.

Los **112 niveles posteriores** eran 80 reales y 32 sintéticos: 16 alertas y 96 suficientes. Con 52 se registraron **15 TP, 0 FP, 1 FN y 96 TN**: precisión 100 %, recall 93,75 % y F1 96,77 %. Es una comprobación separada del ajuste en aquella etapa, con máscaras humanas; no mide por sí sola el flujo completo con máscaras predichas por YOLO.

La limitación es relevante: en ajuste había 37 niveles reales, todos suficientes, y 15 sintéticos que aportaban las 6 alertas. En validación solo había **2 alertas reales**, de las que se detectó **1**; las otras 14 alertas eran sintéticas y se detectaron todas. Por eso el resultado agregado no demuestra una calibración robusta en tienda. Además, son particiones históricas: las migraciones posteriores de imágenes a train impiden tratarlas como validación independiente del modelo oficial actual.

## Comprobación en la muestra ampliada

El registro ampliado, generado el **9/11/2026 a las 01:07 UTC** (8/11 por la noche en Chile), contiene 355 niveles de ajuste (51 alertas y 304 suficientes) y 482 de validación. Sobre su barrido de ajuste:

| Umbral | TP | FP | FN como Suficiente | Alertas derivadas a Revisar | Precisión | Recall automático | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 30 | 33 | 1 | 15 | 3 | 97,06 % | 64,71 % | 77,65 % |
| 46 | 48 | 2 | 2 | 1 | 96,00 % | 94,12 % | **95,05 %** |
| 50 | 49 | 4 | 2 | 0 | 92,45 % | 96,08 % | 94,23 % |
| **52** | 49 | 4 | 2 | 0 | 92,45 % | 96,08 % | 94,23 % |
| 54 | 49 | 4 | 2 | 0 | 92,45 % | 96,08 % | 94,23 % |
| 56 | 49 | 6 | 2 | 0 | 89,09 % | 96,08 % | 92,45 % |

El recall automático usa las 51 alertas como denominador; por eso penaliza también las derivadas a `Revisar`. La columna FN del barrido original cuenta solo falsos `Suficiente`; la revisión se muestra aparte para evitar confundir ambos conceptos.

Este registro **no demuestra que 52 maximice F1**: 46 obtiene un F1 algo mayor, mientras 52 detecta una alerta más y produce dos falsas alertas adicionales. Permite describir un compromiso entre sensibilidad y falsas alertas, pero no consta una función de coste o regla de desempate que obligue a elegir exactamente 52. Conservar 52 mantiene el punto de operación adoptado y evita presentarlo como un óptimo universal. Esta lectura es una interpretación de los registros, no un procedimiento de selección que se afirme ejecutado en su momento.

## Alcance para la versión actual

El estimador vigente usa `CALIBRATED_THRESHOLD_PCT = 52.0`, pero incorpora reglas adicionales: un hueco de frente puede activar `Reponer` aunque el índice sea mayor, y una zona ambigua puede terminar en `Revisar`. Por tanto, las decisiones no dependen exclusivamente de cruzar 52.

Los resultados de Ohiggins 3 documentan evaluación o reevaluación posterior; no fueron la evidencia de este barrido inicial ni deben utilizarse aquí para elegir de nuevo el umbral. Los registros permiten justificar **un corte empírico preliminar y trazable**. Demostrar el mejor corte de v2.2 requiere un plan nuevo, más alertas reales, un criterio de coste o selección explícito y un conjunto independiente sin exposición previa. Esta actualización solo lee registros y documenta su alcance: no ejecuta inferencia, entrenamiento ni recalibración.

[README principal](../README.md#por-qué-se-utiliza-el-umbral-52) · [Ficha del modelo](Modelo_V3_actual.md) · [Resumen numérico](Evidencias/justificacion_umbral_52.json)
