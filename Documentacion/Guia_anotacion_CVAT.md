# Guía para marcar niveles en CVAT

> **Documento histórico · criterio V1 de cuatro estados.** Se conserva para interpretar los datos y modelos V1. Para el lote V2, consultar la [guía de Líder Express](Guia_anotacion_lider_express_20261016.md). Para probar fotografías con los modelos publicados, seguir [Usar Walmart Visión](Usar_Walmart_Vision.md). Véase el [índice histórico](Historico.md).

**Versión 1.3 · 14 de octubre de 2026 · Jobs 36, 37 y 38**

## 1. Qué marcar

Usa la etiqueta **Nivel** y dibuja un **polígono de imagen (Shape)**.

Elige los tramos donde se vean los dos límites laterales. Marca **todos sus niveles**, incluidos los vacíos y los tapados. Mantén la misma zona aunque cambien los productos.

Los fragmentos cortados en los extremos de la foto quedan fuera. Si ya tienen dibujos, consérvalos y avisa al equipo. No hace falta marcar módulos, productos ni huecos por separado.

## 2. Cómo dibujar el nivel

Rodea **todo el espacio del nivel donde van los productos**, incluidos los huecos:

- **Abajo:** sigue el borde delantero de la superficie donde se apoyan los productos.
- **Arriba:** sigue el borde inferior de la repisa de encima.
- **A los lados:** sigue los límites interiores del tramo, sin incluir los soportes.

Sigue la inclinación de las repisas. Deja fuera la franja de precios, el frente de la repisa, el suelo y el techo. Mantén los límites aunque haya menos productos o sean más bajos.

Completa un borde tapado solo si puedes ubicarlo con claridad. Si no puedes identificar los límites, no los inventes: deja el caso para revisión.

## 3. Qué estado elegir

Compara el ancho con productos con **todo el ancho disponible entre los soportes del nivel**.

| Estado en CVAT | Cuándo usarlo |
|---|---|
| **vacio** | No se ve ningún producto y puedes comprobar todo el nivel. |
| **baja_disponibilidad** | Hay productos, pero ocupan menos del 30 % del ancho. |
| **suficiente** | Los productos ocupan el 30 % del ancho o más. |
| **no_evaluable** | No puedes decidir el estado porque el contenido está tapado o no se ve con claridad. |
| **pendiente** | Falta revisar el dibujo o resolver una duda con el equipo. |

Imagina el ancho dividido en **10 partes iguales**: menos de 3 partes con producto es baja disponibilidad; 3 o más es suficiente.

Cuenta los productos visibles al fondo y suma el ancho de los grupos separados. Los productos delante y detrás en el mismo lugar cuentan una sola vez. El aire por encima de los envases no cuenta como falta de producto.

Si está cerca del 30 % y tienes dudas, deja **pendiente** y revísalo con un compañero.

## 4. Carros, cajas y otros casos

| Qué ves | Qué hacer |
|---|---|
| Un carro, persona u otro objeto tapa el nivel | Conserva el polígono completo y activa **Occluded**. No cuentes lo tapado como vacío ni como producto. Si puede cambiar el estado, usa **no_evaluable**. |
| Lo visible ya ocupa al menos el 30 % del ancho completo, aunque haya una parte tapada | Elige **suficiente** y mantén **Occluded** activado. |
| Productos en cajas abiertas sobre una repisa | Marca el nivel y cuenta los productos visibles. |
| Cajas cerradas | No supongas su contenido. Usa **no_evaluable** si impiden decidir el estado. |
| Cajas o bidones apilados sin una repisa que puedas delimitar | Deja ese apilamiento fuera. |

Usa siempre el ancho completo del nivel como referencia. Si ves producto en un 20 % y un carro tapa otro 25 %, corresponde **no_evaluable**: lo oculto podría cambiar la decisión.

## 5. Nivel superior sin repisa encima

**Márcalo también.** Para cerrar el polígono por arriba:

1. Usa la línea acordada en un ejemplo de la misma escena y comprueba que encaje en la foto.
2. Si no hay ejemplo, traza una línea por encima de todos los envases, sin cortarlos ni incluir el techo. Pide a un compañero que la revise y guarden el ejemplo.
3. Conserva la línea aunque haya menos productos. No copies la altura del nivel inferior ni coordenadas de otra foto sin comprobarlas.

Si una foto vacía o cortada no permite fijar la línea, busca otra vista de la escena. Si no la hay, deja el caso **pendiente**. La falta de repisa encima no significa **no_evaluable**.

## 6. Antes de guardar y entregar

- Están marcados todos los niveles de los tramos elegidos, incluidos vacíos y tapados.
- Cada polígono sigue las repisas y cada nivel tiene su estado.
- Los vacíos, bajos y casos próximos al 30 % tienen revisión de otro compañero.
- Aplicas las mismas reglas a las fotos **REAL** y **EQ**. Si encuentras una deformación, avisa al equipo.
- **nivel_id, integridad y observacion son opcionales.** Si completas el ID, usa N1, N2, N3 desde abajo hacia arriba por tramo. Tapado y cortado por el borde de la foto son cosas distintas.

Guarda con **Save** durante el trabajo. Antes de entregar, resuelve los casos **pendiente** con el equipo. No hace falta escribir una observación en cada nivel.
