# Revisión de la tarea 22 — 19 de octubre de 2026

**Actualización:** las correcciones autorizadas ya están aplicadas. [Ver comparativas y validar](correcciones/validacion.html). Este informe conserva la captura anterior y los motivos originales de revisión.

El lote requiere correcciones y adjudicación antes de cerrar. No se modificaron las anotaciones de CVAT durante esta revisión.

[Ver hallazgos con imágenes y enlaces a CVAT](revision.html). [CSV de observaciones](hallazgos.csv). Los números de nivel se cuentan de arriba abajo; los ID de polígonos están en el CSV y la galería.

## Resultado observado

- 60 imágenes y 308 polígonos, todos con estado: 256 `suficiente`, 41 `no_evaluable`, 11 `reponer`.
- 175 polígonos con `Occluded` y 133 sin él. Los 41 `no_evaluable` están marcados como ocluidos; eso es coherente con los obstáculos del lote, pero no acredita que el estado sea correcto.
- Ningún contorno cambió respecto del traspaso inicial. No se añadieron ni eliminaron niveles. Los tres trabajos siguen en progreso, sin incidencias registradas.
- Los 308 polígonos tienen área positiva, geometría válida y coordenadas dentro de la imagen. Esta comprobación no garantiza que sus límites sean correctos en la escena.
- Se registraron 38 observaciones en 24 imágenes: 25 propuestas de cambio de estado, una marca de oclusión omitida, siete comprobaciones de estado y cinco de geometría. Las observaciones pueden afectar al mismo nivel.

Alcance: vista general de las 60 imágenes, ampliaciones de los 52 niveles marcados `reponer` o `no_evaluable` y de ejemplos de oclusión. Los juicios de ocupación son visuales, no mediciones exhaustivas por píxel. Los casos cercanos al 30 % requieren medición o acuerdo de revisores. La propuesta no equivale a una aprobación independiente de todas las imágenes sintéticas.

Ejemplos prioritarios:

| Foto | Nivel | Observación |
|---|---:|---|
| 002, persona | 3 | Está `no_evaluable`, pero las bolsas visibles de la derecha superan el 30 %: propuesta `suficiente`. |
| 024, persona | 4 | El cuerpo tapa la parte izquierda y `Occluded` está desactivado. Activarlo conservando el estado interpretable. |
| 024, persona | 5 | Está `reponer`, pero el cuerpo oculta una zona capaz de cambiar la decisión: revisar como `no_evaluable`. |
| 040, persona | 1–2 | Están `reponer`; sumar los grupos visibles de ambos extremos antes de concluir falta de stock. |
| 044, cajas | 5 | Está `no_evaluable`, pero los sacos visibles a la derecha ya permiten concluir `suficiente`. |
| 046–047 | 4 | Está `reponer`; también cuenta el producto visible al fondo del propio nivel. |

Para los contornos dudosos se señalaron, entre otros, el último nivel de las fotos 001 con cajas, 028, 050 y 053. No se propone borrarlos en bloque: comprobar las referencias y la correspondencia con el original antes de decidir.

## Qué hacen otros proyectos

No existe una norma única que obligue a borrar todos los objetos parcialmente tapados. La política depende de qué debe predecir el modelo. Las siguientes referencias se refieren a objetos o personas; su adaptación a niveles de góndola es una recomendación para este proyecto, no una norma publicada de retail.

| Proyecto | Política documentada |
|---|---|
| [DanceTrack, CVPR 2022, sección 3.1](https://openaccess.thecvf.com/content/CVPR2022/papers/Sun_DanceTrack_Multi-Object_Tracking_in_Uniform_Appearance_and_Diverse_Motion_CVPR_2022_paper.pdf) | Conserva una caja de cuerpo completo cuando la persona está parcialmente oculta. Cuando queda totalmente oculta, no la anota en ese frame. |
| [COCOA — Semantic Amodal Segmentation](https://arxiv.org/abs/1509.01329) | Anota la extensión completa de las regiones, incluidas sus partes ocultas: es una tarea de segmentación amodal. |
| [TAO-Amodal](https://tao-amodal.github.io/) | Incluye cajas amodales de objetos parcialmente e incluso totalmente ocultos, en videos. La información temporal y el objetivo específico del benchmark son relevantes. |
| [CrowdHuman](https://www.crowdhuman.org/) | Guarda por persona tanto una caja de la región visible como otra del cuerpo completo, además de la cabeza. Mantiene separados ambos conceptos. |

[MP3D-Amodal, Oxford/CVPR 2024](https://www.robots.ox.ac.uk/~vgg/research/amodal/) distingue además entre contornos ocultos imaginados por anotadores y geometría respaldada por información 3D. En nuestro caso, el original ayuda a respaldar la geometría si la edición conserva la estructura, pero no debe usarse para decidir el stock que permite observar la edición.

## Recomendación para este lote

1. Conservar el polígono del nivel completo cuando la parte visible y las referencias de la góndola permitan ubicar sus límites con claridad. Activar `Occluded` si un obstáculo tapa parte de su zona. Evitar recortarlo con la silueta del carro o de la persona: cambiaría el espacio y el ancho que se evalúan.
2. Asignar el estado únicamente con la evidencia visible de la imagen editada. Si el producto visible ya alcanza el 30 %, es `suficiente`. Si ni llenando lo oculto alcanzaría ese valor, es `reponer`. Si lo oculto puede cambiar la decisión, es `no_evaluable`.
3. Si solo se puede ubicar el nivel consultando el original, dejar el contorno como pendiente de adjudicación. Con el criterio actual, no aceptar un nivel cuyos límites no puedan sostenerse en la edición; corregir el caso o apartarlo. Anotar niveles totalmente invisibles requeriría acordar expresamente otro objetivo amodal y su evaluación.
4. No retirar contornos de manera automática por tener `Occluded`. Tampoco tratar ese indicador como una orden de ignorar la muestra durante el entrenamiento: el tratamiento de exportación y pérdida debe definirse expresamente. El entrenador local lee polígonos YOLO y tres clases, no una columna de oclusión.

Esta revisión conserva las anotaciones como evidencia de la primera pasada. Las propuestas están pendientes de adjudicación y los recuentos observados no son los recuentos definitivos de un lote cerrado.
