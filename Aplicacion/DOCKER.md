# Ejecutar la app del equipo con Docker

La configuración de esta carpeta ejecuta la **app del equipo** en CPU y publica el puerto local 8095. La definición incluye dependencias para amd64 y arm64. El build y la prueba en un Mac físico siguen pendientes de certificación. [Comprobaciones y límites](../Documentacion/Verificacion_funcional.md#5-empaquetado-y-límites-de-plataforma).

## Preparar e iniciar

1. Instala [Docker Desktop para Mac](https://docs.docker.com/desktop/setup/install/mac-install/) para tu equipo, ábrelo y espera a que esté listo.
2. Extrae todo el ZIP en una carpeta local.
3. Abre Terminal y entra en **Walmart_Vision/Aplicacion** dentro del ZIP extraído, o en **Aplicacion/** dentro del clon. Esa carpeta contiene el `compose.yaml` del equipo.
4. Ejecuta:

   ```bash
   docker compose up --build -d --wait
   ```

5. Abre http://127.0.0.1:8095 en el navegador. La primera construcción necesita Internet y puede tardar varios minutos. No necesitas instalar Python.

Consulta el [manual de uso](../Documentacion/Usar_Walmart_Vision.md) para interpretar los resultados. Las fotos se procesan localmente; la sesión del lote, incluidas las fotos, puede guardarse en el navegador y borrarse desde las opciones de la galería.

## Detener y volver a iniciar

Desde la misma carpeta **Aplicacion**, detén el servicio con este comando.

```bash
docker compose down
```

Para volver a iniciarla con la imagen ya construida, abre Docker Desktop y ejecuta:

```bash
docker compose up -d --wait --pull never --no-build
```

## Resolver problemas

| Situación | Acción |
|---|---|
| Docker no responde | Abre Docker Desktop y espera a que esté listo. |
| No se encuentra `compose.yaml` | Entra con `cd` a la subcarpeta `Aplicacion` del paquete o del clon. |
| Falla una descarga | Comprueba Internet y repite el comando de construcción. |
| El servicio no inicia | Ejecuta `docker compose logs --tail=100 vision` para consultar el error. |
| El puerto 8095 está ocupado | Usa los comandos siguientes para iniciar en 8096. |

```bash
docker compose down
export VISION_PORT=8096
docker compose up -d --wait
```

Abre http://127.0.0.1:8096. Mantén `VISION_PORT` en esa sesión para los comandos posteriores. Para volver al puerto predeterminado, ejecuta `docker compose down`, luego `unset VISION_PORT` y vuelve a iniciar.

## Cliente en Docker

El `compose.apps.yaml` de la raíz define ambas apps. El cliente inicializa SQLite al arrancar y su carpeta está montada en solo lectura en esa definición. Usa la [instalación manual](../README.md#instalación-manual-y-configuración) o el iniciador de Windows para la app cliente con historial y reportes.
