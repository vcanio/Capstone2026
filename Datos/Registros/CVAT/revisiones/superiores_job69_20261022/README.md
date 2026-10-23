# Job 69: niveles superiores

Aplicación solicitada por el usuario el 22 de octubre de 2026 en las fotos 083–122 del [job 69, tarea 28](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/69?frame=82).

Se añadieron **41 superiores en 40 fotos**, conservando exactamente los **161 polígonos manuales anteriores**, incluidos IDs, coordenadas, atributos y oclusión. El job queda con **202 polígonos**. La foto 108 tiene dos módulos anotados y recibe dos superiores independientes. Solo se crearon anotaciones en el job 69 y su estado permanece en curso.

## Criterio y casos especiales

El apoyo se identificó visualmente en cada foto, **sobre el portaprecio**, excluyendo la franja frontal, el espesor del estante y las barandas. No se aplicó un grosor fijo al lote ni se copió automáticamente el borde del polígono inferior.

- **38 superiores abiertos:** se proyectó la mediana de las alturas verticales centrales de los inferiores del mismo módulo, sin redondear. Todos los módulos tenían entre tres y seis referencias; no se usó la excepción de dos referencias del job 67.
- **Foto 108, frame 107:** se separaron las cuatro referencias izquierdas y las cuatro derechas. Medianas respectivas: 515,497553574125 px y 520,0245518762822 px. No se mezclan niveles de módulos diferentes aunque aparezcan en una misma foto.
- **Fotos 115–117, frames 114–116:** se respetaron los límites interiores y la cara interior del techo físico de la vitrina. La mediana queda registrada como referencia, pero no sustituye esa cubierta. El vidrio transparente no activa por sí solo `Occluded`.
- **Fotos 092, 093, 094 y 111, frames 91, 92, 93 y 110:** la proyección sale por arriba del encuadre. Se recortó y se marcó `delimitacion=parcial`, conservando las coordenadas completas en el plan. Los otros 37 superiores tienen delimitación completa.

Se marcaron cinco superiores como `Occluded`: fotos 086, 090 y 091 por vasos colgantes; foto 109 por la tira de etiquetas del margen derecho; foto 110 por la hoja blanca delantera. Los respaldos y carteles situados detrás de los productos no se tomaron como techo ni como oclusión delantera. Se conservaron todas las marcas de los inferiores manuales.

## Verificación y evidencias

La lectura posterior de CVAT coincidió exactamente con las 41 geometrías y sus atributos. Los 161 polígonos manuales tienen el mismo contenido antes y después, comprobado individualmente y con hashes iguales. Se conservaron tags, tracks y el estado del trabajo. No hubo solicitudes de escritura en otros jobs; el registro recoge cambios concurrentes observados en el job 68 sin modificarlos.

- [Plan por módulo](plan.json): apoyo, referencias, mediana, techo físico, recorte, coordenadas y oclusión.
- [Verificación posterior](verificacion.json): IDs creados y comprobación de conservación.
- [Polígonos nuevos leídos de CVAT](poligonos_creados.json).
- Vistas: azul indica los inferiores manuales conservados; verde, los superiores añadidos. [083–088](contacto_01.jpg), [089–094](contacto_02.jpg), [095–100](contacto_03.jpg), [101–106](contacto_04.jpg), [107–112](contacto_05.jpg), [113–118](contacto_06.jpg), [119–122](contacto_07.jpg).

Respaldo privado, programas, solicitud, respuesta y lecturas completas: `.resguardo/superiores_job69_20261022`. **Los superiores ya están creados: no volver a cargar el plan como creación nueva.** El entrenamiento permanece deshabilitado y la revisión humana pendiente.
