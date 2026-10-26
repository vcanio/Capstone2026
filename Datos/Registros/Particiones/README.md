> **Alcance de este registro de procedencia.** La V3 vigente reúne **469 imágenes (337 train / 69 val / 63 test)**. Los inventarios, tareas y particiones descritos aquí conservan su versión y fecha; las menciones de un conjunto actual de 458 imágenes corresponden a la etapa anterior a las 11 tomas de refuerzo. Los lotes se solapan y no deben sumarse como datasets independientes. [Estado vigente y límites](../../../Documentacion/Modelo_V3_actual.md).

# Particiones: entrenamiento, validación y prueba

Aquí se fija el uso reservado de cada foto, manteniendo juntas las familias y las vistas de una escena. No se almacenan nuevas copias de las imágenes para repartirlas.

| Registro | Estado y alcance |
|---|---|
| [V3 · 458 imágenes · 23/10/2026](v3_458_20261023/README.md) | **Vigente para V3:** 327 entrenamiento, 68 validación y 63 prueba. 43 grupos conservadores. Incluye catálogo visual, inventario, listas y verificación. |
| [Líder Express V2 · 19/10/2026](lider_express_v2_20261019/README.md) | Antecedente congelado de 296 imágenes. Sus familias y reservas se conservaron al ampliar a V3. Sus fuentes y hashes no se reescriben. |

Una partición asigna el destino de la imagen; no certifica la calidad de su anotación ni la incluye automáticamente en una exportación. Las futuras variantes heredan el grupo y el uso de su original. El test se reserva para evaluación final; los diagnósticos sintéticos se reportan separados de las fotos reales.

Si aparece una relación entre escenas de particiones distintas, documentar una nueva versión antes de entrenar. No corregir un reparto congelado moviendo fotos silenciosamente.

[Volver al índice de Registros](../README.md).
