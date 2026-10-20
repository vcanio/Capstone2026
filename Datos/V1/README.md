# Primera tanda (V1) · Lote inicial Lider

| Carpeta | Contenido |
|---|---|
| `Lider/` | 30 fotografías reales de desarrollo (`lider_001.jpg` a `lider_037.jpg`, excluyendo las 7 reservadas). |
| `Sinteticas/` | 72 imágenes sintéticas generadas a partir de las escenas de desarrollo (`EQ_*`). |
| `Reservadas/` | 7 fotografías reales reservadas para evaluación independiente (`lider_014.jpg`, `017`, `018`, `019`, `020`, `021` y `035`). |

**Cada imagen tiene una única copia en esta carpeta.**

- El [inventario de fuentes iniciales](../Registros/inventario.csv) registra las 37 fotografías reales del lote original y el [manifiesto de Equilibrado v1](../Registros/Lotes/Equilibrado_v1_20261013/manifest.json) enlaza las 102 imágenes de desarrollo (30 reales + 72 sintéticas) anotadas en la tarea 16 de CVAT.
- La copia revisada usada por los modelos `YOLO11-1` y `YOLO26-1` ([`datos_20261015_012453_4ba1d339`](../Registros/Versiones_modelos/datos_20261015_012453_4ba1d339/version.json)) conserva 91 imágenes activas (86 `train` y 5 `val` reales) tras 11 exclusiones.
- Las 7 imágenes de `Reservadas/` están protegidas por [`reserva_evaluacion.json`](../Registros/reserva_evaluacion.json) para impedir su inclusión en entrenamiento o validación de desarrollo.
- La segunda tanda se encuentra en [Datos/V2](../V2/README.md).
