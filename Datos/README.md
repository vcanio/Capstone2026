# Datos actuales

Los datos necesarios para el modelo oficial, la revisión de anotaciones y la calibración de ocupación permanecen aquí. Las fuentes compartidas mantienen sus nombres y su procedencia; una carpeta llamada V1 o V2 no implica que sus archivos hayan dejado de utilizarse.

| Necesidad | Entrada |
|---|---|
| Fuentes por procedencia | [Fuentes](Fuentes/README.md) y [V3](V3/README.md) |
| Desarrollo del modelo vigente | [Partición activa](../Documentacion/Estado_V3_actual.json) |
| Preparación y selección del ensayo | Preparados V3 (`Datos/Preparados/V3/README.md`, archivo del entorno local; fuera de esta distribución) |
| Anotaciones y revisiones | [CVAT](Registros/CVAT/README.md) |
| Índice de estado | [Registros](Registros/README.md) |
| Calibración de disponibilidad visual | Etiquetas humanas (`Datos/Preparados/V3/Calibracion_ocupacion_20261107/README.md`, archivo del entorno local; fuera de esta distribución) |
| Preparaciones anteriores | Histórico de datos (`Historico/Datos`, archivo del entorno local; fuera de esta distribución) |

El cierre revisado del 10/11 utiliza 256 train (203 reales/53 sintéticas), 1.298 polígonos train y 11 val reales con 55 polígonos. La cadena completa reúne 519 fuentes distintas de train por SHA-256 (299 reales/220 sintéticas). Las 82 antiguas val migradas a train dejan de ser validación independiente; las 68 de Ohiggins 3 solo tienen revisión visual humana y siguen fuera de train. El catálogo de 469 imágenes y sus 63 reservas es un antecedente separado, conservado con sus asignaciones. No se vuelve a repartir ni se usa test para ajustes.

`Registros/Particiones`, los registros CVAT y las fuentes compartidas se mantienen porque el sistema actual los necesita para validar procedencia y compatibilidad. Las preparaciones sustituidas fueron archivadas con sus bytes intactos. No se cuentan como fotos nuevas.
