# Entregables · Walmart Visión

## Prueba de cliente y equipo · 11 de noviembre de 2026

[Descargar ambas apps con el modelo](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-apps-prueba-2026-11-11/Walmart_Vision_Cliente_y_Equipo_20261111.zip) · [SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-apps-prueba-2026-11-11/Walmart_Vision_Cliente_y_Equipo_20261111.sha256) · [Notas e instrucciones](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-11).

Incluye el cierre V3 con contornos revisados adoptado el 10/11, SHA-256 `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`, y el cliente del 11/11: diseño de tres columnas, miniaturas ligeras, guardado por foto, alertas visuales, revisión humana independiente, navegación con teclado y CSV. «Limpiar pasillo» elimina definitivamente el recorrido guardado. El equipo conserva su mesa de revisión y lotes ZIP.

Extrae todo. Windows x64: `Walmart_Vision/iniciar_cliente.cmd` (8098) o `Walmart_Vision/iniciar_equipo.cmd` (8095). Primera preparación con Internet. Docker: `docker compose -f compose.apps.yaml up --build -d --wait` desde `Walmart_Vision`.

Ambas apps comparten un solo modelo y Línea A del 8/11, índice visual preliminar 0–100, umbral 52. No mide stock físico ni detecta personas u obstáculos. La revisión humana no modifica el diagnóstico. Cada persona ejecuta su copia local; no hay sincronización. Dataset y fotografías privadas fuera de la distribución. [Cliente](../Aplicacion_Cliente/README.md) · [Equipo](../Aplicacion/Documentacion/REVISION_EQUIPO.md) · [Modelo y métricas](../Documentacion/Modelo_V3_actual.md).

Código original bajo [AGPL-3.0-only](../LICENSE), con [avisos](../NOTICE.md), [procedencia](../LICENCIAS.md) y fuente correspondiente en el tag de la entrega. La versión sigue siendo de prueba; las verificaciones funcionales no certifican precisión final.

## Distribuciones anteriores

| Fecha | Entrega | Alcance histórico |
|---|---|---|
| 10/11 | [Cliente y equipo r2 con licencias](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10-r2) | Modelo del 5/11, Línea A del 8/11 y cliente anterior. |
| 10/11 | [Primera prueba conjunta](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10) | Antecedente de r2. |
| 5/11 | [Walmart Visión V3](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-11-05) | Modelo del 5/11 y estimador anterior, umbral 30. |

Las releases anteriores conservan sus bytes, nombres y fechas. No se sustituyen sus activos por archivos nuevos. El material académico fechado conserva su alcance histórico. [Historial](https://github.com/vcanio/Capstone2026/blob/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Documentacion/Desarrollo/Historial_modelos_y_cambios.md).
