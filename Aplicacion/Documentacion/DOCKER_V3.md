# Ejecutar las apps con Docker

Para iniciar el equipo en CPU usa el `compose.yaml` de la carpeta `Aplicacion/`. La [guía de Docker para el equipo](../DOCKER.md) indica qué carpeta abrir en el ZIP o en el clon y cómo cambiar el puerto.

El `compose.apps.yaml` de la raíz define cliente y equipo. El cliente necesita escritura en su carpeta de SQLite al iniciar, mientras que el montaje incluido es de solo lectura. Para usar historial compartido y reportes, abre el cliente desde Windows o sigue la [instalación manual](../../README.md#instalación-manual-y-configuración). El build Docker y la prueba en Mac físico siguen pendientes de certificación.

[Manual](../../Documentacion/Usar_Walmart_Vision.md) · [Apps y descarga](../../Entregables/README.md) · [Pruebas y empaquetado](../../Distribucion/README.md).
