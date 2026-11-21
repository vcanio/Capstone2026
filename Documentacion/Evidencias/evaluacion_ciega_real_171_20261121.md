# Test final end-to-end ciego completo · 171 fotos reales vírgenes · 21 de noviembre de 2026

Evaluación congelada y **100 % ciega** sobre las **171 fotos reales `.jpg` vírgenes** de `01_Virgenes_sin_uso` (excluyendo `Ohiggins 4` y las 22 `.png` sintéticas), con `0` coincidencia SHA-256 contra `train`, `val`, `Ohiggins 3`, `Ohiggins 4`, `Set final`, `Fallos comunes` y los 8 ejemplos del cliente.

- **Modelo YOLO:** `V3-cierre-revisado-20261110` (`conf = 0.6`)
- **Estimador de ocupación:** `linea_a_20261119_v2_3_productos_bajos` (`umbral = 52.0`)
- **Dispositivo:** `CPU`
- **SHA-256 sellado verificado:** `7b917550183ad09b0d8c2cc0a45392eaf9e15dab6de065659d2c966f944c8376`

## 1. Puerta de entrada (Calidad + Oclusiones · Global 171)

- Ambas `apta`: **171** · Ambas `no_evaluable`: **0** · Sistema bloqueó / humano `apta`: **0** · Sistema `apta` / humano bloqueó: **0**

## 2. Segmentación YOLO (auditoría visual humana)

> Nota: auditoría visual sobre detecciones de `V3-cierre-revisado-20261110`; no equivale a `mAP` ni `IoU` de polígonos CVAT.

| Alcance | Fotos | TP (OK / Mal) | FP | FN | Precision | Recall | F1 | Contorno OK | Exacto |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| **Global (`171`)** | 171 | 854 (854 / 0) | 0 | 2 | 100.00% | 99.77% | 99.88% | 100.00% | 169/171 |
| **Inéditas (`131`)** | 131 | 661 (661 / 0) | 0 | 2 | 100.00% | 99.70% | 99.85% | 100.00% | 129/131 |
| **Piloto re-etiquetado (`40`)** | 40 | 193 (193 / 0) | 0 | 0 | 100.00% | 100.00% | 100.00% | 100.00% | 40/40 |

### YOLO por sucursal (Global 171)

| Sucursal | Fotos | TP (OK / Mal) | FP | FN | Precision | Recall | F1 | Exacto |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Arauco Quilicura 2 | 35 | 179 (179 / 0) | 0 | 0 | 100.00% | 100.00% | 100.00% | 35/35 |
| Express Independencia | 17 | 75 (75 / 0) | 0 | 0 | 100.00% | 100.00% | 100.00% | 17/17 |
| Express Sta Luisa | 12 | 56 (56 / 0) | 0 | 0 | 100.00% | 100.00% | 100.00% | 12/12 |
| Express Sta Luisa 2 | 12 | 53 (53 / 0) | 0 | 1 | 100.00% | 98.15% | 99.07% | 11/12 |
| Marcoleta | 69 | 349 (349 / 0) | 0 | 1 | 100.00% | 99.71% | 99.86% | 68/69 |
| Ohiggins | 26 | 142 (142 / 0) | 0 | 0 | 100.00% | 100.00% | 100.00% | 26/26 |

## 3. Estimador de disponibilidad visual (`linea_a_20261119_v2_3_productos_bajos` · evaluación ciega)

- Niveles evaluados (`Global 171`): **854** · `Revisar`: **3** (`0.35%`)
- Niveles evaluados (`Inéditas 131`): **661** · `Revisar`: **3** (`0.45%`)

| Alcance y Vista (por nivel) | Total | TP | FP | FN | TN | Accuracy | Precision | Recall | Especificidad | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Global 171 · A (Decididos)** | 851 | 25 | 6 | 3 | 817 | 98.94% | 80.65% | 89.29% | 99.27% | 84.75% |
| **Global 171 · B (Operativa con Revisar)** | 854 | 26 | 8 | 3 | 817 | 98.71% | 76.47% | 89.66% | 99.03% | 82.54% |
| **Global 171 · C (Bruto `< 52`)** | 854 | 25 | 5 | 4 | 820 | 98.95% | 83.33% | 86.21% | 99.39% | 84.75% |
| **Inéditas 131 · A (Decididos)** | 658 | 20 | 1 | 2 | 635 | 99.54% | 95.24% | 90.91% | 99.84% | 93.02% |
| **Inéditas 131 · B (Operativa con Revisar)** | 661 | 21 | 3 | 2 | 635 | 99.24% | 87.50% | 91.30% | 99.53% | 89.36% |
| **Piloto 40 · A (Decididos)** | 193 | 5 | 5 | 1 | 182 | 96.89% | 50.00% | 83.33% | 97.33% | 62.50% |
| **Piloto 40 · B (Operativa con Revisar)** | 193 | 5 | 5 | 1 | 182 | 96.89% | 50.00% | 83.33% | 97.33% | 62.50% |

### Ocupación por sucursal (Global 171 · Vista A Decididos)

| Sucursal | Total | TP | FP | FN | TN | Revisar | Accuracy | Precision | Recall | Especificidad | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Arauco Quilicura 2 | 179 | 0 | 0 | 0 | 179 | 0 | 100.00% | 0.00% | 0.00% | 100.00% | 0.00% |
| Express Independencia | 75 | 1 | 2 | 0 | 72 | 0 | 97.33% | 33.33% | 100.00% | 97.30% | 50.00% |
| Express Sta Luisa | 56 | 2 | 0 | 0 | 54 | 0 | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| Express Sta Luisa 2 | 51 | 1 | 3 | 0 | 47 | 2 | 94.12% | 25.00% | 100.00% | 94.00% | 40.00% |
| Marcoleta | 348 | 9 | 1 | 2 | 336 | 1 | 99.14% | 90.00% | 81.82% | 99.70% | 85.71% |
| Ohiggins | 142 | 12 | 0 | 1 | 129 | 0 | 99.30% | 100.00% | 92.31% | 100.00% | 96.00% |

### Ocupación por foto completa (Global 171)

| Vista (por foto completa) | Total | TP | FP | FN | TN | Accuracy | Precision | Recall | Especificidad | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Foto · `reponer` decidido** | 171 | 21 | 5 | 4 | 141 | 94.74% | 80.77% | 84.00% | 96.58% | 82.35% |
| **Foto · `reponer` + `revisar`** | 171 | 22 | 7 | 3 | 139 | 94.15% | 75.86% | 88.00% | 95.21% | 81.48% |

## 4. Latencia End-to-End

- Media: **2120.61 ms/foto** · Mediana (P50): **2198.35 ms** · P95: **2541.1 ms** · Rango: `907.33–3098.85 ms`

## 5. Discrepancias registradas (Global 171)

Total de eventos/discrepancias: **14** (ver detalle completo en [evaluacion_ciega_real_171_20261121.json](evaluacion_ciega_real_171_20261121.json)).

| Tipo | Foto | Subconjunto | Sucursal | Nivel | Humano | Sistema | Puntaje / Detalle |
|---|---|---|---|---|---|---|---|
| `occ_fn` | `V001` (`2710_ma_014.jpg`) | inedita131 | Marcoleta | N1 | reponer | suficiente | pct=60.18 |
| `occ_fn` | `V003` (`2109_oh_045.jpg`) | piloto40 | Ohiggins | N4 | reponer | suficiente | pct=53.17 |
| `occ_fp` | `V036` (`2710_ma_076.jpg`) | piloto40 | Marcoleta | N1 | suficiente | reponer | pct=51.13 |
| `occ_fp` | `V057` (`20261111_205605.jpg`) | piloto40 | Express Sta Luisa 2 | N3 | suficiente | reponer | pct=54.84 |
| `occ_fp` | `V069` (`20261111_205128.jpg`) | piloto40 | Express Sta Luisa 2 | N5 | suficiente | reponer | pct=33.25 |
| `occ_fp` | `V083` (`20261103_105933.jpg`) | piloto40 | Express Independencia | N1 | suficiente | reponer | pct=34.77 |
| `occ_fp` | `V085` (`20261111_205610.jpg`) | piloto40 | Express Sta Luisa 2 | N1 | suficiente | reponer | pct=48.55 |
| `occ_fn` | `V094` (`2710_ma_045.jpg`) | inedita131 | Marcoleta | N3 | reponer | suficiente | pct=57.36 |
| `occ_revisar` | `V118` (`20261111_205418.jpg`) | inedita131 | Express Sta Luisa 2 | N3 | reponer | revisar | pct=57.27 (Contorno junto al encuadre: revisa lo que queda fuera.) |
| `yolo_falso_negativo` | `V118` (`20261111_205418.jpg`) | inedita131 | Express Sta Luisa 2 | FN=1 | - | - |  |
| `occ_revisar` | `V130` (`20261111_205501.jpg`) | inedita131 | Express Sta Luisa 2 | N1 | suficiente | revisar | pct=78.14 (Contorno junto al encuadre: revisa lo que queda fuera.) |
| `yolo_falso_negativo` | `V136` (`2710_ma_050.jpg`) | inedita131 | Marcoleta | FN=1 | - | - |  |
| `occ_fp` | `V157` (`20261103_105753.jpg`) | inedita131 | Express Independencia | N1 | suficiente | reponer | pct=40.08 |
| `occ_revisar` | `V168` (`2710_ma_020.jpg`) | inedita131 | Marcoleta | N1 | suficiente | revisar | raw=92.79 (Señal alta tipo cartel sobre banda inferior-media vacía.) |

[Resumen estructurado JSON](evaluacion_ciega_real_171_20261121.json) · [Estado vigente](../Estado_V3_actual.json) · [Ficha del modelo](../Modelo_V3_actual.md)
