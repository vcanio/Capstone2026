# Walmart Visión en macOS con Docker

El paquete `Walmart_Vision_Actual_20261023.zip` incluye el visor, los dos modelos V2 y los archivos de Docker. La construcción utiliza Linux y la arquitectura del equipo: ARM64 en Mac con Apple Silicon y AMD64 en Mac Intel. El análisis utiliza CPU. Las fotografías se procesan en memoria en el computador y no se guardan ni se suben a un servicio externo.

## Preparar el equipo

1. Instalar [Docker Desktop para Mac](https://docs.docker.com/desktop/setup/install/mac-install/), eligiendo Apple Silicon o Intel según **Acerca de este Mac**.
2. Abrir Docker Desktop y esperar a que el motor esté listo. Se recomienda disponer de al menos 8 GB de RAM en el equipo y varios GB libres para la imagen y la caché de construcción; el consumo depende de la fotografía.
3. Extraer **todo** el ZIP en una carpeta local. El mismo ZIP sirve para Windows y Mac; en Mac se utilizan los archivos Docker incluidos.
4. Abrir Terminal, escribir `cd `, arrastrar la carpeta **Walmart_Vision** extraída a la ventana y pulsar Intro. Dentro deben estar `compose.yaml`, `Dockerfile` y `modelos.json`.

No hace falta instalar Python ni copiar el repositorio o los datos de entrenamiento. La primera construcción requiere Internet para descargar la imagen base y las bibliotecas. Puede tardar varios minutos.

## Iniciar

En esa Terminal, ejecutar:

```bash
docker compose up --build -d --wait
```

Cuando termine, abrir [Walmart Visión](http://localhost:8095). El navegador se abre manualmente. El visor abre directamente para analizar una foto. Elegir un modelo, cargar una foto JPG/PNG/WebP, seleccionar **Solo YOLO** o **YOLO + detección de bordes** y pulsar **Analizar foto**. Las vistas y los límites de imagen son los mismos que en Windows: 15 MB y 24 megapíxeles.

Para detener la aplicación:

```bash
docker compose down
```

Para volver a iniciarla con la imagen ya construida, incluso sin Internet:

```bash
docker compose up -d --wait --pull never --no-build
```

Docker Desktop debe permanecer abierto mientras se usa Visión. El contenedor no necesita acceso a carpetas del Mac: la fotografía se selecciona desde el navegador. El puerto se publica únicamente en `127.0.0.1` del equipo.

## Resolver problemas

| Situación | Acción |
|---|---|
| No se encuentra `docker` o no conecta con el motor | Instalar/abrir Docker Desktop y esperar a que esté listo. |
| No encuentra el archivo de configuración | Entrar con `cd` a la carpeta `Walmart_Vision` que contiene `compose.yaml`. |
| Falta `modelos.json`, un peso o un módulo de bordes | Extraer de nuevo el ZIP completo. El código fuente de GitHub por sí solo no incluye los modelos. |
| Falla una descarga durante la construcción | Revisar Internet y repetir `docker compose up --build -d --wait`; se reutilizan las capas descargadas. |
| El servicio no queda saludable o se detiene | Ejecutar `docker compose logs --tail=100 vision` y conservar el mensaje. Si Docker informa falta de memoria, aumentar la memoria asignada en sus ajustes y cerrar aplicaciones pesadas. |
| La primera predicción tarda | Esperar la carga del modelo en CPU y revisar `docker compose logs -f vision`; Ctrl+C solo cierra la vista de registros. |
| El puerto 8095 está ocupado | Seguir los comandos de puerto alternativo de abajo. |

Puerto alternativo en la misma sesión de Terminal:

```bash
docker compose down
export VISION_PORT=8096
docker compose up -d --wait
```

Abrir entonces [Walmart Visión en el puerto 8096](http://localhost:8096). Mantener `VISION_PORT` al usar los comandos posteriores. Para volver al puerto predeterminado, ejecutar `docker compose down`, `unset VISION_PORT` y volver a iniciar. Se cambia también el puerto interno para conservar las comprobaciones de Host y Origin del visor.

## Preparación desde el laboratorio

El paquete completo se genera desde la raíz del proyecto, con los pesos originales disponibles:

```bash
python Herramientas/Modelos/empaquetar_demo_lite.py --output Entregables/Walmart_Vision_Actual_20261023.zip
```

El empaquetador agrega los modelos, su manifiesto SHA-256, los módulos de bordes, las instrucciones y los archivos Docker. No incluye fotografías, entornos Python ni datos del laboratorio. Genera un `.sha256` junto al ZIP. Compartir ambos archivos y conservar el nombre y el hash de cada versión distribuida.

El Dockerfile se construye desde la carpeta **extraída del paquete**, no desde `Herramientas/Demo_lite` del repositorio: esa carpeta fuente no contiene los pesos ni el manifiesto generado. El `.dockerignore` limita el contexto a los archivos necesarios. El proceso corre con un usuario sin privilegios y verifica los hashes de los modelos y los módulos de bordes al construir y al iniciar.

Las dependencias principales conservan las versiones del visor: Python 3.12, PyTorch 2.5.1, torchvision 0.20.1, Ultralytics 8.4.174, NumPy 1.26.4 y Pillow 12.3.0. PyTorch se instala desde su índice oficial CPU para ambas arquitecturas. No se fuerza `platform: linux/amd64` en Compose: Apple Silicon construye ARM64 directamente.

Para comprobar ambas arquitecturas desde un constructor con soporte multiplataforma, ejecutar dentro del paquete extraído:

```bash
docker buildx build --platform linux/amd64,linux/arm64 --tag walmart-vision:verificacion --output type=oci,dest=../walmart-vision-multiplataforma.tar .
```

El archivo OCI es una salida técnica opcional y no es necesario para seguir las instrucciones de inicio. La construcción y las pruebas en Linux, incluso con emulación ARM64, no sustituyen la comprobación en un Mac físico. El alcance ejecutado se registra en [VERIFICACION_DOCKER.md](VERIFICACION_DOCKER.md), incluido en el paquete.

Fuentes: [Docker Desktop para Mac](https://docs.docker.com/desktop/setup/install/mac-install/), [construcciones multiplataforma](https://docs.docker.com/build/building/multi-platform/) e [índice CPU de PyTorch](https://download.pytorch.org/whl/cpu/).
