# Usar Walmart Visión

Esta guía corresponde a **V3, en pruebas locales al 26 de octubre de 2026**. La release V3 se prepara como borrador con el paquete y su comprobante SHA-256; todavía no es una descarga pública. Consulta el [estado de distribución](../Entregables/README.md) antes de descargar una entrega: las releases existentes pertenecen a versiones anteriores.

## Abrir la aplicación

Si el equipo te entregó el paquete V3, extrae todo el ZIP. El archivo automático “Source code” de GitHub contiene fuentes, sin los pesos necesarios para ejecutar esta versión de la app.

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
2. Responde **¿Cómo se ve la góndola?** según lo que ves en la imagen.
3. Pulsa **Analizar foto**.
4. Comprueba los contornos y los avisos antes de interpretar los porcentajes.

El análisis utiliza automáticamente el modelo V3 vigente, niveles y detección de bordes, con confianza fija 0,60. No hay que elegir modelos ni ajustar parámetros. La confianza de detección y la ocupación son medidas diferentes.

Las fotografías se procesan en memoria en el computador y no se guardan ni se añaden al entrenamiento.

## Indicar la visibilidad

| Opción | Comportamiento |
|---|---|
| **Completa y despejada** | Estima ocupación dentro de los niveles detectados. |
| **Recortada por la foto** | Limita la medición a la zona visible y marca Revisar. |
| **Con un objeto delante** | Suspende la medición y pide una foto sin el obstáculo. |
| **Con una persona tapándola** | Muestra Góndola tapada, sin contornos, ocupación ni reposición. |

La comprobación es manual: la app no detecta automáticamente esos casos. Si un contorno alcanza el encuadre también aparece un aviso conservador para revisar lo que quedó fuera.

## Revisar el resultado

Los niveles se numeran desde abajo hacia arriba. Utiliza:

- **Original:** la fotografía que cargaste.
- **Niveles:** los contornos, las lecturas estimadas y los avisos.
- **Bordes:** mapas opcionales para inspeccionar la señal visual.
- **Comparar:** original y resultado juntos.
- **Descargar resultado:** una copia de la imagen analizada.

**Reponer** aparece bajo el 30 % y **Suficiente** desde el 30 %, solo cuando la medición y el alcance lo permiten. Son referencias experimentales; no certifican stock disponible.

**Revisar** indica que no se puede confirmar el nivel completo o su ocupación. Si la señal se concentra arriba o en la periferia sin suficiente respaldo central e inferior, la app muestra **Revisar · señal ambigua**, sin porcentaje presentado: puede estar respondiendo a un cartel o al fondo.

Sin niveles detectados, toma otra foto más frontal. La ausencia de detecciones no demuestra que la góndola esté vacía.

## Qué es el mapa de señal

El amarillo destaca zonas que activan el análisis de bordes, color y textura. Puede marcar envases, pero también carteles o fondos. Una zona sin amarillo tampoco garantiza que esté vacía.

El mapa sirve para revisar por qué se obtuvo una estimación. No es una segmentación confirmada de productos ni un porcentaje real de inventario.

## Si no inicia o no termina el análisis

- Extrae el ZIP completo y conserva sus archivos juntos.
- En el primer inicio, comprueba la conexión y espera a que se preparen las dependencias.
- Si usas Docker, comprueba que Docker Desktop esté funcionando.
- Si la foto se rechaza o el análisis tarda demasiado, prueba una imagen JPG, PNG o WebP más pequeña.
- Si el resultado no coincide con la foto, revisa contornos y visibilidad; no lo uses como confirmación de stock.

[Cómo funciona](Guia_para_entender_el_proyecto.md) · [Modelo y limitaciones](Modelo_V3_actual.md) · [Volver al inicio](../README.md)
