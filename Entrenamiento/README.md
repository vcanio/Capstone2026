# Entrenamiento y evaluación reproducible · Walmart Visión V3

Esta carpeta reúne los scripts reproducibles para preparar anotaciones CVAT, configurar el ajuste fino de `YOLO26n-seg` (`V3-cierre-revisado-20261110`) y verificar o reproducir la evaluación independiente sobre **Ohiggins 3** (`68` fotos / `354` niveles).

## Archivos incluidos

| Archivo | Propósito |
|---|---|
| [`preparar_datos_cvat.py`](preparar_datos_cvat.py) | Conversión de polígonos CVAT a YOLO-seg, regla de la mediana sobre portaprecio, partición anti-fuga por escenas y normalización EXIF sin alterar coordenadas. |
| [`entrenar_yolo26n_seg.py`](entrenar_yolo26n_seg.py) | Configuración exacta del ensayo oficial (`seed=42`, `AdamW`, `lr0=0.0001`, `epochs=40`, `patience=10`, `batch=2`, `imgsz=640`) y comprobación de huella del peso oficial. |
| [`data.template.yaml`](data.template.yaml) | Plantilla YOLO-seg de clase única `0: Nivel`. |
| [`evaluar_ohiggins3.py`](evaluar_ohiggins3.py) | Verificación matemática del recibo congelado y script de evaluación de segmentación (`IoU ≥ 0,50`) y ocupación `Línea A`. |

## Verificación rápida sin datasets privados

```bash
python Entrenamiento/preparar_datos_cvat.py --self-check
python Entrenamiento/entrenar_yolo26n_seg.py --dry-run
python Entrenamiento/evaluar_ohiggins3.py --verify-receipt
```

## Reproducción con datos locales preparados

1. Prepara el dataset YOLO-seg desde un snapshot CVAT y su partición anti-fuga:
   ```bash
   python Entrenamiento/preparar_datos_cvat.py --cvat-json snapshot_cvat.json --images-dir ./imagenes --partition-json particion.json --output-dir ./dataset_niveles
   ```
2. Ajusta `path:` en [`data.template.yaml`](data.template.yaml) y lanza el ajuste fino (requiere `--execute` explícito):
   ```bash
   python Entrenamiento/entrenar_yolo26n_seg.py --data Entrenamiento/data.template.yaml --execute
   ```
3. Evalúa el modelo congelado sobre la carpeta de test independiente:
   ```bash
   python Entrenamiento/evaluar_ohiggins3.py --images-dir ./dataset_niveles/images/test --labels-dir ./dataset_niveles/labels/test
   ```

Ver detalles y límites metodológicos en [Entrenamiento y datos](../Documentacion/Entrenamiento_y_datos.md) y [Evaluación cuantitativa de test · Ohiggins 3](../Documentacion/Evidencias/evaluacion_test_ohiggins3_20261114.md).
