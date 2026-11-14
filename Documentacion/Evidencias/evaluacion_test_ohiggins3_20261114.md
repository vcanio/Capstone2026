# Evaluación cuantitativa de test · Ohiggins 3 (14/11/2026)

Evaluación congelada (sin reentrenar pesos ni recalibrar umbrales) del modelo oficial **`V3-cierre-revisado-20261110`** (`YOLO26n-seg`, SHA-256 `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`) y **Línea A** (`linea_a_20261113_techo_y_panel_liso`, umbral `52.0`) sobre **Ohiggins 3**: **68 fotos reales únicas** (68 SHA-256 distintos, `0` coincidencia con `train` o `val`), anotadas en CVAT (`proyecto 11`, `task 47`, `job 94`, `subset="test"`, **354 polígonos `Nivel`** con `delimitacion="completa"`).

El test histórico de **63 fotos** (`v3_458_20261023`) queda formalmente retirado como conjunto de evaluación: 19 de sus fotos reales entraron al conjunto de entrenamiento de `v3_cierre_revisado_20261110` tras su aprobación de uso en desarrollo, y las 44 restantes carecen de polígonos anotados en CVAT y pertenecen a escenas ya vistas en `train`.

---

## 1. Segmentación de niveles (`YOLO26n-seg`)

* **Validación estándar Ultralytics (`imgsz=640`, GPU GTX 1660 SUPER):**
  * `Precision(B / M)`: **0,9991**
  * `Recall(B / M)`: **1,0000**
  * `mAP50(B / M)`: **0,9950** (`99,50 %`)
  * `mAP50-95(B)`: **0,9197** (`91,97 %`) · `mAP50-95(M)`: **0,9036** (`90,36 %`)
  * `fitness`: **1,8233**
* **Emparejamiento operativo (`IoU ≥ 0,50`, `retina_masks=True`, idéntico a `conf=0,60` y `conf=0,25`):**
  * **TP / FP / FN:** **354 / 0 / 0** (`Precision = 1,0000`, `Recall = 1,0000`, `F1 = 1,0000`)
  * **Conteo exacto por foto:** **68 / 68 (100 %)**
  * **IoU de máscara:** media **0,9390** · mediana **0,9498** · mínimo **0,7298** (`20261109_133429.jpg`)
  * **Latencia GPU (`model.predict`, `conf=0,60`, GTX 1660 SUPER, 68 fotos):** media **77,15 ms** · `P50 = 80,34 ms` · `P95 = 101,33 ms`
  * **Latencia CPU (`model.predict`, `conf=0,60`, AMD Ryzen 5 3600, muestra 15 fotos):** media **225,94 ms** · `P50 = 221,08 ms` · `P95 = 241,36 ms`

---

## 2. Disponibilidad visual y alertas · Línea A (`umbral = 52,0`, evaluación ciega)

Las 354 detecciones fueron etiquetadas a ciegas por revisión humana sin visualizar el puntaje del algoritmo (`36` `reponer`, `318` `suficiente`, `0` `no_evaluable`; incluye 2 correcciones humanas auditadas en `20261109_133933.jpg` Nivel 3 y `20261109_134039.jpg` Nivel 2) y cruzadas contra [ocupacion_linea_a.py](../../Aplicacion/ocupacion_linea_a.py):

| Alcance | TP | FP | FN | TN | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Por nivel (354)** | 30 | 2 | 6 | 316 | **97,74 %** | **93,75 %** | **83,33 %** | **88,24 %** |
| **Por foto completa (68)** | 22 | 2 | 3 | 41 | **92,65 %** | **91,67 %** | **88,00 %** | **89,80 %** |

* **Especificidad por nivel (`suficiente`):** **99,37 %** (`316 / 318`)
* **Latencia E2E promedio en producción (`YOLO + Línea A`):** **1.371,9 ms/foto** en GPU (`GTX 1660 SUPER`, 68 fotos) vs **1.442,5 ms/foto** en CPU (`AMD Ryzen 5 3600`, `P50 = 1.425,0 ms`, `P95 = 1.576,9 ms`, muestra 15 fotos; diferencia de solo ~70 ms E2E porque decodificación EXIF, grillas y codificación PNG dominan el tiempo total).

### Análisis de errores observados (`6 FN` y `2 FP`)

* **Falsos Negativos (6):** `20261109_133159.jpg` (N2: `60,57 %`, gap `35,29 %`), `20261109_134033.jpg` (N6: `79,28 %`, gap `0,0 %`), `20261109_134039.jpg` (N6: `75,07 %`, gap `0,0 %`), `20261109_134153.jpg` (N4: `55,84 %`, gap `41,18 %`), `20261109_134245.jpg` (N6: `74,87 %`, gap `0,0 %`), `20261109_134336.jpg` (N5: `67,20 %`, gap `0,0 %`).
  * **Patrón principal:** 4 de los 6 FN ocurren en niveles inferiores (`Nivel 5` o `Nivel 6`) con `max_gap_pct = 0,0 %`, donde la vista picada expone el fondo o reflejos del estante inferior generando textura uniforme sin hueco limpio.
* **Falsos Positivos (2):** `20261109_133300.jpg` (N4: `38,66 %`), `20261109_133413.jpg` (N6: `47,35 %`).

Ver [resumen estructurado JSON](evaluacion_test_ohiggins3_20261114.json) · [Estado vigente](../Estado_V3_actual.json) · [Ficha del modelo](../Modelo_V3_actual.md).
