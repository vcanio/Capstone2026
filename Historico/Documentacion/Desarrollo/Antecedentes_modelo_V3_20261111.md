# Antecedentes del modelo V3 y de su distribución

Detalle histórico trasladado desde el README principal el 11/11/2026 para centrar su lectura en el modelo vigente. Los recuentos y resultados conservan la etapa a la que pertenecen. La condición de oficial de un peso anterior se refiere a su fecha de adopción; el único oficial vigente es **V3-cierre-revisado-20261110**.

[Modelo vigente y límites](../../../Documentacion/Modelo_V3_actual.md) · [Volver al README](../../../README.md).

## Cadena de entrenamiento y procedencia

### Qué imágenes utilizó el modelo oficial

El peso actual deriva de **tres etapas de entrenamiento propias**, además del preentrenamiento general de `yolo26n-seg.pt`. El candidato anterior del 10/11 no forma parte de esta cadena. Estos recuentos corresponden a los archivos efectivamente incluidos en los manifiestos de los ensayos, no a todas las fotos reunidas o revisadas por el equipo.

| Etapa de la cadena del modelo | Train reales | Train sintéticas | Train total | Validación real | Validación sintética |
|---|---:|---:|---:|---:|---:|
| Afinado iniciado el 2/11, base del refuerzo | 153 | 179 | **332** | 32 | 37 |
| Refuerzo del 5/11 (oficial anterior) | 152 | 19 | **171** | 59 | 34 |
| Cierre con contornos revisados del 10/11 | 203 | 53 | **256** | 11 | 0 |

Las **256** son las imágenes del último refuerzo, con **1.298 polígonos**, no toda la experiencia previa del modelo. Las tres etapas reúnen **519 fuentes distintas de train por SHA-256: 299 reales y 220 sintéticas**. No son escenas independientes, ni incluyen aumentos internos o preentrenamiento general. El último ensayo conserva 174 train del cierre anterior y añade 82 antiguas val con sus escenas/familias completas; estas 82 dejan de ser validación independiente. Las 11 val actuales contienen 55 polígonos y no actualizan pesos por gradiente. [Catálogo vigente](../../../Documentacion/Evidencias/catalogo_modelo_oficial_cierre_20261110.json).

### Antecedente: composición del refuerzo del 5/11, por procedencia

Se contrastaron el manifiesto del ensayo oficial, el manifiesto de su exportación y las listas `train.txt`, `val_real.txt` y `val_sintetica.txt`. La exportación final contiene **264 archivos: 171 para entrenar y 93 para validar**. Las 93 de validación no se usaron para ajustar los pesos por gradiente.

| Procedencia registrada | Train reales | Train sintéticas | Val reales | Val sintéticas | Total |
|---|---:|---:|---:|---:|---:|
| Líder 2 (lote histórico) | 26 | 0 | 22 | 0 | 48 |
| Líder Express de octubre: originales y variantes A/B/C | 30 | 0 | 8 | 24 | 62 |
| Refuerzo de papeles de octubre | 1 | 0 | 0 | 0 | 1 |
| Refuerzo: Arauco Quilicura 2 | 18 | 0 | 3 | 0 | 21 |
| Refuerzo: Express Independencia | 23 | 0 | 5 | 0 | 28 |
| Refuerzo: Express Sta Luisa | 10 | 0 | 3 | 0 | 13 |
| Refuerzo: Marcoleta | 35 | 0 | 13 | 0 | 48 |
| Refuerzo: Ohiggins | 9 | 7 | 5 | 5 | 26 |
| Superiores vacíos D (sintéticas de octubre) | 0 | 12 | 0 | 5 | 17 |
| **Total del refuerzo del 5/11** | **152** | **19** | **59** | **34** | **264** |

Los nombres de la tabla son identificadores de procedencia de los registros. «Líder 2» no se presenta como nombre oficial de una sucursal. Los lotes nuevos de Arauco Quilicura 2, Express Independencia, Express Sta Luisa, Marcoleta y Ohiggins aportan **136 archivos incluidos**: 102 train y 34 val. Las restantes 128 referencias corresponden al repaso y a validación de los lotes anteriores.

La partición preparatoria tenía 275 registros; la exportación excluyó 11 según las decisiones documentadas. **R254 permanece excluida deliberadamente**, sin restaurarla ni usarla como negativo. Se mantuvieron las relaciones por escenas/familias; no se repartieron las fotos al azar. La reserva final de **63 fotos de test sigue sin utilizarse** y no forma parte de los 264 archivos de esta exportación.

[Recuento verificable, hashes de manifiestos y alcance](../../../Documentacion/Evidencias/catalogo_modelo_oficial_20261110.json) · [Modelo y métricas](../../../Documentacion/Modelo_V3_actual.md).

## Comparación documentada con el peso anterior

Sobre las mismas 11 fotos de validación, el peso anterior del 5/11 y el cierre revisado del 10/11 detectaron 54 de 55 niveles, con cero falsos positivos. El IoU medio fue 93,52 % y 93,39 %, respectivamente. Esta comparación reducida no demuestra superioridad global del cierre adoptado; su mAP no se compara directamente con el agregado de las antiguas 59 val reales.

La adopción del último peso respondió a la decisión de Vicente tras su revisión visual. Las 68 fotos de Ohiggins 3 tienen 65 aceptadas y tres con siete contornos incorrectos; esa revisión no es mAP, recall ni exactitud de ocupación. R065 mantiene una omisión en un diagnóstico de train. [Adopción y verificaciones](../../../Documentacion/Evidencias/adopcion_cierre_revisado_20261110.md).

## Distribuciones anteriores

La entrega conjunta del 11/11 incluye el cierre revisado del 10/11. Las pruebas conjuntas del 10/11, incluida r2 con licencias, conservan el peso del 5/11 y Línea A del 8/11. La release del 5/11 conserva además su estimador anterior y su estructura con `iniciar.cmd`. Sus instrucciones y resultados se interpretan dentro de cada entrega.

Los activos anteriores mantienen sus nombres, fechas y bytes. [Releases e instrucciones históricas](../../../Entregables/README.md#distribuciones-anteriores). Preparar una entrega nueva no reemplaza los activos anteriores.

## Catálogo histórico

El catálogo de **469 imágenes de octubre** y su partición **337 train / 69 val / 63 test** son antecedentes de otra etapa. No describen la selección del último refuerzo ni el total de fuentes usadas en la cadena del modelo actual. Sus registros se conservan para trazabilidad en el [archivo histórico](../../README.md).

La preparación y la revisión de datos no certifican por sí solas la precisión de ocupación ni convierten las imágenes sintéticas en evidencia de generalización. El ajuste de Línea A y la evaluación final del sistema son trabajos distintos del entrenamiento geométrico descrito aquí.
