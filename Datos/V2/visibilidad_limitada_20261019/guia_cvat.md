# Visibilidad limitada: lote único de 60 variantes IA

24 carros con plástico azul, 24 personas y 12 casos de cajas en el suelo. Iluminación y desenfoque quedan fuera por decisión del usuario. 60 ediciones de 59 familias de Líder Express. La familia 001 tiene dos ediciones desde el mismo original y deben permanecer juntas.

Las 30 imágenes de la primera tanda fueron aprobadas por el usuario; las 30 de la segunda requieren revisión independiente. La producción por tandas queda como procedencia, no como tareas separadas. Cada polígono y estado requiere anotación y revisión propias.

## Anotar todos los niveles delimitables

Un polígono `Nivel` por nivel del tramo cuyos límites puedan localizarse. Delimitar el espacio completo de productos, incluidos los huecos, siguiendo la perspectiva. Dejar fuera las franjas de precios, soportes y suelo. No ajustar el contorno al objeto visible ni contar compras del carro, productos sostenidos por personas o mercancía dentro de cajas como ocupación del nivel.

Se importaron como borrador 308 polígonos de los 59 originales de la tarea 19, escalados de 3000 × 4000 a 1086 × 1448. No se copiaron sus estados. Revisar y ajustar cada contorno sobre la edición: la importación no acredita su validez. Se incluyen todos los niveles del original, también los inferiores; la foto 050 tiene cinco.

Conservar el polígono completo bajo oclusión parcial cuando su geometría pueda establecerse de forma reproducible. No es obligatorio ver cada borde: pueden utilizarse las referencias de la góndola o, en estas ediciones sintéticas emparejadas, el original verificado, orientado y escalado, siempre que la estructura se conserve. El contorno incluye la parte oculta; este es un criterio amodal. Si no existe una referencia geométrica fiable, registrar una incidencia y mantener el caso pendiente sin inventar el polígono. Para el nivel superior sin repisa encima, acordar su límite con otro integrante según la guía del lote fuente.

También se revisa el último nivel, aunque esté tapado. Si su geometría tiene respaldo fiable, se dibuja completo y se activa Occluded. Se conservaron los niveles inferiores de 001 con cajas, 028, 050 y 053 tras compararlos con sus originales y se resolvieron sus incidencias técnicas. Un ejemplo con un solo contorno no representa la anotación completa de una imagen. El original respalda la geometría, pero el estado se decide únicamente con lo visible en la edición.

## Estado real de cada nivel

- `reponer`: puede determinarse que la ocupación es menor del 30 % del ancho completo.
- `suficiente`: puede determinarse que alcanza o supera el 30 %. Si ya se ve un 40 % ocupado, sigue siendo suficiente aunque haya oclusión.
- `no_evaluable`: la parte oculta podría cambiar la decisión entre los dos estados anteriores.

El producto visible al fondo del propio nivel cuenta. Una oclusión por sí sola no determina `no_evaluable`; los casos evaluables pueden conservarse como controles. Revisar Occluded y activarlo cuando corresponda: el borrador no evalúa automáticamente la oclusión.

Los polígonos se importaron inicialmente con estado vacío mediante la opción nativa `__undefined__`, que CVAT muestra en blanco. Esto indica trabajo pendiente, no una cuarta clase. Tras aplicar el criterio y revisar el producto visible del propio estante entre barrotes, a los lados y al fondo, los 308 niveles tienen estado: 299 `suficiente`, 9 `no_evaluable` y 0 `reponer`. Hay 176 ocluidos y ninguna incidencia técnica abierta. La foto 055, nivel 3, quedó `suficiente` por la suma del producto visible de ambos extremos.

La aplicación técnica del criterio quedó completada por Codex a solicitud del usuario y los trabajos pasaron a validación del equipo. Este cierre técnico no certifica la validación humana independiente. Los estados existentes de la tarea 19 se conservaron; el valor predeterminado del proyecto tampoco cambió, por lo que los polígonos nuevos dibujados a mano también requieren selección expresa del estado. La selección y congelación de entrenamiento, validación y reserva se hace después, por familias y escenas.

## Revisión y cierre

Una persona distinta del editor debe revisar cada imagen y luego sus propios polígonos y estados. Mantener pendientes las dudas y resolver incidencias antes de completar los trabajos. Registrar revisor y observaciones en la planilla.

Al cerrar, contar imágenes aceptadas/descartadas y niveles de cada estado por tipo de edición. No existe cuota de polígonos ni de niveles `no_evaluable`. No habilitar entrenamiento con etiquetas provisionales.

## Procedencia y partición

El inventario local relaciona archivo, original, familia, hashes y tarea. Partición `sin_asignar`. Cada edición heredará la partición de su original y escena cuando se defina. Conservar juntas las dos ediciones de la familia 001. Revisar los grupos candidatos 046–048, 049–050, 051–054 y 055–056 y mantenerlos completos en una misma partición. La distribución en tres trabajos de veinte imágenes no representa entrenamiento, validación o evaluación.
