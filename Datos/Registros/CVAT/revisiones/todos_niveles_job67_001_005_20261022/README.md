> **Prueba histórica retirada / vista previa fuera del dataset.** El 23/10/2026 sus imágenes de revisión se trasladaron al archivo local `.resguardo/orden_registros_20261023/vistas_pruebas_retiradas/todos_niveles_job67_001_005_20261022/`. Los planes, coordenadas, verificaciones y reversiones permanecen aquí. Las cifras e instrucciones siguientes describen aquella prueba, no el estado vigente.

# Primeras cinco fotos: niveles centrales y laterales

**REGISTRO HISTÓRICO.** La lectura anterior a la nueva intervención de superiores del job 67 ya no contenía estos polígonos del asistente. El estado vigente se documenta en la [aplicación de 41 superiores sobre 134 polígonos manuales](../superiores_job67_20261022/README.md); no volver a cargar esta prueba ni duplicar los superiores.

Aplicación solicitada por el usuario el 22 de octubre de 2026 en las imágenes originales `lider_2_001_0_original.jpg` a `lider_2_005_0_original.jpg`, frames 0–4 del [trabajo 67](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/67?frame=0), tarea 28. Las fotografías conservan su resolución y encuadre originales; no se sustituyen por los recortes de la prueba anterior.

Se añadieron **45 polígonos**, todos de cuatro vértices: cinco superiores centrales y cuarenta regiones laterales parciales. Cada foto tiene ahora doce niveles marcados: cuatro centrales y cuatro fragmentos de nivel a cada lado. Los quince polígonos manuales inferiores existentes conservan exactamente sus coordenadas, IDs y atributos.

Los cinco superiores centrales siguen la regla acordada de mediana de las alturas centrales de los tres niveles inferiores de su propio tramo, con las x y pendiente de la base conservadas. Los superiores laterales usan las tres referencias visibles de su mismo tramo; se limita la región a la imagen y al poste inclinado visible, sin extrapolar el ancho que queda fuera del encuadre. Los postes y el suelo no constituyen niveles adicionales.

Los cuarenta laterales tienen `delimitacion=parcial`. Los superiores centrales nuevos tienen `delimitacion=completa`, que describe su perímetro, sin certificar una medición de ocupación. Se marcaron las oclusiones delanteras identificadas en las nuevas regiones, como las tiras de vasos colgantes y los carteles de precio que entran en el nivel. La cartelería del fondo no se usa como techo ni activa por sí sola la oclusión. Los atributos de los polígonos manuales anteriores no se modificaron.

Cada imagen recibió una etiqueta `Revision_foto` con `motivo=recorte` para dejar constancia de los niveles laterales truncados. Esta intervención no aprueba los datos para entrenamiento ni habilita el exportador V3. La visibilidad y el tratamiento de parciales requieren revisión antes del entrenamiento y del cálculo de ocupación.

- Vista conjunta (vista archivada localmente: `contacto_todos_niveles.jpg`): azul, quince polígonos manuales conservados; verde, cinco superiores centrales; naranja, cuarenta laterales parciales. Estos colores explicativos son de la vista local; todos los polígonos de CVAT comparten la clase `Nivel`.
- [Plan geométrico](plan.json): coordenadas, referencias de mediana, delimitación y oclusión de cada región nueva.
- [Verificación de la lectura posterior de CVAT](verificacion.json): cuarenta y cinco creaciones, cinco etiquetas de revisión, doce niveles por imagen y conservación íntegra de las anotaciones anteriores.
- Imágenes individuales: 001 (vista archivada localmente: `lider_2_001_todos_niveles.jpg`), 002 (vista archivada localmente: `lider_2_002_todos_niveles.jpg`), 003 (vista archivada localmente: `lider_2_003_todos_niveles.jpg`), 004 (vista archivada localmente: `lider_2_004_todos_niveles.jpg`), 005 (vista archivada localmente: `lider_2_005_todos_niveles.jpg`).

El respaldo privado, las solicitudes y la respuesta completa de CVAT están en `.resguardo/todos_niveles_job67_001_005_20261022T193220Z`. La creación se ejecutó únicamente sobre el trabajo 67 y los frames 0–4. La comprobación posterior verificó las coordenadas y atributos nuevos y la conservación de todos los polígonos, tags y tracks preexistentes, incluidos los frames 5–40. El trabajo no se marcó como completado.
