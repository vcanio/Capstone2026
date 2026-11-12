# V3: localización de áreas útiles

El proyecto V3 usa una clase geométrica, **`Nivel`**, para localizar el área útil de cada nivel. La ocupación y las alertas se calculan después mediante procesamiento experimental.

El modelo vigente es el [cierre revisado del 10/11](../../Documentacion/Modelo_V3_actual.md): 256 train y 11 val reales. La cadena completa usa 519 fuentes train distintas. Las listas de 469 imágenes y el afinado de 113 descritos a continuación son **antecedentes de octubre**, no la preparación actual.

El catálogo histórico tiene **469 imágenes**: 192 reales y 277 sintéticas. La partición histórica de afinado (`Datos/Registros/Particiones/v3_469_afinado_20261025/README.md`, archivo del entorno local; fuera de esta distribución) conserva 337 en entrenamiento, 69 en validación y 63 de prueba final. Una train está desactivada. El último afinado utilizó 113 fotos (`Historico/Datos/Preparados/V3/Refuerzos/afinado_papeles_huevos_20261025/README.md`, archivo del entorno local; fuera de esta distribución), con 49 casos dirigidos y 64 de repaso; su modelo fue integrado en la aplicación de aquella etapa. La [partición histórica de 458](../Registros/Particiones/v3_458_20261023/README.md) y los ensayos anteriores se conservan.

## Fotos según su uso

Abrir galería visual (`Datos/V3/Por_uso/Galeria.html`, archivo del entorno local; fuera de esta distribución) para ver las fotos de desarrollo y filtrar por uso o procedencia.

Entrenamiento, validación y prueba reservada (`Datos/V3/Por_uso/README.md`, archivo del entorno local; fuera de esta distribución) · 113 fotos del último afinado (`Datos/V3/Por_uso/Ultimo_afinado.md`, archivo del entorno local; fuera de esta distribución). Las fotos de V2 que usa V3 aparecen en estas mismas listas.

| Procedencia | Fotos | Tarea V3 | Ubicación |
|---|---:|---:|---|
| Líder Express, originales y A/B/C | 236 | 27 | Líder Express (`Datos/V3/lider_express_20261016/README.md`, archivo del entorno local; fuera de esta distribución) |
| Ediciones con personas, carros y cajas | 60 | 24 | Visibilidad limitada (`Datos/V3/visibilidad_limitada_20261019/README.md`, archivo del entorno local; fuera de esta distribución) |
| Superior vacío D | 40 | 27 | [Lote nuevo V3](superior_vacio_D_20261021/README.md) |
| Líder 2, originales | 122 | 28 | [Lote nuevo V3](Lider 2/README.md) |
| Tomas nuevas de papeles y servilletas | 11 | 31 | Refuerzo revisado (`Datos/V3/Refuerzo/papeles_20261025/README.md`, archivo del entorno local; fuera de esta distribución) |

Los dos lotes de Líder Express están físicamente en V3. Sus rutas anteriores en `Datos/V2` permanecen como enlaces locales para los registros y el laboratorio; los polígonos y criterios se distinguen por tarea. Organizar las imágenes no certifica aprobación de anotaciones ni habilita el entrenamiento.

Las fotos nuevas se reciben en Refuerzo/Por_anotar (`Datos/V3/Refuerzo/Por_anotar/README.md`, archivo del entorno local; fuera de esta distribución). La primera recepción contiene 11 tomas reales de la tarea 31 / trabajo 72 (`Datos/V3/Refuerzo/papeles_20261025/README.md`, archivo del entorno local; fuera de esta distribución), ya anotadas, revisadas e integradas en la partición activa: 47 polígonos, 38 completos y 9 parciales.

El componente de 32 variantes con nivel superior vacío (`Historico/Datos/Preparados/V3/Refuerzos/afinado_superiores_vacios_20261025/README.md`, archivo del entorno local; fuera de esta distribución) se conserva como antecedente de preparación. Esas 32 fotos, las 11 nuevas y las 6 de huevos están incluidas en el afinado de 113; no son conjuntos que deban sumarse otra vez.

[Criterio de anotación](../../Documentacion/Desarrollo/Criterio_V3_niveles.md) · [Tareas y correcciones](../Registros/CVAT/README.md) · [Índice de registros](../Registros/README.md).
