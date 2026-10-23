# V3 · límite superior mediante mediana

Decisión del usuario del 22 de octubre de 2026, con su aclaración: cinco niveles era un ejemplo; se adapta al número de niveles de cada caso y **solo se calcula cuando no hay un tope superior claro**. Aplicación verificada en las tareas 27, 28 y 24, con los alcances y excepciones documentados abajo. La prueba inicial del trabajo 67 fue retirada; después el usuario anotó los inferiores y autorizó calcular sus superiores.

## Prioridad del límite real

Si una repisa o cubierta física delimita claramente la parte superior del área útil, se conserva ese límite. No se sustituye por una altura calculada. Un cartel suspendido, los pilares, la altura de los envases o el borde de un respaldo bajo no constituyen por sí solos un techo del espacio de productos.

## Si falta el tope superior claro

1. Mantener las áreas de los niveles inferiores, delimitadas entre estantes y con ancho de los estantes, no de los pilares.
2. Medir las alturas verticales de todos los niveles inferiores disponibles del mismo tramo. En las anotaciones cuadriláteras con perspectiva se usa la distancia vertical en el centro: promedio de las dos coordenadas y inferiores menos promedio de las dos superiores.
3. Usar la **mediana**, sin alternar con la media. Se adapta al número de niveles: si hay 4 niveles en total se usan los 3 inferiores; con 5 se usan 4; con 6 se usan 5. Con una cantidad par se promedian los dos valores centrales ordenados. Ejemplo: 190, 195, 210 y 220 px → **202,5 px**. Se conservan decimales, sin redondear antes de proyectar.
4. Usar como base la superficie de apoyo del nivel superior, **por encima del portaprecio**, y proyectarla hacia arriba esa mediana. La franja del portaprecio queda fuera del área útil. No copiar sin comprobar el borde superior del polígono inmediatamente inferior: puede representar la cara inferior del estante y arrastrar el portaprecio al área superior. En los polígonos con perspectiva se conservan las x de los dos extremos del apoyo y su pendiente; los laterales de la nueva zona son verticales. En una caja horizontal esto equivale a `y_superior = y_apoyo − mediana`.

No ajustar la caja a los productos, al cartel ni a otros elementos que interseque la proyección. Si un envase sobresale del área convencional, no agrandarla. Un nivel superior vacío conserva el mismo procedimiento.

Si no hay tope claro y hay menos de cuatro niveles visibles en total, o no se pueden medir sus referencias con fiabilidad, conservar los contornos para revisión y marcar `Revision_foto`. No inventar alturas. Si una proyección sale del encuadre, recortar el polígono existente al borde de la imagen y marcar `delimitacion=parcial`; conservar en el registro las coordenadas proyectadas sin recortar. No se presenta como un nivel completo ni se reduce la mediana para hacerlo caber. La revisión del apoyo sobre el portaprecio encontró esta excepción en las cuatro imágenes de la familia 010.

## Primera aplicación en CVAT

[Tarea 27](https://pcvicen.tailca514b.ts.net/tasks/27), 276 imágenes y 1.416 polígonos:

- **168** polígonos superiores ajustados por mediana: 32 con tres referencias, 112 con cuatro y 24 con cinco.
- **108** imágenes conservan su tope físico claro; entre ellas están los casos con 3 y 7 niveles.
- **1.140** polígonos inferiores conservados exactamente.
- Mismos IDs, etiquetas, atributos de revisión y marcas de oclusión. No se crearon ni borraron niveles.
- Sin proyecciones fuera de la imagen ni etiquetas adicionales de revisión.

La clasificación abierto/cubierto se revisó visualmente en las 59 fotos originales y las 217 variantes. La comprobación posterior leyó las anotaciones de CVAT y verificó cada coordenada modificada y la conservación del resto. Esto aplica una convención de anotación; no certifica ocupación calibrada ni sustituye la revisión humana pendiente de los datos.

[Comparación visual](../../Datos/Registros/CVAT/revisiones/mediana_superior_t27_20261022/comparacion.png) · [Plan por imagen](../../Datos/Registros/CVAT/revisiones/mediana_superior_t27_20261022/plan.json) · [Verificación](../../Datos/Registros/CVAT/revisiones/mediana_superior_t27_20261022/verificacion.json).

El respaldo íntegro anterior y posterior está en `.resguardo/mediana_superior_t27_20261022T040248Z`. El entrenamiento permanece deshabilitado.

**Corrección puntual posterior, 22 de octubre:** el usuario detectó que `lider_express_046_B_baja.png` incluía el portaprecio en el polígono superior. Se corrigió exclusivamente el polígono 9346 del frame 212, trabajo 66: base sobre el portaprecio (y izquierda 280 px, derecha 276 px) y proyección de 223,14248563568947 px, mediana de sus cuatro niveles inferiores. Se leyeron las anotaciones posteriores de CVAT y se verificó la conservación exacta de todas las demás formas, etiquetas y atributos del trabajo. [Comparación y verificación](../../Datos/Registros/CVAT/revisiones/correccion_046b_portaprecio_20261022/README.md).

## Revisión general del apoyo sobre el portaprecio

El usuario aprobó la corrección de 046 B y pidió extenderla a todos los casos de la tarea 27. Se revisaron las **276 imágenes**, incluidas 59 originales y 217 variantes. El apoyo se identifica en cada fotografía: no se aplica un desplazamiento fijo a todo el lote.

- **161 superiores corregidos**: 33 originales y 128 variantes. Se sitúa la base sobre el portaprecio y se vuelve a proyectar desde ahí la mediana de los inferiores.
- **115 superiores conservados**: 108 con tope físico y 7 abiertos cuyo apoyo ya era correcto, incluido 046 B.
- **1.140 niveles inferiores conservados exactamente**. Se mantienen los 1.416 polígonos y sus IDs.
- **4 superiores de la familia 010 recortados al borde superior de la foto**, con `delimitacion=parcial`. La proyección completa excede el encuadre después de corregir el apoyo. No se inventan coordenadas fuera de la imagen ni se altera la mediana.

El registro por imagen conserva el apoyo, los niveles de referencia, la mediana, las coordenadas antes/después y cualquier recorte. La lectura posterior de CVAT debe coincidir exactamente con ese plan y conservar las demás anotaciones. [Registro y verificación de la revisión general](../../Datos/Registros/CVAT/revisiones/apoyos_sobre_portaprecio_t27_20261022/README.md). Las cifras de la primera aplicación son históricas; esta revisión la complementa y corrige su punto de partida.

## Prueba manual en Líder 2 · trabajo 67

**Prueba retirada:** se eliminaron exclusivamente los 40 polígonos creados por el asistente en las fotos 001–010. El usuario marcará manualmente los niveles inferiores y avisará para que el asistente calcule y marque únicamente el superior, conservando intactas las anotaciones manuales. No iniciar ese cálculo antes del aviso. [Comparaciones, coordenadas y verificación](../../Datos/Registros/CVAT/revisiones/job67_primeras10_20261022/README.md).

**Aplicación posterior autorizada:** el usuario dio ese aviso y pidió los superiores de todo el job 67. Se crearon 41 superiores y se conservaron exactamente los 134 polígonos manuales. En las fotos 031, 032, 037, 038 y 039 autorizó expresamente usar la mediana de los dos inferiores disponibles; esta excepción se limita a esas cinco fotos. Los superiores de las fotos 007, 018 y 039 se recortaron al encuadre con `delimitacion=parcial`. El apoyo se identificó por encima del portaprecio en cada fotografía. [Registro vigente del job 67](../../Datos/Registros/CVAT/revisiones/superiores_job67_20261022/README.md).

**Continuación autorizada en el job 68:** se añadieron sus 41 superiores manteniendo exactamente los 171 polígonos manuales. En 37 fotos se proyectó la mediana desde el apoyo por encima del portaprecio; en las fotos 074–077 se siguió la cara interior de la cubierta física de la vitrina. No se sustituye una cubierta real por una altura calculada. La foto 060 quedó recortada al encuadre y marcada parcial. Todas las fotos del job 68 tenían al menos tres inferiores, sin recurrir a la excepción de dos referencias del job 67. [Registro del job 68](../../Datos/Registros/CVAT/revisiones/superiores_job68_20261022/README.md).

**Continuación autorizada en el job 69:** se añadieron 41 superiores en 40 fotos y se conservaron exactamente los 161 polígonos manuales. La foto 108 contiene dos módulos previamente anotados: cada superior usa únicamente las cuatro referencias de su módulo. Se proyectaron 38 medianas y se respetó el techo físico de las vitrinas en las fotos 115–117. Las fotos 092, 093, 094 y 111 se recortaron al encuadre y quedaron parciales. Todos los módulos tenían al menos tres referencias. [Registro del job 69](../../Datos/Registros/CVAT/revisiones/superiores_job69_20261022/README.md).

## Consistencia en la tarea 24: visibilidad limitada

El usuario pidió aplicar el mismo criterio a sus 60 imágenes. Se corrigieron **36 superiores abiertos** mediante la mediana de sus inferiores, desde el apoyo revisado sobre el portaprecio, y se conservaron exactamente **24 superiores con techo físico claro**. Los **248 polígonos inferiores**, los **308 IDs** y todas las marcas de oclusión permanecen iguales. El superior de `lider_express_010_D_persona.png` (frame 10) se recortó al encuadre y quedó parcial; los otros 59 superiores tienen delimitación completa. Los inferiores conservan su delimitación pendiente y el lote sigue sin aprobación para entrenar. [Plan, comparaciones y verificación de la tarea 24](../../Datos/Registros/CVAT/revisiones/superiores_t24_20261022/README.md).
