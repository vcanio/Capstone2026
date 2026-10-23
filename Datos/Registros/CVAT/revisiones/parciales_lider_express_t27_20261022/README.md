> **Prueba histórica retirada / vista previa fuera del dataset.** El 23/10/2026 sus imágenes de revisión se trasladaron al archivo local `.resguardo/orden_registros_20261023/vistas_pruebas_retiradas/parciales_lider_express_t27_20261022/`. Los planes, coordenadas, verificaciones y reversiones permanecen aquí. Las cifras e instrucciones siguientes describen aquella prueba, no el estado vigente.

# Líder Express V3: añadir exclusivamente niveles parciales

**RETIRADO A PETICIÓN DEL USUARIO.** El 22 de octubre de 2026 se eliminaron exclusivamente los 2.135 polígonos parciales añadidos por el asistente y sus 14 etiquetas de revisión. La tarea 27 conserva los **1.416 polígonos anteriores**, con los mismos IDs, coordenadas y atributos. La lectura posterior coincide exactamente con el estado previo a esta prueba en los trabajos 64, 65 y 66. [Verificación de reversión](reversion.json).

El usuario decidió conservar el alcance de niveles completos para el flujo de ocupación y alertas, sin continuar la anotación exhaustiva de incompletos. Los planes, imágenes, IDs y cifras siguientes documentan exclusivamente la prueba histórica; **no son las anotaciones vigentes**. El respaldo permite recuperar la prueba si se solicita, pero no debe cargarse automáticamente. No se modificó la prueba separada de Líder 2.

Intervención solicitada por el usuario el 22 de octubre de 2026 en la [tarea 27](https://pcvicen.tailca514b.ts.net/tasks/27), **Líder Express · originales + A/B/C/D · 276 imágenes · V3**. El usuario pidió conservar todos los niveles existentes, marcar los parciales en cada original y copiarlos a sus variantes.

## Resultado verificado

| Concepto | Cantidad |
|---|---:|
| Originales revisadas | 59 |
| Variantes A/B/C revisadas | 177 |
| Variantes D revisadas | 40 |
| Polígonos anteriores conservados íntegramente | 1.416 |
| Parciales nuevos definidos en originales | 457 |
| Copias proporcionales en variantes | 1.678 |
| Parciales nuevos totales | 2.135 |
| Total final de polígonos | 3.551 |
| Imágenes con polígonos añadidos | 237 |
| Etiquetas nuevas de revisión por fragmentos no delimitables | 14 |

Se enviaron únicamente solicitudes de creación. No se actualizaron ni eliminaron polígonos existentes. La lectura posterior comprobó igualdad exacta de los 1.416 registros anteriores, incluidos IDs, coordenadas, clases, atributos y oclusión. Sus hashes SHA-256 coinciden antes y después, por trabajo. Los tags y tracks anteriores se conservaron.

| Trabajo | Anteriores | Nuevos parciales | Total |
|---|---:|---:|---:|
| [64](https://pcvicen.tailca514b.ts.net/tasks/27/jobs/64?frame=0) | 465 | 766 | 1.231 |
| [65](https://pcvicen.tailca514b.ts.net/tasks/27/jobs/65?frame=92) | 500 | 840 | 1.340 |
| [66](https://pcvicen.tailca514b.ts.net/tasks/27/jobs/66?frame=187) | 451 | 529 | 980 |

## Criterio aplicado

Todos los polígonos nuevos usan la clase existente `Nivel`, cuatro vértices y `delimitacion=parcial`. Se incluye únicamente el área visible identificable de los tramos recortados, sin extrapolar su ancho oculto. Las referencias proceden de las originales y de sus estructuras y niveles ya marcados; las propuestas se revisaron sobre cada original. Se adaptaron las distribuciones laterales cuando el vecino tiene otra cantidad de repisas. Los superiores abiertos utilizan las referencias inferiores visibles de su propio tramo cuando son suficientes. Se añadieron también tres zonas superiores recortadas por el borde de la imagen en las familias 035, 037 y 044.

Se revisaron las originales y las 217 variantes mediante las láminas de familia. La transferencia conserva exactamente las mismas coordenadas normalizadas del original y solo aplica escala por resolución. Los originales miden 3000 × 4000; 216 variantes miden 1086 × 1448 y una mide 1087 × 1447. La comprobación leyó las coordenadas guardadas de cada copia y verificó su correspondencia normalizada con el original. No se redibujaron independientemente las variantes, ni se modificaron imágenes, familias o particiones.

En las familias **019, 028, 043 y 055–059** no se añadieron polígonos: son cabeceras sin nuevos parciales del tramo objetivo. Las góndolas del fondo de los pasillos no forman parte de esta anotación.

Se conservaron los niveles existentes incluso cuando su contorno o atributo queda pendiente de revisión. Esta intervención no certifica exhaustividad o precisión de esos polígonos anteriores ni los aprueba para entrenamiento. El atributo `parcial` tampoco habilita ocupación total ni se convierte automáticamente en una clase adicional de YOLO. El entrenamiento permanece sin habilitar.

## Fragmentos que requieren revisión

Tres fragmentos son demasiado estrechos o no permiten recuperar un perímetro fiable: superior derecho de las familias **002** y **022**, y superior izquierdo de **054**. No se inventó su geometría. Se añadió `Revision_foto`, con `motivo=nivel_no_delimitable`, a las originales y sus variantes existentes: catorce imágenes. Los demás polígonos de esas imágenes sí quedaron añadidos según el plan.

Este registro es una revisión del asistente; los casos señalados requieren resolución humana antes de exportar la fotografía como exhaustivamente anotada para entrenamiento.

## Evidencias

- [Verificación posterior de CVAT](verificacion.json): conteos, hashes de conservación y comprobación de copias normalizadas.
- [Polígonos creados](poligonos_creados.json): IDs leídos de CVAT, origen, variante, trabajo, frame, región y coordenadas.
- [Plan completo](plan.json) y [familias originales](familias.json).
- [Fragmentos no delimitables](fragmentos_no_delimitables.json) y [fotos señaladas en CVAT](fotos_para_revision.json).

En las vistas de originales, azul identifica los niveles previos y naranja los parciales nuevos. Los colores son explicativos de la revisión local: en CVAT todos los polígonos comparten la clase `Nivel`.

| Originales | Vista |
|---|---|
| 001–006 | Lámina 1 (vista archivada localmente: `originales_01.jpg`) |
| 007–012 | Lámina 2 (vista archivada localmente: `originales_02.jpg`) |
| 013–018 | Lámina 3 (vista archivada localmente: `originales_03.jpg`) |
| 019–024 | Lámina 4 (vista archivada localmente: `originales_04.jpg`) |
| 025–030 | Lámina 5 (vista archivada localmente: `originales_05.jpg`) |
| 031–036 | Lámina 6 (vista archivada localmente: `originales_06.jpg`) |
| 037–042 | Lámina 7 (vista archivada localmente: `originales_07.jpg`) |
| 043–048 | Lámina 8 (vista archivada localmente: `originales_08.jpg`) |
| 049–054 | Lámina 9 (vista archivada localmente: `originales_09.jpg`) |
| 055–059 | Lámina 10 (vista archivada localmente: `originales_10.jpg`) |

| Familias: original y variantes | Vista |
|---|---|
| 001–005 | Lámina 1 (vista archivada localmente: `familias_variantes_01.jpg`) |
| 006–010 | Lámina 2 (vista archivada localmente: `familias_variantes_02.jpg`) |
| 011–015 | Lámina 3 (vista archivada localmente: `familias_variantes_03.jpg`) |
| 016–020 | Lámina 4 (vista archivada localmente: `familias_variantes_04.jpg`) |
| 021–025 | Lámina 5 (vista archivada localmente: `familias_variantes_05.jpg`) |
| 026–030 | Lámina 6 (vista archivada localmente: `familias_variantes_06.jpg`) |
| 031–035 | Lámina 7 (vista archivada localmente: `familias_variantes_07.jpg`) |
| 036–040 | Lámina 8 (vista archivada localmente: `familias_variantes_08.jpg`) |
| 041–045 | Lámina 9 (vista archivada localmente: `familias_variantes_09.jpg`) |
| 046–050 | Lámina 10 (vista archivada localmente: `familias_variantes_10.jpg`) |
| 051–055 | Lámina 11 (vista archivada localmente: `familias_variantes_11.jpg`) |
| 056–059 | Lámina 12 (vista archivada localmente: `familias_variantes_12.jpg`) |

Respaldo privado, programas reproducibles, solicitudes y lecturas completas anteriores/posteriores: `.resguardo/parciales_t27_20261022T194045Z`. Solo se escribieron los trabajos 64, 65 y 66 de la tarea 27; no se marcó su estado como completado.
