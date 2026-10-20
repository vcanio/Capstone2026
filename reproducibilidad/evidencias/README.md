# Evidencias compactas de la preparación

Estas salidas corresponden a comprobaciones locales del 20 de octubre de 2026.
El alcance completo y los pendientes están en [VERIFICACION](../VERIFICACION.md).

- [Panel Docker en CPU](panel_docker_cpu.json): contenedor aislado construido
  desde el checkout preparado, catálogo de cuatro ensayos y predicción de
  lider_express_040_0_original.jpg con V2 YOLO26, confianza 0,25, NMS 0,70 y
  tamaño 640. Referencia: cinco niveles, cuatro suficientes y uno reponer.
  También se comprobó health, ausencia del archivo privado de CVAT y respuesta
  HTTP 400 al solicitar importación con CVAT deshabilitado.
- [Demo Lite en CPU](demo_lite_cpu.json): solicitudes HTTP con la misma fotografía
  al servidor autónomo extraído del ZIP, sin montar datos ni CVAT. Cada modelo
  respondió y devolvió imagen; los conteos V1 no equivalen a aciertos en V2.
  Los segundos son mediciones de peticiones con el entorno ya preparado, no
  incluyen instalación o arranque y no son una promesa de latencia.

Los JSON son registros de estas comprobaciones; no sustituyen ejecutarlas de
nuevo en el computador del receptor ni la evaluación del conjunto completo.
