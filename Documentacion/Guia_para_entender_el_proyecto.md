# Cómo funciona Walmart Visión

V3 aprende una clase, Nivel, para localizar áreas útiles. Las dos apps del 11/11 comparten el cierre revisado adoptado el 10/11 y Línea A del 8/11: índice visual 0–100 con umbral 52. Los ZIP anteriores conservan su contenido histórico.

## Fotografías frontales

**Para usar esta versión, toma fotos frontales o casi frontales de la góndola.** Sitúate frente al tramo, mantén la cámara nivelada y procura que se vean sus dos extremos y las superficies de apoyo. Evita tomas desde un costado, desde muy arriba o abajo, panorámicas deformadas, desenfoque y reflejos fuertes. Si el mueble es largo, utiliza varias tomas frontales de tramos completos.

La perspectiva oblicua cambia las alturas y anchuras aparentes, oculta huecos detrás de los productos y puede desplazar las máscaras. El algoritmo estima una proporción de la imagen, sin reconstruir el volumen ni corregir automáticamente la perspectiva. Una foto frontal ayuda, pero no garantiza una detección correcta: revisa siempre los contornos y la visibilidad. No hay un ángulo máximo validado ni un detector automático que certifique que la toma sea frontal.

## ¿Qué consideramos un nivel?

Un **nivel** es el área útil de una repisa donde pueden existir **productos y huecos**. Se dibuja un polígono para el espacio completo del mismo tramo de góndola, siguiendo su perspectiva; no se dibuja una máscara por envase ni solo la banda frontal del estante.

| Límite | Criterio de anotación |
|---|---|
| Inferior | Superficie donde apoyan los productos, **por encima del portaprecio**. Se excluyen la franja del precio y el espesor frontal del estante. |
| Superior, cuando existe | Cara inferior de la repisa o cubierta física que cierra el espacio. |
| Laterales | Límites interiores del mismo tramo; no se amplía la zona hasta pilares, suelo u otras góndolas. |
| Huecos | Forman parte del área útil, aunque no haya productos. Un nivel vacío sigue siendo un nivel. |

La región se define por la estructura y la convención de anotación, sin ajustarla a la altura de los envases. Un cartel o panel sin una superficie de apoyo asociada no crea otro nivel. Las barandas que atraviesan un nivel pueden quedar dentro de su región y deben tratarse en el análisis de señal; su exclusión automática todavía es imperfecta.

### Superior abierto: por qué acordamos usar la mediana

En una repisa superior sin techo claro era difícil fijar un límite consistente: una persona podía seguir las tapas de los envases, otra un cartel y otra una altura elegida a ojo. Al retirar los productos, esas referencias desaparecían y el mismo nivel lleno o vacío podía terminar con áreas diferentes. Eso introduce una contradicción en los ejemplos usados para enseñar al modelo.

La solución acordada fue una **convención de anotación reproducible**:

1. Si hay una cubierta o un límite físico superior claro, se respeta.
2. Si falta, se miden las alturas verticales de los niveles inferiores del **mismo tramo**. Con perspectiva se mide la altura en el centro de cada polígono.
3. Se calcula la **mediana**, conservando decimales. Con cuatro referencias de 190, 195, 210 y 220 píxeles, la mediana es **202,5 píxeles**.
4. Desde el apoyo del superior, situado **sobre el portaprecio**, se proyecta esa altura hacia arriba. No se utiliza como base, sin comprobarlo, el borde del polígono de abajo: puede representar la cara inferior del estante.
5. Se mantiene el criterio en el original y sus variantes llenas o vacías. Si la proyección sale de la foto, se recorta al encuadre y se marca **parcial**; no se reduce la altura para hacerla caber.

La mediana reduce la influencia de una altura inferior excepcional frente a un promedio simple. **No demuestra la altura física real de un espacio abierto:** fija una región comparable para anotar. Se utilizan habitualmente al menos tres inferiores medibles; las excepciones autorizadas con dos referencias son casos documentados, no una regla general.

**La app no recalcula ni fuerza la mediana al analizar una foto.** YOLO predice sus propias máscaras a partir de lo aprendido; puede omitir un superior o delimitarlo mal. Esos errores se conservan como limitaciones y deben revisarse visualmente.

[Criterio de anotación V3](Criterio_de_niveles.md) · [Regla completa de mediana](Criterio_de_niveles.md)

### Qué significan los bordes y cómo se calcula el índice

Los bordes son cambios de intensidad que pueden coincidir con envases, carteles o estructuras. YOLO delimita el nivel; Línea A analiza la imagen original dentro de esas máscaras.

1. Conserva Canny y aplica la exclusión estructural de rieles y barandas, sin borrar genéricamente los lados rectos de los productos.
2. Extrae la señal por celdas y comparte los límites de normalización entre niveles de la misma góndola.
3. Combina evidencia visual y penaliza huecos continuos en el frente útil.
4. Presenta un índice de 0 a 100: Reponer bajo 52 y Suficiente desde 52, si no hay abstención. Los recortes y señales ambiguas requieren revisión.

El mapa fucsia representa evidencia híbrida. No certifica presencia de productos ni mide porcentaje físico de stock. La confianza de YOLO y el índice de disponibilidad son medidas distintas.

Línea A se validó inicialmente en desarrollo (112 niveles con máscaras humanas: 15/16 alertas, 0 falsas alertas, 1/2 críticos reales) y posteriormente en test ciego completo sobre las 68 fotos de **Ohiggins 3** (354 niveles predichos por YOLO, umbral 52,0 congelado): **Accuracy 97,74 %**, **Precision 93,75 %**, **Recall 83,33 %** y **F1 88,24 %** por nivel (**F1 89,80 %** por foto). El ZIP publicado del 5/11 conserva el estimador anterior y su umbral 30.

[Detalle actual](../Aplicacion/Documentacion/LINEA_A_20261108.md).

## Visibilidad y alcance

La app incorpora además un filtro automático de calidad de captura (`calidad_foto.py`): si una foto está severamente borrosa, muy oscura o quemada por reflejos, se marca como **`no_evaluable`** antes de inferir para evitar falsas alertas de reposición. Para oclusiones por personas o carros, la app del equipo permite indicar manualmente si la góndola está despejada, recortada o tapada y el cliente registra revisión humana por nivel (`No evaluable`). El recorte al borde (`near_frame`) marca `Revisar`; una foto bloqueada muestra el motivo y pide otra toma sin contornos ni ocupación.

La ausencia de detecciones no prueba vacío. Las métricas mAP evalúan las máscaras de niveles, sin acreditar por sí solas precisión de ocupación; por eso **Línea A** se evaluó por separado en el test ciego de **Ohiggins 3** (14/11/2026; el histórico de 63 fotos quedó retirado). Ver [Evaluación test Ohiggins 3](Evidencias/evaluacion_test_ohiggins3_20261114.md).

[Usar la app](Usar_Walmart_Vision.md) · [Modelo y métricas](Modelo_V3_actual.md) · [Inicio](../README.md)
