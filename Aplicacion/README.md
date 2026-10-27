# Walmart Vision · Aplicación V3

Esta es la copia local de la aplicación vigente, antes ubicada en una extracción de `.tmp/`. Incluye el único modelo propio V3, niveles, bordes y ocupación experimental.

- **Usar en Windows:** abrir [iniciar.cmd](iniciar.cmd). El primer inicio prepara las dependencias.
- **Usar con Docker:** ejecutar `docker compose up --build -d --wait` desde esta carpeta y abrir http://127.0.0.1:8095.
- **Usar el entorno de desarrollo existente:** ejecutar `..\.venv-modelo\Scripts\python.exe app.py --open` desde esta carpeta.
- [Manual de usuario](../Documentacion/Usar_Walmart_Vision.md) · [Guía V3](LEEME_V3.md) · [Modelo y límites](../Documentacion/Modelo_V3_actual.md).
- [ZIP V3 publicado y SHA-256](../Entregables/README.md).

La confianza inicial es 0,60 y puede ajustarse desde 0,40. La visibilidad se indica manualmente por cada foto. La ocupación usa 70/30 y umbral 30 %, con abstención por señal ambigua; sigue siendo experimental. La sesión del lote, incluidas las fotos, se guarda en el navegador y se puede eliminar desde la aplicación; no se incorpora al entrenamiento.

La exclusión de barandas fragmentadas sigue pendiente de revisión visual. La interfaz y las reglas actuales también están incluidas en la descarga publicada del 27 de octubre.

Los archivos del programa y el modelo se conservaron durante el traslado. Los documentos de verificación con fecha anterior describen su propia entrega.

## Desarrollar desde un clon

El repositorio incluye el manifiesto, el peso V3 y el preparador de Windows. Clona el proyecto y abre `Aplicacion/iniciar.cmd` en Windows, o ejecuta `docker compose up --build -d --wait` desde `Aplicacion` para usar Docker. La primera preparación requiere Internet. El código de main puede ser más reciente que el ZIP de la release.

La corrección de barandas sigue pendiente de revisión visual y el mapa de señal se muestra en fucsia. Tras modificar los m?dulos incluidos en `edge_sources`, actualiza sus SHA-256 en `modelos.json` para que la aplicaci?n pueda verificar su integridad.
