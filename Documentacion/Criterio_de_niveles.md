# Criterio de anotación de niveles · V3

Se anota un polígono por nivel del mismo tramo: el área útil completa, incluidos productos y huecos. La clase es Nivel; la reposición se calcula después. La máscara no se ajusta a las tapas de los envases ni a una caja rectangular.

## Apoyo y límites

La base va en la superficie de apoyo **sobre el portaprecio**, excluyendo la franja de precios y el espesor frontal del estante. No copiar automáticamente el borde superior del nivel inferior: puede ser la cara inferior del estante. Identificar el apoyo visualmente en cada imagen, sin restar un grosor fijo ni usar carteles, barandas, reflejos o productos como referencia.

Los laterales siguen el interior del módulo y el superior respeta la cara inferior de la repisa o cubierta física clara. Un cartel sin apoyo no crea un nivel. Los niveles vacíos conservan el mismo objetivo geométrico que los llenos.

## Superior abierto

Si no hay tope físico claro, proyectar desde el apoyo la **mediana de las alturas de los niveles inferiores medibles del mismo tramo**, manteniendo decimales y perspectiva. Habitualmente se requieren al menos tres inferiores; las excepciones autorizadas con dos referencias fueron específicas y no se generalizan. Los módulos distintos usan sus propias referencias.

Si la proyección sale de la imagen, recortar el polígono existente al encuadre y marcar delimitacion=parcial; no inventar área fuera de la foto ni presentarlo como completo. Conservar el techo físico cuando existe. El mismo criterio se aplica a originales y variantes llenas/vacías; si cambia la geometría de una variante sintética, debe revisarse.

## Visibilidad, revisión y conservación

Delimitación y oclusión son atributos de anotación, no clases de YOLO. Un objeto que tapa el contenido no permite inferir cuánto stock existe detrás. Un nivel parcial, desconocido o no detectado no significa 0 % de ocupación.

Las correcciones de superiores preservan inferiores, IDs y atributos ajenos; se respaldan y se verifican mediante lectura posterior de coordenadas. Hubo correcciones asistidas de geometría, conservadas en los recibos. R254 permanece excluida y las decisiones particulares sobre superiores no se generalizan a otras fotos.

La mediana define el objetivo de anotación: **la app no la impone en inferencia**. El modelo puede omitir o delimitar mal un nivel. Revisar contornos y visibilidad antes de interpretar Línea A.

[Criterio original y decisiones fechadas](https://github.com/vcanio/Capstone2026/blob/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Documentacion/Desarrollo/Criterio_V3_niveles.md) · [Regla original de superiores](https://github.com/vcanio/Capstone2026/blob/2467a62974c3f5b28b0e4548bd4c0527230cc8cd/Documentacion/Desarrollo/Regla_nivel_superior_mediana_V3.md) · [Metodología](Metodologia_desarrollo_y_revision.md).
