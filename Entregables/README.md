# Entregables · Walmart Visión

## Entrega final MVP · 16 de noviembre de 2026

[Descargar ambas apps con el modelo (MVP)](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-mvp-2026-11-16/Walmart_Vision_Cliente_y_Equipo_MVP_20261116.zip) · [SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-mvp-2026-11-16/Walmart_Vision_Cliente_y_Equipo_MVP_20261116.sha256) · [Notas e instrucciones](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-mvp-2026-11-16).

El paquete trae las dos apps, el peso oficial **V3-cierre-revisado-20261110** para los niveles, el peso auxiliar para detectar personas, el **estimador de disponibilidad visual** y [ocho ejemplos precargados](../Aplicacion_Cliente/ejemplos/README.md). El cliente incluye historial SQLite y exportación CSV, Excel y PDF. El equipo incluye marcado de incidencias y exportación de lotes ZIP.

Extrae la carpeta completa. En Windows x64, abre `iniciar_cliente.cmd` (8098) o `iniciar_equipo.cmd` (8095). La primera preparación requiere Internet. [Manual de uso](../Documentacion/Usar_Walmart_Vision.md) · [Docker para el equipo](../Aplicacion/DOCKER.md).

| Referencia | Valor |
|---|---|
| Código fuente del ZIP vigente | [`bcdb881`](https://github.com/vcanio/Capstone2026/tree/bcdb881000f5a0f56f5a87822e081524df2f0dbb), registrado en `FUENTE.json` dentro del ZIP. |
| Tag del anuncio del MVP | [`walmart-vision-mvp-2026-11-16`](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-mvp-2026-11-16), creado para la revisión inicial [`6243467`](https://github.com/vcanio/Capstone2026/tree/6243467be034d25ad8d74942f33b291fe9c127d7). |
| SHA-256 del ZIP vigente | `9b7ddba39ea3fc94b9ef90381e5c13cdcf4ba1b7d4b3ac9c22dc1ae4ed973277` |
| SHA-256 del peso oficial | `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5` |

Los [scripts de entrenamiento y evaluación](../Entrenamiento/README.md) están en el repositorio. El ZIP se usa para ejecutar las apps con los pesos ya preparados. El dataset completo queda fuera de la distribución. La [ficha del modelo](../Documentacion/Modelo_V3_actual.md) separa evaluación de segmentación, evaluación ciega de Línea A base y reevaluación posterior de v2.2.

Código original bajo [AGPL-3.0-only](../LICENSE). Consulta [avisos y procedencia](../LICENCIAS.md) y el commit indicado para acceder al código correspondiente al ZIP.

## Distribuciones anteriores

| Fecha | Entrega | Alcance histórico |
|---|---|---|
| 16/11 | [Apps cliente y equipo (`2026-11-16`)](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-2026-11-16) | Modelo del 10/11, filtro previo `calidad_foto.py`, Línea A v2.2 (`F1 94,59 %` en `Ohiggins 3`), vista *Huecos* y severidad operativa. |
| 13/11 | [Apps cliente y equipo (`2026-11-13`)](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-2026-11-13) | Modelo del 10/11, Línea A base (`20261113`), diseño cliente de tres columnas y comparación basal en equipo. |
| 11/11 | [Prueba de cliente y equipo](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-11) | Modelo del 10/11, Línea A del 8/11 y primera versión cliente V3. |
| 10/11 | [Cliente y equipo r2 con licencias](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10-r2) | Modelo del 5/11, Línea A del 8/11 y cliente anterior. |
| 10/11 | [Primera prueba conjunta](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10) | Antecedente de r2. |
| 5/11 | [Walmart Visión V3](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-11-05) | Modelo del 5/11 y estimador anterior, umbral 30. |

Las releases anteriores conservan sus bytes, nombres y fechas. No se sustituyen sus activos por archivos nuevos. El material académico fechado conserva su alcance histórico. [Historial](https://github.com/vcanio/Capstone2026/blob/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Documentacion/Desarrollo/Historial_modelos_y_cambios.md).
