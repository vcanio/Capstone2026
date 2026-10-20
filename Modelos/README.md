# Modelos generales para empezar a entrenar

`preentrenados/` contiene los pesos generales descargados para iniciar los entrenamientos:

- `yolo11n-seg.pt`: base de YOLO11 con segmentación.
- `yolo26n-seg.pt`: base de YOLO26 con segmentación.
- `fuente.json` y `fuente_yolo26.json`: registros de procedencia de esas descargas.

Los **modelos ya entrenados con nuestras anotaciones** están en `Experimentos/<ensayo>/entrenamiento/weights/best.pt`. [Índice de ensayos](../Experimentos/README.md).

Para probarlos en otro computador, el [ZIP de Entregables](../Entregables/README.md) ya incluye ambos modelos entrenados. Esta carpeta contiene los puntos de partida del laboratorio.
