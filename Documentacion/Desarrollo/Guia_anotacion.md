# Guía de anotación y oclusiones en CVAT

**Criterio V2 del 17 de octubre de 2026 · captura del 16 de octubre · guía consolidada con las decisiones de oclusión del 19 de octubre.**

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

Las 236 imágenes pertenecen a familias y grupos de escena con partición fijada. La etapa V2 base usa 160 imágenes para entrenar y 10 originales reales para validar; las variantes de diagnóstico y la reserva final quedan fuera de esa exportación. La asignación por persona no define la partición. Consultar el [registro vigente](../../Datos/Registros/Particiones/lider_express_v2_20261019/README.md). El autor de las capturas permanece sin identificar en el inventario.


## Original y variantes juntos

Cada familia aparece como original, A, B y C, en ese orden, en el mismo trabajo. Anotar todos los niveles delimitables de cada imagen, incluidos los vacíos. A/B/C indican la edición solicitada, no el estado real; por ejemplo 40 % ocupado es suficiente. No copiar automáticamente polígonos entre imágenes, pues la resolución y el contenido pueden cambiar. Los polígonos recuperados de originales corresponden únicamente a su archivo original.

Toda versión nueva debe conservar juntas las familias y escenas, fijar su partición y comprobar la cobertura de faltantes antes de entrenar. La etapa V2 de tres estados con obstáculos sigue pendiente de aprobación final y entrenamiento.

## Oclusiones y geometría

El objetivo es el espacio completo del nivel. Bajo oclusión parcial se conserva su contorno completo, incluida la parte oculta, cuando la geometría pueda establecerse de forma reproducible. Puede respaldarse en las repisas y límites visibles o, en estas ediciones sintéticas emparejadas, en el original orientado y escalado, comprobando que la edición conserva la estructura. No es obligatorio ver cada borde completo. Este es un criterio amodal: el polígono representa el nivel, no solo sus píxeles visibles.

Activar `Occluded` cuando una persona, carro u objeto tape parte de esa zona. Asignar el estado exclusivamente con la evidencia visible de la edición: `suficiente` si ya alcanza el 30 % del ancho completo, `reponer` si ni llenando lo oculto lo alcanzaría, y `no_evaluable` si lo oculto puede cambiar la decisión. La imagen original respalda la geometría; no determina el estado de stock de la edición.

Cuando no existe geometría reproducible ni una referencia verificada, registrar una incidencia y mantener el caso pendiente. No crear un contorno arbitrario ni aceptar la imagen como anotación terminada. Esta excepción no obliga a eliminar todos los casos con bordes ocultos.

## Decisión sobre los cuatro casos del lote 22

Conservar los niveles inferiores de la foto 001 con cajas, 028 con cajas, 050 con carro y 053 con cajas. Se compararon visualmente los contornos con los originales, aplicando la orientación EXIF y la escala a 1086 × 1448. Las repisas y los límites de la estructura coinciden en las zonas comprobables, y el original respalda la parte tapada. Las comparaciones están en `Datos/Registros/CVAT/revisiones/visibilidad_20261019T222744Z/decision_contornos/`.

El usuario autorizó aplicar el criterio para preparar la selección. Los cuatro polígonos quedaron conservados y sus incidencias técnicas se resolvieron, con el motivo registrado en CVAT. El quinto caso, foto 055 nivel 3, pasó a `suficiente` tras sumar el producto visible en ambos extremos. La comprobación final también corrigió otros casos cuyo stock del propio estante ya se veía entre los barrotes del carro: el lote queda con 299 niveles `suficiente` y 9 `no_evaluable`.

La revisión técnica fue completada por Codex y los tres trabajos pasaron a validación del equipo. Este registro conserva el cierre técnico del 19 de octubre; no acredita aprobación humana final ni entrenamiento de V2 con tres estados. La partición vigente está en el [registro por familias y escenas](../../Datos/Registros/Particiones/lider_express_v2_20261019/README.md).

## Respuesta recomendada en producción

Conservar las tres clases por nivel. Si el sistema no consigue una localización fiable para emitir una recomendación, devolver «captura no evaluable; repetir foto», mediante una regla de salida. Esto es una recomendación de comportamiento pendiente de implementar y probar; no se ha añadido una clase nueva ni se afirma que el sistema actual ya detecte todos esos fallos. La ausencia de detecciones no acredita que el stock sea suficiente.

## Referencias

- [DanceTrack, CVPR 2022, sección 3.1](https://openaccess.thecvf.com/content/CVPR2022/papers/Sun_DanceTrack_Multi-Object_Tracking_in_Uniform_Appearance_and_Diverse_Motion_CVPR_2022_paper.pdf): conserva cajas completas bajo oclusión parcial y omite personas totalmente ocultas.
- [COCOA — Semantic Amodal Segmentation](https://arxiv.org/abs/1509.01329): anota la extensión completa de las regiones, incluidas las partes ocultas.

La adopción de estos criterios para espacios de góndola es una decisión de este proyecto, no una norma publicada específica de retail. Un objetivo amodal no garantiza que cualquier nivel totalmente invisible pueda recuperarse a partir de una sola foto.
