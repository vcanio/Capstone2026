# Manifiesto y evidencias de verificación

Esta carpeta conserva los registros que permiten identificar la entrega y comprobar qué se verificó.

**Alcance fechado:** `artefactos.json` identifica distribuciones anteriores. La entrega local revisada del 23/10/2026 se consulta en [Entregables](../Entregables/README.md). No se ha reemplazado el manifiesto histórico ni publicado un paquete durante esta limpieza. El trabajo de datos V3 se identifica por separado en [Registros](../Datos/Registros/README.md).

[activos_locales_20261023.json](activos_locales_20261023.json) complementa ese registro con los recursos V3 y los dos ZIP locales conservados. Incluye archivos, tamaños y hashes reales. No contiene URLs de descarga pública: se suministran al equipo mediante `--assets`. Actualizar el código en GitHub no publica esos activos.

| Archivo o carpeta | Contenido |
|---|---|
| [artefactos.json](artefactos.json) | Paquetes de la aplicación y del laboratorio, archivos incluidos, tamaños y hashes SHA-256. |
| [artefactos_demo_20261020.json](artefactos_demo_20261020.json) | Manifiesto histórico del ZIP Windows del 20 de octubre, conservado al publicar la entrega Docker. |
| [VERIFICACION.md](VERIFICACION.md) | Comprobaciones realizadas, alcance de los resultados y pruebas pendientes. |
| [evidencias](evidencias/README.md) | Resultados compactos de las comprobaciones del panel y de la aplicación. |

Los programas para preparar activos, repetir entrenamientos y verificar la publicación están en [Herramientas/Reproducibilidad](../Herramientas/Reproducibilidad/README.md). Las figuras y comprobaciones que respaldan el informe se organizan en [Documentacion/Evidencias](../Documentacion/Evidencias/README.md).

Para instalar el laboratorio, consultar la [guía técnica](../Documentacion/Desarrollo/Replicar_proyecto.md); para usar la aplicación publicada, seguir la [guía de Walmart Visión](../Documentacion/Usar_Walmart_Vision.md).
