# Propuesta de resultados V3 para Walmart Visión

Fecha: 25 de octubre de 2026. Propuesta para discusión; no implementa inferencia, no cambia anotaciones, particiones, umbrales ni autoriza entrenamiento. Se apoya en el criterio de área útil V3 y en la interfaz V2 existente.

## Recorrido

1. YOLO segmenta cada `Nivel`, incluidos sus huecos y productos.
2. Una comprobación adicional decide si la geometría, la imagen y la visibilidad permiten medir.
3. El algoritmo de bordes/color/textura estima ocupación dentro de una región válida, excluyendo estructura y obstáculos identificados.
4. Una regla calibrada convierte una medición comparable en una recomendación de reposición.
5. La interfaz muestra recomendación, ocupación y alcance de esa ocupación.

Las marcas de CVAT `delimitacion` y `Occluded` no son salidas del modelo de una sola clase. Hay que resolver recorte, obstáculos y calidad en inferencia, mediante comprobaciones adicionales, otro componente o confirmación humana. Tocar el borde de la foto puede ser un indicio de recorte; no demuestra por sí solo su ausencia o presencia.

**Decisión del usuario durante la revisión del 25 de octubre:** confianza mínima aceptada para las detecciones V3 **0,60**. Si una persona tapa la góndola, suprimir los contornos de toda esa foto y no emitir ocupación ni reposición: mostrar **«Góndola tapada»** y pedir otra foto sin personas delante. Esta excepción prevalece sobre los casos genéricos de oclusión de la matriz siguiente. Se trata de visibilidad de la góndola; la mera presencia de una persona fuera de ella no demuestra que esté tapada. El mínimo ya se aplica a las pruebas V3 del laboratorio; la detección automática de la oclusión por personas sigue pendiente. No se borran sus anotaciones ni se convierten estas fotos en negativos de entrenamiento.

## Lectura para el cliente

Mostrar por nivel:

- **Acción:** Reponer / Suficiente / Revisar.
- **Ocupación:** porcentaje estimado, o guion si no existe una medición fiable.
- **Alcance:** Nivel completo / Solo zona visible.
- **Avisos:** Nivel recortado / Objeto delante / Foto insuficiente, con motivo y siguiente paso.

En este documento, «nivel completo» describe el área frontal útil definida por el criterio V3, no el volumen ni el stock detrás de la primera fila. «Suficiente» se refiere a esa ocupación visual bajo la regla de negocio calibrada.

## Matriz de casos

Todos los porcentajes y decisiones presuponen una medición válida y un umbral calibrado para la métrica y el alcance usados. Si ese supuesto falla, prevalece Revisar.

| Caso | Medición y decisión | Presentación y acción |
|---|---|---|
| Completo, sin obstáculos, por debajo del umbral | Ocupación del nivel; Reponer | `Nivel 1 · 18 % · Reponer` |
| Completo, sin obstáculos, por encima del umbral | Ocupación del nivel; Suficiente | `Nivel 2 · 74 % · Suficiente` |
| Completo y vacío con evidencia fiable | 0 % o cercano a cero según el estimador; Reponer | `Nivel 3 · 0 % estimado · Reponer`. No forzar cero porque falten bordes. |
| Completo, cerca del umbral y decisión inestable | Conservar estimación; Revisar | `29 % estimado · Cerca del límite · Revisar`. Margen pendiente de calibración. |
| Completo con oclusión irrelevante para la región medida | Medir solo si se comprueba que no contamina la región | Estado habitual; aviso si ayuda a interpretar la foto. |
| Completo ocluido, máscara del obstáculo fiable y zona visible suficiente | Excluir lo oculto de la región observada; medir solo lo visible | `42 % visible · Objeto delante · Revisar nivel completo`. Puede añadirse señal local si está validada. |
| Completo ocluido, sin máscara fiable o zona visible insuficiente | Sin medición | `— · Objeto delante · Toma otra foto sin el obstáculo`. |
| Parcial, visible bien delimitado, ocupación local baja | Medición visible; recomendación limitada a esa zona si está calibrada | `18 % visible · Reponer en zona visible · Nivel recortado`. El nivel completo sigue pendiente. |
| Parcial, visible bien delimitado, ocupación local alta | Medición visible; sin declarar suficiente el nivel completo | `74 % visible · Zona visible suficiente · Nivel recortado`. Revisar lo que falta. |
| Parcial y zona visible vacía | Medición local válida; reposición local | `0 % visible estimado · Reponer en zona visible`. No decir que todo el nivel está vacío. |
| Parcial recortado arriba/abajo | Área y combinación pueden cambiar de significado al cambiar altura | Mostrar porcentaje visible si es válido; suspender regla global hasta validar comparabilidad. No asumir el mismo umbral que en un nivel completo. |
| Parcial y ocluido | Combinar ambos avisos; medir solo zona visible no tapada si es fiable | `Solo zona visible · Nivel recortado · Objeto delante`; nivel completo pendiente. Si no hay región fiable, guion. |
| Perímetro incierto o mal segmentado | Sin medición sobre región dudosa | `Revisar delimitación · Toma una foto más frontal` o corrección humana explícita. |
| Borroso, oscuro, sobreexpuesto o reflejos intensos | Bloquear los niveles afectados si la calidad invalida su medición | `— · Mejora iluminación / evita reflejos / enfoca`. Conservar niveles válidos de la misma foto. |
| Muy pequeño o perspectiva extrema | Sin medición si no hay resolución o geometría suficiente | `— · Acércate y toma la foto de frente`. |
| Contorno válido, pero medición de bordes/color/textura no fiable | Sin estado de reposición | `Nivel detectado · No se pudo medir · Revisar`. Pocos bordes no significan vacío. |
| Reflejos, carteles, portaprecios, barandas o fondo activan señal falsa | Filtrar estructura y validar; si no se resuelve, abstenerse | No convertir esa señal directamente en producto. Aviso específico de interferencia cuando pueda identificarse. |
| Detecciones duplicadas, niveles mezclados o geometría incompatible | Resolver antes de contar o medir; si persiste, Revisar | No sumar dos veces ni mostrar porcentajes engañosos de un nivel combinado. |
| Ningún nivel detectado | Sin ocupación ni reposición automática | `No pudimos localizar niveles · Toma otra foto`. No significa góndola vacía. |
| Nivel omitido entre otros detectados | No inventar geometría ni un estado | Si hay evidencia independiente de omisión, aviso para revisar; sin inventario no se conoce cuántos niveles faltan. |
| Solo localización, sin ejecutar ocupación | Mostrar contornos sin estado de reposición | `Nivel detectado · Ocupación sin calcular`. |
| Fallo de análisis | No mostrar resultado anterior como vigente | Error claro y reintento, manteniendo la foto elegida. |

## Interfaz

Conservar la foto como elemento principal, niveles numerados y selección enlazada con la tabla o ficha. Para varios módulos, identificar módulo y nivel sin tratar el número de la foto como una identidad persistente.

Rojo con texto para Reponer; verde con texto para Suficiente del nivel completo; ámbar para Revisar; gris para ausencia de medición. Una reposición local puede ser roja, pero debe decir `zona visible` y conservar el aviso de revisión del resto. Una zona visible alta no debe teñir todo el nivel de verde.

Zona desconocida tramada o sombreada, sin pintarla como hueco. Dibujar una oclusión localizada solo cuando exista una máscara fiable; si no, usar aviso textual. No dibujar área fuera de la fotografía. No mostrar porcentaje de visibilidad del nivel entero si se desconoce su extensión.

Tabla: `Nivel | Ocupación estimada | Alcance | Resultado | Aviso / acción`. En móvil, fichas con la misma información. Un porcentaje entero en la vista principal; detalle numérico técnico aparte, sin fingir precisión.

Resumen ejemplo: `6 niveles detectados: 2 para reponer, 1 suficiente y 3 con revisión pendiente`. Las recomendaciones parciales se desglosan aparte: `1 de las revisiones tiene faltantes en la zona visible`. No contar las advertencias como niveles adicionales. No anunciar «góndola suficiente» si quedan zonas sin comprobar.

Acciones por motivo: `Repetir foto`, `Ver zona` y, si se implementa, `Corregir contorno` / `Confirmar visibilidad`. Una corrección humana se registra como tal y obliga a recalcular.

La vista principal es `Resultado`; Original, Comparar y el detalle del cálculo permanecen disponibles. Bordes, pesos y confianza YOLO van en detalle técnico. La descarga debe preservar los mismos estados, alcances y avisos de la pantalla.

## Cambios necesarios frente a V2

- Separar localización de recomendación. Solo YOLO V3 no devuelve reponer/suficiente.
- Añadir calidad y visibilidad a la inferencia; las marcas manuales de entrenamiento no resuelven esta etapa automáticamente.
- Evitar que el porcentaje por sí solo determine el color. Exigir medición válida, alcance conocido y regla aplicable.
- Medir obstáculos como desconocidos, no como producto ni vacío; una máscara visible tiene su propio denominador.
- Definir la magnitud: área frontal, ancho o índice combinado. El combinado actual 70 % de área y 30 % de ancho es un índice; no es directamente una fracción física de producto ni volumen.
- Calibrar umbral, tolerancia cerca del límite y condiciones mínimas de visibilidad. El 30 % actual es una regla provisional de presentación; no transferirlo automáticamente a V3 o a cualquier recorte.
- Validar localización, ocupación, falsos avisos de reposición y abstención por separado en desarrollo. Mantener test reservado hasta congelar modelo y reglas; reportar sintéticas aparte.

Para una primera versión V3: decisiones completas cuando exista evidencia suficiente; mediciones visibles con alcance explícito cuando sean fiables; revisión concreta cuando falte evidencia. No hace falta cambiar la clase `Nivel` ni volver a anotar estados de disponibilidad para construir esta política.

## Referencias

- [Criterio V3](Criterio_V3_niveles.md).
- [Preparación de parciales revisados](Preparacion_V3_parciales_revisados.md).
- [Interfaz actual](../../Aplicacion/interfaz.html).
- [Estimador actual](../../Laboratorio/Modelos/ocupacion_paulo.py).
- [YOLO: salidas de segmentación](https://docs.ultralytics.com/tasks/segment/).
- [OpenCV: Canny](https://docs.opencv.org/4.12.0/d7/de1/tutorial_js_canny.html).
