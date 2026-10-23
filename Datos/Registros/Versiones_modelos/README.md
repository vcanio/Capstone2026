# Versiones de datos para modelos

Cada carpeta `datos_FECHA_HORA_ID/` identifica una copia concreta de anotaciones y particiones preparada para un ensayo. Sus fuentes y verificaciones permiten reconstruir los datos usados. Esta carpeta todavía no contiene una versión entrenable de V3.

| Versión | Criterio | Estado |
|---|---|---|
| [15/10 · `4ba1d339`](datos_20261015_012453_4ba1d339/version.json) | V1 | 91 imágenes activas revisadas, usadas por los primeros ensayos YOLO11-1 y YOLO26-1. |
| [19/10 15:19 · `0340eb69`](datos_20261019_151927_0340eb69/version.json) | V2 | Lectura previa de 236 imágenes, pendiente de revisión; sin exportación ni ensayo asociado en los manifests actuales. Se conserva como antecedente de anotaciones. |
| [19/10 23:46 · `3df2e643`](datos_20261019_234626_3df2e643/version.json) | V2 | Revisión posterior de 236 imágenes, usada por los ensayos base V2 de YOLO11n y YOLO26n. |

Dentro de una versión:

- `version.json`: identidad, fuentes, criterio, revisión y hashes.
- `snapshot_cvat.json`: anotaciones capturadas de CVAT en ese momento.
- `particion.json`: reparto concreto de esa versión.
- `revision_etiquetas.json`: registro de revisión de etiquetas, aunque esté vacío.
- `exportaciones/dataset_niveles/`: imágenes, etiquetas, `data.yaml` e integridad del conjunto preparado. Los ensayos comparten esta exportación mediante `dataset_ref`.

Estas exportaciones explican la mayor parte del espacio de `Registros`. Se conservaron porque las referencian ensayos existentes. Las cachés `train.cache` y `val.cache` son regenerables y se retiraron durante la limpieza del 23/10; no forman parte de la integridad del conjunto.

Modificar anotaciones requiere crear otra versión. No sustituir las exportaciones de un ensayo anterior por datos V3. El V3 actual se consulta en [su partición](../Particiones/v3_458_20261023/README.md) hasta que exista exportador y revisión compatibles.

[Volver al índice de Registros](../README.md).
