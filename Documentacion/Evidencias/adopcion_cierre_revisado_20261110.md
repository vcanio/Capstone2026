# Adopción del cierre revisado · 10/11/2026

Vicente adoptó `V3-cierre-revisado-20261110` como predeterminado en las dos apps para cerrar de momento el localizador y centrarse en ocupación. SHA-256 `dc679fe73a7525dcffefe0381edfc39309d2ebe3f5115387100ae53cf4550af5`. El registro de adopción y sus respaldos completos permanecen locales.

El ensayo completó 40 épocas sobre 256 train (203 reales/53 sintéticas), 1.298 polígonos, y 11 val reales con 55 polígonos. En las mismas 11 val, el anterior y el adoptado tienen 54 TP, 0 FP y 1 FN. No se demuestra superioridad global. En la revisión humana de Ohiggins 3 se aceptaron 65 de 68 fotos y se marcaron siete contornos incorrectos en tres fotos; esa fracción no es mAP, recall ni exactitud de ocupación. R065 mantiene una omisión en diagnóstico de train.

La adopción local comprobó inferencia HTTP GPU en ambas apps sobre la misma foto de train: cinco contornos y estimaciones idénticos, nuevo modelo y hash comprobado. No hubo entrenamiento nuevo ni cambios de ocupación, CVAT o etiquetas. Las 68 fotos revisadas siguen fuera de train y el test histórico de 63 fotos no se utilizó. La adopción original no publicó; la entrega del 11/11 incorpora después este peso.

[Ficha vigente](../Modelo_V3_actual.md) · [Catálogo de entrenamiento](catalogo_modelo_oficial_cierre_20261110.json).
