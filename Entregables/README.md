# Entregables · Walmart Visión

## Apps cliente y equipo · 13 de noviembre de 2026

[Descargar ambas apps con el modelo](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-apps-2026-11-13/Walmart_Vision_Cliente_y_Equipo_20261113.zip) · [SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-apps-2026-11-13/Walmart_Vision_Cliente_y_Equipo_20261113.sha256) · [Notas e instrucciones](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-2026-11-13).

Incluye el cierre V3 con contornos revisados adoptado el 10/11, SHA-256 `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`, el cliente actualizado (diseño de tres columnas, navegación móvil en tres pasos, selector de lente trasera, miniaturas ligeras, guardado por foto, alertas visuales, revisión humana independiente, navegación con teclado y CSV) y la app del equipo con comparación opcional entre Línea A (predeterminada) y franja basal experimental, modo «Ambos», etiquetado por nivel y lotes ZIP. «Limpiar pasillo» elimina definitivamente el recorrido guardado.

Extrae todo. Windows x64: `Walmart_Vision/iniciar_cliente.cmd` (8098) o `Walmart_Vision/iniciar_equipo.cmd` (8095). Primera preparación con Internet. Docker: `docker compose -f compose.apps.yaml up --build -d --wait` desde `Walmart_Vision`.

Ambas apps comparten un solo modelo y Línea A del 8/11 (predeterminada), índice visual preliminar 0–100, umbral 52. La franja basal opcional de la app del equipo (umbral de ensayo 30 %, sin calibrar) es experimental y no constituye una mejora de precisión demostrada ni mide stock físico. La revisión humana no modifica el diagnóstico. Cada persona ejecuta su copia local; no hay sincronización. Dataset y fotografías privadas fuera de la distribución. [Cliente](../Aplicacion_Cliente/README.md) · [Equipo](../Aplicacion/Documentacion/REVISION_EQUIPO.md) · [Comparación basal](../Aplicacion/Documentacion/COMPARACION_BASAL_20261112.md) · [Modelo y métricas](../Documentacion/Modelo_V3_actual.md).

Código original bajo [AGPL-3.0-only](../LICENSE), con [avisos](../NOTICE.md), [procedencia](../LICENCIAS.md) y fuente correspondiente en el tag de la entrega. Las verificaciones funcionales no certifican precisión final.

## Distribuciones anteriores

| Fecha | Entrega | Alcance histórico |
|---|---|---|
| 11/11 | [Prueba de cliente y equipo](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-11) | Modelo del 10/11, Línea A del 8/11 y primera versión cliente V3. |
| 10/11 | [Cliente y equipo r2 con licencias](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10-r2) | Modelo del 5/11, Línea A del 8/11 y cliente anterior. |
| 10/11 | [Primera prueba conjunta](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10) | Antecedente de r2. |
| 5/11 | [Walmart Visión V3](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-11-05) | Modelo del 5/11 y estimador anterior, umbral 30. |

Las releases anteriores conservan sus bytes, nombres y fechas. No se sustituyen sus activos por archivos nuevos. El material académico fechado conserva su alcance histórico. [Historial](https://github.com/vcanio/Capstone2026/blob/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Documentacion/Desarrollo/Historial_modelos_y_cambios.md).
