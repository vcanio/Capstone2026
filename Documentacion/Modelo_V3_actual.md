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

| Máscaras | Fotos | mAP50 | mAP50–95 |
|---|---:|---:|---:|
| Validación real | 11 | 99,50 % | 90,04 % |

La partición de desarrollo es `v3_cierre_revisado_20261110`, con selección `cierre_yolo_contornos_revisados_20261110`. Las escenas relacionadas se agruparon; 82 antiguas val pasaron a train por autorización de Vicente y dejaron de ser validación independiente. Las 11 val actuales (55 polígonos) pertenecen a tres escenas: no comparar su mAP directamente con las antiguas 59 val reales. En las mismas 11 fotos, oficial anterior y nuevo tienen 54 TP, 0 FP y 1 FN; IoU medio 93,52 % → 93,39 %. No se demuestra una mejora global con ese panel reducido.

En la revisión visual posterior de las 68 fotos de Ohiggins 3, Vicente marcó 65 correctas y tres con siete contornos incorrectos; no marcó omisiones. El 95,59 % es fracción de fotos aceptadas por el revisor, no precisión/recall por nivel ni mAP. No hay etiquetas CVAT completas de ese lote ni una comparación equivalente con el oficial anterior. R065 sigue omitiendo el superior en un diagnóstico de train. No se evaluó ocupación. La reserva histórica de 63 fotos permanece sin utilizar.

El modelo localiza áreas de niveles; no decide directamente reposición ni detecta personas u obstáculos. Las dos apps conservan las máscaras y usan Línea A: índice visual 0–100 y umbral 52, con ajuste preliminar. El ZIP publicado del 5/11 conserva el estimador anterior con umbral 30 %. Requiere revisión humana y no mide stock oculto. La mediana es un criterio de anotación y no se fuerza durante la inferencia.

Pueden existir omisiones y contornos incorrectos. Las incidencias históricas de superiores no se declaran resueltas por esta adopción. La preferencia de Vicente por el nuevo peso no se presenta como superioridad global demostrada. Las pruebas de funcionamiento no constituyen una calibración de ocupación ni una evaluación exhaustiva de precisión. [Registro de adopción y verificación de ambas apps](Evidencias/adopcion_cierre_revisado_20261110.md) · [Resumen estructurado](Estado_V3_actual.json) · [Catálogo de la cadena de entrenamiento](Evidencias/catalogo_modelo_oficial_cierre_20261110.json).
