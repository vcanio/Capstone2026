# Instalar y desarrollar Walmart Visión · 11/11/2026

Para usar las apps basta la [descarga vigente](../../Entregables/README.md). El laboratorio y CVAT son herramientas de desarrollo independientes de la inferencia.

## Apps desde un clon

```powershell
git clone https://github.com/vcanio/Capstone2026.git
cd Capstone2026
```

Windows x64: abrir `Aplicacion_Cliente/iniciar_cliente.cmd` (8098) o `Aplicacion/iniciar.cmd` (8095). El preparador instala Python 3.12 y dependencias en una carpeta privada de la aplicación. El primer inicio necesita Internet. Si ya existe el entorno de desarrollo, los iniciadores pueden reutilizarlo.

Con Docker Desktop activo, desde la raíz:

```bash
docker compose -f compose.apps.yaml up --build -d --wait
```

Cliente en http://127.0.0.1:8098 y equipo en http://127.0.0.1:8095. Para detener: `docker compose -f compose.apps.yaml down`. La configuración Compose está validada; esta entrega no tiene una nueva prueba física en Mac ni build Docker verificado.

Las dos apps usan el cierre V3 revisado adoptado el 10/11 y Línea A del 8/11. No instalar ni seleccionar los antiguos cuatro modelos V1/V2 para reproducir el estado vigente. [Ficha del modelo](../Modelo_V3_actual.md) · [Guía cliente](../../Aplicacion_Cliente/README.md) · [Guía equipo](../../Aplicacion/Documentacion/REVISION_EQUIPO.md).

## Laboratorio y activos privados

El clon contiene el código del laboratorio, sin las fotografías, exportaciones completas, configuraciones privadas o respaldos necesarios para repetir todos los ensayos. Coordinar los activos versionados con el mantenedor y comprobar sus manifiestos y hashes. No descargar ni generar sustitutos para aparentar una reproducción completa.

El preparador histórico `Laboratorio/Reproducibilidad/preparar.py --assets RUTA_A_LOS_ZIP` instala los paquetes declarados en sus manifiestos; esos paquetes históricos no garantizan por sí solos el cierre del 10/11. La configuración activa de CVAT, partición, selección, almacenamiento y registro oficial debe corresponder al ensayo que se pretende reproducir.

En una instalación de desarrollo ya preparada:

```powershell
& ./Laboratorio/Modelos/abrir_panel.ps1
```

Panel en http://localhost:8090. El iniciador de servicios admite CPU, desarrollo y CVAT opcional; véase [Infraestructura](../../Infraestructura/Docker/README.md). Los datasets externos se configuran mediante `WALMART_DATA_ROOT`; [almacenamiento](../../Datos/Registros/Almacenamiento/README.md). Conservar junctions, enlaces duros y metadatos congelados. No copiar credenciales del equipo anfitrión al repositorio.

## Verificaciones

Las pruebas de apps y unidades usan fixtures o imágenes generadas. Algunas integraciones se omiten explícitamente si faltan sus activos privados. `Laboratorio/verificar_proyecto.py` tiene un alcance mayor y conserva la incidencia previa de tres fuentes V1 ausentes; pasar CI no equivale a una auditoría global del almacenamiento local ni a evaluación final de precisión.

[Pruebas del laboratorio](../../Laboratorio/README.md#clon-público-y-pruebas) · [Instrucciones anteriores conservadas](../../Historico/Documentacion/Desarrollo/Replicar_proyecto_antes_alineacion_20261111.md).
