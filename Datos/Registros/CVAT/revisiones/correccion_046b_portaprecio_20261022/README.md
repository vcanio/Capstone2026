# Corrección de la base superior en 046 B

Corrección solicitada por el usuario el 22 de octubre de 2026 para `lider_express_046_B_baja.png`, [tarea 27, trabajo 66, frame 212](https://pcvicen.tailca514b.ts.net/tasks/27/jobs/66?frame=212).

El polígono superior 9346 incluía el portaprecio porque su base procedía de la cara inferior del estante. Se situó sobre la franja del portaprecio, en y=280 px a la izquierda y y=276 px a la derecha, manteniendo las x anteriores. Desde esa base se proyectó hacia arriba la mediana de las cuatro alturas inferiores: **223,14248563568947 px**, sin redondear.

Solo se actualizó ese polígono. La lectura posterior de CVAT confirmó sus coordenadas y la conservación exacta de los otros 450 polígonos del trabajo, incluidos los cuatro inferiores de esta imagen, así como IDs, clases, atributos, tags y tracks. No se modificaron otras imágenes ni se habilitó entrenamiento.

- [Comparación: antes a la izquierda, corregido a la derecha](comparacion.png).
- [Plan y coordenadas](plan.json).
- [Verificación posterior de CVAT](verificacion.json).

Respaldo privado y solicitudes completas: `.resguardo/correccion_046b_portaprecio_20261022`. Esta corrección puntual no certifica el apoyo de las otras proyecciones de la tarea 27.
