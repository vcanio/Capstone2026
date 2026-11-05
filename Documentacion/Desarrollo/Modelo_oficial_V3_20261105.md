# Modelo oficial V3 · 5 de noviembre de 2026

Vicente pidió dejar el último entrenamiento como oficial y publicar la aplicación para probarla en otro PC. Se adopta el **best.pt** de `v3_refuerzo_geometria_revision_20261105_022414_e6f0`, con SHA-256 `7ec03c8b6aa1164bc8589faf1e3dc904aefe4d6d8b781c1e1df1aff320dad40a`. La aplicación ofrece ese modelo como única opción y lo selecciona al iniciar. Los pesos anteriores del laboratorio se conservan; la adopción no inicia otro entrenamiento.

El job `f1fa7dd986c64ab68299c779cf83ec24` terminó correctamente el 5 de noviembre a las 01:05 de Santiago. Completó 40 épocas; el CSV sitúa el máximo fitness combinado de cajas y máscaras en la época 35. El afinado partió del modelo aceptado el 3 de noviembre y utilizó 171 fotos de entrenamiento. La evaluación de desarrollo contiene 59 reales y 34 sintéticas, separadas por escenas. R254 sigue excluida.

| Máscaras | Fotos | mAP50 | mAP50–95 |
|---|---:|---:|---:|
| Validación real | 59 | 99,50 % | 89,95 % |
| Diagnóstico sintético | 34 | 99,50 % | 93,14 % |

Estas métricas pertenecen a la partición de desarrollo `v3_refuerzo_geometria_20261104`. No deben compararse directamente con agregados históricos de otra partición. Evalúan geometría, no ocupación ni reposición. La reserva final no se utilizó y no se localizó para esta publicación.

El clon incluye el peso operativo y el preparador Windows. El [ZIP con modelo](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-11-05/Walmart_Vision_V3_20261105.zip) reúne los iniciadores Windows, Docker y los módulos actuales de la aplicación. El empaquetador toma el manifiesto oficial, comprueba peso y módulos y rechaza discrepancias con el registro local; ya no fija un ensayo antiguo. Las releases previas conservan sus activos. [Release de esta entrega](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-11-05).

La confianza inicial es 0,60 y el mínimo técnico es 0,25. La ocupación del frente sigue siendo experimental, con umbral 30 %. El flujo normal no detecta automáticamente personas u obstáculos. Se requiere revisión visual; la adopción no garantiza ausencia de falsos niveles ni una mejora global. La prueba en el otro computador queda a cargo de Vicente.
