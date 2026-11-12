# Entrenamiento geométrico V3 · estado del 11/11/2026

El localizador queda cerrado de momento por decisión de Vicente. El oficial es el `best.pt` de `v3_cierre_yolo_contornos_revisados_20261110_222620_aa7c`, adoptado el 10/11, SHA-256 `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`. Las apps comparten ese peso. [Ficha, datos y métricas](../Modelo_V3_actual.md).

## Último ensayo completado

256 train (203 reales/53 sintéticas), 1.298 polígonos; 11 val reales con 55 polígonos. Entrenamiento desde el oficial del 5/11, 40 épocas, paciencia 10, AdamW, lr 0,0001, resolución 640, batch 2, semilla 42. La selección y exportación del cierre están congeladas; no se proponen otra vez como un entrenamiento pendiente.

Las tres etapas de la cadena contienen 519 fuentes train distintas por SHA-256. Las 82 antiguas val migradas a train ya no son validación independiente. Las 11 val actuales no son comparables directamente con los agregados de antiguas particiones. Las 68 de Ohiggins 3 tienen revisión visual humana y siguen fuera de train; no son un conjunto de etiquetas para ajustar el cierre. El test histórico de 63 fotos permanece reservado.

## Un futuro refuerzo

Requiere un plan nuevo desde el oficial actual, fuentes y anotaciones revisadas, repaso, exclusiones y separación por escenas/familias. Preparar o consultar datos no autoriza a iniciar otro ensayo. **Solo Vicente inicia entrenamiento desde el panel.** Límites acordados para el próximo refuerzo: máximo 40 épocas, paciencia 10 y lr 0,0001, sujetos al plan que apruebe.

El panel conserva hashes de pesos y preparaciones, crea un ensayo nuevo y muestra métricas y decisión sin adoptar automáticamente un candidato. Las cargas y marcas de las apps no se convierten en entrenamiento. No tocar el test para inferencia, selección de checkpoint o ajuste. No restaurar R254 ni generalizar excepciones de anotación.

[Laboratorio actual](../../Laboratorio/Modelos/README.md) · [Criterio V3](Criterio_V3_niveles.md) · [Antecedentes de entrenamiento conservados](../../Historico/Documentacion/Desarrollo/Entrenamiento_geometrico_V3_antes_alineacion_20261111.md).
