# Job 68: niveles superiores

Aplicación solicitada por el usuario el 22 de octubre de 2026 en las fotos 042–082 del [job 68, tarea 28](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/68?frame=41).

Se añadieron **41 superiores**, uno por foto, conservando exactamente los **171 polígonos manuales anteriores**, incluidos IDs, coordenadas, atributos y oclusión. El job queda con **212 polígonos**. Solo se escribieron anotaciones del job 68 mediante creación; no se actualizaron ni eliminaron las existentes, ni se cambió el estado del trabajo.

## Criterio y excepciones

La superficie de apoyo se revisó visualmente en cada foto y se situó **por encima del portaprecio**, excluyendo su franja frontal. No se copió automáticamente el borde superior del polígono de abajo ni se aplicó un grosor fijo al lote.

- **37 superiores abiertos:** altura igual a la mediana de las alturas verticales centrales de los inferiores del mismo tramo, sin redondear. Todas las fotos tenían entre tres y cinco referencias; no se aplicó la excepción de dos referencias del job 67.
- **4 superiores en vitrina, fotos 074–077:** se siguió la cara interior de la cubierta física y los límites interiores de la caja. Se registran las alturas inferiores como referencia, pero la mediana no sustituye ese techo real. El vidrio transparente y sus reflejos no activan por sí solos `Occluded`.
- **Foto 060, frame 59:** la proyección completa sale del borde superior del encuadre. Se conserva su parte visible con `delimitacion=parcial`; el plan guarda también las coordenadas calculadas antes del recorte. Los otros 40 superiores tienen `delimitacion=completa`.

Se marcaron seis superiores como `Occluded` por tiras colgantes, carteles delanteros, una hoja de inventario o el exhibidor de botellas que entra en el margen derecho del tramo de azúcar. El motivo por foto está en el plan. No se cambiaron las marcas de los inferiores manuales.

No se añadieron laterales, tags ni tracks. La operación no aprueba los datos para entrenamiento ni certifica ocupación calibrada. Los productos que exceden la altura convencional no hacen crecer el polígono.

## Evidencias

- [Plan por imagen](plan.json): apoyo, referencias, medianas, cubierta física, recorte, coordenadas y oclusión.
- [Verificación posterior de CVAT](verificacion.json): IDs creados y comprobación exacta de la conservación de las anotaciones manuales.
- [Polígonos nuevos leídos de CVAT](poligonos_creados.json).
- Vistas: azul indica los inferiores manuales conservados; verde, el superior añadido. [042–047](contacto_01.jpg), [048–053](contacto_02.jpg), [054–059](contacto_03.jpg), [060–065](contacto_04.jpg), [066–071](contacto_05.jpg), [072–077](contacto_06.jpg), [078–082](contacto_07.jpg).

Respaldo privado, programas, solicitudes, respuestas y lecturas completas: `.resguardo/superiores_job68_20261022`. Los superiores ya están creados: no volver a cargar el plan como una creación nueva. El trabajo permanece en curso y el entrenamiento sigue deshabilitado.
