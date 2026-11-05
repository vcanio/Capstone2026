# Entregables · Walmart Visión V3

**Entrega oficial del 5 de noviembre de 2026:** [Descargar ZIP con modelo](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-11-05/Walmart_Vision_V3_20261105.zip) · [SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-11-05/Walmart_Vision_V3_20261105.sha256) · [Release e instrucciones](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-11-05).

Incluye el best.pt del refuerzo de geometría del 5 de noviembre y la aplicación actual. No necesitas CVAT ni el dataset para usarla. La primera preparación requiere Internet.

- Windows x64: extraer todo el ZIP y abrir `Walmart_Vision/iniciar.cmd`.
- Docker, macOS y Linux: entrar en `Walmart_Vision`, ejecutar `docker compose up --build -d --wait` y abrir http://127.0.0.1:8095.
- Desde un clon: los mismos pasos dentro de `Aplicacion/`; el peso ya está incluido.

[Modelo y métricas](../Documentacion/Modelo_V3_actual.md) · [Aplicación](../Aplicacion/README.md). La ocupación sigue siendo experimental; revisa los contornos. Las releases anteriores se conservan como historial y contienen modelos anteriores.

Las entregas académicas fechadas y los cuadernos anteriores conservan su alcance histórico. [Historial](../Documentacion/Desarrollo/Historial_modelos_y_cambios.md).
