# Entrenamiento geométrico V3 desde el panel

Integración del 25 de octubre de 2026, solicitada por el usuario para preparar el primer entrenamiento. El entrenamiento se inicia únicamente al pulsar **Entrenar V3**; preparar el flujo y verificar la GPU no ejecuta épocas.

## Aumentos vigentes desde el 2 de noviembre de 2026

Por autorización de Vicente, los próximos entrenamientos V3 aplican rotación suave (`degrees=3`), desplazamiento (`translate=0.03`) y escala (`scale=0.10`). Se mantienen los aumentos de tono, saturación y brillo (`hsv_h=0.01`, `hsv_s=0.2`, `hsv_v=0.2`). Mosaic, mixup, copy-paste, inclinación, perspectiva y volteos permanecen desactivados.

Las imágenes sintéticas de la selección se mantienen como ejemplos válidos y representativos de situaciones reales; estos aumentos automáticos son adicionales y no cambian la selección. Los parámetros efectivos quedan registrados en `parametros_v3.json` de cada nuevo ensayo. Este ajuste no modifica ensayos anteriores, pesos, anotaciones ni particiones, y no inicia entrenamiento. La reserva test sigue excluida. Los parámetros del primer ensayo descritos más abajo son antecedentes.

Comprobación del ajuste: 19 pruebas existentes de entrenamiento y afinado correctas dentro del contenedor del panel, con modelos simulados. Una importación nueva del entrenador en ese mismo contenedor confirmó los tres valores y la conservación del resto de aumentos. El worker carga el módulo en un proceso nuevo al iniciar cada trabajo; el próximo entrenamiento recibe el ajuste sin reiniciar el panel. Esta comprobación no mide una mejora del modelo.

## Afinado preparado desde pesos propios

El laboratorio admite ahora el `best.pt` de un ensayo geométrico V3 terminado, con una clase `Nivel`, métricas finalizadas y sin uso del test. Registra y vuelve a comprobar los hashes de los pesos, manifiesto del padre, exportación y selección. Inicia un ensayo nuevo con optimizador nuevo (`resume=False`), conservando los pesos aprendidos.

La selección `afinado_papeles_huevos_20261025` carga el modelo padre y los parámetros preparados automáticamente: **113 fotos, máximo 40 épocas, paciencia 10, AdamW lr 0.0001, 640, batch 2 y semilla 42**. Incluye 49 casos dirigidos y 64 de repaso. La GPU verificó que sus 844 tensores se transfieren íntegros. El calentamiento dura una época, con bias LR inicial 0.

Abrir el laboratorio local y pulsar **Configurar afinado con 113 fotos**; revisar y pulsar **Entrenar V3**. La validación común son 22 fotos reales y 47 sintéticas; el test permanece reservado. La referencia del padre ya está calculada sobre esa misma validación, sin entrenar. Consultar el plan de afinado (`Historico/Datos/Preparados/V3/Refuerzos/afinado_papeles_huevos_20261025/README.md`, archivo del entorno local; fuera de esta distribución). Las instrucciones del primer ensayo que siguen se conservan como antecedentes.

## Primer ensayo

Abrir [el panel local](http://127.0.0.1:8090/), seleccionar V3 y entrar en Entrenar. Los valores iniciales son:

| Campo | Valor |
|---|---|
| Exportación revisada | `v3_20261025_033415_6e0d391f/exportacion_b797db0d` |
| Nombre | `v3_niveles_yolo26n_base` |
| Modelo de partida | `YOLO26n-seg`, pesos generales locales |
| Épocas máximas | 100 |
| Resolución | 640 |
| Batch | 2 |
| Tasa de aprendizaje | 0.001 |
| Semilla | 42 |
| Parada sin mejora | 20 épocas |
| Optimizador fijo | AdamW |

Propósito: «Base V3: detectar y delimitar áreas útiles de niveles. Validación real y diagnóstico sintético separados; sin usar la prueba final».

Es una configuración inicial conservadora para la GTX 1660 SUPER de 6 GB; no implica que sea la configuración de mayor precisión. El nombre recibe automáticamente fecha UTC y sufijo al pulsar Entrenar V3, conservando los ensayos previos. Para comparar después YOLO11n-seg, usar otro ensayo y el mismo conjunto de datos, cambiando solo el modelo y el nombre.

## Separación e integridad

### Comparación reducida preparada el 25 de octubre

Por autorización del usuario se añadió **Fotos para aprender**: base completa o **Originales + una variante vacía por familia**. La segunda conserva 126 originales y 40 variantes `A_vacios` en entrenamiento (166 fotos), con las mismas 28 reales y 40 sintéticas de validación. Las 160 variantes apartadas permanecen conservadas. No se cambia la partición de 458 imágenes ni las exclusiones de CVAT.

El nombre propuesto es `v3_niveles_una_vacia`, con el mismo modelo de partida, resolución 640, batch 2, tasa 0,001, semilla 42, máximo 100 épocas y paciencia 20 que la base. Comparar inferencia a confianza mínima 0,60. Al tener menos fotos, hay menos pasos por época; reportar las épocas y pasos efectivos, además de tiempo y calidad. El resultado de esta comparación todavía está pendiente: preparar la selección no entrena ni demuestra una mejora.

El flujo guarda la selección autorizada y sus hashes en el ensayo, registra el recuento seleccionado y el recuento de la fuente por separado y copia únicamente las 234 imágenes de desarrollo seleccionadas. El prevuelo nuevo verificó esas imágenes y una pasada de GPU con cero pasos de optimización y cero imágenes de test abiertas. El usuario inicia el ensayo con **Entrenar V3**. Selección, listas y autorización (`Historico/Datos/Preparados/V3/Selecciones/originales_una_vacia_20261025/README.md`, archivo del entorno local; fuera de esta distribución).

El **piloto de módulos** está en otro proyecto CVAT, enlazado desde el mismo formulario. Tiene 12 fotos, 13 propuestas de módulo pendientes de revisión y 64 copias de niveles; no añade una clase a este entrenador. Criterio y límites del piloto (`Historico/Datos/Preparados/V3/Pilotos/modulos_20261025/README.md`, archivo del entorno local; fuera de esta distribución).

El enlace **Ver las 166 fotos seleccionadas**, debajo del resumen de entrenamiento, abre una galería con búsqueda, filtro de originales y variantes, paginación y acceso al original en grande. Solo admite fotos de `train` incluidas en la selección y comprueba su integridad al servirlas; no mezcla validación, test o variantes apartadas.

El entrenador `Herramientas/Modelos/entrenamiento_v3.py` usa la clase única `Nivel`; no usa el entrenador de estados ni vuelve a importar CVAT. Comprueba la revisión humana, política, snapshot, geometrías, partición, listas e integridad de imágenes y etiquetas de desarrollo. Rechaza etiquetas editadas, exportaciones incompletas o sin revisión y pesos de partida de los modelos de estados V1/V2.

La exportación revisada actual contiene 326 imágenes para aprender, 28 reales para validación, 40 sintéticas para diagnóstico y 63 de prueba final reservadas. La foto desactivada permanece excluida. Las 458 asignaciones originales no cambian.

Al iniciar, el worker congela una copia independiente de **394 imágenes de desarrollo** y sus etiquetas, mostrando el avance. Las 153 fotos con orientación EXIF 6 se giran como ya las representa CVAT y se guardan como PNG sin otra pérdida de compresión; no se giran ni cambian sus coordenadas. Se registran nombres, operaciones y hashes antes/después. Las 241 restantes se copian sin cambios. Los píxeles y etiquetas de la reserva final no se copian al dataset del ensayo, no entran en sus YAML y no se abren para el prevuelo. La partición completa y el recibo de exportación se guardan como trazabilidad, conservando la reserva identificada.

Se desactivan mosaico, mezcla, copy-paste, rotaciones, recortes y cambios geométricos aleatorios en esta base. Se permiten variaciones suaves de tono, saturación y brillo. Las máscaras de instancias permanecen separadas, con factor 2. AMP queda desactivado para conservar el comportamiento estable y sin comprobaciones que descarguen otros pesos.

## Resultados y seguimiento

El worker registra etapas, épocas y métricas. Cada ensayo queda en `Experimentos/<nombre_con_fecha>/`, con manifest, hashes, configuración, entorno, logs del trabajo y dataset congelado. Ultralytics guarda curvas, `best.pt` y `last.pt` en `entrenamiento/`.

El seguimiento visual V3 muestra curvas de mAP50–95 de máscaras y pérdida de entrenamiento/validación real, última métrica, mejor valor observado y época, tiempo y ejemplos generados por el ensayo. Se actualiza al completar épocas y mantiene una tabla accesible con los valores. Los datos sintéticos no se mezclan en esas curvas; su evaluación posterior aparece separada.

La selección de `best.pt` usa exclusivamente validación real. Después se evalúan esos pesos en `val_real` y `val_sintetica` por separado, guardando `metricas_geometria_v3.json`. El seguimiento V3 muestra precisión, recall y mAP de máscaras sin sumar ambos conjuntos. No calcula estados de reposición, ocupación ni alertas. La interfaz del cliente y la evaluación final siguen siendo integraciones distintas.

## Verificación antes de pulsar

`check_runtime` comprueba los datos y decodifica desarrollo, carga los pesos locales, construye la arquitectura con una clase y hace una pasada de inferencia con tensores vacíos del tamaño y batch configurados. No crea optimizador, no actualiza pesos, no ejecuta épocas y no usa fotografías de prueba. Esta comprobación no demuestra todavía la calidad del modelo entrenado ni garantiza un tiempo de ejecución.

Las pruebas de contrato ejecutan el despacho y la evaluación con un modelo simulado, sin aprendizaje real; el prevuelo de GPU usa la arquitectura real. La evidencia inicial está en `.resguardo/integracion_entrenamiento_v3_20261025/` y el recibo del entorno en `.config-modelo/v3_preflight_20261025.json`.

[Criterio V3](Criterio_V3_niveles.md) · [Preparación revisada](Preparacion_V3_parciales_revisados.md) · [Parámetros de Ultralytics](https://docs.ultralytics.com/modes/train/).
