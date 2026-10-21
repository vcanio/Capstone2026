# Configuración del laboratorio

Esta carpeta reúne la configuración para ejecutar y trasladar el laboratorio de desarrollo. Para usar Walmart Visión, consultar la [guía de usuario](../Documentacion/Usar_Walmart_Vision.md).

| Ubicación | Para qué sirve |
|---|---|
| [Docker](Docker/README.md) | Servicios del panel, variantes CPU/GPU, desarrollo y plantillas de configuración. |
| [CVAT](CVAT/README.md) | Conexión opcional al servicio de anotación mediante la cuenta personal de cada integrante. |
| [Migracion.md](Migracion.md) | Respaldo y traslado de una instalación del laboratorio a otro computador. |

Los iniciadores están en `Herramientas/Modelos` y `Herramientas/CVAT`. Las credenciales, archivos `.env` reales y volúmenes de CVAT se gestionan fuera de Git.

Para preparar una copia nueva con los activos correspondientes, seguir [Replicar el proyecto](../Documentacion/Desarrollo/Replicar_proyecto.md).
