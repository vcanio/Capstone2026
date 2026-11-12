# Revisar modelos V3 · estado del 11/11/2026

La revisión de fotografías se realiza en la [app del equipo](../../Aplicacion/Documentacion/REVISION_EQUIPO.md), puerto 8095. El laboratorio se centra en preparar datos, entrenar y revisar resultados; su antigua sección «Probar una foto» y la galería de reserva final ya no forman parte del flujo operativo.

## Fotografías y contornos

1. Abrir la app del equipo y comprobar el modelo del análisis. El predeterminado es el cierre revisado adoptado el 10/11. En el entorno local puede haber candidatos adicionales; seleccionarlos para revisión no los adopta.
2. Cargar fotos propias autorizadas, sin usar el test reservado para ajustes. Confianza inicial 0,60, ajustable desde 0,25 en esta app. Mantener iguales los parámetros al comparar pesos.
3. Comprobar omisiones, detecciones extra, apoyo, perspectiva y límite superior en Original, Niveles, Bordes y Comparar. La confianza de detección no es ocupación.
4. Marcar los fallos por foto, nivel o zona y descargar un lote de revisión. Las marcas y fotos no se incorporan automáticamente al entrenamiento ni modifican CVAT.

Una foto sin anotaciones humanas completas permite revisión visual, no mAP o recall. Comparar métricas exige las mismas imágenes, referencias y parámetros. En las 11 val actuales, el oficial anterior y el adoptado obtuvieron 54 TP, 0 FP y 1 FN; no se demuestra superioridad global con ese panel pequeño.

El cliente ofrece [alertas visuales y revisión humana](../../Aplicacion_Cliente/README.md), separadas del diagnóstico original. Ocupación conserva Línea A preliminar, índice 0–100 y umbral 52; no mide porcentaje físico de stock ni detecta automáticamente personas u obstáculos.

[Modelo vigente y límites](../Modelo_V3_actual.md) · [Resultados y decisiones del laboratorio](../../Laboratorio/Modelos/README.md) · [Pruebas geométricas anteriores conservadas](../../Historico/Documentacion/Desarrollo/Probar_modelos_V3_antes_alineacion_20261111.md).
