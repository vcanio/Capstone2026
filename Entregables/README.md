# Entregables · Walmart Visión

## Entrega final MVP · 16 de noviembre de 2026

[Descargar ambas apps con el modelo (MVP)](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-mvp-2026-11-16/Walmart_Vision_Cliente_y_Equipo_MVP_20261116.zip) · [SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-mvp-2026-11-16/Walmart_Vision_Cliente_y_Equipo_MVP_20261116.sha256) · [Notas e instrucciones](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-mvp-2026-11-16).

Incluye el cierre V3 oficial (`V3-cierre-revisado-20261110`, SHA-256 `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`), el filtro previo [`calidad_foto.py`](../Aplicacion/calidad_foto.py), detección automática de personas con `yolo26n-seg.pt` ([`oclusiones.py`](../Aplicacion/oclusiones.py), foto `no_evaluable` con contorno ámbar sutil ante obstrucción), verificación de nivel superior abierto ([`geometria_niveles.py`](../Aplicacion/geometria_niveles.py)), **Línea A v2.2** (`linea_a_20261116_v2_2_cajas_sacos_picada`, `F1 94,59 %` en `Ohiggins 3`), historial compartido en servidor (`SQLite`) y exportación **CSV / Excel (`.xlsx`) / PDF** con resultados directos del modelo en cliente, scripts reproducibles en [`Entrenamiento/`](../Entrenamiento/README.md) y CI en GitHub Actions.

Extrae todo. Windows x64: `Walmart_Vision/iniciar_cliente.cmd` (8098) o `Walmart_Vision/iniciar_equipo.cmd` (8095). Primera preparación con Internet. Docker: `docker compose -f compose.apps.yaml up --build -d --wait` desde `Walmart_Vision`.

Ambas apps comparten un solo modelo y **Línea A v2.2** (predeterminada), índice visual preliminar 0–100 con umbral 52, severidad operativa (`Crítica`, `Alta`, `Normal`, `Verificar`) e índice bruto (`raw_pct`) cuando pasa a revisión. La franja basal opcional de la app del equipo (umbral de ensayo 30 %, sin calibrar) es experimental y no constituye una mejora de precisión demostrada ni mide stock físico. Dataset y fotografías privadas fuera de la distribución. [Cliente](../Aplicacion_Cliente/README.md) · [Equipo](../Aplicacion/Documentacion/REVISION_EQUIPO.md) · [Comparación basal](../Aplicacion/Documentacion/COMPARACION_BASAL_20261112.md) · [Modelo y métricas](../Documentacion/Modelo_V3_actual.md).

Código original bajo [AGPL-3.0-only](../LICENSE), con [avisos](../NOTICE.md), [procedencia](../LICENCIAS.md) y fuente correspondiente en el tag de la entrega. Las verificaciones funcionales no certifican precisión adicional fuera del conjunto `Ohiggins 3`.

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
