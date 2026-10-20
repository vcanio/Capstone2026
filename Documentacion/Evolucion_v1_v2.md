# Evolución del prototipo: V1, V2 base y visibilidad limitada

Documento de referencia para mostrar y explicar el proyecto · 20 de octubre de 2026.

La interfaz comienza con el selector **Versión del proyecto**: **V1 (4 estados)** o **V2 (Disponibilidad visual)**. La selección filtra las copias de datos, entrenamientos, modelos, fotos de desarrollo y resultados. Los modelos generales (`yolo11n-seg` y `yolo26n-seg`) quedan como punto de partida en **Entrenar**; **Probar una foto** ofrece los modelos entrenados de la versión elegida.

| Versión | Carpeta de datos | Estados que aprende | Datos y modelos disponibles |
|---|---|---|---|
| **V1 · 4 estados** | [`Datos/V1/`](../Datos/V1/README.md) | `vacío`, `baja_disponibilidad`, `suficiente`, `no_evaluable` | 91 imágenes activas (`86 train` y `5 val` reales) + 7 reservadas. Modelos: `YOLO11-1` y `YOLO26-1`. |
| **V2 base · 2 estados** | [`Datos/V2/lider_express_20261016/`](../Datos/V2/lider_express_20261016/README.md) | `reponer`, `suficiente` | 236 imágenes (59 reales + 177 variantes IA). Exportación activa: `160 train` y `10 val` reales (`30 val` sintéticas y `36 test` aparte). Modelos: `v2_base_yolo11n_01` y `v2_base_yolo26n_01`. |
| **V2 · 3 estados** | [`Datos/V2/visibilidad_limitada_20261019/`](../Datos/V2/visibilidad_limitada_20261019/README.md) | `reponer`, `suficiente`, `no_evaluable` | 60 imágenes sintéticas con obstáculos (tarea 22, `41 train` / `10 val` / `9 test`) + script [`entrenar_niveles.py`](../Herramientas/Modelos/entrenar_niveles.py). |

`reponer` agrupa el vacío y la presencia de producto en menos del 30 % del ancho del nivel; `suficiente` corresponde al 30 % o más. El polígono delimita el nivel completo.

## Qué se conserva de cada etapa

V2 también permite elegir **YOLO + detección de bordes · experimental** al probar una
foto. Usa los pesos ya entrenados, conserva el estado de YOLO y añade una señal
de bordes/color dentro de cada nivel. La primera comparación y sus límites están
documentados en el [experimento combinado](Experimento_YOLO_Paulo_v2.md).

- **Ensayos V1:** [YOLO11-1](../Experimentos/YOLO11-1_20261015_013749_f709/REVISION_MODELO.md) y [YOLO26-1](../Experimentos/YOLO26-1_20261015_021212_c452/REVISION_MODELO.md) junto con su [copia revisada v1](../Datos/Registros/Versiones_modelos/datos_20261015_012453_4ba1d339/version.json), la [guía histórica v1](Guia_anotacion_CVAT.md), la [revisión de la primera pasada](Revision_primera_pasada_20261016.md) y la demo [Walmart Lite](../Herramientas/Demo_lite/LEEME.md).
- **Ensayos V2 base:** `v2_base_yolo11n_01_20261020_002800_ec8d` y `v2_base_yolo26n_01_20261020_004933_b105` en [`Experimentos/`](../Experimentos/README.md), vinculados a la versión aprobada [`datos_20261019_234626_3df2e643`](../Datos/Registros/Versiones_modelos/datos_20261019_234626_3df2e643/version.json) y a la [partición por familias y escenas](../Datos/Registros/Particiones/lider_express_v2_20261019/README.md).

## Dónde está cada parte del código

| Función | Código | Relación con las versiones |
|---|---|---|
| Resolver rutas de imágenes V1/V2 | [rutas_datos.py](../Herramientas/Modelos/rutas_datos.py) | Resuelve `Datos/V1` y `Datos/V2` manteniendo compatibilidad con los manifiestos históricos. |
| Importar anotaciones y preparar datos | [datos_modelos.py](../Herramientas/Modelos/datos_modelos.py) | Conserva las copias V1 y aplica la partición fijada al lote V2 base. |
| Validar y exportar estados | [niveles_modelos.py](../Herramientas/Modelos/niveles_modelos.py) | Soporta las 4 clases originales (V1), las 2 clases de V2 base y las 3 clases de V2 completo. |
| Entrenar desde el panel | [piloto_modulos.py](../Herramientas/Modelos/piloto_modulos.py) | Usa el YAML y las clases de la copia seleccionada; guarda un ensayo nuevo en `Experimentos/`. |
| Entrenar V2 completo por consola | [entrenar_niveles.py](../Herramientas/Modelos/entrenar_niveles.py) | Entrada específica para datasets con los tres estados completos; [guía](Entrenamiento_niveles_v2.md). |
| Evaluar los ensayos del panel | [comparar_niveles.py](../Herramientas/Modelos/comparar_niveles.py) | Interpreta las clases del manifiesto (`vacío`/`baja` son alertas en V1; `reponer` es alerta en V2). |
| Probar fotos y dibujar resultados | [panel_worker.py](../Herramientas/Modelos/panel_worker.py) | Lee las clases del modelo y aplica sus nombres, colores y alertas. |
| Estimar ocupación por bordes | [gondola_bordes.py](../Experimentos/Bordes/gondola_bordes.py) | Prototipo de detección de bordes; no integrado automáticamente al entrenamiento V2. |

## Cómo mostrar la evolución en el panel

1. Elegir **V1 · Versión original**:
   - En **Probar una foto**, seleccionar `YOLO11-1` o `YOLO26-1` (`v1 · 4 estados`) y analizar una foto de `Datos/V1/` o una foto propia.
   - En **Comparar resultados**, revisar métricas y comparaciones de los ensayos V1.
2. Elegir **V2 · Disponibilidad visual**:
   - En **Probar una foto**, seleccionar `v2_base_yolo11n_01` o `v2_base_yolo26n_01` (`v2 base · 2 estados`) y analizar una de las 170 fotos de desarrollo de `Datos/V2/lider_express_20261016/` (`160 train` + `10 val` reales) o una foto propia.
   - En **Comparar resultados**, contrastar el desempeño entre `v2_base_yolo11n_01` y `v2_base_yolo26n_01` sobre la misma partición de validación real.
