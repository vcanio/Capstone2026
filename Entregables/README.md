# Entregables del proyecto

La [Release vigente de Walmart Visión](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-2026-10-20) contiene un único activo:
**Walmart_Vision_20261020.zip**, para probar fotografías propias con
cuatro modelos YOLO y la revisión 2 de detección de bordes. Incluye pesos e interfaz;
no necesita datos de entrenamiento, CVAT ni Docker.

GitHub conserva este índice. Los ZIP, informes exportados y demás archivos generados se mantienen fuera del historial Git.

## Organización local

| Ubicación | Contenido |
|---|---|
| `Walmart_Vision_20261020.zip` y su `.sha256` | Paquete vigente de la aplicación y comprobación de integridad. |
| `Informe_Intermedio_Avance_20261020.*` | Informe en PDF, Word y HTML, distribuido por separado. |
| `Historico/` | ZIP de versiones anteriores y sus `.sha256`, conservados solo en el laboratorio. |

El código de la aplicación está en [Herramientas/Demo_lite](../Herramientas/Demo_lite/LEEME.md), que conserva su nombre de desarrollo. Para instalar y usar la entrega, consultar la [guía de usuario](../Documentacion/Usar_Walmart_Vision.md).

Los ZIP de datos, modelos/resultados e informe se conservan fuera de la Release,
en `.publicacion/paquetes_desarrollo/` del laboratorio, para compartirlos con el
equipo por un canal separado. No se borran los resultados ni el informe histórico.
Ver la [guía de réplica](../Documentacion/Desarrollo/Replicar_proyecto.md) y el
[manifiesto](../reproducibilidad/artefactos.json).
