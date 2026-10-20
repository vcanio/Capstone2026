# Verificación de la entrega reproducible

Fecha de comprobación: 20 de octubre de 2026. Se preparó un checkout separado
del repositorio remoto y se instalaron allí los activos desde ZIP locales. No se
ha hecho commit, push, tag ni publicación de la Release desde esta preparación.

## Resultado comprobado

| Comprobación | Resultado |
|---|---|
| Instalación en el checkout separado | Fuentes, exportaciones, modelos/resultados e informe instalados sin usar accesos de CVAT. |
| Integridad por SHA-256 de lo instalado | 507 archivos de fuentes, 526 de exportaciones, 3.980 de modelos/resultados y 3 del informe: correctos. |
| Verificador de proyecto y datos | 435 registros de inventario, 405 imágenes únicas y dos exportaciones congeladas: correctos. |
| Partición V2 | 296 registros, familias y grupos conservados; comprobación de partición correcta. |
| Repetición de ensayo en modo solo-verificar | V2 YOLO26: exportación, snapshot, partición y pesos originales disponibles; no inició entrenamiento. |
| Docker final | Imagen construida desde el checkout preparado y contenedor aislado saludable en CPU. |
| Panel sin CVAT | Cuatro ensayos y cuatro modelos entrenados disponibles; CVAT deshabilitado y sin archivo de acceso montado. La operación que requiere CVAT responde HTTP 400 con explicación. |
| Inferencia del panel | V2 YOLO26, lider_express_040_0_original.jpg, confianza 0,25 y NMS 0,70: cinco niveles, cuatro suficientes y uno reponer; 5/5 estados y sin omisiones ni extras en este caso. |
| Demo autónoma extraída del ZIP | Los cuatro modelos respondieron en CPU; V2 YOLO26 produjo el mismo conteo esperado del ejemplo. No necesita el laboratorio, Docker o CVAT. |
| Interfaz Lite | Revisión visual de perfiles V1 y V2 base y de vista móvil de 390 px. |
| Guía de equipo | Ocho páginas PDF renderizadas e inspeccionadas; fuente Markdown incluida en Git. |

La prueba Docker utilizó un proyecto y puerto separados del servicio del
laboratorio. Al terminar se retiraron su contenedor y su red de prueba. Los
resultados JSON compactos se conservan en [evidencias](evidencias/).

## Pruebas de código

- Modelos/panel/datasets: 222 pruebas ejecutadas, resultado OK, una omitida porque
  requiere activar explícitamente la integración real RUN_NIVELES_REAL=1.
- Datos y particiones: 11 pruebas, OK.
- Demo Lite: 11 pruebas, OK.
- Preparador y CVAT opcional: 9 pruebas, OK. Incluyen integridad, rutas de ZIP,
  instalación sin sobrescritura y la respuesta HTTP cuando CVAT está deshabilitado.
- Panel tras el ajuste final de respuesta HTTP: 11 pruebas pertinentes, OK.

El verificador de publicación comprueba los archivos visibles para Git, la
sintaxis Python, enlaces Markdown y activos declarados. Rechaza rutas privadas,
pesos/ZIP en el historial, archivos de 50 MiB o más y campos JSON con posibles
credenciales. Esto no equivale a una auditoría completa de seguridad. El workflow
de GitHub está preparado; su ejecución remota se podrá revisar después del push.

## Qué sigue pendiente

1. Commit y push por el mantenedor, creación de la Release con el tag previsto y
   carga de sus siete archivos. Las URLs remotas aún dependen de esa publicación.
2. Clonar y descargar por HTTPS desde GitHub en otro computador físico, siguiendo
   [la guía de réplica](../Documentacion/Replicar_proyecto.md). La instalación
   local con --assets demuestra el contenido de los ZIP, no su descarga remota.
3. Comprobar GPU y CVAT compartido con cuentas propias si se necesitan esos flujos.
4. Repetir un entrenamiento completo si se pretende contrastar sus métricas. No
   se volvió a entrenar durante esta preparación ni se promete igualdad numérica
   entre hardware diferente.

El ejemplo de cinco niveles es una prueba de funcionamiento, no una estimación
de rendimiento global. La validación real V2 contiene un único nivel reponer;
las limitaciones de datos, oclusiones y generalización siguen vigentes. No se
usó el test reservado para ajustar los cambios de distribución.
