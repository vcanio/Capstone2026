# Partición de Líder Express: originales y variantes IA

**Actualización del 19 de octubre:** la división por familias y grupos de escena
está fijada para las 236 imágenes base y las 60 de visibilidad. Consultar el
[registro y sus comprobaciones](../Datos/Registros/Particiones/lider_express_v2_20261019/README.md).
El lote base queda en 160/40/36; la validación y evaluación principales usan solo
los 10/9 originales reales de esos bloques. Las sintéticas se evalúan aparte.
La división no habilita entrenamiento: faltan la auditoría de cobertura vacío/poco
stock, el cierre de revisión de visibilidad para la segunda etapa y la exportación v2.

## Anotación y partición son decisiones distintas

Se anotan las 236 imágenes seleccionadas en una sola tarea CVAT (19): 59 originales y 177 variantes IA. Cada original aparece junto a A/B/C en el mismo trabajo. Reparto: 001–020, 80 imágenes para vi.canio; 021–040, 80 para pau.guera; 041–059, 76 para vi.vilches. La tarea única sustituye la organización separada anterior.

Las asignaciones a personas no equivalen a entrenamiento, validación y evaluación. La partición quedó registrada antes de entrenar, tras revisar visualmente grupos y comprobar las anotaciones de referencia. Anotar una imagen de evaluación está permitido; usarla para ajustar el modelo o elegir hiperparámetros no lo está.

## Evitar filtración entre conjuntos

- Una foto original y sus variantes A/B/C pertenecen a la misma familia. Ninguna familia puede repartirse entre entrenamiento, validación o evaluación.
- Las fotos distintas de una misma góndola/escena, con productos y fondos compartidos, también deben permanecer juntas. El número de archivo no basta para asegurar independencia.
- Revisar como mínimo las escenas próximas 046–048, 049–050, 051–054 y 055–056; son candidatos conocidos, no una lista exhaustiva de grupos definitivos.
- Mantener intacta la reserva independiente del lote anterior; no incluirla en entrenamiento.

Se tomó 70/15/15 como orientación, sin forzar el porcentaje si rompía grupos. El reparto base aplicado es aproximadamente 68/17/15 por imágenes, con 14/3/2 grupos conservadores. Queda pendiente auditar vacío frente a poco stock dentro de reponer; la cobertura de estados reales es escasa y está documentada en el registro.

## Cobertura obligatoria antes de entrenar

El criterio vigente usa `reponer` cuando un nivel está vacío o tiene menos del 30 % del ancho ocupado; `suficiente` desde el 30 %; `no_evaluable` cuando no se puede decidir. La letra A/B/C y el prompt describen la edición solicitada, no la etiqueta real. Una variante B con 40 % ocupado es `suficiente`.

Para prevenir el problema de la prueba anterior, verificar por partición los niveles y las imágenes que contienen:

1. Vacíos, 0 %.
2. Poco stock, mayor que 0 % y menor que 30 % (`reponer`).
3. Entre 30 % y menos de 50 %: ocupación baja visual pero `suficiente` según el criterio actual.
4. Niveles con 50 % o más y niveles `no_evaluable` si existen.

El formulario de CVAT conserva únicamente los tres estados vigentes. La distinción de vacíos y porcentajes se comprueba en una auditoría de cobertura separada, sin agregar atributos al proyecto ni deducirlos automáticamente del nombre del archivo.

Entrenamiento y validación deben tener tanto `reponer` como `suficiente`, con vacíos y poco stock comprobados. Si faltan grupos independientes de algún caso, ajustar el reparto por grupos o conseguir imágenes reales adicionales. La ausencia de un caso no se corrige trasladando una variante de un original que ya está en otro conjunto.

## Validación sintética y evaluación real

Usar fotos reales independientes para la validación principal y la evaluación final. Las variantes sintéticas de escenas reservadas pueden formar un bloque complementario de diagnóstico, identificado explícitamente como sintético; no mezclar sus métricas con las reales ni tratar sus artefactos como evidencia de rendimiento en supermercado.

Si las fotos reales de validación o evaluación no contienen vacíos y poco stock, todavía no se puede asegurar ese comportamiento con datos reales: incorporar capturas reales independientes de esos casos antes de cerrar la evaluación. La cobertura de las variantes ayuda, pero no sustituye esa comprobación.

## Comprobaciones de cierre

- Anotaciones revisadas, un polígono por nivel delimitable y estados válidos.
- Familias y escenas sin solapamiento entre particiones.
- Cobertura de vacíos, poco stock y suficientes documentada para cada partición; no limitarse al número total de fotos.
- Manifiesto de partición guardado con grupos, fuentes, origen real/IA, hashes y motivos de exclusión.
- Sin entrenamiento automático ni partición definitiva mientras falten las comprobaciones anteriores.

Referencias: [importación de tareas CVAT](https://docs.cvat.ai/docs/dataset_management/import-datasets/), [partición por grupos en scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).
