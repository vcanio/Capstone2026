> **Alcance de este registro de procedencia.** La V3 vigente reúne **469 imágenes (337 train / 69 val / 63 test)**. Los inventarios, tareas y particiones descritos aquí conservan su versión y fecha; las menciones de un conjunto actual de 458 imágenes corresponden a la etapa anterior a las 11 tomas de refuerzo. Los lotes se solapan y no deben sumarse como datasets independientes. [Estado vigente y límites](../../../../Documentacion/Modelo_V3_actual.md).

# Partición V3 de las 458 imágenes

Fijada el **23 de octubre de 2026**, por petición del usuario. Cubre las tareas **24, 27 y 28** del proyecto CVAT V3. Se organizaron las asignaciones mediante inventarios y listas: las fotografías conservan sus nombres, ubicaciones y bytes, y no se escribieron anotaciones en CVAT.

[Abrir catálogo visual por escena](catalogo_escenas.html) · [Inventario completo CSV](inventario.csv) · [Registro completo JSON](particion.json) · [Verificación](verificacion.json).

| Uso | Imágenes | Originales reales | Sintéticas | Grupos conservadores |
|---|---:|---:|---:|---:|
| Entrenamiento | **327** | 126 | 201 | 27 |
| Validación | **68** | 28 | 40 | 7 |
| Prueba final | **63** | 27 | 36 | 9 |
| **Total** | **458** | **181** | **277** | **43** |

El reparto global es aproximadamente **71,4 / 14,8 / 13,8 %**. Los porcentajes se subordinan a mantener juntas las escenas.

| Procedencia actual | Entrenamiento | Validación | Prueba | Total |
|---|---:|---:|---:|---:|
| Tarea 24: variantes de visibilidad limitada | 41 | 10 | 9 | 60 |
| Tarea 27: Líder Express, originales y variantes | 200 | 40 | 36 | 276 |
| Tarea 28: Líder 2, originales | 86 | 18 | 18 | 122 |
| **Total** | **327** | **68** | **63** | **458** |

## Cómo se agruparon

Se conservaron exactamente las **336 asignaciones existentes de Líder Express**, incluidos los 19 grupos de la [partición anterior](../lider_express_v2_20261019/README.md) y las 40 variantes de superior vacío, todas de familias de entrenamiento. No se movieron familias de las reservas anteriores. La reserva histórica ajena a este conjunto también permanece excluida.

Se revisaron visualmente las **122 fotos de Líder 2** en [11 hojas de contacto](evidencia/001_012.jpg). Se definieron **24 grupos conservadores**, manteniendo juntas las vistas repetidas, las zonas compartidas y algunos tramos vecinos cuando la independencia era incierta. Por ejemplo, **033 y 049 muestran el mismo tramo** y pertenecen a `l2_g04`, en validación. Las fotos 092–094 también quedan juntas. La foto 108 tiene dos módulos anotados, pero es una sola imagen y una sola unidad de partición.

Los motivos y miembros de cada grupo están en [lider2_grupos.json](lider2_grupos.json); la configuración de los 43 grupos está en [grupos_escena.json](grupos_escena.json). Los horarios de captura se usaron como apoyo, no como sustituto de la inspección visual. No se usaron predicciones ni métricas de modelos para elegir las particiones.

**43 grupos operativos no equivalen a 43 escenas físicas independientes certificadas.** Los grupos son deliberadamente conservadores; proceden de dos capturas/locales identificados como `lider_express` y `lider_2`. Hay escenas del mismo local en cada partición, por lo que esta evaluación no mide por sí sola generalización a una sucursal nueva.

## Cómo usar el reparto

- Las listas `train_catalogo.txt`, `val_catalogo.txt` y `test_catalogo.txt` contienen las 458 rutas, sin duplicar imágenes. Son listas de asignación, **no un conjunto YOLO exportado ni aprobado**.
- La evaluación principal de validación usa [28 originales reales](listas/val_real_principal.txt). Los [40 casos sintéticos](listas/val_sintetica_diagnostico.txt) se reportan como diagnóstico separado.
- La prueba final principal reserva [27 originales reales](listas/test_real_principal.txt). Sus [36 sintéticos](listas/test_sintetica_diagnostico.txt) también se reportan por separado. No usar ninguna parte del test para elegir modelos, épocas, umbrales ni reglas de producto.
- Toda futura variante debe heredar **familia, grupo de escena y partición de su original**. Una nueva toma del mismo tramo debe incorporarse a su grupo existente, aunque su número de foto sea distinto.
- Si se descubre solapamiento entre grupos de particiones diferentes, detener la exportación y documentar una nueva versión del reparto antes de entrenar; no mover archivos silenciosamente.
- Resolver la elegibilidad de anotaciones sin cambiar la asignación reservada. Si una foto queda fuera de la primera exportación, debe constar explícitamente en ese manifiesto de exportación.

## Estado de las anotaciones y del entrenamiento

Esta organización **no aprueba las anotaciones ni inicia entrenamiento**. La [lectura de CVAT usada como referencia](estado_anotaciones_referencia.json) contabiliza **2.313 polígonos**, con 2.126 atributos `delimitacion=pendiente`, 174 completos y 13 parciales. Es una fotografía del estado previo a esta partición, no una lectura en vivo durante cada verificación. Los pendientes no implican automáticamente un contorno incorrecto, pero requieren cerrar la revisión. Los parciales deben tener una política explícita de exportación; no borrar su polígono y tratar el resto de la foto como si estuviera completamente anotado.

Se mantienen `training_pipeline_supported=false`, `training_enabled=false` y las aprobaciones previas sin cambios. El exportador y la evaluación compatibles con la clase única `Nivel` siguen pendientes. El contador raíz histórico `total_polygons` de `criterio_v3.json` no es la fuente del recuento actual: consultar `live_task_counts` y la lectura de referencia por tarea.

## Respaldo y comprobación

Antes de escribir los registros se respaldaron íntegramente en `.resguardo/particion_v3_458_20261023/`: registro V3, tarea 28, manifest, inventario y README de Líder 2. Los hashes del respaldo y de los **23 archivos históricos protegidos** se guardan en `particion.json`.

La comprobación valida **458 hashes**, cobertura exacta de imágenes, ausencia de duplicados exactos, familias y escenas sin cruces entre particiones, conservación de las 336 asignaciones anteriores, exclusión de la reserva histórica y sincronización de los registros. También comprueba que solo cambiaron los campos de escena y partición de las 122 imágenes nuevas, sin aprobar anotaciones ni alterar otros campos.

Desde la raíz del proyecto:

```powershell
.venv-cvat/Scripts/python.exe Herramientas/Datos/particionar_v3_458.py --verify
```

El script no tiene operaciones de CVAT. `--apply` rechaza sobrescribir una versión o un respaldo ya existentes.
