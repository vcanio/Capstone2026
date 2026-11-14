# Modelo actual de Walmart Visión

**V3 oficial · cierre con contornos revisados**, adoptado por Vicente el 10 de noviembre de 2026 como predeterminado en revisión (8095) y cliente (8098), para cerrar de momento el localizador y centrarse en ocupación. La entrega de prueba del 11/11 incluye este modelo y el cliente actualizado. Las releases anteriores conservan sus modelos y archivos.

| Campo | Valor |
|---|---|
| Arquitectura | YOLO26n-seg |
| Clase | `Nivel` |
| Checkpoint | `best.pt` |
| Ensayo | `v3_cierre_yolo_contornos_revisados_20261110_222620_aa7c` |
| SHA-256 | `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5` |
| Afinado | 256 imágenes (203 reales/53 sintéticas), 1.298 polígonos, 40 épocas, AdamW, lr 0,0001, batch 2, resolución 640, semilla 42 |
| Selección del best | `best.pt` guardado por el entrenador según validación real; no usar `last.pt` como equivalente |
| Confianza en la app | Inicial 0,60; ajustable desde 0,25 |

| Máscaras | Fotos | Niveles | mAP50 | mAP50–95 (M) | Emparejamiento operativo |
|---|---:|---:|---:|---:|---|
| Validación real | 11 | 55 | 99,50 % | 90,04 % | 54 TP, 0 FP, 1 FN |
| **Test independiente (`Ohiggins 3`)** | **68** | **354** | **99,50 %** | **90,36 %** | **354 TP, 0 FP, 0 FN** (`IoU` media `0,9390`) |

La partición de desarrollo es `v3_cierre_revisado_20261110`, con selección `cierre_yolo_contornos_revisados_20261110`. Las escenas relacionadas se agruparon; 82 antiguas val pasaron a train por autorización de Vicente y dejaron de ser validación independiente. Las 11 val actuales (55 polígonos) pertenecen a tres escenas: no comparar su mAP directamente con las antiguas 59 val reales.

El **14/11/2026** se cerró la evaluación cuantitativa independiente sobre las **68 fotos únicas de Ohiggins 3** (`0` coincidencia con `train`/`val`), anotadas íntegramente en CVAT (`354` polígonos `Nivel`, `delimitacion="completa"`):
* **Segmentación YOLO (`conf = 0,60` y `0,25`):** **354 TP / 0 FP / 0 FN** (`Precision = 1,0000`, `Recall = 1,0000`), conteo exacto en **68/68 fotos**, `mAP50(M) = 0,9950`, `mAP50-95(M) = 0,9036` y latencia YOLO media de **77,15 ms** en GPU (`GTX 1660 SUPER`) vs **225,94 ms** en CPU (`AMD Ryzen 5 3600`, muestra 15 fotos).
* **Disponibilidad visual · Línea A (`linea_a_20261113_techo_y_panel_liso`, umbral `52,0`, evaluación ciega):** sobre las 354 detecciones (`36` `reponer` / `318` `suficiente` reales), logró **Accuracy `97,74 %`**, **Precision `93,75 %`**, **Recall `83,33 %`**, **F1 `88,24 %`** (`30 TP / 2 FP / 6 FN / 316 TN`); por foto completa **Accuracy `92,65 %`** y **F1 `89,80 %`**. 4 de los 6 falsos negativos ocurren en el nivel inferior (`Nivel 5` o `6`) con `max_gap_pct = 0,0 %`. Latencia E2E promedio (`YOLO + Línea A`): **1.371,9 ms/foto** en GPU vs **1.442,5 ms/foto** en CPU (`P95 = 1.576,9 ms`).
* El test histórico de **63 fotos** quedó formalmente retirado (19 entraron a `train` y 44 pertenecen a escenas vistas sin polígonos CVAT). Ver [Evaluación test Ohiggins 3 (14/11)](Evidencias/evaluacion_test_ohiggins3_20261114.md).

El modelo localiza áreas de niveles; no decide directamente reposición ni detecta personas u obstáculos. Las dos apps conservan las máscaras y usan Línea A: índice visual 0–100 y umbral 52, evaluado en test ciego. El ZIP publicado del 5/11 conserva el estimador anterior con umbral 30 %. Requiere revisión humana y no mide stock oculto. La mediana es un criterio de anotación y no se fuerza durante la inferencia.

Pueden existir omisiones y contornos incorrectos en condiciones nuevas (`R065` conserva omisión superior en diagnóstico de train). Las incidencias históricas de superiores no se declaran resueltas globalmente por esta adopción. [Registro de adopción y verificación de ambas apps](Evidencias/adopcion_cierre_revisado_20261110.md) · [Evaluación test Ohiggins 3](Evidencias/evaluacion_test_ohiggins3_20261114.md) · [Resumen estructurado](Estado_V3_actual.json) · [Catálogo de la cadena de entrenamiento](Evidencias/catalogo_modelo_oficial_cierre_20261110.json).
