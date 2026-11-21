# Stress-test ciego de ocupación · 60 variantes sintéticas (`03_Pruebas_ocupacion`) · 21 de noviembre de 2026

> **Alcance:** prueba complementaria de sensibilidad (`Recall`) sobre **60 variantes editadas** provenientes de **60 originales reales `.jpg` distintos** (`20` ocupación media, `20` ocupación baja, `20` nivel superior vacío), sin coincidencia con `train`, `val`, `Ohiggins 3`, `Ohiggins 4`, `Set final` ni `ejemplos`. Se reporta **separada** del test real de 171 fotos vírgenes.

- **Modelo YOLO:** `V3-cierre-revisado-20261110` (`conf = 0.6`)
- **Estimador de ocupación:** `linea_a_20261119_v2_3_productos_bajos` (`umbral = 52.0`)
- **Dispositivo:** `CPU`
- **SHA-256 sellado verificado:** `1eac10860ff602e61e2e78ffa00df294236938e07307995721aa32e27f2ccca8`

## 1. Puerta de entrada (Calidad + Oclusiones · Global 60)

- Ambas `apta`: **60** · Ambas `no_evaluable`: **0** · Sistema bloqueó / humano `apta`: **0** · Sistema `apta` / humano bloqueó: **0**

## 2. Segmentación YOLO (auditoría visual humana)

- Global (`60`): **TP = 304** (`OK=304`, `Mal=0`) · **FP = 1** · **FN = 0** · **Precision:** `99.67%` · **Recall:** `100.00%` · **F1:** `99.84%` · **Exacto:** `59/60`

## 3. Estimador de disponibilidad visual (evaluación ciega · Global 60 y por tipo)

- Niveles evaluados (`Global 60`): **304** · `Revisar`: **9** (`2.96%`)

| Alcance y Vista (por nivel) | Total | TP | FP | FN | TN | Accuracy | Precision | Recall | Especificidad | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Global 60 · A (Decididos)** | 295 | 102 | 13 | 6 | 174 | 93.56% | 88.70% | 94.44% | 93.05% | 91.48% |
| **Global 60 · B (Operativa con Revisar)** | 304 | 108 | 16 | 6 | 174 | 92.76% | 87.10% | 94.74% | 91.58% | 90.76% |
| **Global 60 · C (Bruto `< 52`)** | 304 | 105 | 14 | 9 | 176 | 92.43% | 88.24% | 92.11% | 92.63% | 90.13% |
| **Ocupación media (`ocupacion_01`) · A (Decididos)** | 105 | 4 | 5 | 1 | 95 | 94.29% | 44.44% | 80.00% | 95.00% | 57.14% |
| **Ocupación media (`ocupacion_01`) · B (Operativa)** | 108 | 4 | 8 | 1 | 95 | 91.67% | 33.33% | 80.00% | 92.23% | 47.06% |
| **Ocupación baja (`ocupacion_02`) · A (Decididos)** | 91 | 76 | 8 | 4 | 3 | 86.81% | 90.48% | 95.00% | 27.27% | 92.68% |
| **Ocupación baja (`ocupacion_02`) · B (Operativa)** | 97 | 82 | 8 | 4 | 3 | 87.63% | 91.11% | 95.35% | 27.27% | 93.18% |
| **Nivel superior vacío (`superior_vacio`) · A (Decididos)** | 99 | 22 | 0 | 1 | 76 | 98.99% | 100.00% | 95.65% | 100.00% | 97.78% |
| **Nivel superior vacío (`superior_vacio`) · B (Operativa)** | 99 | 22 | 0 | 1 | 76 | 98.99% | 100.00% | 95.65% | 100.00% | 97.78% |

### Ocupación por foto completa (Global 60)

| Vista (por foto completa) | Total | TP | FP | FN | TN | Accuracy | Precision | Recall | Especificidad | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Foto · `reponer` decidido** | 60 | 43 | 3 | 1 | 13 | 93.33% | 93.48% | 97.73% | 81.25% | 95.56% |
| **Foto · `reponer` + `revisar`** | 60 | 43 | 6 | 1 | 10 | 88.33% | 87.76% | 97.73% | 62.50% | 92.47% |

## 4. Latencia End-to-End

- Media: **765.76 ms/foto** · Mediana (P50): **768.83 ms** · P95: **866.9 ms** · Rango: `609.01–979.78 ms`

## 5. Discrepancias registradas (Global 60)

Total de eventos/discrepancias: **29** (ver detalle en [stress_test_ocupacion_60_20261121.json](stress_test_ocupacion_60_20261121.json)).

| Tipo | Foto | Variante | Sucursal | Nivel | Humano | Sistema | Puntaje / Detalle |
|---|---|---|---|---|---|---|---|
| `occ_fn` | `S03` (`Marcoleta__Lote_01__2710_ma_014__superior_vacio.png`) | `superior_vacio` | Marcoleta | N1 | reponer | suficiente | pct=63.12 |
| `yolo_falso_positivo` | `S04` (`Express Independencia__20261103_105630__superior_vacio.png`) | `superior_vacio` | Express Independencia | N5 | - | - | conf=0.8627 |
| `occ_fp` | `S14` (`Arauco Quilicura 2__2810_aq_012__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N4 | suficiente | reponer | pct=48.85 |
| `occ_revisar` | `S22` (`Arauco Quilicura 2__2810_aq_031__ocupacion_01.png`) | `ocupacion_01` | Arauco Quilicura 2 | N5 | suficiente | revisar | raw=40.99 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_fn` | `S26` (`Marcoleta__Lote_02__2710_ma_079__ocupacion_01.png`) | `ocupacion_01` | Marcoleta | N3 | reponer | suficiente | pct=57.84 |
| `occ_revisar` | `S29` (`Arauco Quilicura 2__2810_aq_039__ocupacion_01.png`) | `ocupacion_01` | Arauco Quilicura 2 | N5 | suficiente | revisar | raw=42.31 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_fn` | `S30` (`Arauco Quilicura 2__2810_aq_002__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N5 | reponer | suficiente | pct=55.89 |
| `occ_fp` | `S32` (`Ohiggins__Lote_02__2109_oh_056__ocupacion_01.png`) | `ocupacion_01` | Ohiggins | N1 | suficiente | reponer | pct=64.52 |
| `occ_fp` | `S32` (`Ohiggins__Lote_02__2109_oh_056__ocupacion_01.png`) | `ocupacion_01` | Ohiggins | N5 | suficiente | reponer | pct=35.1 |
| `occ_revisar` | `S33` (`Arauco Quilicura 2__2810_aq_029__ocupacion_01.png`) | `ocupacion_01` | Arauco Quilicura 2 | N5 | suficiente | revisar | raw=47.34 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_fn` | `S37` (`Marcoleta__Lote_01__2710_ma_023__ocupacion_02.png`) | `ocupacion_02` | Marcoleta | N4 | reponer | suficiente | pct=65.62 |
| `occ_revisar` | `S41` (`Arauco Quilicura 2__2810_aq_024__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N1 | reponer | revisar | raw=46.78 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_revisar` | `S41` (`Arauco Quilicura 2__2810_aq_024__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N2 | reponer | revisar | raw=43.25 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_fn` | `S41` (`Arauco Quilicura 2__2810_aq_024__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N3 | reponer | suficiente | pct=53.79 |
| `occ_revisar` | `S41` (`Arauco Quilicura 2__2810_aq_024__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N4 | reponer | revisar | raw=51.63 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_revisar` | `S41` (`Arauco Quilicura 2__2810_aq_024__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N6 | reponer | revisar | raw=46.29 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_fp` | `S44` (`Ohiggins__Lote_02__2109_oh_057__ocupacion_01.png`) | `ocupacion_01` | Ohiggins | N6 | suficiente | reponer | pct=59.38 |
| `occ_fp` | `S49` (`Marcoleta__Lote_01__2710_ma_030__ocupacion_02.png`) | `ocupacion_02` | Marcoleta | N3 | suficiente | reponer | pct=48.07 |
| `occ_fn` | `S49` (`Marcoleta__Lote_01__2710_ma_030__ocupacion_02.png`) | `ocupacion_02` | Marcoleta | N5 | reponer | suficiente | pct=70.26 |
| `occ_fp` | `S50` (`Arauco Quilicura 2__2810_aq_037__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N4 | suficiente | reponer | pct=33.46 |
| `occ_fp` | `S50` (`Arauco Quilicura 2__2810_aq_037__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N5 | suficiente | reponer | pct=48.83 |
| `occ_revisar` | `S55` (`Arauco Quilicura 2__2810_aq_010__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N5 | reponer | revisar | raw=48.07 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_revisar` | `S56` (`Arauco Quilicura 2__2810_aq_022__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N3 | reponer | revisar | raw=46.19 (Frente continuo con señal débil o baja iluminación; confirmar si hay envases oscuros.) |
| `occ_fp` | `S56` (`Arauco Quilicura 2__2810_aq_022__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N5 | suficiente | reponer | pct=43.47 |
| `occ_fp` | `S56` (`Arauco Quilicura 2__2810_aq_022__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N6 | suficiente | reponer | pct=50.17 |
| `occ_fp` | `S57` (`Arauco Quilicura 2__2810_aq_036__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N4 | suficiente | reponer | pct=47.07 |
| `occ_fp` | `S57` (`Arauco Quilicura 2__2810_aq_036__ocupacion_02.png`) | `ocupacion_02` | Arauco Quilicura 2 | N5 | suficiente | reponer | pct=49.86 |
| `occ_fp` | `S60` (`Arauco Quilicura 2__2810_aq_018__ocupacion_01.png`) | `ocupacion_01` | Arauco Quilicura 2 | N1 | suficiente | reponer | pct=45.51 |
| `occ_fp` | `S60` (`Arauco Quilicura 2__2810_aq_018__ocupacion_01.png`) | `ocupacion_01` | Arauco Quilicura 2 | N3 | suficiente | reponer | pct=48.6 |

[Resumen estructurado JSON](stress_test_ocupacion_60_20261121.json) · [Evaluación ciega real 171](evaluacion_ciega_real_171_20261121.md) · [Ficha del modelo](../Modelo_V3_actual.md)
