# V3: localización de áreas útiles

El proyecto V3 usa una clase geométrica, **`Nivel`**, para localizar el área útil de cada nivel. La ocupación y las alertas se calculan después mediante un procesamiento validado.

El conjunto actual tiene **458 imágenes**: 181 reales y 277 sintéticas. Sus registros y asignaciones están en [la partición V3](../Registros/Particiones/v3_458_20261023/README.md), con 327 entrenamiento, 68 validación y 63 prueba.

| Procedencia | Fotos | Tarea V3 | Ubicación |
|---|---:|---:|---|
| Líder Express, originales y A/B/C | 236 | 27 | [Fuentes conservadas en V2](../V2/lider_express_20261016/README.md) |
| Ediciones con personas, carros y cajas | 60 | 24 | [Fuentes conservadas en V2](../V2/visibilidad_limitada_20261019/README.md) |
| Superior vacío D | 40 | 27 | [Lote nuevo V3](superior_vacio_D_20261021/README.md) |
| Líder 2, originales | 122 | 28 | [Lote nuevo V3](Lider%202/README.md) |

Los archivos heredados conservan su ubicación; los polígonos y criterios se distinguen por tarea. Organizar las imágenes no certifica aprobación de anotaciones ni habilita el entrenamiento.

[Criterio de anotación](../../Documentacion/Desarrollo/Criterio_V3_niveles.md) · [Tareas y correcciones](../Registros/CVAT/README.md) · [Índice de registros](../Registros/README.md).
