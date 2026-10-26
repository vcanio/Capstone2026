# Resúmenes públicos de las comprobaciones

Esta carpeta conserva resultados compactos y figuras que respaldan la documentación. Los registros describen la fecha en que se hicieron las comprobaciones; no acreditan una nueva ejecución ni el estado actual de un servicio remoto.

| Evidencia pública | Alcance |
|---|---|
| [Preparación del repositorio, 23/10/2026](sincronizacion_repo_20261023.md) | Pruebas de reproducción, visor, datos y laboratorio; manifiesto complementario y conservación de cambios previos. |
| [Orden del proyecto, 23/10/2026](orden_proyecto_20261023.md) | Guías y enlaces actualizados, entrega local de dos modelos, temporales archivados, cachés eliminadas y conservación de datos y del checkout Git. |
| [Verificación del informe](verificacion_informe_20261020.json) | Corte original del 20 de octubre: 20 casos visuales, 11 pruebas de datos, 222 pruebas de modelos con una omitida y verificación de la partición de 296 imágenes. También conserva los intentos fallidos y las limitaciones del entorno. |
| [Revisión de claridad](verificacion_claridad_20261020.json) | Comprobaciones documentales de lectura y requisitos. |
| [Revisión de planificación](verificacion_planificacion_20261020.json) y [datos de planificación](planificacion_20261020.json) | Hitos, responsables propuestos y datos de la Gantt. |
| [Casos históricos de YOLO](casos_informe_20261020.json) | Selección anterior del 20 de octubre; se conserva su evidencia original. |
| [Casos de YOLO + bordes](casos_yolo_bordes_20261021.json) | Selección actual de 10 casos favorables y 10 con errores; procedencia, imágenes y correcciones de consistencia. B09 reemplaza la fotografía repetida del documento recibido. |
| [Revisión del informe con bordes](verificacion_informe_yolo_bordes_20261021.json) | Integridad de evidencias, comprobación de los veinte casos y revisión visual del documento actualizado. |
| [Plan de la demostración](plan_video_20261021.json) y [verificación del video](verificacion_demo_video_20261021.json) | Guion de diez bloques, cuatro casos del informe (`B06`, `B08`, `F01`, `F03`), locución humana sincronizada (`410,59 s`), 94 bloques de subtítulos y montaje final verificado (`421,59 s`, `1920 × 1080`, SHA-256 `773414e8...`). |
| [Verificación de Visión](../../Aplicacion/VERIFICACION_VISION.md) | Comprobaciones de la aplicación publicada; conserva pendiente la instalación en otro computador físico. |
| [Posprocesamiento de contornos](posprocesamiento_contornos_20261022.json) | Ajuste visual a cuatro vértices: 21 pruebas técnicas y seis ajustes aceptados en una foto conocida. Conserva máscaras y métricas originales; no demuestra mejora de precisión. Paquete de prueba local, sin modificar la release publicada. |
| [Verificación Docker](../../Aplicacion/VERIFICACION_DOCKER.md) y [publicación del 21 de octubre](publicacion_vision_docker_20261021.json) | Inferencia AMD64/ARM64 emulada, Release Docker, hashes y descargas públicas verificadas. La prueba en un Mac físico sigue pendiente. |
| [Preparación del laboratorio y la demo](../../Historico/Reproducibilidad/VERIFICACION.md) | Alcance de las comprobaciones de instalación, Docker e inferencia. |

## Consulta histórica de GitHub

La consulta conservada localmente el 20 de octubre de 2026 correspondía a un estado anterior de `vcanio/Capstone2026`, cuya rama predeterminada era `main`. En su lista de commits figuraba `ddbc7acb9f227faafbf87dfe7c3dcf08f573b125` del 15 de octubre, con el mensaje «Readme update». Ese registro no representa la publicación posterior de Walmart Visión ni el estado remoto actual. La evolución se comprueba en el historial Git y en las referencias actuales del README.

La respuesta completa de la consulta se conserva en local. Este resumen sustituye su publicación; no vuelve a consultar GitHub ni añade una comprobación remota.

## Material que queda solo en local

- Los logs extensos de pruebas y partición bajo `Documentacion/Evidencias/`, incluidos los de subcarpetas.
- Las respuestas completas `consulta_github_*.json` bajo esa misma carpeta.
- Los respaldos bajo `Datos/Registros/Particiones/**/respaldo_registros/`.

Los archivos locales originales se conservan sin cambios. En los registros públicos, `log_local` y `consulta_local` identifican esos originales para el equipo; no son archivos descargables del repositorio. Las reglas de Git, el empaquetador y la auditoría de publicación excluyen este material. Las métricas, particiones vigentes, resúmenes y evidencia técnica de los modelos permanecen en Git.
