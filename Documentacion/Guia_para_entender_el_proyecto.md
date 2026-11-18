# Cómo funciona Walmart Visión

La **segmentación de niveles** con `YOLO26n-seg` crea una máscara por repisa. El estimador calcula la disponibilidad visual dentro de cada máscara. Las dos apps comparten este motor, el filtro de calidad y la detección de personas. El cliente muestra alertas, guarda historial en SQLite y exporta CSV, Excel y PDF. El equipo permite marcar fallos, comparar análisis y exportar lotes ZIP. [Entrega vigente](../Entregables/README.md) · [De la foto a la alerta](../Aplicacion_Cliente/README.md#de-la-foto-a-la-alerta).

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

YOLO predice sus máscaras a partir de lo aprendido. Después, la app compara la altura del superior detectado con la mediana de los inferiores. Si el superior abierto parece truncado, añade un aviso y una lectura «Suficiente» pasa a «Revisar». La máscara original se conserva. Una omisión completa puede requerir revisión visual. [Verificación geométrica](../Aplicacion/geometria_niveles.py).

[Criterio de anotación de niveles y regla de mediana](Criterio_de_niveles.md).

### Qué significan los bordes y cómo se estima la disponibilidad visual

Los bordes son cambios de intensidad que pueden coincidir con envases, carteles o estructuras. YOLO delimita cada nivel; el estimador de disponibilidad visual ([`ocupacion_linea_a.py`](../Aplicacion/ocupacion_linea_a.py)) analiza la imagen original dentro de esas máscaras en cinco etapas:

1. **Grilla de celdas y señales direccionales:** conserva Canny y excluye rieles/barandas horizontales ([`ocupacion_paulo.py`](../Aplicacion/ocupacion_paulo.py)), extrayendo por celda densidad de bordes (`d`), gradiente Sobel (`g`), saturación HSV (`c`), desviación estándar local (`t`), gradientes `gx`/`gy`, bordes verticales (`vx`) y blancura (`bu`).
2. **Anclaje intra-góndola (`P10–P90`) y puntaje por celda:** normaliza todas las máscaras de la misma góndola con límites compartidos (`cell_score = 0,35·dn + 0,28·gn + 0,17·cn + 0,20·tn`) y exige respaldo mínimo de bordes o textura al color saturado para no confundir tableros lisos vacíos.
3. **Bandas adaptativas, filtros de fondo y protecciones `v2.2`:** sigue bandas verticales relativas en estantes inclinados, descarta **cielo abierto** en el nivel superior (`_open_ceiling_mask_v2`) y **bandeja/piso expuesto** en vista picada (`_exposed_floor_mask`), mientras protege **sacos blancos apilados bajo sombra** en niveles medios (`_is_white_stocked_packages`), **cajas máster bicolor impresas** (`_is_bicolor_printed_box`) y **productos retraídos al fondo** sobre bandeja oscura (`_has_recessed_upper_product`).
4. **Cobertura horizontal y hueco efectivo (`analyze_column_gaps`):** una columna de soporte cubre con `≥ 22 %` de celdas activas; neutraliza islas débiles aisladas (hasta `2` columnas con `< 35 %` de apoyo) entre tramos vacíos y calcula el hueco máximo (`max_gap_pct`), los huecos significativos (`≥ 15 %`) y el hueco efectivo `max(max_gap_pct, 0,85 × significant_gaps_pct)`.
5. **Índice visual (`0–100`), decisión combinada y severidad:** acota el relleno vertical por el hueco efectivo (`pct = min(fill_pct, 100 - effective_gap_pct)`, conservado en `raw_pct`). Dispara **Reponer** si `pct < 52` o ante quiebre parcial de frente (`max_gap_pct ≥ 35 %` con `front_hyb_pct < 68 %`, o `significant_gaps_pct ≥ 45 %`) con severidad **`critica`** (`pct ≤ 15 %` o hueco `≥ 60 %`) o **`alta`**; deriva a **Revisar** (`verificar`) recortes al encuadre, carteles altos, señal ambigua o frentes oscuros continuos de bajo contraste (`low_contrast_continuous_front`); y marca **Suficiente** (`normal`) cuando llega al umbral y la lectura está libre de alertas y ambigüedad.

El mapa fucsia representa evidencia híbrida. No certifica presencia de productos ni mide porcentaje físico de stock. La confianza de YOLO y el índice de disponibilidad son medidas distintas.

La línea base del estimador (umbral 52,0 congelado) se evaluó en ciego sobre las 68 fotos de **Ohiggins 3** (354 niveles predichos por YOLO): **Accuracy 97,74 %**, **Precision 93,75 %**, **Recall 83,33 %** y **F1 88,24 %** por nivel (**F1 89,80 %** por foto). En una reevaluación posterior, tras revisar errores del mismo conjunto, el estimador vigente obtuvo **Accuracy 98,87 %**, **Precision 92,11 %**, **Recall 97,22 %**, **Especificidad 99,06 %** y **F1 94,59 %** (`35 TP / 3 FP / 1 FN / 315 TN`), y tuvo una revisión operativa sobre **193 fotos / 893 detecciones** en tres capturas (`9_11 Ohiggins`, `14_11 Ohiggins` y `15_11 Marcoleta`). El ZIP histórico del 5/11 conserva el estimador anterior con umbral 30.

[Detalle inicial (8/11)](../Aplicacion/Documentacion/LINEA_A_20261108.md) · [Ficha del modelo y casos límite](Modelo_V3_actual.md).

## Visibilidad y alcance

La app incorpora además un filtro automático de calidad de captura (`calidad_foto.py`): si una foto está severamente borrosa, muy oscura o quemada por reflejos, se marca como **`no_evaluable`** antes de inferir para evitar falsas alertas de reposición. Con `yolo26n-seg.pt` ([`oclusiones.py`](../Aplicacion/oclusiones.py)), cuando una persona obstruye al menos el 15 % del área o del ancho afectado de un nivel, o el 10 % de la imagen cuando faltan máscaras válidas, la foto también se marca automáticamente como **`no_evaluable`** y muestra un contorno ámbar sutil señalando la obstrucción; carros u otros obstáculos sin máscara de persona siguen sujetos a verificación visual. En cliente se muestran directamente las alertas del modelo sin controles manuales, mientras [`geometria_niveles.py`](../Aplicacion/geometria_niveles.py) alerta cuando el nivel superior abierto parece truncado y `near_frame` marca `Revisar`.

La ausencia de detecciones no prueba vacío. Las métricas mAP evalúan las máscaras de niveles, sin acreditar por sí solas precisión de ocupación. La evaluación ciega del estimador de disponibilidad visual del 14/11 corresponde a la línea base de Ohiggins 3. La v2.2 requiere un conjunto nuevo para medir generalización independiente. Ver [Evaluación test Ohiggins 3](Evidencias/evaluacion_test_ohiggins3_20261114.md).

[Usar la app](Usar_Walmart_Vision.md) · [Modelo y métricas](Modelo_V3_actual.md) · [Inicio](../README.md)
