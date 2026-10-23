# Criterio V3 · Localización de niveles

Revisión del 21 de octubre de 2026: se conserva el área útil del nivel. Se descarta el ensayo de etiquetar solo el frente de la repisa porque no resuelve el límite superior abierto y agrega una reconstrucción innecesaria. Proyecto en preparación; todavía no representa un modelo entrenado ni una ocupación calibrada.

## Objetivo

YOLO aprende una sola clase geométrica: **Nivel**, que representa el área útil donde pueden existir productos y huecos. La estimación de ocupación se ejecuta después dentro de esa región. La reposición se obtiene mediante una regla sobre una medición validada, no mediante las clases `reponer` o `suficiente` de YOLO. Separar localización y estado no exige reemplazar el área por el portaprecios.

**Decisión posterior del usuario, 22 de octubre de 2026, para la tarea 27 de Líder Express:** se descartó el ensayo de añadir todos los niveles parciales. Se retiraron sus 2.135 polígonos y 14 etiquetas de revisión; se conservaron intactos los 1.416 polígonos anteriores. El usuario prioriza los niveles completos para ocupación y alertas y no quiere continuar la anotación exhaustiva de incompletos en ese lote. No volver a cargar esta prueba ni añadir parciales automáticamente sin una nueva petición. [Reversión verificada](../../Datos/Registros/CVAT/revisiones/parciales_lider_express_t27_20261022/reversion.json). Esta decisión no implementa por sí sola un filtro de completitud en la inferencia ni modifica las anotaciones de otros lotes.

## Cómo delimitar

Marca un polígono por nivel que incluya el área útil completa, tanto productos como huecos. Sigue la perspectiva: apoyo abajo, cara inferior de la repisa inmediatamente superior arriba y límites interiores a los lados. Excluye portaprecios, postes, suelo, carteles y góndolas del fondo. Las barandas que atraviesan la zona se excluyen de la señal de ocupación en el procesamiento; su presencia no convierte el polígono en una banda frontal. No ajustes el contorno a cada envase ni elimines los huecos vacíos.

**Base sobre el portaprecio, nunca debajo.** El borde inferior del área útil se coloca en la superficie de apoyo, inmediatamente por encima de la franja del portaprecio. El portaprecio y el espesor frontal del estante quedan fuera. El borde superior del nivel de abajo puede coincidir con la cara inferior del estante: por eso no sirve automáticamente como base del nivel de arriba. Identifica el apoyo en la imagen antes de calcular o copiar coordenadas. Esta regla se mantiene en originales y variantes llenas, vacías o con pocos productos; no se aplica un desplazamiento fijo a todas las fotos.

**El nivel superior se anota también cuando está completamente vacío.** Vaciarlo no elimina el nivel ni cambia su región útil. No agregues un nivel por un cartel o panel que no tenga una superficie de apoyo asociada.

## Límite superior de un nivel abierto

Hay dos asuntos diferentes: que el modelo reconozca un nivel vacío y que su altura de anotación sea consistente. Cambiar el objetivo al frente de la repisa no resuelve ninguno por sí solo.

En pares lleno/vacío con la misma cámara y estructura, **el polígono debe conservar su geometría al quitar productos**, incluido su límite superior. Revisar primero la anotación del original; no copiar sin comprobar una anotación defectuosa. Si una edición generativa modifica perspectiva o dimensiones, revisar y ajustar las coordenadas por geometría, nunca por las nuevas tapas de los envases.

**Regla acordada el 22 de octubre de 2026, con corrección explícita del apoyo:** si hay un tope físico superior claro, se conserva. Si falta, la altura del nivel superior es la **mediana de las alturas de los niveles inferiores disponibles del mismo tramo**, adaptada a su cantidad; cinco niveles era un ejemplo. La proyección comienza en la superficie de apoyo **sobre el portaprecio**, nunca en el borde inferior de esa franja. En polígonos con perspectiva se miden alturas en el centro y se conservan las x y la pendiente del apoyo identificado. No se ajusta a los envases ni a un cartel que interseque la zona. [Regla completa y aplicación verificada a la tarea 27](Regla_nivel_superior_mediana_V3.md).

Antes de guardar, comprobar visualmente que el portaprecio queda fuera, que la altura proyectada coincide con la mediana sin redondear y que las variantes mantienen el mismo criterio estructural. Una base ya correcta se conserva. Al corregir un superior, no mover los niveles inferiores ni alterar sus IDs o atributos. Leer después las coordenadas de CVAT para verificar el resultado y registrar por imagen el apoyo utilizado.

Si falta un tope claro y hay menos de cuatro niveles visibles en total o sus referencias no se pueden medir con fiabilidad, marcar para revisión en vez de inventar el límite. No emitir una ocupación total a partir de una región sin definir. Una vez definida la región y validado el cálculo, un nivel completamente visible y vacío puede medir 0 %; la ausencia de detección por sí sola no significa 0 %. Se ajustó la tarea 27. La prueba de anotación de las primeras diez imágenes del trabajo 67 de la tarea 28 fue retirada a petición del usuario. En ese trabajo el usuario marcará manualmente los niveles inferiores; el asistente calculará y marcará únicamente el último nivel cuando el usuario avise. No modificar los niveles inferiores manuales al calcular el superior.

Cada polígono tiene el atributo administrativo `delimitacion`:

| Valor | Significado |
|---|---|
| `pendiente` | Borrador copiado de V2 o caso aún no revisado con V3. |
| `completa` | Se identifica el perímetro completo del nivel dentro de la imagen. |
| `parcial` | Solo se identifica una parte; el perímetro o alguno de sus extremos no es recuperable con fiabilidad. |

Este atributo no se exporta como clase de YOLO.

## Si el nivel no se ve completo

1. **Objeto delante, pero límites recuperables:** conserva el contorno completo solo si existen referencias claras para ubicarlo y activa **Occluded**. La geometría puede ser válida para localizar el nivel; el contenido oculto sigue siendo desconocido.
2. **Nivel fuera del encuadre o con límites inciertos:** delimita únicamente la parte identificable, recortada al borde de la imagen cuando corresponda, y asigna `parcial`. No extrapoles un ancho inventado. Si además hay un objeto tapándolo, activa **Occluded**.
3. **No puedes ubicar el nivel con fiabilidad:** no inventes un polígono. Añade una etiqueta de imagen **Revision_foto** con el motivo `nivel_no_delimitable`. Usa una incidencia de CVAT para señalar el caso si hace falta explicar dónde está.

**Un nivel parcial, no localizado o con contenido oculto no da 0 % de ocupación.** Debe comunicarse como `sin_medicion` / `no_evaluable`, con una sugerencia de repetir la foto cuando sea necesario. Una medición de la zona visible, si se desarrolla, debe identificarse como parcial y no extrapolarse al nivel completo.

No detectar ningún nivel tampoco demuestra que la góndola esté vacía ni suficientemente abastecida.

## Revisión de fotografías

**Revision_foto** es una etiqueta de tipo **Tag**, para la imagen completa, con atributo `motivo`: `nivel_no_delimitable`, `recorte`, `oclusion`, `desenfoque` u `otro`. No es una segunda clase de segmentación ni una etiqueta de disponibilidad. Solo los polígonos `Nivel` constituyen la clase de entrenamiento.

Las marcas manuales `delimitacion`, **Occluded** y **Revision_foto** sirven para revisar y evaluar los datos. Un modelo YOLO de una clase no predice esos atributos por sí mismo: el sistema de inferencia tendrá que incorporar una comprobación de calidad y visibilidad antes de emitir ocupación total.

## Borradores reutilizados de V2

Las imágenes y polígonos se copian de los dos lotes del proyecto V2. Se conservan las coordenadas, la orientación de la imagen y la marca **Occluded**. Los estados `reponer`, `suficiente` y `no_evaluable` quedan en la procedencia local; no se transfieren como clases ni se interpretan como revisión aprobada de V3.

Todos los polígonos copiados comienzan en `delimitacion=pendiente`. **Los 1.520 polígonos heredados conservan el tipo de geometría que buscamos: el área del nivel. No requieren redibujarse todos como bandas frontales.** Hay que revisarlos, especialmente el límite superior abierto y los niveles vacíos, antes de aprobarlos. No se han alterado las anotaciones de V2. Las fotografías nuevas se incorporarán como otro lote dentro de este proyecto, con su procedencia y agrupación por escenas.

La tarea 25 conserva un ensayo de cinco bandas frontales que queda **descartado como criterio y excluido del entrenamiento**. Su imagen sintética de nivel superior vacío puede reutilizarse después de revisar la edición y anotar las áreas completas; esos cinco polígonos no deben exportarse como `Nivel`.

## Casos para romper la dependencia de los productos

- Pares de una misma estructura con repisa superior llena y completamente vacía, manteniendo visibles sus soportes.
- Repisa superior con pocos productos, envases bajos o altos y huecos en los extremos.
- Niveles intermedios vacíos y góndolas completamente vacías, con todas sus áreas de nivel anotadas.
- Góndolas de otras estructuras y vistas, incluidos soportes parcialmente ocultos. No agregar niveles donde solo haya carteles o paneles sin repisa.

Las variantes sintéticas se identifican como tales y se revisan visualmente antes de anotar. No se reutilizan polígonos automáticamente si la edición modifica geometría, resolución o perspectiva. Se generan únicamente desde familias de entrenamiento y conservan su familia, escena y partición. La evaluación necesita fotografías reales de escenas separadas con estos casos; un ejemplo sintético no demuestra que el modelo haya aprendido.

## Antes de entrenar o medir

- Conservar la separación existente por familias y escenas; la reserva final no se usa para entrenar ni ajustar el algoritmo.
- No exportar automáticamente los borradores pendientes.
- No eliminar un nivel parcial o no delimitable y utilizar el resto de esa foto como si fuera un negativo completamente anotado. En el primer ensayo, apartar la foto hasta resolverla o definir un tratamiento explícito de regiones ignoradas.
- Los niveles ocluidos con perímetro completo pueden servir para aprender geometría tras revisión. Su ocupación total permanece no evaluable hasta que exista evidencia suficiente o un tratamiento de oclusiones validado.
- Definir y validar por separado la medición de ancho, área o combinación y su umbral de reposición. El 30 % del ancho de V2 no equivale al 30 % de la combinación 70/30.
- Adaptar el exportador, las validaciones y la interfaz a una sola clase geométrica, excluyendo pendientes y el ensayo de bandas frontales, antes de iniciar entrenamiento desde el panel. El cálculo de bordes utiliza el área del nivel y suprime la estructura dentro de ella. La preparación de este proyecto no habilita por sí sola ese flujo.

## Referencias de la herramienta

- [CVAT: proyectos y etiquetas compartidas](https://docs.cvat.ai/docs/workspace/projects/).
- [CVAT: modo Shape y propiedad Occluded](https://docs.cvat.ai/docs/annotation/tools/shape-mode-advanced/).
- [CVAT: guía para anotadores](https://docs.cvat.ai/docs/manual/advanced/specification/).

Las reglas sobre perímetros parciales y medición de ocupación son decisiones de este proyecto; no una norma de CVAT sobre góndolas.

## Aplicación autorizada al job 67 de Líder 2

El 22 de octubre de 2026 el usuario avisó que había terminado los inferiores y pidió marcar los superiores del [job 67, tarea 28](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/67). Se añadieron 41 superiores sobre el apoyo situado por encima del portaprecio, con la mediana de los inferiores de cada foto. Los 134 polígonos manuales existentes conservaron exactamente sus IDs, coordenadas, atributos y oclusión.

**Excepción puntual autorizada por el usuario:** en las fotos 031, 032, 037, 038 y 039 (frames 30, 31, 36, 37 y 38) se usa la mediana de los dos inferiores disponibles. La autorización no cambia el mínimo por defecto de otros casos. Con dos referencias, la mediana es el promedio de los dos valores ordenados; no se sustituye por una altura arbitraria.

Los superiores de las fotos 007, 018 y 039 se recortan al encuadre y llevan `delimitacion=parcial`, porque la proyección completa excede el borde de la imagen. Los demás 38 son completos dentro del encuadre. El registro conserva apoyos, referencias, medianas, proyecciones completas y coordenadas visibles. [Plan, comparaciones y verificación](../../Datos/Registros/CVAT/revisiones/superiores_job67_20261022/README.md). No volver a crear esos superiores ni modificar los inferiores manuales al revisarlos.

## Aplicación posterior a la tarea 24

El 22 de octubre de 2026, a petición del usuario, se revisaron sus 60 superiores para mantener este criterio: **36 abiertos corregidos por mediana** desde el apoyo sobre el portaprecio y **24 techos físicos conservados**. Permanecen exactamente iguales los **248 inferiores** y todas las marcas Occluded; se mantienen los 308 IDs. Los superiores tienen delimitación revisada: 59 completa y 1 parcial, `lider_express_010_D_persona.png` (frame 10), recortado al encuadre. Los inferiores siguen pendientes y no se habilita entrenamiento. [Registro vigente de la tarea 24](../../Datos/Registros/CVAT/revisiones/superiores_t24_20261022/README.md).
