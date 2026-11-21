# Entregables · Walmart Visión

## Entrega final v2.3 · 21 de noviembre de 2026

[Descargar ambas apps con el modelo (Final v2.3)](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-final-v2-3-2026-11-21/Walmart_Vision_Cliente_y_Equipo_Final_20261121.zip) · [SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-final-v2-3-2026-11-21/Walmart_Vision_Cliente_y_Equipo_Final_20261121.sha256) · [Notas e instrucciones](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-final-v2-3-2026-11-21).

El paquete trae las dos apps, el peso oficial **V3-cierre-revisado-20261110** para los niveles, el peso auxiliar para detectar personas, el **estimador de disponibilidad visual `v2.3`** (`linea_a_20261119_v2_3_productos_bajos`) y [ocho ejemplos precargados](../Aplicacion_Cliente/ejemplos/README.md). El cliente incluye historial SQLite y exportación CSV, Excel y PDF. El equipo incluye marcado de incidencias y exportación de lotes ZIP.

Extrae la carpeta completa. En Windows x64, abre `iniciar_cliente.cmd` (8098) o `iniciar_equipo.cmd` (8095). La primera preparación requiere Internet. [Manual de uso](../Documentacion/Usar_Walmart_Vision.md) · [Docker para el equipo](../Aplicacion/DOCKER.md).

| Referencia | Valor |
|---|---|
| Código fuente del ZIP vigente | Ver `FUENTE.json` dentro del ZIP y rama `main` bajo tag [`walmart-vision-final-v2-3-2026-11-21`](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-final-v2-3-2026-11-21). |
| Tag de la entrega final | [`walmart-vision-final-v2-3-2026-11-21`](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-final-v2-3-2026-11-21) |
| SHA-256 del peso oficial | `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5` |

Los [scripts de entrenamiento y evaluación](../Entrenamiento/README.md) están en el repositorio. El ZIP se usa para ejecutar las apps con los pesos ya preparados. El dataset completo queda fuera de la distribución. La [ficha del modelo](../Documentacion/Modelo_V3_actual.md) separa evaluación CVAT en `Ohiggins 3`, evaluación ciega independiente en **171 fotos reales vírgenes** y stress-test sintético de **60 variantes**.

Código original bajo [AGPL-3.0-only](../LICENSE). Consulta [avisos y procedencia](../LICENCIAS.md) y el commit indicado para acceder al código correspondiente al ZIP.

## Distribuciones anteriores

| Fecha | Entrega | Alcance histórico |
|---|---|---|
| 16/11 | [Entrega MVP (`2026-11-16`)](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-mvp-2026-11-16) | Modelo del 10/11, Línea A v2.2, 8 casos precargados, historial SQLite, exportación CSV/XLSX/PDF y oclusiones COCO (`SHA-256: 9b7ddba39ea3fc94b9ef90381e5c13cdcf4ba1b7d4b3ac9c22dc1ae4ed973277`). |
| 16/11 | [Apps cliente y equipo (`2026-11-16`)](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-2026-11-16) | Modelo del 10/11, filtro previo `calidad_foto.py`, Línea A v2.2 (`F1 94,59 %` en `Ohiggins 3`), vista *Huecos* y severidad operativa. |
| 13/11 | [Apps cliente y equipo (`2026-11-13`)](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-2026-11-13) | Modelo del 10/11, Línea A base (`20261113`), diseño cliente de tres columnas y comparación basal en equipo. |
| 11/11 | [Prueba de cliente y equipo](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-11) | Modelo del 10/11, Línea A del 8/11 y primera versión cliente V3. |
| 10/11 | [Cliente y equipo r2 con licencias](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10-r2) | Modelo del 5/11, Línea A del 8/11 y cliente anterior. |
| 10/11 | [Primera prueba conjunta](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10) | Antecedente de r2. |
| 5/11 | [Walmart Visión V3](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-11-05) | Modelo del 5/11 y estimador anterior, umbral 30. |

Las releases anteriores conservan sus bytes, nombres y fechas. No se sustituyen sus activos por archivos nuevos. El material académico fechado conserva su alcance histórico. [Historial](https://github.com/vcanio/Capstone2026/blob/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Documentacion/Desarrollo/Historial_modelos_y_cambios.md).
