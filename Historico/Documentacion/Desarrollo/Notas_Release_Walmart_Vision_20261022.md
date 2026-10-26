> **Registro fechado: consultar su alcance original.** Las pruebas, modelos y expresiones de actualidad de este registro corresponden a la etapa que documenta. La distribución vigente es **Walmart Vision V3**, publicada el 26 de octubre de 2026, con un único best.pt propio. Este antecedente no acredita una evaluación nueva de V3. [Versión vigente y límites](../../../Modelos/Actual/README.md).

# Walmart Visión · Windows y macOS · Ocupación visual

**Una sola descarga para Windows x64 y Mac Intel/Apple Silicon:** [Walmart_Vision_Ocupacion_20261022.zip](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-2026-10-22/Walmart_Vision_Ocupacion_20261022.zip). El mismo ZIP incluye el iniciador Windows, Docker para macOS, el visor y los cuatro modelos V1/V2. No hay que descargar paquetes distintos según el sistema operativo.

## Mejoras visuales

- **Un porcentaje de ocupación estimada por nivel**, visible sobre la foto y en una tabla sencilla.
- **Rojo · Reponer:** menos del **30 %**. **Verde · Suficiente:** **30 % o más**. El 30 % exacto es verde.
- **Gris · Sin medición** cuando el nivel no permite calcular la estimación.
- **Original, Niveles, Comparar y la imagen descargada** mantienen el recorrido de revisión; Niveles, Comparar y la descarga muestran los mismos porcentajes y colores.
- El desglose de área y ancho queda plegado en **Cómo se calcula**. El estado original y la confianza de YOLO se consultan en **Detalle del modelo YOLO**.
- **Bordes V2** es el método inicial: combina 70 % de superficie y 30 % de ancho. También se conservan Bordes V1 y Solo YOLO.
- Presentación comprobada en escritorio y móvil, con temas claro y oscuro.

Se corrige además el empaquetado Docker para incluir el módulo necesario del cálculo V2.

## Windows

1. Descargar y extraer **todo el mismo ZIP**.
2. Abrir `Walmart_Vision/iniciar.cmd` y mantener la consola abierta.
3. La primera ejecución prepara automáticamente Python y las dependencias; requiere Internet. Después, el análisis se ejecuta localmente sin conexión.
4. Abrir [Walmart Visión](http://127.0.0.1:8095) si el navegador no se abre automáticamente.

No requiere Docker, CVAT ni instalar Python previamente. El iniciador incluido es para **Windows x64**.

## macOS · Intel y Apple Silicon

1. Instalar y abrir **Docker Desktop para Mac**, según el procesador del equipo.
2. Descargar y extraer **el mismo ZIP**.
3. Abrir Terminal en la carpeta `Walmart_Vision`, donde está `compose.yaml`, y ejecutar:

```bash
docker compose up --build -d --wait
```

4. Abrir [Walmart Visión](http://localhost:8095). La primera construcción requiere Internet; después el procesamiento es local en CPU.

Para detenerlo:

```bash
docker compose down
```

El ZIP incluye `DOCKER.md` con instalación, reinicio sin conexión y solución de problemas. Docker selecciona AMD64 para Intel y ARM64 para Apple Silicon.

## Descarga e integridad

Descargar el ZIP de aplicación de esta release y su [archivo SHA-256](https://github.com/vcanio/Capstone2026/releases/download/walmart-vision-2026-10-22/Walmart_Vision_Ocupacion_20261022.sha256). Los archivos automáticos **Source code** de GitHub contienen el código fuente; el ZIP indicado incluye los modelos necesarios para usar la aplicación.

## Verificación y alcance

Pasaron las 27 pruebas de la aplicación, incluidos 29,99/30 %, cero, cien, falta de medición, colores y limpieza de resultados al cambiar parámetros. Se construyó el paquete Docker para AMD64 y ARM64 y se comprobó inferencia HTTP sin red externa con los cuatro modelos y los tres métodos en ambas arquitecturas: **24 análisis**. Se verificaron las imágenes devueltas, los porcentajes y colores, la conservación de las predicciones originales y los hashes de modelos y módulos.

Las comprobaciones Docker se ejecutaron en Windows con motor Linux; ARM64 utilizó emulación. La prueba física en un Mac y la instalación en otro computador siguen pendientes. La estimación de ocupación es experimental y requiere calibración; estos controles verifican funcionamiento, no precisión sobre ocupación real. No se volvieron a entrenar los modelos. Las fotos se procesan en memoria y no se guardan; el ZIP no incluye el dataset.

Esta release reúne ambos sistemas y queda como descarga vigente. Las releases anteriores y sus archivos se conservan como historial.
