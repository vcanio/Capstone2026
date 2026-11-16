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
* **Disponibilidad visual · Línea A (`linea_a_20261113_techo_y_panel_liso`, umbral `52,0`, evaluación ciega base):** sobre las 354 detecciones (`36` `reponer` / `318` `suficiente` reales), logró **Accuracy `97,74 %`**, **Precision `93,75 %`**, **Recall `83,33 %`**, **F1 `88,24 %`** (`30 TP / 2 FP / 6 FN / 316 TN`); por foto completa **Accuracy `92,65 %`** y **F1 `89,80 %`**. 4 de los 6 falsos negativos ocurren en el nivel inferior (`Nivel 5` o `6`) con `max_gap_pct = 0,0 %`. Latencia E2E promedio (`YOLO + Línea A`): **1.371,9 ms/foto** en GPU vs **1.442,5 ms/foto** en CPU (`P95 = 1.576,9 ms`).
* **Disponibilidad visual · Línea A v2.2 vigente (`linea_a_20261116_v2_2_cajas_sacos_picada`, umbral `52,0`):** sobre la base de `v2.1` (filtro de bandeja/piso expuesto en vista picada, cielo abierto v2 en nivel superior, bandas verticales relativas, puenteo de islas débiles de 2 columnas, alerta de quiebre parcial de frente y guarda `low_contrast_continuous_front`), incorpora protección para sacos blancos apilados bajo sombra, reconocimiento de cajas máster bicolor impresas (`_is_bicolor_printed_box`) y desplazamiento de banda para producto retraído en vista picada (`_has_recessed_upper_product`). Sobre los 354 niveles de `Ohiggins 3` mantiene **Accuracy `98,87 %`**, **Precision `92,11 %`**, **Recall `97,22 %`**, **Especificidad `99,06 %`**, **F1 `94,59 %`** (`35 TP / 3 FP / 1 FN / 315 TN`), además de verificarse operativamente sobre **193 fotos / 893 niveles** en 3 capturas (`9_11 Ohiggins`, `14_11 Ohiggins` y `15_11 Marcoleta`, `0 / 193` fotos sin niveles) y corregir las falsas alertas observadas en sacos, cajas grandes y niveles inferiores de `Marcoleta`.
* El test histórico de **63 fotos** quedó formalmente retirado (19 entraron a `train` y 44 pertenecen a escenas vistas sin polígonos CVAT). Ver [Evaluación test Ohiggins 3 (14/11)](Evidencias/evaluacion_test_ohiggins3_20261114.md).

## Casos límite y fallos conocidos

* **Segmentación YOLO (`YOLO26n-seg`):** puede omitir o recortar el nivel superior abierto sin techo físico claro (`1 FN` en 55 instancias de `val`; casos puntuales de desarrollo `R065` y `le_g10` 029/030) al no imponerse la mediana en inferencia; puede incluir holgura menor en bordes superiores/laterales (`IoU` mínimo `72,98 %` en `20261109_133429.jpg`, 7 contornos en 3/68 fotos); si un estante queda cortado por el borde de cámara (`near_frame`), [vision_v3.py](../Aplicacion/vision_v3.py) lo deriva a `Revisar · zona visible`; fotos muy borrosas, oscuras o quemadas se bloquean antes de YOLO mediante [calidad_foto.py](../Aplicacion/calidad_foto.py).
* **Ocupación Línea A v2.2:** mide disponibilidad visual frontal 2D (no detecta falta de stock detrás de una primera fila completa); frentes oscuros de bajo contraste pueden requerir revisión (`low_contrast_continuous_front`, conservando `raw_pct`); huecos menores a `35 %` rodeados de textura alta pueden superar `52` (`1 FN` residual en `Ohiggins 3`), mientras sombras marcadas o separadores anchos pueden activar alerta (`3 FP` residuales); personas o carros frente al estante siguen requiriendo revisión visual humana.

El modelo localiza áreas de niveles; no decide directamente reposición ni detecta personas u obstáculos. Las dos apps conservan las máscaras y usan Línea A v2.2: índice visual 0–100 y umbral 52, evaluado en test ciego. La entrega vigente del 16/11 ([`walmart-vision-apps-2026-11-16`](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-2026-11-16)) incluye `Línea A v2.2`, [`calidad_foto.py`](../Aplicacion/calidad_foto.py) y el visor cliente actualizado con severidad operativa, índice bruto y reanálisis automático al actualizar revisión; las releases anteriores (`13/11`, `11/11`, `5/11`) conservan sus versiones originales. Requiere revisión humana y no mide stock oculto. La mediana es un criterio de anotación y no se fuerza durante la inferencia.

Pueden existir omisiones y contornos incorrectos en condiciones nuevas (`R065` conserva omisión superior en diagnóstico de train). Las incidencias históricas de superiores no se declaran resueltas globalmente por esta adopción. [Registro de adopción y verificación de ambas apps](Evidencias/adopcion_cierre_revisado_20261110.md) · [Evaluación test Ohiggins 3](Evidencias/evaluacion_test_ohiggins3_20261114.md) · [Resumen estructurado](Estado_V3_actual.json) · [Catálogo de la cadena de entrenamiento](Evidencias/catalogo_modelo_oficial_cierre_20261110.json).
