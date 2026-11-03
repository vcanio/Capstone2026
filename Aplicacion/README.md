# Walmart Vision · Aplicación V3

El selector ofrece **V3 estable · modelo actual** y **Candidato nuevo · 2 noviembre** para evaluar la segmentación. El estable sigue seleccionado al iniciar; el candidato no lo reemplaza. La ocupación es experimental.

- **Usar en Windows:** abrir [iniciar.cmd](iniciar.cmd). El primer inicio prepara las dependencias.
- **Usar con Docker:** ejecutar `docker compose up --build -d --wait` desde esta carpeta y abrir http://127.0.0.1:8095.
- **Usar el entorno de desarrollo existente:** ejecutar `..\.venv-modelo\Scripts\python.exe app.py --open` desde esta carpeta.
- [Manual de usuario](../Documentacion/Usar_Walmart_Vision.md) · [Guía V3](Documentacion/LEEME_V3.md) · [Modelo y límites](../Documentacion/Modelo_V3_actual.md).
- [ZIP V3 publicado y SHA-256](../Entregables/README.md).
- [Cómo leer el código de niveles y ocupación](Documentacion/LEER_CODIGO.md).
- [Documentación técnica y registros](Documentacion/) · [Pruebas de la aplicación](Pruebas/).

La confianza inicial es 0,60 y puede ajustarse desde 0,40. Todas las fotos se analizan sin indicar su visibilidad; la app no detecta automáticamente personas ni obstáculos. V3 interpreta la cobertura experimental del frente con umbral 30 %, suponiendo lleno detrás del producto visible. El espacio libre sobre productos bajos no reduce su aporte. La medición exige señal y respaldo de bordes o textura en al menos dos filas contiguas de la grilla, desde el 35 % de la altura del nivel. Conserva revisión por señal ambigua y recortes; no identifica semánticamente productos y requiere calibración. Las medidas anteriores de superficie, ancho y combinación 70/30 se conservan como diagnóstico y para modelos anteriores. La sesión del lote, incluidas las fotos, se guarda en el navegador y se puede eliminar desde la aplicación; no se incorpora al entrenamiento. Los resultados guardados deben reanalizarse tras actualizar.

La exclusión de barandas fragmentadas sigue pendiente de revisión visual. El ZIP publicado el 28 de octubre no incluye el candidato.

Los archivos del programa y el modelo se conservaron durante el traslado. Los documentos de verificación con fecha anterior describen su propia entrega.

## Desarrollar desde un clon

El repositorio incluye el manifiesto, ambos pesos y el preparador de Windows. Clona el proyecto y abre `Aplicacion/iniciar.cmd` en Windows, o ejecuta `docker compose up --build -d --wait` desde `Aplicacion` para usar Docker. La primera preparación requiere Internet. El código de main puede ser más reciente que el ZIP de la release.

La corrección de barandas sigue pendiente de revisión visual y el mapa de señal se muestra en fucsia. Tras modificar los m?dulos incluidos en `edge_sources`, actualiza sus SHA-256 en `modelos.json` para que la aplicaci?n pueda verificar su integridad.

Para ejecutar las pruebas desde `Aplicacion` en Windows: `..\.venv-modelo\Scripts\python.exe -m unittest discover -s Pruebas`.
