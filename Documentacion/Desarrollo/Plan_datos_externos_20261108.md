# Plan para separar los datasets y ordenar su almacenamiento

Fecha: 8 de noviembre de 2026. Estado: **plan ejecutado con selección conservadora y respaldo independiente en C:**. El [informe de ejecución](Datos_externos_20261108.md) registra el alcance, las comprobaciones, los recibos y el ahorro. La propuesta original se conserva debajo como antecedente; las fuentes compartidas y la recuperación de bytes únicos permanecen en C:.

## Decisión recomendada

Mantener `C:\Proyectos\Walmart` como proyecto de código, aplicación, documentación y registros reproducibles. Usar `E:\Datasets Walmart` como almacenamiento principal de imágenes y exportaciones voluminosas. El proyecto debe conservar un catálogo que identifique exactamente los archivos necesarios y permita encontrarlos mediante una raíz configurable.

**Sí conviene ordenar E:** ya tiene una clasificación valiosa, pero reúne fuentes, copias clasificadas por uso, variantes sintéticas y revisión. La propuesta aprovecha esa clasificación y conserva su trazabilidad. No consiste en borrar las imágenes de C: porque exista una carpeta parecida en E:.

La aplicación distribuida debe seguir funcionando con sus pesos y con fotos que cargue el usuario, sin depender del disco E:. El laboratorio sí necesitará el almacenamiento de datos para preparar conjuntos, mostrar imágenes históricas y realizar comprobaciones de desarrollo.

## Lo comprobado antes de redactar el plan

Se inspeccionaron directorios y tamaños sin recorrer enlaces de compatibilidad, se leyeron los índices de E:, se cruzaron hashes registrados y se revisaron consumidores de rutas en el código. No se abrieron imágenes para evaluarlas ni se inició entrenamiento. Esta inspección **no reemplaza una verificación completa de hashes de los archivos actuales**.

| Material presente en E: | Resultado | Tratamiento recomendado |
| --- | --- | --- |
| Siete carpetas de locales | 609 imágenes, 1,914 GiB | Conservar como fuentes con su procedencia y lotes. Algunas son PNG: la ubicación no certifica que sean tomas reales. |
| `01_Usadas_entrenamiento_y_refuerzo` | 374 imágenes | Mantener la clasificación de uso histórico como metadatos. |
| `02_No_usadas_en_entrenamiento` | 235 imágenes; 44 usadas en validación | Mantener esa distinción; no interpretar las restantes como escenas independientes ni como datos aprobados para entrenar. |
| Las dos carpetas clasificadas, juntas | 609 archivos distintos de sus fuentes, 1,914 GiB adicionales de tamaño lógico | Son copias según el registro del 6/11; verificar de nuevo su contenido antes de consolidarlas. No son junctions ni el mismo archivo que su fuente según `samefile`. |
| `03_Variantes_ocupacion` | 630 archivos, 0,668 GiB | Conservar variantes y controles. Incluye 342 imágenes, de las cuales el registro identifica 281 variantes; no confundir láminas de revisión con datos de entrenamiento. |
| `04_Imagenes_para_pruebas` | 281 PNG y dos índices, 0,623 GiB | Colección operativa de copias de las variantes, según su LEEME. Conservar inicialmente porque la usan herramientas. |
| `Revision` | 662 imágenes y nueve JSON, 1,811 GiB | Mantener como revisión y evidencia, separada de las fuentes. |

El conjunto ocupa aproximadamente **6,93 GiB lógicos en 2.804 archivos**, incluidas las dos entradas de documentación de la raíz. No se encontraron errores de lectura ni enlaces de tipo reparse durante el inventario de E:. Había aproximadamente 14,19 GiB libres en C: y 85,76 GiB en E: al consultar; comprobar de nuevo antes de copiar.

El CSV `Clasificacion_imagenes_20261106.csv` tiene 609 hashes únicos, con las 609 rutas de origen y las 609 de destino presentes. El cruce de esos hashes registrados con la partición `v3_refuerzo_geometria_20261104` encuentra **254 de sus 275 entradas**. Las otras **21 no están identificadas por ese CSV**; esto no demuestra que falten en todo E:. Hay que buscarlas por contenido y, si corresponde, incorporarlas desde C:. Los 275 registros incluyen 11 bloqueados; no equivalen a 275 imágenes habilitadas para entrenar.

El lote de ocupación está incompleto: sus registros declaran **281 variantes disponibles de 705 previstas y 424 pendientes**. Ordenarlo no autoriza completar las generaciones, aprobar su uso ni modificar particiones. `INDICE.json` y los controles de generación contienen rutas absolutas a `02_No_usadas_en_entrenamiento`; hay que resolverlas antes de retirar esas copias.

## Qué permanece dentro del proyecto

- Código de `Aplicacion/`, `Laboratorio/` e infraestructura; pruebas, iniciadores y dependencias operativas.
- Pesos oficiales necesarios para ejecutar la app, su registro de versión y el paquete de distribución vigente. No se externaliza el modelo de la app por esta limpieza.
- Anotaciones, particiones, familias, grupos de escena, selecciones, manifiestos, configuraciones, métricas y etiquetas humanas de ocupación.
- Documentación y evidencias pequeñas necesarias para explicar el progreso. `Historico/` seguirá siendo el índice documental de la evolución, aunque algunos binarios se almacenen en E:.
- Un catálogo portable de datos externos, una plantilla de configuración y las instrucciones para conectar los datasets en otro equipo.

Las imágenes ilustrativas que hagan comprensible un informe pueden permanecer junto al documento. Las colecciones extensas de imágenes, máscaras raster y exportaciones se seleccionan por su función y dependencias, nunca solo por extensión. No se mueve una carpeta mixta completa si contiene registros que deben permanecer en el proyecto.

No se tocarán `.publicacion/repositorio`, sus worktrees, entornos activos, dependencias externas ni el contenido de releases. Las fuentes y metadatos de Fase 1 y Fase 2 quedan fuera de esta migración.

## Orden propuesto para E:

Estructura final orientativa; crear únicamente las categorías que tengan contenido:

```text
E:\Datasets Walmart\
  Catalogo\                         índices, clasificación y recibos
  Fuentes\<local>\<lote>\            fuentes canónicas con procedencia
  Derivados\Ocupacion_20261106\      variantes y sus controles
  Exportaciones\<version>\<id>\      imágenes preparadas para los ensayos
  Pruebas_ocupacion\                 colección práctica de 281 PNG, inicialmente
  Revision\                         revisión visual existente
  Historico\                        binarios de conjuntos y ensayos cerrados
```

Correspondencias propuestas:

| Ubicación actual | Destino o tratamiento |
| --- | --- |
| Carpetas de los siete locales | `Fuentes/`, conservando nombres, lotes e identidad de los archivos. |
| `01_Usadas...` y `02_No_usadas...` | Clasificación conservada en `Catalogo/`; sustituir sus copias por referencias a las fuentes cuando sus consumidores estén adaptados. |
| `03_Variantes_ocupacion` | `Derivados/Ocupacion_20261106/`, conservando controles y estados de generación. |
| `04_Imagenes_para_pruebas` | `Pruebas_ocupacion/`, inicialmente con los PNG para conservar la carga manual por carpetas. |
| `Revision` | Mantener su nombre y contenido; catalogar la relación entre originales y vistas anotadas. |
| Datasets de ensayos cerrados en C: | `Historico/` o `Exportaciones/`, según su función, con un único destino canónico registrado. |

No conviene clasificar físicamente todas las fuentes en «train» y «val» de una única versión: una misma imagen puede tener usos distintos en el historial. Esa relación debe estar en los manifiestos de cada versión. Las variantes heredan la familia y el grupo de escena de su fuente; no pasan a ser ejemplos independientes por cambiar de carpeta.

Durante la transición se conservarán los nombres actuales hasta adaptar y verificar los consumidores. Los índices originales se guardarán sin cambios como evidencia; los índices operativos nuevos tendrán versión y un mapa de equivalencias. La colección práctica de pruebas puede seguir ocupando sus 0,623 GiB: eliminar esa duplicación tiene menos prioridad que conservar un flujo cómodo y funcional.

## Volumen candidato dentro de C:

Inventario de imágenes en los bloques principales, excluyendo enlaces de directorio. Las cifras son tamaños lógicos, no una promesa de espacio físico recuperable ni una orden de trasladar todo el bloque.

| Bloque | Imágenes, aproximadamente | Alcance |
| --- | ---: | --- |
| `Historico/Datos` | 8,594 GiB | Preparaciones y exportaciones anteriores. |
| `Historico/Experimentos` | 4,863 GiB | Datasets y salidas de ensayos cerrados. |
| Ensayo oficial en `Laboratorio/Experimentos` | 3,042 GiB | Principalmente dataset exportado; conservar pesos y registros operativos en C:. |
| `Datos/Preparados/V3` físico actual | 1,246 GiB | Incluye fuentes de refuerzo y preparación vigente; comprobar cada dependencia. |
| Principales carpetas físicas `Datos/V3` | 1,341 GiB | Fuentes y vistas por uso, preservando todas las referencias necesarias. |

Son aproximadamente **19,1 GiB de imágenes candidatas a revisión**. Parte puede coincidir con E: o con otra copia de C:, y parte puede convenir conservar junto a un informe. El ahorro definitivo se calculará con el manifiesto de traslado y la asignación real en disco. Los aproximadamente 19,5 GiB archivados en la limpieza anterior incluyen otros tipos de archivo y no son esta misma medición.

## Ejecución por etapas

### 1. Fijar el inventario y la cobertura

1. Registrar los archivos físicos de C: y E: sin seguir junctions, con tamaño, SHA-256, ubicación, procedencia y función. Trabajar por lotes para no crear otra copia completa temporal en C:.
2. Identificar coincidencias exactas. No deduplicar por nombre, dimensiones ni parecido visual: una exportación con orientación normalizada puede diferir de la fuente y ser necesaria.
3. Resolver las 21 entradas sin correspondencia en el CSV y comprobar la cobertura de toda la partición actual, de la muestra de ocupación y de los conjuntos históricos referenciados. Consultar los 163 registros de `muestra_desarrollo.json`, incluidas sus rutas `serve_path`.
4. Emitir un manifiesto revisable por archivo: origen lógico, origen físico, destino, hash, dependencias, acción y motivo. Distinguir «ya existe en E:», «copiar a E:», «conservar en C:» y «ausencia conocida».
5. Registrar como retiradas intencionalmente las tres imágenes V1 que Vicente confirmó haber eliminado. No restaurarlas automáticamente, inventar sus hashes ni cambiar manifiestos históricos para ocultar su ausencia. El verificador deberá distinguir una excepción documentada de una pérdida nueva.

**Salida:** catálogo completo y correspondencias comprobadas; ninguna fuente necesaria queda sin destino identificado. La reserva final se conserva sin inferencia ni ajustes; verificar integridad no significa evaluarla. R254 permanece excluida.

### 2. Preparar acceso portable a los datos

Propuesta: variable local `WALMART_DATA_ROOT=E:\Datasets Walmart` y catálogo versionado dentro del proyecto, por ejemplo `Datos/Registros/Almacenamiento/catalogo.json`. El catálogo contendrá rutas relativas a esa raíz, hash y tamaño; la letra del disco quedará en configuración local, con plantilla documentada. Los registros privados seguirán siendo privados.

Las referencias históricas como `Datos/V2/...` y los manifiestos congelados se conservarán. Un resolvedor explícito relacionará esas referencias con el archivo externo, sin reescribir sus hashes ni cambiar los identificadores de los ensayos. No basta con dejar un listado de nombres: deben existir código de resolución y controles de integridad.

Puntos de adaptación identificados:

- `Laboratorio/Modelos/preparacion_v3.py` y validadores de refuerzo/partición: hoy restringen las imágenes a `Datos/`.
- Exportadores y lectores de datasets del entrenador: separar metadatos versionados de imágenes externas; generar configuraciones operativas para el equipo sin modificar los manifiestos congelados.
- `Laboratorio/Modelos/panel_modelos.py`: autorizar solo archivos del catálogo. No permitir al servidor leer cualquier ruta de E:.
- `Laboratorio/Ocupacion/preparar_muestra.py`, `evaluar_linea_base.py` y `etiquetador_ocupacion.py`: resolver imágenes de la muestra conservando sus etiquetas y procedencia.
- `Laboratorio/Ocupacion/diagnostico_pruebas_04.py` y `visor_linea_a.py`: sustituir sus rutas E: fijas por configuración y conservar la colección de pruebas.
- Verificadores, galerías, iniciadores y referencias de documentos: comprobar dependencias adicionales con el manifiesto de traslado.

`Laboratorio/Modelos/archivo_historico.py` permite destinos dentro de `Historico/`; no está diseñado para apuntar directamente a E:. La externalización necesita una resolución específica, manteniendo límites de acceso y la compatibilidad existente. No se resolverá simplemente relajando todas las comprobaciones de rutas.

Para Docker, montar la raíz externa en una ruta estable como `/datasets`, en lectura para los consumidores. Los procesos que necesiten crear exportaciones tendrán una salida explícita con escritura, separada de fuentes y reserva final. Revisar `Infraestructura/Docker/compose.modelos.yml` y sus variantes sin depender de junctions de Windows dentro del contenedor.

**Salida:** consumidores capaces de leer tanto la ubicación actual como la externa durante una transición controlada. Si E: no está disponible, el laboratorio debe explicar qué datos faltan; la app distribuida debe seguir operativa.

### 3. Consolidar E: y copiar por lotes

1. Guardar la clasificación del 6/11, los controles de variantes y las equivalencias antes de cambiar rutas operativas.
2. Ordenar fuentes y derivados según el mapa aprobado, preservando nombres, bytes y relaciones entre imagen, anotación y variante. No mezclar sintéticas con tomas reales en los metadatos.
3. Incorporar solo archivos necesarios que no estén ya disponibles con el mismo hash. Copiar desde C:, verificar en E: y conservar el origen hasta terminar las comprobaciones.
4. Externalizar primero datasets históricos; después las exportaciones del ensayo oficial y, finalmente, las fuentes y preparaciones activas. Verificar cada lote antes de continuar.
5. Actualizar el catálogo operativo y los montajes. Mantener un recibo con rutas anteriores y nuevas, conteos, bytes, hashes y resultado.

No trasladar recursivamente un alias. Resolver previamente el destino físico y comprobar que queda dentro de las raíces previstas. No reconstruir respaldos, pesos antiguos ni generaciones pendientes retiradas o incompletas.

### 4. Comprobar funcionamiento antes de retirar copias

- Todos los archivos del manifiesto conservan sus hashes; las ausencias conocidas quedan identificadas por separado.
- La partición vigente conserva sus 275 registros, bloqueos, grupos y asignaciones; la exportación habilitada mantiene 171 train, 59 validación real y 34 sintéticas.
- La muestra y las etiquetas de ocupación siguen enlazadas a las mismas imágenes; no se recalibran umbrales ni se recalculan comparaciones históricas como si fueran equivalentes.
- En Windows y Docker funcionan el catálogo del laboratorio, las imágenes autorizadas, la lectura de la exportación actual y al menos una referencia histórica afectada. Comprobar configuración del entrenamiento sin iniciarlo.
- Ejecutar las pruebas pertinentes de datos, rutas y panel, incluyendo rechazo de rutas fuera del catálogo, disco no disponible y colisiones de nombres.
- Verificar que la app y su paquete aislado pueden analizar una foto de desarrollo sin E:. Conservar pesos, revisión de Línea A y umbral 52.
- No acceder al test para inferencias, no modificar CVAT y no publicar releases ni entrenar como parte de la migración.

**Salida:** informe de comprobaciones y lista exacta de copias de C: que pueden retirarse.

### 5. Liberar espacio y cerrar la documentación

Retirar únicamente las copias incluidas en el manifiesto cuya identidad y funcionamiento externo ya estén verificados. Si un lote falla, mantener su origen y volver a su configuración anterior. Antes de retirar la última copia independiente de un dato único, definir y comprobar su respaldo: estar en E: no demuestra que exista respaldo.

Consolidar las 609 copias clasificadas de E: solo después de adaptar los controles que las referencian. Conservar la colección práctica de pruebas inicialmente. Documentar ahorro real, excepciones, ubicación de cada conjunto y procedimiento de reconexión en otro equipo.

El cierre debe actualizar el mapa del proyecto y su estado, conservando la historia de la limpieza anterior. Tras retirar un origen de C:, la reversión requerirá copiar desde el destino verificado o el respaldo; no presentar esa fase como reversible solo cambiando una variable.

## Criterio de finalización

El proyecto queda ligero y comprensible, E: contiene los datos identificados por versión y procedencia, y un equipo nuevo puede localizar los archivos y comprobar su identidad mediante configuración y manifiestos. Ningún consumidor depende de una ruta absoluta escondida ni de una copia retirada. La aplicación conserva su autonomía y el histórico sigue explicando cómo se llegó a la versión vigente.

Para esta primera migración, usar el sistema de manifiestos ya existente más el catálogo de almacenamiento. La incorporación de DVC puede estudiarse después si se necesita sincronizar versiones entre equipos; no es un requisito para ordenar estas dos carpetas.

## Referencias de la inspección

- [Limpieza anterior](Limpieza_orden_20261108.md) y [mapa del proyecto](Mapa_del_proyecto.md).
- [Partición activa](../Estado_V3_actual.json) y partición de desarrollo (`Datos/Registros/Particiones/v3_refuerzo_geometria_20261104/particion.json`, archivo del entorno local; fuera de esta distribución).
- Muestra de ocupación (`Datos/Preparados/V3/Calibracion_ocupacion_20261107/muestra_desarrollo.json`, archivo del entorno local; fuera de esta distribución).
- En E: `LEEME_Clasificacion_20261106.txt`, `Clasificacion_imagenes_20261106.csv`, `03_Variantes_ocupacion/LEEME.txt`, `ESTADO_DEL_LOTE.txt`, `_control/inventario.json` y `04_Imagenes_para_pruebas/INDICE.json` y `LEEME.txt`.

La entrega original añadió únicamente este plan. Su ejecución posterior queda documentada en el [informe de migración](Datos_externos_20261108.md) y en el [catálogo y sus recibos](../../Datos/Registros/Almacenamiento/README.md).
