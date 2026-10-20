# Defensa del criterio de disponibilidad visual

Documento breve para explicar el proyecto · 15 de octubre de 2026.

## 1. ¿Qué queremos resolver?

Queremos identificar niveles de góndola vacíos o con poca presencia de productos a partir de fotografías, para apoyar la revisión de posibles necesidades de reposición.

El proyecto estima **disponibilidad visual**. No calcula el inventario exacto, las unidades ocultas ni la disponibilidad de cada marca o producto.

## 2. ¿Cuál es nuestro criterio?

Analizamos cada nivel entre sus límites laterales y comparamos el ancho que tiene producto con el ancho completo disponible.

| Estado | Criterio |
|---|---|
| **Vacío** | No se ve producto del propio nivel y se puede comprobar todo su contenido. |
| **Baja disponibilidad** | Hay producto, pero ocupa menos del 30 % del ancho completo. |
| **Suficiente** | El producto ocupa el 30 % del ancho completo o más. |
| **No evaluable** | La visibilidad no permite decidir el estado. |

Contamos el producto visible al fondo del propio nivel. No contamos mercancía de un tramo vecino que aparezca por perspectiva. Si hay una ocultación que podría cambiar la decisión, usamos no evaluable.

“Suficiente” significa que supera nuestro umbral visual; no garantiza stock suficiente para la demanda ni presencia de todos los productos.

## 3. ¿Por qué lo hacemos así?

- **Por nivel:** permite ubicar la zona que requiere revisión dentro de la góndola.
- **Por ancho ocupado:** evita considerar el aire sobre botellas o envases bajos como falta de producto. Es una simplificación que puede perder información sobre profundidad y apilamiento.
- **Con una guía común:** permite que todos anoten con las mismas reglas y que los ejemplos de entrenamiento sean coherentes.
- **Con un estado no evaluable:** evita tomar una zona tapada como evidencia de vacío.

Estas son decisiones de diseño del equipo, que debemos comprobar con datos reales.

## 4. ¿Qué base científica tenemos?

**Jha y colaboradores (2022)** explican que el concepto de estante vacío puede resultar ambiguo y establecen reglas explícitas de anotación. Su trabajo respalda la necesidad de definir qué se marca y mantener un criterio consistente. Sus etiquetas son de huecos; no equivalen a nuestros estados por nivel. [Artículo, sección 5](https://arxiv.org/html/2205.13060v2#S5).

**Šikić y colaboradores (2024)** distinguen espacios completamente vacíos de espacios vacíos al frente con productos detrás. Esto respalda aclarar cómo tratamos el producto del fondo y qué entendemos por disponibilidad. [Artículo](https://pmc.ncbi.nlm.nih.gov/articles/PMC10819825/).

**Estas fuentes apoyan el enfoque general y la definición clara de las etiquetas. No demuestran que el 30 % sea el umbral correcto para nuestro proyecto.**

## 5. ¿Por qué elegimos el 30 %?

Lo adoptamos como una regla inicial, sencilla y común para separar presencia reducida de producto del resto de los niveles con producto.

**Es un umbral provisional del equipo. No lo presentamos como una norma de Walmart ni como un valor científicamente validado.** Para justificar su utilidad necesitamos contrastarlo con personas que conozcan la reposición y con fotos reales.

La validación propuesta es revisar la ocupación y la necesidad de reposición de manera independiente, y comparar alternativas como 20 %, 30 % y 40 %. Si el resultado favorece otro valor, habrá que actualizar el criterio y las etiquetas correspondientes.

## 6. ¿Cómo sabemos si funciona?

Debemos comprobar dos cosas distintas:

1. **El criterio:** que las personas lo apliquen de forma consistente y que los estados sean útiles para la revisión de reposición.
2. **El modelo:** que encuentre los niveles y prediga correctamente sus estados en escenas que no usó para entrenar.

Actualmente las cinco fotos de validación no contienen niveles vacíos ni bajos. Por eso todavía falta evaluar esos casos en escenas nuevas. Que el modelo acierte fotos de entrenamiento no demuestra que funcione igual en otras góndolas.

## 7. Explicación breve para presentar

> Nuestro proyecto identifica disponibilidad visual por nivel de góndola. Elegimos trabajar por nivel para ubicar posibles faltantes y usamos el ancho ocupado como una regla común para anotar. Distinguimos vacío, baja disponibilidad, suficiente y no evaluable. La literatura respalda definir claramente los espacios vacíos y considerar si hay productos al fondo. El 30 % es un umbral inicial del equipo, pendiente de validación con casos reales y conocimiento de reposición. Nuestro objetivo es apoyar la revisión visual; no medir inventario exacto.

## Documentos del proyecto

- [Guía de anotación: cómo aplicar el criterio](Guia_anotacion_CVAT.md).
- [Guía de mejora del modelo](Guia_mejora_modelo_paso_a_paso.md).
- Investigación del enfoque y sus límites (archivo local histórico, fuera de la distribución).
