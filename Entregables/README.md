## Prueba de cliente y equipo · 10 de noviembre

[**Descargar ambas apps con el modelo**](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-apps-prueba-2026-11-10/Walmart_Vision_Cliente_y_Equipo_20261110.zip) · [Notas y SHA-256](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-apps-prueba-2026-11-10).

Extrae todo. Windows x64: `Walmart_Vision/iniciar_cliente.cmd` (8098) o `Walmart_Vision/iniciar_equipo.cmd` (8095). El primer inicio prepara Python/dependencias y requiere Internet. Docker: `docker compose -f compose.apps.yaml up --build -d --wait` desde `Walmart_Vision`.

[App cliente](../Aplicacion_Cliente/README.md): prioridades, checklist y CSV. [App del equipo](../Aplicacion/Documentacion/REVISION_EQUIPO.md): comparación, marcado por nivel/zona y lotes de revisión. Cada colega ejecuta su copia local; no hay sincronización ni alojamiento web. Carga fotos propias: el dataset no se incluye.

Ambas usan el modelo oficial del 5/11 y Línea A del 8/11, índice visual preliminar 0–100, umbral 52. No mide porcentaje físico de stock ni detecta personas u obstáculos. Requiere revisión visual. No es una evaluación final. La release del 5/11 descrita abajo conserva su estimador anterior y sus archivos.


# Entregables · Walmart Visión V3

**Entrega oficial del 5 de noviembre de 2026:** [Descargar ZIP con modelo](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-11-05/Walmart_Vision_V3_20261105.zip) · [SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-11-05/Walmart_Vision_V3_20261105.sha256) · [Release e instrucciones](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-11-05).

Incluye el best.pt del refuerzo de geometría del 5 de noviembre y la aplicación actual. No necesitas CVAT ni el dataset para usarla. La primera preparación requiere Internet.

- Windows x64: extraer todo el ZIP y abrir `Walmart_Vision/iniciar.cmd`.
- Docker, macOS y Linux: entrar en `Walmart_Vision`, ejecutar `docker compose up --build -d --wait` y abrir http://127.0.0.1:8095.
- Desde un clon: los mismos pasos dentro de `Aplicacion/`; el peso ya está incluido.

[Modelo y métricas](../Documentacion/Modelo_V3_actual.md) · [Aplicación](../Aplicacion/README.md). La ocupación sigue siendo experimental; revisa los contornos. Las releases anteriores se conservan como historial y contienen modelos anteriores.

Las entregas académicas fechadas y los cuadernos anteriores conservan su alcance histórico. [Historial](../Documentacion/Desarrollo/Historial_modelos_y_cambios.md).
