> **Alcance de este registro de procedencia.** La V3 vigente reúne **469 imágenes (337 train / 69 val / 63 test)**. Los inventarios, tareas y particiones descritos aquí conservan su versión y fecha; las menciones de un conjunto actual de 458 imágenes corresponden a la etapa anterior a las 11 tomas de refuerzo. Los lotes se solapan y no deben sumarse como datasets independientes. [Estado vigente y límites](../../../../../../Documentacion/Modelo_V3_actual.md).

# Candidatos para entrenamiento, validación y reserva

El criterio de oclusión quedó aplicado técnicamente al lote 22. La selección dispone de [296 imágenes](candidatos_296.csv): 59 originales reales y 237 variantes sintéticas, de 59 familias, con [cobertura por estado y origen](cobertura.json). Las anotaciones de las tareas 19 y 22 están capturadas para esta selección; este cierre no certifica una revisión humana independiente de todas las imágenes.

No se ha asignado ninguna partición ni iniciado entrenamiento. Mantener cada original con todas sus variantes, incluidas las dos ediciones de la familia 001. Los grupos de escena conocidos se propagan a todas sus variantes como bloques provisionales; confirmar también las demás escenas compartidas antes de congelar el reparto.

La validación principal y la reserva final deben basarse en fotos reales independientes. Las variantes de sus escenas solo sirven como diagnóstico sintético separado. Actualmente los nueve niveles no_evaluable del inventario son sintéticos: falta comprobar su comportamiento con oclusiones reales. La reserva independiente anterior queda fuera de este inventario y permanece intacta.

La aprobación para entrenar sigue desactivada hasta seleccionar y validar el reparto y las anotaciones correspondientes.
