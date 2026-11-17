# Entrenamiento y procedencia del modelo oficial

El único oficial vigente es V3-cierre-revisado-20261110, YOLO26n-seg, clase Nivel. La [ficha](Modelo_V3_actual.md) y [modelos.json](../Aplicacion/modelos.json) identifican el peso compartido por las dos apps. Es un afinado de pesos de Ultralytics, no una arquitectura ni un entrenamiento desde cero.

## Tres etapas de la cadena

| Etapa | Train | Val real | Val sintética |
|---|---:|---:|---:|
| Primer afinado · 2/11 | 332 | 32 | 37 |
| Refuerzo geométrico · 5/11 | 171 | 59 | 34 |
| Cierre revisado · 10/11 | 256 | 11 | 0 |

Los recuentos son los archivos efectivamente preparados para cada ensayo, no la suma de los inventarios fuente. Hay repaso entre etapas: la cadena reúne **519 fuentes train distintas por SHA-256, 299 reales y 220 sintéticas**. No son 519 escenas independientes ni incluyen preentrenamiento general o aumentos internos. Las 256 imágenes del cierre no representan toda la experiencia previa. El [catálogo congelado](Evidencias/catalogo_modelo_oficial_cierre_20261110.json) conserva IDs de ensayos y hashes de sus manifiestos; sus rutas de laboratorio son referencias del entorno original, no archivos requeridos en el clon actual.

## Último ensayo

Ensayo: v3_cierre_yolo_contornos_revisados_20261110_222620_aa7c. Parte del oficial del 5/11, con 256 train (203 reales/53 sintéticas), 1.298 polígonos train y 11 val reales con 55 polígonos. Configuración: 40 épocas, paciencia 10, AdamW, lr 0,0001, batch 2, resolución 640 y semilla 42. best.pt se seleccionó por validación real; last.pt no es equivalente.

Partición: v3_cierre_revisado_20261110. Selección: cierre_yolo_contornos_revisados_20261110. Preparación: v3_20261110_221357_2075807e, exportacion_5f25123f. SHA-256 del registro de partición conservado localmente: `9f36ab96ca69163d070f85527acae07007109fdc4b426bf5bd2b97696fd6e8b5`. Los datasets, anotaciones completas y preparaciones privadas no se incluyen en el clon.

Se trasladaron 82 antiguas val a train con cierre por escenas/familias; dejaron de ser validación independiente. Las 11 val actuales corresponden a tres escenas y no se comparan directamente con las antiguas 59 o 93 val. R254 permanece excluida. El test histórico de 63 fotos quedó retirado formalmente el 14/11/2026 (19 entraron a train y 44 pertenecen a escenas ya vistas sin polígonos CVAT) y fue reemplazado como evaluación independiente por **Ohiggins 3** (`68` fotos / `354` polígonos, `0` coincidencia con `train`/`val`).

## Resultados y límites

En las 11 val actuales, las máscaras tienen mAP50 99,50 % y mAP50–95 90,04 %. En una comparación bajo las mismas condiciones, oficial anterior y adoptado registran 54 TP, 0 FP y 1 FN; IoU medio 93,52 % → 93,39 %. Este panel pequeño no demuestra mejora global.

El 14/11/2026 se completó la anotación CVAT (`subset="test"`) y la evaluación congelada sobre las 68 fotos de **Ohiggins 3** (`354` niveles): **YOLO** obtuvo `mAP50 99,50 %`, `mAP50-95(M) 90,36 %` y `354 TP / 0 FP / 0 FN` (`68/68` conteos exactos); **Línea A** línea base (`20261113`) obtuvo `Accuracy 97,74 %`, `Precision 93,75 %`, `Recall 83,33 %` y `F1 88,24 %` por nivel (`F1 89,80 %` por foto), y la revisión **v2.2** (`linea_a_20261116_v2_2_cajas_sacos_picada`) alcanza `Accuracy 98,87 %`, `Precision 92,11 %`, `Recall 97,22 %` y `F1 94,59 %` (`35 TP / 3 FP / 1 FN / 315 TN`), además de validarse operativamente sobre **193 fotos / 893 niveles** en 3 capturas (`9_11 Ohiggins`, `14_11 Ohiggins` y `15_11 Marcoleta`, `0 / 193` fotos sin detecciones). Ohiggins 3 sigue fuera de train; los casos límite de YOLO y Línea A se detallan en [Modelo V3 actual](Modelo_V3_actual.md). Ver [Evaluación test Ohiggins 3](Evidencias/evaluacion_test_ohiggins3_20261114.md).

La calibración inicial de Línea A se definió en desarrollo (112 niveles con máscaras humanas: 15/16 alertas sin falsas alertas) y posteriormente quedó validada en frío con predicciones YOLO sobre Ohiggins 3. No extrapolar los resultados de localización a exactitud de ocupación o stock físico.

Los antecedentes, registros de correcciones y comparaciones se conservan mediante [Archivo del desarrollo](Archivo_del_desarrollo.md). La incidencia de tres fuentes V1 ausentes no se resuelve con esta reorganización ni permite afirmar auditoría global de datos aprobada. No se ha entrenado ni evaluado test para simplificar el repositorio.

## Scripts reproducibles incluidos

Los scripts para preparar anotaciones CVAT (incluida la regla de la mediana para el nivel superior y validación anti-fuga por escenas), configurar el ajuste fino reproducible (`seed=42`) y verificar/reproducir las métricas sobre `Ohiggins 3` están disponibles en [`Entrenamiento/`](../Entrenamiento/README.md):

- [`Entrenamiento/preparar_datos_cvat.py`](../Entrenamiento/preparar_datos_cvat.py) (`--self-check` y exportación YOLO-seg)
- [`Entrenamiento/entrenar_yolo26n_seg.py`](../Entrenamiento/entrenar_yolo26n_seg.py) (`--dry-run` y plantilla [`data.template.yaml`](../Entrenamiento/data.template.yaml))
- [`Entrenamiento/evaluar_ohiggins3.py`](../Entrenamiento/evaluar_ohiggins3.py) (`--verify-receipt` y evaluación de directorio)
