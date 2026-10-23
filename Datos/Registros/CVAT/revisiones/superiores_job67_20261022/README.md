# Job 67: superiores sobre los inferiores manuales

Aplicación solicitada por el usuario el 22 de octubre de 2026 en las 41 fotos del [job 67, tarea 28](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/67?frame=0).

Se añadieron **41 polígonos superiores**, uno por foto. Los **134 polígonos manuales anteriores se conservaron exactamente**, incluidos IDs, coordenadas, atributos y oclusión. El job tiene **175 polígonos**. Solo se enviaron solicitudes de creación al job 67; no se escribieron los trabajos 68 ni 69, ni se cambió el estado del trabajo.

## Criterio aplicado

El apoyo se identificó visualmente en cada imagen **sobre el portaprecio**, excluyendo su franja frontal. Se usaron las x del borde superior del nivel manual inmediatamente inferior para conservar el tramo objetivo y se corrigieron las y del apoyo según la estructura visible; no se copió automáticamente la cara inferior del estante. Desde ese apoyo se proyectó hacia arriba la mediana de las alturas verticales centrales de los inferiores de esa misma foto, sin redondear. Ninguna de estas 41 fotos tiene una cubierta física que cierre claramente la región superior. Carteles del fondo, postes y envases no se usaron como techo.

| Referencias inferiores por foto | Fotos |
|---|---:|
| 2, con autorización explícita | 5 |
| 3 | 22 |
| 4 | 12 |
| 5 | 2 |

El usuario autorizó expresamente la mediana de **dos** inferiores en las fotos **031, 032, 037, 038 y 039**, después de consultar la excepción al mínimo documentado. Esta autorización queda limitada a esas cinco fotos. No se tomaron referencias de otra imagen ni se inventaron alturas.

**38 superiores completos y 3 parciales:** las proyecciones de las fotos **007, 018 y 039** exceden el borde superior del encuadre. Sus polígonos visibles se recortaron a la foto y llevan `delimitacion=parcial`. El plan conserva las coordenadas calculadas antes del recorte y la mediana completa; no se alteró la altura para hacerlas caber.

Se marcaron 14 superiores como `Occluded` por tiras de vasos, banderines, carteles delanteros o una hoja de papel que tapan parte de la nueva región. La oclusión no se activó por el mero apilamiento de productos, la baranda del estante o la cartelería del fondo. Las marcas de oclusión de los inferiores manuales no se modificaron. El motivo concreto de cada superior está en el plan.

No se añadieron laterales, etiquetas de imagen ni tracks. `completa` describe el perímetro visible de la región convencional; no aprueba los datos para entrenamiento ni certifica ocupación calibrada.

## Evidencias

- [Plan por foto](plan.json): apoyo, IDs de referencia, alturas, mediana, coordenadas completas y recortadas, oclusión y autorización de dos referencias.
- [Lectura posterior verificada](verificacion.json): IDs nuevos, conservación de los 134 manuales y hashes coincidentes antes/después.
- [Polígonos nuevos leídos de CVAT](poligonos_creados.json).
- Vistas: azul representa los inferiores manuales conservados; verde, el superior nuevo. [001–006](contacto_01.jpg), [007–012](contacto_02.jpg), [013–018](contacto_03.jpg), [019–024](contacto_04.jpg), [025–030](contacto_05.jpg), [031–036](contacto_06.jpg), [037–041](contacto_07.jpg).

La comprobación exacta se hizo tras crear los superiores. Durante la operación se observaron cambios concurrentes en el job 68; se leyeron para el inventario, sin escribir ese trabajo. Los registros no atribuyen esos cambios a esta intervención.

Respaldo privado, solicitudes, respuesta y lecturas completas: `.resguardo/superiores_job67_20261022`. Los superiores ya están creados: no volver a cargar el plan como una creación nueva. El entrenamiento sigue deshabilitado.
