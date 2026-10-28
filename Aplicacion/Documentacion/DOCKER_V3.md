# Walmart Visión en macOS con Docker

El mismo paquete sirve para Windows y macOS. En Mac, Docker ejecuta la aplicación localmente en CPU, tanto en Apple Silicon como en Intel.

## Preparar e iniciar

1. Instala [Docker Desktop para Mac](https://docs.docker.com/desktop/setup/install/mac-install/) para tu equipo, ábrelo y espera a que esté listo.
2. Extrae todo el ZIP en una carpeta local.
3. Abre Terminal, escribe `cd `, arrastra la carpeta extraída **Walmart_Vision** a la ventana y pulsa Intro.
4. Ejecuta:

   ```bash
   docker compose up --build -d --wait
   ```

5. Abre http://127.0.0.1:8095 en el navegador. La primera construcción necesita Internet y puede tardar varios minutos. No necesitas instalar Python.

Consulta `LEEME.md` para el uso y las limitaciones de los resultados. Las fotos se procesan localmente; la sesión del lote, incluidas las fotos, puede guardarse en el navegador y borrarse desde las opciones de la galería.

## Detener y volver a iniciar

Desde la carpeta `Walmart_Vision`, detén la aplicación con:

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
| No se encuentra `compose.yaml` | Entra con `cd` a la carpeta `Walmart_Vision` extraída. |
| Falla una descarga | Comprueba Internet y repite el comando de construcción. |
| El servicio no inicia | Ejecuta `docker compose logs --tail=100 vision` para consultar el error. |
| El puerto 8095 está ocupado | Usa los comandos siguientes para iniciar en 8096. |

```bash
docker compose down
export VISION_PORT=8096
docker compose up -d --wait
```

Abre http://127.0.0.1:8096. Mantén `VISION_PORT` en esa sesión para los comandos posteriores. Para volver al puerto predeterminado, ejecuta `docker compose down`, luego `unset VISION_PORT` y vuelve a iniciar.
