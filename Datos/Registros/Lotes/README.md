# Lotes: procedencia de las imágenes

Un lote agrupa archivos por captura o generación. Su inventario registra nombres, origen y hashes; su manifest guarda la preparación y procedencia. El [catálogo central `lotes.json`](../lotes.json) enlaza los seis lotes conocidos.

## Lotes que forman el V3 actual

| Lote | Imágenes | Dónde están sus registros | Tarea V3 |
|---|---:|---|---:|
| Líder Express: originales y variantes A/B/C | 236 | [Inventario y manifest del lote](../../V2/lider_express_20261016/README.md) | 27 |
| Visibilidad limitada: personas, carros y cajas | 60 | [Inventario y manifest del lote](../../V2/visibilidad_limitada_20261019/README.md) | 24 |
| Superior vacío D | 40 | [Inventario, manifest y prompts](../../V3/superior_vacio_D_20261021/README.md) | 27 |
| Líder 2: originales | 122 | [Inventario y manifest del lote](../../V3/Lider%202/README.md) | 28 |
| **Total V3** | **458** | [Escenas y particiones](../Particiones/v3_458_20261023/README.md) | |

Algunas fotos de V3 conservan ubicación `V2/` porque son los mismos archivos utilizados con un criterio de anotación nuevo. No se duplicaron ni se renombraron para cambiar de criterio.

## Procedencia anterior

- [Fuentes iniciales](../inventario.csv): 37 fotos reales de Líder, 30 de desarrollo y siete reservadas.
- [Equilibrado V1](Equilibrado_v1_20261013/manifest.json): 102 imágenes de procedencia, que reutilizan esas 30 fotos de desarrollo y añaden 72 sintéticas. Su copia revisada para los primeros ensayos contiene 91 activas.

Por compatibilidad, el inventario antiguo de Equilibrado está dentro de esta carpeta. Los nuevos inventarios viven junto a sus imágenes. **No sumar los seis lotes como si fueran fotografías independientes:** hay fuentes reutilizadas.

Los campos de carga inicial de algunos manifests son históricos. El resumen actual se consulta en [estado_actual.json](../estado_actual.json), y las anotaciones en los registros fechados de [CVAT](../CVAT/README.md). La agrupación en lotes no aprueba el entrenamiento.

[Volver al índice de Registros](../README.md).
