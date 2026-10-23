# Líder 2 · originales para Criterio V3

[Abrir tarea 28 en CVAT](https://pcvicen.tailca514b.ts.net/tasks/28) · proyecto **Walmart Stock · V3**.

122 fotografías reales, tomadas el 17 de octubre de 2026 e incorporadas el 22 de octubre. El identificador local es `lider_2`, para distinguirlo del primer set `lider_express`; el nombre oficial de la sucursal no se ha registrado. El lote incluye góndolas claras y negras, distintas distribuciones, huecos y vistas de un mismo tramo.

## Nombres y procedencia

Las fotos se renombraron en orden cronológico de sus nombres de captura, desde **`lider_2_001_0_original.jpg`** hasta **`lider_2_122_0_original.jpg`**. Se mantiene el esquema `local_secuencia_variante`: `0_original` identifica una foto real. El renombrado no modifica los bytes ni la información EXIF.

- [Inventario de nombres anteriores, nuevos, hashes y acceso a CVAT](inventario.csv).
- [Registro completo del lote y correspondencia con los trabajos](manifest.json).
- [Catálogo visual de escenas y fotos](../../Registros/Particiones/v3_458_20261023/catalogo_escenas.html), con las [hojas de contacto verificadas de la partición](../../Registros/Particiones/v3_458_20261023/README.md).

Los nombres anteriores y hashes también se guardaron antes del renombrado en `.resguardo/lider2_nombres_20261022/nombres_y_hashes_originales.json`. Se verificaron 122 imágenes legibles, dimensiones orientadas 3000 × 4000 y ausencia de duplicados exactos dentro del lote o contra el registro activo de imágenes V3.

## Qué marcar

Se aplica la [guía de áreas de nivel V3](../../../Documentacion/Desarrollo/Criterio_V3_niveles.md), disponible también en el proyecto de CVAT. **Todas las góndolas usan la misma clase `Nivel`, independientemente del color.** Se marca el área útil completa, incluidos sus huecos; no el portaprecios ni el contorno de los envases. No se trasladan clases de reposición a YOLO.

Las 122 imágenes se cargaron sin polígonos. La prueba inicial del asistente en las fotos 001–010 se retiró a petición del usuario y después continuó la anotación manual. [Registro de reversión](../../Registros/CVAT/revisiones/job67_primeras10_20261022/reversion.json). El usuario marca los niveles inferiores y autoriza las intervenciones del asistente; sus polígonos inferiores se conservan al calcular el superior.

La [prueba histórica de las primeras cinco fotos](../../Registros/CVAT/revisiones/todos_niveles_job67_001_005_20261022/README.md) documenta una intervención anterior con laterales; no describe el estado vigente. Antes de la nueva aplicación de superiores, la lectura del job 67 contenía 134 polígonos manuales y ningún superior de aquella prueba.

**Aplicación vigente autorizada por el usuario:** se añadieron los 41 superiores del job 67, conservando exactamente esos 134 polígonos manuales. Las bases se identificaron sobre el portaprecio y se proyectó la mediana de los inferiores de cada foto. En las fotos 031, 032, 037, 038 y 039 el usuario autorizó usar sus dos referencias disponibles. Los superiores de 007, 018 y 039 quedan recortados al encuadre y marcados parciales. El job 67 tiene 175 polígonos. [Plan por foto, comparaciones y verificación](../../Registros/CVAT/revisiones/superiores_job67_20261022/README.md). No duplicar los superiores al continuar la revisión. El trabajo permanece en curso.

**Job 68:** se añadieron los 41 superiores de las fotos 042–082, conservando exactamente sus 171 polígonos manuales. Se calcularon 37 por mediana y se respetó la cubierta física de las vitrinas en 074–077. La foto 060 tiene el superior recortado y marcado parcial; los otros 40 son completos dentro del encuadre. Todas tenían al menos tres referencias inferiores. El job tiene 212 polígonos y permanece en curso. [Registro y vistas](../../Registros/CVAT/revisiones/superiores_job68_20261022/README.md). No volver a crear esos superiores.

**Job 69:** se añadieron 41 superiores en las 40 fotos 083–122, conservando exactamente los 161 polígonos manuales. La foto 108 tiene dos módulos anotados y recibe dos superiores, calculados por separado con las referencias de cada módulo. Se proyectaron 38 medianas y se respetó el techo físico de la vitrina en 115–117. Las fotos 092, 093, 094 y 111 quedaron recortadas y marcadas parciales. El job tiene 202 polígonos y permanece en curso. [Registro y vistas](../../Registros/CVAT/revisiones/superiores_job69_20261022/README.md). No volver a crear esos superiores.

Se mantiene el atributo `delimitacion` (`pendiente`, `completa`, `parcial`) y la etiqueta de imagen `Revision_foto` para casos que necesiten revisión. Un nivel superior vacío también se marca. Si falta un tope superior físico claro se aplica la regla de mediana de los inferiores; no se ajusta al tope del producto de cada foto. `completa` describe el contorno, sin certificar revisión humana ni autorizar entrenamiento.

Los tres trabajos empiezan sin asignación personal:

| Trabajo | Fotos | Cantidad |
|---|---|---:|
| [67](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/67) | 001–041 | 41 |
| [68](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/68) | 042–082 | 41 |
| [69](https://pcvicen.tailca514b.ts.net/tasks/28/jobs/69) | 083–122 | 40 |

No se importan contornos del primer local porque estas imágenes muestran otras escenas. [Registro de la carga verificada](../../Registros/CVAT/tarea_28.json).

## Partición y entrenamiento

La partición quedó **fijada por familias y escenas el 23 de octubre de 2026**: **86 fotos de entrenamiento, 18 de validación y 18 de prueba**, en **24 grupos conservadores** revisados visualmente. Las vistas repetidas y los tramos vecinos se mantienen juntos, incluidas las fotos 033 y 049 del mismo tramo. `grupo_escena` y `particion_modelo` están aplicados en el inventario y sincronizados con el manifest y los registros V3. Toda futura variante hereda el grupo y la partición de su original. La secuencia individual de cada foto no certifica independencia entre escenas.

Consultar el [catálogo y registro de las 458 imágenes V3](../../Registros/Particiones/v3_458_20261023/README.md). El entrenamiento permanece deshabilitado: organizar la partición no aprueba las anotaciones ni sustituye su revisión.

Una imagen todavía sin anotar no se considera un negativo sin niveles. La incorporación a CVAT no habilita exportación ni entrenamiento automático.
