# Usar Walmart Visión

Esta guía corresponde a **V3, publicada el 26 de octubre de 2026**. Descarga el paquete desde la [release actual](https://github.com/vcanio/Capstone2026/releases/tag/walmart-vision-v3-2026-10-26); incluye la aplicación y su modelo para Windows x64 y macOS con Docker.

## Abrir la aplicación

Descarga [`Walmart_Vision_V3_20261028.zip`](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-v3-2026-10-26/Walmart_Vision_V3_20261028.zip) y extrae todo el ZIP. El archivo automático “Source code” de GitHub contiene fuentes, sin los pesos necesarios para ejecutar esta versión de la app.

**Windows:** abre `Walmart_Vision/iniciar.cmd`. El iniciador prepara las dependencias en el primer uso. Después se abre el visor en [http://127.0.0.1:8095](http://127.0.0.1:8095).

**Docker:** con Docker Desktop abierto, entra en la carpeta `Walmart_Vision` extraída y ejecuta:

```bash
docker compose up --build -d --wait
```

Abre [http://127.0.0.1:8095](http://127.0.0.1:8095). Para detenerlo, ejecuta `docker compose down`. Vicente confirmó que estos pasos funcionaron correctamente en su Mac con la release anterior. V3 mantiene el mismo flujo Docker y sus dependencias, incorporando los módulos del modelo actual.

La preparación inicial requiere conexión para obtener dependencias. La inferencia es local. No necesitas instalar CVAT, preparar datasets ni iniciar el laboratorio.

## Fotografías frontales

**Para usar esta versión, toma fotos frontales o casi frontales de la góndola.** Sitúate frente al tramo, mantén la cámara nivelada y procura que se vean sus dos extremos y las superficies de apoyo. Evita tomas desde un costado, desde muy arriba o abajo, panorámicas deformadas, desenfoque y reflejos fuertes. Si el mueble es largo, utiliza varias tomas frontales de tramos completos.

La perspectiva oblicua cambia las alturas y anchuras aparentes, oculta huecos detrás de los productos y puede desplazar las máscaras. El algoritmo estima una proporción de la imagen, sin reconstruir el volumen ni corregir automáticamente la perspectiva. Una foto frontal ayuda, pero no garantiza una detección correcta: revisa siempre los contornos y la visibilidad. No hay un ángulo máximo validado ni un detector automático que certifique que la toma sea frontal.

## Analizar una foto

1. Selecciona o arrastra una foto **JPG, PNG o WebP de hasta 15 MB**.
2. Pulsa **Analizar foto**.
3. Comprueba los contornos, la visibilidad y los avisos antes de interpretar los porcentajes.

El análisis utiliza automáticamente el modelo V3 vigente, niveles y detección de bordes, con confianza inicial 0,60, ajustable desde 0,40. No hay que elegir modelos. La confianza de detección y la ocupación son medidas diferentes.

Las fotografías se procesan localmente y no se añaden al entrenamiento. La sesión del lote, incluidas las fotos, se guarda en el navegador del equipo y puede eliminarse desde «Borrar sesión guardada».

## Revisar la visibilidad

La app no detecta automáticamente personas ni obstáculos. Revisa la foto y toma otra si la góndola está tapada. Si un contorno alcanza el encuadre aparece un aviso para revisar lo que quedó fuera.

## Revisar el resultado

Los niveles se numeran desde abajo hacia arriba. Utiliza:

- **Original:** la fotografía que cargaste.
- **Niveles:** los contornos, las lecturas estimadas y los avisos.
- **Bordes:** mapas opcionales para inspeccionar la señal visual.
- **Comparar:** original y resultado juntos.
- **Descargar resultado:** una copia de la imagen analizada.

**Reponer** aparece bajo el 30 % y **Suficiente** desde el 30 % de cobertura experimental del frente, solo cuando la medición y el alcance lo permiten. Se asume lleno detrás del producto visible; el espacio libre encima no reduce la cobertura. La señal no identifica productos de manera fiable y requiere calibración; revisa la foto antes de tomar decisiones.

**Revisar** indica que no se puede confirmar el nivel completo o su ocupación. Si la señal se concentra arriba o en la periferia sin suficiente respaldo central e inferior, la app muestra **Revisar · señal ambigua**, sin porcentaje presentado: puede estar respondiendo a un cartel o al fondo.

Sin niveles detectados, toma otra foto más frontal. La ausencia de detecciones no demuestra que la góndola esté vacía.

## Qué es el mapa de señal

El fucsia destaca zonas que activan el análisis de bordes, color y textura. Puede marcar envases, pero también carteles o fondos. Una zona sin señal fucsia tampoco garantiza que esté vacía.

El mapa sirve para revisar por qué se obtuvo una estimación. No es una segmentación confirmada de productos ni un porcentaje real de inventario.

## Si no inicia o no termina el análisis

- Extrae el ZIP completo y conserva sus archivos juntos.
- En el primer inicio, comprueba la conexión y espera a que se preparen las dependencias.
- Si usas Docker, comprueba que Docker Desktop esté funcionando.
- Si la foto se rechaza o el análisis tarda demasiado, prueba una imagen JPG, PNG o WebP más pequeña.
- Si el resultado no coincide con la foto, revisa contornos y visibilidad; no lo uses como confirmación de stock.

[Cómo funciona](Guia_para_entender_el_proyecto.md) · [Modelo y limitaciones](Modelo_V3_actual.md) · [Volver al inicio](../README.md)
