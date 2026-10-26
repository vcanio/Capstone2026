# Cómo funciona Walmart Visión

V3 aprende una sola clase, **Nivel**, para localizar áreas útiles. Después, un algoritmo independiente estima señal visual y la interpreta como Reponer, Suficiente o Revisar. La release del 26 de octubre se prepara como borrador; la ocupación sigue sin calibración V3.

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

[Criterio de anotación V3](Desarrollo/Criterio_V3_niveles.md) · [Regla completa de mediana](Desarrollo/Regla_nivel_superior_mediana_V3.md)

### Qué significan los bordes y cómo se calcula la ocupación

En este proyecto, **bordes** son cambios de intensidad de la foto que pueden coincidir con aristas, etiquetas y contornos de envases. No son los contornos del nivel que predice YOLO. El análisis también utiliza color, variaciones locales de brillo y textura; por eso el amarillo de la vista Bordes es un **mapa combinado de señal**, no solamente el resultado de Canny.

El cálculo sigue estas etapas:

1. **YOLO delimita el nivel.** El algoritmo utiliza los píxeles originales dentro de esa máscara, sin analizar los rótulos o colores dibujados sobre el resultado.
2. **Filtra y organiza la señal.** Excluye un margen del contorno y algunas estructuras largas, divide la región en una grilla y calcula bordes, gradiente, color y textura. Los filtros no eliminan de forma fiable todos los carteles, barandas o laterales.
3. **Combina las señales por celda.** Normaliza sus intensidades dentro del nivel y aplica un umbral adaptativo. Después obtiene dos medidas: **A**, superficie con señal, ponderada por la cobertura válida de las celdas, y **W**, proporción de columnas con suficiente señal vertical.
4. **Calcula la estimación:** `ocupación estimada = 0,70 × A + 0,30 × W`. Por ejemplo, A = 40 % y W = 80 % producen **52 %**.
5. **Interpreta la lectura.** Por debajo del 30 % se muestra Reponer y desde el 30 %, Suficiente, siempre que la medición, la visibilidad y las reglas de abstención lo permitan.

El ancho no pregunta solo si una columna tiene algún píxel activo: exige señal en al menos el **20 % de sus celdas utilizables**. El área y el ancho aportan información distinta: unos productos bajos extendidos a lo largo del estante pueden cubrir poco área y mucho ancho.

<details>
<summary>Detalle técnico de la señal actual</summary>

La foto se limita a un lado máximo de 1.600 píxeles y la grilla usa celdas de aproximadamente 24 píxeles. Se combinan **35 % densidad de bordes Canny + 30 % gradiente de intensidad + 20 % color saturado + 15 % desviación local de textura**, después de normalizar cada característica por sus percentiles 10–90 dentro de las celdas utilizables. Canny usa 40/120; el umbral adaptativo de Otsu queda limitado a 0,35–0,62. El área se calcula tras un cierre morfológico 3×3 y el ancho usa las activaciones anteriores a ese cierre. Las exclusiones de estructura afectan a todas las señales y el denominador conserva la cobertura válida original.

Estos pesos describen la **construcción del mapa por celda**. Son distintos de la combinación final **70/30 de área y ancho**. [Implementación](../Herramientas/Modelos/ocupacion_paulo.py).

</details>

**El porcentaje no cuenta productos, no mide inventario ni está calibrado como proporción real de stock.** Carteles y fondos pueden activar la señal; productos claros o lisos pueden producir poca. Una zona amarilla no confirma producto y una zona sin amarillo no garantiza vacío. Tampoco la confianza de YOLO de 0,60 equivale a un 60 % de ocupación.

### Cuándo se abstiene y pide revisión

La app conserva la señal bruta, pero muestra **Revisar · señal ambigua**, sin porcentaje ni decisión de reposición, cuando la señal se concentra casi totalmente arriba o queda en la periferia sin suficiente respaldo central e inferior. Son comprobaciones experimentales, no detectores automáticos de carteles ni de niveles vacíos. Pueden solicitar revisión con productos escasos o de poco contraste.

La última comparación utilizó **151 fotos de desarrollo y 754 detecciones**: las métricas brutas no cambiaron y se añadieron **35 revisiones**, sin nuevas transiciones a Reponer. No es una evaluación exhaustiva de precisión de ocupación. Los filtros agresivos probados no se integraron porque introdujeron nuevas alertas en los controles. La baranda del superior vacío 034 aún produce señal residual.

## Visibilidad y alcance

La persona indica si la góndola está despejada, recortada, tapada por un objeto o por una persona. No se detectan automáticamente estos casos. El recorte limita el porcentaje a la zona visible y marca Revisar; el objeto suspende la medición; una persona tapando muestra Góndola tapada y pide otra foto sin contornos ni ocupación.

La ausencia de detecciones no prueba vacío. Las métricas mAP evalúan las máscaras de niveles, sin acreditar precisión de ocupación. Las 63 fotos de test siguen reservadas.

[Usar la app](Usar_Walmart_Vision.md) · [Modelo y métricas](Modelo_V3_actual.md) · [Inicio](../README.md)
