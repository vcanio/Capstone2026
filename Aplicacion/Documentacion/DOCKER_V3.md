# Ejecutar las apps con Docker

Con Docker Desktop abierto, desde la raíz del clon o de Walmart_Vision extraído:

```bash
docker compose -f compose.apps.yaml up --build -d --wait
```

Cliente: http://127.0.0.1:8098. Equipo: http://127.0.0.1:8095. Las apps ejecutan inferencia en CPU y comparten un modelo oficial. No necesitan CVAT ni el laboratorio.

Para detener ambas:

```bash
docker compose -f compose.apps.yaml down
```

Para ejecutar solo la app del equipo, entrar en Aplicacion/ y usar `docker compose up --build -d --wait`.

La primera construcción necesita Internet. El Dockerfile declara dependencias CPU para amd64 y arm64; la compatibilidad declarada no sustituye una prueba física en Mac. La entrega del 11/11 validó Compose sin construir la imagen ni probarla físicamente en macOS. Las verificaciones de otras fechas mantienen su propio alcance.

Las fotos se procesan localmente y no entrenan el modelo. Revisa contornos y visibilidad: Línea A es un índice visual preliminar 0–100 con umbral 52, no stock físico.

[Manual](../../Documentacion/Usar_Walmart_Vision.md) · [Apps y descarga](../../Entregables/README.md) · [Pruebas y empaquetado](../../Distribucion/README.md).
