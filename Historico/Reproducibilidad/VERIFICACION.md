> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../Modelos/Actual/README.md).

# Verificación de la aplicación y del laboratorio

Este documento conserva las comprobaciones del laboratorio y de las versiones
anteriores de la demo del 20 de octubre de 2026. La entrega descrita en este registro para el usuario
es **Walmart Visión**, con la Release `walmart-vision-2026-10-20` y el activo
`Walmart_Vision_20261020.zip`. Su [verificación específica](../../Aplicacion/VERIFICACION_VISION.md)
registra las comprobaciones de esa versión. Los resultados históricos siguientes
mantienen el alcance y los nombres de los paquetes que se probaron.

Se preparó un checkout separado del repositorio remoto y se instalaron allí los
activos del laboratorio desde ZIP locales. No se hizo commit ni push automáticamente;
el mantenedor conserva esos pasos. La instalación del laboratorio requiere activos
del equipo y es independiente del recorrido del usuario de Visión.

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
resultados JSON compactos se conservan en [evidencias](evidencias).

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

## Qué sigue pendiente para la aplicación

Descargar la Release de Walmart Visión en otro computador físico y comprobar la
preparación inicial, los cuatro modelos, ambos métodos y el reinicio sin conexión.
La [pauta y plantilla de registro](../Documentacion/Uso_Walmart_Vision_V2.md#comprobar-la-instalación-en-otro-computador)
define los pasos. No hace falta clonar el repositorio ni instalar Docker o CVAT
para esta comprobación. La prueba local desde un ZIP extraído no acredita todavía
ese resultado externo.

## Comprobaciones adicionales para continuar el desarrollo

- Comprobar GPU y CVAT compartido con cuentas propias si se necesitan esos flujos.
- Repetir un entrenamiento completo si se pretende contrastar sus métricas. No
  se volvió a entrenar durante esta preparación ni se promete igualdad numérica
  entre hardware diferente.

Los paquetes de datos, exportaciones, resultados e informe se conservan aparte y
se instalan con `--assets` según la [guía técnica](../../Documentacion/Desarrollo/Replicar_proyecto.md).
Estas operaciones pertenecen al laboratorio del equipo y no son requisitos para
usar la aplicación publicada.

El ejemplo de cinco niveles es una prueba de funcionamiento, no una estimación
de rendimiento global. La validación real V2 contiene un único nivel reponer;
las limitaciones de datos, oclusiones y generalización siguen vigentes. No se
usó el test reservado para ajustar los cambios de distribución.

## Actualización: Lite con bordes y Release solo para probar

El ZIP nuevo incluye los cuatro modelos y la revisión 2 de detección de bordes en disposición
autónoma. Pasaron 15 pruebas de Lite, 13 del algoritmo de detección de bordes y 10 del preparador.
Desde el ZIP extraído se ejecutó la misma fotografía de validación con los cuatro
modelos, con y sin bordes. Los estados, conteos y confianzas YOLO se conservaron.
Los tres mapas se generaron en memoria sin guardar fotografías. V2 YOLO26
mantuvo cuatro suficientes y uno reponer.

La [salida compacta](evidencias/demo_lite_bordes_cpu.json) registra la procedencia
de los dos scripts y las mediciones por nivel. Los porcentajes son señal
experimental, no ocupación real validada. La estructura no requiere rutas del
laboratorio ni una conexión a CVAT. Los resultados anteriores de Docker y del
informe conservan su alcance histórico.
