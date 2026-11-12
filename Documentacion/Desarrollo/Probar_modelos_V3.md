# Probar modelos geométricos V3

**Actualización posterior del 25/10:** el usuario cerró e integró el best.pt del afinado en Walmart Vision. Ese es el único modelo entrenado visible en el laboratorio; los anteriores están archivados y sus archivos se conservan. La ocupación de la aplicación es experimental y la visibilidad se confirma manualmente. Integración vigente y límites (`Historico/Documentacion/Desarrollo/Integracion_Walmart_Vision_V3_20261025.md`, archivo del entorno local; fuera de esta distribución). Los apartados que describen integración pendiente corresponden al estado anterior de estas pruebas geométricas.

Integración del 25 de octubre de 2026. En [el panel local](http://127.0.0.1:8090/), seleccionar **V3 → Probar una foto**.

El inicio detecta el ensayo terminado y ofrece **Probar mejor modelo**. El enlace permanente **Inicio y siguiente paso** permite volver a consultar el recorrido: datos revisados, detector entrenado, resultados disponibles, revisión humana e integración con Walmart Visión. Un trabajo de predicción no sustituye el seguimiento del entrenamiento.

## Recorrido

1. Elegir el ensayo y **Mejor (best)**. `best.pt` conserva los pesos seleccionados por validación; `last.pt` permite contrastar la última época del mismo ensayo.
2. En **Foto para probar**, elegir **Validación de desarrollo** o **Subir una foto nueva**.
3. Conservar confianza **0,60 como mínimo aceptado**, IoU de inferencia 0,70 y resolución 640, iguales en las comparaciones entre pesos. El mínimo V3 fue confirmado por el usuario durante la revisión visual del 25 de octubre; lo aplican el formulario y la API. Una confianza mayor no garantiza que el contorno sea correcto.
4. Pulsar **Analizar niveles V3**.
5. Revisar **Contornos** y **Comparar**. Comprobar niveles omitidos, detecciones extra, alineación del apoyo, perspectiva y límite superior, especialmente en vacíos y recortes. La confianza no es ocupación.
6. Pulsar **Registrar la decisión sobre este modelo** para abrir el mismo ensayo en **Resultados y decisión**. Registrar candidato, necesita ajustes o descartado, junto con el motivo y el autor. La decisión se guarda solo al enviar ese formulario y conserva su historial; no equivale a publicar el modelo.

En **Resultados y decisión**, las métricas reales y sintéticas y la curva de contornos se consultan en un detalle desplegable. Después de guardar, el inicio indica qué sigue: revisar los ajustes, configurar otro ensayo o resolver la integración de ocupación de un candidato. El panel no presenta como disponible una publicación V3 que todavía no está integrada.

El resultado muestra niveles numerados, contornos y confianza del detector. En las fotos anotadas de validación se añaden coincidencias por IoU de máscara ≥ 0,5, omisiones y detecciones extra. Una foto propia muestra predicciones y no permite medir precisión sin anotaciones de referencia. Se puede descargar la imagen con contornos.

Las métricas históricas de entrenamiento conservan sus condiciones originales. No se deben presentar como una nueva evaluación operativa a confianza 0,60. La primera revisión visual a 0,60 (`Historico/Experimentos/Registros_anteriores.md`, archivo del entorno local; fuera de esta distribución) dejó el ensayo en **Necesita ajustes**.

## Datos permitidos

El selector usa las 68 fotos de validación del ensayo terminado: 28 reales y 40 sintéticas, identificadas por separado. Las fotos se leen de la copia congelada y orientada del ensayo y se verifican contra sus hashes, incluidas sus etiquetas. No se muestran fotos de entrenamiento en ese selector.

Las subidas admiten JPG, PNG o WebP hasta 15 MB y los límites de píxeles del panel. Se orientan según EXIF y permanecen en el área aislada de subidas, fuera de inventarios y datasets. Para V3 se rechaza una subida cuyo hash original identifique una imagen de entrenamiento del modelo o una imagen de la reserva final; una transformación de la imagen puede impedir esa identificación automática.

Las 63 fotos de prueba final permanecen en una galería independiente y cerrada inicialmente, solo para consulta. Su imagen no se carga hasta abrir la galería. No se habilitan sus predicciones ni se usan para ajustar parámetros o seleccionar pesos.

## Alcance

Esta integración prueba la clase geométrica `Nivel` con `best.pt` y `last.pt` de ensayos V3 terminados. Mantiene separados los recorridos V1/V2 y no inicia entrenamiento. La inferencia conserva las máscaras del modelo; no ajusta automáticamente los contornos a cuadriláteros.

Para llevar el modelo a **Walmart Visión** todavía hay que integrar la clase única y el cálculo de ocupación, las comprobaciones de calidad/visibilidad y las reglas de presentación acordadas. Los resultados de esta prueba geométrica no indican `Reponer` o `Suficiente` ni aprueban una publicación del cliente.

[Entrenamiento V3](Entrenamiento_geometrico_V3.md) · [Criterio de niveles](Criterio_V3_niveles.md) · [Propuesta de resultados del cliente](Propuesta_resultados_cliente_V3.md).
