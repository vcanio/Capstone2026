# Docker y configuración del proyecto

Esta guía es para el **laboratorio del equipo de desarrollo**. La aplicación de usuario Walmart Visión conserva su iniciador Windows y tiene un paquete Docker independiente para macOS: consultar la [guía de uso](../../Documentacion/Usar_Walmart_Vision.md) y [Docker para Visión](../../Herramientas/Demo_lite/DOCKER.md). El Compose de Visión viene dentro de su paquete y no inicia el laboratorio ni CVAT.

Los comandos de esta guía se ejecutan desde la raíz del proyecto. Los Compose del panel resuelven sus rutas a Datos, Experimentos, Modelos y Herramientas desde esta carpeta; mantienen el proyecto Docker `walmart-modelos` y los montajes anteriores.

| Archivo | Uso |
|---|---|
| compose.modelos.yml | Panel y laboratorio, configuración base. |
| compose.modelos.gpu.yml | Acceso a GPU NVIDIA. |
| compose.modelos.dev.yml | Código local montado para desarrollo. |
| compose.modelos.linux.yml | Red del anfitrión en Docker Engine Linux. |
| compose.cvat.migracion.yml | Ajustes para trasladar CVAT a otro equipo. |
| .env.modelos.example | Plantilla de conexión del panel a CVAT. |
| .env.cvat.migracion.example | Plantilla de configuración de la migración. |

## Inicio habitual

```powershell
& .\Herramientas\Modelos\iniciar_panel.ps1
```

El mismo script admite `-Cpu` y `-Build`. El inicio base no necesita CVAT. Para conectarlo a un CVAT ya disponible, configurar la URL y las credenciales personales según la [guía de conexión opcional](../CVAT/README.md) y ejecutar:

```powershell
& .\Herramientas\Modelos\iniciar_panel.ps1 -Cpu -ConCvat
```

`Herramientas/CVAT/iniciar_cvat.ps1` sirve para iniciar una instalación de CVAT que ya tenga sus fuentes, archivos privados y volúmenes preparados. El clon público no incluye ese entorno. Los iniciadores de acceso privado del anfitrión son específicos de su instalación y están excluidos de Git; no forman parte de las instrucciones para otro computador.

## Desarrollo del panel

```powershell
& .\Herramientas\Modelos\iniciar_panel.ps1 -Dev
```

Admite también `-Cpu`. El montaje de `Herramientas/Modelos` es de solo lectura: al guardar `panel.html` o los archivos CSS y JavaScript de `static/`, basta F5 en el navegador. No hace falta reconstruir la imagen. Para cambios de Python, reiniciar el servicio cuando no haya entrenamientos activos:

```powershell
docker compose -f Infraestructura/Docker/compose.modelos.yml -f Infraestructura/Docker/compose.modelos.dev.yml restart panel_modelos
```

Los cambios en `docker/requirements.txt` o en el Dockerfile sí necesitan `-Build`. Para volver a usar el código de la imagen, ejecutar `iniciar_panel.ps1` sin `-Dev`.

## Consultar el panel

```powershell
docker compose -f Infraestructura/Docker/compose.modelos.yml -f Infraestructura/Docker/compose.modelos.gpu.yml ps
docker compose -f Infraestructura/Docker/compose.modelos.yml -f Infraestructura/Docker/compose.modelos.gpu.yml logs --tail 80 panel_modelos
```

## Configuración opcional

Copiar `.env.modelos.example` a `.env.modelos` dentro de esta carpeta y editar la URL de CVAT. El script de inicio lee ese archivo automáticamente. Con Docker CLI, añadir `--env-file Infraestructura/Docker/.env.modelos` antes de la acción.

Para migrar CVAT, copiar `.env.cvat.migracion.example` a `.env.cvat.migracion` dentro de esta carpeta y seguir la [guía de migración](../Migracion.md). Los archivos de configuración reales están ignorados por Git. Las credenciales y la configuración privada de esta instalación están en Infraestructura/CVAT.

## Datos y ejecución

El panel utiliza Datos para imágenes, registros y exportaciones; Experimentos para pesos y resultados; Modelos para los checkpoints generales; y .config-modelo para estado y cachés. Los originales de V1, V2 y la reserva final se montan en solo lectura. Las exportaciones compartidas se escriben en Datos/Registros/Versiones_modelos.

Las anotaciones de CVAT son un estado independiente, guardado en sus volúmenes Docker. Copiar las carpetas del proyecto no sustituye un respaldo de esos volúmenes. La guía de migración contiene el procedimiento completo de respaldo y restauración.

Solo se ejecuta un trabajo de entrenamiento o inferencia del panel a la vez. Con GPU se añade compose.modelos.gpu.yml; con -Cpu se utiliza CPU. El importador consulta CVAT a través de MODEL_CVAT_URL y sus credenciales locales; esas consultas no modifican dibujos. Una nueva copia requiere revisión antes de entrenar.

Los cambios de esta reorganización requieren reconstruir una imagen Docker antigua con `iniciar_panel.ps1 -Build`, o usar el montaje de desarrollo y reiniciar el servicio. No se inicia ni se detiene un entrenamiento al reorganizar los archivos.

[Configuración de CVAT](../CVAT/README.md) · [Migración](../Migracion.md) · [Entrada del proyecto](../../README.md).
