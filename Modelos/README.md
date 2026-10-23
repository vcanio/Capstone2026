# Modelos generales para empezar a entrenar

Esta carpeta organiza los modelos generales que sirven de punto de partida para el laboratorio. `preentrenados/` recibe los pesos descargados para iniciar los entrenamientos:

- `yolo11n-seg.pt`: base de YOLO11 con segmentación.
- `yolo26n-seg.pt`: base de YOLO26 con segmentación.
- `fuente.json` y `fuente_yolo26.json`: registros de procedencia de esas descargas.

Los **modelos ya entrenados con nuestras anotaciones** están en `Experimentos/<ensayo>/entrenamiento/weights/best.pt`. [Índice de ensayos](../Experimentos/README.md).

GitHub conserva este índice y los registros de procedencia; los pesos `.pt` se instalan desde los activos del equipo según la [guía del laboratorio](../Documentacion/Desarrollo/Replicar_proyecto.md).

Para probar fotos en otro computador, la [entrega local actual de Walmart Visión](../Entregables/README.md) incluye los dos modelos V2 base: YOLO11 y YOLO26. Los dos ensayos V1 se conservan en el laboratorio y en sus distribuciones anteriores. V3 está en preparación y aún no tiene pesos entrenados.

El código para entrenar está en [Herramientas/Modelos](../Herramientas/Modelos/README.md). Los resultados de cada entrenamiento están en [Experimentos](../Experimentos/README.md).
