# Modelos entrenados y resultados

| Etapa | Ensayo | Modelo base y criterio | Evidencia |
|---|---|---|---|
| **V1** (4 estados) | `YOLO11-1_20261015_013749_f709` | `yolo11n-seg.pt` · `disponibilidad_visual_nivel_v1` (86 train / 5 val) | [Revisión del modelo](YOLO11-1_20261015_013749_f709/REVISION_MODELO.md) |
| **V1** (4 estados) | `YOLO26-1_20261015_021212_c452` | `yolo26n-seg.pt` · `disponibilidad_visual_nivel_v1` (86 train / 5 val) | [Revisión y comparación](YOLO26-1_20261015_021212_c452/REVISION_MODELO.md) |
| **V2 base** (2 estados) | `v2_base_yolo11n_01_20261020_002800_ec8d` | `yolo11n-seg.pt` · `disponibilidad_visual_nivel_v2_base_2clases` (160 train / 10 val) | `manifest.json`, `metricas_validacion.json`, `metricas_alertas.json` |
| **V2 base** (2 estados) | `v2_base_yolo26n_01_20261020_004933_b105` | `yolo26n-seg.pt` · `disponibilidad_visual_nivel_v2_base_2clases` (160 train / 10 val) | `manifest.json`, `metricas_validacion.json`, `metricas_alertas.json` |

## Otras carpetas en `Experimentos/`

- `Bordes/`: prototipo experimental independiente de estimación de ocupación por bordes ([`gondola_bordes.py`](Bordes/gondola_bordes.py)).
- `panel_pruebas/`: historial operativo de trabajos e inferencias manuales del panel, incluyendo `Subidas_panel/` para las fotografías subidas desde **Probar una foto**.
- Diagnóstico histórico REAL_03 (archivo local histórico, fuera de la distribución): evidencia archivada sobre omisiones, duplicados y pertenencia espacial en la primera pasada.

## Trazabilidad de exportaciones y ensayos

- Cada versión aprobada en `Datos/Registros/Versiones_modelos/<id>/exportaciones/dataset_niveles/` genera una exportación verificada por SHA-256 (`integridad.json`) que los ensayos de esa misma versión comparten mediante `dataset_ref` en `manifest.json`.
- Cada carpeta de ensayo conserva su `snapshot_cvat.json`, `particion.json`, `version_datos.json`, `config_interfaz.json`, pesos (`entrenamiento/weights/best.pt` y `last.pt`), métricas de validación y comparaciones por imagen.
