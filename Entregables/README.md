# Entregables del proyecto

La [Release vigente de Walmart Visión](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-docker-2026-10-21) contiene **Walmart_Vision_Docker_20261021.zip** y su archivo **Walmart_Vision_Docker_20261021.sha256**. El ZIP permite probar fotografías propias con cuatro modelos YOLO y la revisión 2 de detección de bordes. Incluye pesos, interfaz, iniciador Windows y ejecución con Docker para Mac Intel y Apple Silicon; no necesita datos de entrenamiento ni CVAT.

GitHub conserva este índice. Los ZIP, informes exportados y demás archivos generados se mantienen fuera del historial Git.

## Organización local

El paquete publicado incluye las instrucciones de [Docker](../Herramientas/Demo_lite/DOCKER.md). La Release del 20 de octubre y su ZIP Windows se conservan como versión anterior.

| Ubicación | Contenido |
|---|---|
| `Walmart_Vision_Docker_20261021.zip` y su `.sha256` | Paquete vigente para Windows y Mac con Docker, con comprobación de integridad. |
| `Walmart_Vision_20261020.zip` y su `.sha256` | Entrega Windows anterior, conservada con sus bytes originales. |
| `Informe_Intermedio_Avance_20261020.*` | Informe en PDF, Word y HTML, distribuido por separado. |
| `Historico/` | ZIP de versiones anteriores y sus `.sha256`, conservados solo en el laboratorio. |

El código de la aplicación está en [Herramientas/Demo_lite](../Herramientas/Demo_lite/LEEME.md), que conserva su nombre de desarrollo. Para instalar y usar la entrega, consultar la [guía de usuario](../Documentacion/Usar_Walmart_Vision.md).

Los ZIP de datos, modelos/resultados e informe se conservan fuera de la Release,
en `.publicacion/paquetes_desarrollo/` del laboratorio, para compartirlos con el
equipo por un canal separado. No se borran los resultados ni el informe histórico.
Ver la [guía de réplica](../Documentacion/Desarrollo/Replicar_proyecto.md) y el
[manifiesto](../reproducibilidad/artefactos.json).
