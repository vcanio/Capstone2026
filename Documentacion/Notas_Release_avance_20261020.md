# Walmart Lite V2 + detección de bordes

Descargar **Walmart_Lite_V2_Deteccion_Bordes_20261020.zip**, extraer todo y ejecutar
**Walmart_Lite/iniciar.cmd** en Windows x64. El visor se abre en
http://127.0.0.1:8095. El primer inicio necesita Internet para preparar Python y
sus dependencias; no hace falta instalarlos previamente ni usar Docker o CVAT.

Esta Release sirve únicamente para probar los modelos con fotografías propias.
El ZIP incluye los cuatro pesos entrenados: **YOLO11-1, YOLO26-1, V2-YOLO11 y
V2-YOLO26**. No hay que descargar modelos por separado.

## Cómo probar

1. Seleccionar o arrastrar una foto JPG, PNG o WebP de hasta 15 MB.
2. Elegir uno de los cuatro modelos y **YOLO + detección de bordes** o **Solo YOLO**.
3. Pulsar **Analizar foto** para ver los niveles numerados, estados y alertas.
4. Con bordes, revisar la señal por nivel, **Ver mapa de señal** y
   **Ver solo los bordes**. Se muestran los bordes originales y los filtrados.
5. Mantener la consola abierta durante el uso; Ctrl+C detiene el visor.

Las fotos y los mapas se procesan localmente en memoria. No se guardan ni se
incorporan al entrenamiento. Los siguientes inicios reutilizan el entorno.

## Interpretación

- V1 reconoce vacío, baja disponibilidad, suficiente y no evaluable.
- V2 base reconoce reponer y suficiente; todavía no reconoce no evaluable.
- Bordes, color y textura son una señal experimental, no un porcentaje validado
  de producto. Se conserva el estado de YOLO; sin máscara o sin evaluación
  posible se informa sin medición.
- La confianza es el puntaje del detector, no el porcentaje de ocupación.
- Una foto sin anotaciones permite observar resultados, no medir precisión.

Prototipo académico en evaluación. La velocidad depende del computador; la
validación real de faltantes sigue siendo limitada. La Release no contiene
informes, datasets ni paquetes de entrenamiento.

En **Assets**, elegir el ZIP de Walmart Lite indicado arriba. Los archivos
**Source code** automáticos de GitHub contienen el código, no el paquete portátil
con los cuatro modelos.

SHA-256 del ZIP: `4c512a3760488488ed19885e39d3bf9e06ac99e6ff64eb15e687f70ceba59155`.
