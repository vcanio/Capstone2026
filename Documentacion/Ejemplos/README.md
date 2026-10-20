# Ejemplo de nivel parcialmente oculto

`nivel_ocluido_carro_050.png` es una ilustración didáctica generada con ImageGen integrado a partir de `Datos/Pendientes/visibilidad_limitada_20261019/imagenes/lider_express_050_E_carro.png`. No es una anotación validada ni modifica la imagen del lote o CVAT. El prompt está en `nivel_ocluido_carro_050_prompt.txt`.

El contorno señala el espacio completo del penúltimo nivel, siguiendo las repisas y los límites interiores del tramo. La parte oculta se completa solo cuando su posición puede localizarse con claridad. En CVAT el polígono conserva ese espacio y se activa `Occluded`.

El estado se decide aparte por lo visible en la edición: `suficiente` si ya se observa al menos el 30 % ocupado; `reponer` si incluso con toda la zona oculta llena no alcanzaría el 30 %; `no_evaluable` si lo oculto puede cambiar la decisión. La ilustración no asigna un estado definitivo a la foto. Si no pueden localizarse los límites, se deja el caso para revisión sin inventar el polígono.

La imagen muestra solo el penúltimo nivel como ejemplo de contorno. No es una anotación completa: también debe revisarse el último nivel. En la foto 050, el carro y las compras ocultan el borde inferior del último nivel; si no puede localizarse con claridad, se registra una incidencia para revisar su delimitación. No se omite silenciosamente ni se inventa el contorno. El lote de 60 imágenes está reunido en la tarea 22 del proyecto 7.
