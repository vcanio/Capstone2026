# Walmart Vision V3 en macOS con Docker

Descarga el [ZIP V3 publicado](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-10-26/Walmart_Vision_V3_20261028.zip). Incluye el visor, el único modelo V3 y los archivos Docker para Mac Intel y Apple Silicon. Source code contiene fuentes sin pesos y no sustituye ese paquete.

## Iniciar

1. Instalar y abrir Docker Desktop para Mac según el procesador del equipo.
2. Extraer todo el ZIP y abrir Terminal en la carpeta `Walmart_Vision`, donde está `compose.yaml`.
3. Ejecutar `docker compose up --build -d --wait`. La primera construcción necesita Internet para preparar la imagen y las dependencias.
4. Abrir http://127.0.0.1:8095, seleccionar una foto frontal o casi frontal, pulsar Analizar foto.

El procesamiento es local en CPU. La sesión del lote, incluidas las fotos, se guarda en el navegador local y puede borrarse desde la aplicación; no se añade al entrenamiento. La confianza inicial es 0,60, ajustable desde 0,40; la ocupación sigue siendo experimental y no se detectan automáticamente obstáculos.

## Volver a usar y detener

Con la imagen ya preparada, usar `docker compose up -d --wait`. Para detener: `docker compose down`. Si el puerto 8095 está ocupado, detener otra instancia o seguir las opciones de Compose incluidas en la descarga. Mantener todos los archivos del ZIP juntos.

Vicente confirmó que este procedimiento funcionó en macOS con la release anterior. V3 mantiene el mismo flujo y dependencias. Las pruebas anteriores de AMD64 y ARM64 emulada están en el [registro Docker fechado](VERIFICACION_DOCKER.md); no constituyen una nueva validación de precisión V3. La [guía del 23 de octubre](../Historico/Documentacion/Aplicacion/DOCKER_20261023.md) se conserva como antecedente.

[Manual V3](../Documentacion/Usar_Walmart_Vision.md) · [Distribución](../Entregables/README.md) · [Modelo y límites](../Modelos/Actual/README.md).
