# Segunda tanda (V2) · Líder Express y Visibilidad limitada

Lotes correspondientes al criterio v2 (`reponer`, `suficiente`, `no_evaluable`) en el proyecto 7 de CVAT.

| Lote | Imágenes | Estado y tarea CVAT |
|---|---:|---|
| [Líder Express · etapa base](lider_express_20261016/README.md) | 236 | 59 reales + 177 variantes A/B/C en la [tarea 19](https://pcvicen.tailca514b.ts.net/tasks/19) (80 Canio, 80 Guerra, 76 Vilches). Partición por familias/escenas fijada (160 train / 40 val / 36 test). |
| [Visibilidad limitada · etapa con obstáculos](visibilidad_limitada_20261019/README.md) | 60 | 24 carros, 24 personas y 12 cajas de 59 familias en la [tarea 22](https://pcvicen.tailca514b.ts.net/tasks/22). Partición heredada de cada familia (41 train / 10 val / 9 test). |

Cada lote contiene únicamente sus imágenes activas, prompts, `inventario.csv`, `manifest.json`, galería de revisión y README. El catálogo [Registros/lotes.json](../Registros/lotes.json) y la [partición registrada](../Registros/Particiones/lider_express_v2_20261019/README.md) enlazan ambos lotes sin duplicar archivos.

El material intermedio de generación, muestras previas y carpetas duplicadas de tandas se apartó en .resguardo/orden_v1_v2_20261019 (archivo local histórico, fuera de la distribución).
