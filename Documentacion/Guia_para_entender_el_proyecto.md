# Cómo funciona Walmart Visión

V3 aprende una sola clase, **Nivel**, para localizar áreas útiles. Después, un algoritmo independiente estima señal visual y la interpreta como Reponer, Suficiente o Revisar. La [release V3 del 26 de octubre](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-10-26) ya está publicada; la ocupación sigue sin calibración V3.

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

En este proyecto, **bordes** son cambios de intensidad de la foto que pueden coincidir con aristas, etiquetas y contornos de envases. No son los contornos del nivel que predice YOLO. El análisis también utiliza color, variaciones locales de brillo y textura; por eso el fucsia de la vista Bordes es un **mapa combinado de señal**, no solamente el resultado de Canny.

El cálculo sigue estas etapas:

1. **YOLO delimita el nivel.** El algoritmo utiliza los píxeles originales dentro de esa máscara, sin analizar los rótulos o colores dibujados sobre el resultado.
2. **Filtra y organiza la señal.** Excluye un margen del contorno y algunas estructuras largas, divide la región en una grilla y calcula bordes, gradiente, color y textura. Los filtros no eliminan de forma fiable todos los carteles, barandas o laterales.
3. **Combina las señales por celda.** Normaliza bordes, gradiente, color y textura dentro del nivel y aplica un umbral adaptativo.
4. **Estima la cobertura del frente.** Cuenta las columnas con señal respaldada por bordes o textura en al menos dos celdas contiguas, a partir del 35 % de la altura del nivel. El espacio libre sobre un producto bajo no reduce la lectura. Se asume lleno detrás del producto visible.
5. **Interpreta la lectura.** Por debajo del 30 % se muestra Reponer y desde el 30 %, Suficiente, cuando la medición y las reglas de revisión lo permiten.

<details>
<summary>Detalle técnico de la señal actual</summary>

La foto se limita a un lado máximo de 1.600 píxeles y la grilla usa celdas de aproximadamente 24 píxeles. Se combinan **35 % densidad de bordes Canny + 30 % gradiente de intensidad + 20 % color saturado + 15 % desviación local de textura**, después de normalizar cada característica por sus percentiles 10–90 dentro de las celdas utilizables. Canny usa 40/120; el umbral adaptativo de Otsu queda limitado a 0,35–0,62. El área se calcula tras un cierre morfológico 3×3 y el ancho usa las activaciones anteriores a ese cierre. Las exclusiones de estructura afectan a todas las señales y el denominador conserva la cobertura válida original.

Estos pesos describen la **construcción del mapa por celda**. La antigua combinación 70/30 de área y ancho se conserva como diagnóstico; la lectura V3 utiliza la cobertura experimental del frente. [Implementación](../Laboratorio/Modelos/ocupacion_paulo.py).

</details>

**El porcentaje no cuenta productos, no mide inventario ni está calibrado como proporción real de stock.** Carteles y fondos pueden activar la señal; productos claros o lisos pueden producir poca. Una zona fucsia no confirma producto y una zona sin señal fucsia no garantiza vacío. Tampoco la confianza de YOLO de 0,60 equivale a un 60 % de ocupación.

### Cuándo se abstiene y pide revisión

La app conserva la señal bruta, pero muestra **Revisar · señal ambigua**, sin porcentaje ni decisión de reposición, cuando la señal se concentra casi totalmente arriba o queda en la periferia sin suficiente respaldo central e inferior. Son comprobaciones experimentales, no detectores automáticos de carteles ni de niveles vacíos. Pueden solicitar revisión con productos escasos o de poco contraste.

La última comparación utilizó **151 fotos de desarrollo y 754 detecciones**: las métricas brutas no cambiaron y se añadieron **35 revisiones**, sin nuevas transiciones a Reponer. No es una evaluación exhaustiva de precisión de ocupación. Los filtros agresivos probados no se integraron porque introdujeron nuevas alertas en los controles. La baranda del superior vacío 034 aún produce señal residual.

## Visibilidad y alcance

La persona revisa si la góndola está despejada o tapada: la app no detecta automáticamente personas ni objetos. Si un contorno alcanza el encuadre, se indica que solo se ve parte del nivel y se pide revisión. Una zona tapada requiere comprobar la foto o tomar otra.

La ausencia de detecciones no prueba vacío. Las métricas mAP evalúan las máscaras de niveles, sin acreditar precisión de ocupación. Las 63 fotos de test siguen reservadas.

[Usar la app](Usar_Walmart_Vision.md) · [Modelo y métricas](Modelo_V3_actual.md) · [Inicio](../README.md)
