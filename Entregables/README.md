# Distribución de Walmart Visión

## V3 · descarga actual

La [release V3 publicada el 26 de octubre de 2026](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-10-26) reúne Windows x64 y macOS con Docker en un único paquete.

**Descarga [`Walmart_Vision_V3_20261028.zip`](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-10-26/Walmart_Vision_V3_20261028.zip): incluye la aplicación y el modelo. Los archivos Source code contienen solamente el código fuente.**

El [archivo SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-10-26/Walmart_Vision_V3_20261028.sha256) permite comprobar opcionalmente la integridad de la descarga; no es necesario para abrir la aplicación.

V3 usa una sola clase Nivel, confianza inicial 0,60 ajustable desde 0,40 y cobertura experimental del frente a partir de bordes, gradiente, color y textura. Asume lleno detrás del producto visible y usa un umbral experimental de 30 %. Requiere fotos frontales o casi frontales y revisión visual; no detecta automáticamente personas, carteles o vacío.

La primera preparación requiere conexión; la inferencia posterior es local. La sesión del lote, incluidas las fotos, se guarda en el navegador y puede eliminarse desde la aplicación. El procedimiento Docker fue probado correctamente por Vicente en macOS con la release anterior; V3 conserva ese flujo y sus dependencias.

[Manual](../Documentacion/Usar_Walmart_Vision.md) · [Criterios y cálculo](../Documentacion/Guia_para_entender_el_proyecto.md) · [Modelo y métricas](../Documentacion/Modelo_V3_actual.md)

## Entregas anteriores

Las [Releases de GitHub](https://github.com/vcanio/Capstone2026/releases) conservan las versiones anteriores como historial.

## Material académico

El [informe intermedio](../Documentacion/Informe_Intermedio_Avance_20261020.md) y su [PDF](Informe_Intermedio_Avance_20261020.pdf) conservan sus resultados fechados. Son antecedentes académicos; no certifican el comportamiento de la V3 actual.
