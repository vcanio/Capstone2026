# Líder Express · captura del 16 de octubre de 2026

**236 imágenes en una sola [tarea de CVAT](https://pcvicen.tailca514b.ts.net/tasks/19): 59 originales reales y 177 variantes IA.** Cada foto aparece seguida de A, B y C. Las tres variantes y su original quedan en el mismo trabajo.

| Responsable | Fotos base | Originales | Variantes | Total | Trabajo |
|---|---|---:|---:|---:|---|
| Vicente Canio · `vi.canio` | 001–020 | 20 | 60 | 80 | [45](https://pcvicen.tailca514b.ts.net/tasks/19/jobs/45) |
| Paulo Guerra · `pau.guera` | 021–040 | 20 | 60 | 80 | [46](https://pcvicen.tailca514b.ts.net/tasks/19/jobs/46) |
| Vicente Vilches · `vi.vilches` | 041–059 | 19 | 57 | 76 | [47](https://pcvicen.tailca514b.ts.net/tasks/19/jobs/47) |

Un polígono `Nivel` por nivel delimitable. El atributo `estado` admite `reponer` (vacío o menos del 30 % del ancho ocupado), `suficiente` (30 % o más) y `no_evaluable`. A/B/C describe la edición solicitada, no el estado verdadero.

Consultar la [guía de anotación](../../../Documentacion/Desarrollo/Guia_anotacion.md), el [registro verificado](../../Registros/CVAT/tarea_19.json) y el [plan de partición](../../../Documentacion/Desarrollo/Plan_particion_lider_express_20261016.md).

| Contenido | Uso |
|---|---|
| `imagenes_ordenadas/` | 236 imágenes finales: `*_0_original.jpg`, `*_A_vacios.png`, `*_B_baja.png`, `*_C_mixta.png`. |
| [inventario.csv](inventario.csv) | 236 filas con rutas, origen real/IA, fuente, dimensiones, SHA-256, tarea, trabajo y responsable. |
| [Galería](galeria_imagenes_ordenadas.html) | Original y variantes por foto. |
| [Índice](indice_imagenes_ordenadas.json) | Archivos finales y procedencia. |
| [manifest.json](manifest.json) | Cantidades y reparto actual de CVAT. |
| `documentacion_ia/` | Manifiesto de variantes y sus 177 prompts seleccionados. |

Las cinco anotaciones originales disponibles en el respaldo se recuperaron en sus imágenes originales y se verificaron las coordenadas. No se copiaron polígonos a variantes sin anotación. Los registros anteriores y respaldos están en `.resguardo/unificacion_cvat_lider_express_20261017`, relativos a la raíz del proyecto. Los seis trabajos anteriores ya no están activos.

Las 236 imágenes están anotadas. La asignación por persona no define entrenamiento, validación o evaluación. El 19 de octubre se aplicó `particion_modelo=train/val/test` y `grupo_escena` al inventario, manteniendo familias y grupos conservadores juntos: 160/40/36 imágenes base. Consultar el [registro de partición](../../Registros/Particiones/lider_express_v2_20261019/README.md). Entrenamiento sin habilitar; la auditoría de vacíos/poco stock y la exportación siguen pendientes. El autor permanece sin identificar.

Los originales conservan sus bytes y las variantes se identifican como sintéticas. El inventario usa rutas relativas a este lote y fecha de captura únicamente para originales; la fecha de captura fuente se conserva para variantes. Los porcentajes de los prompts no son etiquetas.

[Flujo de datos](../../README.md) · [Catálogo de lotes](../../Registros/lotes.json).
