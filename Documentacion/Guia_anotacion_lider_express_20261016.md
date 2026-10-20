# Líder Express · anotación por nivel

**17 de octubre de 2026 · captura del 16 de octubre · criterio `disponibilidad_visual_nivel_v2_reponer`**

Esta guía corresponde a la tarea unificada 19, con 59 originales reales y 177 variantes IA (236 imágenes), y establece los valores válidos para su entrega.

## Qué marcar

Dibuja **un polígono de imagen (Shape) por nivel de góndola**, con la etiqueta **`Nivel`**. Incluye todo el espacio donde van los productos, también los huecos. Marca todos los niveles de los tramos cuyos dos límites laterales puedan identificarse.

Sigue el borde delantero de la superficie de apoyo por abajo, el borde inferior de la repisa superior por arriba y los límites interiores del tramo a los lados. Sigue la perspectiva. Deja fuera soportes, franjas de precios, suelo y techo. No ajustes el contorno al tamaño de los productos.

Si un límite está tapado, complétalo solo cuando se pueda ubicar con claridad. Si no puedes identificarlo, deja el caso para revisión mediante una incidencia de CVAT; no inventes el polígono. En el nivel superior sin repisa encima, acuerda una línea sobre los envases con otro integrante y conserva el criterio para la misma escena.

## Estado obligatorio

Cada polígono entregado debe tener el atributo **`estado`** con **uno de estos tres valores**:

| Valor | Cuándo usarlo |
|---|---|
| **`reponer`** | Está vacío o el producto ocupa menos del 30 % del ancho completo del nivel. |
| **`suficiente`** | El producto ocupa el 30 % o más del ancho completo del nivel. |
| **`no_evaluable`** | La visibilidad impide decidir entre los dos anteriores. |

Imagina el ancho completo del nivel dividido en diez partes: menos de tres partes con producto corresponde a `reponer`; tres o más, a `suficiente`. Un nivel vacío también es `reponer`.

Suma el ancho de los grupos separados. Cuenta los productos visibles al fondo del propio nivel; delante y detrás en la misma posición cuentan una sola vez. No cuentes productos de un tramo vecino. El aire sobre los envases no es un hueco de ancho.

Ante oclusión, activa **Occluded** y conserva el polígono completo cuando puedas delimitarlo. Si el producto visible ya ocupa al menos el 30 % del ancho completo, corresponde `suficiente`. Si lo oculto puede cambiar la decisión, usa `no_evaluable`. Por ejemplo: un 20 % visible con producto y otro 25 % tapado es `no_evaluable`.

Las cajas cerradas no demuestran presencia de producto. Los apilamientos sin una repisa delimitable quedan fuera. Los casos próximos al 30 % deben revisarse con otro integrante antes de entregar; las dudas de criterio pueden registrarse como incidencias.

## Entrega

- Comprueba que cada nivel tenga un solo polígono, siga las repisas y tenga un `estado` válido.
- Revisa con otro integrante los niveles `reponer` y los próximos al 30 %.
- Resuelve las incidencias antes de marcar el trabajo como completado.
- Guarda con **Save** durante el trabajo.

**Formulario:** la etiqueta `Nivel` tiene únicamente el atributo `estado`, con los tres valores de esta guía. No hay campos adicionales. CVAT inicia el selector en `no_evaluable`: comprueba y elige el estado de cada polígono antes de entregar; el valor inicial no acredita que el nivel haya sido evaluado. CVAT no dispone de un bloqueo nativo que obligue a cambiar el selector antes de guardar.

Las 236 imágenes se destinan a anotación. Esta asignación no define entrenamiento, validación ni evaluación y no habilita automáticamente su incorporación a modelos. Los grupos de escena y el autor siguen pendientes de identificación.


## Original y variantes juntos

Cada familia aparece como original, A, B y C, en ese orden, en el mismo trabajo. Anotar todos los niveles delimitables de cada imagen, incluidos los vacíos. A/B/C indican la edición solicitada, no el estado real; por ejemplo 40 % ocupado es suficiente. No copiar automáticamente polígonos entre imágenes, pues la resolución y el contenido pueden cambiar. Los polígonos recuperados de originales corresponden únicamente a su archivo original.

La asignación a personas no es la partición del modelo. Antes de entrenar, mantener familias y escenas juntas, congelar entrenamiento/validación/evaluación y comprobar cobertura de vacíos y poco stock, con evaluación real independiente.
